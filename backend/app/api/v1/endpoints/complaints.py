"""
IntelliHall — Complaint Endpoints

Role model
----------
STUDENT  : create complaints; list/view only their own.
HALL_ADMIN: view/update/delete complaints from their hall; update status.

Endpoints
---------
POST   /api/v1/complaints/
    Create a complaint [authenticated student]                           201

GET    /api/v1/complaints/
    List the calling student's own complaints (paginated)               200

GET    /api/v1/complaints/{complaint_id}
    Student: own complaint only (403 if foreign)                        200

PATCH  /api/v1/complaints/{complaint_id}/status
    Update complaint status + write history [HALL_ADMIN only]           200

PATCH  /api/v1/complaints/{complaint_id}
    Update non-status fields [HALL_ADMIN only, own hall]               200

DELETE /api/v1/complaints/{complaint_id}
    Hard-delete [HALL_ADMIN only, own hall]                            204

Design
------
- Every handler is a thin delegation to ComplaintService.
- Authentication uses get_current_user from app.api.dependencies.auth.
- Role enforcement is done inside the service (defence-in-depth) and
  also at the router layer via require_hall_admin where appropriate.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.halls import require_hall_admin
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintFilters,
    ComplaintRead,
    ComplaintSummary,
    ComplaintUpdate,
    PaginatedResponse,
    StatusUpdateRequest,
)
from app.services.complaint_service import ComplaintService

router = APIRouter()

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

DBSession  = Annotated[AsyncSession, Depends(get_db)]
AuthUser   = Annotated[User, Depends(get_current_user)]
AdminUser  = Annotated[User, Depends(require_hall_admin)]


# ---------------------------------------------------------------------------
# POST /  — Create complaint (any authenticated user)
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=ComplaintRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a complaint",
    description=(
        "Raise a new maintenance complaint.\n\n"
        "**Requires:** any valid Bearer token (typically a student).\n\n"
        "**Business rules:**\n"
        "- Your account must be assigned to a hall.\n"
        "- `PERSONAL` complaints require `room_number`.\n"
        "- `COMMON_AREA` complaints require at least one of "
        "`block`, `floor`, `common_area`, or `qr_location_id`.\n\n"
        "`hall_id` and `created_by` are derived from your token — "
        "never supplied in the request body."
    ),
    responses={
        201: {"description": "Complaint created."},
        400: {"description": "Business-rule validation failure."},
        401: {"description": "Missing or invalid Bearer token."},
        403: {"description": "Account not assigned to a hall."},
    },
    tags=["complaints"],
)
async def create_complaint(
    payload: ComplaintCreate,
    session: DBSession,
    current_user: AuthUser,
) -> ComplaintRead:
    """Create and return a new complaint (authenticated users only)."""
    complaint = await ComplaintService.create(session, payload, current_user)
    return ComplaintRead.model_validate(complaint)


# ---------------------------------------------------------------------------
# GET /  — Student: list own complaints
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=PaginatedResponse[ComplaintSummary],
    status_code=status.HTTP_200_OK,
    summary="List my complaints",
    description=(
        "Return a paginated list of complaints **created by the authenticated user**.\n\n"
        "**Requires:** any valid Bearer token.\n\n"
        "Results are always scoped to the calling user — you cannot query other "
        "users' complaints through this endpoint.\n\n"
        "**Sortable columns:** `created_at`, `updated_at`, `priority`, "
        "`status`, `category`, `title`."
    ),
    responses={
        200: {"description": "Paginated list of the caller's own complaints."},
        401: {"description": "Missing or invalid Bearer token."},
    },
    tags=["complaints"],
)
async def list_my_complaints(
    session: DBSession,
    current_user: AuthUser,
    filters: Annotated[ComplaintFilters, Depends()],
) -> PaginatedResponse[ComplaintSummary]:
    """Return the authenticated user's own complaints (paginated)."""
    return await ComplaintService.list_for_student(session, filters, current_user)


# ---------------------------------------------------------------------------
# GET /{complaint_id}  — Student: own complaint detail
# ---------------------------------------------------------------------------

@router.get(
    "/{complaint_id}",
    response_model=ComplaintRead,
    status_code=status.HTTP_200_OK,
    summary="Get my complaint",
    description=(
        "Retrieve the full detail of one of **your own** complaints.\n\n"
        "**Requires:** any valid Bearer token.\n\n"
        "Returns the complaint with attached **images** and full **status-history**.\n\n"
        "Returns `403` if the complaint belongs to another user.\n"
        "Returns `404` if the complaint does not exist."
    ),
    responses={
        200: {"description": "Complaint detail (with images and status history)."},
        401: {"description": "Missing or invalid Bearer token."},
        403: {"description": "Complaint belongs to another user/hall."},
        404: {"description": "Complaint not found."},
    },
    tags=["complaints"],
)
async def get_my_complaint(
    complaint_id: Annotated[str, Path(description="UUID of the complaint.")],
    session: DBSession,
    current_user: AuthUser,
) -> ComplaintRead:
    """Fetch a single complaint by ID — must belong to the calling user or admin's hall."""
    if current_user.role == UserRole.HALL_ADMIN:
        complaint = await ComplaintService.get_for_admin(session, complaint_id, current_user)
    else:
        complaint = await ComplaintService.get_for_student(session, complaint_id, current_user)
    return ComplaintRead.model_validate(complaint)


