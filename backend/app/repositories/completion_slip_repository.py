"""
IntelliHall — Completion Slip Repository

Pure database access for CompletionSlip records.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.completion_slip import CompletionSlip
from app.models.enums import MaintenanceType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CompletionSlipRepository:
    """Database access layer for CompletionSlip."""

    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        complaint_id: str,
        hall_id: str,
        room_number: str | None,
        worker_name: str,
        worker_type: MaintenanceType,
        work_done: str,
        admin_remarks: str | None = None,
    ) -> CompletionSlip:
        """Create a new completion slip record."""
        slip = CompletionSlip(
            complaint_id=complaint_id,
            hall_id=hall_id,
            room_number=room_number,
            worker_name=worker_name,
            worker_type=worker_type,
            completion_date=_utcnow(),
            work_done=work_done,
            admin_remarks=admin_remarks,
        )
        session.add(slip)
        await session.flush()
        await session.refresh(slip)
        return slip

    @staticmethod
    async def get_by_complaint_id(
        session: AsyncSession,
        complaint_id: str,
    ) -> CompletionSlip | None:
        """Fetch a completion slip by complaint ID."""
        result = await session.execute(
            select(CompletionSlip).where(
                CompletionSlip.complaint_id == complaint_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        session: AsyncSession,
        slip: CompletionSlip,
        **fields: object,
    ) -> CompletionSlip:
        """Apply given field updates to a completion slip."""
        for field, value in fields.items():
            setattr(slip, field, value)
        slip.updated_at = _utcnow()  # type: ignore[attr-defined]
        await session.flush()
        await session.refresh(slip)
        return slip
