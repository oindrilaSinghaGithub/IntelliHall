"""
IntelliHall — Verification Pydantic Schemas

Defines request/response shapes for the Hall Verification workflow.

    VerificationRequestRead   – Student card shown to the Hall Admin
    VerificationActionRequest – Body for approve/reject endpoints
    PaginatedVerificationResponse – Paginated list of verification requests
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import HallVerificationStatus


# ---------------------------------------------------------------------------
# Student card — read-only, shown to the admin
# ---------------------------------------------------------------------------

class VerificationRequestRead(BaseModel):
    """
    Student data shown to the Hall Admin on the Pending Verifications page.
    Mirrors the relevant subset of UserRead — no sensitive fields.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="User UUID.")
    name: str = Field(..., description="Student's full name.")
    email: str = Field(..., description="Student's e-mail address.")
    roll_number: str | None = Field(default=None, description="Student roll number.")
    room_number: str | None = Field(default=None, description="Requested room number.")
    hall_id: str | None = Field(default=None, description="Requested hall UUID.")
    hall_name: str | None = Field(default=None, description="Requested hall name.")
    hall_verification_status: HallVerificationStatus = Field(
        ..., description="Current verification state."
    )
    hall_rejection_reason: str | None = Field(
        default=None, description="Rejection reason (if applicable)."
    )
    created_at: datetime = Field(..., description="When the account was created.")
    updated_at: datetime = Field(..., description="When the record was last updated.")


# ---------------------------------------------------------------------------
# Admin action — approve or reject a student
# ---------------------------------------------------------------------------

class VerificationActionRequest(BaseModel):
    """Body for POST /verification/{user_id}/approve and /reject."""

    rejection_reason: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional reason text when rejecting. Ignored on approve.",
    )


# ---------------------------------------------------------------------------
# Paginated response wrapper
# ---------------------------------------------------------------------------

class PaginatedVerificationResponse(BaseModel):
    """Paginated list of verification requests."""

    items: list[VerificationRequestRead]
    total: int = Field(..., description="Total matching records.")
    page: int = Field(..., description="Current page number (1-indexed).")
    page_size: int = Field(..., description="Number of items per page.")
    total_pages: int = Field(..., description="Total number of pages.")
