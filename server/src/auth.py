"""JWT access-token creation and verification for student authentication."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import config  # noqa: F401  # ensures server/.env is loaded before reading os.getenv
from jose import JWTError, jwt

_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-insecure-secret-change-me")
_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
# Default token lifetime: 7 days.
_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", str(60 * 24 * 7)))


def create_access_token(student_id: int) -> str:
    """Sign a JWT whose subject is the student id."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=_EXPIRE_MINUTES)
    payload = {"sub": str(student_id), "exp": expire}
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> int:
    """Return the student id from a valid token; raise JWTError otherwise."""
    payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
    sub = payload.get("sub")
    if sub is None:
        raise JWTError("Token missing subject")
    return int(sub)
