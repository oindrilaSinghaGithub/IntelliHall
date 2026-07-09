"""
IntelliHall — Auth Pydantic Schemas

Defines the request/response shapes for authentication endpoints.

    RegisterRequest  – POST /auth/register body
    LoginRequest     – POST /auth/login body
    TokenResponse    – response carrying the JWT access token

password_hash is never exposed in any of these schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole
from app.schemas.user import UserRead


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    """Body accepted by POST /auth/register."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        examples=["Aarav Sharma"],
        description="Full display name of the new user.",
    )
    email: EmailStr = Field(
        ...,
        description="Unique login e-mail address.",
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Plain-text password (hashed server-side before storage).",
    )
    role: UserRole = Field(
        default=UserRole.STUDENT,
        description="Role of the user. Defaults to STUDENT.",
    )
    hall_id: str = Field(
        ...,
        description="UUID of the hall this user belongs to.",
    )


class LoginRequest(BaseModel):
    """Body accepted by POST /auth/login."""

    email: EmailStr = Field(..., description="Registered e-mail address.")
    password: str = Field(..., description="Plain-text password.")


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class TokenResponse(BaseModel):
    """Response returned by POST /auth/login."""

    access_token: str = Field(..., description="Signed JWT access token.")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer').")


class RegisterResponse(BaseModel):
    """Response returned by POST /auth/register — mirrors UserRead."""

    user: UserRead
    access_token: str = Field(..., description="Signed JWT access token for immediate use.")
    token_type: str = Field(default="bearer")
