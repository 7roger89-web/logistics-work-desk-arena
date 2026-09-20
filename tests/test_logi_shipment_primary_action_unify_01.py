"""LOGI_SHIPMENT_PRIMARY_ACTION_UNIFY_01 (issue #82) — focused acceptance evidence.

The lot detail used to carry TWO next-action authorities: the legacy
dashboard/readiness projection (``shipment.nextAction``) at the top and the
execution-profile projection (``executionProfile.nextAction``) lower on the
page — and they could disagree. This slice COMPOSES one primary instruction
from the two existing in-memory projections and routes it to an EXISTING work
surface. No new cockpit, page, writer, field, event, handler or database read.

What this file proves, in order:

 A. ROAD FTL without a truck type composes "Xac nhan loai xe" and routes to
    the EXISTING van-tai tab (which owns the truck/container editors);
 B. SEA FCL without equipment composes "Bo sung loai container" to van-tai;
 C. an IMPORT_CUSTOMS gap routes to the EXISTING nhap tab at fld-tk;
 D. a CIF + actual-NO red mismatch wins over a dashboard WARNING;
 E. a genuine dashboard CRITICAL is never hidden by a profile gap;
 F. a DONE/MONITOR profile falls back to the existing dashboard action;
 G. PROFILE_INCOMPLETE routes to the EXISTING profile section;
 H. no alert keeps the existing stable/no-alert behaviour;
 I. invariants: ONE profile build per row (identity-reused), ZERO added
    database reads, no new dispatch surface, and Tasks/Home/notifications all
    carry the SAME composed route (no divergent routing).

Every row-level assertion runs the real ``shipment_projection`` over an
in-memory document: the profile side is the real ``build_execution_profile``
derivation, not a hand-built stub.
"""

from __future__ import annotations

import pytest

from core import shipment_execution_profile as ep
from views import logi_real_data as rd
from views import logi_view_model as vm


# ---------------------------------------------------------------------------
# Harness — in-memory documents through the real projection
# ---------------------------------------------------------------------------

def _profiled_doc(
    sid: str,
    *,
    mode: str,
    incoterm: str,
    load_model: str,
    scope: list[str],
    insurance: str = "NO",
    place: str = "Pingxiang Warehouse",
    customs: dict | None = None,
    transport: dict | None = None,
    delivery: dict | None = None,
) -> dict:
    return {
        "id": sid,
        "data": {
            "0.0": {
                "mode": mode,
                "incoterm": incoterm,
                "execution_profile": {
                    "incoterm_version": "2020",
                    "incoterm_named_place": place,
                    "load_model": load_model,
                    "service_scope": list(scope),
                    "service_scope_confirmed": True,
                    "cargo_insurance": {"status": insurance},
                },
            },
            "1.2": dict(transport or {}),
            "2.4": dict(customs or {}),
            "2.6": {},
            "2.7": dict(delivery or {}),
        },
    }


def _warning_dashboard(label: str = "Theo dõi tiến độ hồ sơ") -> dict:
    return {
        "next_action": {"label": label, "detail": "Hồ sơ đang chờ xử lý."},
        "top_alert": {"severity": "warning", "label": label, "detail": "Hồ sơ đang chờ xử lý."},
    }


def _critical_dashboard() -> dict:
    return {
        "next_action": {"label": "Xử lý nợ quá hạn", "detail": "Công nợ vượt hạn 7 ngày."},
        "top_alert": {"severity": "critical", "label": "Nợ quá hạn", "detail": "Công nợ vượt hạn 7 ngày."},
    }


def _row(document: dict, dashboard: dict | None = None) -> dict:
    return rd.shipment_projection(document, dashboard={} if dashboard is None else dashboard)


# ===========================================================================
# A. ROAD FTL without a truck → "Xác nhận loại xe" → van-tai
# ===========================================================================

def _road_ftl_doc(sid: str = "LO-ROAD-FTL") -> dict:
    # Proven shape: test_road_ftl_without_a_truck_asks_to_confirm_the_truck_type.
    return _profiled_doc(
        sid, mode="Truck", incoterm="FCA", load_model="FTL",
        scope=["ORIGIN_PICKUP"], insurance="NO",
    )


def test_road_ftl_without_truck_composes_the_truck_question_to_van_tai():
    row = _row(_road_ftl_doc(), _warning_dashboard())

    assert row["executionProfile"]["nextAction"]["code"] == "ROAD_TRUCK_PROFILE"
    assert "Xác nhận loại xe" in row["nextAction"], row["nextAction"]
    assert row["nextAction"] == row["executionProfile"]["nextAction"]["label"]
    assert row["nextRoute"] == f"/lo-hang/{row['id']}?tab=van-tai", row["nextRoute"]
    assert row["priority"] == "CanXuLy"
    assert row["nextLabel"] == "XỬ LÝ NGAY"


