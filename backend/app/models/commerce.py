"""Carts, orders, order lines, batch allocations, status history and invoices."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from app.models.enums import CartStatus, OrderStatus, PaymentMethod, PaymentStatus


class Cart(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Customer cart or guest cart (identified by an opaque `guest_token`).
    Guest carts are merged into the customer cart on login."""

    __tablename__ = "carts"
    __table_args__ = (
        Index(
            "uq_carts_active_customer",
            "customer_id",
            unique=True,
            postgresql_where=text("status = 'active' AND customer_id IS NOT NULL"),
        ),
        CheckConstraint("customer_id IS NOT NULL OR guest_token_hash IS NOT NULL", name="has_owner"),
    )

    customer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    guest_token_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    status: Mapped[CartStatus] = mapped_column(str_enum(CartStatus), default=CartStatus.ACTIVE)
    coupon_code: Mapped[str | None] = mapped_column(String(40))
    expires_at: Mapped[datetime | None]

    items: Mapped[list[CartItem]] = relationship(back_populates="cart", order_by="CartItem.created_at")


class CartItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "variant_id"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    cart_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), index=True)
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column(Integer)
    # No price column on purpose: prices are always recalculated server-side.

    cart: Mapped[Cart] = relationship(back_populates="items")


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_customer_created", "customer_id", "created_at"),
        Index("ix_orders_status_created", "status", "created_at"),
        CheckConstraint(
            "subtotal_amount >= 0 AND discount_amount >= 0 AND coupon_discount_amount >= 0 "
            "AND tax_amount >= 0 AND shipping_amount >= 0 AND total_amount >= 0",
            name="amounts_non_negative",
        ),
        CheckConstraint("shipping_pincode ~ '^[1-9][0-9]{5}$'", name="shipping_pincode_format"),
    )

    order_number: Mapped[str] = mapped_column(String(30), unique=True)  # e.g. ORD-261110-000123
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"))
    status: Mapped[OrderStatus] = mapped_column(str_enum(OrderStatus), default=OrderStatus.PENDING)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        str_enum(PaymentStatus), default=PaymentStatus.PENDING, index=True
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(str_enum(PaymentMethod))
    requires_prescription: Mapped[bool] = mapped_column(default=False, server_default=text("false"))

    # Money (INR). All computed by the pricing service; never accepted from clients.
    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))  # sum of MRP x qty
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)  # MRP - selling price
    coupon_discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)  # GST included in prices
    shipping_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="INR", server_default="INR")
    coupon_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("coupons.id", ondelete="SET NULL"))
    coupon_code: Mapped[str | None] = mapped_column(String(40))

    # Shipping address snapshot (addresses can be edited/deleted later).
    shipping_name: Mapped[str] = mapped_column(String(150))
    shipping_phone: Mapped[str] = mapped_column(String(15))
    shipping_address_line1: Mapped[str] = mapped_column(String(255))
    shipping_address_line2: Mapped[str | None] = mapped_column(String(255))
    shipping_landmark: Mapped[str | None] = mapped_column(String(150))
    shipping_city: Mapped[str] = mapped_column(String(100))
    shipping_state: Mapped[str] = mapped_column(String(100))
    shipping_state_code: Mapped[str] = mapped_column(String(2))
    shipping_pincode: Mapped[str] = mapped_column(String(6))

    customer_notes: Mapped[str | None] = mapped_column(Text)
    placed_at: Mapped[datetime | None]
    confirmed_at: Mapped[datetime | None]
    delivered_at: Mapped[datetime | None]
    cancelled_at: Mapped[datetime | None]
    cancellation_reason: Mapped[str | None] = mapped_column(Text)
    cancelled_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    expected_delivery_date: Mapped[datetime | None]

    items: Mapped[list[OrderItem]] = relationship(back_populates="order")
    status_history: Mapped[list[OrderStatusHistory]] = relationship(
        back_populates="order", order_by="OrderStatusHistory.created_at"
    )


class OrderItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("unit_price <= unit_mrp", name="price_within_mrp"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id", ondelete="RESTRICT"), index=True)
    # Snapshots so invoices stay correct when the catalog changes.
    product_name_snapshot: Mapped[str] = mapped_column(String(255))
    variant_name_snapshot: Mapped[str] = mapped_column(String(255))
    sku_snapshot: Mapped[str] = mapped_column(String(64))
    hsn_code: Mapped[str | None] = mapped_column(String(8))
    prescription_required: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_mrp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    coupon_discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    cgst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    sgst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    igst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    order: Mapped[Order] = relationship(back_populates="items")
    batch_allocations: Mapped[list[OrderItemBatch]] = relationship(back_populates="order_item")


class OrderItemBatch(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """FEFO allocation of an order line to specific batches (traceability for recalls)."""

    __tablename__ = "order_item_batches"
    __table_args__ = (
        UniqueConstraint("order_item_id", "batch_id"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    order_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("order_items.id", ondelete="CASCADE"), index=True)
    batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inventory_batches.id", ondelete="RESTRICT"), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    released_at: Mapped[datetime | None]  # set when reservation is released (cancel/timeout)
    dispatched_at: Mapped[datetime | None]

    order_item: Mapped[OrderItem] = relationship(back_populates="batch_allocations")


class OrderStatusHistory(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Order activity timeline (append-only)."""

    __tablename__ = "order_status_history"

    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    from_status: Mapped[OrderStatus | None] = mapped_column(str_enum(OrderStatus, name="orderstatus_from"))
    to_status: Mapped[OrderStatus] = mapped_column(str_enum(OrderStatus, name="orderstatus_to"))
    remarks: Mapped[str | None] = mapped_column(Text)
    is_customer_visible: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    changed_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)

    order: Mapped[Order] = relationship(back_populates="status_history")


class Invoice(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """GST tax invoice. Seller details are snapshotted at issue time."""

    __tablename__ = "invoices"

    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="RESTRICT"), unique=True)
    invoice_number: Mapped[str] = mapped_column(String(30), unique=True)  # sequential per financial year
    financial_year: Mapped[str] = mapped_column(String(7), index=True)  # e.g. "2026-27"
    issued_at: Mapped[datetime]
    seller_snapshot: Mapped[dict] = mapped_column(JSONB)  # legal name, GSTIN, drug licence nos, address
    place_of_supply_state_code: Mapped[str] = mapped_column(String(2))
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    cgst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    sgst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    igst_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    file_key: Mapped[str | None] = mapped_column(String(512))  # generated PDF in private bucket
