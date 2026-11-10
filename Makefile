.PHONY: up down db-migrate db-revision api worker test test-backend test-frontend lint

up:            ## Start Postgres + Redis
	docker compose up -d postgres redis
down:
	docker compose down
db-migrate:    ## Apply migrations
	cd backend && uv run alembic upgrade head
db-revision:   ## make db-revision m="add x"
	cd backend && uv run alembic revision --autogenerate -m "$(m)"
api:
	cd backend && uv run fastapi dev app/main.py
worker:
	cd backend && uv run celery -A app.tasks.celery_app worker -B --loglevel=INFO
test: test-backend test-frontend
test-backend:
	cd backend && uv run pytest
test-frontend:
	cd frontend/customer && npm test && cd ../admin && npm test
lint:
	cd backend && uv run ruff check app tests && uv run ruff format --check app tests
	cd frontend/customer && npm run lint && cd ../admin && npm run lint
