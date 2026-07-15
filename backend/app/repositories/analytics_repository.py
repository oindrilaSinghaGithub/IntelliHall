"""
IntelliHall — Analytics Repository

SQL aggregation queries for hall-scoped complaint analytics.
Contains no business logic or HTTP concerns.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.complaint import Complaint, ComplaintStatusHistory
from app.models.enums import ComplaintCategory, ComplaintPriority, ComplaintStatus


def _utc_midnight_today() -> datetime:
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _utc_week_start() -> datetime:
    """Monday 00:00 UTC of the current week."""
    today = _utc_midnight_today()
    return today - timedelta(days=today.weekday())


class AnalyticsRepository:
    """Database aggregation layer for hall analytics."""

    # ------------------------------------------------------------------
    # Summary KPIs — single query with FILTER aggregates
    # ------------------------------------------------------------------

    @staticmethod
    async def get_summary_counts(
        session: AsyncSession,
        hall_id: str,
    ) -> dict[str, int]:
        """Return all scalar KPI counts for a hall in one round-trip."""
        today_start = _utc_midnight_today()
        week_start = _utc_week_start()

        stmt = select(
            func.count().label("total"),
            func.count()
            .filter(Complaint.status != ComplaintStatus.CLOSED)
            .label("open"),
            func.count()
            .filter(Complaint.status == ComplaintStatus.IN_PROGRESS)
            .label("in_progress"),
            func.count()
            .filter(Complaint.status == ComplaintStatus.CLOSED)
            .label("completed"),
            func.count()
            .filter(
                and_(
                    Complaint.priority == ComplaintPriority.CRITICAL,
                    Complaint.status != ComplaintStatus.CLOSED,
                )
            )
            .label("critical"),
            func.count()
            .filter(Complaint.created_at >= today_start)
            .label("today"),
            func.count()
            .filter(Complaint.created_at >= week_start)
            .label("this_week"),
        ).where(Complaint.hall_id == hall_id)

        row = (await session.execute(stmt)).one()
        return {
            "total": row.total,
            "open": row.open,
            "in_progress": row.in_progress,
            "completed": row.completed,
            "critical": row.critical,
            "today": row.today,
            "this_week": row.this_week,
        }

    # ------------------------------------------------------------------
    # Average resolution time (hours)
    # ------------------------------------------------------------------

    @staticmethod
    async def get_avg_resolution_hours(
        session: AsyncSession,
        hall_id: str,
    ) -> float | None:
        """
        Average hours from complaint creation to the first ``closed`` history entry.

        Returns None when no closed complaints exist for the hall.
        """
        closed_at_subq = (
            select(
                ComplaintStatusHistory.complaint_id.label("complaint_id"),
                func.min(ComplaintStatusHistory.timestamp).label("closed_at"),
            )
            .where(ComplaintStatusHistory.new_status == ComplaintStatus.CLOSED)
            .group_by(ComplaintStatusHistory.complaint_id)
            .subquery()
        )

        stmt = (
            select(
                func.avg(
                    extract(
                        "epoch",
                        closed_at_subq.c.closed_at - Complaint.created_at,
                    )
                    / 3600.0
                )
            )
            .select_from(Complaint)
            .join(
                closed_at_subq,
                closed_at_subq.c.complaint_id == Complaint.id,
            )
            .where(Complaint.hall_id == hall_id)
        )

        result = await session.execute(stmt)
        avg_hours = result.scalar_one_or_none()
        if avg_hours is None:
            return None
        return round(float(avg_hours), 2)

    # ------------------------------------------------------------------
    # GROUP BY — category and status
    # ------------------------------------------------------------------

    @staticmethod
    async def count_by_category(
        session: AsyncSession,
        hall_id: str,
    ) -> list[tuple[ComplaintCategory, int]]:
        """Return (category, count) pairs ordered by count descending."""
        stmt = (
            select(Complaint.category, func.count())
            .where(Complaint.hall_id == hall_id)
            .group_by(Complaint.category)
            .order_by(func.count().desc())
        )
        rows = await session.execute(stmt)
        return list(rows.all())

    @staticmethod
    async def count_by_status(
        session: AsyncSession,
        hall_id: str,
    ) -> list[tuple[ComplaintStatus, int]]:
        """Return (status, count) pairs ordered by count descending."""
        stmt = (
            select(Complaint.status, func.count())
            .where(Complaint.hall_id == hall_id)
            .group_by(Complaint.status)
            .order_by(func.count().desc())
        )
        rows = await session.execute(stmt)
        return list(rows.all())

    # ------------------------------------------------------------------
    # Monthly trend
    # ------------------------------------------------------------------

    @staticmethod
    async def count_by_month(
        session: AsyncSession,
        hall_id: str,
        *,
        months: int = 12,
    ) -> list[tuple[datetime, int]]:
        """
        Return (month_start, count) for each month that has complaints.

        Limited to complaints created within the last *months* calendar months.
        """
        cutoff = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        # Walk back (months - 1) additional months from the first of this month
        month_index = cutoff.month - (months - 1)
        year = cutoff.year
        while month_index <= 0:
            month_index += 12
            year -= 1
        cutoff = cutoff.replace(year=year, month=month_index)

        month_bucket = func.date_trunc("month", Complaint.created_at)
        stmt = (
            select(month_bucket.label("month"), func.count())
            .where(
                Complaint.hall_id == hall_id,
                Complaint.created_at >= cutoff,
            )
            .group_by(month_bucket)
            .order_by(month_bucket)
        )
        rows = await session.execute(stmt)
        return [(row.month, row[1]) for row in rows.all()]

    # ------------------------------------------------------------------
    # Recent complaints
    # ------------------------------------------------------------------

    @staticmethod
    async def get_recent_complaints(
        session: AsyncSession,
        hall_id: str,
        *,
        limit: int = 5,
    ) -> list[Complaint]:
        """Return the most recently created complaints for a hall."""
        stmt = (
            select(Complaint)
            .where(Complaint.hall_id == hall_id)
            .options(
                selectinload(Complaint.creator),
                selectinload(Complaint.affected_entries),
            )
            .order_by(Complaint.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
