"""
IntelliHall — Complaint Service

Sits between the API router and the repository.  All business logic,
validation rules, and exception mapping live here.  The router stays
thin and the repository stays pure.

Public API
----------
ComplaintService.create(session, data)                   -> Complaint
ComplaintService.get_or_404(session, complaint_id)       -> Complaint
ComplaintService.list(session, filters)                  -> PaginatedResponse[ComplaintSummary]
ComplaintService.update(session, complaint_id, data)     -> Complaint
ComplaintService.delete(session, complaint_id)           -> None
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint
from app.models.enums import ComplaintType
from app.repositories.complaint_repository import ComplaintRepository
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintFilters,
    ComplaintSummary,
    ComplaintUpdate,
    PaginatedResponse,
)

if TYPE_CHECKING:
    from app.models.user import User


class ComplaintService:
    """Business-logic layer for the Complaint domain."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    async def create(
        session: AsyncSession,
        data: ComplaintCreate,
        current_user: "User",
    ) -> Complaint:
        """
        Validate business rules then delegate to the repository.

        ``hall_id`` and ``created_by`` are derived from *current_user* so
        that clients can never supply or spoof them in the request body.

        Rules enforced:
        - The authenticated user must have a hall assigned (hall_id not NULL).
        - PERSONAL complaints must supply room_number.
        - COMMON_AREA complaints must supply at least one location field.
        """
        if not current_user.hall_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is not assigned to a hall. "
                       "Please contact an administrator.",
            )

        if data.complaint_type == ComplaintType.PERSONAL:
            if not data.room_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="room_number is required for PERSONAL complaints.",
                )

        if data.complaint_type == ComplaintType.COMMON_AREA:
            has_location = any(
                [data.block, data.floor, data.common_area, data.qr_location_id]
            )
            if not has_location:
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
    # Read — single (with 404 guard)
    # ------------------------------------------------------------------

    @staticmethod
    async def get_or_404(
        session: AsyncSession,
        complaint_id: str,
    ) -> Complaint:
        """
        Fetch a complaint by ID or raise HTTP 404.

        Centralising the 404 logic here keeps every endpoint handler
        to a single line for the fetch step.
        """
        complaint = await ComplaintRepository.get_by_id(session, complaint_id)
        if complaint is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Complaint '{complaint_id}' not found.",
            )
        return complaint

    # ------------------------------------------------------------------
    # Read — paginated list
    # ------------------------------------------------------------------

    @staticmethod
    async def list(
        session: AsyncSession,
        filters: ComplaintFilters,
    ) -> PaginatedResponse[ComplaintSummary]:
        """
        Apply filters, fetch a page of complaints, and wrap in a
        PaginatedResponse envelope.
        """
        items, total = await ComplaintRepository.list(
            session,
            hall_id=filters.hall_id,
            status=filters.status,
            priority=filters.priority,
            category=filters.category,
            complaint_type=filters.complaint_type,
            created_by=filters.created_by,
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
    # Update
    # ------------------------------------------------------------------

    @staticmethod
    async def update(
        session: AsyncSession,
        complaint_id: str,
        data: ComplaintUpdate,
    ) -> Complaint:
        """
        Fetch the complaint (raising 404 if absent), validate the patch,
        then apply the update.

        Business rule: if status_history tracking is needed on status
        transitions, that logic will be added here when auth is wired up.
        """
        complaint = await ComplaintService.get_or_404(session, complaint_id)

        # Guard: reject empty PATCH bodies
        if not data.model_dump(exclude_none=True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update.",
            )

        return await ComplaintRepository.update(session, complaint, data)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @staticmethod
    async def delete(
        session: AsyncSession,
        complaint_id: str,
    ) -> None:
        """Fetch the complaint (raising 404 if absent) then hard-delete it."""
        complaint = await ComplaintService.get_or_404(session, complaint_id)
        await ComplaintRepository.delete(session, complaint)
