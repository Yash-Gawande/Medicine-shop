"""Permission catalog and default role grants: the single source of truth.

- Codes are `<module>:<action>`. Routes declare the code they need via
  `require_permission("products:write")` (Phase 2).
- Default grants seed the system roles. Admins can edit grants at runtime
  (`roles:manage`), but cannot edit `super_admin` or remove their own access.
- `docs/rbac.md` documents this file; `tests/test_permissions.py` keeps them consistent.
"""

from __future__ import annotations

from typing import Final

PERMISSIONS: Final[dict[str, str]] = {
    # Dashboard & reports
    "dashboard:view": "View dashboard metrics",
    "reports:view": "View sales, inventory and operational reports",
    "reports:export": "Export reports to CSV/Excel",
    # Catalog
    "products:read": "View products in admin",
    "products:write": "Create and edit products, variants, images, attributes",
    "products:publish": "Publish, unpublish and archive products",
    "products:import": "Bulk import products from CSV",
    "catalog:manage": "Manage categories, brands, manufacturers, attributes",
    # Inventory
    "inventory:read": "View stock, batches and movements",
    "inventory:adjust": "Record stock adjustments and write-offs",
    "inventory:receive": "Receive stock against purchase orders",
    "inventory:recall": "Quarantine or recall batches",
    "suppliers:manage": "Manage suppliers and purchase orders",
    # Prescriptions
    "prescriptions:read": "View prescription queue and documents (access is logged)",
    "prescriptions:review": "Approve, reject or request re-upload (needs pharmacist registration)",
    # Orders
    "orders:read": "View orders",
    "orders:update_status": "Move orders through fulfilment states",
    "orders:cancel": "Cancel eligible orders",
    "refunds:process": "Initiate refunds",
    "payments:read": "View payments, webhooks and reconciliation",
    "invoices:read": "Download invoices",
    # Delivery
    "delivery:read": "View delivery assignments",
    "delivery:assign": "Assign orders to staff or partners",
    "delivery:update": "Update delivery status and upload proof",
    "delivery:configure": "Manage partners, serviceable PIN codes, delivery charges",
    # Customers
    "customers:read": "View customer profiles, addresses, order history",
    "customers:manage": "Activate or deactivate customer accounts",
    # Marketing & CMS
    "coupons:manage": "Manage coupons and campaigns",
    "cms:manage": "Edit banners, homepage sections, pages, FAQ (drafts)",
    "cms:publish": "Publish CMS content",
    # System
    "settings:manage": "Edit business settings (fees, licences, GSTIN)",
    "users:manage": "Create staff users and assign roles",
    "roles:manage": "Edit role permissions",
    "audit:read": "View audit logs",
}

ALL: Final = frozenset(PERMISSIONS)

ROLES: Final[dict[str, dict]] = {
    "super_admin": {
        "name": "Super Admin",
        "description": "Complete access. Cannot be edited.",
        "permissions": ALL,
    },
    "admin": {
        "name": "Admin",
        "description": "Runs the business. No prescription approval (requires a pharmacist).",
        "permissions": ALL - {"prescriptions:review", "roles:manage"},
    },
    "pharmacist": {
        "name": "Pharmacist",
        "description": "Prescription review and dispensing checks.",
        "permissions": frozenset(
            {
                "dashboard:view",
                "prescriptions:read",
                "prescriptions:review",
                "orders:read",
                "products:read",
                "inventory:read",
                "customers:read",
            }
        ),
    },
    "inventory_manager": {
        "name": "Inventory Manager",
        "description": "Products, stock, batches, expiry, suppliers.",
        "permissions": frozenset(
            {
                "dashboard:view",
                "products:read",
                "products:write",
                "products:import",
                "catalog:manage",
                "inventory:read",
                "inventory:adjust",
                "inventory:receive",
                "inventory:recall",
                "suppliers:manage",
                "reports:view",
                "reports:export",
            }
        ),
    },
    "order_manager": {
        "name": "Order Manager",
        "description": "Orders, fulfilment, cancellations, refunds.",
        "permissions": frozenset(
            {
                "dashboard:view",
                "orders:read",
                "orders:update_status",
                "orders:cancel",
                "refunds:process",
                "payments:read",
                "invoices:read",
                "delivery:read",
                "delivery:assign",
                "customers:read",
                "products:read",
                "inventory:read",
                "reports:view",
            }
        ),
    },
    "customer_support": {
        "name": "Customer Support",
        "description": "Customer and order lookups; no money or stock changes.",
        "permissions": frozenset(
            {
                "dashboard:view",
                "customers:read",
                "orders:read",
                "invoices:read",
                "delivery:read",
                "products:read",
            }
        ),
    },
    "delivery_manager": {
        "name": "Delivery Manager",
        "description": "Delivery assignments, status and configuration.",
        "permissions": frozenset(
            {
                "dashboard:view",
                "orders:read",
                "delivery:read",
                "delivery:assign",
                "delivery:update",
                "delivery:configure",
            }
        ),
    },
    "delivery_agent": {
        "name": "Delivery Agent",
        "description": "Own-staff rider: sees and updates only their assigned deliveries.",
        "permissions": frozenset({"delivery:read", "delivery:update"}),
    },
}
