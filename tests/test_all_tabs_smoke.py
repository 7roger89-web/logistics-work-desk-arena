# -*- coding: utf-8 -*-
"""Comprehensive workspace smoke test for the live shell entrypoint.

One mounted app run, one view-model payload: every workspace slice the shell
mounts must be present and the shipment row behind the operational routes must
be complete — and the run must raise no Streamlit exception.

(The Streamlit sidebar SPA and its ``refresh_core_data`` fixture were retired by
LOGI-GOOD-V6 Phase A; the fixture helpers below are still imported by other
regression tests, so they stay.)
"""

import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import tests.test_dashboard_financial_write_oracle as oracle_mod

APP_PATH = oracle_mod.APP_PATH if hasattr(oracle_mod, "APP_PATH") else \
    oracle_mod.__file__.replace("test_dashboard_financial_write_oracle.py", "web_app.py")
# Fallback: try the actual web_app.py path
import os
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_web_app_candidates = [
    os.path.join(_repo_root, "web_app.py"),
    os.path.join(_repo_root, "views", "web_app.py"),
    os.path.join(_repo_root, "views", "web_app.py"),
]
for _c in _web_app_candidates:
    if os.path.exists(_c):
        APP_PATH = _c
        break


def _shipments():
    """Minimal fixture: one shipment with master + service data."""
    return {
        "S-001": {
            "id": "S-001",
            "shipment_id": "S-001",
            "client": "fixture",
            "customer": {"customer_code": "CUS-1", "customer_name": "Fixture Customer",
                         "phone": "0123456789", "email": "test@example.com",
                         "delivery_address": "Hanoi"},
            "created_at": "2026-08-01",
            "status": "pending",
            "data": {
                "0.0": {
                    "created_at": "2026-08-01",
                    "order_date": "2026-08-01",
                    "executor": "Fixture",
                    "customer_code": "CUS-1",
                    "customer_name": "Fixture Customer",
                    "phone": "0123456789",
                    "email": "test@example.com",
                    "delivery_address": "Hanoi",
                    "contact_person": "Fixture",
                    "contact_phone": "0123456789",
                    "province": "Hanoi",
                    "district": "Ba Dinh",
                    "customer_source": "web",
                },
                "3.4": {
                    "details": [
                        {
                            "product_code": "P-1",
                            "product_name": "Fixture Product",
                            "description": "",
                            "unit": "pcs",
                            "product_group": "general",
                            "quantity": 1,
                            "cost": 100000,
                            "price": 150000,
                            "discount_pct": 0,
                            "discount_amount": 0,
                            "vat_pct": 8,
                            "total": 150000,
                            "product_profit": 50000,
                            "revenue": 150000,
                            "discount_line": 0,
                            "revenue_after_discount": 150000,
                            "shipping_fee": 0,
                            "install_fee": 0,
                            "revenue_before_tax": 138888.89,
                            "vat_amount": 11111.11,
                            "net_revenue": 150000,
                            "paid": 0,
                            "debt": 150000,
                            "profit": 50000,
                        }
                    ],
                    "commission": "0",
                    "payments": [],
                    "currency": "VND",
                    "out": 150000,
                    "in": 100000,
                    "paid": 0,
                    "debt": 150000,
                    "profit": 50000,
                },
            },
            "is_archived": False,
            "is_deleted": False,
            "version": 1,
        },
    }


def _customers():
    return {
        "CUS-1": {
            "id": "CUS-1",
            "customer_code": "CUS-1",
            "customer_name": "Fixture Customer",
            "phone": "0123456789",
            "email": "test@example.com",
        },
    }


def _login_fixture(overrides=None):
    base = {"username": "fixture", "display_name": "Fixture", "role": "admin",
            "permissions": ["dashboard", "customers", "sales", "contracts",
                            "receivables", "reports", "tariff", "tracking",
                            "knowledge", "admin", "shipment_create", "finance_write"]}
    if overrides:
        base.update(overrides)
    return base


def _assert_no_exceptions(test_case, app):
    if app.exception:
        raise AssertionError(f"Streamlit exception: {app.exception}")


class AllTabsSmokeTest(unittest.TestCase):
    """Every workspace the shell can open is delivered without an exception.

    The Streamlit sidebar SPA this test was written for was retired by
    LOGI-GOOD-V6 Phase A: ``app.py`` now mounts ONE Components-v2 shell whose
    routes live in the React bundle, so "click every sidebar tab" no longer
    exists.  The invariant it protected — no workspace raises, and every route
    has real data behind it — is asserted here against the live entrypoint and
    the ONE payload the shell receives.
    """

    #: Every workspace slice the shell mounts. Losing one is a broken tab.
    WORKSPACE_SLICES = (
        "home", "tasks", "shipments", "quotes", "contracts", "customers",
        "receivables", "payables", "reconciliation", "tariff", "handbook",
        "userAccess", "costIntelligence", "inbox", "notifications",
        "translation", "partnerContext", "workModules",
    )

    def test_all_routes_render(self):
        from streamlit.components.v2.bidi_component.state import ComponentResult
        from views import logi_sandbox, logi_shell

        logi_sandbox.reset_backend()
        self.assertEqual(logi_sandbox.ensure_backend(), logi_sandbox.SANDBOX_TRANSPORT)

        captured: dict = {}

        def fake_renderer(**kwargs):
            captured.update(kwargs)
            return ComponentResult({}, {})

        app = AppTest.from_file(str(APP_PATH), default_timeout=120)
        app.session_state["current_user"] = {"username": "admin", "role": "admin"}
        with patch("views.logi_shell._renderer", return_value=fake_renderer):
            app.run()
            _assert_no_exceptions(self, app)

        vm = captured.get("data")
        self.assertIsInstance(vm, dict, "the shell must receive the view-model")
        missing = [key for key in self.WORKSPACE_SLICES if key not in vm]
        self.assertEqual(missing, [], f"workspace slices missing from the payload: {missing}")
        # A shipment row backs every operational route; it must be complete.
        self.assertTrue(vm["shipments"], "the worklist must carry real rows")
        row = vm["shipments"][0]
        for key in ("id", "nextRoute", "status", "journey", "executionProfile"):
            self.assertIn(key, row)
        # Logged-in, i.e. NOT the login/bootstrap screen.
        self.assertNotIn("login_username", app.session_state)
        self.assertEqual(logi_shell.COMPONENT_KEY, captured.get("key"))


if __name__ == "__main__":
    unittest.main()
