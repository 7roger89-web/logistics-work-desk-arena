# -*- coding: utf-8 -*-
"""LG05: Comprehensive tab-by-tab smoke test.

Navigates through ALL routes in the sidebar and checks that each renders
without Streamlit exceptions. Uses fixture data with proper patches.
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
    """Navigate every sidebar route and verify no Streamlit exception."""

    def test_all_routes_render(self):
        shipments = _shipments()
        customers = _customers()
        with patch("views.web_app.refresh_core_data", return_value=None):
            with patch("views.web_app.require_login",
                         return_value=_login_fixture()):
                with patch("views.dashboard.load_data",
                           return_value=shipments):
                    with patch("views.dashboard.load_tasks", return_value=[]):
                        with patch("views.customers.load_customers",
                                   return_value=customers):
                            app = AppTest.from_file(str(APP_PATH),
                                                    default_timeout=120)
                            app.run()
                            _assert_no_exceptions(self, app)

                            # Navigate via sidebar buttons
                            sidebar_buttons = [
                                b for b in app.sidebar.button
                                if hasattr(b, "label")
                            ]
                            sidebar_selectboxes = app.sidebar.selectbox

                            # Collect route labels from buttons
                            route_labels = []
                            for b in sidebar_buttons:
                                label = getattr(b, "label", "")
                                if label and label not in route_labels:
                                    route_labels.append(label)

                            # Also check selectboxes for page selection
                            for sb in sidebar_selectboxes:
                                opts = getattr(sb, "options", [])
                                for opt in opts:
                                    if opt not in route_labels:
                                        route_labels.append(opt)

                            # Test each route by clicking/selecting
                            for label in route_labels:
                                # Try clicking a button with this label
                                found = False
                                for b in app.sidebar.button:
                                    if getattr(b, "label", "") == label:
                                        b.click()
                                        found = True
                                        break
                                if not found:
                                    # Try selecting from a selectbox
                                    for sb in app.sidebar.selectbox:
                                        opts = getattr(sb, "options", [])
                                        if label in opts:
                                            sb.set_value(label)
                                            found = True
                                            break
                                if found:
                                    app.run()
                                    _assert_no_exceptions(self, app)
                                    # Close any open shipment detail
                                    if "btn_close_top" in {e.key for e in app.button}:
                                        for b in app.button:
                                            if b.key == "btn_close_top":
                                                b.click()
                                                break
                                        app.run()
                                        _assert_no_exceptions(self, app)


if __name__ == "__main__":
    unittest.main()
