"""
IntelliHall — Assignment Pydantic Schemas
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MaintenanceType


class AssignmentCreate(BaseModel):
    """Schema for creating/updating a complaint assignment."""

    worker_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the maintenance worker.",
    )
    worker_type: MaintenanceType = Field(
        ...,
        description="Type of maintenance worker.",
    )
    scheduled_date: date = Field(
        ...,
        description="Date when the maintenance visit is scheduled.",
    )
    scheduled_time: str | None = Field(
        default=None,
        max_length=50,
        description="Optional time slot (e.g. '10:00–12:00').",
    )
    admin_remarks: str | None = Field(
        default=None,
        description="Optional admin notes about the assignment.",
    )


class AssignmentRead(BaseModel):
    """Read-only schema for a complaint assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID primary key.")
    complaint_id: str = Field(..., description="Parent complaint UUID.")
    worker_name: str = Field(..., description="Name of the maintenance worker.")
    worker_type: MaintenanceType = Field(..., description="Type of maintenance worker.")
    scheduled_date: date = Field(..., description="Scheduled visit date.")
    scheduled_time: str | None = Field(default=None, description="Optional time slot.")
    admin_remarks: str | None = Field(default=None, description="Optional admin notes.")
    created_at: datetime = Field(..., description="UTC creation timestamp.")
    updated_at: datetime = Field(..., description="UTC last-update timestamp.")
