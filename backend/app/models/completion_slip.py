"""
IntelliHall — CompletionSlip ORM Model

Digital replacement for the paper completion slip used in IIT KGP hostels.
Stores what work was done, worker info, and student's confirmation status.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase
from app.models.enums import MaintenanceType, StudentConfirmationStatus

if TYPE_CHECKING:
    from app.models.complaint import Complaint


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CompletionSlip(TimestampedBase):
    """
    Digital completion slip created when a complaint is marked complete.
    
    One slip per complaint (enforced by UNIQUE on complaint_id).
    """

    __tablename__ = "completion_slips"

    # ------------------------------------------------------------------
    # Foreign keys
    # ------------------------------------------------------------------

    complaint_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="FK to the complaint this slip belongs to (UNIQUE).",
    )

    hall_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("halls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Denormalized hall FK for fast schedule queries.",
    )

    # ------------------------------------------------------------------
    # Snapshot fields (captured at completion time)
    # ------------------------------------------------------------------

    room_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Snapshot of room number from the complaint.",
    )

    worker_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Name of the worker who performed the repair.",
    )

    worker_type: Mapped[MaintenanceType] = mapped_column(
        SAEnum(
            MaintenanceType,
            name="maintenancetype",
            create_type=False,          # type already exists in DB
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        comment="Type of worker who performed the repair.",
    )

    completion_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        comment="UTC timestamp when the repair was marked complete.",
    )

    # ------------------------------------------------------------------
    # Admin-filled fields
    # ------------------------------------------------------------------

    work_done: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Description of the work performed (admin-supplied).",
    )

    admin_remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional additional remarks from the admin.",
    )

    # ------------------------------------------------------------------
    # Student-filled fields
    # ------------------------------------------------------------------

    student_comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Student's comment on the repair outcome.",
    )

    student_confirmation_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=StudentConfirmationStatus.PENDING.value,
        comment="Student confirmation state: pending | confirmed | rejected.",
    )

    student_confirmation_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="UTC timestamp when the student confirmed or rejected.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    complaint: Mapped["Complaint"] = relationship(
        "Complaint",
        back_populates="completion_slip",
        lazy="selectin",
    )

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<CompletionSlip id={self.id!r} "
            f"complaint_id={self.complaint_id!r} "
            f"status={self.student_confirmation_status!r}>"
        )
