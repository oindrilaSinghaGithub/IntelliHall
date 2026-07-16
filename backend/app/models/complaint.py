"""
IntelliHall — Complaint Domain ORM Models

Contains three tightly coupled models:
  - Complaint               : Core complaint record.
  - ComplaintImage          : Attached photo evidence for a complaint.
  - ComplaintStatusHistory  : Audit trail of every status transition.

Design notes
------------
- All three share the same module because they are semantically inseparable;
  splitting them would force circular imports without real architectural gain.
- Location fields are intentionally nullable at the DB layer.
  Business-level rules (e.g. personal complaints must have room_number) are
  deferred to the service/validation layer and will be added later.
- `current_assignee` is a free-text name string rather than a FK so the
  system can record external contractor names without requiring a user account.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    select,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, column_property

from app.db.base import TimestampedBase
from app.models.enums import (
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
    ComplaintType,
    MaintenanceType,
)

if TYPE_CHECKING:
    from app.models.assignment import ComplaintAssignment
    from app.models.completion_slip import CompletionSlip
    from app.models.hall import Hall
    from app.models.user import User
    from app.models.worker import Worker



def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Complaint
# ---------------------------------------------------------------------------


class Complaint(TimestampedBase):
    """A maintenance complaint raised by a student."""

    __tablename__ = "complaints"

    # ------------------------------------------------------------------
    # Core fields
    # ------------------------------------------------------------------

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Short summary entered by the student.",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Detailed description of the issue.",
    )

    complaint_type: Mapped[ComplaintType] = mapped_column(
        SAEnum(
            ComplaintType,
            name="complainttype",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        comment="Whether the complaint is for a personal room or a common area.",
    )

    category: Mapped[ComplaintCategory] = mapped_column(
        SAEnum(
            ComplaintCategory,
            name="complaintcategory",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
        comment="Maintenance category (electrical, plumbing, …).",
    )

    priority: Mapped[ComplaintPriority] = mapped_column(
        SAEnum(
            ComplaintPriority,
            name="complaintpriority",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=ComplaintPriority.MEDIUM,
        index=True,
        comment="Urgency level of the complaint.",
    )

    predicted_priority: Mapped[ComplaintPriority | None] = mapped_column(
        SAEnum(
            ComplaintPriority,
            name="complaintpriority",
            create_constraint=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
        comment="AI-predicted urgency level (may differ from student-selected priority).",
    )

    ai_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Prediction confidence score in range [0.0, 1.0].",
    )

    status: Mapped[ComplaintStatus] = mapped_column(
        SAEnum(
            ComplaintStatus,
            name="complaintstatus",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=ComplaintStatus.SUBMITTED,
        index=True,
        comment="Current lifecycle state of the complaint.",
    )

    maintenance_type: Mapped[MaintenanceType | None] = mapped_column(
        SAEnum(
            MaintenanceType,
            name="maintenancetype",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
        comment="Type of maintenance worker required (set by admin).",
    )

    current_assignee: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Name of the person / contractor currently handling the complaint.",
    )

    # ------------------------------------------------------------------
    # Personal-complaint location fields
    # ------------------------------------------------------------------

    room_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Room number — required for PERSONAL complaints.",
    )

    # ------------------------------------------------------------------
    # Common-area location fields
    # ------------------------------------------------------------------

    block: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Block / wing identifier for COMMON_AREA complaints.",
    )

    floor: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="Floor identifier for COMMON_AREA complaints.",
    )

    common_area: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Name of the common area (e.g. 'Reading Room', 'Corridor').",
    )

    qr_location_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Optional QR-code location tag scanned at the common area.",
    )

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------

    preferred_visit_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Student's preferred time slot for the maintenance visit.",
    )

    # ------------------------------------------------------------------
    # Foreign keys
    # ------------------------------------------------------------------

    hall_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("halls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Hall this complaint belongs to.",
    )

    created_by: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User (student) who raised the complaint.",
    )

    assigned_worker_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Worker assigned to resolve this complaint.",
    )

    recommended_worker_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("workers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Worker recommended by the AI for this complaint.",
    )

    recommendation_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="AI recommendation match score percentage (0-100).",
    )

    recommendation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="AI recommendation reasoning explaining the choice.",
    )


    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    hall: Mapped["Hall"] = relationship(
        "Hall",
        back_populates="complaints",
        lazy="selectin",
    )

    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="complaints_created",
        lazy="selectin",
    )

    assigned_worker: Mapped[Worker | None] = relationship(
        "Worker",
        foreign_keys=[assigned_worker_id],
        back_populates="assigned_complaints",
        lazy="selectin",
    )

    recommended_worker: Mapped[Worker | None] = relationship(
        "Worker",
        foreign_keys=[recommended_worker_id],
        lazy="selectin",
    )


    images: Mapped[list["ComplaintImage"]] = relationship(
        "ComplaintImage",
        back_populates="complaint",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    status_history: Mapped[list["ComplaintStatusHistory"]] = relationship(
        "ComplaintStatusHistory",
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="ComplaintStatusHistory.timestamp",
        lazy="selectin",
    )

    # One-to-one: worker assignment (set when complaint is scheduled)
    assignment: Mapped["ComplaintAssignment | None"] = relationship(
        "ComplaintAssignment",
        back_populates="complaint",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )

    # One-to-one: completion slip (set when complaint is marked complete)
    completion_slip: Mapped["CompletionSlip | None"] = relationship(
        "CompletionSlip",
        back_populates="complaint",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )

    affected_entries: Mapped[list["CommonAreaAffected"]] = relationship(
        "CommonAreaAffected",
        back_populates="complaint",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # ------------------------------------------------------------------
    # Composite indexes for common query patterns
    # ------------------------------------------------------------------

    __table_args__ = (
        Index("ix_complaints_hall_id_status", "hall_id", "status"),
        Index("ix_complaints_created_by_status", "created_by", "status"),
        Index("ix_complaints_created_at", "created_at"),
    )

    @property
    def student_name(self) -> str | None:
        """Return the display name of the student who created the complaint."""
        return self.creator.name if self.creator else None

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Complaint id={self.id!r} status={self.status.value!r} "
            f"priority={self.priority.value!r}>"
        )


# ---------------------------------------------------------------------------
# ComplaintImage
# ---------------------------------------------------------------------------


class ComplaintImage(TimestampedBase):
    """
    A photo attached to a complaint.

    `uploaded_at` is a dedicated column (separate from the TimestampedBase
    `created_at`) kept for semantic clarity in queries like
    "show images uploaded after X".
    """

    __tablename__ = "complaint_images"

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    complaint_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The complaint this image belongs to.",
    )

    image_url: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        comment="Relative or absolute URL to the stored image file.",
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        comment="UTC timestamp when the image was uploaded.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    complaint: Mapped["Complaint"] = relationship(
        "Complaint",
        back_populates="images",
        lazy="selectin",
    )

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ComplaintImage id={self.id!r} complaint_id={self.complaint_id!r}>"


# ---------------------------------------------------------------------------
# ComplaintStatusHistory
# ---------------------------------------------------------------------------


class ComplaintStatusHistory(TimestampedBase):
    """
    Immutable audit record of every status transition on a complaint.

    One row is written each time a complaint's status changes.  Rows are
    intentionally never updated or deleted (cascade only on parent removal).
    """

    __tablename__ = "complaint_status_history"

    # ------------------------------------------------------------------
    # Columns
    # ------------------------------------------------------------------

    complaint_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The complaint this history entry belongs to.",
    )

    previous_status: Mapped[ComplaintStatus | None] = mapped_column(
        SAEnum(
            ComplaintStatus,
            name="complaintstatus",
            create_constraint=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=True,
        comment="Status before the transition (NULL for the initial SUBMITTED entry).",
    )

    new_status: Mapped[ComplaintStatus] = mapped_column(
        SAEnum(
            ComplaintStatus,
            name="complaintstatus",
            create_constraint=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        comment="Status after the transition.",
    )

    updated_by: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who triggered this status change.",
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional free-text note explaining the transition.",
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        index=True,
        comment="UTC time at which this transition occurred.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    complaint: Mapped["Complaint"] = relationship(
        "Complaint",
        back_populates="status_history",
        lazy="selectin",
    )

    actor: Mapped["User"] = relationship(
        "User",
        foreign_keys=[updated_by],
        back_populates="status_updates",
        lazy="selectin",
    )

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ComplaintStatusHistory id={self.id!r} "
            f"complaint_id={self.complaint_id!r} "
            f"new_status={self.new_status.value!r}>"
        )


# ---------------------------------------------------------------------------
# CommonAreaAffected
# ---------------------------------------------------------------------------


class CommonAreaAffected(TimestampedBase):
    """Tracks which students are affected by a common area complaint."""

    __tablename__ = "common_area_affected"

    # Foreign keys
    complaint_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to the complaint this student is affected by.",
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to the student who marked themselves as affected.",
    )

    # Relationships
    complaint: Mapped["Complaint"] = relationship(
        "Complaint",
        back_populates="affected_entries",
        lazy="selectin",
    )

    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )

    # Unique index to prevent duplicate records
    __table_args__ = (
        Index("ix_common_area_affected_unique", "complaint_id", "user_id", unique=True),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<CommonAreaAffected complaint_id={self.complaint_id!r} user_id={self.user_id!r}>"


# Define column property on Complaint after CommonAreaAffected is declared
Complaint.affected_count = column_property(
    select(func.count(CommonAreaAffected.id))
    .where(CommonAreaAffected.complaint_id == Complaint.id)
    .correlate_except(CommonAreaAffected)
    .scalar_subquery()
)
