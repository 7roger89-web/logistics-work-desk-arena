"""LOGI-255-LASTWRITES-ISOLATION — lastWrites chi den dung actor/role da ghi.

WRONG_PASS: ket qua write trong ``lastWrites`` duoc tra cho BAT KY actor nao dang
dung cung session (mien la con quyen), hoac cho chinh account do sau khi bi ha
quyen. So tien / readback gia von cua nguoi ghi truoc do van nam trong payload
cua nguoi sau.

Cac test duoi day chi dung boundary THAT trong app: ``vm.dispatch()`` luu outcome
vao ``LAST_WRITES_KEY``, roi ``vm.build_view_model()`` dung payload. Khong co
helper nao ghi thang vao session state de "chung minh" filter.

A. Support A ghi tien -> Support B (cung quyen) dang nhap cung session: B khong
   nhan outcome cua A.
B. Support ghi tien -> chinh account do ha xuong Sale: khong nhan outcome tai
   chinh cu.
C. Support tao outcome ``cost_rate_save`` co readback gia von -> doi sang Sale:
   khong nhan readback gia von cu.
D. Support hop le, khong doi actor/role: van nhan dung outcome, requestId va
   readback (khong bi chan oan, khong lo field noi bo).
E. Sau khi actor moi tu ghi, chi outcome cua chinh actor moi duoc tra.
"""

from __future__ import annotations

import json

import pytest
import streamlit as st

from views import logi_sandbox
from views import logi_view_model as vm

from tests.test_issue254_shipment_debt_glance import _seed_issue254_scenarios  # noqa: E402

LAST_WRITES_KEY = vm.LAST_WRITES_KEY
PROVENANCE_KEY = "_provenance"
SID = "LO-0308"
AMOUNT = 35_000_000
COST_AMOUNT = 4250.0

SUPPORT_A = {
    "username": "qa.s255.support.a",
    "full_name": "Support A (Test)",
    "role": "support",
    "user_id": "QA-S255-SUPPORT-A",
}
SUPPORT_B = {
    "username": "qa.s255.support.b",
    "full_name": "Support B (Test)",
    "role": "support",
    "user_id": "QA-S255-SUPPORT-B",
}
# Cung account Support A nhung bi ha xuong Sale (khong doi username/user_id).
SALE_SAME_ACCOUNT = dict(SUPPORT_A, role="sale")


@pytest.fixture()
def staging255iso(monkeypatch):
    """Mongomock staging trong + session trong; actor hien tai = Support A."""
    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state.clear()
    # dispatch() yeu cau ONE rerun; trong test chi can ghi nhan, khong rerun that.
    monkeypatch.setattr(st, "rerun", lambda: None)
    st.session_state["current_user"] = dict(SUPPORT_A)
    yield
    st.session_state.clear()
    logi_sandbox.reset_backend()


def _payment_payload(request_id: str) -> dict:
    return {
        "shipmentId": SID,
        "amount": AMOUNT,
        "requestId": request_id,
        "date": "2026-11-01",
        "note": "Thu tien dich vu (S255 isolation)",
    }


def _cost_rate_payload(request_id: str) -> dict:
    """Snapshot giao vận có giá vốn thật (USD) — readback mang so tien."""
    return {
        "requestId": request_id,
        "supplier": "Hang tau S255",
        "rawText": "SHANGHAI -> HANOI 4.250 USD/40HC",
        "status": "ACTIVE",
        "rows": [
            {
                "id": "line-1",
                "kind": "OCEAN_FREIGHT",
                "status": "QUOTED",
                "amount": COST_AMOUNT,
                "currency": "USD",
                "unit": "40HC",
                "carrier": {"id": "CARR-S255", "name": "Hang tau S255", "state": "CONFIRMED"},
                "origin": {"id": "SHA", "name": "Shanghai", "state": "UNKNOWN"},
                "destination": {"id": "HAN", "name": "Hanoi", "state": "UNKNOWN"},
                "rawLine": "SHANGHAI -> HANOI 4.250 USD/40HC",
                "confidence": "CONFIRMED",
            }
        ],
    }


