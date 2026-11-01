"""INDEPENDENT REVIEW LOGI-255 — lai tao ro ri lastWrites cho row LEGACY.

Muc dich: do xem mot row KHONG co _provenance (dung hinh dang ma source truoc
commit 911f317 luu: `st.session_state[LAST_WRITES_KEY] = outcomes`) co duoc tra
cho actor KHAC / actor da bi ha quyen hay khong, khi actor doi qua DUNG duong
runtime cua app (`core.auth.fresh_session_identity_for_action` +
`_revalidate_session`, doc lai role tu canonical user store).

Khong mock logic app. Chi thao _provenance khoi stored row de tao trang thai
session dung nhu session dang mo tu truoc khi deploy commit nay.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import streamlit as st

from core import auth, database
from core.users import build_user_document
from views import logi_sandbox
from views import logi_view_model as vm
from tests.test_issue254_shipment_debt_glance import _seed_issue254_scenarios

LAST_WRITES_KEY = vm.LAST_WRITES_KEY
PROVENANCE = "_provenance"
PASSWORD = "review-only-password"
OUT = Path(os.environ.get("REVIEW_EV_OUT") or "/tmp/review255/ev")
USER = "qa.review.s255"
SID = "LO-0308"
AMOUNT = 35_000_000
COST_AMOUNT = 4250.0


def _seed_user(role: str) -> dict:
    db = database.get_db()
    db.users.delete_many({"username": USER})
    doc = build_user_document(USER, PASSWORD, "Review S255", role, created_by="review.fixture")
    db.users.insert_one(doc)
    from core.users import public_identity

    return public_identity(doc)


def _payment_payload(request_id: str) -> dict:
    return {
        "shipmentId": SID,
        "amount": AMOUNT,
        "requestId": request_id,
        "date": "2026-11-01",
        "note": "Thu tien dich vu (review legacy)",
    }


def _cost_rate_payload(request_id: str) -> dict:
    return {
        "requestId": request_id,
        "supplier": "Hang tau REVIEW",
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
                "carrier": {"id": "CARR-R", "name": "Hang tau REVIEW", "state": "CONFIRMED"},
                "origin": {"id": "SHA", "name": "Shanghai", "state": "UNKNOWN"},
                "destination": {"id": "HAN", "name": "Hanoi", "state": "UNKNOWN"},
                "rawLine": "SHANGHAI -> HANOI 4.250 USD/40HC",
                "confidence": "CONFIRMED",
            }
        ],
    }


@pytest.fixture()
def sandbox(monkeypatch):
    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state.clear()
    monkeypatch.setattr(st, "rerun", lambda: None)
    yield
    st.session_state.clear()
    logi_sandbox.reset_backend()


def _dispatch(seq: dict, events: dict[str, dict]) -> list[dict]:
    trigger = {}
    for event, payload in events.items():
        seq["n"] += 1
        trigger[event] = {"seq": seq["n"], "event": event, "payload": payload}
    return vm.dispatch(trigger)


def _demote_to_sale() -> dict:
    """Dung DUNG duong runtime: doi user doc trong canonical store."""
    db = database.get_db()
    db.users.update_one({"username": USER}, {"$set": {"role": "sale"}})
    fresh = auth.fresh_session_identity_for_action()
    assert fresh is not None, "session bi day ra ngoai — khong phai kich ban ha quyen"
    assert fresh["role"] == "sale", fresh
    return fresh


def _tokens(model) -> str:
    return json.dumps(model.get("lastWrites"), ensure_ascii=False, default=str)


def test_legacy_row_delivered_to_demoted_sale(sandbox, record_property):
    _seed_issue254_scenarios()
    st.session_state["current_user"] = _seed_user("support")
    assert auth.current_user()["role"] == "support"
    assert auth.has_permission("finance_view") is True

    seq = {"n": 0}
    outcomes = _dispatch(
        seq,
        {
            "payment_record": _payment_payload("PAY-REVIEW-LEGACY-1"),
            "cost_rate_save": _cost_rate_payload("COST-REVIEW-LEGACY-1"),
        },
    )
    by_event = {o.get("event"): o for o in outcomes}
    assert by_event["payment_record"]["ok"] is True, by_event
    assert by_event["cost_rate_save"]["ok"] is True, by_event

    # CONTROL: row co provenance (do commit nay ghi) -> Sale khong nhan.
    support_model = vm.build_view_model()
    assert support_model["user"]["canViewFinance"] is True
    assert {w["requestId"] for w in support_model["lastWrites"]} >= {
        "PAY-REVIEW-LEGACY-1",
        "COST-REVIEW-LEGACY-1",
    }

    # LEGACY: dung y hinh dang source truoc 911f317 luu (khong co _provenance).
    stored = st.session_state[LAST_WRITES_KEY]
    for row in stored:
        row.pop(PROVENANCE, None)
    assert all(PROVENANCE not in row for row in stored)

    fresh = _demote_to_sale()
    assert st.session_state["current_user"]["role"] == "sale"
    assert LAST_WRITES_KEY in st.session_state, "row legacy van con trong session"
    assert len(st.session_state[LAST_WRITES_KEY]) == 2

    sale_model = vm.build_view_model()
    assert sale_model["user"]["canViewFinance"] is False
    writes = sale_model["lastWrites"]
    record_property("legacy_sale_lastWrites", writes)

    # Lop 1 (finance_view) van chan payment_record.
    assert not any(w.get("event") == "payment_record" for w in writes)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "leaked-sale-lastwrites.json").write_text(
        json.dumps({"actor_after": "sale (demoted same account)", "lastWrites": writes},
                   ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

    leaked_cost = [w for w in writes if w.get("event") == "cost_rate_save"]
    print("\n=== SALE lastWrites sau khi bi ha quyen (row legacy) ===")
    print(json.dumps(writes, ensure_ascii=False, default=str, indent=2)[:4000])
    print("=== fresh identity ===", fresh)

    # Ket luan do duoc: row legacy cost_rate_save VAN toi Sale.
    assert leaked_cost, "khong tai hien duoc ro ri legacy"
    assert leaked_cost[0]["requestId"] == "COST-REVIEW-LEGACY-1"
    assert leaked_cost[0]["readback"]["rows"][0]["amount"] == COST_AMOUNT

    # Cung kenh do, so lieu cua nguoi khac co mat trong payload Sale khong?
    return writes


def test_legacy_row_vs_stamped_row_control(sandbox):
    """Control: row CO provenance -> Sale khong nhan gi (chung minh lop moi dung)."""
    _seed_issue254_scenarios()
    st.session_state["current_user"] = _seed_user("support")
    seq = {"n": 0}
    _dispatch(seq, {"cost_rate_save": _cost_rate_payload("COST-REVIEW-STAMPED-1")})
    _demote_to_sale()
    sale_model = vm.build_view_model()
    assert sale_model["user"]["canViewFinance"] is False
    assert sale_model["lastWrites"] == [], sale_model["lastWrites"]


USER_B = "qa.review.s255.b"


def test_legacy_payment_outcome_reaches_support_b_after_relogin(sandbox):
    """Variant 2: A bi vo hieu hoa -> login B cung tab -> legacy row cua A con lai?

    Day la duong runtime that: `fresh_session_identity_for_action()` pop
    `current_user` khi account bi deactivate, require_login() hien form, B dang
    nhap set lai `current_user`. `logi_last_writes` CHI bi xoa trong logout().
    """
    from core.users import public_identity

    _seed_issue254_scenarios()
    st.session_state["current_user"] = _seed_user("support")
    seq = {"n": 0}
    _dispatch(seq, {"payment_record": _payment_payload("PAY-REVIEW-LEGACY-B")})

    for row in st.session_state[LAST_WRITES_KEY]:
        row.pop(PROVENANCE, None)

    db = database.get_db()
    db.users.update_one({"username": USER}, {"$set": {"active": False}})
    assert auth.fresh_session_identity_for_action() is None, "account bi deactivate -> session fail closed"
    assert "current_user" not in st.session_state

    doc_b = build_user_document(USER_B, PASSWORD, "Review S255 B", "support", created_by="review.fixture")
    db.users.insert_one(doc_b)
    st.session_state["current_user"] = public_identity(doc_b)

    print("\n=== session key con lai sau khi doi actor (khong logout) ===",
          sorted(k for k in st.session_state.keys()))
    model_b = vm.build_view_model()
    writes_b = model_b["lastWrites"]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "leaked-support-b-lastwrites.json").write_text(
        json.dumps({"actor_after": "support B (other account, same tab, no logout)",
                    "lastWrites": writes_b}, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8")
    print("=== SUPPORT B lastWrites ===")
    print(json.dumps(writes_b, ensure_ascii=False, default=str, indent=2)[:2500])
    assert model_b["user"]["canViewFinance"] is True
    legacy = [w for w in writes_b if w.get("requestId") == "PAY-REVIEW-LEGACY-B"]
    assert legacy, "khong tai hien duoc: legacy payment outcome khong toi B"
    assert legacy[0]["persisted"]["amount"] == float(AMOUNT)
