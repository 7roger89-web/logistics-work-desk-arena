"""LOGI_CEO_REPORT_01 — focused tests for the bounded read-only CEO summary.

The adapter is intentionally presentation-only: it consumes the projections
already assembled by ``views.logi_view_model``. These tests prove the narrow
contract rather than introducing an analytics model:

* current shipment / established open-work counts;
* C2C and C2D outstanding positions remain separated by currency;
* incomplete Finance Actual remains visible and never becomes a zero amount;
* reconciliation state counts come from the existing canonical projection;
* the normal view-model exposes the same bounded slice on isolated staging.

Production database is never used.
"""

from __future__ import annotations

import pytest

from views import ceo_report
from views import reconciliation_desk


def _positions_by_currency(section: dict) -> dict[str, dict]:
    return {item["currency"]: item for item in section["positions"]}


def test_ceo_projection_uses_existing_current_position_without_cross_currency_total():
    """C2C/C2D totals pass through by currency; incomplete rows do not leak in."""
    report = ceo_report.ceo_report_projection(
        shipments=[
            {"id": "LO-1", "status": "Đang vận chuyển"},
            {"id": "LO-2", "status": "Đã giao"},
            {"id": "LO-3", "status": "Chờ giao"},
        ],
        home={"runningCount": 2},
        tasks=[
            {"id": "OPS-1", "level": "Khan"},
            {"id": "OPS-2", "level": "CanXuLy"},
            {"id": "OPS-3", "level": "BinhThuong"},
        ],
        receivables={
            "rows": [
                {"id": "LO-1", "currency": "VND", "hasActualLines": True, "outstanding": 60_000_000},
                {"id": "LO-2", "currency": "USD", "hasActualLines": True, "outstanding": 800},
                # Finance Actual is absent: it must not become VND 0 or enter totals.
                {"id": "LO-3", "currency": "VND", "hasActualLines": False, "outstanding": None},
            ],
            "totals": {
                "VND": {"receivable": 100_000_000, "received": 40_000_000, "outstanding": 60_000_000},
                "USD": {"receivable": 1_000, "received": 200, "outstanding": 800},
            },
        },
        payables={
            "rows": [
                {"id": "LO-1|AGT|VND", "currency": "VND", "remaining": 37_000_000},
                {"id": "LO-2|AGT|CNY", "currency": "CNY", "remaining": 2_000},
            ],
            "totals": {
                "VND": {"payable": 57_000_000, "paid": 20_000_000, "remaining": 37_000_000, "count": 1},
                "CNY": {"payable": 3_000, "paid": 1_000, "remaining": 2_000, "count": 1},
            },
            "status": "CONFIRMED",
        },
        reconciliation={
            "status": "REVIEW_REQUIRED",
            "summary": {
                "obligations": {"MATCHED": 1, "PARTIAL": 1, "UNMATCHED": 1, "UNKNOWN": 1},
                "money": {"ALLOCATED": 1, "PARTIAL": 1, "UNALLOCATED": 0, "UNKNOWN": 0},
                "reviewCount": 1,
            },
            "error": None,
        },
    )

    assert report["classification"] == "PARTIAL_BACKED_READY"
    assert report["readOnly"] is True
    assert report["operations"] == {
        "totalShipmentCount": 3,
        "openShipmentCount": 2,
        "statusCounts": [
            {"status": "Đang vận chuyển", "count": 1},
            {"status": "Đã giao", "count": 1},
            {"status": "Chờ giao", "count": 1},
        ],
        "actionableTaskCount": 2,
    }

    receivables = _positions_by_currency(report["receivables"])
    assert set(receivables) == {"VND", "USD"}
    assert receivables["VND"]["outstanding"] == 60_000_000
    assert receivables["VND"]["openCount"] == 1
    assert receivables["USD"]["outstanding"] == 800
    assert report["finance"]["incompleteShipmentCount"] == 1
    # The adapter has no cross-currency money total at all.
    assert "grandTotal" not in report["receivables"]
    assert "total" not in report["receivables"]

    payables = _positions_by_currency(report["payables"])
    assert set(payables) == {"VND", "CNY"}
    assert payables["VND"]["outstanding"] == 37_000_000
    assert payables["CNY"]["outstanding"] == 2_000
    assert "grandTotal" not in report["payables"]

    assert report["reconciliation"]["available"] is True
    assert report["reconciliation"]["obligations"] == {
        "MATCHED": 1,
        "PARTIAL": 1,
        "UNMATCHED": 1,
        "UNKNOWN": 1,
    }
    assert report["reconciliation"]["money"] == {
        "ALLOCATED": 1,
        "PARTIAL": 1,
        "UNALLOCATED": 0,
        "UNKNOWN": 0,
    }
    assert report["reconciliation"]["reviewCount"] == 1
    assert {link["href"] for link in report["quickLinks"]} == {
        "/lo-hang",
        "/tai-chinh/thu-tien",
        "/tai-chinh/cong-no-doi-tac",
        "/tai-chinh/doi-soat",
    }


