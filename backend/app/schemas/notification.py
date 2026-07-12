"""
IntelliHall — Notification Pydantic Schemas
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationRead(BaseModel):
    """Read-only schema for a notification."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="UUID primary key.")
    user_id: str = Field(..., description="Recipient user UUID.")
    complaint_id: str | None = Field(default=None, description="Related complaint UUID.")
    message: str = Field(..., description="Notification message text.")
    is_read: bool = Field(..., description="Whether the user has read this notification.")
    created_at: datetime = Field(..., description="UTC creation timestamp.")


class PaginatedNotificationResponse(BaseModel):
    """Paginated list of notifications."""

    items: list[NotificationRead]
    total: int = Field(..., description="Total matching records.")
    page: int = Field(..., description="Current page (1-indexed).")
    page_size: int = Field(..., description="Items per page.")
    pages: int = Field(..., description="Total number of pages.")
    unread_count: int = Field(..., description="Total unread notifications.")


class UnreadCountResponse(BaseModel):
    """Simple unread count response."""

    unread_count: int = Field(..., description="Number of unread notifications.")
