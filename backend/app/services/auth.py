"""Authentication use-cases. Services commit their own transactions."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    hash_password,
    hash_token,
    new_refresh_token,
    password_needs_rehash,
    verify_password,
)
from app.models.auth import RefreshToken, Role, User
from app.models.customer import Customer
from app.models.enums import UserStatus, UserType
from app.schemas.auth import RegisterRequest, normalize_mobile

INVALID_CREDENTIALS = "Invalid email/mobile or password"
_LOGIN_BLOCKED = (UserStatus.INACTIVE,)


@dataclass
class Session:
    user: User
    access_token: str
    expires_in: int
    refresh_token: str
    remember: bool = True  # False -> browser-session cookie and a 1-day server-side lifetime


def user_permissions(user: User) -> set[str]:
    return {p.code for r in user.roles for p in r.permissions}


def _now() -> datetime:
    return datetime.now(UTC)


SESSION_TOKEN_TTL = timedelta(days=1)


async def _issue(
    db: AsyncSession,
    user: User,
    *,
    family_id: uuid.UUID | None,
    ip: str | None,
    ua: str | None,
    remember: bool = True,
):
    s = get_settings()
    raw, digest = new_refresh_token()
    row = RefreshToken(
        user_id=user.id,
        token_hash=digest,
        family_id=family_id or uuid.uuid4(),
        expires_at=_now() + (timedelta(days=s.refresh_token_expire_days) if remember else SESSION_TOKEN_TTL),
        user_agent=(ua or "")[:255] or None,
        ip_address=ip,
    )
    db.add(row)
    await db.flush()
    access, ttl = create_access_token(user.id, user.user_type.value)
    return row, Session(user=user, access_token=access, expires_in=ttl, refresh_token=raw, remember=remember)


async def register_customer(db: AsyncSession, data: RegisterRequest, *, ip: str | None, ua: str | None) -> Session:
    email = data.email.lower()
    clash = await db.scalar(
        select(User.id).where(
            User.deleted_at.is_(None),
            or_(func.lower(User.email) == email, User.mobile == data.mobile if data.mobile else False),
        )
    )
    if clash:
        raise ConflictError("An account with this email or mobile already exists", code="account_exists")
    user = User(
        email=email,
        mobile=data.mobile,
        password_hash=hash_password(data.password),
        user_type=UserType.CUSTOMER,
        status=UserStatus.PENDING_VERIFICATION,
        password_changed_at=_now(),
    )
    customer_role = await db.scalar(select(Role).where(Role.slug == "customer"))
    if customer_role:
        user.roles.append(customer_role)
    db.add(user)
    try:
        await db.flush()
    except IntegrityError as exc:  # race against the partial unique indexes
        await db.rollback()
        raise ConflictError("An account with this email or mobile already exists", code="account_exists") from exc
    db.add(Customer(user_id=user.id, full_name=data.full_name.strip()))
    _, session = await _issue(db, user, family_id=None, ip=ip, ua=ua)
    await db.commit()
    return session


async def login(
    db: AsyncSession, identifier: str, password: str, *, ip: str | None, ua: str | None, remember: bool = True
) -> Session:
    s = get_settings()
    ident = identifier.strip()
    if "@" in ident:
        cond = func.lower(User.email) == ident.lower()
    else:
        try:
            cond = User.mobile == normalize_mobile(ident)
        except ValueError:
            cond = User.id.is_(None)  # matches nothing; still burns a password verify
    user = await db.scalar(select(User).where(User.deleted_at.is_(None), cond).with_for_update())

    now = _now()
    if user and user.locked_until and user.locked_until > now:
        raise AuthenticationError("Account temporarily locked. Try again later.", code="account_locked")

    ok = verify_password(password, user.password_hash if user else None)
    if not user or not ok:
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= s.login_max_failed_attempts:
                user.locked_until = now + timedelta(minutes=s.login_lockout_minutes)
                user.failed_login_attempts = 0
            await db.commit()
        raise AuthenticationError(INVALID_CREDENTIALS, code="invalid_credentials")
    if user.status in _LOGIN_BLOCKED:
        raise AuthenticationError("This account is disabled", code="account_disabled")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    _, session = await _issue(db, user, family_id=None, ip=ip, ua=ua, remember=remember)
    await db.commit()
    return session


async def refresh(db: AsyncSession, raw_token: str | None, *, ip: str | None, ua: str | None) -> Session:
    if not raw_token:
        raise AuthenticationError("Missing refresh token", code="invalid_refresh_token")
    row = await db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token)).with_for_update()
    )
    if not row:
        raise AuthenticationError("Invalid refresh token", code="invalid_refresh_token")
    if row.revoked_at is not None:
        # Reuse of a rotated token: assume theft and kill the whole family.
        await _revoke_family(db, row.family_id)
        await db.commit()
        raise AuthenticationError("Refresh token reuse detected", code="refresh_token_reused")
    if row.expires_at <= _now():
        raise AuthenticationError("Refresh token expired", code="invalid_refresh_token")
    user = await db.get(User, row.user_id)
    if not user or user.deleted_at or user.status in _LOGIN_BLOCKED:
        raise AuthenticationError("Account unavailable", code="account_disabled")

    remember = (row.expires_at - row.created_at) > timedelta(days=2)  # inherit the original choice
    new_row, session = await _issue(db, user, family_id=row.family_id, ip=ip, ua=ua, remember=remember)
    row.revoked_at = _now()
    row.replaced_by_id = new_row.id
    await db.commit()
    return session


async def logout(db: AsyncSession, raw_token: str | None) -> None:
    if not raw_token:
        return
    row = await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token)))
    if row:
        await _revoke_family(db, row.family_id)
        await db.commit()


async def _revoke_family(db: AsyncSession, family_id: uuid.UUID) -> None:
    rows = await db.scalars(
        select(RefreshToken).where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
    )
    now = _now()
    for r in rows:
        r.revoked_at = now
