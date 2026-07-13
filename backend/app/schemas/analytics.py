"""
IntelliHall — Hall Analytics Pydantic Schemas

Response shapes for GET /halls/{hall_id}/analytics.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ComplaintCategory, ComplaintStatus
from app.schemas.complaint import ComplaintSummary


class AnalyticsSummaryRead(BaseModel):
    """High-level KPI counts for a hall."""

    total_complaints: int = Field(..., description="All complaints ever filed in this hall.")
    open_complaints: int = Field(
        ...,
        description="Complaints not yet closed (status != closed).",
    )
    in_progress: int = Field(..., description="Complaints with status in_progress.")
    completed: int = Field(..., description="Complaints with status closed.")
    critical_complaints: int = Field(
        ...,
        description="Active critical-priority complaints (priority=critical, not closed).",
    )
    complaints_today: int = Field(
        ...,
        description="Complaints created since midnight UTC today.",
    )
    complaints_this_week: int = Field(
        ...,
        description="Complaints created since Monday 00:00 UTC this week.",
    )
    avg_resolution_time_hours: float | None = Field(
        default=None,
        description=(
            "Average hours from complaint creation to first closed status transition. "
            "Null when no closed complaints exist."
        ),
    )


class CategoryCountRead(BaseModel):
    """Complaint count grouped by maintenance category."""

    category: ComplaintCategory
    count: int


class StatusCountRead(BaseModel):
    """Complaint count grouped by lifecycle status."""

    status: ComplaintStatus
    count: int


class MonthlyTrendPointRead(BaseModel):
    """Complaint volume for a single calendar month."""

    month: str = Field(..., description="Month key in YYYY-MM format.")
    count: int


class HallAnalyticsRead(BaseModel):
    """Full analytics payload for a hall administrator dashboard."""

    hall_id: str
    hall_name: str
    summary: AnalyticsSummaryRead
    by_category: list[CategoryCountRead]
    by_status: list[StatusCountRead]
    monthly_trend: list[MonthlyTrendPointRead]
    recent_complaints: list[ComplaintSummary]
