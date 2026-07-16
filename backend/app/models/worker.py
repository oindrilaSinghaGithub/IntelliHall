"""
IntelliHall — Worker ORM Model

Represents a maintenance staff worker assigned to a specific residential hall.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum, Float, ForeignKey, Integer, String, select, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, column_property

from app.db.base import TimestampedBase
from app.models.enums import (
    WorkerAvailability,
    WorkerExperienceLevel,
    WorkerSpecialization,
    ComplaintStatus,
)
from app.models.complaint import Complaint

if TYPE_CHECKING:
    from app.models.hall import Hall


class Worker(TimestampedBase):
    """A maintenance staff worker."""

    __tablename__ = "workers"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Full name of the worker.",
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Phone number of the worker.",
    )

    specialization: Mapped[WorkerSpecialization] = mapped_column(
        SAEnum(
            WorkerSpecialization,
            name="workerspecialization",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
        comment="Specialization of the worker.",
    )

    availability_status: Mapped[WorkerAvailability] = mapped_column(
        SAEnum(
            WorkerAvailability,
            name="workeravailability",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=WorkerAvailability.AVAILABLE,
        index=True,
        comment="Availability status of the worker.",
    )

    skill_rating: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=5.0,
        comment="Skill rating out of 5.0.",
    )

    experience_years: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Years of work experience.",
    )

    experience_level: Mapped[WorkerExperienceLevel] = mapped_column(
        SAEnum(
            WorkerExperienceLevel,
            name="workerexperiencelevel",
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=WorkerExperienceLevel.INTERMEDIATE,
        comment="Worker experience level.",
    )

    completed_jobs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Count of completed jobs by this worker.",
    )

    hall_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("halls.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Hall this worker belongs to.",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    hall: Mapped["Hall"] = relationship(
        "Hall",
        back_populates="workers",
        lazy="selectin",
    )

    assigned_complaints: Mapped[list["Complaint"]] = relationship(
        "Complaint",
        foreign_keys=[Complaint.assigned_worker_id],
        back_populates="assigned_worker",
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Worker id={self.id!r} name={self.name!r} spec={self.specialization!r}>"


# ---------------------------------------------------------------------------
# Correlated Column Properties (added after class definition to resolve types)
# ---------------------------------------------------------------------------

Worker.active_jobs = column_property(
    select(func.count(Complaint.id))
    .where(Complaint.assigned_worker_id == Worker.id)
    .where(Complaint.status.not_in([ComplaintStatus.COMPLETED, ComplaintStatus.CLOSED]))
    .scalar_subquery()
)

