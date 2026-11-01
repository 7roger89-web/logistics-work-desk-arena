"""Issue #254 — Service debt at a glance on /lo-hang (desktop + mobile) + server finance_view boundary.

Covers both positive behavior and the explicit WRONG_PASS traps locked in Issue #254:
1. Quote-only shipment (no Finance Actual lines) must keep receivable/outstanding UNKNOWN (None -> "—"),
   never 0 VND, never quote estimate, and never "đã thanh toán đủ", even when received == 0 or > 0.
2. Server-side finance_view role boundary: actor without finance_view (e.g. Sale, Operations)
   must NOT receive finance actual / receivable / payment / payable / profit amounts in server
   projections (finance_projection, shipment_projection, build_view_model, post-write readback)
   and must NOT see the debt cluster on /lo-hang; Support / Accounting / Viewer / Admin do.
3. Recording (payment_record) and reversing/cancelling (payment_correction) a payment via the
   existing writer updates received and outstanding identically across core.logic, ShipmentDetail,
   and /lo-hang without stale cached values.
4. Multi-currency shipments (VND, USD, CNY) project per-shipment currency without FX conversion
   or cross-currency summation.
5. Customer portal (Lục Giác / HEXA, core/customer_journey.py) remains untouched with
   debt_summary.status == "UNKNOWN".
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess

import pytest

from types import SimpleNamespace

from core.auth import ROLE_PERMISSIONS, has_permission
from core.customer_journey import build_portal_model
from core.logic import calculate_from_shipment
from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm

ROOT = Path(__file__).resolve().parents[1]

SUPPORT_ACTOR = {
    "username": "staging.support",
    "full_name": "Support (Test)",
    "role": "support",
    "user_id": "STAGING-SUPPORT",
}
ACCOUNTING_ACTOR = {
    "username": "staging.accounting",
    "full_name": "Accounting (Test)",
    "role": "accounting",
    "user_id": "STAGING-ACCOUNTING",
}
VIEWER_ACTOR = {
    "username": "staging.viewer",
    "full_name": "Viewer (Test)",
    "role": "viewer",
    "user_id": "STAGING-VIEWER",
}
ADMIN_ACTOR = {
    "username": "staging.admin",
    "full_name": "Admin (Test)",
    "role": "admin",
    "user_id": "STAGING-ADMIN",
}
SALE_ACTOR = {
    "username": "staging.sale",
    "full_name": "Sale (Test)",
    "role": "sale",
    "user_id": "STAGING-SALE",
}
OPERATIONS_ACTOR = {
    "username": "staging.ops",
    "full_name": "Operations (Test)",
    "role": "operations",
    "user_id": "STAGING-OPS",
}


@pytest.fixture()
def staging():
    import streamlit as st

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(SUPPORT_ACTOR)
    yield transport
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


def _dispatch(seq_box: dict[str, int], event_name: str, payload: dict) -> dict:
    seq_box["n"] += 1
    outcomes = vm.consume_phase_b_triggers(
        {"seq": seq_box["n"] - 1},
        {event_name: {"seq": seq_box["n"], "event": event_name, "payload": payload}},
    )
    assert len(outcomes) == 1
    return outcomes[0]


def _seed_issue254_scenarios() -> dict[str, str]:
    """Seed deterministic multi-currency + quote-only + deposit-only lots in isolated mongomock."""
    from core.database import get_db

    db = get_db()
    base = copy.deepcopy(db.shipments.find_one({"id": "LO-0308"}, {"_id": 0}))
    assert base is not None

    # 1. Quote-only lot: positive linked quote (28,450,000 VND), zero Finance Actual lines, zero payments
    db.quotes.replace_one(
        {"id": "BG-254-QUOTE-ONLY"},
        {
            "id": "BG-254-QUOTE-ONLY",
            "quote_no": "BG-254-QUOTE-ONLY",
            "customer_id": base.get("customer_id", "CUST-ANPHAT"),
            "status": "ACCEPTED",
            "currency": "VND",
            "lines": [
                {"name": "Cước vận chuyển trọn gói", "qty": 1, "amount": 28_450_000, "currency": "VND", "vat": 0},
            ],
        },
        upsert=True,
    )
    quote_only = copy.deepcopy(base)
    quote_only["id"] = "LO-254-QUOTE"
    quote_only["quote_id"] = "BG-254-QUOTE-ONLY"
    quote_only["currency"] = "VND"
    quote_only["data"]["3.4"] = {"currency": "VND", "details": [], "payments": [], "commission": {"total": 0}}
    db.shipments.replace_one({"id": "LO-254-QUOTE"}, quote_only, upsert=True)

    # 2. Deposit-only lot: customer paid 12,300,000 VND advance, still zero Finance Actual lines
    deposit_only = copy.deepcopy(base)
    deposit_only["id"] = "LO-254-DEPOSIT"
    deposit_only["quote_id"] = "BG-254-QUOTE-ONLY"
    deposit_only["currency"] = "VND"
    deposit_only["data"]["3.4"] = {
        "currency": "VND",
        "details": [],
        "payments": [
            {"id": "PAY-DEP-254", "amount": 12_300_000, "date": "2026-10-15", "note": "Tạm ứng", "status": "confirmed"},
        ],
        "commission": {"total": 0},
    }
    db.shipments.replace_one({"id": "LO-254-DEPOSIT"}, deposit_only, upsert=True)

    # 3. USD lot with Finance Actual lines: receivable = 2,400 USD, received = 900 USD, outstanding = 1,500 USD
    usd_lot = copy.deepcopy(base)
    usd_lot["id"] = "LO-254-USD"
    usd_lot["currency"] = "USD"
    usd_lot["data"]["3.4"] = {
        "currency": "USD",
        "details": [
            {"id": "ACT-USD-1", "name": "Ocean Freight", "qty": 1, "price": 2400, "vat": 0, "cost": 1950, "currency": "USD"},
        ],
        "payments": [
            {"id": "PAY-USD-1", "amount": 900, "date": "2026-10-18", "note": "Partial USD receipt", "status": "confirmed"},
        ],
        "commission": {"total": 0},
    }
    db.shipments.replace_one({"id": "LO-254-USD"}, usd_lot, upsert=True)

    # 4. CNY lot with Finance Actual settled + a reversed historical receipt that must NOT double count
    cny_lot = copy.deepcopy(base)
    cny_lot["id"] = "LO-254-CNY"
    cny_lot["currency"] = "CNY"
    cny_lot["data"]["3.4"] = {
        "currency": "CNY",
        "details": [
            {"id": "ACT-CNY-1", "name": "Inland trucking CN", "qty": 1, "price": 18000, "vat": 0, "cost": 14200, "currency": "CNY"},
        ],
        "payments": [
            {"id": "PAY-CNY-OLD", "amount": 5000, "date": "2026-10-10", "note": "Nhầm khoản", "status": "reversed", "is_reversed": True},
            {"id": "PAY-CNY-OK", "amount": 18000, "date": "2026-10-19", "note": "Thu đủ CNY", "status": "confirmed"},
        ],
        "commission": {"total": 0},
    }
    db.shipments.replace_one({"id": "LO-254-CNY"}, cny_lot, upsert=True)

    return {
        "vndActual": "LO-0308",
        "quoteOnly": "LO-254-QUOTE",
        "depositNoActual": "LO-254-DEPOSIT",
        "usdActual": "LO-254-USD",
        "cnySettled": "LO-254-CNY",
    }


def test_rbac_matrix_finance_view_membership_is_unchanged():
    """Verify existing ROLE_PERMISSIONS contract without adding or mutating permissions."""
    import streamlit as st

    assert "*" in ROLE_PERMISSIONS["admin"]
    for allowed_role in ("support", "accounting", "viewer"):
        assert "finance_view" in ROLE_PERMISSIONS[allowed_role]
    for denied_role in ("sale", "sales", "operations"):
        assert "finance_view" not in ROLE_PERMISSIONS[denied_role]

    for actor, expected in (
        (ADMIN_ACTOR, True),
        (SUPPORT_ACTOR, True),
        (ACCOUNTING_ACTOR, True),
        (VIEWER_ACTOR, True),
        (SALE_ACTOR, False),
        (OPERATIONS_ACTOR, False),
    ):
        st.session_state["current_user"] = dict(actor)
        assert has_permission("finance_view") is expected


def test_unknown_not_zero_and_quote_never_leaks_into_service_debt(staging):
    """Quote-only or deposit-only shipments without Finance Actual keep receivable & outstanding None."""
    ids = _seed_issue254_scenarios()
    built = vm.build_view_model()
    by_id = {row["id"]: row for row in built["shipments"]}

    quote_row = by_id[ids["quoteOnly"]]
    assert quote_row["finance"]["hasActualLines"] is False
    assert quote_row["finance"]["quote"] and quote_row["finance"]["quote"][0]["amount"] == 28_450_000.0
    assert quote_row["finance"]["receivable"] is None
    assert quote_row["finance"]["outstanding"] is None
    assert quote_row["finance"]["received"] == 0.0

    deposit_row = by_id[ids["depositNoActual"]]
    assert deposit_row["finance"]["hasActualLines"] is False
    assert deposit_row["finance"]["receivable"] is None
    assert deposit_row["finance"]["outstanding"] is None
    assert deposit_row["finance"]["received"] == 12_300_000.0


def test_server_side_finance_view_boundary_blocks_sale_and_allows_support(staging):
    """Sale (no finance_view) must NOT receive finance_view money fields anywhere in server payload."""
    import streamlit as st

    ids = _seed_issue254_scenarios()

    for actor in (SUPPORT_ACTOR, ACCOUNTING_ACTOR, VIEWER_ACTOR, ADMIN_ACTOR):
        st.session_state["current_user"] = dict(actor)
        allowed_vm = vm.build_view_model()
        assert allowed_vm["user"]["canViewFinance"] is True
        vnd = next(r for r in allowed_vm["shipments"] if r["id"] == ids["vndActual"])
        expected = calculate_from_shipment(vm.read_shipment(ids["vndActual"]))
        assert vnd["finance"]["canView"] is True
        assert vnd["finance"]["receivable"] == expected["receivable"] > 0
        assert vnd["finance"]["received"] == expected["paid"]
        assert vnd["finance"]["outstanding"] == expected["debt"]

    for denied_actor in (SALE_ACTOR, OPERATIONS_ACTOR):
        st.session_state["current_user"] = dict(denied_actor)
        denied_vm = vm.build_view_model()
        assert denied_vm["user"]["canViewFinance"] is False
        assert denied_vm["home"]["outstandingTotal"] is None
        assert denied_vm["home"]["outstandingCount"] == 0
        assert denied_vm["home"]["summary"]["financialAttention"] == 0
        assert denied_vm["receivables"] == {"rows": [], "totals": {}}
        assert denied_vm["payables"]["rows"] == []
        assert denied_vm["payables"]["totals"] == {}
        assert denied_vm["reconciliation"]["rows"] == []
        assert denied_vm["reconciliation"]["totals"] == {}

        for row in denied_vm["shipments"]:
            fin = row["finance"]
            assert fin["canView"] is False
            assert fin["hasActualLines"] is False
            for money_key in (
                "receivable",
                "received",
                "receivableNet",
                "outputVat",
                "outstanding",
                "payable",
                "paid",
                "commission",
                "profit",
                "profitMargin",
            ):
                assert fin[money_key] is None, f"{denied_actor['role']} leaked {money_key} on {row['id']}"
            assert fin["actual"] == []
            assert fin["payments"] == []
            assert fin["partner"]["payable"] is None
            assert fin["partner"]["paid"] is None
            assert fin["partner"]["remaining"] is None
            assert fin["partner"]["payments"] == []

        # Post-write readback (_projection_for) for Sale must ALSO stay gated
        readback = vm._projection_for(vm.read_shipment(ids["vndActual"]))
        assert readback["finance"]["canView"] is False
        assert readback["finance"]["receivable"] is None
        assert readback["finance"]["received"] is None
        assert readback["finance"]["outstanding"] is None
        assert readback["finance"]["actual"] == []
        assert readback["finance"]["payments"] == []


def test_payment_record_and_reversal_update_projection_without_stale_balance(staging):
    """Recording then reversing a receipt via canonical writers updates received & outstanding."""
    ids = _seed_issue254_scenarios()
    seq = {"n": 0}
    sid = ids["vndActual"]

    before_ship = vm.read_shipment(sid)
    before_calc = calculate_from_shipment(before_ship)
    assert before_calc["receivable"] > 50_000_000
    assert before_calc["paid"] == 0.0

    # 1. Record 50,000,000 VND receipt
    rec_out = _dispatch(seq, "payment_record", {
        "shipmentId": sid,
        "amount": 50_000_000,
        "requestId": "PAY-254-1",
        "date": "2026-10-20",
        "note": "Thu đợt 1",
    })
    assert rec_out["ok"] is True

    after_pay_vm = vm.build_view_model()
    after_pay_row = next(r for r in after_pay_vm["shipments"] if r["id"] == sid)
    after_pay_calc = calculate_from_shipment(vm.read_shipment(sid))
    assert after_pay_row["finance"]["received"] == 50_000_000.0 == after_pay_calc["paid"]
    assert after_pay_row["finance"]["outstanding"] == before_calc["receivable"] - 50_000_000.0 == after_pay_calc["debt"]

    # 2. Reverse that exact payment via payment_correction
    payment_id = next(
        p["id"] for p in after_pay_row["finance"]["payments"] if p.get("requestId") == "PAY-254-1"
    )
    rev_out = _dispatch(seq, "payment_correction", {
        "shipmentId": sid,
        "paymentId": payment_id,
        "correctionRequestId": "CORR-254-1",
        "reason": "Khách chuyển nhầm tài khoản, hoàn trả",
    })
    assert rev_out["ok"] is True

    after_rev_vm = vm.build_view_model()
    after_rev_row = next(r for r in after_rev_vm["shipments"] if r["id"] == sid)
    after_rev_calc = calculate_from_shipment(vm.read_shipment(sid))
    assert after_rev_row["finance"]["received"] == 0.0 == after_rev_calc["paid"]
    assert after_rev_row["finance"]["outstanding"] == before_calc["receivable"] == after_rev_calc["debt"]


def test_customer_portal_hexa_remains_out_of_scope_unknown(staging):
    """Lục Giác / HEXA customer portal keeps debt_summary.status == UNKNOWN with zero leaked amounts."""
    from core.database import get_db

    _seed_issue254_scenarios()
    db = get_db()
    ship = db.shipments.find_one({"id": "LO-0308"}, {"_id": 0})
    card_stub = SimpleNamespace(
        reference=ship["id"],
        transport_mode="Road",
        cargo_summary="Máy móc",
        route_summary="Thẩm Quyến → Hữu Nghị",
        events=(),
        documents=(),
        publication={"published": True, "approved_at": "2026-10-20"},
        contact_point={},
        next_step={},
    )
    view_stub = SimpleNamespace(
        principal=SimpleNamespace(display_name="Lục Giác"),
        cards=(card_stub,),
        denied_lots=0,
        data_issues=0,
    )
    portal = build_portal_model(view_stub)
    assert len(portal["lots"]) == 1
    lot = portal["lots"][0]
    assert lot["debt_summary"] == {"status": "UNKNOWN", "currency": "VND"}
    assert lot["finance_detail"] is None
    assert lot["quote"] is None
    for forbidden_key in ("receivable", "received", "outstanding", "finance", "payable", "profit"):
        assert forbidden_key not in lot


def test_shipments_list_dom_bundle_acceptance(staging):
    """Run the real built bundle against live Python ViewModel snapshots (Support + Sale + reversal)."""
    import streamlit as st

    ids = _seed_issue254_scenarios()
    seq = {"n": 0}
    sid = ids["vndActual"]

    st.session_state["current_user"] = dict(SUPPORT_ACTOR)
    support_initial = vm.build_view_model()
    vnd_before = next(r for r in support_initial["shipments"] if r["id"] == sid)["finance"]
    rec_val = int(round(vnd_before["receivable"]))
    fmt_vn = lambda n: f"{int(round(n)):,}".replace(",", ".")

    out_pay = _dispatch(seq, "payment_record", {
        "shipmentId": sid,
        "amount": 50_000_000,
        "requestId": "DOM-PAY-254-1",
        "date": "2026-10-20",
        "note": "Thu tiền khách",
    })
    assert out_pay["ok"] is True
    support_after_payment = vm.build_view_model()
    payment_id = next(
        p["id"]
        for r in support_after_payment["shipments"]
        if r["id"] == sid
        for p in r["finance"]["payments"]
        if p.get("requestId") == "DOM-PAY-254-1"
    )

    out_rev = _dispatch(seq, "payment_correction", {
        "shipmentId": sid,
        "paymentId": payment_id,
        "correctionRequestId": "DOM-CORR-254-1",
        "reason": "Huỷ phiếu thu nhầm",
    })
    assert out_rev["ok"] is True
    support_after_reversal = vm.build_view_model()

    # Re-record a receipt so the DB has live non-zero received AND outstanding when Sale loads /lo-hang
    out_pay2 = _dispatch(seq, "payment_record", {
        "shipmentId": sid,
        "amount": 50_000_000,
        "requestId": "DOM-PAY-254-2",
        "date": "2026-10-21",
        "note": "Thu lại đợt 1",
    })
    assert out_pay2["ok"] is True

    st.session_state["current_user"] = dict(SALE_ACTOR)
    sale_view = vm.build_view_model()

    payload = {
        "ids": ids,
        "supportInitial": support_initial,
        "supportAfterPayment": support_after_payment,
        "supportAfterReversal": support_after_reversal,
        "saleView": sale_view,
        "forbiddenQuoteFormatted": "28.450.000",
        "secretFiguresForSale": [
            fmt_vn(rec_val),
            fmt_vn(rec_val - 50_000_000),
            "2.400 USD",
            "1.500 USD",
            "18.000 CNY",
        ],
        "expected": {
            "vndInitial": {
                "receivable": f"{fmt_vn(rec_val)} VND",
                "received": "0 VND",
                "outstanding": f"{fmt_vn(rec_val)} VND",
            },
            "vndAfterPayment": {
                "receivable": f"{fmt_vn(rec_val)} VND",
                "received": "50.000.000 VND",
                "outstanding": f"{fmt_vn(rec_val - 50_000_000)} VND",
            },
            "depositNoActual": {
                "received": "12.300.000 VND",
            },
        },
    }

    proc = subprocess.run(
        ["node", str(ROOT / "tests/component/dom_acceptance_issue254_shipment_debt.mjs")],
        input=json.dumps(payload, ensure_ascii=False, default=str),
        text=True,
        capture_output=True,
        cwd=str(ROOT),
        timeout=60,
        check=False,
    )
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "DOM_ACCEPTANCE_ISSUE254=PASS" in proc.stdout
