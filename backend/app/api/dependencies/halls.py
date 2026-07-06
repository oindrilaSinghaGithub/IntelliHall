"""
IntelliHall — API Dependencies: Hall Authorization

Provides role-based guards for the Hall endpoints.

Usage::

    from app.api.dependencies.halls import require_hall_admin
    from typing import Annotated
    from fastapi import Depends
    from app.models.user import User

    @router.post("/")
    async def create_hall(
        current_user: Annotated[User, Depends(require_hall_admin)],
        ...
    ):
        ...
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.api.dependencies.auth import get_current_user
from app.models.enums import UserRole
from app.models.user import User


async def require_hall_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    FastAPI dependency that enforces the ``HALL_ADMIN`` role.

    Passes through the authenticated user unchanged if they are a
    ``HALL_ADMIN``; otherwise raises HTTP 403 Forbidden.

    This is composed on top of ``get_current_user``, so a missing or
    invalid Bearer token will still yield HTTP 401 from the inner dependency.
    """
    if current_user.role != UserRole.HALL_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hall administrators can perform this action.",
        )
    return current_user
