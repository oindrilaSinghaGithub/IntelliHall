"""
IntelliHall — Notification Repository

Pure database access for Notification records.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NotificationRepository:
    """Database access layer for Notification."""

    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        user_id: str,
        message: str,
        complaint_id: str | None = None,
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=user_id,
            complaint_id=complaint_id,
            message=message,
        )
        session.add(notification)
        await session.flush()
        await session.refresh(notification)
        return notification

    @staticmethod
    async def list_for_user(
        session: AsyncSession,
        user_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
    ) -> tuple[list[Notification], int]:
        """
        Paginated list of notifications for a user.
        Returns (items, total_count).
        """
        base_where = [Notification.user_id == user_id]
        if unread_only:
            base_where.append(Notification.is_read == False)  # noqa: E712

        count_stmt = (
            select(func.count())
            .select_from(Notification)
            .where(*base_where)
        )
        total: int = (await session.execute(count_stmt)).scalar_one()

        data_stmt = (
            select(Notification)
            .where(*base_where)
            .order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list((await session.execute(data_stmt)).scalars().all())
        return items, total

    @staticmethod
    async def get_unread_count(
        session: AsyncSession,
        user_id: str,
    ) -> int:
        """Return the number of unread notifications for a user."""
        result = await session.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
        )
        return result.scalar_one()

    @staticmethod
    async def mark_read(
        session: AsyncSession,
        notification_id: str,
        user_id: str,
    ) -> Notification | None:
        """Mark a single notification as read (only if it belongs to user)."""
        result = await session.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = result.scalar_one_or_none()
        if notification:
            notification.is_read = True
            await session.flush()
            await session.refresh(notification)
        return notification

    @staticmethod
    async def mark_all_read(
        session: AsyncSession,
        user_id: str,
    ) -> int:
        """Mark all notifications as read for a user. Returns count updated."""
        result = await session.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .values(is_read=True)
        )
        return result.rowcount  # type: ignore[return-value]
