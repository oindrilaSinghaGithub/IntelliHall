"""
IntelliHall — Schedule Pydantic Schemas
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.models.enums import ComplaintCategory, ComplaintStatus, MaintenanceType


class ScheduleItemRead(BaseModel):
    """A single item in the maintenance schedule."""

    complaint_id: str = Field(..., description="Complaint UUID.")
    complaint_title: str = Field(..., description="Complaint title.")
    room_number: str | None = Field(default=None, description="Room number (if applicable).")
    category: ComplaintCategory = Field(..., description="Maintenance category.")
    status: ComplaintStatus = Field(..., description="Current status.")
    visit_date: date = Field(..., description="Scheduled visit date.")
    scheduled_time: str | None = Field(default=None, description="Optional time slot.")
    worker_name: str = Field(..., description="Assigned worker name.")
    worker_type: MaintenanceType = Field(..., description="Assigned worker type.")
    admin_remarks: str | None = Field(default=None, description="Optional admin remarks.")


class ScheduleFilters(BaseModel):
    """Query parameters for the schedule endpoint."""

    scheduled_date: date | None = Field(default=None, description="Filter by exact date.")
    worker_name: str | None = Field(
        default=None,
        description="Filter by worker name (partial match).",
    )
    worker_type: MaintenanceType | None = Field(
        default=None,
        description="Filter by worker type.",
    )
    category: ComplaintCategory | None = Field(
        default=None,
        description="Filter by maintenance category.",
    )
