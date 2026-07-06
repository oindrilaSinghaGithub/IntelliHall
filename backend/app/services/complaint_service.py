"""
IntelliHall — Complaint Service

Sits between the API router and the repository.  All business logic,
validation rules, authorization checks, and exception mapping live here.
The router stays thin; the repository stays pure.

Role model
----------
STUDENT
  - create()            : own hall only; hall_id + created_by taken from token
  - get_for_student()   : own complaints only (403 if foreign)
  - list_for_student()  : paginated list scoped to created_by = current_user.id

HALL_ADMIN
  - get_for_admin()              : any complaint in their hall (403 if foreign hall)
  - list_for_hall()              : paginated list scoped to hall
  - update_status()              : valid transition + writes history row
  - update() / delete()          : hall-scoped

Public API
----------
ComplaintService.create(session, data, current_user)
ComplaintService.get_for_student(session, complaint_id, current_user)
ComplaintService.list_for_student(session, filters, current_user)
ComplaintService.get_for_admin(session, complaint_id, current_user)
ComplaintService.list_for_hall(session, hall_id, filters, current_user)
ComplaintService.update_status(session, complaint_id, payload, current_user)
ComplaintService.update(session, complaint_id, data, current_user)
ComplaintService.delete(session, complaint_id, current_user)
ComplaintService.get_or_404(session, complaint_id)          [internal helper]
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint
from app.models.enums import ComplaintStatus, ComplaintType, UserRole
from app.repositories.complaint_repository import ComplaintRepository
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintFilters,
    ComplaintSummary,
    ComplaintUpdate,
    HallComplaintFilters,
    PaginatedResponse,
    StatusUpdateRequest,
)

if TYPE_CHECKING:
    from app.models.user import User


# ---------------------------------------------------------------------------
# Allowed status transitions
# ---------------------------------------------------------------------------

# Maps current status → set of valid next statuses.
# VISIT_FAILED_ROOM_LOCKED can be reached from ANY status.
_TRANSITIONS: dict[ComplaintStatus, set[ComplaintStatus]] = {
    ComplaintStatus.SUBMITTED: {ComplaintStatus.VERIFIED},
    ComplaintStatus.VERIFIED: {ComplaintStatus.SCHEDULED},
    ComplaintStatus.SCHEDULED: {ComplaintStatus.IN_PROGRESS},
    ComplaintStatus.IN_PROGRESS: {ComplaintStatus.COMPLETED},
    ComplaintStatus.COMPLETED: {ComplaintStatus.WAITING_STUDENT_CONFIRMATION},
    ComplaintStatus.WAITING_STUDENT_CONFIRMATION: {ComplaintStatus.CLOSED},
    # Terminal states — no further progression (except VISIT_FAILED universal rule)
    ComplaintStatus.CLOSED: set(),
    ComplaintStatus.VISIT_FAILED_ROOM_LOCKED: set(),
}

# These statuses can be transitioned to from ANY current status
_UNIVERSAL_TARGETS: set[ComplaintStatus] = {ComplaintStatus.VISIT_FAILED_ROOM_LOCKED}


def _is_valid_transition(current: ComplaintStatus, target: ComplaintStatus) -> bool:
    """Return True when the current→target transition is permitted."""
    if target in _UNIVERSAL_TARGETS:
        return True
    return target in _TRANSITIONS.get(current, set())


class ComplaintService:
    """Business-logic layer for the Complaint domain."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def get_or_404(session: AsyncSession, complaint_id: str) -> Complaint:
        """Fetch a Complaint by ID, raising HTTP 404 if absent."""
        complaint = await ComplaintRepository.get_by_id(session, complaint_id)
        if complaint is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint '{complaint_id}' not found.",
            )
        return complaint

    # ------------------------------------------------------------------
    # Create (Student)
    # ------------------------------------------------------------------

    @staticmethod
    async def create(
        session: AsyncSession,
        data: ComplaintCreate,
        current_user: "User",
    ) -> Complaint:
        """
        Validate and persist a new complaint raised by a student.

        Rules:
        - Caller must be assigned to a hall (HTTP 403 otherwise).
        - PERSONAL complaints must supply room_number.
        - COMMON_AREA complaints must supply at least one location field.
        - hall_id and created_by come from the token, never from the body.
        """
        if not current_user.hall_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Your account is not assigned to a hall. "
                    "Please contact an administrator."
                ),
            )

        if data.complaint_type == ComplaintType.PERSONAL:
            if not data.room_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="room_number is required for PERSONAL complaints.",
                )

        if data.complaint_type == ComplaintType.COMMON_AREA:
            if not any([data.block, data.floor, data.common_area, data.qr_location_id]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "At least one of block, floor, common_area, or "
                        "qr_location_id is required for COMMON_AREA complaints."
                    ),
                )

        return await ComplaintRepository.create(
            session,
            data,
            user_id=current_user.id,
            hall_id=current_user.hall_id,
        )

    # ------------------------------------------------------------------
    # Read — Student: own complaint only
    # ------------------------------------------------------------------

    @staticmethod
    async def get_for_student(
        session: AsyncSession,
        complaint_id: str,
        current_user: "User",
    ) -> Complaint:
        """
        Fetch a complaint for a student, enforcing ownership.

        Returns HTTP 404 if absent.
        Returns HTTP 403 if the complaint belongs to another student.
        """
        complaint = await ComplaintService.get_or_404(session, complaint_id)
        if complaint.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this complaint.",
            )
        return complaint

    # ------------------------------------------------------------------
    # List — Student: own complaints, paginated
    # ------------------------------------------------------------------

    @staticmethod
    async def list_for_student(
        session: AsyncSession,
        filters: ComplaintFilters,
        current_user: "User",
    ) -> "PaginatedResponse[ComplaintSummary]":
        """
        Return a paginated list of the authenticated student's own complaints.

        ``created_by`` is always forced to current_user.id regardless of any
        value in filters, so students cannot query other users' complaints.
        """
        items, total = await ComplaintRepository.list(
            session,
            created_by=current_user.id,  # always scope to caller
            status=filters.status,
            priority=filters.priority,
            category=filters.category,
            complaint_type=filters.complaint_type,
            page=filters.page,
            page_size=filters.page_size,
            sort_by=filters.sort_by,
            sort_order=filters.sort_order,
        )
        summaries = [ComplaintSummary.model_validate(c) for c in items]
        pages = math.ceil(total / filters.page_size) if total > 0 else 1
        return PaginatedResponse[ComplaintSummary](
            items=summaries,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            pages=pages,
        )

    # ------------------------------------------------------------------
    # Read — Admin: any complaint in their hall
    # ------------------------------------------------------------------

    @staticmethod
    async def get_for_admin(
        session: AsyncSession,
        complaint_id: str,
        current_user: "User",
    ) -> Complaint:
        """
        Fetch a complaint for a hall admin, enforcing hall membership.

        Returns HTTP 404 if absent.
        Returns HTTP 403 if the complaint belongs to a different hall.
        """
        complaint = await ComplaintService.get_or_404(session, complaint_id)
        if complaint.hall_id != current_user.hall_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access complaints from another hall.",
            )
        return complaint

    # ------------------------------------------------------------------
    # List — Admin: all complaints for a specific hall
    # ------------------------------------------------------------------

    @staticmethod
    async def list_for_hall(
        session: AsyncSession,
        hall_id: str,
        filters: HallComplaintFilters,
        current_user: "User",
    ) -> "PaginatedResponse[ComplaintSummary]":
        """
        Return a paginated list of complaints for a hall (admin view).

        The admin may only list complaints from their own assigned hall.
        HTTP 403 if they try to access a different hall's complaints.
        """
        if current_user.hall_id != hall_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view complaints from your own hall.",
            )

        items, total = await ComplaintRepository.list(
            session,
            hall_id=hall_id,
            status=filters.status,
            priority=filters.priority,
            category=filters.category,
            complaint_type=filters.complaint_type,
            page=filters.page,
            page_size=filters.page_size,
            sort_by=filters.sort_by,
            sort_order=filters.sort_order,
        )
        summaries = [ComplaintSummary.model_validate(c) for c in items]
        pages = math.ceil(total / filters.page_size) if total > 0 else 1
        return PaginatedResponse[ComplaintSummary](
            items=summaries,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            pages=pages,
        )

    # ------------------------------------------------------------------
    # Status update — Admin only
    # ------------------------------------------------------------------

    @staticmethod
    async def update_status(
        session: AsyncSession,
        complaint_id: str,
        payload: StatusUpdateRequest,
        current_user: "User",
    ) -> Complaint:
        """
        Transition a complaint to a new status.

        Rules:
        - Caller must be HALL_ADMIN (enforced by the router dependency, but
          checked here too for defence-in-depth).
        - The complaint must belong to the admin's hall (HTTP 403).
        - The transition must be valid per _TRANSITIONS (HTTP 400).
        - A ComplaintStatusHistory row is always written on success.
        """
        if current_user.role != UserRole.HALL_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only hall administrators can update complaint status.",
            )

        complaint = await ComplaintService.get_or_404(session, complaint_id)

        if complaint.hall_id != current_user.hall_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only manage complaints from your own hall.",
            )

        previous = complaint.status
        target = payload.new_status

        if not _is_valid_transition(previous, target):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid status transition: "
                    f"'{previous.value}' → '{target.value}'. "
                    f"Allowed next statuses from '{previous.value}': "
                    + ", ".join(
                        f"'{s.value}'"
                        for s in (
                            _TRANSITIONS.get(previous, set()) | _UNIVERSAL_TARGETS
                        )
                    )
                    + "."
                ),
            )

        # Apply status change
        complaint.status = target
        complaint.updated_at = datetime.now(timezone.utc)
        await session.flush()

        # Write history record
        await ComplaintRepository.add_status_history(
            session,
            complaint_id=complaint.id,
            previous_status=previous,
            new_status=target,
            updated_by=current_user.id,
            remarks=payload.remarks,
        )

        await session.refresh(complaint)
        return complaint

    # ------------------------------------------------------------------
    # Generic update (admin, field-level)
    # ------------------------------------------------------------------

    @staticmethod
    async def update(
        session: AsyncSession,
        complaint_id: str,
        data: ComplaintUpdate,
        current_user: "User",
    ) -> Complaint:
        """
        Partially update complaint fields (admin only, own hall).

        Use update_status() for status transitions — it enforces the FSM
        and writes a history record.  This method is for non-status fields
        such as current_assignee, maintenance_type, priority, etc.
        """
        complaint = await ComplaintService.get_for_admin(session, complaint_id, current_user)

        if not data.model_dump(exclude_none=True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update.",
            )

        return await ComplaintRepository.update(session, complaint, data)

    # ------------------------------------------------------------------
    # Delete (admin only)
    # ------------------------------------------------------------------

    @staticmethod
    async def delete(
        session: AsyncSession,
        complaint_id: str,
        current_user: "User",
    ) -> None:
        """Hard-delete a complaint (admin, own hall only)."""
        complaint = await ComplaintService.get_for_admin(session, complaint_id, current_user)
        await ComplaintRepository.delete(session, complaint)
