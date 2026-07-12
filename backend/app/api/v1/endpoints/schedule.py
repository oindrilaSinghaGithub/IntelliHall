"""
IntelliHall — Schedule Endpoints

Endpoints for viewing the upcoming maintenance work schedule and exporting as PDF.

GET  /api/v1/halls/{hall_id}/schedule         — list scheduled work
GET  /api/v1/halls/{hall_id}/schedule/export  — download PDF
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import StreamingResponse
import io

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.halls import require_hall_admin
from app.db.session import get_db
from app.models.enums import ComplaintCategory, MaintenanceType
from app.models.user import User
from app.repositories.hall_repository import HallRepository
from app.schemas.schedule import ScheduleFilters, ScheduleItemRead
from app.services.schedule_service import ScheduleService

router = APIRouter()

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

DBSession  = Annotated[AsyncSession, Depends(get_db)]
AdminUser  = Annotated[User, Depends(require_hall_admin)]


# ---------------------------------------------------------------------------
# GET /halls/{hall_id}/schedule
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=list[ScheduleItemRead],
    summary="List upcoming maintenance schedule",
    description=(
        "Return all scheduled and in-progress complaints for a hall.\n\n"
        "**Requires:** HALL_ADMIN role for the specified hall.\n\n"
        "Supports filters: `scheduled_date`, `worker_name`, `worker_type`, `category`."
    ),
    tags=["schedule"],
)
async def list_schedule(
    hall_id: Annotated[str, Path(description="UUID of the hall.")],
    session: DBSession,
    current_user: AdminUser,
    scheduled_date: Annotated[date | None, Query(description="Filter by exact visit date.")] = None,
    worker_name: Annotated[str | None, Query(description="Filter by worker name (partial match).")] = None,
    worker_type: Annotated[MaintenanceType | None, Query(description="Filter by worker type.")] = None,
    category: Annotated[ComplaintCategory | None, Query(description="Filter by category.")] = None,
) -> list[ScheduleItemRead]:
    """List upcoming maintenance schedule for a hall."""
    filters = ScheduleFilters(
        scheduled_date=scheduled_date,
        worker_name=worker_name,
        worker_type=worker_type,
        category=category,
    )
    return await ScheduleService.list_schedule(session, hall_id, filters, current_user)


# ---------------------------------------------------------------------------
# GET /halls/{hall_id}/schedule/export
# ---------------------------------------------------------------------------

@router.get(
    "/export",
    summary="Export maintenance schedule as PDF",
    description=(
        "Generate a printable PDF of the upcoming maintenance schedule.\n\n"
        "**Requires:** HALL_ADMIN role for the specified hall.\n\n"
        "Accepts the same filters as the schedule list endpoint."
    ),
    tags=["schedule"],
    response_class=StreamingResponse,
)
async def export_schedule_pdf(
    hall_id: Annotated[str, Path(description="UUID of the hall.")],
    session: DBSession,
    current_user: AdminUser,
    scheduled_date: Annotated[date | None, Query(description="Filter by exact visit date.")] = None,
    worker_name: Annotated[str | None, Query(description="Filter by worker name (partial match).")] = None,
    worker_type: Annotated[MaintenanceType | None, Query(description="Filter by worker type.")] = None,
    category: Annotated[ComplaintCategory | None, Query(description="Filter by category.")] = None,
) -> StreamingResponse:
    """Download maintenance schedule as a PDF."""
    filters = ScheduleFilters(
        scheduled_date=scheduled_date,
        worker_name=worker_name,
        worker_type=worker_type,
        category=category,
    )

    # Get schedule items
    items = await ScheduleService.list_schedule(session, hall_id, filters, current_user)

    # Fetch hall name
    hall = await HallRepository.get_by_id(session, hall_id)
    hall_name = hall.name if hall else hall_id

    # Generate PDF
    today = date.today()
    pdf_bytes = ScheduleService.export_pdf(items, hall_name, today)

    filename = f"maintenance_schedule_{today.isoformat()}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
