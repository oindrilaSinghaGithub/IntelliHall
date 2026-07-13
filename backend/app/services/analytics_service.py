"""
IntelliHall — Analytics Service

Business logic for hall-scoped complaint analytics.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.hall_repository import HallRepository
from app.schemas.analytics import (
    AnalyticsSummaryRead,
    CategoryCountRead,
    HallAnalyticsRead,
    MonthlyTrendPointRead,
    StatusCountRead,
)
from app.schemas.complaint import ComplaintSummary

if TYPE_CHECKING:
    from app.models.user import User


class AnalyticsService:
    """Hall analytics business logic."""

    @staticmethod
    async def get_hall_analytics(
        session: AsyncSession,
        hall_id: str,
        current_user: "User",
        *,
        months: int = 12,
    ) -> HallAnalyticsRead:
        """
        Return aggregated analytics for a hall.

        Only the hall administrator assigned to *hall_id* may access this data.
        """
        if current_user.hall_id != hall_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view analytics for your own hall.",
            )

        hall = await HallRepository.get_by_id(session, hall_id)
        if hall is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hall '{hall_id}' not found.",
            )

        counts = await AnalyticsRepository.get_summary_counts(session, hall_id)
        avg_hours = await AnalyticsRepository.get_avg_resolution_hours(session, hall_id)
        by_category = await AnalyticsRepository.count_by_category(session, hall_id)
        by_status = await AnalyticsRepository.count_by_status(session, hall_id)
        monthly_raw = await AnalyticsRepository.count_by_month(
            session, hall_id, months=months
        )
        recent = await AnalyticsRepository.get_recent_complaints(session, hall_id)

        monthly_trend = AnalyticsService._build_monthly_trend(monthly_raw, months)

        return HallAnalyticsRead(
            hall_id=hall_id,
            hall_name=hall.name,
            summary=AnalyticsSummaryRead(
                total_complaints=counts["total"],
                open_complaints=counts["open"],
                in_progress=counts["in_progress"],
                completed=counts["completed"],
                critical_complaints=counts["critical"],
                complaints_today=counts["today"],
                complaints_this_week=counts["this_week"],
                avg_resolution_time_hours=avg_hours,
            ),
            by_category=[
                CategoryCountRead(category=category, count=count)
                for category, count in by_category
            ],
            by_status=[
                StatusCountRead(status=status_value, count=count)
                for status_value, count in by_status
            ],
            monthly_trend=monthly_trend,
            recent_complaints=[
                ComplaintSummary.model_validate(complaint) for complaint in recent
            ],
        )

    @staticmethod
    def _build_monthly_trend(
        raw: list[tuple[datetime, int]],
        months: int,
    ) -> list[MonthlyTrendPointRead]:
        """
        Zero-fill missing months so the trend always spans *months* buckets.

        *raw* contains UTC month-start datetimes from ``date_trunc``.
        """
        counts_by_month: dict[str, int] = {}
        for month_dt, count in raw:
            key = month_dt.astimezone(timezone.utc).strftime("%Y-%m")
            counts_by_month[key] = count

        now = datetime.now(timezone.utc)
        year = now.year
        month = now.month
        points: list[MonthlyTrendPointRead] = []

        for _ in range(months):
            key = f"{year:04d}-{month:02d}"
            points.append(
                MonthlyTrendPointRead(month=key, count=counts_by_month.get(key, 0))
            )
            month -= 1
            if month == 0:
                month = 12
                year -= 1

        points.reverse()
        return points
