"""
IntelliHall — Workers API Endpoints

Provides CRUD operations for Hall maintenance staff.
Scoped and isolated to the logged-in Hall Admin's hall.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.enums import UserRole, ComplaintStatus
from app.models.user import User
from app.models.complaint import Complaint
from app.repositories.worker_repository import WorkerRepository
from app.schemas.worker import (
    WorkerCreate,
    WorkerRead,
    WorkerUpdate,
    PaginatedWorkerResponse,
)

router = APIRouter()

DBSession = Annotated[AsyncSession, Depends(get_db)]
AuthUser = Annotated[User, Depends(get_current_user)]


def _check_admin(current_user: User) -> None:
    """Enforce that the calling user is a hall administrator with a bound hall."""
    if current_user.role != UserRole.HALL_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hall administrators can manage staff.",
        )
    if not current_user.hall_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must be assigned to a hall to manage staff.",
        )


@router.post(
    "/",
    response_model=WorkerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new maintenance worker to the hall",
)
async def create_worker(
    session: DBSession,
    current_user: AuthUser,
    data: WorkerCreate,
) -> WorkerRead:
    """
    Create a new worker.
    Automatically bound to the hall of the authenticated Hall Admin.
    """
    _check_admin(current_user)
    worker = await WorkerRepository.create(session, data, hall_id=current_user.hall_id)
    return WorkerRead.model_validate(worker)


@router.get(
    "/",
    response_model=PaginatedWorkerResponse,
    summary="List workers in the administrator's hall",
)
async def list_workers(
    session: DBSession,
    current_user: AuthUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> PaginatedWorkerResponse:
    """
    List workers belonging to the administrator's hall.
    Includes dynamic workload/active jobs count.
    """
    _check_admin(current_user)
    items, total = await WorkerRepository.list_by_hall(
        session, hall_id=current_user.hall_id, page=page, page_size=page_size
    )

    pages = int((total + page_size - 1) / page_size) if total > 0 else 0

    return PaginatedWorkerResponse(
        items=[WorkerRead.model_validate(w) for w in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.put(
    "/{id}",
    response_model=WorkerRead,
    summary="Update details of a worker",
)
async def update_worker(
    session: DBSession,
    current_user: AuthUser,
    id: str,
    data: WorkerUpdate,
) -> WorkerRead:
    """
    Update worker attributes.
    Enforces hall isolation.
    """
    _check_admin(current_user)
    worker = await WorkerRepository.get_by_id(session, id)
    if not worker or worker.hall_id != current_user.hall_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found in your hall.",
        )

    updated_worker = await WorkerRepository.update(session, worker, data)
    return WorkerRead.model_validate(updated_worker)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
    summary="Delete a worker",
)


async def delete_worker(
    session: DBSession,
    current_user: AuthUser,
    id: str,
) -> None:
    """
    Delete a worker.
    Fails with 409 Conflict if they have unresolved active complaints.
    """
    _check_admin(current_user)
    worker = await WorkerRepository.get_by_id(session, id)
    if not worker or worker.hall_id != current_user.hall_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found in your hall.",
        )

    # Prevent deletion if the worker has unresolved assignments
    # We query dynamically to count complaints assigned to worker that are not completed/closed
    active_jobs_stmt = select(func.count(Complaint.id)).where(
        Complaint.assigned_worker_id == worker.id,
        Complaint.status.not_in([ComplaintStatus.COMPLETED, ComplaintStatus.CLOSED]),
    )
    active_count_res = await session.execute(active_jobs_stmt)
    active_jobs_count = active_count_res.scalar_one()

    if active_jobs_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Worker has active assignments. Please reassign complaints before deleting.",
        )

    # Reassign completed or closed complaints to NULL so they don't break foreign key constraints
    # (Although sqlalchemy SET NULL on delete handles this, we explicitly flush it)
    await WorkerRepository.delete(session, worker)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

