"""
IntelliHall — Completion Slip Pydantic Schemas
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MaintenanceType, StudentConfirmationStatus


class CompletionSlipRead(BaseModel):
    """Read-only schema for a completion slip."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID primary key.")
    complaint_id: str = Field(..., description="Parent complaint UUID.")
    hall_id: str = Field(..., description="Hall UUID.")
    room_number: str | None = Field(default=None, description="Room number snapshot.")
    worker_name: str = Field(..., description="Name of the worker who did the repair.")
    worker_type: MaintenanceType = Field(..., description="Type of worker.")
    completion_date: datetime = Field(..., description="UTC timestamp of completion.")
    work_done: str = Field(..., description="Description of work performed.")
    admin_remarks: str | None = Field(default=None, description="Optional admin notes.")
    student_comment: str | None = Field(default=None, description="Student's comment.")
    student_confirmation_status: str = Field(
        ...,
        description="Confirmation status: pending | confirmed | rejected.",
    )
    student_confirmation_time: datetime | None = Field(
        default=None,
        description="UTC timestamp when student confirmed or rejected.",
    )
    created_at: datetime = Field(..., description="UTC creation timestamp.")
    updated_at: datetime = Field(..., description="UTC last-update timestamp.")


class WorkDoneRequest(BaseModel):
    """Request body for marking a complaint complete."""

    work_done: str = Field(
        ...,
        min_length=5,
        description="Description of the work performed (required).",
    )
    admin_remarks: str | None = Field(
        default=None,
        description="Optional additional remarks from the admin.",
    )
