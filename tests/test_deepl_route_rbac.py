"""Translation route + RBAC acceptance for /dich-thuat.

LOGI_TRANSLATION_RUNTIME_UI_PARITY_01 — repaired for the CURRENT app shape:
since the single React shell (PR #44), ``views/web_app.py`` no longer carries
a Streamlit ``ROUTES`` / ``NAVIGATION_GROUPS`` registry; the /dich-thuat route
lives in the component router (``component/src/App.tsx``) and the RBAC gate
is the EXISTING ``translation`` permission over ``core.auth.ROLE_PERMISSIONS``
enforced server-side by the dispatcher. The old assertions targeted the dead
multi-page shell and could only fail, so they are replaced by equivalent
checks against the architecture that actually ships:

- the component router binds ``/dich-thuat`` to ``TranslationWorkspace``
- sale/support keep the ``translation`` permission; viewer and anonymous don't
- ``translation_capability()`` reflects that session RBAC answer without ever
  exposing key material
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from unittest.mock import patch

from core.auth import has_permission

ROOT = Path(__file__).resolve().parents[1]
APP_TSX = ROOT / "component" / "src" / "App.tsx"

FAKE_KEY = "fake-route-rbac-key-not-a-secret"


class DeepLRouteRBACTests(unittest.TestCase):
    def test_dich_thuat_route_is_bound_to_translation_workspace(self) -> None:
        source = APP_TSX.read_text(encoding="utf-8")
        self.assertIn('import TranslationWorkspace from "./pages/TranslationWorkspace"', source)
        self.assertRegex(
            source,
            re.compile(
                r'<Route\s+path="/dich-thuat"\s+element=\{<TranslationWorkspace\s*/>\}',
            ),
        )

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

    def test_capability_reflects_session_rbac_without_key_material(self) -> None:
        from views import translation as translation_view

        with patch("core.auth.st") as streamlit:
            streamlit.session_state = {
                "current_user": {"username": "support-user", "role": "support"}
            }
            capability = translation_view.translation_capability(api_keys=[FAKE_KEY])
            self.assertTrue(capability["allowed"])
            self.assertTrue(capability["configured"])
            self.assertNotIn(FAKE_KEY, json.dumps(capability, ensure_ascii=False))

        with patch("core.auth.st") as streamlit:
            streamlit.session_state = {
                "current_user": {"username": "viewer-user", "role": "viewer"}
            }
            capability = translation_view.translation_capability(api_keys=[FAKE_KEY])
            self.assertFalse(capability["allowed"])


if __name__ == "__main__":
    unittest.main()