def _write(seq_box: dict, events: dict[str, dict]) -> list[dict]:
    """Gui trigger THẬT qua vm.dispatch(); tra outcomes da duoc luu doc lap.

    Moi event mang MOT seq tang dan rieng (nhu component that): dispatcher dung
    chung mot bo dem seq cho phase B va C1 nen hai event trung seq se bi coi la
    replay va event thu hai bi bo qua.
    """
    result = {}
    for event, payload in events.items():
        seq_box["n"] += 1
        result[event] = {"seq": seq_box["n"], "event": event, "payload": payload}
    return vm.dispatch(result)


def _by_event(outcomes: list[dict]) -> dict[str, dict]:
    return {str(out.get("event")): out for out in outcomes}


# ---------------------------------------------------------------- A (negative)
def test_support_b_same_session_never_receives_support_a_outcome(staging255iso):
    """A. Support A ghi tien -> Support B (cung quyen) khong nhan outcome cua A."""
    _seed_issue254_scenarios()
    seq = {"n": 0}

    pay_a = _write(seq, {"payment_record": _payment_payload("PAY-255-A-1")})
    outcome_a = _by_event(pay_a)["payment_record"]
    assert outcome_a["ok"] is True, outcome_a
    assert st.session_state[LAST_WRITES_KEY], "dispatch() phai luu outcome truoc rerun"

    # Cung session: doi sang mot account Support KHAC, van du quyen tai chinh.
    st.session_state["current_user"] = dict(SUPPORT_B)
    model_b = vm.build_view_model()
    assert model_b["user"]["canViewFinance"] is True, "B cung quyen nhu A"

    writes_b = model_b["lastWrites"]
    assert writes_b == [], (
        "Support B khong duoc nhan bat ky outcome nao cua Support A: "
        f"{[(w.get('event'), w.get('requestId')) for w in writes_b]}"
    )
    # Pham vi task = kenh lastWrites. Du lieu so cai tren chinh lo (finance block
    # cua shipment) van den B qua projection doc-only vi B CO finance_view —
    # do la ledger that, khong phai outcome cua A.
    assert "PAY-255-A-1" not in json.dumps(writes_b, default=str)
    assert str(AMOUNT) not in json.dumps(writes_b, default=str)


# ---------------------------------------------------------------- B (negative)
def test_downgraded_sale_same_account_does_not_receive_finance_outcome(staging255iso):
    """B. Support ghi tien -> cung account ha xuong Sale: khong nhan outcome cu."""
    _seed_issue254_scenarios()
    seq = {"n": 0}

    pay = _write(seq, {"payment_record": _payment_payload("PAY-255-B-1")})
    assert _by_event(pay)["payment_record"]["ok"] is True

    st.session_state["current_user"] = dict(SALE_SAME_ACCOUNT)
    model = vm.build_view_model()
    assert model["user"]["canViewFinance"] is False

    writes = model["lastWrites"]
    assert not any(w.get("event") == "payment_record" for w in writes)
    for row in writes:
        persisted = row.get("persisted") or {}
        readback = row.get("readback") or {}
        assert "amount" not in persisted
        assert "derivedPaid" not in persisted
        assert "derivedDebt" not in persisted
        assert not (readback.get("finance") or {})
    assert "PAY-255-B-1" not in json.dumps(writes, default=str)
    # Sale khong con finance_view -> ca payload khong con so tien cua khoan thu.
    assert "PAY-255-B-1" not in json.dumps(model, default=str)
    assert str(AMOUNT) not in json.dumps(model, default=str)


