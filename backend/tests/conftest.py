"""Test configuration. Tests run against a real PostgreSQL database
(`pharmacy_test`, created by infrastructure/postgres/init.sql) because the
schema relies on Postgres features: CHECK constraints, partial unique indexes,
pg_trgm, and triggers."""

import os

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://pharmacy:pharmacy@localhost:5433/pharmacy_test"),
)

from collections.abc import AsyncIterator

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings

DB_URL = os.environ["DATABASE_URL"]


def alembic_config() -> Config:
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", DB_URL)
    return cfg


@pytest.fixture(scope="session", autouse=True)
def migrated_db() -> None:
    assert "test" in DB_URL, "refusing to run tests against a non-test database"
    cfg = alembic_config()
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


@pytest.fixture
async def db() -> AsyncIterator[AsyncSession]:
    """Session wrapped in an outer transaction that is always rolled back."""
    engine = create_async_engine(DB_URL)
    async with engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()
    await engine.dispose()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from app.main import create_app

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def settings():
    return get_settings()
