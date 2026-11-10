"""Product catalog: brands, manufacturers, categories, products, variants, images."""

from __future__ import annotations

import uuid
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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin, str_enum
from app.models.enums import AttributeDataType, DosageForm, DrugSchedule, ProductStatus, ProductType

product_categories = Table(
    "product_categories",
    Base.metadata,
    Column("product_id", ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True, index=True),
)


class Manufacturer(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "manufacturers"

    name: Mapped[str] = mapped_column(String(200), unique=True)
    slug: Mapped[str] = mapped_column(String(220), unique=True)
    address: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str] = mapped_column(String(60), default="India", server_default="India")
    drug_license_number: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class Brand(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(String(200), unique=True)
    slug: Mapped[str] = mapped_column(String(220), unique=True)
    manufacturer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("manufacturers.id", ondelete="SET NULL"), index=True
    )
    logo_key: Mapped[str | None] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class Category(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        Index("ix_categories_parent_order", "parent_id", "display_order"),
        CheckConstraint("parent_id IS NULL OR parent_id <> id", name="not_own_parent"),
    )

    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(150))
    slug: Mapped[str] = mapped_column(String(170), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    image_key: Mapped[str | None] = mapped_column(String(512))
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    seo_title: Mapped[str | None] = mapped_column(String(200))
    seo_description: Mapped[str | None] = mapped_column(String(400))

    parent: Mapped[Category | None] = relationship(remote_side="Category.id", back_populates="children")
    children: Mapped[list[Category]] = relationship(back_populates="parent", order_by="Category.display_order")


class Product(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A sellable item family. Price, SKU and stock live on `ProductVariant`."""

    __tablename__ = "products"
    __table_args__ = (
        # Typo-tolerant search (pg_trgm). Extension created in the initial migration.
        Index("ix_products_name_trgm", "name", postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"}),
        Index(
            "ix_products_generic_name_trgm",
            "generic_name",
            postgresql_using="gin",
            postgresql_ops={"generic_name": "gin_trgm_ops"},
        ),
        Index(
            "ix_products_composition_trgm",
            "composition",
            postgresql_using="gin",
            postgresql_ops={"composition": "gin_trgm_ops"},
        ),
        Index("ix_products_listing", "status", "product_type", "brand_id"),
        # Compliance guard: Schedule X and NDPS drugs can never be sold online.
        CheckConstraint(
            "NOT (online_sale_allowed AND drug_schedule IN ('x', 'ndps'))",
            name="no_online_sale_schedule_x_ndps",
        ),
        # Schedule H / H1 always require a prescription.
        CheckConstraint(
            "prescription_required OR drug_schedule NOT IN ('h', 'h1', 'x', 'ndps')",
            name="scheduled_requires_prescription",
        ),
    )

    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(280), unique=True)
    brand_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("brands.id", ondelete="RESTRICT"), index=True)
    manufacturer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("manufacturers.id", ondelete="RESTRICT"), index=True
    )
    primary_category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    product_type: Mapped[ProductType] = mapped_column(str_enum(ProductType))
    status: Mapped[ProductStatus] = mapped_column(str_enum(ProductStatus), default=ProductStatus.DRAFT)

    # Medicine-specific
    generic_name: Mapped[str | None] = mapped_column(String(255))
    composition: Mapped[str | None] = mapped_column(Text)
    dosage_form: Mapped[DosageForm | None] = mapped_column(str_enum(DosageForm))
    drug_schedule: Mapped[DrugSchedule] = mapped_column(
        str_enum(DrugSchedule), default=DrugSchedule.NONE, server_default=DrugSchedule.NONE.value
    )
    prescription_required: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    online_sale_allowed: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    is_cold_chain: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))

    # Tax
    hsn_code: Mapped[str | None] = mapped_column(String(8))

    # Content
    short_description: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    product_information: Mapped[dict | None] = mapped_column(JSONB)  # uses, side effects, etc. (editorial)
    storage_instructions: Mapped[str | None] = mapped_column(Text)
    safety_information: Mapped[str | None] = mapped_column(Text)

    # Merchandising
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    popularity_score: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    seo_title: Mapped[str | None] = mapped_column(String(200))
    seo_description: Mapped[str | None] = mapped_column(String(400))
    seo_keywords: Mapped[str | None] = mapped_column(String(400))

    brand: Mapped[Brand | None] = relationship(lazy="joined")
    manufacturer: Mapped[Manufacturer | None] = relationship(lazy="joined")
    categories: Mapped[list[Category]] = relationship(secondary=product_categories)
    variants: Mapped[list[ProductVariant]] = relationship(
        back_populates="product", order_by="ProductVariant.display_order"
    )
    images: Mapped[list[ProductImage]] = relationship(back_populates="product", order_by="ProductImage.display_order")


class ProductVariant(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Purchasable SKU (e.g. 'Paracetamol 650mg, strip of 15')."""

    __tablename__ = "product_variants"
    __table_args__ = (
        CheckConstraint("mrp > 0", name="mrp_positive"),
        CheckConstraint("selling_price > 0 AND selling_price <= mrp", name="selling_price_within_mrp"),
        CheckConstraint("gst_rate >= 0 AND gst_rate <= 100", name="gst_rate_range"),
        CheckConstraint("max_order_quantity > 0", name="max_qty_positive"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True)
    barcode: Mapped[str | None] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(255))  # display label, e.g. "650 mg · 15 tablets"
    strength: Mapped[str | None] = mapped_column(String(100))
    pack_size: Mapped[str | None] = mapped_column(String(100))
    units_per_pack: Mapped[int | None] = mapped_column(Integer)
    mrp: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    selling_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    gst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    max_order_quantity: Mapped[int] = mapped_column(Integer, default=10, server_default=text("10"))
    weight_grams: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))

    product: Mapped[Product] = relationship(back_populates="variants")


