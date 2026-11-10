from app.core.permissions import ALL, PERMISSIONS, ROLES


def test_role_grants_reference_known_permissions():
    for slug, spec in ROLES.items():
        assert spec["permissions"] <= ALL, f"{slug} grants unknown permissions: {spec['permissions'] - ALL}"


def test_permission_codes_are_module_action():
    assert all(code.count(":") == 1 for code in PERMISSIONS)


def test_only_pharmacist_and_super_admin_can_review_prescriptions():
    holders = {s for s, spec in ROLES.items() if "prescriptions:review" in spec["permissions"]}
    assert holders == {"super_admin", "pharmacist"}
