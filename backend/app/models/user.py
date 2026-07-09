"""
IntelliHall — User ORM Model

Represents a system user — either a student living in a hall or a hall
administrator.  Every user must belong to exactly one Hall.
"""

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase
from app.models.enums import UserRole

if TYPE_CHECKING:
    from app.models.complaint import Complaint, ComplaintStatusHistory
    from app.models.hall import Hall


class User(TimestampedBase):
    """A platform user (student or hall administrator)."""

    __tablename__ = "users"

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Full display name of the user.",
    )

    email: Mapped[str] = mapped_column(
        String(320),   # RFC 5321 maximum email length
        nullable=False,
        unique=True,
        index=True,
        comment="Unique login e-mail address.",
    )

    password_hash: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        comment="Bcrypt / argon2 hashed password — never store plaintext.",
    )

    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            name="userrole",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=UserRole.STUDENT,
        index=True,
        comment="Role of the user within the system.",
    )

    hall_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("halls.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK to the hall this user belongs to.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    hall: Mapped["Hall"] = relationship(
        "Hall",
        back_populates="users",
        lazy="selectin",
    )

    complaints_created: Mapped[list["Complaint"]] = relationship(
        "Complaint",
        foreign_keys="Complaint.created_by",
        back_populates="creator",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    status_updates: Mapped[list["ComplaintStatusHistory"]] = relationship(
        "ComplaintStatusHistory",
        foreign_keys="ComplaintStatusHistory.updated_by",
        back_populates="actor",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def hall_name(self) -> str | None:
        """Return the readable name of the user's assigned residential hall."""
        return self.hall.name if self.hall else None

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<User id={self.id!r} email={self.email!r} role={self.role.value!r}>"
        )
