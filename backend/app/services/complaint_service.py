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
from app.models.complaint import Complaint, CommonAreaAffected
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
    # VISIT_FAILED_ROOM_LOCKED:
    #   VERIFIED  — admin re-verifies and re-schedules manually
    #   SCHEDULED — student self-reschedules via POST /reschedule (new workflow)
    ComplaintStatus.VISIT_FAILED_ROOM_LOCKED: {
        ComplaintStatus.VERIFIED,
        ComplaintStatus.SCHEDULED,
    },
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

        # ------------------------------------------------------------------
        # AI Priority Prediction
        # Runs after all validation passes; never overwrites student's choice.
        # ------------------------------------------------------------------
        from app.ai import PriorityPredictor  # local import keeps startup fast

        prediction = PriorityPredictor().predict(
            title=data.title,
            description=data.description,
        )
        predicted_priority = prediction["priority"]
        ai_confidence = prediction["confidence"]

        # ------------------------------------------------------------------
        # AI Worker Recommendation
        # Runs at creation time to populate initial recommendations.
        # ------------------------------------------------------------------
        recommended_worker_id = None
        recommendation_score = None
        recommendation_reason = None
        try:
            from app.ai import WorkerRecommender
            from app.repositories import WorkerRepository

            hall_workers = await WorkerRepository.list_all_in_hall(session, current_user.hall_id)
            rec = WorkerRecommender().recommend_worker(
                category=data.category,
                title=data.title,
                description=data.description,
                predicted_priority=predicted_priority,
                workers=hall_workers,
            )
            recommended_worker = rec["recommended_worker"]
            recommended_worker_id = recommended_worker.id if recommended_worker else None
            recommendation_score = rec["recommendation_score"]
            recommendation_reason = rec["recommendation_reason"]
        except Exception as e:
            recommendation_reason = f"Recommendation engine unavailable: {str(e)}"

        return await ComplaintRepository.create(
            session,
            data,
            user_id=current_user.id,
            hall_id=current_user.hall_id,
            predicted_priority=predicted_priority,
            ai_confidence=ai_confidence,
            recommended_worker_id=recommended_worker_id,
            recommendation_score=recommendation_score,
            recommendation_reason=recommendation_reason,
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
        """Fetch a complaint for a student, enforcing ownership or hall common area visibility."""
        complaint = await ComplaintService.get_or_404(session, complaint_id)
        if complaint.complaint_type == ComplaintType.COMMON_AREA:
            if complaint.hall_id != current_user.hall_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view common area complaints from another hall.",
                )
        else:
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
        """Return a paginated list of the student's own complaints or all hall common area complaints."""
        if filters.complaint_type == ComplaintType.COMMON_AREA:
            items, total = await ComplaintRepository.list(
                session,
                hall_id=current_user.hall_id,
                status=filters.status,
                priority=filters.priority,
                category=filters.category,
                complaint_type=ComplaintType.COMMON_AREA,
                page=filters.page,
                page_size=filters.page_size,
                sort_by=filters.sort_by,
                sort_order=filters.sort_order,
            )
        else:
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
        
        summaries = []
        for c in items:
            summary = ComplaintSummary.model_validate(c)
            summary.is_affected = any(entry.user_id == current_user.id for entry in c.affected_entries)
            if c.creator.room_number:
                summary.reporter_room = f"Room {c.creator.room_number}"
            else:
                summary.reporter_room = "Anonymous Student"
            summaries.append(summary)

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
        summaries = []
        for c in items:
            summary = ComplaintSummary.model_validate(c)
            summary.is_affected = any(entry.user_id == current_user.id for entry in c.affected_entries)
            if c.creator.room_number:
                summary.reporter_room = f"Room {c.creator.room_number}"
            else:
                summary.reporter_room = "Anonymous Student"
            summaries.append(summary)

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

        # Notify student when their visit fails due to a locked room so they
        # know to reschedule.
        if target == ComplaintStatus.VISIT_FAILED_ROOM_LOCKED:
            await NotificationService.send(
                session,
                user_id=complaint.created_by,
                complaint_id=complaint.id,
                message=(
                    f"Your maintenance visit for complaint '{complaint.title}' could not "
                    "be completed because your room was locked. "
                    "Please choose another visit time."
                ),
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

        # Process force_recompute_recommendation custom field
        force_recompute = data.force_recompute_recommendation
        data.force_recompute_recommendation = None

        if not data.model_dump(exclude_none=True) and not force_recompute:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update.",
            )

        # Handle assigned_worker_id update
        if data.assigned_worker_id is not None:
            if data.assigned_worker_id == "":
                complaint.assigned_worker_id = None
                complaint.current_assignee = None
                data.assigned_worker_id = None
            else:
                from app.repositories.worker_repository import WorkerRepository
                worker = await WorkerRepository.get_by_id(session, data.assigned_worker_id)
                if not worker or worker.hall_id != complaint.hall_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Worker not found or does not belong to this hall.",
                    )
                complaint.assigned_worker_id = worker.id
                complaint.current_assignee = worker.name
                
                from app.models.enums import WorkerSpecialization, MaintenanceType
                _SPEC_TO_MAINT = {
                    WorkerSpecialization.ELECTRICIAN: MaintenanceType.ELECTRICIAN,
                    WorkerSpecialization.PLUMBER: MaintenanceType.PLUMBER,
                    WorkerSpecialization.CARPENTER: MaintenanceType.CARPENTER,
                    WorkerSpecialization.CLEANING_STAFF: MaintenanceType.CLEANING_STAFF,
                    WorkerSpecialization.NETWORK_STAFF: MaintenanceType.ELECTRICIAN,
                    WorkerSpecialization.CIVIL_MAINTENANCE: MaintenanceType.CIVIL,
                }
                complaint.maintenance_type = _SPEC_TO_MAINT.get(worker.specialization, MaintenanceType.ELECTRICIAN)
                data.assigned_worker_id = worker.id

        # Re-run priority predictor and worker recommender if fields change OR forced
        title_changed = data.title is not None and data.title != complaint.title
        desc_changed = data.description is not None and data.description != complaint.description
        cat_changed = data.category is not None and data.category != complaint.category
        
        should_recompute = force_recompute or (
            (title_changed or desc_changed or cat_changed) and complaint.assigned_worker_id is None
        )

        if should_recompute:
            # Re-predict priority
            from app.ai import PriorityPredictor
            new_title = data.title if data.title is not None else complaint.title
            new_desc = data.description if data.description is not None else complaint.description
            prediction = PriorityPredictor().predict(title=new_title, description=new_desc)
            complaint.predicted_priority = prediction["priority"]
            complaint.ai_confidence = prediction["confidence"]
            
            # Re-run recommendation
            try:
                from app.ai import WorkerRecommender
                from app.repositories.worker_repository import WorkerRepository
                new_cat = data.category if data.category is not None else complaint.category
                hall_workers = await WorkerRepository.list_all_in_hall(session, complaint.hall_id)
                
                rec = WorkerRecommender().recommend_worker(
                    category=new_cat,
                    title=new_title,
                    description=new_desc,
                    predicted_priority=complaint.predicted_priority,
                    workers=hall_workers,
                )
                recommended_worker = rec["recommended_worker"]
                complaint.recommended_worker_id = recommended_worker.id if recommended_worker else None
                complaint.recommendation_score = rec["recommendation_score"]
                complaint.recommendation_reason = rec["recommendation_reason"]
            except Exception as e:
                complaint.recommendation_reason = f"Recommendation engine unavailable: {str(e)}"

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

    # ------------------------------------------------------------------
    # Reschedule Visit (Student — own complaint, VISIT_FAILED_ROOM_LOCKED only)
    # ------------------------------------------------------------------

    @staticmethod
    async def reschedule_visit(
        session: AsyncSession,
        complaint_id: str,
        preferred_visit_time: datetime,
        current_user: "User",
    ) -> Complaint:
        """
        Allow a student to reschedule a maintenance visit after it failed
        because their room was locked.

        Rules
        -----
        - Only the complaint owner (student who created it) may call this.
        - Complaint must currently be VISIT_FAILED_ROOM_LOCKED.
        - preferred_visit_time must be in the future.
        - Transitions the complaint to SCHEDULED.
        - Preserves all existing history, images, and assignment records.
        - Writes a new ComplaintStatusHistory entry.
        - Sends notifications to the student (confirmation) and all hall admins.
        """
        complaint = await ComplaintService.get_or_404(session, complaint_id)

        # Ownership check
        if complaint.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to reschedule this complaint.",
            )

        # Status check
        if complaint.status != ComplaintStatus.VISIT_FAILED_ROOM_LOCKED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot reschedule: complaint must be in "
                    f"'visit_failed_room_locked' status "
                    f"(current status: '{complaint.status.value}')."
                ),
            )

        # Future-time validation
        now_utc = datetime.now(timezone.utc)
        # Make preferred_visit_time timezone-aware for comparison if it is naive
        pvt = preferred_visit_time
        if pvt.tzinfo is None:
            pvt = pvt.replace(tzinfo=timezone.utc)
        if pvt <= now_utc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="preferred_visit_time must be a future date and time.",
            )

        previous = complaint.status

        # Apply changes — preserve everything else
        complaint.preferred_visit_time = pvt
        complaint.status = ComplaintStatus.SCHEDULED
        complaint.updated_at = now_utc
        await session.flush()

        # Audit trail
        await ComplaintRepository.add_status_history(
            session,
            complaint_id=complaint.id,
            previous_status=previous,
            new_status=ComplaintStatus.SCHEDULED,
            updated_by=current_user.id,
            remarks="Student rescheduled visit after room-locked failure.",
        )

        # Notify student — confirmation that rescheduling was received
        await NotificationService.send(
            session,
            user_id=complaint.created_by,
            complaint_id=complaint.id,
            message=(
                f"Your maintenance visit for complaint '{complaint.title}' has been "
                "rescheduled. The hall admin will confirm a new visit slot."
            ),
        )

        # Notify all hall admins
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
                    f"The student has requested a new maintenance visit "
                    f"for complaint '{complaint.title}'."
                ),
            )

        await session.refresh(complaint)
        return complaint

    @staticmethod
    async def mark_affected(
        session: AsyncSession,
        complaint_id: str,
        current_user: "User",
    ) -> dict[str, object]:
        """Mark the authenticated student as affected by a common area complaint (idempotent)."""
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can mark themselves as affected by common area complaints.",
            )

        complaint = await ComplaintService.get_or_404(session, complaint_id)

        if complaint.complaint_type != ComplaintType.COMMON_AREA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Community impact can only be marked on common area complaints.",
            )

        if complaint.hall_id != current_user.hall_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot mark yourself affected by complaints from another hall.",
            )

        if complaint.status == ComplaintStatus.CLOSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Closed complaints cannot receive new affected responses.",
            )

        # Check if already marked
        result = await session.execute(
            select(CommonAreaAffected).where(
                CommonAreaAffected.complaint_id == complaint_id,
                CommonAreaAffected.user_id == current_user.id,
            )
        )
        existing = result.scalar_one_or_none()

        if not existing:
            new_affected = CommonAreaAffected(
                complaint_id=complaint_id,
                user_id=current_user.id,
            )
            session.add(new_affected)
            await session.flush()
            await session.refresh(complaint)

        return {
            "affected_count": complaint.affected_count,
            "is_affected": True,
        }

    @staticmethod
    async def remove_affected(
        session: AsyncSession,
        complaint_id: str,
        current_user: "User",
    ) -> dict[str, object]:
        """Remove the authenticated student from being affected by a common area complaint."""
        if current_user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can toggle affected status.",
            )

        complaint = await ComplaintService.get_or_404(session, complaint_id)

        if complaint.complaint_type != ComplaintType.COMMON_AREA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Community impact can only be removed from common area complaints.",
            )

        if complaint.hall_id != current_user.hall_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot interact with complaints from another hall.",
            )

        # Check if marked
        result = await session.execute(
            select(CommonAreaAffected).where(
                CommonAreaAffected.complaint_id == complaint_id,
                CommonAreaAffected.user_id == current_user.id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            await session.delete(existing)
            await session.flush()
            await session.refresh(complaint)

        return {
            "affected_count": complaint.affected_count,
            "is_affected": False,
        }

