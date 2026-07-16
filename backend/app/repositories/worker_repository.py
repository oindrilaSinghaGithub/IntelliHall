"""
IntelliHall — Worker Repository

Handles database operations for the Worker model.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.worker import Worker
from app.schemas.worker import WorkerCreate, WorkerUpdate


class WorkerRepository:
    """Data-access object for the ``workers`` table."""

    @staticmethod
    async def get_by_id(session: AsyncSession, worker_id: str) -> Worker | None:
        """Return the Worker with the given *worker_id*, or None."""
        result = await session.execute(select(Worker).where(Worker.id == worker_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_hall(
        session: AsyncSession,
        hall_id: str,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Worker], int]:
        """
        Return a paginated list of workers for the given *hall_id*,
        along with the total count.
        """
        # Base query
        stmt = select(Worker).where(Worker.hall_id == hall_id)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await session.execute(count_stmt)
        total = total_result.scalar_one()

        # Paginated fetch, ordered by name
        stmt = stmt.order_by(Worker.name).offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    @staticmethod
    async def list_all_in_hall(session: AsyncSession, hall_id: str) -> list[Worker]:
        """Return every Worker in the given *hall_id* (unpaginated)."""
        result = await session.execute(
            select(Worker).where(Worker.hall_id == hall_id).order_by(Worker.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(session: AsyncSession, data: WorkerCreate, hall_id: str) -> Worker:
        """Persist a new Worker in the given *hall_id* and return the refreshed instance."""
        worker = Worker(
            name=data.name,
            phone=data.phone,
            specialization=data.specialization,
            availability_status=data.availability_status,
            skill_rating=data.skill_rating,
            experience_years=data.experience_years,
            experience_level=data.experience_level,
            hall_id=hall_id,
        )
        session.add(worker)
        await session.commit()
        await session.refresh(worker)
        return worker

    @staticmethod
    async def update(session: AsyncSession, worker: Worker, data: WorkerUpdate) -> Worker:
        """Apply non-None fields from *data* onto *worker*."""
        if data.name is not None:
            worker.name = data.name
        if data.phone is not None:
            worker.phone = data.phone
        if data.specialization is not None:
            worker.specialization = data.specialization
        if data.availability_status is not None:
            worker.availability_status = data.availability_status
        if data.skill_rating is not None:
            worker.skill_rating = data.skill_rating
        if data.experience_years is not None:
            worker.experience_years = data.experience_years
        if data.experience_level is not None:
            worker.experience_level = data.experience_level

        worker.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(worker)
        return worker

    @staticmethod
    async def delete(session: AsyncSession, worker: Worker) -> None:
        """Delete the worker from the database."""
        await session.delete(worker)
        await session.commit()
