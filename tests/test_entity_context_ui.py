from __future__ import annotations
import streamlit as st
"""Mounted Streamlit behavior checks for LOG-C09 context navigation."""
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
def _shipments() -> dict[str, dict]:
    return {
        "S-001": {
            "id": "S-001",
            "shipment_id": "S-001",
            "customer": "Acme",
            "customer_id": "CUS-1",
            "status": "pending",
            "customer_required_date": "2026-08-30",
            "factories": [{
                "factory_name": "Factory North",
                "lot_id": "LOT-1",
                "product": "Widgets",
                "quantity": 12,
                "factory_ready_date": "2026-08-20",
                "required_information_complete": True,
            }],
            "partner": {"name": "Blue Agent", "role": "Pickup agent"},
            "data": {
                "0.0": {"created_at": "2026-08-01", "mode": "Sea"},
                "1.2": {"pol": "Yantian", "pod": "Cat Lai"},
                "2.4": {},
                "2.6": {},
                "2.7": {},
                "3.4": {"details": [], "payments": []},
            },
        }
    }

def _login_fixture(user):
    """Set the login fixture user into the Streamlit session and return it."""
    import streamlit as st
    st.session_state.current_user = user
    return user

class EntityContextMountedTests(unittest.TestCase):
    def _app(self, page: str, request: dict[str, str] | None = None) -> AppTest:
        app = AppTest.from_file(str(APP_PATH), default_timeout=60)
        app.session_state.active_page = page
        app.session_state.db_shipments = _shipments()
        app.session_state.db_customers = {"CUS-1": {"id": "CUS-1", "name": "Acme", "contact_person": "Lan"}}
        app.session_state.entity_context_request = request or {}
        return app
    def test_entity_workspace_opens_shipment_360(self) -> None:
        app = self._app("Ngữ Cảnh Đối Tác", {"entity_type": "customer", "entity_key": "CUS-1"})
        # Keep patch contexts alive for the AppTest run.
        with ExitStack() as stack:
            stack.enter_context(patch("views.web_app.require_login", side_effect=lambda: (_login_fixture({"username": "fixture", "display_name": "Fixture", "role": "admin"}), {"username": "fixture", "display_name": "Fixture", "role": "admin"})[-1]))
            stack.enter_context(patch("core.database.init_connection", return_value=None))
            stack.enter_context(patch("views.web_app.refresh_core_data", return_value=None))
            stack.enter_context(patch("views.dashboard.cached_load_data", return_value=_shipments()))
            stack.enter_context(patch("views.dashboard.load_tasks", return_value=[]))
            stack.enter_context(patch("views.shipment.load_proxy_payments", return_value={}))
            stack.enter_context(patch("views.shipment.load_entrustments", return_value={}))
            stack.enter_context(patch("views.shipment.load_audit_logs", return_value=[]))
            app.run()
            self.assertFalse(app.exception)
            self.assertTrue(any("Khách hàng 360" in item.value for item in app.subheader))
            open_button = next(item for item in app.button if item.key.startswith("customer_active_open_"))
            open_button.click()
            app.run()
            self.assertFalse(app.exception)
            self.assertIn("btn_close_top", {item.key for item in app.button})
    def test_shipment_360_links_to_customer_factory_partner_and_returns(self) -> None:
        app = self._app("Tổng Quan Công Việc")
        with ExitStack() as stack:
            stack.enter_context(patch("views.web_app.require_login", side_effect=lambda: (_login_fixture({"username": "fixture", "display_name": "Fixture", "role": "admin"}), {"username": "fixture", "display_name": "Fixture", "role": "admin"})[-1]))
            stack.enter_context(patch("core.database.init_connection", return_value=None))
            stack.enter_context(patch("views.web_app.refresh_core_data", return_value=None))
            stack.enter_context(patch("views.dashboard.cached_load_data", return_value=_shipments()))
            stack.enter_context(patch("views.dashboard.load_tasks", return_value=[]))
            stack.enter_context(patch("views.shipment.load_proxy_payments", return_value={}))
            stack.enter_context(patch("views.shipment.load_entrustments", return_value={}))
            stack.enter_context(patch("views.shipment.load_audit_logs", return_value=[]))
            app.run()
            open_button = next(item for item in app.button if item.key == "dashboard_open_360_S-001")
            open_button.click()
            app.run()
            self.assertFalse(app.exception)
            keys = {item.key for item in app.button}
            self.assertTrue({
                "shipment_customer_context_S-001",
                "shipment_factory_context_S-001",
                "shipment_partner_context_S-001",
            }.issubset(keys))
            app.button(key="shipment_customer_context_S-001").click()
            app.run()
            self.assertFalse(app.exception)
            self.assertTrue(any("Khách hàng 360" in item.value for item in app.subheader))
            app.button(key="entity_back_shipment").click()
            app.run()
            self.assertFalse(app.exception)
            self.assertIn("btn_close_top", {item.key for item in app.button})
if __name__ == "__main__":
    unittest.main()
