"""Domain enumerations. Values are persisted, so never rename a value in place."""

from enum import StrEnum


# --- Auth ---------------------------------------------------------------------
class UserType(StrEnum):
    CUSTOMER = "customer"
    STAFF = "staff"


class UserStatus(StrEnum):
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"


class OtpPurpose(StrEnum):
    MOBILE_VERIFICATION = "mobile_verification"
    EMAIL_VERIFICATION = "email_verification"
    LOGIN = "login"
    PASSWORD_RESET = "password_reset"  # noqa: S105


class OtpChannel(StrEnum):
    SMS = "sms"
    EMAIL = "email"


# --- Customer -----------------------------------------------------------------
class AddressType(StrEnum):
    HOME = "home"
    WORK = "work"
    OTHER = "other"


class Gender(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNDISCLOSED = "undisclosed"


# --- Catalog ------------------------------------------------------------------
class ProductStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ProductType(StrEnum):
    PRESCRIPTION_MEDICINE = "prescription_medicine"
    OTC_MEDICINE = "otc_medicine"
    AYURVEDIC = "ayurvedic"
    HOMEOPATHIC = "homeopathic"
    SUPPLEMENT = "supplement"
    PERSONAL_CARE = "personal_care"
    BABY_CARE = "baby_care"
    MEDICAL_DEVICE = "medical_device"
    FIRST_AID = "first_aid"
    WELLNESS = "wellness"
    OTHER = "other"


class DrugSchedule(StrEnum):
    """Drugs and Cosmetics Rules, 1945 schedules relevant to retail sale.

    Online-sale eligibility is decided by `Product.online_sale_allowed`, which
    compliance staff set; the schedule only drives defaults and warnings.
    Schedule X and narcotic/psychotropic (NDPS) items are blocked from online
    sale by a database CHECK constraint.
    """

    NONE = "none"  # non-drug / cosmetic / device
    OTC = "otc"
    G = "g"
    H = "h"
    H1 = "h1"
    X = "x"
    NDPS = "ndps"


class AttributeDataType(StrEnum):
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"  # one of `options`
    MULTI_SELECT = "multi_select"


class DosageForm(StrEnum):
    TABLET = "tablet"
    CAPSULE = "capsule"
    SYRUP = "syrup"
    SUSPENSION = "suspension"
    INJECTION = "injection"
    OINTMENT = "ointment"
    CREAM = "cream"
    GEL = "gel"
    DROPS = "drops"
    INHALER = "inhaler"
    POWDER = "powder"
    SPRAY = "spray"
    LOTION = "lotion"
    SACHET = "sachet"
    DEVICE = "device"
    OTHER = "other"


# --- Inventory ----------------------------------------------------------------
class BatchStatus(StrEnum):
    ACTIVE = "active"
    QUARANTINED = "quarantined"
    RECALLED = "recalled"
    EXPIRED = "expired"
    DEPLETED = "depleted"


class StockMovementType(StrEnum):
    PURCHASE_RECEIPT = "purchase_receipt"
    OPENING_STOCK = "opening_stock"
    RESERVATION = "reservation"
    RESERVATION_RELEASE = "reservation_release"
    SALE = "sale"  # reservation converted to dispatch
    CUSTOMER_RETURN = "customer_return"
    ADJUSTMENT_INCREASE = "adjustment_increase"
    ADJUSTMENT_DECREASE = "adjustment_decrease"
    DAMAGE = "damage"
    EXPIRY_WRITE_OFF = "expiry_write_off"
    RECALL = "recall"
    SUPPLIER_RETURN = "supplier_return"


class PurchaseOrderStatus(StrEnum):
    DRAFT = "draft"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


# --- Prescription ---------------------------------------------------------------
class PrescriptionStatus(StrEnum):
    UPLOADED = "uploaded"
    PENDING_REVIEW = "pending_review"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REUPLOAD_REQUESTED = "reupload_requested"
    EXPIRED = "expired"


class PrescriptionDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REUPLOAD_REQUESTED = "reupload_requested"


# --- Commerce -------------------------------------------------------------------
class CartStatus(StrEnum):
    ACTIVE = "active"
    MERGED = "merged"
    CONVERTED = "converted"
    ABANDONED = "abandoned"


class OrderStatus(StrEnum):
    PENDING = "pending"
    PRESCRIPTION_VERIFICATION_PENDING = "prescription_verification_pending"
    PAYMENT_PENDING = "payment_pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    PACKED = "packed"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    DELIVERY_FAILED = "delivery_failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"


class PaymentMethod(StrEnum):
    RAZORPAY = "razorpay"
    COD = "cod"


class RefundStatus(StrEnum):
    REQUESTED = "requested"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class WebhookStatus(StrEnum):
    RECEIVED = "received"
    PROCESSED = "processed"
    IGNORED = "ignored"
    FAILED = "failed"


# --- Delivery -------------------------------------------------------------------
class DeliveryProviderType(StrEnum):
    OWN_STAFF = "own_staff"
    THIRD_PARTY = "third_party"


class DeliveryStatus(StrEnum):
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    BOOKED = "booked"  # third-party provider confirmed
    PICKED_UP = "picked_up"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


# --- Marketing / CMS --------------------------------------------------------------
class DiscountType(StrEnum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class CouponScope(StrEnum):
    ALL = "all"
    PRODUCTS = "products"
    CATEGORIES = "categories"


class PublishStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class HomepageSectionType(StrEnum):
    HERO_BANNERS = "hero_banners"
    CATEGORY_GRID = "category_grid"
    PRODUCT_CAROUSEL = "product_carousel"
    PROMO_STRIP = "promo_strip"
    UPLOAD_PRESCRIPTION_CTA = "upload_prescription_cta"
    HEALTH_ARTICLES = "health_articles"
    TESTIMONIALS = "testimonials"
    NEWSLETTER = "newsletter"
    RICH_TEXT = "rich_text"


class BannerPlacement(StrEnum):
    HOME_HERO = "home_hero"
    HOME_SECONDARY = "home_secondary"
    CATEGORY_TOP = "category_top"
    ANNOUNCEMENT_BAR = "announcement_bar"


# --- System -----------------------------------------------------------------------
class NotificationChannel(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"


class NotificationStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"
