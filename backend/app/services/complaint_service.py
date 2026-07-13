"""
IntelliHall — Complaint Service

Sits between the API router and the repository.  All business logic,
validation rules, authorization checks, and exception mapping live here.
The router stays thin; the repository stays pure.

Role model
----------
STUDENT
  - create()                  : own hall only
  - get_for_student()         : own complaints only
  - list_for_student()        : paginated list scoped to created_by
  - confirm_repair()          : own complaint, waiting_student_confirmation only
  - reject_repair()           : own complaint, waiting_student_confirmation only
  - upload_images()           : own complaint, submitted status only

HALL_ADMIN
  - get_for_admin()           : any complaint in their hall
  - list_for_hall()           : paginated list for hall
  - update_status()           : valid transition + writes history + assignment/slip
  - update() / delete()       : hall-scoped
  - get_completion_slip()     : own hall or complaint creator
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.complaint import Complaint
from app.models.enums import ComplaintStatus, ComplaintType, StudentConfirmationStatus, UserRole
from app.models.user import User
from app.repositories.assignment_repository import AssignmentRepository
from app.repositories.complaint_repository import ComplaintRepository
from app.repositories.completion_slip_repository import CompletionSlipRepository
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintFilters,
    ComplaintSummary,
    ComplaintUpdate,
    HallComplaintFilters,
    PaginatedResponse,
    StatusUpdateRequest,
)
from app.schemas.completion_slip import CompletionSlipRead
from app.services.notification_service import NotificationService
from app.utils.file_utils import delete_complaint_image, read_and_validate_image, save_complaint_image

if TYPE_CHECKING:
    from app.models.complaint import ComplaintImage
    from app.models.completion_slip import CompletionSlip


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
    # COMPLETED → WAITING_STUDENT_CONFIRMATION is an auto-transition;
    # the admin sends COMPLETED but the system stores WAITING_STUDENT_CONFIRMATION
    ComplaintStatus.COMPLETED: {ComplaintStatus.WAITING_STUDENT_CONFIRMATION},
    ComplaintStatus.WAITING_STUDENT_CONFIRMATION: {ComplaintStatus.CLOSED},
    ComplaintStatus.REOPENED: {ComplaintStatus.VERIFIED},
    # Terminal states
    ComplaintStatus.CLOSED: set(),
    ComplaintStatus.VISIT_FAILED_ROOM_LOCKED: {ComplaintStatus.VERIFIED},
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
        """Validate and persist a new complaint raised by a student."""
        if not current_user.hall_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Your account is not assigned to a hall. "
                    "Please contact an administrator."
                ),
            )

        from app.models.enums import HallVerificationStatus
        if current_user.hall_verification_status != HallVerificationStatus.APPROVED:
            if current_user.hall_verification_status == HallVerificationStatus.PENDING:
                msg = (
                    "Your hall affiliation is pending verification by the Hall Office. "
                    "Complaint submission will be enabled after approval."
                )
            else:
                msg = (
                    "Your hall affiliation has been rejected. "
                    "Please update your hall information from your profile and resubmit."
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=msg,
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
    # Upload images (Student — own complaint, submitted status only)
    # ------------------------------------------------------------------

    @staticmethod
    async def upload_images(
        session: AsyncSession,
        complaint_id: str,
        files: list[UploadFile],
        current_user: "User",
    ) -> list["ComplaintImage"]:
        """
        Attach one or more images to a complaint owned by the current user.

        Images may only be uploaded while the complaint is still ``submitted``.
        """
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one image file is required.",
            )

        complaint = await ComplaintService.get_or_404(session, complaint_id)

        if complaint.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to upload images for this complaint.",
            )

        if complaint.status != ComplaintStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Images can only be uploaded while the complaint is in "
                    "'submitted' status."
                ),
            )

        existing_count = await ComplaintRepository.count_images(session, complaint_id)
        if existing_count + len(files) > settings.MAX_IMAGES_PER_COMPLAINT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"A complaint may have at most {settings.MAX_IMAGES_PER_COMPLAINT} "
                    f"images. This complaint already has {existing_count}."
                ),
            )

        saved_urls: list[str] = []
        try:
            for upload in files:
                data, content_type = await read_and_validate_image(upload)
                image_url = save_complaint_image(complaint_id, data, content_type)
                saved_urls.append(image_url)

            return await ComplaintRepository.add_images(
                session,
                complaint_id,
                saved_urls,
            )
        except Exception:
            for url in saved_urls:
                delete_complaint_image(url)
            raise

    # ------------------------------------------------------------------
    # Read — Student: own complaint only
    # ------------------------------------------------------------------

    @staticmethod
    async def get_for_student(
        session: AsyncSession,
        complaint_id: str,
        current_user: "User",
    ) -> Complaint:
        """Fetch a complaint for a student, enforcing ownership."""
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
        """Return a paginated list of the authenticated student's own complaints."""
        items, total = await ComplaintRepository.list(
            session,
            created_by=current_user.id,
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
        """Fetch a complaint for a hall admin, enforcing hall membership."""
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
        """Return a paginated list of complaints for a hall (admin view)."""
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
    # Status update — Admin only (extended FSM)
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

        Extended behaviour:
        - SCHEDULED: requires worker assignment fields; creates ComplaintAssignment
        - COMPLETED: requires work_done; creates CompletionSlip; auto-transitions
          to WAITING_STUDENT_CONFIRMATION
        - CLOSED: requires student confirmation on the completion slip
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

        # -- COMPLETED is the admin-facing target; we auto-step to WAITING --
        # Validate transition using the logical flow
        effective_target = target
        if target == ComplaintStatus.COMPLETED:
            # The FSM maps IN_PROGRESS → COMPLETED → WAITING_STUDENT_CONFIRMATION
            # We validate as IN_PROGRESS → COMPLETED here
            pass

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

        # ----------------------------------------------------------------
        # SCHEDULED transition — create/update worker assignment
        # ----------------------------------------------------------------
        if target == ComplaintStatus.SCHEDULED:
            # Validate required fields
            if not payload.worker_name:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="worker_name is required when scheduling a complaint.",
                )
            if not payload.worker_type:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="worker_type is required when scheduling a complaint.",
                )
            if not payload.scheduled_date:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="scheduled_date is required when scheduling a complaint.",
                )

            # Upsert assignment
            await AssignmentRepository.upsert(
                session,
                complaint_id,
                worker_name=payload.worker_name,
                worker_type=payload.worker_type,
                scheduled_date=payload.scheduled_date,
                scheduled_time=payload.scheduled_time,
                admin_remarks=payload.admin_remarks,
            )

            # Update backwards-compat fields
            complaint.current_assignee = payload.worker_name
            complaint.maintenance_type = payload.worker_type
            complaint.updated_at = datetime.now(timezone.utc)
            await session.flush()

            # Apply status change
            complaint.status = target
            complaint.updated_at = datetime.now(timezone.utc)
            await session.flush()

            # Write history
            await ComplaintRepository.add_status_history(
                session,
                complaint_id=complaint.id,
                previous_status=previous,
                new_status=target,
                updated_by=current_user.id,
                remarks=payload.remarks,
            )

            # Notify student
            await NotificationService.send(
                session,
                user_id=complaint.created_by,
                complaint_id=complaint.id,
                message=(
                    f"Your complaint '{complaint.title}' has been scheduled. "
                    f"Worker: {payload.worker_name} ({payload.worker_type.value}), "
                    f"Visit Date: {payload.scheduled_date}."
                ),
            )

            await session.refresh(complaint)
            return complaint

        # ----------------------------------------------------------------
        # COMPLETED transition — create completion slip, auto-transition to
        # WAITING_STUDENT_CONFIRMATION
        # ----------------------------------------------------------------
        if target == ComplaintStatus.COMPLETED:
            if not payload.work_done:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="work_done is required when marking a complaint as completed.",
                )

            # Fetch assignment to get worker info
            assignment = await AssignmentRepository.get_by_complaint_id(
                session, complaint_id
            )
            if assignment is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Cannot mark complaint as completed: no worker assignment found. "
                        "Please schedule the complaint first."
                    ),
                )

            # Create completion slip
            await CompletionSlipRepository.create(
                session,
                complaint_id=complaint_id,
                hall_id=complaint.hall_id,
                room_number=complaint.room_number,
                worker_name=assignment.worker_name,
                worker_type=assignment.worker_type,
                work_done=payload.work_done,
                admin_remarks=payload.admin_remarks or payload.remarks,
            )

            # Write history: IN_PROGRESS → COMPLETED
            await ComplaintRepository.add_status_history(
                session,
                complaint_id=complaint.id,
                previous_status=previous,
                new_status=ComplaintStatus.COMPLETED,
                updated_by=current_user.id,
                remarks=payload.remarks,
            )

            # Auto-transition to WAITING_STUDENT_CONFIRMATION
            complaint.status = ComplaintStatus.WAITING_STUDENT_CONFIRMATION
            complaint.updated_at = datetime.now(timezone.utc)
            await session.flush()

            # Write history: COMPLETED → WAITING_STUDENT_CONFIRMATION
            await ComplaintRepository.add_status_history(
                session,
                complaint_id=complaint.id,
                previous_status=ComplaintStatus.COMPLETED,
                new_status=ComplaintStatus.WAITING_STUDENT_CONFIRMATION,
                updated_by=current_user.id,
                remarks="Auto-transition: awaiting student confirmation.",
            )

            # Notify student
            await NotificationService.send(
                session,
                user_id=complaint.created_by,
                complaint_id=complaint.id,
                message=(
                    f"The repair for your complaint '{complaint.title}' has been completed. "
                    "Please confirm or reject the repair from your dashboard."
                ),
            )

            await session.refresh(complaint)
            return complaint

        # ----------------------------------------------------------------
        # CLOSED transition — check student confirmed
        # ----------------------------------------------------------------
        if target == ComplaintStatus.CLOSED:
            slip = await CompletionSlipRepository.get_by_complaint_id(
                session, complaint_id
            )
            if slip is None or slip.student_confirmation_status != StudentConfirmationStatus.CONFIRMED.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Complaint cannot be closed: student confirmation is still "
                        "pending or rejected. Please wait for the student to confirm the repair."
                    ),
                )

        # ----------------------------------------------------------------
        # Default path for all other transitions
        # ----------------------------------------------------------------
        complaint.status = target
        complaint.updated_at = datetime.now(timezone.utc)
        await session.flush()

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
    # Student: Confirm Repair
    # ------------------------------------------------------------------

    @staticmethod
    async def confirm_repair(
        session: AsyncSession,
        complaint_id: str,
        current_user: "User",
        comment: str | None = None,
    ) -> Complaint:
        """
        Student confirms that the repair was completed satisfactorily.
        Updates the completion slip; notifies the hall admin.
        """
        complaint = await ComplaintService.get_or_404(session, complaint_id)

        if complaint.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to confirm this complaint.",
            )

        if complaint.status != ComplaintStatus.WAITING_STUDENT_CONFIRMATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot confirm repair: complaint is not awaiting confirmation "
                    f"(current status: '{complaint.status.value}')."
                ),
            )

        slip = await CompletionSlipRepository.get_by_complaint_id(session, complaint_id)
        if slip is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Completion slip not found for this complaint.",
            )

        # Update completion slip
        await CompletionSlipRepository.update(
            session,
            slip,
            student_confirmation_status=StudentConfirmationStatus.CONFIRMED.value,
            student_comment=comment,
            student_confirmation_time=datetime.now(timezone.utc),
        )

        # Write status history (complaint stays at WAITING_STUDENT_CONFIRMATION
        # until admin explicitly closes it)
        await ComplaintRepository.add_status_history(
            session,
            complaint_id=complaint.id,
            previous_status=complaint.status,
            new_status=complaint.status,
            updated_by=current_user.id,
            remarks=f"Student confirmed repair. Comment: {comment}" if comment else "Student confirmed repair.",
        )

        # Notify all Hall Admins of this hall
        # A hall may have multiple admins — notify every one of them.
        admin_result = await session.execute(
            select(User).where(
                User.hall_id == complaint.hall_id,
                User.role == UserRole.HALL_ADMIN,
            )
        )
        admins = admin_result.scalars().all()
        for admin in admins:
            await NotificationService.send(
                session,
                user_id=admin.id,
                complaint_id=complaint.id,
                message=(
                    f"Student confirmed the repair for complaint '{complaint.title}'. "
                    f"You can now close the complaint."
                    + (f" Student comment: {comment}" if comment else "")
                ),
            )

        await session.refresh(complaint)
        return complaint

    # ------------------------------------------------------------------
    # Student: Reject Repair
    # ------------------------------------------------------------------

    @staticmethod
    async def reject_repair(
        session: AsyncSession,
        complaint_id: str,
        current_user: "User",
        comment: str,
    ) -> Complaint:
        """
        Student rejects the repair — complaint is reopened and returned to verified.
        Updates the completion slip; notifies the hall admin.
        """
        if not comment or not comment.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A comment is required when rejecting a repair.",
            )

        complaint = await ComplaintService.get_or_404(session, complaint_id)

        if complaint.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to reject this complaint.",
            )

        if complaint.status != ComplaintStatus.WAITING_STUDENT_CONFIRMATION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot reject repair: complaint is not awaiting confirmation "
                    f"(current status: '{complaint.status.value}')."
                ),
            )

        slip = await CompletionSlipRepository.get_by_complaint_id(session, complaint_id)
        if slip is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Completion slip not found for this complaint.",
            )

        # Update completion slip
        await CompletionSlipRepository.update(
            session,
            slip,
            student_confirmation_status=StudentConfirmationStatus.REJECTED.value,
            student_comment=comment,
            student_confirmation_time=datetime.now(timezone.utc),
        )

        # Write history: WAITING → REOPENED
        await ComplaintRepository.add_status_history(
            session,
            complaint_id=complaint.id,
            previous_status=ComplaintStatus.WAITING_STUDENT_CONFIRMATION,
            new_status=ComplaintStatus.REOPENED,
            updated_by=current_user.id,
            remarks=f"Student rejected repair: {comment}",
        )

        # Write history: REOPENED → VERIFIED
        await ComplaintRepository.add_status_history(
            session,
            complaint_id=complaint.id,
            previous_status=ComplaintStatus.REOPENED,
            new_status=ComplaintStatus.VERIFIED,
            updated_by=current_user.id,
            remarks="Complaint reopened and returned to verified for re-scheduling.",
        )

        # Apply final status
        complaint.status = ComplaintStatus.VERIFIED
        complaint.updated_at = datetime.now(timezone.utc)
        await session.flush()

        # Notify all Hall Admins of this hall
        # A hall may have multiple admins — notify every one of them.
        admin_result = await session.execute(
            select(User).where(
                User.hall_id == complaint.hall_id,
                User.role == UserRole.HALL_ADMIN,
            )
        )
        admins = admin_result.scalars().all()
        for admin in admins:
            await NotificationService.send(
                session,
                user_id=admin.id,
                complaint_id=complaint.id,
                message=(
                    f"Student rejected the repair for complaint '{complaint.title}'. "
                    f"Complaint has been reopened and returned to Verified. "
                    f"Student comment: {comment}"
                ),
            )

        await session.refresh(complaint)
        return complaint

    # ------------------------------------------------------------------
    # Get Completion Slip
    # ------------------------------------------------------------------

    @staticmethod
    async def get_completion_slip(
        session: AsyncSession,
        complaint_id: str,
        current_user: "User",
    ) -> "CompletionSlip":
        """
        Fetch the completion slip for a complaint.
        Only accessible by the complaint creator or hall admin.
        """
        complaint = await ComplaintService.get_or_404(session, complaint_id)

        # Check access
        if current_user.role == UserRole.HALL_ADMIN:
            if complaint.hall_id != current_user.hall_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only access completion slips from your own hall.",
                )
        else:
            if complaint.created_by != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view this completion slip.",
                )

        slip = await CompletionSlipRepository.get_by_complaint_id(session, complaint_id)
        if slip is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Completion slip not found for this complaint.",
            )
        return slip

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
        """Partially update complaint fields (admin only, own hall)."""
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
