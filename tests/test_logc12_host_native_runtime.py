from __future__ import annotations
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

#: Current entry point: ``app.py`` → ``views.web_app.main`` → the ONE
#: Logi-good component shell over ``views.logi_view_model.build_view_model()``.
#: The sales workspace is the React ``/kinh-doanh-bao-gia`` page
#: (``component/src/pages/SalesQuotes.tsx``) fed by the ``quotes`` slice.
APP_PATH = Path(__file__).resolve().parents[1] / "app.py"

#: Quote intake contract the sales workspace form binds to — exactly the fields
#: ``views.logi_c1.quote_projection`` publishes for every quote document.
INTAKE_FORM_FIELDS = frozenset({
    "id",
    "quoteNo",
    "customerId",
    "salesOwner",
    "origin",
    "destination",
    "incoterm",
    "transportMode",
    "goodsDescription",
    "expectedDeliveryDate",
    "serviceLines",
    "status",
    "allowedTransitions",
})


def _login_fixture(user):
    """Set the login fixture user into the Streamlit session and return it."""
    import streamlit as st
    st.session_state.current_user = user
    return user


class LogC12HostNativeRuntimeTests(unittest.TestCase):
    def test_sales_workspace_mounts_and_exposes_intake_form(self):
        rendered: dict = {}

        def _sales_login():
            return (_login_fixture({"username": "fixture", "display_name": "Fixture",
                                    "role": "sale"}), {"username": "fixture",
                                                       "display_name": "Fixture",
                                                       "role": "sale"})[-1]

        app = AppTest.from_file(str(APP_PATH), default_timeout=60)
        with ExitStack() as stack:
            # The approved sales workspace (\"Kinh doanh & Báo giá\" → the
            # ``/kinh-doanh-bao-gia`` component route) must mount for a SALE
            # session and the ONE render must publish the quote intake payload.
            stack.enter_context(patch("views.web_app.require_login", side_effect=_sales_login))
            stack.enter_context(patch("views.logi_shell.render",
                                      side_effect=lambda vm: rendered.update(vm)))
            app.run()
            self.assertFalse(app.exception)

        self.assertEqual(rendered["user"]["role"], "SALE")
        # Customer picker of the intake form.
        self.assertTrue(rendered["customers"], "sales intake needs the customer reader")
        self.assertTrue(
            all({"id", "name"} <= set(customer) for customer in rendered["customers"]),
        )
        quotes = rendered["quotes"]
        self.assertTrue(quotes, "fresh quote reader must populate the sales workspace")
        for quote in quotes:
            self.assertTrue(
                INTAKE_FORM_FIELDS <= set(quote),
                f"quote {quote.get('id')!r} is missing intake-form fields: "
                f"{sorted(INTAKE_FORM_FIELDS - set(quote))}",
            )
            self.assertTrue(quote["source"].startswith("core.database.load_quotes"))


if __name__ == "__main__":
    unittest.main()
