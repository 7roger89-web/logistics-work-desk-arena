from __future__ import annotations
import streamlit as st
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
APP_PATH = Path(__file__).resolve().parents[1] / "app.py"

def _login_fixture(user):
    """Set the login fixture user into the Streamlit session and return it."""
    import streamlit as st
    st.session_state.current_user = user
    return user

class LogC12HostNativeRuntimeTests(unittest.TestCase):
    """The Sales workspace mounts in the live shell and exposes the quote intake.

    LOGI-GOOD-V6 Phase A replaced the Streamlit "Kinh doanh & Báo giá" page with
    the React ``SalesQuotes`` route inside the ONE shell, so this test now
    proves the SAME contract on the live path: the approved navigation label is
    gone from Streamlit only because the workspace moved — the quote slice still
    arrives in the shell payload, the intake form still exists in the shipped
    component source, and mounting the app raises nothing.
    """

    INTAKE_MARKERS = (
        "Tạo báo giá mới",          # create panel title
        "Khách hàng",               # customer picker
        "dispatch(\"quote_create\"",  # the ONE create event
    )

    def test_sales_workspace_mounts_and_exposes_intake_form(self):
        from pathlib import Path

        from streamlit.components.v2.bidi_component.state import ComponentResult
        from views import logi_sandbox

        logi_sandbox.reset_backend()
        self.assertEqual(logi_sandbox.ensure_backend(), logi_sandbox.SANDBOX_TRANSPORT)

        captured: dict = {}

        def fake_renderer(**kwargs):
            captured.update(kwargs)
            return ComponentResult({}, {})

        app = AppTest.from_file(str(APP_PATH), default_timeout=60)
        app.session_state["current_user"] = {"username": "admin", "role": "admin"}
        with patch("views.logi_shell._renderer", return_value=fake_renderer):
            app.run()
        self.assertFalse(app.exception)

        vm = captured.get("data") or {}
        self.assertIn("quotes", vm)
        self.assertIn("costIntelligence", vm)
        self.assertIsInstance(vm["quotes"], list)
        self.assertTrue(vm["quotes"], "the quote workspace must carry real rows")
        for key in ("id", "quoteNo", "customer", "status", "allowedTransitions"):
            self.assertIn(key, vm["quotes"][0])

        source = (
            Path(__file__).resolve().parents[1] / "component" / "src" / "pages" / "SalesQuotes.tsx"
        ).read_text(encoding="utf-8")
        for marker in self.INTAKE_MARKERS:
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
