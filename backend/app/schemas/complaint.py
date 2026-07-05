"""
IntelliHall — Complaint Domain Pydantic Schemas

Schema hierarchy
----------------

ComplaintBase              — shared writable fields
├── ComplaintCreate        — POST body; all required writable fields
├── ComplaintUpdate        — PATCH body; all fields optional
└── ComplaintRead          — GET response; adds server-generated fields

ComplaintSummary           — lightweight list view (id, title, priority, status,
                             category, created_at only)

ComplaintImageRead         — GET response for a single attached image
ComplaintStatusHistoryRead — GET response for a single status-history entry
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
    ComplaintType,
    MaintenanceType,
)


# ---------------------------------------------------------------------------
# ComplaintImage
# ---------------------------------------------------------------------------


class ComplaintImageRead(BaseModel):
    """Read-only schema for a complaint image."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID primary key.")
    complaint_id: str = Field(..., description="Parent complaint UUID.")
    image_url: str = Field(..., description="URL to the stored image file.")
    uploaded_at: datetime = Field(..., description="UTC timestamp of upload.")


# ---------------------------------------------------------------------------
# ComplaintStatusHistory
# ---------------------------------------------------------------------------


class ComplaintStatusHistoryRead(BaseModel):
    """Read-only schema for a single status-history entry."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID primary key.")
    complaint_id: str = Field(..., description="Parent complaint UUID.")
    previous_status: ComplaintStatus | None = Field(
        default=None,
        description="Status before the transition (None for the initial SUBMITTED entry).",
    )
    new_status: ComplaintStatus = Field(..., description="Status after the transition.")
    updated_by: str = Field(..., description="UUID of the user who triggered this change.")
    remarks: str | None = Field(default=None, description="Optional explanatory note.")
    timestamp: datetime = Field(..., description="UTC time of the transition.")


# ---------------------------------------------------------------------------
# Complaint — Base
# ---------------------------------------------------------------------------


class ComplaintBase(BaseModel):
    """Shared writable fields for Complaint schemas."""

    title: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Short summary of the issue.",
    )
    description: str = Field(
        ...,
        min_length=10,
        description="Detailed description of the issue.",
    )
    complaint_type: ComplaintType = Field(
        ...,
        description="Personal room or common area.",
    )
    category: ComplaintCategory = Field(
        ...,
        description="Maintenance category.",
    )
    priority: ComplaintPriority = Field(
        default=ComplaintPriority.MEDIUM,
        description="Urgency level.",
    )

    # -- Personal location --------------------------------------------------
    room_number: str | None = Field(
        default=None,
        max_length=20,
        description="Room number — required when complaint_type is PERSONAL.",
    )

    # -- Common-area location -----------------------------------------------
    block: str | None = Field(
        default=None,
        max_length=50,
        description="Block/wing — relevant for COMMON_AREA complaints.",
    )
    floor: str | None = Field(
        default=None,
        max_length=10,
        description="Floor identifier — relevant for COMMON_AREA complaints.",
    )
    common_area: str | None = Field(
        default=None,
        max_length=100,
        description="Name of the common area.",
    )
    qr_location_id: str | None = Field(
        default=None,
        max_length=100,
        description="QR-code location tag scanned at the common area.",
    )

    # -- Scheduling ---------------------------------------------------------
    preferred_visit_time: datetime | None = Field(
        default=None,
        description="Student's preferred time slot for the maintenance visit.",
    )


# ---------------------------------------------------------------------------
# Complaint — Create
# ---------------------------------------------------------------------------


class ComplaintCreate(ComplaintBase):
    """
    Schema for creating a new Complaint (POST body).
    `hall_id` and `created_by` are supplied by the caller / service layer.
    """

    hall_id: str = Field(..., description="UUID of the hall.")
    created_by: str = Field(..., description="UUID of the user raising the complaint.")


# ---------------------------------------------------------------------------
# Complaint — Update
# ---------------------------------------------------------------------------


class ComplaintUpdate(BaseModel):
    """Schema for partially updating a Complaint (PATCH body). All fields optional."""

    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=10)
    priority: ComplaintPriority | None = Field(default=None)
    status: ComplaintStatus | None = Field(default=None)
    maintenance_type: MaintenanceType | None = Field(default=None)
    current_assignee: str | None = Field(default=None, max_length=255)
    room_number: str | None = Field(default=None, max_length=20)
    block: str | None = Field(default=None, max_length=50)
    floor: str | None = Field(default=None, max_length=10)
    common_area: str | None = Field(default=None, max_length=100)
    qr_location_id: str | None = Field(default=None, max_length=100)
    preferred_visit_time: datetime | None = Field(default=None)


# ---------------------------------------------------------------------------
# Complaint — Read
# ---------------------------------------------------------------------------


class ComplaintRead(ComplaintBase):
    """
    Full Complaint representation returned by GET endpoints.
    Includes all server-generated and admin-set fields.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID primary key.")
    status: ComplaintStatus = Field(..., description="Current lifecycle status.")
    maintenance_type: MaintenanceType | None = Field(
        default=None,
        description="Assigned maintenance worker type.",
    )
    current_assignee: str | None = Field(
        default=None,
        description="Name of the current assignee.",
    )
    hall_id: str = Field(..., description="UUID of the parent hall.")
    created_by: str = Field(..., description="UUID of the creating user.")
    created_at: datetime = Field(..., description="UTC creation timestamp.")
    updated_at: datetime = Field(..., description="UTC last-update timestamp.")

    images: list[ComplaintImageRead] = Field(
        default_factory=list,
        description="Attached images.",
    )
    status_history: list[ComplaintStatusHistoryRead] = Field(
        default_factory=list,
        description="Status-change audit trail.",
    )


# ---------------------------------------------------------------------------
# Complaint — Summary (lightweight list view)
# ---------------------------------------------------------------------------


class ComplaintSummary(BaseModel):
    """
    Minimal projection used in list endpoints where full detail is unnecessary.
    Contains only the fields required for a complaint card in a list view.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID primary key.")
    title: str = Field(..., description="Short summary of the issue.")
    priority: ComplaintPriority = Field(..., description="Urgency level.")
    status: ComplaintStatus = Field(..., description="Current lifecycle status.")
    category: ComplaintCategory = Field(..., description="Maintenance category.")
    created_at: datetime = Field(..., description="UTC creation timestamp.")
