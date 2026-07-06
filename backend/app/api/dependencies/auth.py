"""
IntelliHall — API Dependencies: Authentication

Provides the ``get_current_user`` FastAPI dependency.

Usage in route handlers::

    from typing import Annotated
    from fastapi import Depends
    from app.api.dependencies.auth import get_current_user
    from app.models.user import User

    @router.get("/me")
    async def me(current_user: Annotated[User, Depends(get_current_user)]):
        ...
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

# ---------------------------------------------------------------------------
# OAuth2 scheme — tells FastAPI/Swagger where to find the Bearer token
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    FastAPI dependency that authenticates the request.

    1. Extracts the Bearer token from the ``Authorization`` header.
    2. Decodes and validates the JWT signature and expiry.
    3. Reads ``sub`` (user_id) from the payload.
    4. Fetches the User from the database.
    5. Returns the authenticated User, or raises HTTP 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise credentials_exception

    return user
