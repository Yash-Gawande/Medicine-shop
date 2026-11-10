"""Customers, profiles, addresses and wishlists."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Numeric, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, CreatedAtMixin, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from app.models.enums import AddressType, Gender

PINCODE_CHECK = "pincode ~ '^[1-9][0-9]{5}$'"


class Customer(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "customers"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), unique=True)
    full_name: Mapped[str] = mapped_column(String(150))
    mobile: Mapped[str | None] = mapped_column(String(15), index=True)

    profile: Mapped[CustomerProfile | None] = relationship(back_populates="customer", uselist=False)
    addresses: Mapped[list[CustomerAddress]] = relationship(
        back_populates="customer", order_by="CustomerAddress.created_at"
    )


class CustomerProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customer_profiles"

    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), unique=True)
    date_of_birth: Mapped[date | None]
    gender: Mapped[Gender | None] = mapped_column(str_enum(Gender))
    avatar_key: Mapped[str | None] = mapped_column(String(512))
    marketing_email_opt_in: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    marketing_sms_opt_in: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    preferred_language: Mapped[str] = mapped_column(String(10), default="en", server_default="en")

    customer: Mapped[Customer] = relationship(back_populates="profile")


class CustomerAddress(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "customer_addresses"
    __table_args__ = (
        # At most one live default address per customer.
        Index(
            "uq_customer_addresses_default",
            "customer_id",
            unique=True,
            postgresql_where=text("is_default AND deleted_at IS NULL"),
        ),
        CheckConstraint(PINCODE_CHECK, name="pincode_format"),
        CheckConstraint("contact_phone ~ '^\\+91[6-9][0-9]{9}$'", name="contact_phone_format"),
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    label: Mapped[AddressType] = mapped_column(str_enum(AddressType), default=AddressType.HOME)
    contact_name: Mapped[str] = mapped_column(String(150))
    contact_phone: Mapped[str] = mapped_column(String(15))
    address_line1: Mapped[str] = mapped_column(String(255))
    address_line2: Mapped[str | None] = mapped_column(String(255))
    landmark: Mapped[str | None] = mapped_column(String(150))
    city: Mapped[str] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    state_code: Mapped[str] = mapped_column(String(2))  # GST state code, drives CGST+SGST vs IGST
    pincode: Mapped[str] = mapped_column(String(6), index=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))

    customer: Mapped[Customer] = relationship(back_populates="addresses")


class WishlistItem(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "wishlist_items"
    __table_args__ = (UniqueConstraint("customer_id", "variant_id"),)

    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    variant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_variants.id", ondelete="CASCADE"))
