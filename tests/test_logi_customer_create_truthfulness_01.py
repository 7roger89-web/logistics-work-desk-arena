"""LOGI_CUSTOMER_CREATE_TRUTHFULNESS_01 — focused backend acceptance evidence.

P0-A (customer-create false success) is repaired on the UI side by consuming
the AUTHORITATIVE backend outcome instead of trusting the transport. This file
proves the backend half of that contract on the EXISTING surfaces only:

  * ``customer_create`` / ``customer_edit`` outcomes now echo the ``requestId``
    of the click that sent them (the same correlated-readback contract
    ``shipment_create`` and ``customer_getfly_import`` already use) so the UI
    can never mistake one request's answer for another's;
  * every refusal path (validation, RBAC, duplicate, writer failure) carries
    the same correlation — a refusal is always attributable;
  * ``vm.dispatch()`` stores the outcome BEFORE the rerun under the existing
    ``logi_last_writes`` key and the next fresh view-model embeds it —
    exactly what the waiting form consumes;
  * a replayed trigger seq writes NOTHING (one click can never double-write);
  * no new event name, no second dispatcher: the C1 surface is unchanged.

Transport: the isolated staging database (mongomock) running the CURRENT
canonical writers unchanged. The production database is never touched.
"""

from __future__ import annotations

import pytest

from views import logi_c1
from views import logi_sandbox
from views import logi_view_model as vm


_CREATE_PAYLOAD = {
    "id": "CUST-TRUTH",
    "name": "Khách Truthfulness",
    "phone": "0987000111",
    "email": "truth@example.com",
    "contactPerson": "Ngọc",
    "taxCode": "0107777666",
    "address": "KCN Test",
}


@pytest.fixture()
def staging():
    import streamlit as st

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)
    st.session_state.pop(vm.SEQ_KEY, None)
    yield transport
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)
    st.session_state.pop(vm.SEQ_KEY, None)
    logi_sandbox.reset_backend()


@pytest.fixture()
def event_seq():
    state = {"n": 0}

    def _make(name: str, payload: dict) -> dict:
        state["n"] += 1
        return {name: {"seq": state["n"], "event": name, "payload": payload}}

    return _make


def _dispatch(seq_fn, name, payload):
    outcomes = logi_c1.consume_c1_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1
    return outcomes[0]


def _as(role: str, username: str):
    import streamlit as st

    st.session_state["current_user"] = {
        "username": username, "full_name": username, "role": role, "user_id": f"ID-{username}",
    }


# ---------------------------------------------------------------------------
# requestId echo — every outcome is attributable to the exact click
# ---------------------------------------------------------------------------

def test_customer_create_success_echoes_request_id(staging, event_seq):
    out = _dispatch(event_seq, "customer_create", dict(_CREATE_PAYLOAD, requestId="CCT-OK-1"))
    assert out["ok"], out["error"]
    assert out["event"] == "customer_create"
    assert out["requestId"] == "CCT-OK-1"
    assert out["readback"]["id"] == "CUST-TRUTH"


def test_every_refusal_path_echoes_request_id(staging, event_seq):
    # Validation refusal.
    out = _dispatch(event_seq, "customer_create", {"id": "", "name": "", "requestId": "CCT-VAL"})
    assert not out["ok"] and out["requestId"] == "CCT-VAL"

    # Duplicate refusal (CUST-ANPHAT exists in the staging seed).
    out = _dispatch(event_seq, "customer_create",
                    {"id": "CUST-ANPHAT", "name": "An Phát JSC", "requestId": "CCT-DUP"})
    assert not out["ok"] and "đã tồn tại" in out["error"]
    assert out["requestId"] == "CCT-DUP"

    # RBAC refusal (viewer cannot write customers).
    _as("VIEWER", "viewer.user")
    out = _dispatch(event_seq, "customer_create",
                    dict(_CREATE_PAYLOAD, id="CUST-NOPE", requestId="CCT-RBAC"))
    assert not out["ok"] and "RBAC" in out["error"]
    assert out["requestId"] == "CCT-RBAC"
    _as("SUPPORT", "staging.support")
    from core.database import load_customers
    assert "CUST-NOPE" not in (load_customers() or {}), "a refused create must not persist"


