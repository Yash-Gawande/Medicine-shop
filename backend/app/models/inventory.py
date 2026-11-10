"""Batch-aware inventory, suppliers, purchase orders and the immutable stock ledger."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from app.models.enums import BatchStatus, PurchaseOrderStatus, StockMovementType


class Supplier(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "suppliers"

    name: Mapped[str] = mapped_column(String(200), unique=True)
    contact_person: Mapped[str | None] = mapped_column(String(150))
    contact_number: Mapped[str | None] = mapped_column(String(15))
    email: Mapped[str | None] = mapped_column(String(255))
    gstin: Mapped[str | None] = mapped_column(String(15))
    drug_license_number: Mapped[str | None] = mapped_column(String(100))
    address: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))


class Inventory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Per-variant stock settings. Quantities are the sum of sellable batches;
    `quantity_on_hand`/`quantity_reserved` here are a cache maintained by the
    inventory service inside the same transaction as batch changes."""

    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint("quantity_on_hand >= 0", name="on_hand_non_negative"),
        CheckConstraint(
            "quantity_reserved >= 0 AND quantity_reserved <= quantity_on_hand", name="reserved_within_on_hand"
        ),
        CheckConstraint("low_stock_threshold >= 0", name="threshold_non_negative"),
    )

    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id", ondelete="CASCADE"), unique=True)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    quantity_reserved: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=10, server_default=text("10"))
    reorder_quantity: Mapped[int | None] = mapped_column(Integer)
    # Batches expiring within this many days are not allocated to customer orders.
    min_shelf_life_days: Mapped[int] = mapped_column(Integer, default=30, server_default=text("30"))


class InventoryBatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inventory_batches"
    __table_args__ = (
        UniqueConstraint("variant_id", "batch_number", name="uq_inventory_batches_variant_batch"),
        # FEFO allocation: sellable batches of a variant ordered by expiry.
        Index(
            "ix_inventory_batches_fefo",
            "variant_id",
            "expiry_date",
            postgresql_where=text("status = 'active' AND quantity_on_hand > quantity_reserved"),
        ),
        Index("ix_inventory_batches_expiry", "expiry_date"),
        CheckConstraint("quantity_on_hand >= 0", name="on_hand_non_negative"),
        CheckConstraint(
            "quantity_reserved >= 0 AND quantity_reserved <= quantity_on_hand", name="reserved_within_on_hand"
        ),
        CheckConstraint("manufacturing_date IS NULL OR manufacturing_date < expiry_date", name="mfg_before_expiry"),
        CheckConstraint("purchase_price >= 0", name="purchase_price_non_negative"),
        CheckConstraint("mrp > 0", name="mrp_positive"),
    )

    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id", ondelete="RESTRICT"), index=True)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"), index=True)
    purchase_order_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("purchase_order_items.id", ondelete="SET NULL")
    )
    batch_number: Mapped[str] = mapped_column(String(64))
    manufacturing_date: Mapped[date | None]
    expiry_date: Mapped[date]
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    mrp: Mapped[Decimal] = mapped_column(Numeric(12, 2))  # printed MRP of this batch
    quantity_received: Mapped[int] = mapped_column(Integer)
    quantity_on_hand: Mapped[int] = mapped_column(Integer)
    quantity_reserved: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    status: Mapped[BatchStatus] = mapped_column(str_enum(BatchStatus), default=BatchStatus.ACTIVE, index=True)
    status_reason: Mapped[str | None] = mapped_column(Text)  # recall notice ref, quarantine reason
    status_changed_at: Mapped[datetime | None]
    received_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class StockMovement(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Append-only stock ledger. UPDATE/DELETE are blocked by a DB trigger.

    `quantity_delta` is signed against on-hand stock; reservation movements
    use `reserved_delta` and leave on-hand untouched.
    """

    __tablename__ = "stock_movements"
    __table_args__ = (
        Index("ix_stock_movements_reference", "reference_type", "reference_id"),
        CheckConstraint("quantity_delta <> 0 OR reserved_delta <> 0", name="non_zero_movement"),
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("inventory_batches.id", ondelete="RESTRICT"), index=True)
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id", ondelete="RESTRICT"), index=True)
    movement_type: Mapped[StockMovementType] = mapped_column(str_enum(StockMovementType), index=True)
    quantity_delta: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    reserved_delta: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    on_hand_after: Mapped[int] = mapped_column(Integer)
    reserved_after: Mapped[int] = mapped_column(Integer)
    reference_type: Mapped[str | None] = mapped_column(String(50))  # order, purchase_order, adjustment, recall
    reference_id: Mapped[uuid.UUID | None]
    reason: Mapped[str | None] = mapped_column(Text)
    performed_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))


class PurchaseOrder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "purchase_orders"

    po_number: Mapped[str] = mapped_column(String(30), unique=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("suppliers.id", ondelete="RESTRICT"), index=True)
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        str_enum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT, index=True
    )
    supplier_invoice_number: Mapped[str | None] = mapped_column(String(64))
    ordered_at: Mapped[datetime | None]
    expected_at: Mapped[date | None]
    received_at: Mapped[datetime | None]
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    items: Mapped[list[PurchaseOrderItem]] = relationship(back_populates="purchase_order")


class PurchaseOrderItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "purchase_order_items"
    __table_args__ = (
        CheckConstraint("quantity_ordered > 0", name="qty_ordered_positive"),
        CheckConstraint("quantity_received >= 0", name="qty_received_non_negative"),
    )

    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="CASCADE"), index=True
    )
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id", ondelete="RESTRICT"))
    quantity_ordered: Mapped[int] = mapped_column(Integer)
    quantity_received: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))

    purchase_order: Mapped[PurchaseOrder] = relationship(back_populates="items")
