"""Coupons, coupon usage, banners, campaigns, testimonials, newsletter."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from app.models.enums import BannerPlacement, CouponScope, DiscountType, PublishStatus

coupon_products = Table(
    "coupon_products",
    Base.metadata,
    Column("coupon_id", ForeignKey("coupons.id", ondelete="CASCADE"), primary_key=True),
    Column("product_id", ForeignKey("products.id", ondelete="CASCADE"), primary_key=True, index=True),
)

coupon_categories = Table(
    "coupon_categories",
    Base.metadata,
    Column("coupon_id", ForeignKey("coupons.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True, index=True),
)


class Coupon(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "coupons"
    __table_args__ = (
        CheckConstraint("code = upper(code)", name="code_uppercase"),
        CheckConstraint("discount_value > 0", name="discount_positive"),
        CheckConstraint("discount_type <> 'percentage' OR discount_value <= 100", name="percentage_max_100"),
        CheckConstraint("expires_at IS NULL OR expires_at > starts_at", name="valid_window"),
        CheckConstraint("usage_limit IS NULL OR usage_limit > 0", name="usage_limit_positive"),
        CheckConstraint("times_used >= 0", name="times_used_non_negative"),
    )

    code: Mapped[str] = mapped_column(String(40), unique=True)
    description: Mapped[str | None] = mapped_column(String(255))
    discount_type: Mapped[DiscountType] = mapped_column(str_enum(DiscountType))
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    max_discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    min_order_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, server_default=text("0"))
    scope: Mapped[CouponScope] = mapped_column(str_enum(CouponScope), default=CouponScope.ALL)
    # Discounts on prescription medicines can be restricted; default excludes them.
    exclude_prescription_items: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    starts_at: Mapped[datetime]
    expires_at: Mapped[datetime | None]
    usage_limit: Mapped[int | None] = mapped_column(Integer)
    per_customer_limit: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"))
    times_used: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    first_order_only: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class CouponUsage(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "coupon_usages"
    __table_args__ = (
        UniqueConstraint("coupon_id", "order_id"),
        Index("ix_coupon_usages_customer", "coupon_id", "customer_id"),
    )

    coupon_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("coupons.id", ondelete="RESTRICT"))
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"))
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    reversed_at: Mapped[datetime | None]  # order cancelled -> usage released


class PromotionalCampaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "promotional_campaigns"
    __table_args__ = (CheckConstraint("ends_at IS NULL OR ends_at > starts_at", name="valid_window"),)

    name: Mapped[str] = mapped_column(String(150))
    slug: Mapped[str] = mapped_column(String(170), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    coupon_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("coupons.id", ondelete="SET NULL"))
    starts_at: Mapped[datetime]
    ends_at: Mapped[datetime | None]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class Banner(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "banners"
    __table_args__ = (
        Index("ix_banners_live", "placement", "status", "display_order"),
        CheckConstraint("ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at", name="valid_window"),
    )

    title: Mapped[str] = mapped_column(String(150))  # internal name
    placement: Mapped[BannerPlacement] = mapped_column(str_enum(BannerPlacement), default=BannerPlacement.HOME_HERO)
    heading: Mapped[str | None] = mapped_column(String(200))
    subheading: Mapped[str | None] = mapped_column(String(300))
    cta_text: Mapped[str | None] = mapped_column(String(60))
    cta_url: Mapped[str | None] = mapped_column(String(500))
    desktop_image_key: Mapped[str | None] = mapped_column(String(512))
    mobile_image_key: Mapped[str | None] = mapped_column(String(512))
    background_color: Mapped[str | None] = mapped_column(String(9))
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("promotional_campaigns.id", ondelete="SET NULL"))
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    starts_at: Mapped[datetime | None]
    ends_at: Mapped[datetime | None]
    status: Mapped[PublishStatus] = mapped_column(str_enum(PublishStatus), default=PublishStatus.DRAFT)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class Testimonial(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "testimonials"
    __table_args__ = (CheckConstraint("rating IS NULL OR rating BETWEEN 1 AND 5", name="rating_range"),)

    author_name: Mapped[str] = mapped_column(String(100))
    author_location: Mapped[str | None] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    rating: Mapped[int | None] = mapped_column(Integer)
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class NewsletterSubscriber(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "newsletter_subscribers"

    email: Mapped[str] = mapped_column(String(255), unique=True)
    confirmed_at: Mapped[datetime | None]
    unsubscribed_at: Mapped[datetime | None]
