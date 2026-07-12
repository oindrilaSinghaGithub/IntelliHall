"""
IntelliHall — ComplaintAssignment ORM Model

Represents a worker assignment for a scheduled complaint.
"""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TimestampedBase
from app.models.enums import MaintenanceType

if TYPE_CHECKING:
    from app.models.complaint import Complaint


class ComplaintAssignment(TimestampedBase):
    """
    A worker assignment for a scheduled maintenance complaint.
    
    One assignment per complaint (enforced by UNIQUE on complaint_id).
    Re-scheduling replaces the existing assignment.
    """

    __tablename__ = "complaint_assignments"

    # ------------------------------------------------------------------
    # Foreign key
    # ------------------------------------------------------------------

    complaint_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="FK to the complaint this assignment belongs to (UNIQUE).",
    )

    # ------------------------------------------------------------------
    # Assignment fields
    # ------------------------------------------------------------------

    worker_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Name of the maintenance worker assigned to this complaint.",
    )

    worker_type: Mapped[MaintenanceType] = mapped_column(
        SAEnum(
            MaintenanceType,
            name="maintenancetype",
            create_type=False,          # type already exists in DB
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        comment="Type of maintenance worker (electrician, plumber, etc.).",
    )

    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Date when the maintenance visit is scheduled.",
    )

    scheduled_time: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Optional time slot (e.g. '10:00–12:00').",
    )

    admin_remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional admin notes about the assignment.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    complaint: Mapped["Complaint"] = relationship(
        "Complaint",
        back_populates="assignment",
        lazy="selectin",
    )

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ComplaintAssignment id={self.id!r} "
            f"complaint_id={self.complaint_id!r} "
            f"worker={self.worker_name!r}>"
        )
