"""LOGI_CUSTOMER_PAYMENT_CORRECTION_UI_01 — canonical payment correction/reversal.

Turns the decorative "Điều chỉnh" action into the REAL canonical workflow:

    React → payment_correction → existing dispatcher
    → existing RBAC + save_direct_payment_correction (canonical writer)
    → financial_corrections + audit(payment_reversed) + shipment.payment_reversed
    → fresh readback.

Acceptance proven here (writer semantics, NOT an invented replacement model):

 1. create one customer payment;
 2. correction/reversal against it succeeds;
 3. the original payment record still exists (same id/amount/date — the writer
    only marks it reversed; it is never deleted and its money facts stay);
 4. a correction record exists in financial_corrections linked to the payment;
 5. audit contains the canonical payment_reversed event;
 6. fresh shipment finance totals (read model) reflect the reversal;
 7. replay of the SAME correctionRequestId does not duplicate the correction;
 8. a NEW correctionRequestId against an already-reversed payment is REFUSED
    exactly as the canonical writer already behaves (no invented acceptance);
 9. unknown paymentId is rejected;
10. viewer/unauthorized role is refused by the existing finance_write boundary;
11. formatted optional evidence "1.200.000" parses to 1200000;
12. blank/garbage evidence never silently becomes zero (it stays absent).

Plus the handler contract the UI relies on:
  - reason is REQUIRED identity (no silent default reason);
  - the outcome echoes correctionRequestId on success AND refusal so the UI
    matches the authoritative backend answer to its own pending intent.

Transport: isolated staging (mongomock) via views.logi_sandbox — zero
production/pilot access.
"""

from __future__ import annotations

import pytest

from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm

SHIPMENT = "LO-0308"


@pytest.fixture()
def staging():
    import streamlit as st

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    yield transport
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


@pytest.fixture()
def event_seq():
    state = {"n": 0}

    def _make(name: str, payload: dict) -> dict:
        state["n"] += 1
        return {name: {"seq": state["n"], "event": name, "payload": payload}}

    return _make


def _dispatch(seq_fn, name, payload):
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1
    return outcomes[0]


def _payments(shipment_id: str = SHIPMENT):
    return rd.shipment_projection(vm.read_shipment(shipment_id))["finance"]["payments"]


def _finance(shipment_id: str = SHIPMENT):
    return rd.shipment_projection(vm.read_shipment(shipment_id))["finance"]


def _raw_payment(pid: str):
    ship = vm.read_shipment(SHIPMENT) or {}
    rows = (ship.get("data", {}).get("3.4", {}).get("payments") or [])
    return next((p for p in rows if str(p.get("id")) == pid), None)


def _create_receipt(seq_fn, request_id: str, amount: str = "150.000.000") -> str:
    out = _dispatch(seq_fn, "payment_record", {
        "shipmentId": SHIPMENT,
        "amount": amount,
        "requestId": request_id,
        "date": "2026-09-10",
        "note": "Thu tiền khách",
    })
    assert out["ok"], out["error"]
    return out["paymentId"]


# ---------------------------------------------------------------------------
# Core journey: 1-4 + 6 + outcome identity echo
# ---------------------------------------------------------------------------


