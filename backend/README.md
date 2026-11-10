# Backend

FastAPI + SQLAlchemy 2 (async) + Alembic + PostgreSQL. See the [root README](../README.md) and [docs](../docs/).

```bash
uv sync
uv run alembic upgrade head
uv run fastapi dev app/main.py
uv run pytest
```
