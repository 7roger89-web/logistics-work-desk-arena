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
    def test_sales_workspace_mounts_and_exposes_intake_form(self):
        app = AppTest.from_file(str(APP_PATH), default_timeout=60)
        app.session_state.active_page = "Kinh doanh & Báo giá"
        app.session_state.db_customers = {
            "CUS-FIXTURE": {"id": "CUS-FIXTURE", "name": "Fixture Customer"},
        }
        app.session_state.db_quotes = {}
        app.session_state.db_rate_cards = {}
        app.session_state.db_shipments = {}
        app.session_state.data_loaded = True
        # Approved Vietnamese navigation label: "Kinh doanh & Báo giá" — the
        # workspace must still mount under it. Patches stay alive for ALL runs
        # (click triggers a rerun that must also be covered).
        with ExitStack() as stack:
            stack.enter_context(patch("views.web_app.require_login", side_effect=lambda: (_login_fixture({"display_name": "Fixture", "role": "SALE"}), {"display_name": "Fixture", "role": "SALE"})[-1]))
            stack.enter_context(patch("views.web_app.has_permission", return_value=True))
            stack.enter_context(patch("core.database.init_connection", return_value=None))
            stack.enter_context(patch("views.web_app.refresh_core_data", return_value=None))
            stack.enter_context(patch("views.quotations.load_quotes", return_value={}))
            stack.enter_context(patch("views.quotations.load_customers", return_value=app.session_state.db_customers))
            app.run()
            self.assertFalse(app.exception)
            sales_nav = next((item for item in app.button if "sale" in str(item.key).lower() or "b_o_gi" in str(item.key).lower()), None)
            self.assertIsNotNone(sales_nav)
            sales_nav.click()
            app.run()
            self.assertFalse(app.exception)
        self.assertIn("new_quote_save", {item.key for item in app.button})
        self.assertIn("new_quote_goods", {item.key for item in app.text_input})
        self.assertIn("new_quote_bank_pct", {item.key for item in app.number_input})
        self.assertIn("new_quote_swift", {item.key for item in app.number_input})
if __name__ == "__main__":
    unittest.main()
