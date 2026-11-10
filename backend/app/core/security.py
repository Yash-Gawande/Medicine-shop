"""Password hashing, access-token JWTs and opaque refresh tokens."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings

_hasher = PasswordHasher()
# Verified against when the account doesn't exist, so response time doesn't reveal it.
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def create_access_token(user_id: uuid.UUID, user_type: str) -> tuple[str, int]:
    """Returns (token, expires_in_seconds)."""
    s = get_settings()
    now = datetime.now(UTC)
    ttl = timedelta(minutes=s.access_token_expire_minutes)
    payload = {"sub": str(user_id), "typ": user_type, "jti": uuid.uuid4().hex, "iat": now, "exp": now + ttl}
    token = jwt.encode(payload, s.jwt_secret_key.get_secret_value(), algorithm=s.jwt_algorithm)
    return token, int(ttl.total_seconds())


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError on any invalid/expired token."""
    s = get_settings()
    return jwt.decode(
        token,
        s.jwt_secret_key.get_secret_value(),
        algorithms=[s.jwt_algorithm],
        options={"require": ["sub", "exp", "iat"]},
    )


def new_refresh_token() -> tuple[str, str]:
    """Returns (raw_token, sha256_hash). Only the hash is persisted."""
    raw = secrets.token_urlsafe(48)
    return raw, hash_token(raw)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
