"""
IntelliHall — Hall Endpoints

Provides CRUD and user-assignment operations for the Hall resource.

Endpoints
---------
POST   /api/v1/halls/                           Create a hall             201  [HALL_ADMIN]
GET    /api/v1/halls/                           List all halls            200  [authenticated]
GET    /api/v1/halls/{hall_id}                  Get a hall                200  [authenticated]
PATCH  /api/v1/halls/{hall_id}                  Partial update            200  [HALL_ADMIN]
DELETE /api/v1/halls/{hall_id}                  Delete a hall             204  [HALL_ADMIN]
POST   /api/v1/halls/{hall_id}/assign-user      Assign user to hall       200  [HALL_ADMIN]
DELETE /api/v1/halls/{hall_id}/unassign-user/{user_id}
                                                Remove user from hall     200  [HALL_ADMIN]

Authorization model
-------------------
- Read operations (GET /) and (GET /{id}) require a valid Bearer token.
- All write operations require the token to belong to a HALL_ADMIN.
- Role enforcement is done via the ``require_hall_admin`` dependency so the
  service layer stays clean of HTTP concerns.

Design
------
- Every handler is a thin delegation call to HallService.
- Response schemas are validated via model_validate() so ORM objects are
  never leaked directly to the HTTP response.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.halls import require_hall_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.complaint import (
    ComplaintSummary,
    HallComplaintFilters,
    PaginatedResponse,
)
from app.schemas.hall import AssignUserRequest, HallCreate, HallRead, HallUpdate, HallPublicRead
from app.schemas.user import UserRead
from app.services.complaint_service import ComplaintService
from app.services.hall_service import HallService

router = APIRouter()

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

DBSession   = Annotated[AsyncSession, Depends(get_db)]
AuthUser    = Annotated[User, Depends(get_current_user)]
AdminUser   = Annotated[User, Depends(require_hall_admin)]


# ---------------------------------------------------------------------------
# POST /
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=HallRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a hall",
    description=(
        "Create a new residential hall.\n\n"
        "**Requires:** `HALL_ADMIN` role.\n\n"
        "**Rules:**\n"
        "- `name` must be unique.\n"
        "- `code` must be unique (automatically uppercased on write).\n\n"
        "Example codes: `TH` (Tagore Hall), `RH` (Radha Hall)."
    ),
    responses={
        201: {"description": "Hall created successfully."},
        401: {"description": "Missing or invalid Bearer token."},
        403: {"description": "Caller is not a HALL_ADMIN."},
        409: {"description": "A hall with that name or code already exists."},
    },
)
async def create_hall(
    payload: HallCreate,
    session: DBSession,
    _admin: AdminUser,
) -> HallRead:
    """Create a new hall. Requires HALL_ADMIN role."""
    hall = await HallService.create(session, payload)
    return HallRead.model_validate(hall)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=list[HallRead],
    status_code=status.HTTP_200_OK,
    summary="List all halls",
    description=(
        "Return every hall in the system, ordered alphabetically by name.\n\n"
        "**Requires:** any valid Bearer token.\n\n"
        "Useful for populating drop-down menus in the student registration flow."
    ),
    responses={
        200: {"description": "List of halls (may be empty)."},
        401: {"description": "Missing or invalid Bearer token."},
    },
)
async def list_halls(
    session: DBSession,
    _user: AuthUser,
) -> list[HallRead]:
    """Return all halls (requires authentication)."""
    halls = await HallService.list_all(session)
    return [HallRead.model_validate(h) for h in halls]


# ---------------------------------------------------------------------------
# GET /public
# ---------------------------------------------------------------------------

@router.get(
    "/public",
    response_model=list[HallPublicRead],
    status_code=status.HTTP_200_OK,
    summary="List all halls publicly",
    description=(
        "Return a public list of every hall in the system, "
        "containing only ID and Name. Does not require authentication."
    ),
    responses={
        200: {"description": "List of public halls (may be empty)."},
    },
)
async def list_halls_public(
    session: DBSession,
) -> list[HallPublicRead]:
    """Return all halls publicly (does not require authentication)."""
    halls = await HallService.list_all(session)
    return [HallPublicRead.model_validate(h) for h in halls]


# ---------------------------------------------------------------------------
# GET /{hall_id}
# ---------------------------------------------------------------------------

@router.get(
    "/{hall_id}",
    response_model=HallRead,
    status_code=status.HTTP_200_OK,
    summary="Get a hall",
    description=(
        "Retrieve the details of a single hall by its UUID.\n\n"
        "**Requires:** any valid Bearer token."
    ),
    responses={
        200: {"description": "Hall found."},
        401: {"description": "Missing or invalid Bearer token."},
        404: {"description": "No hall with the given ID exists."},
    },
)
async def get_hall(
    hall_id: Annotated[str, Path(description="UUID of the hall to retrieve.")],
    session: DBSession,
    _user: AuthUser,
) -> HallRead:
    """Fetch a single hall by ID (404 if not found)."""
    hall = await HallService.get_or_404(session, hall_id)
    return HallRead.model_validate(hall)


# ---------------------------------------------------------------------------
# PATCH /{hall_id}
# ---------------------------------------------------------------------------

@router.patch(
    "/{hall_id}",
    response_model=HallRead,
    status_code=status.HTTP_200_OK,
    summary="Update a hall",
    description=(
        "Partially update a hall's `name` and/or `code`.\n\n"
        "**Requires:** `HALL_ADMIN` role.\n\n"
        "Only supplied fields are modified — omitted fields keep their current values.\n\n"
        "`code` values are automatically uppercased."
    ),
    responses={
        200: {"description": "Hall updated successfully."},
        400: {"description": "No updatable fields were provided."},
        401: {"description": "Missing or invalid Bearer token."},
        403: {"description": "Caller is not a HALL_ADMIN."},
        404: {"description": "No hall with the given ID exists."},
        409: {"description": "The new name or code conflicts with another hall."},
    },
)
async def update_hall(
    hall_id: Annotated[str, Path(description="UUID of the hall to update.")],
    payload: HallUpdate,
    session: DBSession,
    _admin: AdminUser,
) -> HallRead:
    """Partially update a hall. Requires HALL_ADMIN role."""
    hall = await HallService.update(session, hall_id, payload)
    return HallRead.model_validate(hall)


# ---------------------------------------------------------------------------
# DELETE /{hall_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/{hall_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
    summary="Delete a hall",
    description=(
        "Permanently delete a hall.\n\n"
        "**Requires:** `HALL_ADMIN` role.\n\n"
        "> ⚠️ **Cascading delete:** All users assigned to this hall will have "
        "their `hall_id` set to `NULL`. All complaints belonging to the hall "
        "will be deleted."
    ),
    responses={
        401: {"description": "Missing or invalid Bearer token."},
        403: {"description": "Caller is not a HALL_ADMIN."},
        404: {"description": "No hall with the given ID exists."},
    },
)
async def delete_hall(
    hall_id: Annotated[str, Path(description="UUID of the hall to delete.")],
    session: DBSession,
    _admin: AdminUser,
) -> None:
    """Hard-delete a hall. Requires HALL_ADMIN role."""
    await HallService.delete(session, hall_id)


# ---------------------------------------------------------------------------
# POST /{hall_id}/assign-user
# ---------------------------------------------------------------------------

@router.post(
    "/{hall_id}/assign-user",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Assign a user to a hall",
    description=(
        "Assign an existing user to this hall (sets the user's `hall_id`).\n\n"
        "**Requires:** `HALL_ADMIN` role.\n\n"
        "If the user is already assigned to a different hall, their assignment "
        "is **replaced** (not blocked). This allows admins to transfer students "
        "between halls.\n\n"
        "Raises `404` if either the hall or the user does not exist."
    ),
    responses={
        200: {"description": "User assigned to hall successfully. Returns the updated user."},
        401: {"description": "Missing or invalid Bearer token."},
        403: {"description": "Caller is not a HALL_ADMIN."},
        404: {"description": "Hall or user not found."},
    },
)
async def assign_user_to_hall(
    hall_id: Annotated[str, Path(description="UUID of the hall.")],
    payload: AssignUserRequest,
    session: DBSession,
    _admin: AdminUser,
) -> UserRead:
    """Assign a user to this hall. Requires HALL_ADMIN role."""
    user = await HallService.assign_user(session, hall_id, payload.user_id)
    return UserRead.model_validate(user)


# ---------------------------------------------------------------------------
# DELETE /{hall_id}/unassign-user/{user_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/{hall_id}/unassign-user/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Remove a user from a hall",
    description=(
        "Remove a user's hall assignment (`hall_id` → `NULL`).\n\n"
        "**Requires:** `HALL_ADMIN` role.\n\n"
        "The `hall_id` path parameter is validated to confirm the hall exists.\n"
        "The user does **not** need to currently belong to that specific hall — "
        "the call simply clears whatever hall they are assigned to."
    ),
    responses={
        200: {"description": "User unassigned successfully. Returns the updated user."},
        401: {"description": "Missing or invalid Bearer token."},
        403: {"description": "Caller is not a HALL_ADMIN."},
        404: {"description": "Hall or user not found."},
    },
)
async def unassign_user_from_hall(
    hall_id: Annotated[str, Path(description="UUID of the hall (must exist).")],
    user_id: Annotated[str, Path(description="UUID of the user to unassign.")],
    session: DBSession,
    _admin: AdminUser,
) -> UserRead:
    """Remove a user's hall assignment. Requires HALL_ADMIN role."""
    # Validate the hall exists before touching the user
    await HallService.get_or_404(session, hall_id)
    user = await HallService.unassign_user(session, user_id)
    return UserRead.model_validate(user)


