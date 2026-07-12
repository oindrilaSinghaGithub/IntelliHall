"""
IntelliHall — User Pydantic Schemas

Defines request/response shapes for the User resource.

Schema hierarchy:
    UserBase        – shared readable fields (name, email, role, hall_id, verification)
    ├── UserCreate  – adds password (plain-text, hashed by service layer)
    ├── UserUpdate  – all fields optional for PATCH
    └── UserRead    – adds id, timestamps, verification detail; excludes password_hash
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import HallVerificationStatus, UserRole


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
    hall_name: str | None = Field(
        default=None,
        description="Full display name of the hall this user belongs to.",
    )
    roll_number: str | None = Field(
        default=None,
        max_length=50,
        description="Student roll number (e.g. 21CS10001). Display only.",
    )
    room_number: str | None = Field(
        default=None,
        max_length=20,
        description="Student's room number within the hall (e.g. B-302).",
    )
    hall_verification_status: HallVerificationStatus = Field(
        default=HallVerificationStatus.PENDING,
        description="Hall affiliation verification state: pending | approved | rejected.",
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
    hall_id: str | None = Field(
        default=None,
        description="Changing hall_id resets hall_verification_status to PENDING.",
    )
    room_number: str | None = Field(default=None, max_length=20)
    roll_number: str | None = Field(default=None, max_length=50)
    password: str | None = Field(
        default=None,
        min_length=8,
        description="New plain-text password (will be hashed before storage).",
    )


# ---------------------------------------------------------------------------
# Hall-only update (student PATCH /users/me/hall)
# ---------------------------------------------------------------------------

class UpdateHallRequest(BaseModel):
    """Body for PATCH /users/me/hall — updates hall affiliation and resets verification."""

    hall_id: str = Field(..., description="UUID of the new hall to affiliate with.")
    room_number: str | None = Field(
        default=None,
        max_length=20,
        description="Updated room number in the new hall (optional).",
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

    # Verification detail — exposed to admins and to the student themselves
    verified_by_admin_id: str | None = Field(
        default=None,
        description="UUID of the admin who last actioned the verification.",
    )
    hall_verified_at: datetime | None = Field(
        default=None,
        description="UTC timestamp of the most recent verification action.",
    )
    hall_rejection_reason: str | None = Field(
        default=None,
        description="Reason provided by the admin when rejecting.",
    )