# ---------------------------------------------------------------------------
# PATCH /{complaint_id}/status  — Admin: status transition
# ---------------------------------------------------------------------------

@router.patch(
    "/{complaint_id}/status",
    response_model=ComplaintRead,
    status_code=status.HTTP_200_OK,
    summary="Update complaint status",
    description=(
        "Transition a complaint to a new status.\n\n"
        "**Requires:** `HALL_ADMIN` role. The complaint must belong to your hall.\n\n"
        "**Allowed transitions:**\n"
        "```\n"
        "SUBMITTED              → VERIFIED\n"
        "VERIFIED               → SCHEDULED\n"
        "SCHEDULED              → IN_PROGRESS\n"
        "IN_PROGRESS            → COMPLETED\n"
        "COMPLETED              → WAITING_STUDENT_CONFIRMATION\n"
        "WAITING_STUDENT_CONFIRMATION → CLOSED\n"
        "ANY                    → VISIT_FAILED_ROOM_LOCKED\n"
        "```\n\n"
        "Every successful transition automatically creates a "
        "**ComplaintStatusHistory** audit record containing `previous_status`, "
        "`new_status`, `updated_by`, `remarks`, and `timestamp`."
    ),
    responses={
        200: {"description": "Status updated. Returns the updated complaint."},
        400: {"description": "Invalid transition for the current status."},
        401: {"description": "Missing or invalid Bearer token."},
        403: {"description": "Not a HALL_ADMIN, or complaint is from another hall."},
        404: {"description": "Complaint not found."},
    },
    tags=["complaints"],
)
async def update_complaint_status(
    complaint_id: Annotated[str, Path(description="UUID of the complaint.")],
    payload: StatusUpdateRequest,
    session: DBSession,
    current_user: AdminUser,
) -> ComplaintRead:
    """Transition complaint status (HALL_ADMIN only). Writes an audit record."""
    complaint = await ComplaintService.update_status(
        session, complaint_id, payload, current_user
    )
    return ComplaintRead.model_validate(complaint)


# ---------------------------------------------------------------------------
# PATCH /{complaint_id}  — Admin: update non-status fields
# ---------------------------------------------------------------------------

@router.patch(
    "/{complaint_id}",
    response_model=ComplaintRead,
    status_code=status.HTTP_200_OK,
    summary="Update complaint fields",
    description=(
        "Partially update a complaint's non-status fields.\n\n"
        "**Requires:** `HALL_ADMIN` role. The complaint must belong to your hall.\n\n"
        "Updatable fields: `title`, `description`, `priority`, "
        "`maintenance_type`, `current_assignee`, `room_number`, `block`, "
        "`floor`, `common_area`, `qr_location_id`, `preferred_visit_time`.\n\n"
        "> Use `PATCH /status` to change the lifecycle status — that endpoint "
        "enforces valid transitions and writes an audit record."
    ),
    responses={
        200: {"description": "Complaint updated. Returns updated complaint."},
        400: {"description": "No updatable fields were provided."},
        401: {"description": "Missing or invalid Bearer token."},
        403: {"description": "Not a HALL_ADMIN, or complaint is from another hall."},
        404: {"description": "Complaint not found."},
    },
    tags=["complaints"],
)
async def update_complaint(
    complaint_id: Annotated[str, Path(description="UUID of the complaint.")],
    payload: ComplaintUpdate,
    session: DBSession,
    current_user: AdminUser,
) -> ComplaintRead:
    """Partially update complaint fields (HALL_ADMIN only, own hall)."""
    complaint = await ComplaintService.update(session, complaint_id, payload, current_user)
    return ComplaintRead.model_validate(complaint)


# ---------------------------------------------------------------------------
# DELETE /{complaint_id}  — Admin: hard delete
# ---------------------------------------------------------------------------

@router.delete(
    "/{complaint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
    summary="Delete a complaint",
    description=(
        "Permanently delete a complaint and all its images and history records.\n\n"
        "**Requires:** `HALL_ADMIN` role. The complaint must belong to your hall."
    ),
    responses={
        401: {"description": "Missing or invalid Bearer token."},
        403: {"description": "Not a HALL_ADMIN, or complaint is from another hall."},
        404: {"description": "Complaint not found."},
    },
    tags=["complaints"],
)
async def delete_complaint(
    complaint_id: Annotated[str, Path(description="UUID of the complaint.")],
    session: DBSession,
    current_user: AdminUser,
) -> None:
    """Hard-delete a complaint (HALL_ADMIN only, own hall)."""
    await ComplaintService.delete(session, complaint_id, current_user)