# ---------------------------------------------------------------------------
# GET /{hall_id}/complaints  — Admin: list all complaints for a hall
# ---------------------------------------------------------------------------

@router.get(
    "/{hall_id}/complaints",
    response_model=PaginatedResponse[ComplaintSummary],
    status_code=status.HTTP_200_OK,
    summary="List complaints for a hall",
    description=(
        "Return a paginated list of all complaints belonging to the specified hall.\n\n"
        "**Requires:** `HALL_ADMIN` role.\n\n"
        "The calling admin must be assigned to the same hall they are querying — "
        "cross-hall access is rejected with HTTP `403`.\n\n"
        "**Filterable by:** `status`, `priority`, `category`, `complaint_type`.\n\n"
        "**Sortable columns:** `created_at`, `updated_at`, `priority`, "
        "`status`, `category`, `title`.\n\n"
        "Results are ordered newest-first by default."
    ),
    responses={
        200: {"description": "Paginated list of complaint summaries for the hall."},
        401: {"description": "Missing or invalid Bearer token."},
        403: {"description": "Not a HALL_ADMIN, or querying a different hall."},
        404: {"description": "Hall not found."},
    },
    tags=["halls"],
)
async def list_hall_complaints(
    hall_id: Annotated[str, Path(description="UUID of the hall to list complaints for.")],
    session: DBSession,
    current_user: AdminUser,
    filters: Annotated[HallComplaintFilters, Depends()],
) -> PaginatedResponse[ComplaintSummary]:
    """List all complaints for a hall (HALL_ADMIN only, own hall)."""
    # Verify the hall itself exists (service checks admin's hall membership)
    await HallService.get_or_404(session, hall_id)
    return await ComplaintService.list_for_hall(session, hall_id, filters, current_user)
