"""
IntelliHall — Hall Pydantic Schemas

Defines the request/response shapes for the Hall resource.

Schema hierarchy:
    HallBase          – shared fields (name, code)
    ├── HallCreate    – POST body (inherits HallBase)
    ├── HallUpdate    – PATCH body (all fields optional)
    └── HallRead      – GET response (adds id, timestamps)

    AssignUserRequest – body for POST /halls/{id}/assign-user
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class HallBase(BaseModel):
    """Fields shared by all Hall schemas."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        examples=["Tagore Hall"],
        description="Full display name of the hall.",
    )
    code: str = Field(
        ...,
        min_length=1,
        max_length=20,
        examples=["TH"],
        description=(
            "Short unique identifier for the hall (e.g. 'TH'). "
            "Automatically uppercased on write."
        ),
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class HallCreate(HallBase):
    """Schema for creating a new Hall (POST body)."""
    pass


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

class HallUpdate(BaseModel):
    """Schema for partially updating a Hall (PATCH body). All fields optional."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated display name.",
    )
    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
        description="Updated short identifier (automatically uppercased).",
    )


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

class HallRead(HallBase):
    """
    Schema returned by GET endpoints.
    Includes server-generated fields (id, timestamps).
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID primary key.")
    created_at: datetime = Field(..., description="UTC timestamp of creation.")
    updated_at: datetime = Field(..., description="UTC timestamp of last update.")


# ---------------------------------------------------------------------------
# Assign-user request
# ---------------------------------------------------------------------------

class AssignUserRequest(BaseModel):
    """Body for POST /halls/{hall_id}/assign-user."""

    user_id: str = Field(
        ...,
        description="UUID of the user to assign to this hall.",
    )


# ---------------------------------------------------------------------------
# Public Read
# ---------------------------------------------------------------------------

class HallPublicRead(BaseModel):
    """Schema returned by GET /halls/public. Exposes only id and name."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID primary key.")
    name: str = Field(..., description="Full display name of the hall.")

