"""
IntelliHall — Hall Analytics Endpoints

GET /api/v1/halls/{hall_id}/analytics — aggregated complaint metrics
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.halls import require_hall_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import HallAnalyticsRead
from app.services.analytics_service import AnalyticsService

router = APIRouter()

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

DBSession = Annotated[AsyncSession, Depends(get_db)]
AdminUser = Annotated[User, Depends(require_hall_admin)]


# ---------------------------------------------------------------------------
# GET / — Hall analytics dashboard data
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=HallAnalyticsRead,
    summary="Get hall analytics",
    description=(
        "Return aggregated complaint analytics for a hall.\n\n"
        "**Requires:** `HALL_ADMIN` role for the specified hall.\n\n"
        "All metrics are computed server-side using SQL aggregations. "
        "Includes KPI summary counts, category/status breakdowns, "
        "monthly trend, average resolution time, and the 5 most recent complaints."
    ),
    tags=["analytics"],
)
async def get_hall_analytics(
    hall_id: Annotated[str, Path(description="UUID of the hall.")],
    session: DBSession,
    current_user: AdminUser,
    months: Annotated[
        int,
        Query(
            ge=1,
            le=24,
            description="Number of calendar months to include in the trend (default 12).",
        ),
    ] = 12,
) -> HallAnalyticsRead:
    """Return aggregated analytics for the authenticated admin's hall."""
    return await AnalyticsService.get_hall_analytics(
        session,
        hall_id,
        current_user,
        months=months,
    )
