"""
IntelliHall — Assignment Repository

Pure database access for ComplaintAssignment records.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import ComplaintAssignment
from app.models.enums import MaintenanceType


class AssignmentRepository:
    """Database access layer for ComplaintAssignment."""

    @staticmethod
    async def upsert(
        session: AsyncSession,
        complaint_id: str,
        *,
        worker_name: str,
        worker_type: MaintenanceType,
        scheduled_date: date,
        scheduled_time: str | None = None,
        admin_remarks: str | None = None,
    ) -> ComplaintAssignment:
        """
        Upsert an assignment for a complaint.
        
        If an assignment already exists for this complaint_id, delete it first
        then insert the new one (simulating an upsert via UNIQUE constraint).
        """
        # Delete existing assignment if any
        existing = await AssignmentRepository.get_by_complaint_id(session, complaint_id)
        if existing:
            await session.delete(existing)
            await session.flush()

        # Create new assignment
        assignment = ComplaintAssignment(
            complaint_id=complaint_id,
            worker_name=worker_name,
            worker_type=worker_type,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            admin_remarks=admin_remarks,
        )
        session.add(assignment)
        await session.flush()
        await session.refresh(assignment)
        return assignment

    @staticmethod
    async def get_by_complaint_id(
        session: AsyncSession,
        complaint_id: str,
    ) -> ComplaintAssignment | None:
        """Fetch an assignment by complaint ID."""
        result = await session.execute(
            select(ComplaintAssignment).where(
                ComplaintAssignment.complaint_id == complaint_id
            )
        )
        return result.scalar_one_or_none()
