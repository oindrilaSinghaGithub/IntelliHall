"""
IntelliHall — Hall Service

Sits between the API router and HallRepository.
All business logic, uniqueness validation, and exception mapping live here.
The router stays thin; the repository stays pure.

Public API
----------
HallService.create(session, data)                       -> Hall
HallService.get_or_404(session, hall_id)                -> Hall
HallService.list_all(session)                           -> list[Hall]
HallService.update(session, hall_id, data)              -> Hall
HallService.delete(session, hall_id)                    -> None
HallService.assign_user(session, hall_id, user_id)      -> User
HallService.unassign_user(session, user_id)             -> User
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hall import Hall
from app.models.user import User
from app.repositories.hall_repository import HallRepository
from app.repositories.user_repository import UserRepository
from app.schemas.hall import HallCreate, HallUpdate


class HallService:
    """Business-logic layer for the Hall domain."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    async def create(session: AsyncSession, data: HallCreate) -> Hall:
        """
        Create a new Hall after validating uniqueness constraints.

        Rules:
        - ``name`` must be unique (case-sensitive).
        - ``code`` must be unique (stored uppercased).

        Raises:
            HTTP 409 if name or code already exists.
        """
        if await HallRepository.get_by_name(session, data.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A hall named '{data.name}' already exists.",
            )
        if await HallRepository.get_by_code(session, data.code.upper()):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A hall with code '{data.code.upper()}' already exists.",
            )
        return await HallRepository.create(session, data)

    # ------------------------------------------------------------------
    # Read — single (with 404 guard)
    # ------------------------------------------------------------------

    @staticmethod
    async def get_or_404(session: AsyncSession, hall_id: str) -> Hall:
        """
        Fetch a Hall by ID, raising HTTP 404 if it does not exist.

        Centralising the 404 guard here keeps every endpoint handler
        to a single delegation call.
        """
        hall = await HallRepository.get_by_id(session, hall_id)
        if hall is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hall '{hall_id}' not found.",
            )
        return hall

    # ------------------------------------------------------------------
    # Read — list
    # ------------------------------------------------------------------

    @staticmethod
    async def list_all(session: AsyncSession) -> list[Hall]:
        """Return every Hall ordered alphabetically by name."""
        return await HallRepository.list_all(session)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    @staticmethod
    async def update(
        session: AsyncSession,
        hall_id: str,
        data: HallUpdate,
    ) -> Hall:
        """
        Partially update a Hall.

        Rules:
        - Raises HTTP 404 if the hall does not exist.
        - Raises HTTP 400 if no fields are provided.
        - Raises HTTP 409 if the new name or code conflicts with another hall.
        """
        hall = await HallService.get_or_404(session, hall_id)

        # Reject empty PATCH bodies
        if not data.model_dump(exclude_none=True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update.",
            )

        # Uniqueness: name must not belong to a *different* hall
        if data.name is not None:
            existing = await HallRepository.get_by_name(session, data.name)
            if existing and existing.id != hall_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A hall named '{data.name}' already exists.",
                )

        # Uniqueness: code must not belong to a *different* hall
        if data.code is not None:
            existing = await HallRepository.get_by_code(session, data.code.upper())
            if existing and existing.id != hall_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A hall with code '{data.code.upper()}' already exists.",
                )

        return await HallRepository.update(session, hall, data)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @staticmethod
    async def delete(session: AsyncSession, hall_id: str) -> None:
        """
        Hard-delete a Hall and cascade to its users/complaints at DB level.

        Raises HTTP 404 if the hall does not exist.
        """
        hall = await HallService.get_or_404(session, hall_id)
        await HallRepository.delete(session, hall)

    # ------------------------------------------------------------------
    # Assign user to hall
    # ------------------------------------------------------------------

    @staticmethod
    async def assign_user(
        session: AsyncSession,
        hall_id: str,
        user_id: str,
    ) -> User:
        """
        Assign *user_id* to *hall_id*.

        Rules:
        - Hall must exist (HTTP 404).
        - User must exist (HTTP 404).

        Returns the updated User.
        """
        # Verify hall exists
        await HallService.get_or_404(session, hall_id)

        # Verify user exists
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found.",
            )

        return await HallRepository.assign_user(session, user, hall_id)

    # ------------------------------------------------------------------
    # Unassign user from hall
    # ------------------------------------------------------------------

    @staticmethod
    async def unassign_user(
        session: AsyncSession,
        user_id: str,
    ) -> User:
        """
        Remove a user's hall assignment (sets hall_id to NULL).

        Rules:
        - User must exist (HTTP 404).

        Returns the updated User.
        """
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{user_id}' not found.",
            )

        return await HallRepository.assign_user(session, user, None)
