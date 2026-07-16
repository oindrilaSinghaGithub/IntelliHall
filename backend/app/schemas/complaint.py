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

PaginatedResponse[T]       — generic paginated envelope used by the list endpoint
ComplaintFilters           — query-parameter model for list filtering / sorting
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.enums import (
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
    ComplaintType,
    MaintenanceType,
)
from app.schemas.worker import WorkerRead


T = TypeVar("T")
# ---------------------------------------------------------------------------
# Generic paginated envelope
# ---------------------------------------------------------------------------


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper.

    Used by the list endpoint so consumers always know the total count and
    can calculate how many pages remain without a second request.
    """

    items: list[T]
    total: int = Field(..., description="Total matching records (across all pages).")
    page: int = Field(..., description="Current page number (1-indexed).")
    page_size: int = Field(..., description="Number of items per page.")
    pages: int = Field(..., description="Total number of pages.")


# ---------------------------------------------------------------------------
# List filters / sorting (used as FastAPI Query dependencies)
# ---------------------------------------------------------------------------


class ComplaintFilters(BaseModel):
    """
    Query parameters accepted by GET /complaints.

    All fields are optional; omitting a field means "no filter on that column".
    """

    hall_id: str | None = Field(default=None, description="Filter by hall UUID.")
    status: ComplaintStatus | None = Field(default=None, description="Filter by status.")
    priority: ComplaintPriority | None = Field(default=None, description="Filter by priority.")
    category: ComplaintCategory | None = Field(default=None, description="Filter by category.")
    complaint_type: ComplaintType | None = Field(
        default=None, description="Filter by complaint type."
    )
    created_by: str | None = Field(
        default=None, description="Filter by creator user UUID."
    )
    page: int = Field(default=1, ge=1, description="Page number (1-indexed).")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100).")
    sort_by: Literal[
        "created_at", "updated_at", "priority", "status", "category", "title"
    ] = Field(default="created_at", description="Column to sort by.")
    sort_order: Literal["asc", "desc"] = Field(
        default="desc", description="Sort direction."
    )


class HallComplaintFilters(BaseModel):
    """
    Query parameters for GET /halls/{hall_id}/complaints (admin view).

    ``hall_id`` is taken from the URL path, so it is not a query parameter here.
    Supports the same filter dimensions as ComplaintFilters minus hall_id/created_by.
    """

    status: ComplaintStatus | None = Field(default=None, description="Filter by status.")
    priority: ComplaintPriority | None = Field(default=None, description="Filter by priority.")
    category: ComplaintCategory | None = Field(default=None, description="Filter by category.")
    complaint_type: ComplaintType | None = Field(
        default=None, description="Filter by complaint type."
    )
    page: int = Field(default=1, ge=1, description="Page number (1-indexed).")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100).")
    sort_by: Literal[
        "created_at", "updated_at", "priority", "status", "category", "title"
    ] = Field(default="created_at", description="Column to sort by.")
    sort_order: Literal["asc", "desc"] = Field(
        default="desc", description="Sort direction."
    )


# ---------------------------------------------------------------------------
# Status-update request body
# ---------------------------------------------------------------------------


class StatusUpdateRequest(BaseModel):
    """Body for PATCH /complaints/{complaint_id}/status."""

    new_status: ComplaintStatus = Field(
        ...,
        description="The target status to transition to.",
    )
    remarks: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional note explaining the reason for this transition.",
    )

    # Assignment fields (required only when new_status == SCHEDULED)
    worker_name: str | None = Field(
        default=None,
        max_length=255,
        description="Worker name (required for SCHEDULED transition).",
    )
    worker_type: MaintenanceType | None = Field(
        default=None,
        description="Worker type (required for SCHEDULED transition).",
    )
    scheduled_date: date | None = Field(
        default=None,
        description="Scheduled visit date (required for SCHEDULED transition).",
    )
    scheduled_time: str | None = Field(
        default=None,
        max_length=50,
        description="Optional time slot (e.g. '10:00–12:00').",
    )
    admin_remarks: str | None = Field(
        default=None,
        description="Optional admin remarks for assignment.",
    )

    # Completion field (required only when new_status == COMPLETED)
    work_done: str | None = Field(
        default=None,
        description="Work done description (required for COMPLETED transition).",
    )



# ---------------------------------------------------------------------------
# Reschedule Request
# ---------------------------------------------------------------------------


class RescheduleRequest(BaseModel):
    """Body for POST /complaints/{complaint_id}/reschedule."""

    preferred_visit_time: datetime = Field(
        ...,
        description=(
            "New preferred visit datetime (ISO 8601, timezone-aware). "
            "Must be a future timestamp."
        ),
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


class ComplaintImagesUploadResponse(BaseModel):
    """Response returned after uploading one or more complaint images."""

    images: list[ComplaintImageRead] = Field(
        ...,
        description="Newly uploaded image records.",
    )


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

    ``hall_id`` and ``created_by`` are intentionally absent: they are
    derived server-side from the authenticated user (current_user.hall_id
    and current_user.id) and must never be accepted from the client.
    """


# ---------------------------------------------------------------------------
# Complaint — Update
# ---------------------------------------------------------------------------


