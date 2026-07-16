"""
IntelliHall — Worker Pydantic Schemas

Defines the request/response shapes for the Worker resource.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    WorkerAvailability,
    WorkerExperienceLevel,
    WorkerSpecialization,
)


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class WorkerBase(BaseModel):
    """Fields shared by all Worker schemas."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        examples=["Ramesh Kumar"],
        description="Full name of the worker.",
    )
    phone: str = Field(
        ...,
        min_length=1,
        max_length=20,
        examples=["+919876543210"],
        description="Phone number of the worker.",
    )
    specialization: WorkerSpecialization = Field(
        ...,
        description="Specialization of the worker.",
    )
    availability_status: WorkerAvailability = Field(
        default=WorkerAvailability.AVAILABLE,
        description="Availability status of the worker.",
    )
    skill_rating: float = Field(
        default=5.0,
        ge=1.0,
        le=5.0,
        description="Skill rating out of 5.0.",
    )
    experience_years: int = Field(
        default=0,
        ge=0,
        description="Years of work experience.",
    )
    experience_level: WorkerExperienceLevel = Field(
        default=WorkerExperienceLevel.INTERMEDIATE,
        description="Worker experience level.",
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class WorkerCreate(WorkerBase):
    """Schema for creating a new Worker (POST body)."""
    pass


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

class WorkerUpdate(BaseModel):
    """Schema for partially updating a Worker (PUT/PATCH body). All fields optional."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated name.",
    )
    phone: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
        description="Updated phone number.",
    )
    specialization: WorkerSpecialization | None = Field(
        default=None,
        description="Updated specialization.",
    )
    availability_status: WorkerAvailability | None = Field(
        default=None,
        description="Updated availability status.",
    )
    skill_rating: float | None = Field(
        default=None,
        ge=1.0,
        le=5.0,
        description="Updated skill rating.",
    )
    experience_years: int | None = Field(
        default=None,
        ge=0,
        description="Updated experience years.",
    )
    experience_level: WorkerExperienceLevel | None = Field(
        default=None,
        description="Updated experience level.",
    )


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

class WorkerRead(WorkerBase):
    """
    Schema returned by GET endpoints.
    Includes server-generated and computed fields.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID primary key.")
    hall_id: str = Field(..., description="Hall this worker belongs to.")
    active_jobs: int = Field(
        ...,
        description="Count of currently active complaints assigned to this worker.",
    )
    completed_jobs: int = Field(
        ...,
        description="Count of completed jobs by this worker.",
    )
    created_at: datetime = Field(..., description="UTC timestamp of creation.")
    updated_at: datetime = Field(..., description="UTC timestamp of last update.")


# ---------------------------------------------------------------------------
# Paginated list response
# ---------------------------------------------------------------------------

class PaginatedWorkerResponse(BaseModel):
    """Paginated list of workers."""

    items: list[WorkerRead] = Field(..., description="List of workers on current page.")
    total: int = Field(..., description="Total count of workers matching filters.")
    page: int = Field(..., description="Current page number.")
    page_size: int = Field(..., description="Number of items per page.")
    pages: int = Field(..., description="Total number of pages.")
