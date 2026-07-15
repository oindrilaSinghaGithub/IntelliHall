"""
IntelliHall — Complaint Repository

Responsible exclusively for database access.  Contains no business logic,
HTTP concerns, or exception handling beyond letting SQLAlchemy exceptions
propagate naturally to the service layer.

Public API
----------
ComplaintRepository.create(session, data)              -> Complaint
ComplaintRepository.get_by_id(session, id)             -> Complaint | None
ComplaintRepository.list(session, ...)                 -> tuple[list[Complaint], int]
ComplaintRepository.update(session, complaint, data)   -> Complaint
ComplaintRepository.delete(session, complaint)         -> None
ComplaintRepository.add_status_history(session, ...)   -> ComplaintStatusHistory
ComplaintRepository.count_images(session, complaint_id) -> int
ComplaintRepository.add_images(session, complaint_id, image_urls) -> list[ComplaintImage]
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint, ComplaintImage, ComplaintStatusHistory
from app.models.enums import (
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
    ComplaintType,
)
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate


# ---------------------------------------------------------------------------
# Sortable columns — map string key → ORM attribute for safe dynamic ordering
# ---------------------------------------------------------------------------

_SORTABLE: dict[str, object] = {
    "created_at": Complaint.created_at,
    "updated_at": Complaint.updated_at,
    "priority": Complaint.priority,
    "status": Complaint.status,
    "category": Complaint.category,
    "title": Complaint.title,
}

_DEFAULT_SORT = "created_at"


class ComplaintRepository:
    """Pure database-access layer for the Complaint domain."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    async def create(
        session: AsyncSession,
        data: ComplaintCreate,
        *,
        user_id: str,
        hall_id: str,
        predicted_priority: ComplaintPriority | None = None,
        ai_confidence: float | None = None,
    ) -> Complaint:
        """
        Persist a new Complaint row.

        ``user_id`` and ``hall_id`` are passed explicitly (resolved from the
        authenticated user by the service layer) rather than taken from the
        request schema, so that clients can never spoof either field.

        ``predicted_priority`` and ``ai_confidence`` are optional AI-generated
        values injected by the service layer after calling PriorityPredictor.
        They are stored alongside the student's own ``priority`` selection and
        never overwrite it.

        Sets ``status`` to SUBMITTED and leaves all admin-only fields
        (maintenance_type, current_assignee) as NULL.
        """
        complaint = Complaint(
            title=data.title,
            description=data.description,
            complaint_type=data.complaint_type,
            category=data.category,
            priority=data.priority,
            status=ComplaintStatus.SUBMITTED,
            room_number=data.room_number,
            block=data.block,
            floor=data.floor,
            common_area=data.common_area,
            qr_location_id=data.qr_location_id,
            preferred_visit_time=data.preferred_visit_time,
            hall_id=hall_id,
            created_by=user_id,
            predicted_priority=predicted_priority,
            ai_confidence=ai_confidence,
        )
        session.add(complaint)
        await session.flush()          # obtain id without committing
        await session.refresh(complaint)
        return complaint


    # ------------------------------------------------------------------
    # Read — single
    # ------------------------------------------------------------------

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        complaint_id: str,
    ) -> Complaint | None:
        """Return a Complaint by its UUID, or None if not found."""
        result = await session.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Read — list with filters + pagination
    # ------------------------------------------------------------------

    @staticmethod
    async def list(
        session: AsyncSession,
        *,
        hall_id: str | None = None,
        status: ComplaintStatus | None = None,
        priority: ComplaintPriority | None = None,
        category: ComplaintCategory | None = None,
        complaint_type: ComplaintType | None = None,
        created_by: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = _DEFAULT_SORT,
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> tuple[list[Complaint], int]:
        """
        Return a page of Complaints matching the given filters.

        Returns a (items, total_count) tuple so callers can build a
        paginated envelope without a second round-trip.
        """
        base_where = []
        if hall_id is not None:
            base_where.append(Complaint.hall_id == hall_id)
        if status is not None:
            base_where.append(Complaint.status == status)
        if priority is not None:
            base_where.append(Complaint.priority == priority)
        if category is not None:
            base_where.append(Complaint.category == category)
        if complaint_type is not None:
            base_where.append(Complaint.complaint_type == complaint_type)
        if created_by is not None:
            base_where.append(Complaint.created_by == created_by)

        # -- Total count (without pagination) --------------------------------
        count_stmt = select(func.count()).select_from(Complaint)
        if base_where:
            count_stmt = count_stmt.where(*base_where)
        total: int = (await session.execute(count_stmt)).scalar_one()

        # -- Data query -------------------------------------------------------
        sort_col = _SORTABLE.get(sort_by, Complaint.created_at)
        order_fn = desc if sort_order == "desc" else asc

        data_stmt = select(Complaint)
        if base_where:
            data_stmt = data_stmt.where(*base_where)
        data_stmt = (
            data_stmt
            .order_by(order_fn(sort_col))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list((await session.execute(data_stmt)).scalars().all())
        return items, total

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    @staticmethod
    async def update(
        session: AsyncSession,
        complaint: Complaint,
        data: ComplaintUpdate,
    ) -> Complaint:
        """
        Apply the non-None fields from `data` onto the given complaint.

        Only fields explicitly set by the caller are modified; omitted
        fields (None) leave the existing value unchanged.
        """
        update_map = data.model_dump(exclude_none=True)
        for field, value in update_map.items():
            setattr(complaint, field, value)
        complaint.updated_at = datetime.now(timezone.utc)
        await session.flush()
        await session.refresh(complaint)
        return complaint

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @staticmethod
    async def delete(
        session: AsyncSession,
        complaint: Complaint,
    ) -> None:
        """Hard-delete the complaint and all its cascaded children."""
        await session.delete(complaint)
        await session.flush()

    # ------------------------------------------------------------------
    # Images
    # ------------------------------------------------------------------

    @staticmethod
    async def count_images(
        session: AsyncSession,
        complaint_id: str,
    ) -> int:
        """Return the number of images attached to a complaint."""
        result = await session.execute(
            select(func.count())
            .select_from(ComplaintImage)
            .where(ComplaintImage.complaint_id == complaint_id)
        )
        return result.scalar_one()

    @staticmethod
    async def add_images(
        session: AsyncSession,
        complaint_id: str,
        image_urls: list[str],
    ) -> list[ComplaintImage]:
        """Persist one ComplaintImage row per URL and return the new records."""
        now = datetime.now(timezone.utc)
        images: list[ComplaintImage] = []
        for url in image_urls:
            image = ComplaintImage(
                complaint_id=complaint_id,
                image_url=url,
                uploaded_at=now,
            )
            session.add(image)
            images.append(image)
        await session.flush()
        for image in images:
            await session.refresh(image)
        return images

    # ------------------------------------------------------------------
    # Status History
    # ------------------------------------------------------------------

    @staticmethod
    async def add_status_history(
        session: AsyncSession,
        *,
        complaint_id: str,
        previous_status: "ComplaintStatus | None",
        new_status: "ComplaintStatus",
        updated_by: str,
        remarks: str | None,
    ) -> ComplaintStatusHistory:
        """
        Insert a new ComplaintStatusHistory row.

        Called by the service layer every time a complaint status changes.
        The repository makes no decision about *when* to call this — it only
        writes the row and returns the refreshed instance.
        """
        entry = ComplaintStatusHistory(
            complaint_id=complaint_id,
            previous_status=previous_status,
            new_status=new_status,
            updated_by=updated_by,
            remarks=remarks,
            timestamp=datetime.now(timezone.utc),
        )
        session.add(entry)
        await session.flush()
        await session.refresh(entry)
        return entry
