"""Management commands. Run: `uv run python -m app.cli create-superadmin`"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import sys
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.core.seed import seed_rbac
from app.models.auth import Role, StaffProfile, User
from app.models.enums import UserStatus, UserType

DEFAULT_EMAIL = "admin@pharmacy.local"


async def create_superadmin(
    db: AsyncSession, password: str, email: str = DEFAULT_EMAIL, full_name: str = "Super Admin"
) -> User:
    """Creates the super admin, or resets its password if the email already exists."""
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    await seed_rbac(db)
    email = email.lower()
    user = await db.scalar(select(User).where(func.lower(User.email) == email, User.deleted_at.is_(None)))
    if user is None:
        user = User(email=email, user_type=UserType.STAFF, roles=[])
        db.add(user)
        user.staff_profile = StaffProfile(full_name=full_name)
    user.password_hash = hash_password(password)
    user.password_changed_at = datetime.now(UTC)
    user.status = UserStatus.ACTIVE
    user.is_email_verified = True
    user.failed_login_attempts = 0
    user.locked_until = None
    role = await db.scalar(select(Role).where(Role.slug == "super_admin"))
    if role not in user.roles:
        user.roles.append(role)
    await db.commit()
    return user


async def _run(args: argparse.Namespace) -> None:
    from app.core.database import SessionLocal, engine

    password = args.password or os.environ.get("SUPERADMIN_PASSWORD") or getpass.getpass("Super admin password: ")
    async with SessionLocal() as db:
        user = await create_superadmin(db, password, args.email, args.name)
    await engine.dispose()
    print(f"Super admin ready: {user.email}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("create-superadmin", help="Create (or reset the password of) the super admin")
    p.add_argument("--password", help="Prefer the prompt or SUPERADMIN_PASSWORD; args show up in shell history")
    p.add_argument("--email", default=DEFAULT_EMAIL)
    p.add_argument("--name", default="Super Admin")
    args = parser.parse_args()
    try:
        asyncio.run(_run(args))
    except ValueError as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