def test_ceo_projection_keeps_empty_ledger_and_missing_open_count_unknown_not_zero():
    """No C2D/C6 record is not rendered as a balanced money or state zero."""
    report = ceo_report.ceo_report_projection(
        shipments=[],
        home={},
        tasks=[],
        receivables={"rows": [], "totals": {}},
        payables={"rows": [], "totals": {}, "status": "UNKNOWN"},
        reconciliation={"status": "EMPTY", "summary": None, "error": None},
    )

    assert report["operations"]["totalShipmentCount"] == 0
    assert report["operations"]["openShipmentCount"] is None
    assert report["receivables"]["positions"] == []
    assert report["receivables"]["hasAuthoritativeAmounts"] is False
    assert report["payables"]["hasCanonicalRecords"] is False
    assert report["payables"]["positions"] == []
    assert report["reconciliation"]["available"] is False
    assert report["reconciliation"]["obligations"] is None
    assert report["reconciliation"]["money"] is None
    assert report["reconciliation"]["reviewCount"] is None


def test_reconciliation_summary_counts_existing_states_before_filtering():
    """PARTIAL stays separated by obligation/money side and UNKNOWN stays visible."""
    projection = {
        "rows": [
            {"side": "obligation", "matchState": "MATCHED"},
            {"side": "obligation", "matchState": "PARTIAL"},
            {"side": "obligation", "matchState": None},
            {"side": "money", "matchState": "ALLOCATED"},
            {"side": "money", "matchState": "PARTIAL"},
            {"side": "money", "matchState": "UNALLOCATED"},
        ],
        "totals": {
            "VND": {"review": {"count": 1}},
            "CNY": {"review": {"count": 2}},
        },
    }

    summary = reconciliation_desk.reconciliation_summary(projection)
    assert summary["obligations"] == {
        "MATCHED": 1,
        "PARTIAL": 1,
        "UNMATCHED": 0,
        "UNKNOWN": 1,
    }
    assert summary["money"] == {
        "ALLOCATED": 1,
        "PARTIAL": 1,
        "UNALLOCATED": 1,
        "UNKNOWN": 0,
    }
    assert summary["reviewCount"] == 3


@pytest.fixture()
def staging():
    """Clean, isolated mongomock staging database with the deterministic actor."""
    import streamlit as st

    from views import logi_sandbox

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    yield transport
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


def _dispatch(vm, sequence: int, event: str, payload: dict) -> dict:
    outcomes = vm.consume_phase_b_triggers(
        {"seq": 0},
        {event: {"seq": sequence, "event": event, "payload": payload}},
    )
    assert len(outcomes) == 1
    return outcomes[0]


def test_view_model_exposes_ceo_section_from_existing_staging_projections(staging):
    """The normal model has the CEO bridge; canonical C2D records flow through it."""
    from views import logi_view_model as vm

    initial = vm.build_view_model()
    report = initial["ceoReport"]
    assert report["readOnly"] is True
    assert report["operations"]["totalShipmentCount"] == len(initial["shipments"])
    assert report["reconciliation"]["status"] == "EMPTY"
    assert report["reconciliation"]["available"] is False

    obligation = _dispatch(vm, 1, "partner_payable_record", {
        "shipmentId": "LO-0308",
        "partnerId": "AGT-PHUANH",
        "requestId": "CEO-TEST-OBLIGATION",
        "amount": 10_000_000,
        "currency": "VND",
        "note": "Phải trả chi phí đối tác theo thực tế lô",
    })
    assert obligation["ok"], obligation["error"]
    payment = _dispatch(vm, 2, "partner_payment_record", {
        "shipmentId": "LO-0308",
        "partnerId": "AGT-PHUANH",
        "requestId": "CEO-TEST-PAYMENT",
        "amount": 10_000_000,
        "currency": "VND",
        "date": "2026-09-10",
        "note": "Chuyển khoản thanh toán đối tác",
    })
    assert payment["ok"], payment["error"]

    refreshed = vm.build_view_model()
    report = refreshed["ceoReport"]
    assert report["payables"]["hasCanonicalRecords"] is True
    vnd = _positions_by_currency(report["payables"])["VND"]
    assert vnd["outstanding"] == 0.0
    assert vnd["openCount"] == 0
    assert report["reconciliation"]["available"] is True
    assert report["reconciliation"]["obligations"]["MATCHED"] >= 1
    assert report["reconciliation"]["money"]["ALLOCATED"] >= 1
