"""Notifications, audit log, runtime settings, document sequences, search log."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from app.models.enums import NotificationChannel, NotificationStatus


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_unread", "user_id", "status"),)

    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    channel: Mapped[NotificationChannel] = mapped_column(str_enum(NotificationChannel))
    template: Mapped[str] = mapped_column(String(80))  # e.g. "order_confirmed"
    recipient: Mapped[str | None] = mapped_column(String(255))  # masked when displayed
    subject: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text)  # never contains OTPs or prescription content
    context: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[NotificationStatus] = mapped_column(str_enum(NotificationStatus), default=NotificationStatus.QUEUED)
    sent_at: Mapped[datetime | None]
    read_at: Mapped[datetime | None]
    error: Mapped[str | None] = mapped_column(Text)


class AuditLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Append-only audit trail for sensitive operations (UPDATE/DELETE blocked by trigger).

    Also records reads of sensitive data (e.g. prescription views) with action="view".
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_actor", "actor_user_id", "created_at"),
    )

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    action: Mapped[str] = mapped_column(String(80), index=True)  # "product.update", "prescription.view"
    entity_type: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    changes: Mapped[dict | None] = mapped_column(JSONB)  # {"field": [old, new]}, secrets redacted
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(String(255))
    request_id: Mapped[str | None] = mapped_column(String(64))


class Setting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Runtime business configuration editable from the admin dashboard.

    e.g. delivery.min_order_value, delivery.free_shipping_threshold,
    pharmacy.legal_name, pharmacy.gstin, pharmacy.drug_license_numbers.
    `is_public` settings are exposed to the customer site.
    """

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(120), unique=True)
    value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB)
    group: Mapped[str] = mapped_column(String(60), index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))


class DocumentSequence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Gap-free counters (GST invoices must be consecutive per financial year).
    Incremented with SELECT ... FOR UPDATE inside the issuing transaction."""

    __tablename__ = "document_sequences"
    __table_args__ = (UniqueConstraint("name", "period"),)

    name: Mapped[str] = mapped_column(String(40))  # invoice, order, prescription, purchase_order
    period: Mapped[str] = mapped_column(String(10))  # "2026-27" or "global"
    next_value: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"))


class SearchQuery(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Search log for history and popular searches. Raw query text only; no PII."""

    __tablename__ = "search_queries"

    customer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    query: Mapped[str] = mapped_column(String(200))
    normalized_query: Mapped[str] = mapped_column(String(200), index=True)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