# ===========================================================================
# B. SEA FCL without equipment → "Bổ sung loại container" → van-tai
# ===========================================================================

def test_sea_fcl_without_equipment_composes_the_container_question_to_van_tai():
    # Proven shape: test_sea_fcl_without_equipment_asks_for_the_container_type.
    document = _profiled_doc(
        "LO-SEA-FCL", mode="Sea", incoterm="CIF", load_model="FCL",
        scope=["MAIN_CARRIAGE", "IMPORT_CUSTOMS"], insurance="NO",
        place="Hai Phong Port",
    )
    row = _row(document, _warning_dashboard())

    assert row["executionProfile"]["nextAction"]["code"] == "SEA_EQUIPMENT"
    assert "Bổ sung loại container" in row["nextAction"], row["nextAction"]
    assert row["nextRoute"] == f"/lo-hang/{row['id']}?tab=van-tai", row["nextRoute"]
    assert row["priority"] == "CanXuLy"
    assert row["nextLabel"] == "XỬ LÝ NGAY"


# ===========================================================================
# C. IMPORT_CUSTOMS gap → nhap at the existing fld-tk input
# ===========================================================================

def _import_customs_doc(sid: str = "LO-IMPORT-TK", **overrides) -> dict:
    kwargs: dict = dict(
        mode="Truck", incoterm="FCA", load_model="LTL",
        scope=["IMPORT_CUSTOMS"], insurance="NO",
    )
    kwargs.update(overrides)
    return _profiled_doc(sid, **kwargs)


def test_import_customs_gap_routes_to_nhap_at_the_tk_input():
    row = _row(_import_customs_doc(), _warning_dashboard())

    assert row["executionProfile"]["nextAction"]["code"] == "IMPORT_CUSTOMS"
    assert "tờ khai" in row["nextAction"], row["nextAction"]
    assert row["nextRoute"] == f"/lo-hang/{row['id']}?tab=nhap#fld-tk", row["nextRoute"]
    assert row["priority"] == "CanXuLy"
    assert row["nextLabel"] == "XỬ LÝ NGAY"


# ===========================================================================
# D. CIF + actual NO (red mismatch) wins over a dashboard WARNING
# ===========================================================================

def test_cif_no_insurance_red_mismatch_wins_over_a_dashboard_warning():
    # Proven shape: _insurance_doc (Sea LCL CIF, IMPORT_CUSTOMS satisfied, so
    # the ONLY unmet stage is the red INSURANCE_EVIDENCE mismatch).
    document = _profiled_doc(
        "LO-CIF-NO", mode="Sea", incoterm="CIF", load_model="LCL",
        scope=["IMPORT_CUSTOMS"], insurance="NO", place="Hai Phong Port",
        customs={"tk_no": "105588421330", "customs_status": True},
    )
    row = _row(document, _warning_dashboard())

    profile_action = row["executionProfile"]["nextAction"]
    assert profile_action["code"] == "INSURANCE_EVIDENCE"
    assert profile_action["tone"] == "red"
    assert row["nextAction"] == profile_action["label"]
    assert row["priority"] == "Khan", "a red profile blocker is Khan, like a critical alert"
    assert row["nextLabel"] == "XỬ LÝ NGAY"
    assert row["nextRoute"].endswith("#shipment-execution-profile"), row["nextRoute"]
    assert "?tab=nhap" in row["nextRoute"], "the existing status tab is kept, only the anchor is added"


# ===========================================================================
# E. A genuine dashboard CRITICAL is never hidden by a profile gap
# ===========================================================================

def test_dashboard_critical_wins_over_a_profile_gap():
    row = _row(_road_ftl_doc(), _critical_dashboard())

    assert row["executionProfile"]["nextAction"]["code"] == "ROAD_TRUCK_PROFILE"
    assert row["nextAction"] == "Xử lý nợ quá hạn"
    assert row["nextActionDetail"] == "Công nợ vượt hạn 7 ngày."
    assert row["priority"] == "Khan"
    assert row["nextLabel"] == "XỬ LÝ NGAY"
    # The dashboard action keeps its existing status-tab route — no anchor, no
    # profile wording, nothing invented.
    assert row["nextRoute"] == f"/lo-hang/{row['id']}?tab=lay-hang", row["nextRoute"]


# ===========================================================================
# F. DONE / MONITOR profiles fall back to the dashboard action
# ===========================================================================

