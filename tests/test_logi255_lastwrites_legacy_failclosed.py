"""LOGI-255-LEGACY-FAILCLOSED — row khong chung minh duoc danh tinh/quyen thi khong giao.

WRONG_PASS (do o slice nay): ``_last_writes_for_actor`` giu lai duong fail-open cho
row KHONG co ``_provenance`` — ``delivered.append(row)``. Vi vay mot row legacy con
trong ``LAST_WRITES_KEY`` (session dang mo khi nang cap code, fixture/script ghi
thang) van duoc giao cho BAT KY actor nao dang dung session, va cho ca event khong
nam trong ``FINANCE_WRITE_EVENTS`` (``cost_rate_save`` mang readback gia von).

Phep thu phan biet: Support A ghi 35.000.000 VND (``payment_record``) + mot
``cost_rate_save`` qua ``dispatch()``, bo ``_provenance`` de mo phong row legacy,
doi sang Support B / Sale cung session -> ``lastWrites`` phai la ``[]``.

Cac test duoi day di qua boundary THAT: ``vm.dispatch()`` cho ca positive lan
negative (negative chi bo key provenance da luu, khong tu che outcome). Khong co
helper nao ghi thang outcome "thanh cong" vao session state.
"""

from __future__ import annotations

import json

import pytest
import streamlit as st

from views import logi_sandbox
from views import logi_view_model as vm

from tests.test_issue254_shipment_debt_glance import _seed_issue254_scenarios  # noqa: E402

LAST_WRITES_KEY = vm.LAST_WRITES_KEY
PROVENANCE_KEY = vm.LAST_WRITES_PROVENANCE
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
SALE_SAME_ACCOUNT = dict(SUPPORT_A, role="sale")


@pytest.fixture()
def staging255legacy(monkeypatch):
    """Mongomock staging trong + session trong; actor hien tai = Support A."""
    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state.clear()
    monkeypatch.setattr(st, "rerun", lambda: None)
    st.session_state["current_user"] = dict(SUPPORT_A)
    yield
    st.session_state.clear()
    logi_sandbox.reset_backend()


def _payment_payload(request_id: str, amount: float = AMOUNT) -> dict:
    return {
        "shipmentId": SID,
        "amount": amount,
        "requestId": request_id,
        "date": "2026-11-01",
        "note": "Thu tien dich vu (S255 legacy closure)",
    }


def _cost_rate_payload(request_id: str) -> dict:
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
    """Gui trigger THAT qua ``vm.dispatch()`` (moi event mot seq rieng)."""
    triggers = {}
    for event, payload in events.items():
        seq_box["n"] += 1
        triggers[event] = {"seq": seq_box["n"], "event": event, "payload": payload}
    return vm.dispatch(triggers, allow_rerun=False)


def _by_event(outcomes: list[dict]) -> dict[str, dict]:
    return {str(out.get("event")): out for out in outcomes}


def _drop_provenance() -> int:
    """Mo phong row legacy: bo key provenance da duoc dispatch() gan khi luu."""
    rows = st.session_state.get(LAST_WRITES_KEY) or []
    dropped = 0
    for row in rows:
        if isinstance(row, dict) and PROVENANCE_KEY in row:
            del row[PROVENANCE_KEY]
            dropped += 1
    return dropped


# ------------------------------------------------------- N1 (negative, fail-open)
def test_legacy_rows_without_provenance_not_delivered_to_support_b(staging255legacy):
    """N1. Support A ghi tien + gia von -> bo provenance -> Support B: lastWrites []."""
    _seed_issue254_scenarios()
    seq = {"n": 0}

    outcomes = _write(seq, {
        "payment_record": _payment_payload("PAY-255-LEGACY-A"),
        "cost_rate_save": _cost_rate_payload("COST-255-LEGACY-A"),
    })
    by_event = _by_event(outcomes)
    assert by_event["payment_record"]["ok"] is True, by_event
    assert by_event["cost_rate_save"]["ok"] is True, by_event
    assert all(PROVENANCE_KEY in row for row in st.session_state[LAST_WRITES_KEY]), (
        "dispatch() phai gan provenance truoc khi luu"
    )

    assert _drop_provenance() == len(st.session_state[LAST_WRITES_KEY])

    st.session_state["current_user"] = dict(SUPPORT_B)
    model = vm.build_view_model()
    assert model["user"]["canViewFinance"] is True, "Support B cung quyen nhu Support A"

    writes = model["lastWrites"]
    assert writes == [], (
        "Row khong co provenance khong duoc giao cho Support B: "
        f"{[(w.get('event'), w.get('requestId')) for w in writes]}"
    )
    payload = json.dumps(writes, default=str)
    assert "PAY-255-LEGACY-A" not in payload
    assert str(AMOUNT) not in payload
    assert "COST-255-LEGACY-A" not in payload
    assert "4.250 USD/40HC" not in payload


# ------------------------------------------------------- N2 (negative, fail-open)
def test_legacy_rows_without_provenance_not_delivered_to_sale(staging255legacy):
    """N2. Support A ghi tien + gia von -> bo provenance -> Sale cung session: []."""
    _seed_issue254_scenarios()
    seq = {"n": 0}

    outcomes = _write(seq, {
        "payment_record": _payment_payload("PAY-255-LEGACY-B"),
        "cost_rate_save": _cost_rate_payload("COST-255-LEGACY-B"),
    })
    assert _by_event(outcomes)["payment_record"]["ok"] is True
    assert _by_event(outcomes)["cost_rate_save"]["ok"] is True
    assert _drop_provenance() == len(st.session_state[LAST_WRITES_KEY])

    st.session_state["current_user"] = dict(SALE_SAME_ACCOUNT)
    model = vm.build_view_model()
    assert model["user"]["canViewFinance"] is False

    writes = model["lastWrites"]
    assert writes == [], (
        "Ke ca event khong mang tien (cost_rate_save) cung khong duoc giao cho Sale "
        f"khi row khong co provenance: {[(w.get('event'), w.get('requestId')) for w in writes]}"
    )
    payload = json.dumps(writes, default=str)
    assert "PAY-255-LEGACY-B" not in payload
    assert str(AMOUNT) not in payload
    assert "COST-255-LEGACY-B" not in payload
    assert "4.250 USD/40HC" not in payload


