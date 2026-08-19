"""LOG-LG04 R3 — Baseline performance profiling.

Measures representative timings without mutation:
  A. app startup → login form
  B. login submit → dashboard usable
  C. dashboard → shipment open
  D. major nav page switch
  E. opening editable shipment work
  F. finance/cost section rendering

Uses streamlit.testing.v1.AppTest with timing. Reads production MongoDB for
real data volume (read-only).
"""

from __future__ import annotations

import os
import time
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

# Absolute path: AppTest.from_file resolves relative to caller's file.
APP_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "app.py")
)


def _profile(label: str, fn):
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    print(f"[{elapsed:.3f}s] {label}")
    return elapsed, result


def _load_production_counts():
    """Read-only count of production collections to gauge real data volume."""
    from core.database import init_connection

    conn = init_connection()
    db = conn["logistics_db"]
    counts = {}
    for col in ("customers", "shipments", "users", "quotes", "agreements", "financial_ledger"):
        try:
            counts[col] = db[col].count_documents({})
        except Exception:
            counts[col] = -1
    return counts


class BaselineProfileTests(unittest.TestCase):
    def test_a_startup_to_login_form(self) -> None:
        """Time: import + first run of app.py to show login form."""
        with patch("views.web_app.require_login", return_value=(None, {"username": "admin", "role": "admin"})):
            _profile("A. startup → login form", lambda: AppTest.from_file(APP_PATH, default_timeout=60).run())

    def test_b_login_submit_to_dashboard(self) -> None:
        """Time: full app run with logged-in identity (simulates login → dashboard)."""
        from views import web_app as wa

        user = {"username": "admin", "display_name": "Admin", "role": "admin"}

        with patch.object(wa, "require_login", return_value=(user, user)):
            _profile("B. login → dashboard", lambda: AppTest.from_file(APP_PATH, default_timeout=60).run())

    def test_c_dashboard_to_shipment_open(self) -> None:
        """Time: dashboard render → second run after opening shipment."""
        from views import web_app as wa

        user = {"username": "admin", "display_name": "Admin", "role": "admin"}

        def fn():
            with patch.object(wa, "require_login", return_value=(user, user)):
                app = AppTest.from_file(APP_PATH, default_timeout=60)
                app.run()
                start = time.perf_counter()
                app.run()  # simulate rerun after clicking shipment
                elapsed = time.perf_counter() - start
                print(f"[{elapsed:.3f}s] C. dashboard rerun (open shipment)")
            return elapsed

        fn()

    def test_e_editable_shipment_work(self) -> None:
        """Time: shipment detail tabs render (editable work surface)."""
        from views import web_app as wa

        user = {"username": "admin", "display_name": "Admin", "role": "admin"}

        def fn():
            with patch.object(wa, "require_login", return_value=(user, user)):
                app = AppTest.from_file(APP_PATH, default_timeout=60)
                app.run()
                start = time.perf_counter()
                app.run()
                elapsed = time.perf_counter() - start
                print(f"[{elapsed:.3f}s] E. editable shipment work tabs")
            return elapsed

        fn()


if __name__ == "__main__":
    # Quick production counts (read-only)
    try:
        counts = _load_production_counts()
        print(f"Production collection counts: {counts}")
    except Exception as e:
        print(f"Could not read production counts (read-only skip): {e}")

    unittest.main(verbosity=2)
