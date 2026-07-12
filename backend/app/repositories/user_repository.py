"""
IntelliHall — User Repository

Handles all database operations for the User model.
Contains NO business logic — that lives in the service layer.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import HallVerificationStatus, UserRole
from app.models.user import User


class UserRepository:
    """Data-access object for the ``users`` table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    async def get_by_email(self, email: str) -> User | None:
        """Return the User with the given *email*, or None if not found."""
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()

    async def get_by_id(self, user_id: str) -> User | None:
        """Return the User with the given *user_id*, or None if not found."""
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalars().first()

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def create(self, user: User) -> User:
        """
        Persist a new *user* row and return the refreshed instance.

        The caller is responsible for constructing the User object with all
        required fields already set (including the hashed password).
        """
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def save(self, user: User) -> User:
        """Flush changes to an already-attached *user* instance and return it."""
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    # ------------------------------------------------------------------
    # Verification queries
    # ------------------------------------------------------------------

    async def list_pending_for_hall(
        self,
        hall_id: str,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[User], int]:
        """
        Return paginated students whose hall affiliation is PENDING for
        the given *hall_id*.

        Returns:
            (list[User], total_count)
        """
        base_query = (
            select(User)
            .where(
                User.hall_id == hall_id,
                User.role == UserRole.STUDENT,                      # admins never in queue
                User.hall_verification_status == HallVerificationStatus.PENDING,
            )
            .order_by(User.updated_at.asc())
        )

        count_result = await self._session.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar_one()

        rows_result = await self._session.execute(
            base_query.offset((page - 1) * page_size).limit(page_size)
        )
        users = list(rows_result.scalars().all())

        return users, total

    async def approve_verification(
        self,
        user_id: str,
        admin_id: str,
    ) -> User | None:
        """
        Set ``hall_verification_status = APPROVED`` for *user_id*.
        Records ``verified_by_admin_id`` and ``hall_verified_at``.
        Clears any previous rejection reason.

        Returns the updated User or None if not found.
        """
        result = await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                hall_verification_status=HallVerificationStatus.APPROVED,
                verified_by_admin_id=admin_id,
                hall_verified_at=datetime.now(timezone.utc),
                hall_rejection_reason=None,
            )
            .returning(User)
        )
        await self._session.commit()
        return result.scalars().first()

    async def reject_verification(
        self,
        user_id: str,
        admin_id: str,
        reason: str | None = None,
    ) -> User | None:
        """
        Set ``hall_verification_status = REJECTED`` for *user_id*.
        Optionally stores a *reason* visible to the student.

        Returns the updated User or None if not found.
        """
        result = await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                hall_verification_status=HallVerificationStatus.REJECTED,
                verified_by_admin_id=admin_id,
                hall_verified_at=datetime.now(timezone.utc),
                hall_rejection_reason=reason,
            )
            .returning(User)
        )
        await self._session.commit()
        return result.scalars().first()

    async def update_hall(
        self,
        user_id: str,
        new_hall_id: str,
        room_number: str | None = None,
    ) -> User | None:
        """
        Change the student's hall affiliation and reset verification to PENDING.

        Existing complaints are unaffected — they retain the hall_id under
        which they were originally created.

        Returns the updated User or None if not found.
        """
        values: dict = {
            "hall_id": new_hall_id,
            "hall_verification_status": HallVerificationStatus.PENDING,
            "verified_by_admin_id": None,
            "hall_verified_at": None,
            "hall_rejection_reason": None,
        }
        if room_number is not None:
            values["room_number"] = room_number

        result = await self._session.execute(
            update(User)
            .where(User.id == user_id)
            .values(**values)
            .returning(User)
        )
        await self._session.commit()
        return result.scalars().first()

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @staticmethod
    def total_pages(total: int, page_size: int) -> int:
        """Return the number of pages for a given *total* and *page_size*."""
        return max(1, math.ceil(total / page_size))
