"""
IntelliHall — SQLAlchemy Declarative Base + Mixins

All ORM models should inherit from `Base`.
The `TimestampedBase` mixin adds:
  - id          : UUID primary key (auto-generated)
  - created_at  : UTC timestamp set on insert
  - updated_at  : UTC timestamp updated on every write
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Root SQLAlchemy declarative base for all models."""
    pass


class UUIDMixin:
    """Adds a UUID primary key column named `id`."""

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )


class TimestampMixin:
    """Adds `created_at` and `updated_at` timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )


class TimestampedBase(UUIDMixin, TimestampMixin, Base):
    """
    Convenience base combining UUID PK + timestamps.

    All IntelliHall domain models should inherit from this class:

        class User(TimestampedBase):
            __tablename__ = "users"
            ...
    """
    __abstract__ = True
