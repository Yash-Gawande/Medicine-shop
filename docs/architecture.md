# Architecture

## System overview

```
Users ─▶ CDN ─▶ Nginx (TLS, load balancing)
                 ├─▶ /            customer SPA (static)
                 ├─▶ /admin/      admin SPA (static)
                 └─▶ /api/v1/     FastAPI instances (N, stateless)
                                     ├─ PostgreSQL primary (+ read replica for reports)
                                     ├─ Redis (cache, rate limits, Celery broker)
                                     ├─ S3: public bucket (product/banner images via CDN)
                                     │      private bucket (prescriptions, invoices, delivery proof;
                                     │      signed URLs only)
                                     └─ Razorpay (payments, refunds, webhooks)
                 Celery workers + beat ─▶ email / SMS providers, expiry sweeps,
                                          reservation timeouts, report exports
```

### Differences from the architecture diagram

| Diagram | Implementation | Reason |
|---|---|---|
| MySQL primary + replica | **PostgreSQL** primary + replica | The project spec requires PostgreSQL. The schema also relies on `pg_trgm` (typo-tolerant search), partial unique indexes, JSONB and triggers. |
| Separate Auth Service | Auth **module** inside the FastAPI app | Fewer moving parts. The module has its own models, services and routes, so it can be split out later. |
| API Gateway | Nginx reverse proxy plus FastAPI middleware | Rate limiting, CORS and request IDs live in middleware. A managed gateway can sit in front without code changes. |
| Message Queue | Redis + Celery | Celery is in the required stack. Use SQS or RabbitMQ in production if durability needs grow. |

## Backend layout (modular monolith)

```
app/
  api/v1/         HTTP routes only: parse input, call a service, shape output
  core/           config, database, logging, exceptions, security primitives
  models/         SQLAlchemy models, one file per domain
  schemas/        Pydantic request/response models per domain
  repositories/   data access (queries); no business rules
  services/       business rules and transaction boundaries
  integrations/   Razorpay, S3, SMS, email, courier adapters
  middleware/     request context, security headers, rate limiting
  tasks/          Celery app and background jobs
```

Rules:
- Route handlers contain no business logic.
- Services own transactions: one `async with session.begin()` per use case.
- Money, stock and status changes happen only in services, never on the client.

## Key decisions

1. **Products have variants.** A product (for example "Dolo 650") has one or more `product_variants` (SKU, strength, pack size, MRP, selling price, GST rate). Carts, orders and inventory reference variants. This matches the ER diagram and the admin flow step "add variants and pricing".
2. **Batch-aware inventory with FEFO.** Stock lives in `inventory_batches`, each with its own expiry date and printed MRP. Orders reserve stock batch by batch, earliest expiry first, and record the allocation in `order_item_batches` so every unit can be traced in a recall. The FEFO partial index only covers `active` batches, and expired, recalled or quarantined batches are never allocated.
3. **Immutable history.** Database triggers block UPDATE and DELETE on `stock_movements`, `audit_logs`, `prescription_reviews` and `order_status_history`.
4. **Compliance guards in the database, not only in code.** CHECK constraints stop Schedule X and NDPS drugs from being sold online, force a prescription for Schedule H and H1 drugs, and keep the selling price at or below MRP.
5. **Rx-before-payment flow.** An order containing prescription items goes `prescription_verification_pending` → (pharmacist approves) → `payment_pending` → `confirmed`. A pharmacist reviews the prescription first, so the customer is never charged for something that can't be dispensed. Pharmacists must have a registration number on their `staff_profiles` record, and each review snapshots it.
6. **No client-trusted prices.** Cart items store only variant and quantity. Totals, coupons, GST split (CGST+SGST within the state, IGST across states) and shipping are always recomputed on the server.
7. **Idempotent payments.** Webhooks go into `payment_webhooks`, which has a unique `event_id`. Refunds carry an `idempotency_key`.
8. **Enums stored as VARCHAR plus a CHECK constraint**, not native Postgres enums, so adding a status is an ordinary migration.
9. **GST invoice numbers have no gaps.** `document_sequences` is locked per financial year while an invoice is issued.

## Order state machine (enforced in the service layer, Phase 9)

```
pending ─▶ prescription_verification_pending ─▶ payment_pending ─▶ confirmed
pending ─────────────────────────────────────▶ payment_pending
confirmed ─▶ processing ─▶ packed ─▶ shipped ─▶ out_for_delivery ─▶ delivered
out_for_delivery ─▶ delivery_failed ─▶ out_for_delivery | cancelled
{pending, *_pending, confirmed, processing} ─▶ cancelled ─▶ refunded (if paid)
```
