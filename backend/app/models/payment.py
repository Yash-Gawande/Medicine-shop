"""Payments (Razorpay), webhook inbox (idempotency) and refunds."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from app.models.enums import PaymentMethod, PaymentStatus, RefundStatus, WebhookStatus


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One payment attempt for an order. A retry creates a new row.
    Card/UPI credentials are never stored; only gateway references."""

    __tablename__ = "payments"
    __table_args__ = (CheckConstraint("amount > 0", name="amount_positive"),)

    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="RESTRICT"), index=True)
    method: Mapped[PaymentMethod] = mapped_column(str_enum(PaymentMethod))
    status: Mapped[PaymentStatus] = mapped_column(str_enum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR")
    gateway_order_id: Mapped[str | None] = mapped_column(String(64), unique=True)  # razorpay order_xxx
    gateway_payment_id: Mapped[str | None] = mapped_column(String(64), unique=True)  # razorpay pay_xxx
    gateway_method: Mapped[str | None] = mapped_column(String(30))  # upi/card/netbanking/wallet
    signature_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    failure_code: Mapped[str | None] = mapped_column(String(100))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    captured_at: Mapped[datetime | None]
    amount_refunded: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, server_default=text("0"))


class PaymentWebhook(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Inbox of gateway webhooks. Unique `event_id` makes processing idempotent."""

    __tablename__ = "payment_webhooks"
    __table_args__ = (Index("ix_payment_webhooks_status", "status", "created_at"),)

    provider: Mapped[str] = mapped_column(String(30), default="razorpay")
    event_id: Mapped[str] = mapped_column(String(100), unique=True)  # x-razorpay-event-id
    event_type: Mapped[str] = mapped_column(String(80))
    signature_valid: Mapped[bool] = mapped_column(Boolean)
    payload: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[WebhookStatus] = mapped_column(str_enum(WebhookStatus), default=WebhookStatus.RECEIVED)
    processed_at: Mapped[datetime | None]
    error: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(default=0, server_default=text("0"))


class Refund(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "refunds"
    __table_args__ = (CheckConstraint("amount > 0", name="amount_positive"),)

    payment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payments.id", ondelete="RESTRICT"), index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="RESTRICT"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[RefundStatus] = mapped_column(str_enum(RefundStatus), default=RefundStatus.REQUESTED, index=True)
    gateway_refund_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True)
    reason: Mapped[str] = mapped_column(Text)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    initiated_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    processed_at: Mapped[datetime | None]
