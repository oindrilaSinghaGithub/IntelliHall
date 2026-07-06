"""
IntelliHall — Hall Repository

Handles all database operations for the Hall model.
Contains NO business logic — that lives in the service layer.

Public API
----------
HallRepository.get_by_id(session, hall_id)          -> Hall | None
HallRepository.get_by_name(session, name)            -> Hall | None
HallRepository.get_by_code(session, code)            -> Hall | None
HallRepository.list_all(session)                     -> list[Hall]
HallRepository.create(session, data)                 -> Hall
HallRepository.update(session, hall, data)           -> Hall
HallRepository.delete(session, hall)                 -> None
HallRepository.assign_user(session, user, hall_id)   -> User
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hall import Hall
from app.models.user import User
from app.schemas.hall import HallCreate, HallUpdate


class HallRepository:
    """Data-access object for the ``halls`` table."""

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @staticmethod
    async def get_by_id(session: AsyncSession, hall_id: str) -> Hall | None:
        """Return the Hall with the given *hall_id*, or None."""
        result = await session.execute(select(Hall).where(Hall.id == hall_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(session: AsyncSession, name: str) -> Hall | None:
        """Return the Hall with the given *name* (case-sensitive), or None."""
        result = await session.execute(select(Hall).where(Hall.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_code(session: AsyncSession, code: str) -> Hall | None:
        """Return the Hall with the given *code* (case-sensitive), or None."""
        result = await session.execute(select(Hall).where(Hall.code == code))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_all(session: AsyncSession) -> list[Hall]:
        """Return every Hall ordered alphabetically by name."""
        result = await session.execute(select(Hall).order_by(Hall.name))
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    @staticmethod
    async def create(session: AsyncSession, data: HallCreate) -> Hall:
        """Persist a new Hall and return the refreshed instance."""
        hall = Hall(name=data.name, code=data.code.upper())
        session.add(hall)
        await session.commit()
        await session.refresh(hall)
        return hall

    @staticmethod
    async def update(session: AsyncSession, hall: Hall, data: HallUpdate) -> Hall:
        """
        Apply non-None fields from *data* onto *hall*.

        Code values are automatically uppercased for consistency.
        """
        if data.name is not None:
            hall.name = data.name
        if data.code is not None:
            hall.code = data.code.upper()
        hall.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(hall)
        return hall

    @staticmethod
    async def delete(session: AsyncSession, hall: Hall) -> None:
        """Hard-delete the hall (cascades to users and complaints at DB level)."""
        await session.delete(hall)
        await session.commit()

    @staticmethod
    async def assign_user(
        session: AsyncSession,
        user: User,
        hall_id: str | None,
    ) -> User:
        """
        Set *user.hall_id* to *hall_id* (or None to unassign).

        The caller is responsible for verifying the hall exists before calling
        this method.
        """
        user.hall_id = hall_id
        user.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(user)
        return user
