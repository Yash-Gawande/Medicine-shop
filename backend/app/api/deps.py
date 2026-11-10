"""Shared FastAPI dependencies: current user and permission checks."""

from __future__ import annotations

import uuid
from collections.abc import Callable

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_access_token
from app.models.auth import User
from app.models.enums import UserStatus
from app.services.auth import user_permissions

_bearer = HTTPBearer(auto_error=False)


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not creds:
        raise AuthenticationError("Authentication required")
    try:
        claims = decode_access_token(creds.credentials)
        user_id = uuid.UUID(claims["sub"])
    except (jwt.PyJWTError, ValueError, KeyError) as exc:
        raise AuthenticationError("Invalid or expired token", code="invalid_token") from exc
    user = await db.get(User, user_id)
    if not user or user.deleted_at or user.status == UserStatus.INACTIVE:
        raise AuthenticationError("Account unavailable", code="invalid_token")
    return user


def require_permission(*codes: str) -> Callable[..., User]:
    """Route dependency: user must hold ALL listed permission codes."""

    async def _check(user: User = Depends(get_current_user)) -> User:
        missing = set(codes) - user_permissions(user)
        if missing:
            raise PermissionDeniedError("You do not have permission to perform this action", details=sorted(missing))
        return user

    return _check
