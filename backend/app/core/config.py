"""Application configuration loaded from environment variables.

Every setting is documented in docs/environment.md. Secrets never have
production-safe defaults: the app refuses to boot in staging/production
if they are left at their development placeholders.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Annotated

from pydantic import AnyHttpUrl, Field, PostgresDsn, RedisDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

_DEV_SECRET = "dev-only-change-me-dev-only-change-me"  # noqa: S105 - rejected outside dev


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App -------------------------------------------------------------
    app_name: str = "Online Pharmacy API"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    cors_origins: Annotated[list[AnyHttpUrl], NoDecode] = Field(
        default_factory=lambda: [
            AnyHttpUrl("http://localhost:5173"),
            AnyHttpUrl("http://localhost:5174"),
        ]
    )

    # --- Database / cache -----------------------------------------------
    database_url: PostgresDsn = PostgresDsn("postgresql+asyncpg://pharmacy:pharmacy@localhost:5433/pharmacy")
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False
    redis_url: RedisDsn = RedisDsn("redis://localhost:6380/0")
    celery_broker_url: str = "redis://localhost:6380/1"
    celery_result_backend: str = "redis://localhost:6380/2"

    # --- Security --------------------------------------------------------
    jwt_secret_key: SecretStr = SecretStr(_DEV_SECRET)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 14
    password_reset_token_expire_minutes: int = 30
    otp_expire_minutes: int = 10
    otp_max_attempts: int = 5
    login_max_failed_attempts: int = 5
    login_lockout_minutes: int = 15
    rate_limit_default: str = "120/minute"
    rate_limit_auth: str = "10/minute"

    # --- Razorpay --------------------------------------------------------
    razorpay_key_id: str = ""
    razorpay_key_secret: SecretStr = SecretStr("")
    razorpay_webhook_secret: SecretStr = SecretStr("")

    # --- AWS S3 ----------------------------------------------------------
    aws_region: str = "ap-south-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: SecretStr = SecretStr("")
    s3_endpoint_url: str | None = None  # set for MinIO/LocalStack in dev
    s3_public_bucket: str = "pharmacy-public-assets"
    s3_private_bucket: str = "pharmacy-private-documents"
    s3_signed_url_expire_seconds: int = 300
    max_upload_size_mb: int = 10

    # --- Notifications ---------------------------------------------------
    email_backend: str = "console"  # console | smtp | ses
    email_from: str = "no-reply@example.com"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_username: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_use_tls: bool = False
    sms_backend: str = "console"  # console | msg91 | twilio
    sms_api_key: SecretStr = SecretStr("")
    sms_sender_id: str = ""

    # --- Frontend URLs (for links in emails) ------------------------------
    customer_app_url: AnyHttpUrl = AnyHttpUrl("http://localhost:5173")
    admin_app_url: AnyHttpUrl = AnyHttpUrl("http://localhost:5174")

    # --- Business defaults (overridable at runtime via `settings` table) --
    default_currency: str = "INR"
    business_state_code: str = "27"  # GST state code of the dispatching pharmacy

    @model_validator(mode="before")
    @classmethod
    def _split_cors(cls, data: dict) -> dict:
        raw = data.get("cors_origins") if isinstance(data, dict) else None
        if isinstance(raw, str):
            data["cors_origins"] = [o.strip() for o in raw.split(",") if o.strip()]
        return data

    @model_validator(mode="after")
    def _guard_production_secrets(self) -> Settings:
        if self.environment in (Environment.STAGING, Environment.PRODUCTION):
            problems = []
            if self.jwt_secret_key.get_secret_value() == _DEV_SECRET:
                problems.append("JWT_SECRET_KEY")
            if len(self.jwt_secret_key.get_secret_value()) < 32:
                problems.append("JWT_SECRET_KEY (min 32 chars)")
            if self.debug:
                problems.append("DEBUG must be false")
            if problems:
                raise ValueError(f"Insecure configuration for {self.environment}: {problems}")
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def sync_database_url(self) -> str:
        """psycopg URL for Alembic and tooling that needs a sync driver."""
        return str(self.database_url).replace("+asyncpg", "+psycopg")


@lru_cache
def get_settings() -> Settings:
    return Settings()
