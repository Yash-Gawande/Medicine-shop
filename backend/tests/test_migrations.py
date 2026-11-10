from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from app.models import Base
from tests.conftest import DB_URL, alembic_config

SYNC_URL = DB_URL.replace("+asyncpg", "+psycopg")


def test_models_and_migrations_have_no_drift():
    engine = create_engine(SYNC_URL)
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn, opts={"compare_type": True, "compare_server_default": True})
        diff = compare_metadata(ctx, Base.metadata)
    engine.dispose()
    assert diff == [], f"models differ from migrations: {diff}"


def test_all_tables_created():
    engine = create_engine(SYNC_URL)
    tables = set(inspect(engine).get_table_names())
    engine.dispose()
    assert set(Base.metadata.tables) <= tables


def test_downgrade_then_upgrade_roundtrip():
    cfg = alembic_config()
    command.downgrade(cfg, "base")
    engine = create_engine(SYNC_URL)
    remaining = set(inspect(engine).get_table_names()) - {"alembic_version"}
    engine.dispose()
    assert remaining == set()
    command.upgrade(cfg, "head")
