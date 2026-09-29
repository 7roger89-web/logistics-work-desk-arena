"""Regression guards for the unauthenticated login critical path.

The login shell should stay bounded: it only needs to know whether at least one
live user exists, and it must not import the authenticated Logistics graph until
authentication succeeds.
"""
from __future__ import annotations

import importlib
import sys
import unittest
from unittest.mock import patch

from core.database import has_any_users


class _UsersCollection:
    def __init__(self, rows):
        self.rows = list(rows)
        self.calls = []

    def find(self, query, projection):
        self.calls.append((query, projection))
        return iter(self.rows)


class _Db:
    def __init__(self, rows):
        self.users = _UsersCollection(rows)


class LoginShellLatencyTest(unittest.TestCase):
    def test_user_existence_probe_uses_only_bootstrap_fields(self):
        db = _Db([{"username": "admin", "is_deleted": False}])

        self.assertTrue(has_any_users(db=db))
        self.assertEqual(
            db.users.calls,
            [
                (
                    {},
                    {"_id": 0, "username": 1, "is_deleted": 1},
                )
            ],
        )

    def test_user_existence_probe_false_when_no_live_user(self):
        db = _Db([])

        self.assertFalse(has_any_users(db=db))
        self.assertEqual(len(db.users.calls), 1)

    def test_user_existence_probe_preserves_load_users_truthiness_semantics(self):
        # load_users() historically counted any truthy username value and
        # excluded any truthy is_deleted marker. Keep that decision exactly,
        # including malformed/legacy values, while projecting only two fields.
        db = _Db(
            [
                {"username": "", "is_deleted": False},
                {"username": 123, "is_deleted": "legacy-deleted"},
                {"username": 456, "is_deleted": False},
            ]
        )

        self.assertTrue(has_any_users(db=db))

        deleted_only = _Db(
            [
                {"username": "admin", "is_deleted": True},
                {"username": 123, "is_deleted": "yes"},
            ]
        )
        self.assertFalse(has_any_users(db=deleted_only))

    def test_require_login_does_not_load_full_user_documents_for_bootstrap_check(self):
        from core.auth import require_login

        with (
            patch("core.auth.fresh_session_identity_for_action", return_value=None),
            patch("core.database.has_any_users", return_value=True) as existence_probe,
            patch("core.database.load_users") as load_all_users,
            patch("core.auth._login_hero_css", return_value="<style></style>"),
            patch("core.auth.st") as fake_st,
        ):
            fake_st.form.return_value.__enter__.return_value = fake_st.form.return_value
            fake_st.text_input.side_effect = ["", ""]
            fake_st.form_submit_button.return_value = False

            self.assertIsNone(require_login())

        existence_probe.assert_called_once_with()
        load_all_users.assert_not_called()

    def test_importing_web_app_defers_authenticated_modules(self):
        target_modules = (
            "views.web_app",
            "views.logi_shell",
            "views.logi_view_model",
        )
        saved = {name: sys.modules.get(name) for name in target_modules}
        for name in target_modules:
            sys.modules.pop(name, None)

        try:
            importlib.import_module("views.web_app")
            self.assertNotIn("views.logi_shell", sys.modules)
            self.assertNotIn("views.logi_view_model", sys.modules)
        finally:
            for name in target_modules:
                sys.modules.pop(name, None)
            for name, module in saved.items():
                if module is not None:
                    sys.modules[name] = module


if __name__ == "__main__":
    unittest.main()
