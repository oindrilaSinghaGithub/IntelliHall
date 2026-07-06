"""
IntelliHall — User Repository

Handles all database operations for the User model.
Contains NO business logic — that lives in the service layer.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Data-access object for the ``users`` table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Queries
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
