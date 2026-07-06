"""
IntelliHall — Security Utilities

Provides:
  - Password hashing and verification (bcrypt, called directly)
  - JWT access-token creation and decoding (HS256 via python-jose)

All helpers are pure functions with no I/O or HTTP concerns.

Note on passlib: passlib 1.7.4 is incompatible with bcrypt ≥ 4.0 because
its internal bug-detection probe sends an 80-byte test password that bcrypt
4+ rejects with ValueError.  We therefore call the ``bcrypt`` package
directly, which gives identical security with no compatibility shims needed.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Return the bcrypt hash of *password* (UTF-8 encoded, cost=12)."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed_password: str) -> bool:
    """Return True if *password* matches *hashed_password*."""
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict) -> str:
    """
    Create a signed JWT access token.

    The *data* dict is copied and augmented with an ``exp`` claim set to
    30 minutes from now (UTC).  The token is signed with the application's
    SECRET_KEY using HS256.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["exp"] = expire
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT access token.

    Returns the decoded payload dict on success.
    Raises ``jose.JWTError`` on any validation failure (expired, bad
    signature, malformed, etc.) — callers must catch this and raise an
    appropriate HTTP 401.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALGORITHM])
