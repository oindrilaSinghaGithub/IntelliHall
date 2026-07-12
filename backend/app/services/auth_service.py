"""
IntelliHall — Auth Service

Business logic for user registration and login.
Raises HTTP-level exceptions so route handlers stay thin.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    """Encapsulates authentication business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepository(session)

    # ------------------------------------------------------------------
    # Register
    # ------------------------------------------------------------------

    async def register(self, payload: RegisterRequest) -> tuple[User, str]:
        """
        Create a new user account.

        Rules:
          - Email must not already exist.
          - Password is hashed before storage.
          - Role defaults to STUDENT if not provided.

        Returns:
            (User ORM instance, JWT access token)

        Raises:
            HTTPException 409 if the email is already registered.
        """
        existing = await self._repo.get_by_email(payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this e-mail address already exists.",
            )

        from app.repositories.hall_repository import HallRepository
        hall = await HallRepository.get_by_id(self._repo._session, payload.hall_id)
        if hall is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hall with ID '{payload.hall_id}' does not exist.",
            )

        from datetime import datetime, timezone
        from app.models.enums import HallVerificationStatus

        resolved_role = payload.role if payload.role is not None else UserRole.STUDENT

        # Hall Admins are trusted accounts — bypass verification entirely.
        # Students start as PENDING and must be approved by their Hall Admin.
        is_admin = resolved_role == UserRole.HALL_ADMIN
        verification_status = (
            HallVerificationStatus.APPROVED if is_admin else HallVerificationStatus.PENDING
        )
        verified_at = datetime.now(timezone.utc) if is_admin else None

        user = User(
            name=payload.name,
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=resolved_role,
            hall_id=payload.hall_id,
            roll_number=payload.roll_number,
            room_number=payload.room_number,
            hall_verification_status=verification_status,
            hall_verified_at=verified_at,
        )
        user = await self._repo.create(user)

        token = create_access_token({"sub": user.id, "role": user.role.value})
        return user, token

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    async def login(self, payload: LoginRequest) -> str:
        """
        Authenticate an existing user.

        Returns:
            Signed JWT access token string.

        Raises:
            HTTPException 401 if credentials are invalid.
        """
        _INVALID = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect e-mail or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

        user = await self._repo.get_by_email(payload.email)
        if user is None:
            raise _INVALID

        if not verify_password(payload.password, user.password_hash):
            raise _INVALID

        return create_access_token({"sub": user.id, "role": user.role.value})
