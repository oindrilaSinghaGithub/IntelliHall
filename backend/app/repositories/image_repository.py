"""
IntelliHall — Image Repository

Responsible exclusively for database access to complaint images.
Contains no business logic, HTTP concerns, or exception handling beyond
letting SQLAlchemy exceptions propagate naturally to the service layer.

Public API
----------
ImageRepository.create(session, complaint_id, image_url)  -> ComplaintImage
ImageRepository.get_by_id(session, image_id)              -> ComplaintImage | None
ImageRepository.count_for_complaint(session, complaint_id) -> int
ImageRepository.delete(session, image)                    -> None
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.complaint import ComplaintImage


class ImageRepository:
    """Pure database-access layer for ComplaintImage records."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    async def create(
        session: AsyncSession,
        complaint_id: str,
        image_url: str,
    ) -> ComplaintImage:
        """
        Insert a new ComplaintImage record and return the refreshed instance.

        The ``uploaded_at`` field is populated automatically by the model default.
        """
        image = ComplaintImage(
            complaint_id=complaint_id,
            image_url=image_url,
        )
        session.add(image)
        await session.flush()
        await session.refresh(image)
        return image

    # ------------------------------------------------------------------
    # Read — single
    # ------------------------------------------------------------------

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        image_id: str,
    ) -> ComplaintImage | None:
        """Return an image by its UUID with the complaint relationship loaded, or None."""
        result = await session.execute(
            select(ComplaintImage)
            .options(joinedload(ComplaintImage.complaint))
            .where(ComplaintImage.id == image_id)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Read — count
    # ------------------------------------------------------------------

    @staticmethod
    async def count_for_complaint(
        session: AsyncSession,
        complaint_id: str,
    ) -> int:
        """Count existing images attached to a complaint."""
        result = await session.execute(
            select(func.count())
            .select_from(ComplaintImage)
            .where(ComplaintImage.complaint_id == complaint_id)
        )
        return result.scalar_one()

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @staticmethod
    async def delete(
        session: AsyncSession,
        image: ComplaintImage,
    ) -> None:
        """Hard-delete the image record."""
        await session.delete(image)
        await session.flush()
