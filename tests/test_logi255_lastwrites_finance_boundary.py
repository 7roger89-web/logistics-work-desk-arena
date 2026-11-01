"""Issue #255 — lastWrites finance boundary khi doi actor cung session.

WRONG_PASS tunnel: Support ghi 35.000.000 VND (payment_record thanh cong).
Cung session, logout roi dang nhap Sale (hoac ha Support xuong Sale)
va build_view_model() lai -> payload lastWrites KHONG duoc chua
readback/persisted/audit cua khoan thu cu (so tien, da thu, cong no).
Support hop le van doc lai dung.

requestId / idempotency / thong bao thanh cong that thay duoc giu nguyen
cho actor hop le.
"""

from __future__ import annotations

import pytest
import streamlit as st

from core.auth import logout
from views import logi_sandbox
from views import logi_view_model as vm

from tests.test_issue254_shipment_debt_glance import (  # noqa: E402
    OPERATIONS_ACTOR,
    SALE_ACTOR,
    SUPPORT_ACTOR,
    _dispatch,
    _seed_issue254_scenarios,
)

LAST_WRITES_KEY = vm.LAST_WRITES_KEY
PAYMENT_EVENT = "payment_record"
SID = "LO-0308"  # vndActual trong cac scenario Issue #254
AMOUNT = 35_000_000


@pytest.fixture()
def staging255():
    """mongomock tram trong + session trong, Support la hien tai."""
    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state.clear()
    st.session_state["current_user"] = dict(SUPPORT_ACTOR)
    yield transport
    st.session_state.clear()
    logi_sandbox.reset_backend()


def _write_payment(seq, request_id="PAY-255-1", amount=AMOUNT):
    return _dispatch(seq, PAYMENT_EVENT, {
        "shipmentId": SID,
        "amount": amount,
        "requestId": request_id,
        "date": "2026-11-01",
        "note": "Thu tien dich vu",
    })


def test_logout_clears_current_user_and_lastwrites(staging255):
    """Logout xoa current_user VA LAST_WRITES_KEY (khong ke thua boi actor moi)."""
    st.session_state[LAST_WRITES_KEY] = [{
        "event": PAYMENT_EVENT,
        "shipmentId": SID,
        "ok": True,
        "requestId": "PAY-255-OLD",
        "persisted": {"amount": float(AMOUNT)},
    }]
    assert st.session_state.get(LAST_WRITES_KEY)
    assert st.session_state.get("current_user")

    logout()

    assert "current_user" not in st.session_state
    assert st.session_state.get(LAST_WRITES_KEY) in (None, [])


def test_support_finance_write_kept_in_lastwrites(staging255):
    """Actor co finance_view (Support) nhan duoc toan bo ket qua ghi tien."""
    import streamlit as st  # noqa: F401

    _seed_issue254_scenarios()
    seq = {"n": 0}
    st.session_state["current_user"] = dict(SUPPORT_ACTOR)
    pay_out = _write_payment(seq, "PAY-255-1")
    assert pay_out["ok"] is True
    st.session_state[LAST_WRITES_KEY] = [pay_out]  # nhu dispatch() luu truoc rerun

    model = vm.build_view_model()
    assert model["user"]["canViewFinance"] is True
    writes = model["lastWrites"]
    assert len(writes) == 1
    assert writes[0]["event"] == PAYMENT_EVENT
    assert writes[0]["ok"] is True
    assert writes[0]["requestId"] == "PAY-255-1"
    assert writes[0]["persisted"]["amount"] == float(AMOUNT)
    assert writes[0]["readback"] is not None


def test_lastwrites_finance_not_leaked_to_sale_same_session(staging255):
    """NEGATIVE / WRONG_PASS: Support ghi tien, ha xuong Sale cung session.

    Sale (khong finance_view) KHONG duoc so tien cua Support qua lastWrites,
    ngay ca lastWrites chua duoc xoa khoi session.
    """
    import streamlit as st  # noqa: F401

    _seed_issue254_scenarios()
    seq = {"n": 0}
    st.session_state["current_user"] = dict(SUPPORT_ACTOR)
    pay_out = _write_payment(seq, "PAY-255-1")
    assert pay_out["ok"] is True
    st.session_state[LAST_WRITES_KEY] = [pay_out]  # session cua Support con ke

    # Support hop le van doc lai dung (requestId/idempotency/thong bao duoc giu)
    support_model = vm.build_view_model()
    assert support_model["user"]["canViewFinance"] is True
    assert support_model["lastWrites"][0]["persisted"]["amount"] == float(AMOUNT)

    # Cung session: Support -> Sale (khong logout, lastWrites con luu tru)
    st.session_state["current_user"] = dict(SALE_ACTOR)
    sale_model = vm.build_view_model()
    assert sale_model["user"]["canViewFinance"] is False

    sale_writes = sale_model["lastWrites"]
    assert not any(w.get("event") == PAYMENT_EVENT for w in sale_writes), (
        "Sale khong duoc nhan su kien ghi tien cu qua lastWrites"
    )
    for w in sale_writes:
        assert w.get("event") != PAYMENT_EVENT
        persisted = w.get("persisted") or {}
        assert "amount" not in persisted
        assert "derivedPaid" not in persisted
        assert "derivedDebt" not in persisted
        readback = w.get("readback") or {}
        assert (readback.get("finance") or {}).get("receivable") is None


def test_lastwrites_finance_blocked_for_operations_and_unknown_role(staging255):
    """Operations va role lai (xac thuc nhung role khong duoc Support) khong sot duoc so tien."""
    import streamlit as st  # noqa: F401

    from core.auth import has_permission

    st.session_state[LAST_WRITES_KEY] = [{
        "event": PAYMENT_EVENT,
        "shipmentId": SID,
        "ok": True,
        "requestId": "PAY-255-OLD",
        "persisted": {
            "amount": float(AMOUNT),
            "derivedPaid": 35_000_000.0,
            "derivedDebt": 100_000_000.0,
            "version": 1,
        },
        "readback": {
            "finance": {
                "receivable": 135_000_000.0,
                "received": 35_000_000.0,
                "outstanding": 100_000_000.0,
            }
        },
    }]

    for actor in (OPERATIONS_ACTOR,
                  {"user_id": "u-contractor", "username": "legacy.contractor",
                   "display_name": "Legacy Contractor", "role": "contractor"}):
        st.session_state["current_user"] = dict(actor)
        assert has_permission("finance_view") is False
        model = vm.build_view_model()
        assert model["user"]["canViewFinance"] is False
        writes = model["lastWrites"]
        assert not any(w.get("event") == PAYMENT_EVENT for w in writes)
        for w in writes:
            persisted = w.get("persisted") or {}
            assert "amount" not in persisted
            assert "derivedPaid" not in persisted
            assert "derivedDebt" not in persisted
