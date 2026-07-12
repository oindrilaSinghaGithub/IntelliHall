"""
IntelliHall — Notification ORM Model

In-app notifications for students and admins.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.complaint import Complaint


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _generate_uuid() -> str:
    return str(uuid.uuid4())


class Notification(Base):
    """
    In-app notification for a user.
    
    Note: Uses Base instead of TimestampedBase because we only need created_at,
    not updated_at. Notifications are immutable after creation.
    """

    __tablename__ = "notifications"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=_generate_uuid,
        comment="UUID primary key.",
    )

    # ------------------------------------------------------------------
    # Foreign keys
    # ------------------------------------------------------------------

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to the user who should see this notification.",
    )

    complaint_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("complaints.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional FK to the related complaint.",
    )

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The notification message text.",
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether the user has read this notification.",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
        comment="UTC timestamp when notification was created.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="selectin",
    )

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Notification id={self.id!r} "
            f"user_id={self.user_id!r} "
            f"is_read={self.is_read}>"
        )
