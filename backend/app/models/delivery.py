"""Serviceable PIN codes, delivery partners and per-order delivery assignments."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from app.models.enums import DeliveryProviderType, DeliveryStatus


class ServiceablePincode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "serviceable_pincodes"
    __table_args__ = (
        CheckConstraint("pincode ~ '^[1-9][0-9]{5}$'", name="pincode_format"),
        CheckConstraint(
            "min_delivery_days >= 0 AND max_delivery_days >= min_delivery_days", name="delivery_days_range"
        ),
    )

    pincode: Mapped[str] = mapped_column(String(6), unique=True)
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    state_code: Mapped[str] = mapped_column(String(2))
    min_delivery_days: Mapped[int] = mapped_column(Integer, default=1)
    max_delivery_days: Mapped[int] = mapped_column(Integer, default=3)
    cod_available: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    cold_chain_available: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    shipping_fee_override: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class DeliveryPartner(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "delivery_partners"

    name: Mapped[str] = mapped_column(String(150), unique=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)  # integration adapter key
    provider_type: Mapped[DeliveryProviderType] = mapped_column(str_enum(DeliveryProviderType))
    tracking_url_template: Mapped[str | None] = mapped_column(String(500))  # "https://x/track/{tracking_number}"
    config: Mapped[dict | None] = mapped_column(JSONB)  # non-secret settings; secrets live in env
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class DeliveryAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A delivery attempt. Own-staff (staff_user_id) or third-party (partner_id + tracking)."""

    __tablename__ = "delivery_assignments"
    __table_args__ = (
        Index(
            "uq_delivery_assignments_active",
            "order_id",
            unique=True,
            postgresql_where=text("status NOT IN ('delivered', 'failed', 'cancelled')"),
        ),
        CheckConstraint("partner_id IS NOT NULL OR staff_user_id IS NOT NULL", name="has_carrier"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="RESTRICT"), index=True)
    partner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("delivery_partners.id", ondelete="RESTRICT"))
    staff_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    status: Mapped[DeliveryStatus] = mapped_column(str_enum(DeliveryStatus), default=DeliveryStatus.ASSIGNED)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    tracking_number: Mapped[str | None] = mapped_column(String(100), index=True)
    provider_shipment_id: Mapped[str | None] = mapped_column(String(100))
    assigned_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    accepted_at: Mapped[datetime | None]
    picked_up_at: Mapped[datetime | None]
    delivered_at: Mapped[datetime | None]
    failed_at: Mapped[datetime | None]
    failure_reason: Mapped[str | None] = mapped_column(Text)
    proof_file_key: Mapped[str | None] = mapped_column(String(512))  # photo/signature, private bucket
    recipient_name: Mapped[str | None] = mapped_column(String(150))
