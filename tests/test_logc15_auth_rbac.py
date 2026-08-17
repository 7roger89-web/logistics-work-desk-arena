"""LOG-C15 tests: xác thực và phân quyền RBAC tối thiểu.

Guarantees under test:
1. User documents are always stored hashed (pbkdf2_sha256) — never plaintext,
   and public views never expose password material.
2. Authentication requires a valid hash AND active=True; failure exposes no
   internal state (wrong password and inactive both return None).
3. RBAC is a single authoritative matrix in core.auth: the 3 modern roles are
   admin / sale / support; the legacy viewer role gets read-only surfaces.
4. finance_write, finance_review_write, admin_write, proxy_payment_delete and
   receivables are exclusively admin — support/sale/viewer cannot touch money
   writes or user management.
5. PermissionDeniedError is raised by assert_permission when the actor lacks
   the required permission, so view rendering can stop safely.
6. Username normalization rejects unsafe identifiers; role validation rejects
   unknown roles; passwords under 8 characters are rejected.
7. Audit provenance (created_by, active_states) is recorded by every admin
   action on the user document.
"""
from __future__ import annotations

import unittest

from core.auth import (
    PermissionDeniedError,
    ROLE_PERMISSIONS,
    assert_permission,
    has_permission,
    has_write_permission,
    hash_password,
    verify_password,
)
from core.users import (
    SUPPORTED_ROLES,
    UserError,
    authenticate,
    build_user_document,
    change_password,
    normalize_role,
    normalize_username,
    public_identity,
    public_summary,
    redact_password_material,
    set_active,
)

SUPPORT_ONLY_READ = frozenset({
    "dashboard", "shipment_edit", "customers", "shipment_360_read",
    "entity_context", "contracts", "tariff", "tracking", "knowledge",
    "commercial_view", "finance_view", "operations_write",
})


class TestPasswordHashing(unittest.TestCase):
    def test_hash_is_pbkdf2_and_never_plaintext(self) -> None:
        encoded = hash_password("correct-horse-battery-staple")
        self.assertTrue(encoded.startswith("pbkdf2_sha256$"))
        self.assertNotIn("correct-horse", encoded)

    def test_roundtrip_and_mismatch(self) -> None:
        encoded = hash_password("p@ssW0rd!99")
        self.assertTrue(verify_password("p@ssW0rd!99", encoded))
        self.assertFalse(verify_password("wrong", encoded))
        self.assertFalse(verify_password("", encoded))

    def test_salt_differs_between_hashes(self) -> None:
        first, second = hash_password("same"), hash_password("same")
        self.assertNotEqual(first, second)

    def test_verify_rejects_malformed(self) -> None:
        self.assertFalse(verify_password("x", ""))
        self.assertFalse(verify_password("x", "scrypt$1$2$3"))


class TestUserNormalization(unittest.TestCase):
    def test_username_requires_safe_identifiers(self) -> None:
        self.assertEqual(normalize_username("  Anh.Sale "), "anh.sale")
        for bad in ("ab", "", "an h", "a.b.c/d", "!", "Aa@1"):
            try:
                normalize_username(bad)
            except UserError:
                continue
            self.fail(f"normalize_username({bad!r}) must raise UserError")

    def test_role_validation(self) -> None:
        for role in SUPPORTED_ROLES:
            self.assertEqual(normalize_role(role), role)
        self.assertEqual(normalize_role("ADMIN"), "admin")
        with self.assertRaises(UserError):
            normalize_role("manager")
        with self.assertRaises(UserError):
            normalize_role("")


class TestUserDocument(unittest.TestCase):
    def _doc(self, **overrides) -> dict:
        defaults = {
            "username": "lan.sale",
            "password": "secure-8-chars",
            "display_name": "Lan",
            "role": "sale",
            "email": "lan@example.com",
            "created_by": "admin",
        }
        defaults.update(overrides)
        return build_user_document(**defaults)

    def test_document_fields_and_hashing(self) -> None:
        doc = self._doc()
        self.assertEqual(doc["username"], "lan.sale")
        self.assertEqual(doc["role"], "sale")
        self.assertTrue(doc["password_hash"].startswith("pbkdf2_sha256$"))
        self.assertEqual(doc["created_by"], "admin")
        self.assertEqual(len(doc["active_states"]), 1)
        self.assertEqual(doc["active_states"][0]["actor"], "admin")

    def test_password_minimum_length(self) -> None:
        with self.assertRaises(UserError):
            self._doc(password="short")

    def test_display_falls_back_to_username(self) -> None:
        doc = self._doc(display_name="")
        self.assertEqual(doc["display_name"], "lan.sale")

    def test_display_name_length_cap(self) -> None:
        doc = self._doc(display_name="x" * 200)
        self.assertLessEqual(len(doc["display_name"]), 60)