def test_delivered_done_profile_falls_back_to_the_dashboard_action():
    document = _import_customs_doc(
        "LO-DONE", delivery={"is_delivered": True, "addr": "Bắc Ninh"},
        customs={"tk_no": "105588421330", "customs_status": True},
    )
    row = _row(document, _warning_dashboard("Đối soát công nợ cuối lô"))

    assert row["executionProfile"]["nextAction"]["code"] == "DONE"
    assert row["nextAction"] == "Đối soát công nợ cuối lô"
    assert row["priority"] == "CanXuLy"
    assert row["nextRoute"] == f"/lo-hang/{row['id']}?tab=lay-hang", row["nextRoute"]


def test_monitor_profile_falls_back_to_the_dashboard_action():
    # Tk registered → IMPORT_CUSTOMS satisfied → nothing unmet → MONITOR.
    document = _import_customs_doc(
        "LO-MONITOR", customs={"tk_no": "105588421330"},
    )
    row = _row(document, _warning_dashboard("Chuẩn bị chứng từ giao hàng"))

    assert row["executionProfile"]["nextAction"]["code"] == "MONITOR"
    assert row["nextAction"] == "Chuẩn bị chứng từ giao hàng"
    assert row["nextActionDetail"] == "Hồ sơ đang chờ xử lý."
    assert row["priority"] == "CanXuLy"
    assert row["nextRoute"] == f"/lo-hang/{row['id']}?tab=nhap", row["nextRoute"]


# ===========================================================================
# G. PROFILE_INCOMPLETE routes to the EXISTING profile section
# ===========================================================================

def test_profile_incomplete_routes_to_the_existing_profile_section():
    legacy = {"id": "LO-LEGACY", "data": {"0.0": {"mode": "Truck", "incoterm": "DAP"}}}
    row = _row(legacy)

    assert row["executionProfile"]["state"] == ep.STATE_INCOMPLETE
    assert row["executionProfile"]["nextAction"]["code"] == "PROFILE_INCOMPLETE"
    assert row["nextAction"] == row["executionProfile"]["nextAction"]["label"]
    assert "Bổ sung hồ sơ thực hiện lô" in row["nextAction"]
    assert row["nextRoute"] == f"/lo-hang/{row['id']}?tab=lay-hang#shipment-execution-profile"
    assert row["priority"] == "CanXuLy"
    assert row["nextLabel"] == "XỬ LÝ NGAY"


def test_config_check_red_routes_to_the_profile_section_as_khan():
    document = _profiled_doc(
        "LO-CONFIG", mode="Truck", incoterm="FOB", load_model="FTL",
        scope=["ORIGIN_PICKUP"], insurance="NO",
    )
    row = _row(document, _warning_dashboard())

    assert row["executionProfile"]["nextAction"]["code"] == "CONFIG_CHECK"
    assert row["executionProfile"]["nextAction"]["tone"] == "red"
    assert row["nextAction"] == row["executionProfile"]["nextAction"]["label"]
    assert row["priority"] == "Khan"
    assert row["nextRoute"].endswith("#shipment-execution-profile")


# ===========================================================================
# H. No alert keeps the existing stable behaviour
# ===========================================================================

def test_no_alert_keeps_the_stable_no_alert_behaviour():
    document = _import_customs_doc(
        "LO-STABLE", customs={"tk_no": "105588421330"},
    )
    row = _row(document, {})

    assert row["executionProfile"]["nextAction"]["code"] == "MONITOR"
    assert row["nextAction"] == "Lô hàng ổn định — không có cảnh báo"
    assert row["nextActionDetail"] == ""
    assert row["priority"] == "BinhThuong"
    assert row["nextLabel"] == "XEM LÔ"
    assert row["nextRoute"] == f"/lo-hang/{row['id']}?tab=nhap"


# ===========================================================================
# I. Invariants
# ===========================================================================

def test_the_profile_is_built_once_per_row_and_reused_by_identity(monkeypatch):
    """EXECUTION_PROFILE_BUILDS_PER_ROW=1: the served object IS the composed one."""

    calls: list[dict] = []
    real_build = ep.build_execution_profile

    def _counting(shipment, legs=None):
        profile = real_build(shipment, legs=legs)
        calls.append(profile)
        return profile

    monkeypatch.setattr(ep, "build_execution_profile", _counting)
    row = _row(_road_ftl_doc(), _warning_dashboard())

    assert len(calls) == 1, "one profile build per projected row — no second derivation"
    assert row["executionProfile"] is calls[0]
    assert row["nextAction"] == calls[0]["nextAction"]["label"]


