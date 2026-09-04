from __future__ import annotations

import unittest
from unittest.mock import patch

from core.auth import has_permission
from views.web_app import NAVIGATION_GROUPS, ROUTES


class DeepLRouteRBACTests(unittest.TestCase):
    def test_translation_route_points_to_dedicated_view_and_permission(self) -> None:
        route = next(route for route in ROUTES if route.label == "Dịch Thuật DeepL")

        self.assertEqual(route.icon, "🌐")
        self.assertEqual(route.permission, "translation")
        self.assertEqual(route.module, "views.translation")
        self.assertEqual(route.function, "ui_translation")

    def test_translation_route_is_grouped_under_tools_and_reference(self) -> None:
        group = next(group for group in NAVIGATION_GROUPS if group[0] == "CÔNG CỤ & THAM KHẢO")

        self.assertIn("Dịch Thuật DeepL", group[1])

    def test_support_and_sale_are_allowed_but_viewer_is_denied(self) -> None:
        for role in ("sale", "support"):
            with self.subTest(role=role), patch("core.auth.st") as streamlit:
                streamlit.session_state = {
                    "current_user": {"username": f"{role}-user", "role": role}
                }
                self.assertTrue(has_permission("translation"))

        with patch("core.auth.st") as streamlit:
            streamlit.session_state = {
                "current_user": {"username": "viewer-user", "role": "viewer"}
            }
            self.assertFalse(has_permission("translation"))

    def test_unauthenticated_user_is_denied(self) -> None:
        with patch("core.auth.st") as streamlit:
            streamlit.session_state = {}
            self.assertFalse(has_permission("translation"))


if __name__ == "__main__":
    unittest.main()
