# Roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Architecture, repo, database design, environment config | ✅ Done |
| 2 | Backend foundation: auth (password + OTP), JWT and refresh rotation, RBAC, audit logging, rate limiting | Next |
| 3 | Catalog APIs: categories, brands, manufacturers, products and variants, search | |
| 4 | Admin dashboard shell, product and category management | |
| 5 | Inventory: batches, FEFO, suppliers, purchase orders, stock movements, expiry, recalls | |
| 6 | Customer website: homepage, listings, product details, search UI | |
| 7 | Cart (guest and logged-in), addresses, PIN validation, checkout, coupons | |
| 8 | Prescription upload, pharmacist review queue, approval workflow | |
| 9 | Orders and state machine, Razorpay, webhooks, refunds, invoices, delivery | |
| 10 | CMS: banners, homepage sections, pages, FAQ, settings, preview | |
| 11 | Reports, analytics, CSV/Excel export, notifications | |
| 12 | Security audit, E2E tests, performance work, deployment (Nginx, TLS, CI/CD, backups, monitoring) | |

## Phase 1: delivered

- Monorepo layout, `docker-compose.yml` (Postgres 17, Redis 7, optional MinIO and Mailpit), backend Dockerfile, Makefile
- 58-table schema with constraints, indexes, `pg_trgm` and append-only triggers, in one initial Alembic migration
- FastAPI app factory: environment-based settings with production guards, structured logging with redaction, request IDs, security headers, a consistent error envelope, liveness and readiness probes, Swagger
- Celery app skeleton
- Customer and admin apps on Vite + React + TypeScript + Tailwind v4, with shadcn/ui config, TanStack Query, an API client that understands the error envelope, and routing
- Tests: 19 backend (migration round trip, drift check, compliance constraints, immutability, trigram search, health, config); 3 tests per frontend app
