"""
IntelliHall — Complaint Endpoints

Provides the full CRUD surface for the Complaint resource.

Endpoints
---------
POST   /api/v1/complaints/                    Create a complaint        201
GET    /api/v1/complaints/                    List / filter complaints  200
GET    /api/v1/complaints/{complaint_id}      Get single complaint      200
PATCH  /api/v1/complaints/{complaint_id}      Partial update            200
DELETE /api/v1/complaints/{complaint_id}      Hard delete               204

Design decisions
----------------
- The router is intentionally thin: every handler is a one-liner that
  delegates entirely to ComplaintService.
- `Annotated[AsyncSession, Depends(get_db)]` is the standard DI pattern used
  throughout IntelliHall; no authentication is wired yet.
- Filter query-params are collected via `Depends(ComplaintFilters)` which
  gives us automatic Swagger documentation and Pydantic validation for free.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintFilters,
    ComplaintRead,
    ComplaintSummary,
    ComplaintUpdate,
    PaginatedResponse,
)
from app.services.complaint_service import ComplaintService

router = APIRouter()

# ---------------------------------------------------------------------------
# Type alias for the injected DB session
# ---------------------------------------------------------------------------

DBSession = Annotated[AsyncSession, Depends(get_db)]


# ---------------------------------------------------------------------------
# POST /
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=ComplaintRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a complaint",
    description=(
        "Raise a new maintenance complaint.\n\n"
        "**Business rules enforced:**\n"
        "- `PERSONAL` complaints require `room_number`.\n"
        "- `COMMON_AREA` complaints require at least one of "
        "`block`, `floor`, `common_area`, or `qr_location_id`.\n\n"
        "The initial status is always **SUBMITTED**."
    ),
    responses={
        201: {"description": "Complaint created successfully."},
        400: {"description": "Validation error — check business rules above."},
    },
    tags=["complaints"],
)
async def create_complaint(
    payload: ComplaintCreate,
    session: DBSession,
) -> ComplaintRead:
    """Create and return a new complaint."""
    complaint = await ComplaintService.create(session, payload)
    return ComplaintRead.model_validate(complaint)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=PaginatedResponse[ComplaintSummary],
    status_code=status.HTTP_200_OK,
    summary="List complaints",
    description=(
        "Retrieve a paginated, filtered, and sorted list of complaints.\n\n"
        "All filter parameters are optional — omitting a parameter means "
        "**no filter** is applied on that column.\n\n"
        "**Sortable columns:** `created_at`, `updated_at`, `priority`, "
        "`status`, `category`, `title`."
    ),
    responses={
        200: {"description": "Paginated list of complaint summaries."},
    },
    tags=["complaints"],
)
async def list_complaints(
    session: DBSession,
    filters: Annotated[ComplaintFilters, Depends()],
) -> PaginatedResponse[ComplaintSummary]:
    """Return a paginated page of complaint summaries matching the filters."""
    return await ComplaintService.list(session, filters)


# ---------------------------------------------------------------------------
# GET /{complaint_id}
# ---------------------------------------------------------------------------


@router.get(
    "/{complaint_id}",
    response_model=ComplaintRead,
    status_code=status.HTTP_200_OK,
    summary="Get a complaint",
    description=(
        "Retrieve the full detail of a single complaint by its UUID.\n\n"
        "The response includes attached **images** and the full "
        "**status-change history**."
    ),
    responses={
        200: {"description": "Complaint found."},
        404: {"description": "No complaint with the given ID exists."},
    },
    tags=["complaints"],
)
async def get_complaint(
    complaint_id: Annotated[
        str,
        Path(description="UUID of the complaint to retrieve."),
    ],
    session: DBSession,
) -> ComplaintRead:
    """Fetch a single complaint by ID (404 if not found)."""
    complaint = await ComplaintService.get_or_404(session, complaint_id)
    return ComplaintRead.model_validate(complaint)


# ---------------------------------------------------------------------------
# PATCH /{complaint_id}
# ---------------------------------------------------------------------------


@router.patch(
    "/{complaint_id}",
    response_model=ComplaintRead,
    status_code=status.HTTP_200_OK,
    summary="Update a complaint",
    description=(
        "Partially update a complaint.\n\n"
        "Only the fields supplied in the request body are changed; "
        "omitted fields retain their current values.\n\n"
        "Updatable fields: `title`, `description`, `priority`, `status`, "
        "`maintenance_type`, `current_assignee`, `room_number`, `block`, "
        "`floor`, `common_area`, `qr_location_id`, `preferred_visit_time`."
    ),
    responses={
        200: {"description": "Complaint updated successfully."},
        400: {"description": "No updatable fields were provided."},
        404: {"description": "No complaint with the given ID exists."},
    },
    tags=["complaints"],
)
async def update_complaint(
    complaint_id: Annotated[
        str,
        Path(description="UUID of the complaint to update."),
    ],
    payload: ComplaintUpdate,
    session: DBSession,
) -> ComplaintRead:
    """Partially update and return the updated complaint."""
    complaint = await ComplaintService.update(session, complaint_id, payload)
    return ComplaintRead.model_validate(complaint)


# ---------------------------------------------------------------------------
# DELETE /{complaint_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/{complaint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
    summary="Delete a complaint",
    description=(
        "Permanently delete a complaint and all its associated images "
        "and status-history records (cascaded at the database level)."
    ),
    responses={
        404: {"description": "No complaint with the given ID exists."},
    },
    tags=["complaints"],
)
async def delete_complaint(
    complaint_id: Annotated[
        str,
        Path(description="UUID of the complaint to delete."),
    ],
    session: DBSession,
) -> None:
    """Hard-delete a complaint (and its children) by ID."""
    await ComplaintService.delete(session, complaint_id)
