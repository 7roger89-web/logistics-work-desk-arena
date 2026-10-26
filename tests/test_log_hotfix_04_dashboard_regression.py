"""Focused mounted regression coverage for LOG-HOTFIX-04.

These tests exercise the real lazy Dashboard row path and the real Shipment
workspace function with in-memory fixtures. They do not connect to MongoDB or
submit any business write.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import date
from inspect import signature
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from core.readiness import CRITICAL, derive_next_action, get_all_readiness
from core.shipment_360 import UNKNOWN
from core.shipment_dashboard import (
    build_shipment_dashboard_view,
    build_shipment_summary,
)
from tests.test_all_tabs_smoke import _customers, _login_fixture, _shipments

#: Current entry point: ``app.py`` → ``views.web_app.main`` → the Logi-good
#: single-component shell (``views.logi_shell.render`` over the view-model).
APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def _assert_no_streamlit_exceptions(app: AppTest) -> None:
    assert not app.exception, str(app.exception)


def test_summary_alias_contract_is_exact_and_read_only() -> None:
    shipment = _shipments()["S-001"]
    before = deepcopy(shipment)

    params = signature(build_shipment_summary).parameters
    assert list(params) == ["shipment", "today", "financial_view"]
    actual = build_shipment_summary(shipment, today=date(2026, 8, 14))
    expected = build_shipment_dashboard_view(shipment, today=date(2026, 8, 14))

    assert actual == expected
    assert shipment == before
    assert actual["read_only_financial"] is True
    assert actual["financial_projection"].get("read_only") is True


def test_dashboard_lazy_workdesk_rows_call_summary_alias_and_render() -> None:
    """The mounted worklist builds every row through the dashboard alias.

    Re-pointed from the retired Streamlit dashboard (``views.dashboard``) to the
    current entry point: the rows the component shell renders are the
    ``views.logi_view_model`` payload, and the per-row summary alias that feeds
    them is ``core.shipment_dashboard.build_shipment_dashboard_view``.
    """
    shipments = _shipments()
    customers = _customers()
    rendered: dict = {}

    with patch("views.logi_view_model.load_shipments", return_value=shipments):
        with patch("core.database._load_customers_impl", return_value=customers):
            with patch("views.web_app.require_login", return_value=_login_fixture()):
                with patch("views.logi_shell.render", side_effect=lambda vm: rendered.update(vm)):
                    with patch(
                        "core.shipment_dashboard.build_shipment_dashboard_view",
                        wraps=build_shipment_dashboard_view,
                    ) as summary_alias:
                        app = AppTest.from_file(str(APP_PATH), default_timeout=120)
                        app.run()

    _assert_no_streamlit_exceptions(app)
    assert summary_alias.call_count >= 1
    rows = {row["id"]: row for row in rendered["shipments"]}
    assert "S-001" in rows
    assert rows["S-001"]["nextAction"]
    assert rows["S-001"]["nextRoute"].startswith("/lo-hang/S-001")
    assert rendered["home"]["focus"]["id"] == "S-001"
    assert rendered["home"]["focus"]["nextAction"] == rows["S-001"]["nextAction"]


def test_shipment_workspace_lazy_path_renders_readiness_without_exception() -> None:
    shipment = _shipments()["S-001"]
    shipment["data"]["3.4"]["commission"] = {}
    page_src = f"""
import json
import streamlit as st
from views.shipment import ui_shipment_detail_tabs

SHIPMENT = json.loads(r'''{json.dumps(shipment, ensure_ascii=False)}''')
st.session_state.db_customers = json.loads(r'''{json.dumps(_customers(), ensure_ascii=False)}''')
ui_shipment_detail_tabs("S-001", SHIPMENT)
"""
    patches = [
        patch("core.database.init_connection", return_value=None),
        patch("views.shipment.load_proxy_payments", return_value={}),
        patch("views.shipment.load_entrustments", return_value={}),
        patch("views.shipment.load_audit_logs", return_value=[]),
    ]
    for active_patch in patches:
        active_patch.start()
    try:
        app = AppTest.from_string(page_src, default_timeout=120)
        app.run()
    finally:
        for active_patch in reversed(patches):
            active_patch.stop()

    _assert_no_streamlit_exceptions(app)
    rendered = "\n".join(str(element.value or "") for element in app.markdown)
    rendered += "\n" + "\n".join(
        str(element.value or "")
        for collection in (app.subheader, app.text_input, app.caption)
        for element in collection
    )
    assert "VIỆC TIẾP THEO" in rendered
    assert "S-001" in rendered
    tab_labels = {str(tab.label) for tab in app.tabs if tab.label}
    assert "🚛 PICKUP & XUẤT KHẨU" in tab_labels
    assert "🛃 IMPORT & GIAO HÀNG" in tab_labels
    assert "💰 FINANCE (CÔNG NỢ)" in tab_labels


def test_readiness_deadline_coercion_preserves_unknown_and_source_identity() -> None:
    shipment = _shipments()["S-001"]
    shipment["customer_required_date"] = "2020-01-01"
    before = deepcopy(shipment)
    dashboard = build_shipment_summary(shipment)
    readiness = get_all_readiness(shipment, dashboard)
    action = derive_next_action(shipment, readiness)

    assert action.severity == CRITICAL
    assert action.due_at == date(2020, 1, 1)
    assert shipment == before

    unknown_shipment = {"shipment_id": "UNKNOWN-001", "customer_required_date": UNKNOWN}
    unknown_dashboard = build_shipment_summary(unknown_shipment)
    unknown_action = derive_next_action(
        unknown_shipment,
        get_all_readiness(unknown_shipment, unknown_dashboard),
    )
    assert unknown_action.due_at is None
    assert unknown_shipment["customer_required_date"] == UNKNOWN