class ComplaintUpdate(BaseModel):
    """Schema for partially updating a Complaint (PATCH body). All fields optional."""

    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=10)
    priority: ComplaintPriority | None = Field(default=None)
    category: ComplaintCategory | None = Field(default=None)

    status: ComplaintStatus | None = Field(default=None)
    maintenance_type: MaintenanceType | None = Field(default=None)
    current_assignee: str | None = Field(default=None, max_length=255)
    room_number: str | None = Field(default=None, max_length=20)
    block: str | None = Field(default=None, max_length=50)
    floor: str | None = Field(default=None, max_length=10)
    common_area: str | None = Field(default=None, max_length=100)
    qr_location_id: str | None = Field(default=None, max_length=100)
    preferred_visit_time: datetime | None = Field(default=None)
    assigned_worker_id: str | None = Field(default=None)
    force_recompute_recommendation: bool | None = Field(default=None)




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
    student_name: str | None = Field(default=None, description="Display name of the creator student.")

    images: list[ComplaintImageRead] = Field(
        default_factory=list,
        description="Attached images.",
    )
    status_history: list[ComplaintStatusHistoryRead] = Field(
        default_factory=list,
        description="Status-change audit trail.",
    )

    # AI prediction fields
    predicted_priority: ComplaintPriority | None = Field(
        default=None,
        description="AI-predicted urgency level (may differ from student-selected priority).",
    )
    ai_confidence: float | None = Field(
        default=None,
        description="AI prediction confidence score in range [0.0, 1.0].",
    )

    # New relationships for maintenance workflow
    assignment: "AssignmentRead | None" = Field(
        default=None,
        description="Worker assignment (when complaint is scheduled).",
    )
    completion_slip: "CompletionSlipRead | None" = Field(
        default=None,
        description="Completion slip (when complaint is marked complete).",
    )

    # Community Impact fields
    affected_count: int = Field(
        default=0,
        description="Total number of students who marked themselves affected.",
    )
    is_affected: bool = Field(
        default=False,
        description="True if the current calling user has marked themselves affected.",
    )
    reporter_room: str | None = Field(
        default=None,
        description="Privacy-friendly room/location identifier of the reporter student.",
    )

    # Worker Assignment and Recommendation fields
    assigned_worker_id: str | None = Field(
        default=None,
        description="UUID of the assigned worker.",
    )
    recommended_worker_id: str | None = Field(
        default=None,
        description="UUID of the recommended worker.",
    )
    recommendation_score: float | None = Field(
        default=None,
        description="AI recommendation score out of 100.",
    )
    recommendation_reason: str | None = Field(
        default=None,
        description="Explanation/reasoning bullets for the AI recommendation.",
    )
    assigned_worker: WorkerRead | None = Field(
        default=None,
        description="Details of the assigned worker.",
    )

    @computed_field
    @property
    def recommendation_confidence(self) -> str | None:
        if self.recommendation_score is None:
            return None
        if self.recommendation_score >= 90:
            return "Very High"
        elif self.recommendation_score >= 75:
            return "High"
        elif self.recommendation_score >= 60:
            return "Medium"
        else:
            return "Low"




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
    complaint_type: ComplaintType = Field(..., description="Type of the complaint.")
    room_number: str | None = Field(default=None, description="Room number for personal complaints.")
    block: str | None = Field(default=None, description="Block wing for common area complaints.")
    floor: str | None = Field(default=None, description="Floor level for common area complaints.")
    common_area: str | None = Field(default=None, description="Common area location name.")
    student_name: str | None = Field(default=None, description="Display name of the creator student.")
    predicted_priority: ComplaintPriority | None = Field(
        default=None,
        description="AI-predicted urgency level.",
    )
    ai_confidence: float | None = Field(
        default=None,
        description="AI prediction confidence score in range [0.0, 1.0].",
    )

    # Community Impact fields
    affected_count: int = Field(
        default=0,
        description="Total number of students who marked themselves affected.",
    )
    is_affected: bool = Field(
        default=False,
        description="True if the current calling user has marked themselves affected.",
    )
    reporter_room: str | None = Field(
        default=None,
        description="Privacy-friendly room/location identifier of the reporter student.",
    )

    # Worker Assignment and Recommendation fields
    assigned_worker_id: str | None = Field(
        default=None,
        description="UUID of the assigned worker.",
    )
    recommended_worker_id: str | None = Field(
        default=None,
        description="UUID of the recommended worker.",
    )
    recommendation_score: float | None = Field(
        default=None,
        description="AI recommendation score out of 100.",
    )
    recommendation_reason: str | None = Field(
        default=None,
        description="Explanation/reasoning bullets for the AI recommendation.",
    )
    assigned_worker: WorkerRead | None = Field(
        default=None,
        description="Details of the assigned worker.",
    )

    @computed_field
    @property
    def recommendation_confidence(self) -> str | None:
        if self.recommendation_score is None:
            return None
        if self.recommendation_score >= 90:
            return "Very High"
        elif self.recommendation_score >= 75:
            return "High"
        elif self.recommendation_score >= 60:
            return "Medium"
        else:
            return "Low"



# ---------------------------------------------------------------------------
# Forward references resolution
# ---------------------------------------------------------------------------

# Import assignment and completion slip schemas for forward references
from app.schemas.assignment import AssignmentRead  # noqa: E402
from app.schemas.completion_slip import CompletionSlipRead  # noqa: E402

# Rebuild models to resolve forward references
ComplaintRead.model_rebuild()
