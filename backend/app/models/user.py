"""
IntelliHall — User ORM Model

Represents a system user — either a student living in a hall or a hall
administrator.  Every user must belong to exactly one Hall.

Hall Verification Workflow
--------------------------
When a student registers (or changes their hall), ``hall_verification_status``
is set to PENDING.  The corresponding Hall Admin must explicitly APPROVE or
REJECT the affiliation before the student can raise complaints.

Columns added for verification:
  roll_number              – Student roll number (display only; nullable)
  room_number              – Room at time of registration or last update
  hall_verification_status – pending | approved | rejected (default pending)
  verified_by_admin_id     – FK → users.id of the approving admin
  hall_verified_at         – UTC timestamp of the last approval/rejection
  hall_rejection_reason    – Optional reason text when rejected
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase
from app.models.enums import HallVerificationStatus, UserRole

if TYPE_CHECKING:
    from app.models.complaint import Complaint, ComplaintStatusHistory
    from app.models.hall import Hall


class User(TimestampedBase):
    """A platform user (student or hall administrator)."""

    __tablename__ = "users"

    # ------------------------------------------------------------------
    # Core identity columns
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

    # ------------------------------------------------------------------
    # Hall affiliation
    # ------------------------------------------------------------------

    hall_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("halls.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="FK to the hall this user belongs to.",
    )

    roll_number: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Student roll number (e.g. 21CS10001). Display only.",
    )

    room_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Student's room number within the hall (e.g. B-302).",
    )

    # ------------------------------------------------------------------
    # Hall verification
    # ------------------------------------------------------------------

    hall_verification_status: Mapped[HallVerificationStatus] = mapped_column(
        SAEnum(
            HallVerificationStatus,
            name="hallverificationstatus",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=HallVerificationStatus.PENDING,
        index=True,
        comment="Whether this student's hall affiliation has been verified by the admin.",
    )

    verified_by_admin_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK to the Hall Admin who last approved/rejected this student.",
    )

    hall_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp of the most recent verification action.",
    )

    hall_rejection_reason: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
        comment="Optional rejection reason set by the Hall Admin.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    hall: Mapped["Hall"] = relationship(
        "Hall",
        back_populates="users",
        lazy="selectin",
    )

    verified_by: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[verified_by_admin_id],
        remote_side="User.id",
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

    @property
    def is_verified(self) -> bool:
        """Convenience: True when hall affiliation is approved."""
        return self.hall_verification_status == HallVerificationStatus.APPROVED

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<User id={self.id!r} email={self.email!r} role={self.role.value!r} "
            f"verification={self.hall_verification_status.value!r}>"
        )
