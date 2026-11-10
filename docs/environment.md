# Environment variables

The backend reads its configuration from the environment or `backend/.env`, defined in `app/core/config.py`. In `staging` and `production`, the app refuses to start if `JWT_SECRET_KEY` is still the dev placeholder, is shorter than 32 characters, or if `DEBUG=true`.

## Backend

| Variable | Default | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | `development` \| `test` \| `staging` \| `production`. In production, `/docs` and the OpenAPI schema are disabled. |
| `DEBUG` | `false` | Must be false outside development |
| `LOG_LEVEL` | `INFO` | JSON logs outside development. Keys that look like secrets are redacted. |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:5174` | Comma-separated list of allowed origins |
| `DATABASE_URL` | `postgresql+asyncpg://pharmacy:pharmacy@localhost:5433/pharmacy` | Async SQLAlchemy URL |
| `DATABASE_POOL_SIZE` / `DATABASE_MAX_OVERFLOW` | `10` / `20` | Connection pool size per process |
| `REDIS_URL` | `redis://localhost:6380/0` | Cache and rate limiting |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | `redis://localhost:6380/1` / `/2` | Background jobs |
| `JWT_SECRET_KEY` | dev placeholder | **Secret.** At least 32 characters. Generate with `python -c "import secrets;print(secrets.token_urlsafe(48))"` |
| `JWT_ALGORITHM` | `HS256` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `14` | Refresh tokens rotate on every use |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | `30` | |
| `OTP_EXPIRE_MINUTES` / `OTP_MAX_ATTEMPTS` | `10` / `5` | |
| `LOGIN_MAX_FAILED_ATTEMPTS` / `LOGIN_LOCKOUT_MINUTES` | `5` / `15` | Account lockout |
| `RATE_LIMIT_DEFAULT` / `RATE_LIMIT_AUTH` | `120/minute` / `10/minute` | |
| `RAZORPAY_KEY_ID` | – | Public key ID |
| `RAZORPAY_KEY_SECRET` | – | **Secret.** Used to sign and verify payments |
| `RAZORPAY_WEBHOOK_SECRET` | – | **Secret.** Used to verify webhook signatures |
| `AWS_REGION` | `ap-south-1` | Mumbai, so data stays in India |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | – | **Secret.** Prefer IAM roles in production |
| `S3_ENDPOINT_URL` | – | Set to `http://localhost:9000` for local MinIO. Leave unset for AWS. |
| `S3_PUBLIC_BUCKET` | `pharmacy-public-assets` | Product, brand and banner images (served through the CDN) |
| `S3_PRIVATE_BUCKET` | `pharmacy-private-documents` | Prescriptions, invoices, delivery proof. Block all public access. |
| `S3_SIGNED_URL_EXPIRE_SECONDS` | `300` | Lifetime of signed URLs for private documents |
| `MAX_UPLOAD_SIZE_MB` | `10` | |
| `EMAIL_BACKEND` | `console` | `console` \| `smtp` \| `ses` |
| `EMAIL_FROM`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS` | – | SMTP settings (`SMTP_PASSWORD` is secret) |
| `SMS_BACKEND` | `console` | `console` \| `msg91` \| `twilio` |
| `SMS_API_KEY` / `SMS_SENDER_ID` | – | SMS provider settings (DLT-registered sender ID for India) |
| `CUSTOMER_APP_URL` / `ADMIN_APP_URL` | localhost | Used in links inside emails |
| `BUSINESS_STATE_CODE` | `27` | GST state code of the dispatching pharmacy (decides CGST+SGST vs IGST) |

Business settings that change at runtime (minimum order value, delivery charges, pharmacy licence details, GSTIN) live in the `settings` table, edited from the admin dashboard, not in env vars.

## Frontend (both apps)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `/api/v1` | API base URL. In dev, the Vite proxy forwards `/api` to the backend. |
| `VITE_DEV_API_TARGET` | `http://localhost:8000` | Dev only: where the proxy sends requests |
| `VITE_RAZORPAY_KEY_ID` | – | Customer app only. Public key. |
| `VITE_BASE_PATH` | `/admin/` | Admin app only. Path the app is served under. |

## Tests

| Variable | Default |
|---|---|
| `TEST_DATABASE_URL` | `postgresql+asyncpg://pharmacy:pharmacy@localhost:5433/pharmacy_test` (the test suite refuses any URL that doesn't contain "test") |
