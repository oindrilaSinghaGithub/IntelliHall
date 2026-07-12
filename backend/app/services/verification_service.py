"""
IntelliHall — Verification Service

Business logic for the Hall Verification workflow.

Public API
----------
VerificationService.list_pending(hall_id, admin, page, page_size, session)
    Returns paginated pending requests for the admin's hall.

VerificationService.approve(user_id, admin, session)
    Approves a student's hall affiliation.

VerificationService.reject(user_id, admin, reason, session)
    Rejects a student's hall affiliation with an optional reason.

VerificationService.change_hall(user_id, new_hall_id, room_number, session)
    Changes the student's hall and resets verification to PENDING.
    Called from the student's own PATCH /users/me/hall endpoint.

Authorization
-------------
- Only HALL_ADMIN may approve/reject.
- The admin may only action students from their own hall.
- Students call change_hall on themselves only (enforced by the route layer).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import HallVerificationStatus, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.verification import (
    PaginatedVerificationResponse,
    VerificationRequestRead,
)

if TYPE_CHECKING:
    from app.models.user import User


class VerificationService:
    """Business-logic layer for the Hall Verification domain."""

    # ------------------------------------------------------------------
    # List pending (admin)
    # ------------------------------------------------------------------

    @staticmethod
    async def list_pending(
        session: AsyncSession,
        current_admin: "User",
        page: int = 1,
        page_size: int = 25,
    ) -> PaginatedVerificationResponse:
        """
        Return paginated PENDING verification requests for the admin's hall.

        Raises HTTP 403 if caller is not a HALL_ADMIN.
        Raises HTTP 403 if the admin has no hall assigned.
        """
        if current_admin.role != UserRole.HALL_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Hall Admins can view verification requests.",
            )
        if not current_admin.hall_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your admin account is not assigned to a hall.",
            )

        repo = UserRepository(session)
        users, total = await repo.list_pending_for_hall(
            hall_id=current_admin.hall_id,
            page=page,
            page_size=page_size,
        )
        total_pages = UserRepository.total_pages(total, page_size)

        return PaginatedVerificationResponse(
            items=[VerificationRequestRead.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # ------------------------------------------------------------------
    # Approve (admin)
    # ------------------------------------------------------------------

    @staticmethod
    async def approve(
        session: AsyncSession,
        user_id: str,
        current_admin: "User",
    ) -> VerificationRequestRead:
        """
        Approve a student's hall affiliation.

        Raises HTTP 403 if caller is not a HALL_ADMIN.
        Raises HTTP 404 if the student does not exist.
        Raises HTTP 403 if the student belongs to a different hall.
        Raises HTTP 409 if the student is already approved.
        """
        if current_admin.role != UserRole.HALL_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Hall Admins can approve verification requests.",
            )

        repo = UserRepository(session)
        student = await repo.get_by_id(user_id)
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found.",
            )

        if student.hall_id != current_admin.hall_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only approve students from your own hall.",
            )

        if student.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Hall verification applies only to student accounts.",
            )

        if student.hall_verification_status == HallVerificationStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This student's hall affiliation is already approved.",
            )

        updated = await repo.approve_verification(
            user_id=user_id,
            admin_id=current_admin.id,
        )
        return VerificationRequestRead.model_validate(updated)

    # ------------------------------------------------------------------
    # Reject (admin)
    # ------------------------------------------------------------------

    @staticmethod
    async def reject(
        session: AsyncSession,
        user_id: str,
        current_admin: "User",
        reason: str | None = None,
    ) -> VerificationRequestRead:
        """
        Reject a student's hall affiliation.

        Raises HTTP 403 if caller is not a HALL_ADMIN.
        Raises HTTP 404 if the student does not exist.
        Raises HTTP 403 if the student belongs to a different hall.
        Raises HTTP 409 if the student is already in a terminal rejected state
                        and was not changed since.
        """
        if current_admin.role != UserRole.HALL_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Hall Admins can reject verification requests.",
            )

        repo = UserRepository(session)
        student = await repo.get_by_id(user_id)
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found.",
            )

        if student.hall_id != current_admin.hall_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only reject students from your own hall.",
            )

        if student.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Hall verification applies only to student accounts.",
            )

        updated = await repo.reject_verification(
            user_id=user_id,
            admin_id=current_admin.id,
            reason=reason,
        )
        return VerificationRequestRead.model_validate(updated)

    # ------------------------------------------------------------------
    # Change hall (student)
    # ------------------------------------------------------------------

    @staticmethod
    async def change_hall(
        session: AsyncSession,
        user_id: str,
        new_hall_id: str,
        room_number: str | None = None,
    ) -> VerificationRequestRead:
        """
        Change the student's hall affiliation and reset verification to PENDING.

        Business rules:
        - The new hall must exist (validated by route layer via HallRepository).
        - Existing complaints are NOT moved — they keep the original hall_id.
        - Previous verification metadata (admin, timestamp, reason) is cleared.

        Raises HTTP 404 if the user cannot be found (should not happen in practice
        since route resolves the user first).
        """
        repo = UserRepository(session)
        updated = await repo.update_hall(
            user_id=user_id,
            new_hall_id=new_hall_id,
            room_number=room_number,
        )
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found.",
            )
        return VerificationRequestRead.model_validate(updated)
