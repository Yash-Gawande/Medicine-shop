import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import get_db
from app.core.seed import seed_rbac
from app.models.auth import RefreshToken, Role, User
from app.models.customer import Customer
from app.models.enums import UserStatus, UserType

PW = "Str0ngPass1"
BASE = "/api/v1/auth"


@pytest.fixture
async def api(db):
    from app.main import create_app

    app = create_app()

    async def _db():
        yield db

    app.dependency_overrides[get_db] = _db
    await seed_rbac(db)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        c.app = app
        yield c


async def register(api, email="a@example.com", mobile="9876543210"):
    payload = {"full_name": "A B", "email": email, "mobile": mobile, "password": PW}
    return await api.post(f"{BASE}/register", json=payload)


async def test_register_login_me(api, db):
    r = await register(api)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["user"]["mobile"] == "+919876543210"
    assert (await db.scalar(select(Customer.full_name))) == "A B"
    assert body["user"]["roles"] == ["customer"] and body["user"]["permissions"] == []
    assert "httponly" in r.headers["set-cookie"].lower()

    api.cookies.clear()
    r = await api.post(f"{BASE}/login", json={"identifier": "A@Example.com", "password": PW})
    assert r.status_code == 200
    token = r.json()["access_token"]
    r = await api.get(f"{BASE}/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200 and r.json()["email"] == "a@example.com"

    api.cookies.clear()
    r = await api.post(f"{BASE}/login", json={"identifier": "98765 43210", "password": PW})
    assert r.status_code == 200


async def test_duplicate_and_validation(api):
    assert (await register(api)).status_code == 201
    assert (await register(api, mobile="9123456780")).status_code == 409
    assert (await register(api, email="b@example.com", mobile="1234")).status_code == 422
    r = await api.post(f"{BASE}/register", json={"full_name": "A B", "email": "c@example.com", "password": "short"})
    assert r.status_code == 422


async def test_bad_credentials_and_lockout(api, settings):
    await register(api)
    for _ in range(settings.login_max_failed_attempts):
        r = await api.post(f"{BASE}/login", json={"identifier": "a@example.com", "password": "wrong"})
        assert r.status_code == 401 and r.json()["error"]["code"] == "invalid_credentials"
    r = await api.post(f"{BASE}/login", json={"identifier": "a@example.com", "password": PW})
    assert r.status_code == 401 and r.json()["error"]["code"] == "account_locked"
    r = await api.post(f"{BASE}/login", json={"identifier": "nobody@example.com", "password": PW})
    assert r.json()["error"]["code"] == "invalid_credentials"


async def test_me_requires_valid_token(api):
    assert (await api.get(f"{BASE}/me")).status_code == 401
    r = await api.get(f"{BASE}/me", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "invalid_token"


async def test_refresh_rotation_and_reuse_detection(api):
    await register(api)
    old = api.cookies.get("refresh_token")
    r = await api.post(f"{BASE}/refresh")
    assert r.status_code == 200
    new = api.cookies.get("refresh_token")
    assert new and new != old

    # replay the rotated token -> whole family revoked
    api.cookies.clear()
    api.cookies.set("refresh_token", old, path="/api/v1/auth")
    r = await api.post(f"{BASE}/refresh")
    assert r.json()["error"]["code"] == "refresh_token_reused"
    api.cookies.clear()
    api.cookies.set("refresh_token", new, path="/api/v1/auth")
    assert (await api.post(f"{BASE}/refresh")).status_code == 401


async def test_logout_revokes_session(api, db):
    await register(api)
    assert (await api.post(f"{BASE}/logout")).status_code == 204
    rows = (await db.scalars(select(RefreshToken))).all()
    assert rows and all(r.revoked_at for r in rows)


async def test_inactive_user_cannot_login(api, db):
    await register(api)
    user = await db.scalar(select(User))
    user.status = UserStatus.INACTIVE
    await db.commit()
    r = await api.post(f"{BASE}/login", json={"identifier": "a@example.com", "password": PW})
    assert r.json()["error"]["code"] == "account_disabled"


async def test_require_permission(api, db):
    from fastapi import Depends

    from app.api.deps import require_permission

    @api.app.get("/_t/orders")
    async def _orders(user: User = Depends(require_permission("orders:read"))):
        return {"ok": True}

    r = await register(api)
    hdr = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert (await api.get("/_t/orders", headers=hdr)).status_code == 403

    user = await db.scalar(select(User))
    user.user_type = UserType.STAFF
    user.roles.append(await db.scalar(select(Role).where(Role.slug == "order_manager")))
    await db.commit()
    db.expire_all()
    assert (await api.get("/_t/orders", headers=hdr)).status_code == 200


async def test_superadmin_password_only_login(api, db):
    from app.cli import DEFAULT_EMAIL, create_superadmin

    await create_superadmin(db, "AdminPass123")
    await create_superadmin(db, "AdminPass456")  # re-run resets password, no duplicate
    r = await api.post(f"{BASE}/login", json={"identifier": DEFAULT_EMAIL, "password": "AdminPass123"})
    assert r.status_code == 401
    r = await api.post(f"{BASE}/login", json={"identifier": DEFAULT_EMAIL, "password": "AdminPass456"})
    assert r.status_code == 200
    user = r.json()["user"]
    assert user["roles"] == ["super_admin"] and user["user_type"] == "staff"
    assert "roles:manage" in user["permissions"]
