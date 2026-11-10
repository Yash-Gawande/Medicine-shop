"""Prescriptions, their files, pharmacist reviews and order coverage.

Files live in the private S3 bucket; only object keys are stored, and the API
issues short-lived signed URLs to authorised viewers.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from app.models.enums import PrescriptionDecision, PrescriptionStatus


class Prescription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "prescriptions"
    __table_args__ = (Index("ix_prescriptions_review_queue", "status", "created_at"),)

    reference_number: Mapped[str] = mapped_column(String(30), unique=True)  # shown to customer, e.g. RX-2611-000123
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), index=True)
    status: Mapped[PrescriptionStatus] = mapped_column(
        str_enum(PrescriptionStatus), default=PrescriptionStatus.UPLOADED
    )
    # Details captured by the pharmacist during review (never auto-extracted).
    patient_name: Mapped[str | None] = mapped_column(String(150))
    doctor_name: Mapped[str | None] = mapped_column(String(150))
    doctor_registration_number: Mapped[str | None] = mapped_column(String(60))
    prescribed_on: Mapped[date | None]
    valid_until: Mapped[date | None]
    customer_notes: Mapped[str | None] = mapped_column(Text)
    rejection_reason: Mapped[str | None] = mapped_column(Text)  # customer-visible
    assigned_pharmacist_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    reviewed_at: Mapped[datetime | None]
    replaces_prescription_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("prescriptions.id", ondelete="SET NULL")
    )  # re-upload chain
    retain_until: Mapped[date | None]  # retention policy; purge job respects this

    files: Mapped[list[PrescriptionFile]] = relationship(
        back_populates="prescription", order_by="PrescriptionFile.page_number"
    )
    reviews: Mapped[list[PrescriptionReview]] = relationship(
        back_populates="prescription", order_by="PrescriptionReview.created_at"
    )


class PrescriptionFile(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "prescription_files"
    __table_args__ = (
        CheckConstraint(
            "content_type IN ('image/jpeg', 'image/png', 'image/webp', 'application/pdf')", name="allowed_content_type"
        ),
        CheckConstraint("size_bytes > 0", name="size_positive"),
    )

    prescription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prescriptions.id", ondelete="CASCADE"), index=True)
    file_key: Mapped[str] = mapped_column(String(512), unique=True)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(50))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    page_number: Mapped[int] = mapped_column(Integer, default=1)

    prescription: Mapped[Prescription] = relationship(back_populates="files")


class PrescriptionReview(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Immutable record of each pharmacist decision."""

    __tablename__ = "prescription_reviews"

    prescription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prescriptions.id", ondelete="CASCADE"), index=True)
    pharmacist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    pharmacist_registration_number: Mapped[str] = mapped_column(String(50))  # snapshot at decision time
    decision: Mapped[PrescriptionDecision] = mapped_column(str_enum(PrescriptionDecision))
    internal_remarks: Mapped[str | None] = mapped_column(Text)
    customer_message: Mapped[str | None] = mapped_column(Text)

    prescription: Mapped[Prescription] = relationship(back_populates="reviews")


class PrescriptionOrderItem(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Which prescription authorises which Rx order line, and for how many units."""

    __tablename__ = "prescription_order_items"
    __table_args__ = (
        UniqueConstraint("prescription_id", "order_item_id"),
        CheckConstraint("approved_quantity IS NULL OR approved_quantity >= 0", name="approved_qty_non_negative"),
    )

    prescription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prescriptions.id", ondelete="RESTRICT"), index=True)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    order_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("order_items.id", ondelete="CASCADE"), index=True)
    approved_quantity: Mapped[int | None] = mapped_column(Integer)
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
