# -*- coding: utf-8 -*-
"""V4 Logi-good donor shell smoke tests.

Renders the donor view layer (views/lg_app.py) across every registered route
plus the Shipment detail 5-tab surface and asserts no Streamlit exceptions.
A DEV-only in-memory stand-in is seeded automatically when no live Mongo is
reachable, so the donor surfaces render real projections over sample records.
"""

import os
import unittest

from streamlit.testing.v1 import AppTest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_PATH = os.path.join(_REPO, "views", "lg_app.py")

ROUTES = [
    "home", "tasks", "shipments", "new_shipment", "tracking",
    "customers", "context", "quote", "agreement", "contracts",
    "contract_detail", "new_contract", "receive", "reconcile",
    "partner_debt", "ceo", "tariff", "notebook", "translate", "admin",
]
DETAIL_TABS = ["lay-hang", "nhap", "tai-chinh", "chung-tu", "lich-su"]


def _new_at(**state):
    at = AppTest.from_file(APP_PATH, default_timeout=40)
    for key, value in state.items():
        at.session_state[key] = value
    at.run()
    return at


class DonorShellRouteTests(unittest.TestCase):
    def test_home_renders_no_exceptions_and_has_sidebar_nav(self):
        at = _new_at(lg_page="home")
        self.assertEqual([], [e.message for e in at.exception])
        nav_keys = [b.key for b in at.button if (b.key or "").startswith("nav_")]
        self.assertGreaterEqual(len(nav_keys), 18)

    def test_all_routes_render_without_exception(self):
        for route in ROUTES:
            with self.subTest(route=route):
                at = _new_at(lg_page=route)
                self.assertEqual(
                    [], [e.message for e in at.exception], msg=f"route={route}"
                )


class DonorDetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shipment_ids = _discover_shipment_ids()

    def test_shipment_detail_all_tabs_render(self):
        if not self.shipment_ids:
            self.skipTest("no shipment available to open")
        sid = self.shipment_ids[0]
        for tab in DETAIL_TABS:
            with self.subTest(tab=tab):
                at = _new_at(lg_page="shipment_detail", lg_shipment=sid, lg_tab=tab)
                self.assertEqual(
                    [], [e.message for e in at.exception],
                    msg=f"detail sid={sid} tab={tab}",
                )


def _discover_shipment_ids():
    """Seed (if needed) and return real shipment ids via the DEV stand-in."""
    at = _new_at(lg_page="shipments")
    import core.database as cdb

    return list((cdb.load_data() or {}).keys())


if __name__ == "__main__":
    unittest.main()