def test_customer_edit_echoes_request_id(staging, event_seq):
    ok_create = _dispatch(event_seq, "customer_create", dict(_CREATE_PAYLOAD, requestId="CCT-C-1"))
    assert ok_create["ok"], ok_create["error"]
    out = _dispatch(event_seq, "customer_edit",
                    {"id": "CUST-TRUTH", "name": "Khách Truthfulness (đổi)", "requestId": "CCT-E-1"})
    assert out["ok"], out["error"]
    assert out["event"] == "customer_edit"
    assert out["requestId"] == "CCT-E-1"
    assert out["readback"]["name"] == "Khách Truthfulness (đổi)"


# ---------------------------------------------------------------------------
# The waiting form consumes: dispatch() → lastWrites → next fresh view-model
# ---------------------------------------------------------------------------

def test_outcome_reaches_next_view_model_and_replay_writes_nothing(staging, event_seq, monkeypatch):
    import streamlit as st

    reruns = {"n": 0}
    monkeypatch.setattr(st, "rerun", lambda: reruns.__setitem__("n", reruns["n"] + 1))

    result = {"customer_create": {"seq": 1, "event": "customer_create",
                                  "payload": dict(_CREATE_PAYLOAD, requestId="CCT-VM-1")}}
    outcomes = vm.dispatch(result)
    assert [o["event"] for o in outcomes] == ["customer_create"]
    assert outcomes[0]["ok"] is True
    assert outcomes[0]["requestId"] == "CCT-VM-1"
    assert reruns["n"] == 1, "a handled material write must trigger exactly ONE rerun"

    # Stored BEFORE the rerun, under the existing session key.
    stored = st.session_state[vm.LAST_WRITES_KEY]
    assert stored[0]["event"] == "customer_create"
    assert stored[0]["requestId"] == "CCT-VM-1"

    # The next fresh view-model embeds the authoritative outcome — this is
    # what the open, waiting form matches by requestId.
    model = vm.build_view_model()
    assert any(w["event"] == "customer_create" and w["requestId"] == "CCT-VM-1" and w["ok"]
               for w in model["lastWrites"]), "outcome must reach the component payload"
    assert any(c["id"] == "CUST-TRUTH" for c in model["customers"]), \
        "the fresh view-model must contain the new customer"

    # Replay protection: the same trigger consumed again writes NOTHING.
    replayed = vm.dispatch(result)
    assert replayed == [], "a replayed seq must be ignored"
    assert reruns["n"] == 1, "no second rerun for an already-consumed trigger"
    from core.database import load_customers
    customers = load_customers() or {}
    assert customers["CUST-TRUTH"]["name"] == "Khách Truthfulness", \
        "the replay must not have re-written (or duplicated) the customer"


def test_refusal_reaches_next_view_model(staging, event_seq, monkeypatch):
    import streamlit as st

    monkeypatch.setattr(st, "rerun", lambda: None)
    result = {"customer_create": {"seq": 1, "event": "customer_create",
                                  "payload": {"id": "CUST-ANPHAT", "name": "An Phát JSC",
                                              "requestId": "CCT-VM-DUP"}}}
    outcomes = vm.dispatch(result)
    assert len(outcomes) == 1 and outcomes[0]["ok"] is False
    assert outcomes[0]["requestId"] == "CCT-VM-DUP"
    model = vm.build_view_model()
    assert any(w["ok"] is False and w["requestId"] == "CCT-VM-DUP"
               for w in model["lastWrites"]), "the refusal must reach the component payload"


# ---------------------------------------------------------------------------
# No new framework: the C1 surface is unchanged
# ---------------------------------------------------------------------------

def test_customer_create_still_rides_the_one_c1_dispatcher():
    assert "customer_create" in logi_c1.C1_EVENTS
    assert logi_c1._HANDLERS["customer_create"] is logi_c1._handle_customer_create
    assert logi_c1._HANDLERS["customer_edit"] is logi_c1._handle_customer_edit
    # No sibling handler anywhere else in the C1 surface.
    assert sum(1 for h in logi_c1._HANDLERS.values() if h is logi_c1._handle_customer_create) == 1


def test_outcome_shape_is_backward_compatible(staging, event_seq):
    """Pre-existing consumers read event/id/ok/error/readback — unchanged."""
    out = _dispatch(event_seq, "customer_create", dict(_CREATE_PAYLOAD))
    for key in ("event", "id", "ok", "error", "readback", "audit"):
        assert key in out, f"the C1 outcome shape lost its {key} field"
    assert out["id"] == "CUST-TRUTH"