def test_correction_reversal_roundtrip_and_fresh_readback(staging, event_seq):
    pid = _create_receipt(event_seq, "CORRUI-PAY-1")
    before = _finance()
    assert before["received"] == 150_000_000.0

    out = _dispatch(event_seq, "payment_correction", {
        "shipmentId": SHIPMENT,
        "paymentId": pid,
        "correctionRequestId": "CORRUI-REQ-1",
        "reason": "Khách chuyển khoản sai nội dung, cần hoàn tác để ghi nhận lại",
    })
    assert out["ok"] is True, out["error"]
    # (7) UI matching: the outcome carries the intent identity and the exact
    # shipment/payment identity it was dispatched for.
    assert out["event"] == "payment_correction"
    assert out["shipmentId"] == SHIPMENT
    assert out["correctionRequestId"] == "CORRUI-REQ-1"
    assert out["paymentId"] == pid
    # success carries a fresh readback, like every other material write
    assert isinstance(out.get("readback"), dict) and out["readback"].get("id") == SHIPMENT

    # (3) the ORIGINAL payment still exists; its money facts are untouched
    raw = _raw_payment(pid)
    assert raw is not None
    assert float(raw["amount"]) == 150_000_000.0
    assert str(raw.get("date")) == "2026-09-10"
    # reversal marking is the writer's own semantics (append/audit based, no delete)
    assert raw.get("is_reversed") is True
    assert str(raw.get("status")).lower() == "reversed"

    # (4) the linked financial_corrections row exists
    from core.database import get_db
    correction = get_db().financial_corrections.find_one({"correction_request_id": "CORRUI-REQ-1"})
    assert correction is not None
    assert correction["original_type"] == "shipment_payment"
    assert correction["original_id"] == pid
    assert correction["shipment_id"] == SHIPMENT
    assert correction["correction_type"] == "payment_reversal"
    assert correction["reason"].startswith("Khách chuyển khoản sai")
    assert correction["status"] == "applied"

    # (6) read model: row is honestly flagged and totals move via the backend
    rows = _payments()
    row = next(p for p in rows if p["id"] == pid)
    assert row["reversed"] is True
    after = _finance()
    assert after["received"] == 0
    assert after["outstanding"] == before["outstanding"] + 150_000_000.0


def test_audit_contains_canonical_reversal_events(staging, event_seq):
    pid = _create_receipt(event_seq, "CORRUI-PAY-AUD")
    out = _dispatch(event_seq, "payment_correction", {
        "shipmentId": SHIPMENT, "paymentId": pid,
        "correctionRequestId": "CORRUI-REQ-AUD",
        "reason": "Đối soát cuối tháng — hoàn tác ghi nhận trùng",
    })
    assert out["ok"], out["error"]

    # audit trail returned in the outcome AND present in the audit collection
    assert any(row["action"] == "payment_reversed" for row in out["audit"])
    from core.database import get_db
    logs = list(get_db().audit_logs.find({"entity_type": "shipment", "entity_id": SHIPMENT}))
    reversal = [row for row in logs if row.get("action") == "payment_reversed"]
    assert len(reversal) == 1
    assert reversal[0]["after"]["correction"]["original_id"] == pid
    # domain event exists for downstream consumers (canonical outbox)
    events = list(get_db().notification_outbox.find({}))
    assert any(
        event.get("event_type") == "shipment.payment_reversed"
        and event.get("payload", {}).get("payment_id") == pid
        for event in events
    ), "canonical domain event shipment.payment_reversed must be enqueued"


# ---------------------------------------------------------------------------
# Idempotency: (7) same correctionRequestId replays without duplicating
# ---------------------------------------------------------------------------


def test_replay_same_correction_request_id_does_not_duplicate(staging, event_seq):
    pid = _create_receipt(event_seq, "CORRUI-PAY-IDEM")
    first = _dispatch(event_seq, "payment_correction", {
        "shipmentId": SHIPMENT, "paymentId": pid,
        "correctionRequestId": "CORRUI-REQ-IDEM",
        "reason": "Hoàn tác vì trùng nghiệp vụ",
    })
    replay = _dispatch(event_seq, "payment_correction", {
        "shipmentId": SHIPMENT, "paymentId": pid,
        "correctionRequestId": "CORRUI-REQ-IDEM",
        "reason": "Hoàn tác vì trùng nghiệp vụ",
    })
    assert first["ok"] and replay["ok"], (first["error"], replay["error"])
    assert replay["persisted"] == first["persisted"]

    from core.database import get_db
    assert get_db().financial_corrections.count_documents({"correction_request_id": "CORRUI-REQ-IDEM"}) == 1
    # and the replay is still ONE reversal of ONE payment
    raw_rows = [p for p in (vm.read_shipment(SHIPMENT) or {})["data"]["3.4"]["payments"]]
    assert sum(1 for p in raw_rows if p.get("is_reversed")) == 1


