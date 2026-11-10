"""Database-level guarantees that must hold even if application code is wrong."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.models import (
    AuditLog,
    Customer,
    CustomerAddress,
    InventoryBatch,
    Product,
    ProductVariant,
    StockMovement,
    User,
)
from app.models.enums import DrugSchedule, ProductType, StockMovementType, UserType


async def _product(db, **overrides) -> Product:
    data = {"name": "Paracetamol 650", "slug": f"p-{uuid.uuid4().hex[:8]}", "product_type": ProductType.OTC_MEDICINE}
    data.update(overrides)
    p = Product(**data)
    db.add(p)
    await db.flush()
    return p


async def _variant(db, product: Product, **overrides) -> ProductVariant:
    data = {
        "sku": f"SKU-{uuid.uuid4().hex[:8]}",
        "name": "15 tablets",
        "mrp": Decimal("30.00"),
        "selling_price": Decimal("27.00"),
        "gst_rate": Decimal("5"),
    }
    data.update(overrides)
    v = ProductVariant(product_id=product.id, **data)
    db.add(v)
    await db.flush()
    return v


async def _customer(db) -> Customer:
    u = User(email=f"{uuid.uuid4().hex[:8]}@example.com", user_type=UserType.CUSTOMER)
    db.add(u)
    await db.flush()
    c = Customer(user_id=u.id, full_name="Test Customer")
    db.add(c)
    await db.flush()
    return c


async def test_schedule_x_cannot_be_sold_online(db):
    with pytest.raises(IntegrityError, match="no_online_sale_schedule_x_ndps"):
        async with db.begin_nested():
            await _product(db, drug_schedule=DrugSchedule.X, prescription_required=True, online_sale_allowed=True)


async def test_schedule_h_requires_prescription(db):
    with pytest.raises(IntegrityError, match="scheduled_requires_prescription"):
        async with db.begin_nested():
            await _product(db, drug_schedule=DrugSchedule.H, prescription_required=False)


async def test_selling_price_cannot_exceed_mrp(db):
    p = await _product(db)
    with pytest.raises(IntegrityError, match="selling_price_within_mrp"):
        async with db.begin_nested():
            await _variant(db, p, mrp=Decimal("30"), selling_price=Decimal("31"))


async def test_duplicate_sku_rejected(db):
    p = await _product(db)
    await _variant(db, p, sku="DUP-1")
    with pytest.raises(IntegrityError):
        async with db.begin_nested():
            await _variant(db, p, sku="DUP-1")


async def test_email_unique_case_insensitive(db):
    db.add(User(email="Same@Example.com", user_type=UserType.CUSTOMER))
    await db.flush()
    with pytest.raises(IntegrityError, match="uq_users_email_lower"):
        async with db.begin_nested():
            db.add(User(email="same@example.com", user_type=UserType.CUSTOMER))
            await db.flush()


async def test_only_one_default_address_per_customer(db):
    c = await _customer(db)
    base = {
        "customer_id": c.id,
        "contact_name": "A",
        "contact_phone": "+919876543210",
        "address_line1": "1 MG Road",
        "city": "Pune",
        "state": "Maharashtra",
        "state_code": "27",
        "pincode": "411001",
        "is_default": True,
    }
    db.add(CustomerAddress(**base))
    await db.flush()
    with pytest.raises(IntegrityError, match="uq_customer_addresses_default"):
        async with db.begin_nested():
            db.add(CustomerAddress(**base))
            await db.flush()


async def test_invalid_pincode_rejected(db):
    c = await _customer(db)
    with pytest.raises(IntegrityError, match="pincode_format"):
        async with db.begin_nested():
            db.add(
                CustomerAddress(
                    customer_id=c.id,
                    contact_name="A",
                    contact_phone="+919876543210",
                    address_line1="x",
                    city="x",
                    state="x",
                    state_code="27",
                    pincode="012345",
                )
            )
            await db.flush()


async def test_batch_reserved_cannot_exceed_on_hand(db):
    v = await _variant(db, await _product(db))
    with pytest.raises(IntegrityError, match="reserved_within_on_hand"):
        async with db.begin_nested():
            db.add(
                InventoryBatch(
                    variant_id=v.id,
                    batch_number="B1",
                    expiry_date=date.today() + timedelta(days=365),
                    purchase_price=Decimal("10"),
                    mrp=Decimal("30"),
                    quantity_received=5,
                    quantity_on_hand=5,
                    quantity_reserved=6,
                )
            )
            await db.flush()


async def test_stock_movements_are_append_only(db):
    v = await _variant(db, await _product(db))
    batch = InventoryBatch(
        variant_id=v.id,
        batch_number="B2",
        expiry_date=date.today() + timedelta(days=365),
        purchase_price=Decimal("10"),
        mrp=Decimal("30"),
        quantity_received=10,
        quantity_on_hand=10,
    )
    db.add(batch)
    await db.flush()
    mv = StockMovement(
        batch_id=batch.id,
        variant_id=v.id,
        movement_type=StockMovementType.OPENING_STOCK,
        quantity_delta=10,
        on_hand_after=10,
        reserved_after=0,
    )
    db.add(mv)
    await db.flush()
    for stmt in (
        "UPDATE stock_movements SET quantity_delta = 99 WHERE id = :id",
        "DELETE FROM stock_movements WHERE id = :id",
    ):
        with pytest.raises(DBAPIError, match="append-only"):
            async with db.begin_nested():
                await db.execute(text(stmt), {"id": mv.id})


async def test_audit_logs_are_append_only(db):
    log = AuditLog(action="test.create", entity_type="test")
    db.add(log)
    await db.flush()
    with pytest.raises(DBAPIError, match="append-only"):
        async with db.begin_nested():
            await db.execute(text("DELETE FROM audit_logs WHERE id = :id"), {"id": log.id})


async def test_trigram_search_tolerates_typos(db):
    await _product(db, name="Paracetamol 650mg Tablet")
    rows = (
        (
            await db.execute(
                text("SELECT name FROM products WHERE similarity(name, :q) > 0.2 ORDER BY similarity(name, :q) DESC"),
                {"q": "paracetmol"},
            )
        )
        .scalars()
        .all()
    )
    assert "Paracetamol 650mg Tablet" in rows


async def test_attribute_value_must_have_exactly_one_typed_value(db):
    from app.models import Attribute, ProductAttributeValue
    from app.models.enums import AttributeDataType

    attr = Attribute(code="sugar_free", name="Sugar free", data_type=AttributeDataType.BOOLEAN)
    db.add(attr)
    p = await _product(db)
    db.add(ProductAttributeValue(product_id=p.id, attribute_id=attr.id, value_boolean=True))
    await db.flush()
    with pytest.raises(IntegrityError, match="exactly_one_value"):
        async with db.begin_nested():
            db.add(ProductAttributeValue(product_id=p.id, attribute_id=attr.id, value_boolean=True, value_text="yes"))
            await db.flush()
