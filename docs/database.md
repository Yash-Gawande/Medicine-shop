# Database design

PostgreSQL 17. 58 tables. Migrations live in `backend/migrations/` (Alembic), and models in `backend/app/models/`.

Conventions:
- UUID primary keys. `created_at` and `updated_at` are `timestamptz`, set by the server.
- `deleted_at` soft deletes on catalog, customers, addresses, users, coupons, banners and pages.
- Money is `numeric(12,2)` in INR, and GST rates are `numeric(5,2)`.
- Constraint names follow a fixed convention (`uq_`, `fk_`, `ck_`, `ix_`).
- A test (`tests/test_migrations.py`) fails if the models and migrations drift apart.

## Tables by domain

| Domain | Tables |
|---|---|
| Auth / RBAC | `users`, `staff_profiles`, `roles`, `permissions`, `user_roles`, `role_permissions`, `refresh_tokens`, `otp_verifications` |
| Customer | `customers`, `customer_profiles`, `customer_addresses`, `wishlist_items` |
| Catalog | `manufacturers`, `brands`, `categories` (self-referencing tree), `products`, `product_variants`, `product_images`, `product_categories` |
| Inventory | `inventory` (per-variant thresholds and cached totals), `inventory_batches`, `stock_movements`, `suppliers`, `purchase_orders`, `purchase_order_items` |
| Prescription | `prescriptions`, `prescription_files`, `prescription_reviews`, `prescription_order_items` |
| Commerce | `carts`, `cart_items`, `orders`, `order_items`, `order_item_batches`, `order_status_history`, `invoices` |
| Delivery | `serviceable_pincodes`, `delivery_partners`, `delivery_assignments` |
| Payment | `payments`, `payment_webhooks`, `refunds` |
| Marketing | `coupons`, `coupon_products`, `coupon_categories`, `coupon_usages`, `promotional_campaigns`, `banners`, `testimonials`, `newsletter_subscribers` |
| CMS | `pages`, `homepage_sections`, `faq` |
| System | `notifications`, `audit_logs`, `settings`, `document_sequences`, `search_queries` |

### Additions beyond the provided ER diagram and the spec's minimum list

| Table | Why |
|---|---|
| `staff_profiles` | Stores the pharmacist's registration number, which is required before they can approve prescriptions |
| `prescription_files` | A prescription can have several pages or images |
| `order_item_batches` | FEFO allocation and recall traceability (also in the ER diagram) |
| `serviceable_pincodes` | Delivery PIN validation, delivery estimates, COD and cold-chain availability |
| `delivery_partners`, `delivery_assignments` | Own-staff and third-party delivery flows (from the delivery diagram) |
| `document_sequences` | Gap-free GST invoice numbering per financial year |
| `search_queries` | Search history and popular searches |
| `testimonials`, `newsletter_subscribers` | Homepage content managed from the admin |
| `coupon_products`, `coupon_categories` | Coupon applicability |

## Enforced invariants

| Rule | Mechanism |
|---|---|
| Schedule X / NDPS never sold online | `ck_products_no_online_sale_schedule_x_ndps` |
| Schedule H/H1/X/NDPS need a prescription | `ck_products_scheduled_requires_prescription` |
| Selling price ≤ MRP | `ck_product_variants_selling_price_within_mrp`, `ck_order_items_price_within_mrp` |
| Unique SKU and barcode | unique constraints on `product_variants` |
| Email unique, case-insensitive | `uq_users_email_lower` (partial, ignores soft-deleted users) |
| One default address per customer | `uq_customer_addresses_default` (partial unique) |
| One active cart per customer | `uq_carts_active_customer` |
| One active delivery assignment per order | `uq_delivery_assignments_active` |
| Valid Indian PIN code / mobile number | regex CHECKs (`^[1-9][0-9]{5}$`, `^\+91[6-9][0-9]{9}$`) |
| Reserved stock ≤ on-hand, never negative | CHECKs on `inventory_batches` and `inventory` |
| Unique batch per variant | `uq_inventory_batches_variant_batch` |
| Webhook processed once | unique `payment_webhooks.event_id` |
| Immutable ledgers | `forbid_update_delete()` trigger on 4 tables |

## Search

The `pg_trgm` extension, with GIN trigram indexes on `products.name`, `generic_name` and `composition`, gives typo-tolerant matching (for example, "paracetmol" finds Paracetamol). Ranking and suggestions are built on it in Phase 3.
