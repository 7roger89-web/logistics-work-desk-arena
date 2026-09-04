"""Focused regression coverage for Support Finance service-row entry."""

from __future__ import annotations

import ast
import json
from contextlib import ExitStack
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def _shipment_fixture() -> dict:
    return {
        "id": "S-001",
        "shipment_id": "S-001",
        "client": "TEST CUSTOMER",
        "customer": "TEST CUSTOMER",
        "customer_id": "C-TEST",
        "status": "wait",
        "version": 0,
        "is_deleted": False,
        "is_archived": False,
        "data": {
            "0.0": {
                "created_at": "2026-09-04",
                "mode": "Sea",
                "incoterm": "EXW",
                "st": "wait",
            },
            "1.2": {},
            "2.4": {},
            "2.6": {},
            "2.7": {},
            "3.4": {
                "details": [],
                "commission": {"list": [], "total": 0},
                "payments": [],
            },
            "entrustment": {"active": False},
        },
    }


def _dialog_decorator_names() -> dict[str, int]:
    tree = ast.parse(
        (ROOT / "views" / "dashboard.py").read_text(encoding="utf-8"),
        filename="views/dashboard.py",
    )
    counts: dict[str, int] = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        counts[node.name] = sum(
            1
            for decorator in node.decorator_list
            if isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "dialog"
        )
    return counts


class SupportFinanceServiceRegressionTests(TestCase):
    def test_quick_task_dialog_decorator_is_not_on_user_id_helper(self) -> None:
        decorators = _dialog_decorator_names()
        self.assertEqual(decorators.get("_get_current_user_id"), 0)
        self.assertEqual(decorators.get("quick_assign_task_dialog"), 1)

    def test_support_add_service_row_is_enabled_and_retained_after_rerun(self) -> None:
        shipment = _shipment_fixture()
        page_src = f"""
import json
import streamlit as st
from views.shipment import ui_shipment_detail_tabs

SHIPMENT = json.loads(r'''{json.dumps(shipment)}''')
st.session_state.current_user = {{
    "user_id": "support-user-01",
    "username": "support.test",
    "display_name": "Support Test",
    "role": "support",
}}
st.session_state.db_customers = {{"C-TEST": {{"name": "TEST CUSTOMER"}}}}
st.session_state.setdefault("db_shipments", {{"S-001": SHIPMENT}})
st.session_state.data_loaded = True
st.session_state.active_shipment_section = "finance"
ui_shipment_detail_tabs("S-001", st.session_state.db_shipments["S-001"])
"""
        with ExitStack() as stack:
            stack.enter_context(patch("views.shipment.load_proxy_payments", return_value={}))
            stack.enter_context(patch("views.shipment.load_entrustments", return_value={}))
            stack.enter_context(patch("views.shipment.load_audit_logs", return_value=[]))
            app = AppTest.from_string(page_src, default_timeout=60)
            app.run()
            self.assertFalse(list(app.exception), msg=str(app.exception))

            add_service = next(button for button in app.button if button.label == "➕ Thêm Dịch vụ")
            self.assertFalse(add_service.disabled)

            add_service.click()
            app.run()
            self.assertFalse(list(app.exception), msg=str(app.exception))
            self.assertTrue(any(element.key == "dt_S-001_s_0" for element in app.selectbox))
            self.assertEqual(
                len(app.session_state.db_shipments["S-001"]["data"]["3.4"]["details"]),
                1,
            )