def test_same_request_id_with_different_fingerprint_is_refused(staging, event_seq):
    pid = _create_receipt(event_seq, "CORRUI-PAY-FP")
    first = _dispatch(event_seq, "payment_correction", {
        "shipmentId": SHIPMENT, "paymentId": pid,
        "correctionRequestId": "CORRUI-REQ-FP",
        "reason": "Lý do A",
    })
    assert first["ok"], first["error"]
    conflict = _dispatch(event_seq, "payment_correction", {
        "shipmentId": SHIPMENT, "paymentId": pid,
        "correctionRequestId": "CORRUI-REQ-FP",
        "reason": "Lý do B khác nội dung",
    })
    assert conflict["ok"] is False
    assert conflict["correctionRequestId"] == "CORRUI-REQ-FP"
    from core.database import get_db
    assert get_db().financial_corrections.count_documents({"correction_request_id": "CORRUI-REQ-FP"}) == 1


# ---------------------------------------------------------------------------
# (8) NEW correctionRequestId against an already-reversed payment — the
# canonical writer's documented behavior: refuse, no second correction.
# ---------------------------------------------------------------------------


def test_second_new_request_on_reversed_payment_is_refused(staging, event_seq):
    pid = _create_receipt(event_seq, "CORRUI-PAY-TWICE")
    first = _dispatch(event_seq, "payment_correction", {
        "shipmentId": SHIPMENT, "paymentId": pid,
        "correctionRequestId": "CORRUI-REQ-T1",
        "reason": "Hoàn tác lần đầu",
    })
    assert first["ok"], first["error"]
    second = _dispatch(event_seq, "payment_correction", {
        "shipmentId": SHIPMENT, "paymentId": pid,
        "correctionRequestId": "CORRUI-REQ-T2",
        "reason": "Cố tình hoàn tác lần hai",
    })
    assert second["ok"] is False
    # writer's own semantics, surfaced verbatim (identity still echoed for the UI)
    assert "reversal" in second["error"] or "Đã được" in second["error"]
    assert second["correctionRequestId"] == "CORRUI-REQ-T2"
    from core.database import get_db
    assert get_db().financial_corrections.count_documents({
        "$or": [{"correction_request_id": "CORRUI-REQ-T1"},
                {"correction_request_id": "CORRUI-REQ-T2"}]
    }) == 1


def test_unknown_payment_id_rejected(staging, event_seq):
    _create_receipt(event_seq, "CORRUI-PAY-UNK")
    out = _dispatch(event_seq, "payment_correction", {
        "shipmentId": SHIPMENT, "paymentId": "PAY-KHONG-TON-TAI",
        "correctionRequestId": "CORRUI-REQ-UNK",
        "reason": "Bất kỳ",
    })
    assert out["ok"] is False
    assert "PAY-KHONG-TON-TAI" in out["error"] or "Không tìm thấy" in out["error"]


def test_missing_identity_or_reason_refused_with_echo(staging, event_seq):
    # blank reason: REQUIRED identity, never a defaulted "operational" reason
    out = _dispatch(event_seq, "payment_correction", {
        "shipmentId": SHIPMENT, "paymentId": "PAY-X",
        "correctionRequestId": "CORRUI-REQ-R",
        "reason": "   ",
    })
    assert out["ok"] is False
    assert "lý do" in out["error"].lower()
    assert out["correctionRequestId"] == "CORRUI-REQ-R"
    # the writer refuses nothing silently: no correction rows were written
    from core.database import get_db
    assert get_db().financial_corrections.count_documents({}) == 0


# ---------------------------------------------------------------------------
# (10) RBAC — the EXISTING finance_write boundary; viewer refused, no row,
# no new permission matrix.
# ---------------------------------------------------------------------------


