"""
IntelliHall — Auth Endpoints

Endpoints
---------
POST /api/v1/auth/register   Register a new user account
POST /api/v1/auth/token      OAuth2 form login (Swagger Authorize)
POST /api/v1/auth/login      JSON login (curl / API clients)
GET  /api/v1/auth/me         Return the currently authenticated user
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, RegisterResponse, TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter()

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Create a new user account.\n\n"
        "**Rules:**\n"
        "- `email` must be unique.\n"
        "- `password` must be at least 8 characters (stored as a bcrypt hash).\n"
        "- `role` defaults to `student` if omitted.\n\n"
        "The response includes a ready-to-use JWT access token so clients "
        "do not need to immediately call `/login`."
    ),
    responses={
        201: {"description": "User registered successfully."},
        409: {"description": "A user with this e-mail already exists."},
    },
)
async def register(
    payload: RegisterRequest,
    session: DBSession,
) -> RegisterResponse:
    """Register a new user and return the user record plus a JWT."""
    user, token = await AuthService(session).register(payload)
    return RegisterResponse(user=UserRead.model_validate(user), access_token=token)


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login",
    description=(
        "Authenticate with `email` and `password`.\n\n"
        "Returns a signed **JWT Bearer token** valid for 30 minutes.\n\n"
        "Pass the token in subsequent requests as:\n"
        "```\nAuthorization: Bearer <token>\n```"
    ),
    responses={
        200: {"description": "Authentication successful."},
        401: {"description": "Incorrect e-mail or password."},
    },
)
async def login(
    payload: LoginRequest,
    session: DBSession,
) -> TokenResponse:
    """Authenticate user credentials and return a JWT access token."""
    token = await AuthService(session).login(payload)
    return TokenResponse(access_token=token)


# ---------------------------------------------------------------------------
# POST /token  — OAuth2 form endpoint consumed by Swagger's Authorize dialog
# ---------------------------------------------------------------------------

@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="OAuth2 token (Swagger)",
    description=(
        "Form-encoded login endpoint used by Swagger UI's **Authorize** dialog.\n\n"
        "Accepts `application/x-www-form-urlencoded` with fields:\n"
        "- `username` — your registered e-mail address\n"
        "- `password` — your password\n\n"
        "For API clients prefer `POST /login` which accepts JSON."
    ),
    include_in_schema=True,
    responses={
        200: {"description": "Authentication successful."},
        401: {"description": "Incorrect username or password."},
    },
)
async def token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: DBSession,
) -> TokenResponse:
    """
    OAuth2 password-flow endpoint for Swagger UI.

    ``username`` is treated as the user's e-mail address so that the
    Swagger Authorize dialog works out of the box without any schema changes.
    """
    jwt_token = await AuthService(session).login(
        LoginRequest(email=form_data.username, password=form_data.password)
    )
    return TokenResponse(access_token=jwt_token)


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description=(
        "Return the profile of the currently authenticated user.\n\n"
        "Requires a valid `Authorization: Bearer <token>` header.\n\n"
        "`password_hash` is never included in the response."
    ),
    responses={
        200: {"description": "Authenticated user's profile."},
        401: {"description": "Missing or invalid Bearer token."},
    },
)
async def me(current_user: CurrentUser) -> UserRead:
    """Return the authenticated user's profile (requires Bearer token)."""
    return UserRead.model_validate(current_user)