class ProductImage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "product_images"

    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("product_variants.id", ondelete="CASCADE"))
    image_key: Mapped[str] = mapped_column(String(512))
    alt_text: Mapped[str | None] = mapped_column(String(255))
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))

    product: Mapped[Product] = relationship(back_populates="images")


class Attribute(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Admin-defined product attribute (e.g. "Flavour", "Age group", "Sugar free",
    "Skin type"). Core medicine fields (composition, strength, dosage form) stay
    as real columns because business rules and search depend on them."""

    __tablename__ = "attributes"
    __table_args__ = (
        CheckConstraint(
            "data_type NOT IN ('select', 'multi_select') OR jsonb_typeof(options) = 'array'",
            name="select_has_options",
        ),
    )

    code: Mapped[str] = mapped_column(String(60), unique=True)  # snake_case, stable key for filters
    name: Mapped[str] = mapped_column(String(100))
    data_type: Mapped[AttributeDataType] = mapped_column(str_enum(AttributeDataType))
    unit: Mapped[str | None] = mapped_column(String(20))  # "ml", "g", "years"
    options: Mapped[list | None] = mapped_column(JSONB)  # allowed values for select types
    is_filterable: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    is_variant_level: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    display_order: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))


class ProductAttributeValue(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Attribute value on a product, or on one variant when `variant_id` is set.
    Exactly one typed value column is populated, matching the attribute's type."""

    __tablename__ = "product_attribute_values"
    __table_args__ = (
        Index(
            "uq_product_attribute_values_product",
            "product_id",
            "attribute_id",
            unique=True,
            postgresql_where=text("variant_id IS NULL"),
        ),
        UniqueConstraint("variant_id", "attribute_id"),
        Index("ix_product_attribute_values_filter", "attribute_id", "value_text"),
        CheckConstraint(
            "num_nonnulls(value_text, value_number, value_boolean, value_list) = 1",
            name="exactly_one_value",
        ),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("product_variants.id", ondelete="CASCADE"))
    attribute_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("attributes.id", ondelete="RESTRICT"))
    value_text: Mapped[str | None] = mapped_column(String(255))
    value_number: Mapped[Decimal | None] = mapped_column(Numeric(14, 4))
    value_boolean: Mapped[bool | None] = mapped_column(Boolean)
    value_list: Mapped[list | None] = mapped_column(JSONB)  # multi_select

    attribute: Mapped[Attribute] = relationship(lazy="joined")
