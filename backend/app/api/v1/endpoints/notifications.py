"""
IntelliHall — Notification Endpoints

GET    /api/v1/notifications/              — list notifications (paginated)
GET    /api/v1/notifications/unread-count  — unread count
PATCH  /api/v1/notifications/{id}/read     — mark one as read
PATCH  /api/v1/notifications/read-all      — mark all as read
"""

from __future__ import annotations

import math
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import (
    NotificationRead,
    PaginatedNotificationResponse,
    UnreadCountResponse,
)

router = APIRouter()

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

DBSession  = Annotated[AsyncSession, Depends(get_db)]
AuthUser   = Annotated[User, Depends(get_current_user)]


# ---------------------------------------------------------------------------
# GET /notifications/
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=PaginatedNotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="List my notifications",
    description="Return a paginated list of notifications for the authenticated user.",
    tags=["notifications"],
)
async def list_notifications(
    session: DBSession,
    current_user: AuthUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    unread_only: Annotated[bool, Query()] = False,
) -> PaginatedNotificationResponse:
    """List notifications for the current user (paginated)."""
    items, total = await NotificationRepository.list_for_user(
        session,
        current_user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )
    unread_count = await NotificationRepository.get_unread_count(session, current_user.id)
    notifications = [NotificationRead.model_validate(n) for n in items]
    pages = math.ceil(total / page_size) if total > 0 else 1

    return PaginatedNotificationResponse(
        items=notifications,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        unread_count=unread_count,
    )


# ---------------------------------------------------------------------------
# GET /notifications/unread-count
# ---------------------------------------------------------------------------

@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    status_code=status.HTTP_200_OK,
    summary="Get unread notification count",
    description="Return the number of unread notifications for the authenticated user.",
    tags=["notifications"],
)
async def get_unread_count(
    session: DBSession,
    current_user: AuthUser,
) -> UnreadCountResponse:
    """Get the count of unread notifications for the current user."""
    count = await NotificationRepository.get_unread_count(session, current_user.id)
    return UnreadCountResponse(unread_count=count)


# ---------------------------------------------------------------------------
# PATCH /notifications/read-all   ← must be defined BEFORE /{id}/read
# so FastAPI matches the literal path before the parameterised one
# ---------------------------------------------------------------------------

@router.patch(
    "/read-all",
    status_code=status.HTTP_200_OK,
    summary="Mark all notifications as read",
    description="Mark all unread notifications as read for the authenticated user.",
    tags=["notifications"],
)
async def mark_all_read(
    session: DBSession,
    current_user: AuthUser,
) -> dict[str, int]:
    """Mark all notifications as read for the current user."""
    count = await NotificationRepository.mark_all_read(session, current_user.id)
    await session.commit()
    return {"marked_read": count}


# ---------------------------------------------------------------------------
# PATCH /notifications/{notification_id}/read
# ---------------------------------------------------------------------------

@router.patch(
    "/{notification_id}/read",
    response_model=NotificationRead,
    status_code=status.HTTP_200_OK,
    summary="Mark notification as read",
    description="Mark a single notification as read.",
    tags=["notifications"],
)
async def mark_notification_read(
    notification_id: Annotated[str, Path(description="UUID of the notification.")],
    session: DBSession,
    current_user: AuthUser,
) -> NotificationRead:
    """Mark a notification as read."""
    notification = await NotificationRepository.mark_read(
        session, notification_id, current_user.id
    )
    if notification is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or does not belong to you.",
        )
    await session.commit()
    return NotificationRead.model_validate(notification)
