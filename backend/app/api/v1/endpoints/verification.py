"""
IntelliHall — Hall Verification Endpoints

Role model
----------
HALL_ADMIN : list pending requests / approve / reject (own hall only)
STUDENT    : change their own hall affiliation

Endpoints
---------
GET  /api/v1/verification/pending
    List PENDING hall verification requests for the admin's hall.        200

POST /api/v1/verification/{user_id}/approve
    Approve a student's hall affiliation [HALL_ADMIN only].             200

POST /api/v1/verification/{user_id}/reject
    Reject a student's hall affiliation [HALL_ADMIN only].             200

PATCH /api/v1/users/me/hall
    Student changes their hall → resets verification to PENDING.        200
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.hall_repository import HallRepository
from app.schemas.user import UpdateHallRequest, UserRead
from app.schemas.verification import (
    PaginatedVerificationResponse,
    VerificationActionRequest,
    VerificationRequestRead,
)
from app.services.verification_service import VerificationService
from fastapi import HTTPException

router = APIRouter()

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

DBSession   = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


# ---------------------------------------------------------------------------
# GET /verification/pending
# ---------------------------------------------------------------------------

@router.get(
    "/pending",
    response_model=PaginatedVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="List pending hall verification requests",
    description=(
        "Return paginated students whose hall affiliation is **PENDING** "
        "for the authenticated Hall Admin's hall.\n\n"
        "Requires `HALL_ADMIN` role."
    ),
    responses={
        200: {"description": "Paginated list of pending verification requests."},
        403: {"description": "Caller is not a Hall Admin or has no hall assigned."},
    },
)
async def list_pending(
    current_user: CurrentUser,
    session: DBSession,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(default=25, ge=1, le=100, description="Items per page."),
) -> PaginatedVerificationResponse:
    """List PENDING verification requests for the admin's hall."""
    return await VerificationService.list_pending(
        session=session,
        current_admin=current_user,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# POST /verification/{user_id}/approve
# ---------------------------------------------------------------------------

@router.post(
    "/{user_id}/approve",
    response_model=VerificationRequestRead,
    status_code=status.HTTP_200_OK,
    summary="Approve a student's hall affiliation",
    description=(
        "Set `hall_verification_status = approved` for the given student.\n\n"
        "Requires `HALL_ADMIN` role. Admin may only approve students from "
        "their own hall."
    ),
    responses={
        200: {"description": "Verification approved successfully."},
        403: {"description": "Not a Hall Admin or student is from a different hall."},
        404: {"description": "Student not found."},
        409: {"description": "Student is already approved."},
    },
)
async def approve(
    current_user: CurrentUser,
    session: DBSession,
    user_id: str = Path(..., description="UUID of the student to approve."),
    _body: VerificationActionRequest = None,
) -> VerificationRequestRead:
    """Approve a student's hall affiliation."""
    return await VerificationService.approve(
        session=session,
        user_id=user_id,
        current_admin=current_user,
    )


# ---------------------------------------------------------------------------
# POST /verification/{user_id}/reject
# ---------------------------------------------------------------------------

@router.post(
    "/{user_id}/reject",
    response_model=VerificationRequestRead,
    status_code=status.HTTP_200_OK,
    summary="Reject a student's hall affiliation",
    description=(
        "Set `hall_verification_status = rejected` for the given student.\n\n"
        "An optional `rejection_reason` can be supplied and will be shown "
        "to the student on their dashboard.\n\n"
        "Requires `HALL_ADMIN` role. Admin may only reject students from "
        "their own hall."
    ),
    responses={
        200: {"description": "Verification rejected."},
        403: {"description": "Not a Hall Admin or student is from a different hall."},
        404: {"description": "Student not found."},
    },
)
async def reject(
    current_user: CurrentUser,
    session: DBSession,
    user_id: str = Path(..., description="UUID of the student to reject."),
    body: VerificationActionRequest | None = None,
) -> VerificationRequestRead:
    """Reject a student's hall affiliation with an optional reason."""
    reason = body.rejection_reason if body else None
    return await VerificationService.reject(
        session=session,
        user_id=user_id,
        current_admin=current_user,
        reason=reason,
    )


# ---------------------------------------------------------------------------
# PATCH /users/me/hall  (student self-service)
# ---------------------------------------------------------------------------

@router.patch(
    "/me/hall",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Update own hall affiliation",
    description=(
        "Allows a student to change their registered hall and/or room number.\n\n"
        "**Changing the hall always resets `hall_verification_status` to `pending`.** "
        "The student will not be able to submit new complaints until the new Hall "
        "Admin approves their affiliation.\n\n"
        "Existing complaints are **not affected** — they retain the hall they "
        "were originally filed under."
    ),
    responses={
        200: {"description": "Hall updated; verification reset to pending."},
        400: {"description": "The requested hall does not exist."},
        401: {"description": "Not authenticated."},
    },
)
async def update_my_hall(
    body: UpdateHallRequest,
    current_user: CurrentUser,
    session: DBSession,
) -> UserRead:
    """Student updates their hall — triggers re-verification."""
    # Validate that the requested hall exists
    hall = await HallRepository.get_by_id(session, body.hall_id)
    if hall is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Hall '{body.hall_id}' does not exist.",
        )

    updated = await VerificationService.change_hall(
        session=session,
        user_id=current_user.id,
        new_hall_id=body.hall_id,
        room_number=body.room_number,
    )
    # Re-fetch the full user so hall_name is eagerly loaded
    from app.repositories.user_repository import UserRepository
    full_user = await UserRepository(session).get_by_id(updated.id)
    return UserRead.model_validate(full_user)