def test_viewer_role_refused_by_existing_rbac(staging, event_seq):
    import streamlit as st

    pid = _create_receipt(event_seq, "CORRUI-PAY-RBAC")
    st.session_state["current_user"] = {
        "username": "viewer.fixture", "full_name": "Viewer Fixture",
        "role": "VIEWER", "user_id": "VIEWER-FIXTURE",
    }
    out = _dispatch(event_seq, "payment_correction", {
        "shipmentId": SHIPMENT, "paymentId": pid,
        "correctionRequestId": "CORRUI-REQ-RBAC",
        "reason": "Thử điều chỉnh bằng vai viewer",
    })
    assert out["ok"] is False
    assert "quyền" in out["error"] or "finance_write" in out["error"]
    assert out["correctionRequestId"] == "CORRUI-REQ-RBAC"
    # refusal is total: payment untouched, no correction row, no reversal audit
    raw = _raw_payment(pid)
    assert not raw.get("is_reversed")
    assert str(raw.get("status") or "").lower() != "reversed"
    from core.database import get_db
    assert get_db().financial_corrections.count_documents({"correction_request_id": "CORRUI-REQ-RBAC"}) == 0
    logs = list(get_db().audit_logs.find({"entity_type": "shipment", "entity_id": SHIPMENT}))
    assert all(row.get("action") != "payment_reversed" for row in logs)


# ---------------------------------------------------------------------------
# (5)+(11)+(12) evidence: canonical parser reused for optional amounts;
# garbage/blank can never become a silent 0.
# ---------------------------------------------------------------------------


def test_formatted_evidence_amount_parsed_via_canonical_parser(staging, event_seq):
    pid = _create_receipt(event_seq, "CORRUI-PAY-EV")
    out = _dispatch(event_seq, "payment_correction", {
        "shipmentId": SHIPMENT, "paymentId": pid,
        "correctionRequestId": "CORRUI-REQ-EV",
        "reason": "Hoàn tác theo ủy nhiệm chi",
        # raw formatted strings exactly as the sheet dispatches them
        "amount": "1.200.000",
        "date": "11/09/2026",
        "note": "UNC 45 ngày 11/09",
    })
    assert out["ok"], out["error"]
    from core.database import get_db
    correction = get_db().financial_corrections.find_one({"correction_request_id": "CORRUI-REQ-EV"})
    # canonical to_decimal semantics: 1.200.000 → 1200000; DD/MM/YYYY → ISO
    assert float(correction["evidence"]["amount"]) == 1_200_000.0
    assert correction["evidence"]["date"] == "2026-09-11"
    assert correction["evidence"]["note"] == "UNC 45 ngày 11/09"
    # evidence never becomes a replacement payment: exactly ONE payment row
    assert len(_payments()) == 1


def test_blank_or_garbage_evidence_never_becomes_zero(staging, event_seq):
    pid = _create_receipt(event_seq, "CORRUI-PAY-EV0")
    out = _dispatch(event_seq, "payment_correction", {
        "shipmentId": SHIPMENT, "paymentId": pid,
        "correctionRequestId": "CORRUI-REQ-EV0",
        "reason": "Hoàn tác, bằng chứng nhập nhằng",
        "amount": "abc",   # garbage must NOT silently become 0
        "date": "",        # blank stays absent
        "note": "  ",
    })
    assert out["ok"], out["error"]
    from core.database import get_db
    correction = get_db().financial_corrections.find_one({"correction_request_id": "CORRUI-REQ-EV0"})
    assert "amount" not in (correction["evidence"] or {})
    assert correction["evidence"] == {}
    # the reversal itself is still exactly the canonical writer's semantics
    assert float(correction["result"]["derived_paid"]) == 0.0


# ---------------------------------------------------------------------------
# Display integrity: reversed row keeps its facts and flag in the projection,
# so the UI can show truth without faking anything.
# ---------------------------------------------------------------------------


def test_projection_keeps_original_facts_next_to_reversed_flag(staging, event_seq):
    kept = _create_receipt(event_seq, "CORRUI-PAY-KEEP")
    other = _create_receipt(event_seq, "CORRUI-PAY-KEEP2", amount="40.000.000")
    out = _dispatch(event_seq, "payment_correction", {
        "shipmentId": SHIPMENT, "paymentId": other,
        "correctionRequestId": "CORRUI-REQ-KEEP",
        "reason": "Hoàn tác riêng khoản 40tr",
    })
    assert out["ok"], out["error"]
    rows = {p["id"]: p for p in _payments()}
    assert rows[kept]["reversed"] is False
    assert float(rows[kept]["amount"]) == 150_000_000.0
    assert rows[other]["reversed"] is True
    # original facts still visible next to the flag
    assert float(rows[other]["amount"]) == 40_000_000.0
    assert _finance()["received"] == 150_000_000.0