# ------------------------------------- N3 (negative, provenance khong hop le/rong)
@pytest.mark.parametrize("provenance", [
    {"actor": "", "userId": "", "role": ""},
    {},
    "qa.s255.support.a",
    {"actor": "qa.s255.support.a", "role": "support"},
    {"actor": "qa.s255.support.a", "userId": "QA-S255-SUPPORT-A", "role": "sale"},
])
def test_invalid_provenance_never_delivers_legacy_row(staging255legacy, provenance):
    """N3. Provenance rong/khong phai Mapping/thieu field/lech role -> khong giao."""
    _seed_issue254_scenarios()
    st.session_state["current_user"] = dict(SUPPORT_A)
    st.session_state[LAST_WRITES_KEY] = [{
        "event": "cost_rate_save",
        "shipmentId": SID,
        "ok": True,
        "requestId": "COST-255-LEGACY-C",
        "readback": {"rows": [{"amount": COST_AMOUNT, "currency": "USD"}]},
        PROVENANCE_KEY: provenance,
    }]

    model = vm.build_view_model()
    writes = model["lastWrites"]
    assert writes == [], (
        "Provenance khong chung minh duoc danh tinh/quyen thi khong duoc giao row: "
        f"{provenance!r} -> {[(w.get('event'), w.get('requestId')) for w in writes]}"
    )
    assert "COST-255-LEGACY-C" not in json.dumps(writes, default=str)


def test_empty_role_is_not_identity_proof(staging255legacy):
    """N3b. Role trong (username trung) KHONG phai bang chung cung danh tinh/quyen."""
    _seed_issue254_scenarios()
    st.session_state[LAST_WRITES_KEY] = [{
        "event": "cost_rate_save",
        "shipmentId": SID,
        "ok": True,
        "requestId": "COST-255-LEGACY-D",
        "readback": {"rows": [{"amount": COST_AMOUNT, "currency": "USD"}]},
        PROVENANCE_KEY: {"actor": SUPPORT_A["username"], "userId": SUPPORT_A["user_id"], "role": ""},
    }]
    # Cung username/userId nhung role rong: "rong" khong duoc coi la "khop quyen".
    st.session_state["current_user"] = {
        "username": SUPPORT_A["username"],
        "user_id": SUPPORT_A["user_id"],
        "role": "",
    }

    model = vm.build_view_model()
    writes = model["lastWrites"]
    assert writes == [], (
        "Role trong khong phai bang chung danh tinh/quyen: "
        f"{[(w.get('event'), w.get('requestId')) for w in writes]}"
    )


# ------------------------------------------------------------- P1 (positive)
def test_valid_support_actor_still_receives_full_readback(staging255legacy):
    """P1. Support A khong doi danh tinh/quyen: van nhan du requestId/readback/status."""
    _seed_issue254_scenarios()
    seq = {"n": 0}

    outcomes = _write(seq, {
        "payment_record": _payment_payload("PAY-255-LEGACY-P"),
        "cost_rate_save": _cost_rate_payload("COST-255-LEGACY-P"),
    })
    by_event = _by_event(outcomes)
    assert by_event["payment_record"]["ok"] is True, by_event
    assert by_event["cost_rate_save"]["ok"] is True, by_event

    model = vm.build_view_model()
    assert model["user"]["canViewFinance"] is True
    writes = {w.get("event"): w for w in model["lastWrites"]}

    payment = writes["payment_record"]
    assert payment["requestId"] == "PAY-255-LEGACY-P"
    assert payment["ok"] is True
    assert payment["shipmentId"] == SID
    assert payment["persisted"]["amount"] == float(AMOUNT)
    assert payment["readback"] is not None
    assert payment["error"] == "Đã ghi nhận khoản thu."

    cost = writes["cost_rate_save"]
    assert cost["requestId"] == "COST-255-LEGACY-P"
    assert cost["readback"]["rows"][0]["amount"] == COST_AMOUNT

    for row in model["lastWrites"]:
        assert PROVENANCE_KEY not in row, "Key noi bo khong duoc ro ri vao payload"


# ------------------------------------------------------------- P2 (positive)
def test_refused_write_still_reaches_its_own_actor(staging255legacy):
    """P2. Ket qua ghi THAT BAI cua chinh actor van duoc bao (khong bi chan oan)."""
    _seed_issue254_scenarios()
    seq = {"n": 0}

    outcomes = _write(seq, {"payment_record": _payment_payload("PAY-255-LEGACY-F", amount=0)})
    refused = _by_event(outcomes)["payment_record"]
    assert refused["ok"] is False, refused

    model = vm.build_view_model()
    writes = [w for w in model["lastWrites"] if w.get("requestId") == "PAY-255-LEGACY-F"]
    assert len(writes) == 1, model["lastWrites"]
    assert writes[0]["ok"] is False
    assert writes[0]["error"] == "Số tiền thanh toán phải lớn hơn 0."
