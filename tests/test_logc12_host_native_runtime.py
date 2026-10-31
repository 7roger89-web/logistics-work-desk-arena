"""LOG-C12 host-native sales workspace — current-runtime acceptance.

History: LOG-C12 moved the sales/quotations workspace onto the host runtime and
this file asserted the legacy Streamlit intake widgets (``new_quote_save``,
``new_quote_goods``, ``new_quote_bank_pct``, ``new_quote_swift``). Those widget
keys exist nowhere in ``component/src`` any more: the workspace is now the React
``SalesQuotes`` page, and the intake form is its create-quote sheet, whose ONLY
write is the bounded ``quote_create`` event (RBAC ``sales_write`` → real
``core.quotations`` writer → audit → fresh readback).

Current contract proven here:

* the host mounts and serves the quotes workspace data to the shell;
* the create-quote intake exists with the four things the LOG-C12 form was
  actually for — a real customer picker, goods description, priced service
  lines, and a save action — each with a stable test id;
* the save path is the bounded typed event, not a Streamlit button;
* the bank-percentage / SWIFT fields the old test pinned are absent from the
  quote intake, because quoting is an ESTIMATE and never carries payment
  instructions (those live on the contract/finance surfaces).
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from views import logi_view_model as vm

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
COMPONENT_SRC = Path(__file__).resolve().parents[1] / "component" / "src"

_FIXTURE_USER = {
    "username": "fixture", "display_name": "Fixture", "role": "SALE",
    "user_id": "U-FIXTURE", "email": "", "active": True,
}


class LogC12HostNativeRuntimeTests(unittest.TestCase):
    def test_sales_workspace_mounts_and_exposes_intake_form(self) -> None:
        # 1. The host mounts and delivers the quotes workspace.
        app = AppTest.from_file(str(APP_PATH), default_timeout=120)
        app.session_state["current_user"] = dict(_FIXTURE_USER)
        with patch("core.database.load_users",
                   return_value={"fixture": dict(_FIXTURE_USER)}):
            app.run()
        self.assertFalse(
            [(e.type, str(e.value)) for e in app.exception],
            msg="mounted host raised",
        )
        self.assertIn(vm.STATE_KEY, app.session_state)
        model = app.session_state[vm.STATE_KEY]
        self.assertIn("quotes", model)
        self.assertIn("customers", model)
        self.assertTrue(model["customers"], "the intake form needs a real customer master")

        # 2. The page is mounted on its approved route.
        routes = (COMPONENT_SRC / "App.tsx").read_text(encoding="utf-8")
        self.assertIn('<Route path="/kinh-doanh-bao-gia" element={<SalesQuotes />} />', routes)

        # 3. The intake form: customer picker, goods description, priced lines,
        #    and a save action — the four capabilities of the LOG-C12 form.
        page = (COMPONENT_SRC / "pages" / "SalesQuotes.tsx").read_text(encoding="utf-8")
        for test_id in (
            'testId="quote-customer-picker"',
            'data-testid="quote-line-section"',
            'data-testid="quote-line-count"',
            'data-testid="quote-add-line"',
            'data-testid="quote-lines"',
        ):
            self.assertIn(test_id, page)
        self.assertIn('label="Mô tả hàng hóa"', page)
        self.assertIn('TẠO BÁO GIÁ', page)

        # 4. Saving is the ONE bounded typed event (never a Streamlit button).
        self.assertIn("quote_create", vm.ALL_EVENTS)
        self.assertIn('dispatch("quote_create"', page)
        for legacy_key in ("new_quote_save", "new_quote_goods",
                           "new_quote_bank_pct", "new_quote_swift"):
            self.assertNotIn(legacy_key, page)

        # Quoting is an estimate: no bank-%/SWIFT payment instruction entered
        # here (the old Streamlit form carried them for the printed quotation
        # header; that surface no longer exists in the quote intake).
        self.assertNotIn("SWIFT", page)
        self.assertNotIn("bankPct", page)


if __name__ == "__main__":
    unittest.main()
