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
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from core.readiness import CRITICAL, derive_next_action, get_all_readiness
from core.shipment_360 import UNKNOWN
from core.shipment_dashboard import (
    build_shipment_dashboard_view,
    build_shipment_summary,
)
from tests.test_all_tabs_smoke import APP_PATH, _customers, _login_fixture, _shipments


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


def test_dashboard_lazy_workdesk_rows_build_one_projection_and_render() -> None:
    """The mounted desk builds its rows through the ONE lazy projection.

    LOG-HOTFIX-04 pinned the legacy Streamlit dashboard's lazy-row path and its
    ``build_shipment_summary`` alias. That page is unmounted (the desk is the
    React shell), but the property the hotfix cared about is unchanged and is
    asserted on the CURRENT path: the delivered worklist is built by
    ``core.shipment_dashboard.build_shipment_dashboard_view`` exactly once per
    shipment (no per-widget recomputation), and each row still carries a
    deterministic next action for the UI to render.
    """
    calls: list[str] = []

    from core.shipment_dashboard import build_shipment_dashboard_view as real_view

    def _spy(shipment, *args, **kwargs):
        calls.append(str(shipment.get("id") or shipment.get("shipment_id") or "?"))
        return real_view(shipment, *args, **kwargs)

    fixture_user = _login_fixture({
        "username": "fixture", "user_id": "U-FIXTURE", "email": "", "active": True,
    })
    with patch("core.shipment_dashboard.build_shipment_dashboard_view", side_effect=_spy):
        app = AppTest.from_file(str(APP_PATH), default_timeout=120)
        app.session_state["current_user"] = dict(fixture_user)
        with patch("core.database.load_users",
                   return_value={"fixture": dict(fixture_user)}):
            app.run()

    _assert_no_streamlit_exceptions(app)

    from views import logi_view_model as vm

    model = app.session_state[vm.STATE_KEY]
    rows = list(model["shipments"].values())
    assert rows, "the desk delivered no worklist"
    # ONE dashboard projection per shipment — the lazy path, not per widget.
    assert sorted(calls) == sorted(row["id"] for row in rows), (calls, [r["id"] for r in rows])
    for row in rows:
        assert row["nextAction"], row["id"]
        assert row["priority"] in {"Khan", "CanXuLy", "BinhThuong"}, row["id"]
        assert row["nextLabel"] and row["nextRoute"].startswith("/lo-hang/"), row["id"]


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