class TestAuthentication(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = build_user_document(
            username="minh", password="long-password-1",
            display_name="Minh", role="support", created_by="admin",
        )

    def test_valid_login(self) -> None:
        identity = authenticate(self.doc, "long-password-1")
        self.assertIsNotNone(identity)
        self.assertEqual(identity["role"], "support")
        self.assertNotIn("password_hash", identity)

    def test_wrong_password_is_opaque(self) -> None:
        self.assertIsNone(authenticate(self.doc, "wrong"))

    def test_inactive_user_cannot_login(self) -> None:
        deactivated = set_active(self.doc, False, actor="admin")
        self.assertIsNone(authenticate(deactivated, "long-password-1"))

    def test_password_change_keeps_history_proof(self) -> None:
        updated = change_password(self.doc, "new-long-password", actor="admin")
        self.assertTrue(verify_password("new-long-password", updated["password_hash"]))
        self.assertFalse(verify_password("long-password-1", updated["password_hash"]))
        self.assertEqual(updated["password_changed_by"], "admin")


class TestPublicViews(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = build_user_document(
            username="hue", password="long-password-2",
            display_name="Huệ", role="sale", created_by="admin",
        )

    def test_public_identity_never_carries_hash(self) -> None:
        identity = public_identity(self.doc)
        self.assertNotIn("password_hash", identity)
        self.assertNotIn("password", identity)
        self.assertEqual(identity["username"], "hue")
        self.assertEqual(identity["role"], "sale")

    def test_redact_removes_all_password_material(self) -> None:
        redacted = redact_password_material(self.doc)
        self.assertNotIn("password_hash", redacted)
        self.assertNotIn("password", redacted)

    def test_summary_sorts_stable(self) -> None:
        docs = [self.doc, build_user_document(
            username="bao", password="long-password-3",
            display_name="Bảo", role="admin", created_by="admin",
        )]
        summary = public_summary(docs)
        self.assertEqual([u["username"] for u in summary], ["bao", "hue"])


class TestActiveStateProvenance(unittest.TestCase):
    def test_deactivate_records_actor_and_note(self) -> None:
        doc = build_user_document(
            username="mai", password="long-password-4",
            display_name="Mai", role="support", created_by="admin",
        )
        deactivated = set_active(doc, False, actor="admin")
        self.assertFalse(deactivated["active"])
        self.assertEqual(deactivated["deactivated_by"], "admin")
        self.assertEqual(len(deactivated["active_states"]), 2)
        self.assertEqual(deactivated["active_states"][1]["actor"], "admin")
        self.assertIn("deactivated", deactivated["active_states"][1]["note"])

    def test_noop_when_state_unchanged(self) -> None:
        doc = build_user_document(
            username="duc", password="long-password-5",
            display_name="Đức", role="sale", created_by="admin",
        )
        same = set_active(doc, True, actor="admin")
        self.assertEqual(len(same["active_states"]), 1)


class TestRoleMatrix(unittest.TestCase):
    def test_supported_modern_roles(self) -> None:
        self.assertEqual(set(SUPPORTED_ROLES), {"admin", "sale", "support"})
        self.assertEqual(set(ROLE_PERMISSIONS["admin"]), {"*"})

    def test_support_is_read_only_on_finance_and_admin(self) -> None:
        self.assertEqual(set(ROLE_PERMISSIONS["support"]), SUPPORT_ONLY_READ)
        for forbidden in ("finance_write", "receivables", "admin_write",
                          "finance_review_write", "proxy_payment_delete",
                          "commercial_write", "sales_write"):
            self.assertNotIn(forbidden, ROLE_PERMISSIONS["support"],
                             f"support must not hold {forbidden}")

    def test_sale_cannot_touch_finance_writes_or_admin(self) -> None:
        sale = ROLE_PERMISSIONS["sale"]
        for forbidden in ("finance_write", "receivables", "admin_write",
                          "finance_review_write", "proxy_payment_delete"):
            self.assertNotIn(forbidden, sale, f"sale must not hold {forbidden}")
        self.assertIn("sales_write", sale)
        self.assertIn("commercial_write", sale)

    def test_support_cannot_create_shipments_or_quotes(self) -> None:
        support = ROLE_PERMISSIONS["support"]
        self.assertNotIn("shipment_create", support)
        self.assertNotIn("sales", support)
        self.assertNotIn("sales_write", support)

    def test_viewer_is_read_only(self) -> None:
        for permission in ROLE_PERMISSIONS["viewer"]:
            self.assertFalse(permission.endswith("_write"),
                             f"viewer must not hold {permission}")

    def test_unknown_role_falls_back_to_viewer(self) -> None:
        has_permission_cache_state = {}  # no cache exists; call directly
        self.assertFalse(has_permission("receivables"))  # unauthenticated -> viewer

    def test_permission_denied_error_for_unauthorized(self) -> None:
        from unittest.mock import patch
        with patch("core.auth.st") as mock_st:
            mock_st.session_state = {"current_user": {"username": "hue", "role": "support"}}
            with self.assertRaises(PermissionDeniedError):
                assert_permission("admin_write")
            assert_permission("dashboard")  # allowed


class TestHasPermissionSignature(unittest.TestCase):
    def test_has_write_permission_requires_write_permission(self) -> None:
        from unittest.mock import patch
        with patch("core.auth.st") as mock_st:
            mock_st.session_state = {"current_user": {"username": "hue", "role": "sale"}}
            self.assertTrue(has_write_permission("sales_write"))
            self.assertFalse(has_write_permission("finance_write"))


if __name__ == "__main__":
    unittest.main()
