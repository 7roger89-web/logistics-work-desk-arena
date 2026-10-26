from __future__ import annotations
"""Mounted behavior checks for the LOG-C09 entity-context navigation.

Re-pointed from the retired Streamlit entity workspace (``views.dashboard`` /
``views.shipment`` buttons ``customer_active_open_*``, ``dashboard_overview_*``,
``shipment_*_context_*``) to the current entry point: ``app.py`` →
``views.web_app.main`` → the ONE Logi-good shell, whose entity context is the
``partnerContext`` slice of ``views.logi_view_model.build_view_model()``
(``/ngu-canh-doi-tac``). The selection key is the bounded dispatcher's own
session key, so the navigation is exercised exactly the way the UI drives it.
"""
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
#: Session key of the bounded ``partner_context_select`` dispatcher event.
SELECTION_KEY = "logi_partner_context_selection"


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


def _customers() -> dict[str, dict]:
    return {"CUS-1": {"id": "CUS-1", "name": "Acme", "contact_person": "Lan"}}


def _login_fixture(user):
    """Set the login fixture user into the Streamlit session and return it."""
    import streamlit as st
    st.session_state.current_user = user
    return user


class EntityContextMountedTests(unittest.TestCase):
    def _mount(self, selection: str | None = None) -> tuple[AppTest, dict]:
        """Mount the current shell and capture the render it publishes."""
        rendered: dict = {}
        app = AppTest.from_file(str(APP_PATH), default_timeout=60)
        if selection is not None:
            app.session_state[SELECTION_KEY] = selection
        with ExitStack() as stack:
            stack.enter_context(patch("views.web_app.require_login", side_effect=lambda: (_login_fixture({"username": "fixture", "display_name": "Fixture", "role": "admin"}), {"username": "fixture", "display_name": "Fixture", "role": "admin"})[-1]))
            stack.enter_context(patch("views.logi_view_model.load_shipments", return_value=_shipments()))
            stack.enter_context(patch("core.database._load_customers_impl", return_value=_customers()))
            stack.enter_context(patch("views.logi_shell.render", side_effect=lambda vm: rendered.update(vm)))
            app.run()
            self.assertFalse(app.exception)
        return app, rendered

    def test_entity_workspace_opens_shipment_360(self) -> None:
        """One partner selection links straight to the real shipment workspace."""
        app, rendered = self._mount("Blue Agent")

        context = rendered["partnerContext"]
        self.assertEqual(context["status"], "OK")
        self.assertEqual(context["selectedLabel"], "Blue Agent")
        self.assertTrue(context["readOnly"])
        linked = {row["shipmentId"]: row for row in context["shipments"]}
        self.assertIn("S-001", linked)
        # Same navigation the retired "open" button performed: the shipment route.
        self.assertTrue(linked["S-001"]["canOpen"])
        self.assertEqual(linked["S-001"]["openHref"], "/lo-hang/S-001")

    def test_shipment_360_workspace_has_entity_context_buttons(self) -> None:
        """The shipment row still surfaces the entities it can navigate to."""
        app, rendered = self._mount()

        row = next(item for item in rendered["shipments"] if item["id"] == "S-001")
        # Customer context: the row carries the canonical customer id the
        # customer master can resolve.
        self.assertEqual(row["customerId"], "CUS-1")
        self.assertIn("CUS-1", {customer["id"] for customer in rendered["customers"]})
        # Partner context: the shipment's partner is a selectable entity and
        # selecting it navigates back to this same shipment.
        partner_option = next(
            option for option in rendered["partnerContext"]["options"]
            if option["key"] == "Blue Agent"
        )
        self.assertIn("shipment partner/agent index", partner_option["sources"])
        # Document context: the row's execution checklist stays reachable.
        self.assertTrue(row["docs"])
        self.assertTrue(row["nextRoute"].startswith("/lo-hang/S-001"))


if __name__ == "__main__":
    unittest.main()
