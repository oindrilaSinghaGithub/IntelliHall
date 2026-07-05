"""
IntelliHall — Hall ORM Model

Represents a residential hall/hostel in the system.
Each Hall can have many Users (students and admins) associated with it.
"""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase

if TYPE_CHECKING:
    from app.models.complaint import Complaint
    from app.models.user import User


class Hall(TimestampedBase):
    """A residential hall / hostel."""

    __tablename__ = "halls"

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Full display name of the hall (e.g. 'Tagore Hall').",
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        unique=True,
        index=True,
        comment="Short uppercase identifier for the hall (e.g. 'TH').",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="hall",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    complaints: Mapped[list["Complaint"]] = relationship(
        "Complaint",
        back_populates="hall",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Hall id={self.id!r} code={self.code!r} name={self.name!r}>"
