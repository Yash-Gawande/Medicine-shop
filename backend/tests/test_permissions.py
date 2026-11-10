from pathlib import Path

from app.core.permissions import ALL, PERMISSIONS, ROLES

RBAC_DOC = Path(__file__).parents[2] / "docs" / "rbac.md"


def test_role_grants_reference_known_permissions():
    for slug, role in ROLES.items():
        unknown = set(role["permissions"]) - ALL
        assert not unknown, f"{slug} grants unknown permissions {unknown}"


def test_only_pharmacists_and_super_admin_can_review_prescriptions():
    reviewers = {slug for slug, r in ROLES.items() if "prescriptions:review" in r["permissions"]}
    assert reviewers == {"super_admin", "pharmacist"}


def test_permission_codes_are_module_action():
    for code in PERMISSIONS:
        module, _, action = code.partition(":")
        assert module and action and code == code.lower()


def test_rbac_doc_lists_every_permission():
    doc = RBAC_DOC.read_text()
    missing = [code for code in PERMISSIONS if f"`{code}`" not in doc]
    assert not missing, f"docs/rbac.md is missing {missing}"
