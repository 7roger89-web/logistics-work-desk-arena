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
            {"status": "Đang vận chuyển", "count": 1, "share": 0.3333},
            {"status": "Đã giao", "count": 1, "share": 0.3333},
            {"status": "Chờ giao", "count": 1, "share": 0.3333},
        ],
        "actionableTaskCount": 2,
    }
    assert report["actionables"] == [
        {
            "id": "OPS-1",
            "level": "Khan",
            "shipmentId": "UNKNOWN",
            "customer": "Chưa xác định",
            "job": "Chưa xác định",
            "detail": None,
            "route": "/lo-hang",
        },
        {
            "id": "OPS-2",
            "level": "CanXuLy",
            "shipmentId": "UNKNOWN",
            "customer": "Chưa xác định",
            "job": "Chưa xác định",
            "detail": None,
            "route": "/lo-hang",
        },
    ]
    # No shipment row in this scenario carries Finance Actual: the actual
    # position stays UNKNOWN rather than becoming VND 0.
    assert report["financeActual"] == {"positions": [], "available": False}
    assert report["topCustomers"] == []

    receivables = _positions_by_currency(report["receivables"])
    assert set(receivables) == {"VND", "USD"}
    assert receivables["VND"]["outstanding"] == 60_000_000
    assert receivables["VND"]["openCount"] == 1
    assert receivables["VND"]["rowCount"] == 1
    assert receivables["VND"]["incompleteRowCount"] == 1
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


def test_reconciliation_summary_remains_complete_when_list_rows_are_bounded():
    """A CEO count must not silently become a first-400-row count."""
    positions = [
        {
            "shipment_id": f"LO-{index:03d}",
            "partners": [],
            "obligations": [
                {
                    "obligation_id": f"OBL-{index:03d}",
                    "currency": "VND",
                    "amount": 1.0,
                    "allocated": 0.0,
                    "outstanding": 1.0,
                    "status": "CONFIRMED",
                }
            ],
            "payments": [],
        }
        for index in range(reconciliation_desk.MAX_ROWS + 1)
    ]

    projection = reconciliation_desk.reconciliation_projection(positions)
    assert projection["truncated"] is True
    assert len(projection["rows"]) == reconciliation_desk.MAX_ROWS
    assert reconciliation_desk.reconciliation_summary(projection)["obligations"]["UNMATCHED"] == reconciliation_desk.MAX_ROWS + 1


# ----------------------------------------------------------------------------
# LOGI_CEO_REPORT_REAL_PARITY_01 — status visual, bottleneck panel, actual
# per-currency finance position and per-currency top customers.  All figures
# must stay direct source facts or trivial same-currency presentation sums.
# ----------------------------------------------------------------------------

from collections.abc import Mapping as _Mapping

# Donor (logi-good CEO.tsx) business samples. None of them may ever enter the
# real report or the production bundle (DONOR MOCK FIREWALL).
DONOR_SAMPLE_VALUES = (
    "1.510 tr",
    "262 tr",
    "+22% vs kỳ trước",
    "873 tr",
    "Thông quan Hữu Nghị chậm 1,5 ngày",
)


def _ship_row(
    sid: str,
    customer: str,
    *,
    ccy: str = "VND",
    has_actual: bool = True,
    revenue: float | None = 100.0,
    cost: float | None = 60.0,
    profit: float | None = 40.0,
    status: str = "Đang vận chuyển",
    customer_id: str | None = None,
) -> dict:
    return {
        "id": sid,
        "status": status,
        "customer": customer,
        "customerId": customer_id,
        "finance": {
            "currency": ccy,
            "hasActualLines": has_actual,
            "receivableNet": revenue,
            "payable": cost,
            "profit": profit,
        },
    }


def _report(**overrides) -> dict:
    payload = {
        "shipments": [],
        "home": {},
        "tasks": [],
        "receivables": {"rows": [], "totals": {}},
        "payables": {"rows": [], "totals": {}, "status": "UNKNOWN"},
        "reconciliation": {"status": "EMPTY", "summary": None, "error": None},
    }
    payload.update(overrides)
    return ceo_report.ceo_report_projection(**payload)


