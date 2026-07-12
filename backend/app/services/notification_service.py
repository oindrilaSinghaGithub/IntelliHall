"""
IntelliHall — Notification Service

Sends in-app notifications. All exceptions are caught and logged so that
notification failures never abort the main transaction.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending in-app notifications."""

    @staticmethod
    async def send(
        session: AsyncSession,
        *,
        user_id: str,
        message: str,
        complaint_id: str | None = None,
    ) -> None:
        """
        Create a notification record for a user.
        
        Failures are caught and logged — they must never roll back
        the main complaint status transaction.
        """
        try:
            await NotificationRepository.create(
                session,
                user_id=user_id,
                message=message,
                complaint_id=complaint_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to create notification for user %s: %s",
                user_id,
                exc,
            )
