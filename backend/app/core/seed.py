"""Idempotent seed of permissions and system roles from app.core.permissions.

Run: `uv run python -m app.core.seed`
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import PERMISSIONS, ROLES
from app.models.auth import Permission, Role

CUSTOMER_ROLE = {
    "name": "Customer",
    "description": "Storefront shopper. No admin permissions.",
    "permissions": frozenset(),
}


async def seed_rbac(db: AsyncSession) -> None:
    existing = {p.code: p for p in await db.scalars(select(Permission))}
    for code, description in PERMISSIONS.items():
        if code in existing:
            existing[code].description = description
        else:
            existing[code] = Permission(code=code, module=code.split(":")[0], description=description)
            db.add(existing[code])

    roles = {r.slug: r for r in await db.scalars(select(Role))}
    for slug, spec in {**ROLES, "customer": CUSTOMER_ROLE}.items():
        role = roles.get(slug) or Role(slug=slug, name=spec["name"], is_system=True)
        role.description = spec["description"]
        role.is_system = True
        # Only reset grants on first creation or for super_admin; admins may edit the rest at runtime.
        if slug not in roles or slug == "super_admin":
            role.permissions = [existing[c] for c in sorted(spec["permissions"])]
        db.add(role)
    await db.commit()


async def _main() -> None:
    from app.core.database import SessionLocal, engine

    async with SessionLocal() as db:
        await seed_rbac(db)
    await engine.dispose()
    print("RBAC seeded")


if __name__ == "__main__":
    asyncio.run(_main())