def _all_numbers(value):
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        yield float(value)
    elif isinstance(value, _Mapping):
        for item in value.values():
            yield from _all_numbers(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_numbers(item)


def test_status_distribution_share_uses_real_total_only():
    """Bar width = count / REAL current row count. No invented denominator."""
    report = _report(shipments=[
        {"id": "LO-1", "status": "Chờ thông quan"},
        {"id": "LO-2", "status": "Chờ thông quan"},
        {"id": "LO-3", "status": "Chờ thông quan"},
        {"id": "LO-4", "status": "Đã giao"},
    ])
    counts = {item["status"]: item for item in report["operations"]["statusCounts"]}
    assert counts["Chờ thông quan"]["count"] == 3
    assert counts["Chờ thông quan"]["share"] == 0.75
    assert counts["Đã giao"]["count"] == 1
    assert counts["Đã giao"]["share"] == 0.25
    # The shares of rows actually counted sum to exactly 1 over that total.
    assert sum(item["share"] for item in report["operations"]["statusCounts"]) == 1.0
    # An empty desk has no statuses and therefore no invented bar.
    assert _report()["operations"]["statusCounts"] == []


def test_finance_actual_positions_equal_canonical_values_and_isolate_currencies():
    """Same-currency sums equal the source rows exactly; no cross-currency sum."""
    report = _report(shipments=[
        _ship_row("LO-1", "Khách A", ccy="VND", revenue=111_000, cost=60_000, profit=51_000, customer_id="CUST-A"),
        _ship_row("LO-2", "Khách B", ccy="VND", revenue=222_000, cost=90_000, profit=132_000, customer_id="CUST-B"),
        _ship_row("LO-3", "Client C", ccy="USD", revenue=500, cost=200, profit=300),
        _ship_row("LO-4", "Клиент D", ccy="CNY", revenue=3_000, cost=2_500, profit=500),
    ])

    positions = {item["currency"]: item for item in report["financeActual"]["positions"]}
    assert set(positions) == {"VND", "USD", "CNY"}
    assert report["financeActual"]["available"] is True

    vnd, usd, cny = positions["VND"], positions["USD"], positions["CNY"]
    assert (vnd["revenueNet"], vnd["cost"], vnd["profit"]) == (333_000, 150_000, 183_000)
    assert vnd["marginPct"] == round(183_000 / 333_000 * 100, 2)
    assert vnd["rowCount"] == 2
    assert (usd["revenueNet"], usd["cost"], usd["profit"], usd["marginPct"]) == (500, 200, 300, 60.0)
    assert (cny["revenueNet"], cny["cost"], cny["profit"], cny["marginPct"]) == (3_000, 2_500, 500, round(500 / 3_000 * 100, 2))

    # NO figure anywhere in the whole report may be a cross-currency total.
    numbers = set(_all_numbers(report))
    for forbidden in (
        333_000 + 500, 333_000 + 3_000, 500 + 3_000, 333_000 + 500 + 3_000,  # revenue
        150_000 + 200, 150_000 + 2_500, 150_000 + 200 + 2_500,              # cost
        183_000 + 300, 183_000 + 500, 183_000 + 300 + 500,                  # profit
    ):
        assert float(forbidden) not in numbers, f"cross-currency total {forbidden} leaked"


def test_finance_actual_unknown_stays_none_and_never_zero():
    """Missing Finance Actual or an unsafe row is UNKNOWN, never a 0 amount."""
    report = _report(shipments=[
        # Not booked yet: excluded entirely, visible via incomplete count.
        _ship_row("LO-1", "Khách A", has_actual=False, revenue=None, cost=None, profit=None),
        # Booked but the profit figure is unsafe: excluded, counted incomplete.
        _ship_row("LO-2", "Khách B", revenue=100.0, cost=40.0, profit=None),
        _ship_row("LO-3", "Khách C", revenue=200.0, cost=90.0, profit=110.0),
    ])
    positions = report["financeActual"]["positions"]
    assert len(positions) == 1
    vnd = positions[0]
    # The position equals the ONE fully-known row exactly — nothing zero-filled.
    assert (vnd["revenueNet"], vnd["cost"], vnd["profit"]) == (200.0, 90.0, 110.0)
    assert vnd["rowCount"] == 1
    assert vnd["incompleteRowCount"] == 1

    # Zero revenue is a real value: margin stays UNKNOWN, never a forced 0%.
    zero_rev = _report(shipments=[_ship_row("LO-9", "Khách Z", revenue=0.0, cost=10.0, profit=-10.0)])
    assert zero_rev["financeActual"]["positions"][0]["marginPct"] is None

    empty = _report()
    assert empty["financeActual"] == {"positions": [], "available": False}


def test_actionables_pass_through_only_real_task_projection_facts_bounded():
    """Bottleneck rows are the task projection's own facts, bounded, routed."""
    tasks = [
        {"id": f"OPS-LO-{i:03d}", "level": "CanXuLy", "lot": f"LO-{i:03d}",
         "customer": f"Khách {i}", "job": "Tài chính cần theo dõi",
         "dueNote": "CHỜ THU", "route": f"/lo-hang/LO-{i:03d}?tab=nhap"}
        for i in range(7)
    ] + [{"id": "OPS-OK", "level": "BinhThuong", "lot": "LO-999"}]
    report = _report(tasks=tasks)

    actionables = report["actionables"]
    assert len(actionables) == ceo_report.ACTIONABLE_LIMIT == 5
    assert [item["id"] for item in actionables] == [f"OPS-LO-{i:03d}" for i in range(5)]
    first = actionables[0]
    assert first == {
        "id": "OPS-LO-000",
        "level": "CanXuLy",
        "shipmentId": "LO-000",
        "customer": "Khách 0",
        "job": "Tài chính cần theo dõi",
        "detail": "CHỜ THU",
        "route": "/lo-hang/LO-000?tab=nhap",
    }
    # Every field is a pass-through of the input projection; nothing invented.
    for item in actionables:
        source = next(task for task in tasks if task["id"] == item["id"])
        assert item["shipmentId"] == source["lot"]
        assert item["customer"] == source["customer"]
        assert item["job"] == source["job"]
        assert item["detail"] == source["dueNote"]
        assert item["route"] == source["route"]
    # BinhThuong never counts as a bottleneck; nothing beyond the bound leaks.
    assert all(item["level"] in ceo_report.ACTIONABLE_TASK_LEVELS for item in actionables)
    assert all(item["id"] != "OPS-OK" for item in actionables)
    assert _report(tasks=[])["actionables"] == []


def test_top_customers_rank_within_single_currency_only():
    """Ranking uses actual revenue and never crosses a currency boundary."""
    report = _report(shipments=[
        _ship_row("LO-1", "Khách A", ccy="VND", revenue=100.0, customer_id="CUST-A"),
        _ship_row("LO-2", "Khách A", ccy="VND", revenue=50.0, customer_id="CUST-A"),
        _ship_row("LO-3", "Khách B", ccy="VND", revenue=120.0, customer_id="CUST-B"),
        _ship_row("LO-4", "Client C", ccy="USD", revenue=999.0),
        _ship_row("LO-5", "Khách D", ccy="VND", revenue=None),          # unknown revenue → excluded
        _ship_row("LO-6", "", ccy="VND", revenue=80.0),                  # unknown identity → excluded
        _ship_row("LO-7", "Khách E", ccy="VND", has_actual=False, revenue=None),
    ])

    groups = {group["currency"]: group for group in report["topCustomers"]}
    assert set(groups) == {"VND", "USD"}

    vnd = groups["VND"]["customers"]
    assert [item["name"] for item in vnd] == ["Khách A", "Khách B"]
    # Same customer's same-currency shipments aggregate; shipmentCount is real.
    assert vnd[0] == {"name": "Khách A", "revenueNet": 150.0, "shipmentCount": 2}
    assert vnd[1]["revenueNet"] == 120.0
    usd = groups["USD"]["customers"]
    assert usd == [{"name": "Client C", "revenueNet": 999.0, "shipmentCount": 1}]

    # No cross-currency ranking figure may exist anywhere in the report.
    numbers = set(_all_numbers(report))
    assert 150.0 + 999.0 not in numbers
    assert 120.0 + 999.0 not in numbers
    # A missing actual book is NOT ranked as revenue 0.
    assert 0.0 not in {item["revenueNet"] for item in vnd}
    assert _report()["topCustomers"] == []


def test_report_contains_no_donor_sample_values():
    """Donor mock KPI/bottleneck samples never appear in the real projection."""
    report = _report(
        shipments=[
            _ship_row("LO-1", "Khách A", revenue=100.0, cost=60.0, profit=40.0),
            {"id": "LO-2", "status": "Chờ thông quan"},
        ],
        tasks=[
            {"id": "OPS-LO-1", "level": "Khan", "lot": "LO-1", "customer": "Khách A",
             "job": "Quá hạn khách", "dueNote": "CHỜ THU", "route": "/lo-hang/LO-1?tab=nhap"},
        ],
    )
    rendered = __import__("json").dumps(report, ensure_ascii=False)
    for sample in DONOR_SAMPLE_VALUES:
        assert sample not in rendered, f"donor sample {sample!r} leaked into report"


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
