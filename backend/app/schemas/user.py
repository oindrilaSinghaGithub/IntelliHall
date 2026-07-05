"""
IntelliHall — User Pydantic Schemas

Defines request/response shapes for the User resource.

Schema hierarchy:
    UserBase        – shared readable fields (name, email, role, hall_id)
    ├── UserCreate  – adds password (plain-text, hashed by service layer)
    ├── UserUpdate  – all fields optional for PATCH
    └── UserRead    – adds id, timestamps; excludes password_hash
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    """Shared readable fields for User schemas (no sensitive data)."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        examples=["Aarav Sharma"],
        description="Full display name of the user.",
    )
    email: EmailStr = Field(
        ...,
        description="Unique login e-mail address.",
    )
    role: UserRole = Field(
        default=UserRole.STUDENT,
        description="Role of the user within the system.",
    )
    hall_id: str | None = Field(
        default=None,
        description="UUID of the hall this user belongs to.",
    )


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

class UserCreate(UserBase):
    """
    Schema for creating a new User (POST body).
    The plain-text `password` field is accepted here and must be hashed
    by the service layer before persisting — never store it raw.
    """

    password: str = Field(
        ...,
        min_length=8,
        description="Plain-text password (will be hashed before storage).",
    )


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

class UserUpdate(BaseModel):
    """Schema for partially updating a User (PATCH body). All fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = Field(default=None)
    role: UserRole | None = Field(default=None)
    hall_id: str | None = Field(default=None)
    password: str | None = Field(
        default=None,
        min_length=8,
        description="New plain-text password (will be hashed before storage).",
    )


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

class UserRead(UserBase):
    """
    Schema returned by GET endpoints.
    Intentionally omits `password_hash` — never expose it over the API.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID primary key.")
    created_at: datetime = Field(..., description="UTC timestamp of creation.")
    updated_at: datetime = Field(..., description="UTC timestamp of last update.")
