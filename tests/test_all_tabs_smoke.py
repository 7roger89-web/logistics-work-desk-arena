# -*- coding: utf-8 -*-
"""LG05: Comprehensive tab-by-tab smoke test.

Navigates through ALL routes in the sidebar and checks that each renders
without Streamlit exceptions. Uses fixture data with proper patches.
"""

import re
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import tests.test_dashboard_financial_write_oracle as oracle_mod

APP_PATH = oracle_mod.APP_PATH if hasattr(oracle_mod, "APP_PATH") else \
    oracle_mod.__file__.replace("test_dashboard_financial_write_oracle.py", "web_app.py")
# Fallback: try the actual web_app.py path
import os
from pathlib import Path
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = Path(_repo_root)
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
    """Navigate every sidebar route and verify no Streamlit exception."""

    def test_all_routes_render(self):
        """The CURRENT host boots and every navigation destination resolves.

        LOGI-GOOD-V6 replaced the legacy Streamlit sidebar/dashboard with ONE
        Components-v2 root whose pages live in the React shell (``component/
        src``). The old route loop (click every sidebar button) can no longer
        mean anything: there IS no Streamlit sidebar. The equivalent current
        guarantee is asserted here, at the layers that own it today:

        1. the host script boots with an authenticated session and raises
           nothing (the same "no Streamlit exception" invariant);
        2. the view-model delivered to the component carries the worklist data
           every page reads;
        3. the legacy Streamlit navigation surface is NOT mounted (a silent
           resurrection of the removed sidebar fails this test);
        4. every destination in the shell's NAV table has a declared route, so a
           nav item can never point at a dead page.
        """
        from views import logi_view_model as vm

        fixture_user = _login_fixture({
            "username": "fixture", "user_id": "U-FIXTURE", "email": "",
            "active": True,
        })
        app = AppTest.from_file(str(APP_PATH), default_timeout=120)
        app.session_state["current_user"] = dict(fixture_user)
        with patch("core.database.load_users",
                   return_value={"fixture": dict(fixture_user)}):
            app.run()
        _assert_no_exceptions(self, app)

        # 2. The ONE payload the shell renders from.
        self.assertIn(vm.STATE_KEY, app.session_state)
        model = app.session_state[vm.STATE_KEY]
        self.assertEqual(
            set(model),
            {"version", "shipments", "tasks", "contracts", "customers",
             "quotes", "notifications"},
            "the delivered payload is the Phase A session shape",
        )
        self.assertTrue(model["version"], "a view-model version must be built")
        self.assertIsInstance(model["shipments"], dict)
        self.assertTrue(model["shipments"], "the sandbox worklist must not be empty")

        # Every action link the payload hands the shell is an in-app route that
        # the shell declares — the data-level equivalent of "the page exists".
        for row in model["shipments"].values():
            # ``route`` is the PHYSICAL lane ("Bằng Tường → Bắc Ninh"); the
            # action links are ``nextRoute`` and the journey primary action.
            links = [row.get("nextRoute") or ""]
            links.append(((row.get("journey") or {}).get("primaryAction") or {}).get("route") or "")
            for value in links:
                if value:
                    self.assertTrue(
                        value.startswith(f"/lo-hang/{row['id']}"), (row.get("id"), value)
                    )
        for note in model["notifications"]:
            self.assertTrue((note.get("route") or "/").startswith("/"), note)

        # 3. No legacy Streamlit page switcher is mounted any more.
        self.assertEqual([b.label for b in app.sidebar.button], [])
        self.assertEqual([s.key for s in app.sidebar.selectbox], [])

        # 4. Every shell NAV destination resolves to a declared route.
        routes_source = (_REPO_ROOT / "component" / "src" / "App.tsx").read_text(encoding="utf-8")
        declared = {chunk.split('"')[0] for chunk in routes_source.split('<Route path="')[1:]}
        self.assertIn("/lo-hang/:id", declared)
        nav_source = (_REPO_ROOT / "component" / "src" / "lib" / "data.ts").read_text(encoding="utf-8")
        nav_block = nav_source[nav_source.index("export const NAV"):]
        # The type annotation above the table also contains ``}[];`` — slice at
        # the array's own closing ``];`` at column 0.
        nav_block = nav_block[:nav_block.index("\n];")]
        destinations = [chunk.split('"')[0] for chunk in nav_block.split('to: "')[1:]]
        self.assertGreaterEqual(len(destinations), 10, destinations)
        dead = sorted(set(destinations) - declared)
        self.assertEqual(dead, [], f"NAV destinations without a declared route: {dead}")

if __name__ == "__main__":
    unittest.main()