# ---------------------------------------------------------------- C (negative)
def test_cost_rate_readback_not_delivered_to_sale_same_session(staging255iso):
    """C. ``cost_rate_save`` co readback gia von -> Sale khong nhan readback cu."""
    seq = {"n": 0}

    saved = _write(seq, {"cost_rate_save": _cost_rate_payload("COST-255-C-1")})
    outcome = _by_event(saved)["cost_rate_save"]
    assert outcome["ok"] is True, outcome
    assert (outcome.get("readback") or {}).get("rows")[0]["amount"] == COST_AMOUNT, (
        "readback that phai mang gia von cua snapshot vua luu"
    )

    # Support (khong doi actor/role) van doc duoc readback cua chinh minh.
    support_model = vm.build_view_model()
    support_costs = [w for w in support_model["lastWrites"] if w.get("event") == "cost_rate_save"]
    assert support_costs and support_costs[0]["requestId"] == "COST-255-C-1"
    assert support_costs[0]["readback"]["rows"][0]["amount"] == COST_AMOUNT

    # Cung session, ha xuong Sale: khong con readback gia von cua Support.
    st.session_state["current_user"] = dict(SALE_SAME_ACCOUNT)
    sale_model = vm.build_view_model()
    assert sale_model["user"]["canViewFinance"] is False
    sale_writes = sale_model["lastWrites"]
    assert sale_writes == [], (
        "Sale khong duoc nhan outcome gia von cua actor truoc: "
        f"{[(w.get('event'), w.get('requestId')) for w in sale_writes]}"
    )
    assert "COST-255-C-1" not in json.dumps(sale_writes, default=str)
    assert "4.250 USD/40HC" not in json.dumps(sale_writes, default=str)
    # Ghi nhan (khong sua trong task nay): projection doc-only `costIntelligence`
    # van tra snapshot gia von cho moi role, ke ca Sale — do la be mat KHAC voi
    # kenh lastWrites va thuoc quyet dinh quyen cua Owner, khong nam trong
    # LOGI-255-LASTWRITES-ISOLATION.


# ---------------------------------------------------------------- D (positive)
def test_unchanged_actor_keeps_outcome_requestid_and_readback(staging255iso):
    """D. Support hop le, khong doi actor/role: van nhan dung outcome day du."""
    _seed_issue254_scenarios()
    seq = {"n": 0}

    outcomes = _write(seq, {
        "payment_record": _payment_payload("PAY-255-D-1"),
        "cost_rate_save": _cost_rate_payload("COST-255-D-1"),
    })
    by_event = _by_event(outcomes)
    assert by_event["payment_record"]["ok"] is True, by_event
    assert by_event["cost_rate_save"]["ok"] is True, by_event

    model = vm.build_view_model()
    assert model["user"]["canViewFinance"] is True
    writes = {w.get("event"): w for w in model["lastWrites"]}

    assert writes["payment_record"]["requestId"] == "PAY-255-D-1"
    assert writes["payment_record"]["ok"] is True
    assert writes["payment_record"]["persisted"]["amount"] == float(AMOUNT)
    assert (writes["payment_record"].get("readback") or {}).get("finance") or writes[
        "payment_record"
    ].get("readback") is not None

    assert writes["cost_rate_save"]["requestId"] == "COST-255-D-1"
    assert writes["cost_rate_save"]["readback"]["rows"][0]["amount"] == COST_AMOUNT

    # Field noi bo cua provenance khong duoc ro ri vao payload component.
    for row in model["lastWrites"]:
        assert PROVENANCE_KEY not in row


# ---------------------------------------------------------------- E (positive)
def test_new_actor_gets_only_its_own_outcome_after_own_write(staging255iso):
    """E. Sau khi actor moi tu ghi, chi outcome cua chinh actor moi duoc tra."""
    _seed_issue254_scenarios()
    seq = {"n": 0}

    _write(seq, {"payment_record": _payment_payload("PAY-255-E-A")})
    st.session_state["current_user"] = dict(SUPPORT_B)

    before_write = vm.build_view_model()
    assert before_write["lastWrites"] == [], "outcome cua A khong duoc ke thua"

    pay_b = _write(seq, {"payment_record": _payment_payload("PAY-255-E-B")})
    assert _by_event(pay_b)["payment_record"]["ok"] is True

    model = vm.build_view_model()
    request_ids = [w.get("requestId") for w in model["lastWrites"]]
    assert request_ids == ["PAY-255-E-B"], request_ids
