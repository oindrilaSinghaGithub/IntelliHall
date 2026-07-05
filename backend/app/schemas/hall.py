"""
IntelliHall — Hall Pydantic Schemas

Defines the request/response shapes for the Hall resource.

Schema hierarchy:
    HallBase        – shared fields (name, code)
    ├── HallCreate  – used for POST body (inherits HallBase)
    ├── HallUpdate  – used for PATCH body (all fields optional)
    └── HallRead    – used for GET responses (adds id, timestamps)
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
        description="Short unique identifier for the hall (e.g. 'TH').",
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
        description="Updated short identifier.",
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