def test_the_composition_issues_zero_database_reads(monkeypatch):
    """PRIMARY_ACTION_DB_READS_ADDED=0: the composer is pure over memory."""

    from core import database as core_database

    def _forbidden(*args, **kwargs):
        raise AssertionError("compose_primary_action must not touch the database")

    monkeypatch.setattr(core_database, "get_db", _forbidden)
    composed = rd.compose_primary_action(
        shipment_id="LO-X",
        dashboard=_warning_dashboard(),
        execution_profile={"nextAction": {
            "code": "ROAD_TRUCK_PROFILE", "label": "Xác nhận loại xe",
            "detail": "Thiếu loại xe.", "tone": "amber"}},
        status_tab="lay-hang",
    )
    assert composed["text"] == "Xác nhận loại xe"
    assert composed["route"] == "/lo-hang/LO-X?tab=van-tai"


def test_no_new_dispatch_surface_was_added():
    """ONE handler per declared event: this slice adds no event and no handler."""

    assert set(vm._HANDLERS) == set(vm.PHASE_B_EVENTS)
    assert not [name for name in vm._HANDLERS if "primary" in name]


def test_tasks_home_and_notifications_carry_the_same_composed_route():
    """No divergent routing: every surface reuses row.nextRoute verbatim."""

    alert_dashboard = dict(_warning_dashboard("Bổ sung chứng từ vận chuyển"))
    alert_dashboard["alerts"] = [{
        "code": "DOCS", "severity": "warning",
        "label": "Thiếu chứng từ", "detail": "Còn thiếu vận đơn.",
    }]
    rows = [
        _row(_road_ftl_doc("LO-T1"), alert_dashboard),
        _row(_import_customs_doc("LO-T2"), _warning_dashboard()),
        _row(_import_customs_doc("LO-T3", customs={"tk_no": "105588421330"}), {}),
    ]
    by_id = {row["id"]: row for row in rows}

    tasks = vm._task_projection(rows, {"tasks": []})
    derived = [task for task in tasks if task["id"].startswith("OPS-")]
    assert derived, "the gapped rows must still surface as derived ops rows"
    for task in derived:
        assert task["route"] == by_id[task["lot"]]["nextRoute"], task
        assert task["job"] == by_id[task["lot"]]["nextAction"], task

    summary = {"total": 3, "critical": 0, "warning": 2, "deadline_soon": 0,
               "financial_attention": 0, "missing_info": 0}
    home = vm._home_projection(rows, summary, {"tasks": []})
    assert home["focus"] is not None
    assert home["focus"]["to"] == by_id[home["focus"]["id"]]["nextRoute"]
    assert home["focus"]["nextAction"] == by_id[home["focus"]["id"]]["nextAction"]

    notifications = vm._notifications(rows)
    assert notifications, "the alerted row must still notify"
    for note in notifications:
        lot = note["id"].split("-")[0] + "-" + note["id"].split("-")[1]
        assert note["route"] == by_id[lot]["nextRoute"], note


@pytest.mark.parametrize("code,expected_tab,expected_anchor", [
    ("ORIGIN_PICKUP", "lay-hang", ""),
    ("EXPORT_HANDLING", "lay-hang", ""),
    ("ORIGIN_HANDOFF", "lay-hang", ""),
    ("CROSS_BORDER", "lay-hang", ""),
    ("MAIN_CARRIAGE", "van-tai", ""),
    ("SEA_DOCUMENTS", "van-tai", ""),
    ("AIR_DOCUMENTS", "van-tai", ""),
    ("RAIL_CARRIAGE", "van-tai", ""),
    ("SEA_EQUIPMENT", "van-tai", ""),
    ("SEA_CONSOLIDATION", "van-tai", ""),
    ("ROAD_TRUCK_PROFILE", "van-tai", ""),
    ("ROAD_CONSOLIDATION", "van-tai", ""),
    ("IMPORT_CUSTOMS", "nhap", "#fld-tk"),
    ("DELIVERY", "nhap", ""),
    ("PROFILE_INCOMPLETE", "lay-hang", "#shipment-execution-profile"),
    ("CONFIG_CHECK", "lay-hang", "#shipment-execution-profile"),
    ("INSURANCE_EVIDENCE", "lay-hang", "#shipment-execution-profile"),
])
def test_every_profile_code_routes_to_an_existing_surface(code, expected_tab, expected_anchor):
    composed = rd.compose_primary_action(
        shipment_id="LO-X",
        dashboard=_warning_dashboard(),
        execution_profile={"nextAction": {
            "code": code, "label": f"Việc {code}", "detail": "", "tone": "amber"}},
        status_tab="lay-hang",
    )
    assert composed["text"] == f"Việc {code}"
    assert composed["route"] == f"/lo-hang/LO-X?tab={expected_tab}{expected_anchor}", code
