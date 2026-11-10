"""CMS: static pages, configurable homepage sections, FAQ.

Draft/publish: editors change `draft_*` fields and preview them; publishing
copies draft -> published fields so the live site never shows half-edits.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from app.models.enums import HomepageSectionType, PublishStatus


class Page(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """About, Contact, Privacy, Terms, Returns & Refunds, Delivery policy, ..."""

    __tablename__ = "pages"

    slug: Mapped[str] = mapped_column(String(120), unique=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(Text)  # published, sanitised HTML
    draft_title: Mapped[str | None] = mapped_column(String(200))
    draft_content: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PublishStatus] = mapped_column(str_enum(PublishStatus), default=PublishStatus.DRAFT)
    seo_title: Mapped[str | None] = mapped_column(String(200))
    seo_description: Mapped[str | None] = mapped_column(String(400))
    show_in_footer: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    published_at: Mapped[datetime | None]
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))


class HomepageSection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Ordered building blocks of the homepage.

    `config` shape depends on `section_type`, validated by Pydantic schemas, e.g.
    product_carousel: {"source": "manual"|"best_sellers"|"featured"|"category",
                       "product_ids": [...], "category_id": ..., "limit": 12}
    """

    __tablename__ = "homepage_sections"
    __table_args__ = (Index("ix_homepage_sections_order", "is_active", "display_order"),)

    key: Mapped[str] = mapped_column(String(80), unique=True)
    section_type: Mapped[HomepageSectionType] = mapped_column(str_enum(HomepageSectionType))
    title: Mapped[str | None] = mapped_column(String(200))
    subtitle: Mapped[str | None] = mapped_column(String(300))
    config: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"))
    draft_config: Mapped[dict | None] = mapped_column(JSONB)
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    status: Mapped[PublishStatus] = mapped_column(str_enum(PublishStatus), default=PublishStatus.DRAFT)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    published_at: Mapped[datetime | None]


class Faq(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "faq"
    __table_args__ = (Index("ix_faq_category_order", "category", "display_order"),)

    category: Mapped[str] = mapped_column(String(80), default="general")
    question: Mapped[str] = mapped_column(String(500))
    answer: Mapped[str] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
