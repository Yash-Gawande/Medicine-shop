# Online Pharmacy Platform

Indian online pharmacy: a customer storefront, a separate admin and pharmacy dashboard, and a FastAPI backend.

| App | Path | Dev URL |
|---|---|---|
| Backend API (FastAPI) | `backend/` | http://localhost:8000 (Swagger at `/docs`) |
| Customer website (React) | `frontend/customer/` | http://localhost:5173 |
| Admin dashboard (React) | `frontend/admin/` | http://localhost:5174/admin/ |

Each app builds and deploys on its own.

## Quick start

Prerequisites: Docker, [uv](https://docs.astral.sh/uv/), Node 22 (`nvm use 22`).

```bash
make up                                   # Postgres on :5433, Redis on :6380
cd backend && cp .env.example .env && uv sync && uv run alembic upgrade head
uv run fastapi dev app/main.py            # API on :8000

cd frontend/customer && npm install && npm run dev   # :5173
cd frontend/admin    && npm install && npm run dev   # :5174/admin/
```

Optional local services: `docker compose --profile storage up -d minio` starts S3-compatible storage, and `--profile mail up -d mailpit` starts an email sink.

## Tests

```bash
make test       # backend pytest (runs against real Postgres) + both frontends' vitest
make lint
```

## Docs

- [Architecture](docs/architecture.md): system design, module layout, key decisions
- [Database](docs/database.md): schema by domain, constraints, compliance guards
- [Environment variables](docs/environment.md)
- [Roadmap and phase status](docs/roadmap.md)

> **Compliance:** this software supports, but does not guarantee, compliance with Indian drug, pharmacy, tax and privacy law. Qualified Indian pharmacy and legal professionals must review it before production use.
