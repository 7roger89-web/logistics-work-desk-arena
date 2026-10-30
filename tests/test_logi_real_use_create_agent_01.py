"""LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01 — focused acceptance evidence.

Two usability blockers fixed in ONE bounded slice:

A. "Tạo Lô Mới" really creates a shipment end-to-end and the backend outcome
   (success OR refusal) is delivered back to the component via the existing
   ``st.session_state["logi_last_writes"]`` readback embedded in the NEXT
   fresh view-model — the UI must never act on "event transported" alone.

B. "Đại Lý Trường Thành" (route unchanged: /ngu-canh-doi-tac) exposes
   CREATE / EDIT of the EXISTING canonical authority_agents master through
   ONE new typed event ``authority_agent_save`` on the existing C1 dispatcher
   surface → RBAC (sales_write) → core.database.save_authority_agent (upsert +
   audit) → fresh load_authority_agents readback. No agents_v2, no new writer,
   no new database, no production mutation.

Transport: the isolated staging database (mongomock) running the CURRENT
canonical writers unchanged. The production database is never touched.
"""

from __future__ import annotations

import pytest

from views import logi_c1
from views import logi_sandbox
from views import logi_view_model as vm


# ---------------------------------------------------------------------------
# Fixtures (same infrastructure as test_phase_b_real_data.py)
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    """A clean isolated staging database + a deterministic staging actor."""
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


def _dispatch_phase_b(seq_fn, name, payload):
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1
    return outcomes[0]


def _dispatch_c1(seq_fn, name, payload):
    outcomes = logi_c1.consume_c1_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1
    return outcomes[0]


def _as(role: str, username: str):
    import streamlit as st

    st.session_state["current_user"] = {
        "username": username, "full_name": username, "role": role,
        "user_id": f"ID-{username}",
    }


def _shipment_count() -> int:
    return len(vm.load_shipments())


_CREATE_PAYLOAD = {
    "shipmentId": "LO-0470",
    "customerId": "CUST-ANPHAT",
    "customer": "Tên giả từ browser",
    "contractId": "",
    "currency": "VND",
    "requestId": "CSX-REQ-1",
    "transport": {"mode": "Truck", "incoterm": "DAP",
                  "pol": "Bằng Tường (Quảng Tây)", "pod": "Hữu Nghị (Lạng Sơn)"},
}


# ---------------------------------------------------------------------------
# A. CREATE SHIPMENT — real use
# ---------------------------------------------------------------------------

def test_valid_create_persists_exactly_one_shipment(staging, event_seq):
    """1. A valid create writes exactly ONE shipment through the canonical writer."""
    from core.database import load_audit_logs

    before = _shipment_count()
    out = _dispatch_phase_b(event_seq, "shipment_create", dict(_CREATE_PAYLOAD))
    assert out["ok"], out["error"]
    assert _shipment_count() == before + 1, "exactly one shipment may be created"
    fresh = vm.read_shipment("LO-0470")
    assert fresh is not None and fresh["customer"] == "An Phát JSC"
    assert fresh["customer"] != _CREATE_PAYLOAD["customer"]
    assert out["persisted"]["id"] == "LO-0470"
    actions = [row.get("action") for row in load_audit_logs("shipment", "LO-0470", limit=5)]
    assert "create" in actions, "the canonical writer must produce real audit"


def test_duplicate_shipment_id_is_rejected(staging, event_seq):
    """2. Duplicate id → backend refuses; nothing extra is persisted."""
    first = _dispatch_phase_b(event_seq, "shipment_create", dict(_CREATE_PAYLOAD))
    assert first["ok"], first["error"]
    count_after_first = _shipment_count()

    dup = _dispatch_phase_b(event_seq, "shipment_create",
                            dict(_CREATE_PAYLOAD, requestId="CSX-REQ-DUP"))
    assert not dup["ok"]
    assert "đã tồn tại" in dup["error"]
    assert dup["requestId"] == "CSX-REQ-DUP", "the refusal must echo the request id"
    assert _shipment_count() == count_after_first, "a duplicate must not persist"


def test_backend_outcome_is_delivered_in_next_view_model(staging, event_seq, monkeypatch):
    """3. dispatch() stores the outcome BEFORE the rerun and the fresh
    view-model carries it — that is what the UI consumes before navigating."""
    import streamlit as st

    reruns = {"n": 0}

    def _fake_rerun():
        reruns["n"] += 1  # record instead of throwing, like the v2 one-shot rerun

    monkeypatch.setattr(st, "rerun", _fake_rerun)

    result = {"shipment_create": {"seq": 1, "event": "shipment_create",
                                  "payload": dict(_CREATE_PAYLOAD)}}
    outcomes = vm.dispatch(result)
    assert [o["event"] for o in outcomes] == ["shipment_create"]
    assert outcomes[0]["ok"] is True
    assert reruns["n"] == 1, "a handled material write must trigger ONE rerun"

    # Stored BEFORE the rerun, under the existing session key.
    stored = st.session_state[vm.LAST_WRITES_KEY]
    assert stored[0]["requestId"] == "CSX-REQ-1"

    # The next fresh view-model embeds the authoritative outcome.
    model = vm.build_view_model()
    assert any(w["event"] == "shipment_create" and w["requestId"] == "CSX-REQ-1"
               for w in model["lastWrites"]), "outcome must reach the component payload"

    # Replay protection: the same trigger value consumed again writes NOTHING.
    monkeypatch.setattr(st, "rerun", _fake_rerun)
    replayed = vm.dispatch(result)
    assert replayed == [], "a replayed seq must be ignored"
    assert reruns["n"] == 1, "no second rerun for an already-consumed trigger"
    assert _shipment_count() == sum(1 for s in vm.load_shipments()) \
        and vm.read_shipment("LO-0470") is not None


def test_backend_failure_is_delivered_and_nothing_persists(staging, event_seq, monkeypatch):
    """4. A refusal (RBAC here) is delivered as an ok=False outcome and the
    UI therefore stays on the form with the real error."""
    import streamlit as st

    monkeypatch.setattr(st, "rerun", lambda: None)
    _as("VIEWER", "viewer.user")
    result = {"shipment_create": {"seq": 1, "event": "shipment_create",
                                  "payload": dict(_CREATE_PAYLOAD, shipmentId="LO-0471",
                                                  requestId="CSX-REQ-RBAC")}}
    outcomes = vm.dispatch(result)
    assert len(outcomes) == 1 and outcomes[0]["ok"] is False
    assert "RBAC" in outcomes[0]["error"]
    assert outcomes[0]["requestId"] == "CSX-REQ-RBAC"
    assert vm.read_shipment("LO-0471") is None, "a refused create must not persist"
    # The refusal still travels to the component through the same readback.
    model = vm.build_view_model()
    assert any(w["ok"] is False and w["requestId"] == "CSX-REQ-RBAC"
               for w in model["lastWrites"])


def test_fresh_readback_contains_the_created_shipment(staging, event_seq):
    """5. The refreshed view-model contains the newly created shipment row."""
    out = _dispatch_phase_b(event_seq, "shipment_create", dict(_CREATE_PAYLOAD))
    assert out["ok"], out["error"]
    model = vm.build_view_model()
    ids = {s["id"] for s in model["shipments"]}
    assert "LO-0470" in ids, "the fresh view-model must contain the new shipment"
    assert out["readback"]["id"] == "LO-0470", "the outcome readback is the fresh row"


# ---------------------------------------------------------------------------
# B. ĐẠI LÝ TRƯỜNG THÀNH — authority_agent_save through the existing writer
# ---------------------------------------------------------------------------

_AGENT_PAYLOAD = {
    "agentId": "AGT-MINHPHAT",
    "legalName": "CÔNG TY TNHH ĐẠI LÝ MINH PHÁT",
    "legalCode": "0101234567",
    "legalAddress": "Số 1, Đường Test, Hà Nội",
    "legalRepresentative": "Nguyễn Minh Phát",
    "representativeTitle": "Giám đốc",
    "phone": "0912000111",
    "email": "phat@dailymn.vn",
    "bankAccountHolder": "ĐẠI LÝ MINH PHÁT",
    "bankAccountNumber": "1111222233",
    "bankName": "Vietcombank",
    "bankBranch": "CN Hà Nội",
    "requestId": "AGX-REQ-1",
}


def test_authority_agent_save_creates_master_via_existing_writer(staging, event_seq):
    """6. CREATE goes through core.database.save_authority_agent (upsert+audit)."""
    from core.database import load_audit_logs, load_authority_agents

    assert "AGT-MINHPHAT" not in (load_authority_agents() or {})
    out = _dispatch_c1(event_seq, "authority_agent_save", dict(_AGENT_PAYLOAD))
    assert out["ok"], out["error"]
    assert out["id"] == "AGT-MINHPHAT" and out["requestId"] == "AGX-REQ-1"

    agents = load_authority_agents() or {}
    assert "AGT-MINHPHAT" in agents, "the master must be persisted by the writer"
    actions = [row.get("action") for row in load_audit_logs("authority_agent", "AGT-MINHPHAT", limit=5)]
    assert "create" in actions, "the canonical writer must produce real audit"

    # The readback uses the SAME party projection every other screen uses.
    assert out["readback"]["legalName"] == "CÔNG TY TNHH ĐẠI LÝ MINH PHÁT"
    assert out["readback"]["bankName"] == "Vietcombank"

    # And the next fresh view-model already carries the saved master — both in
    # the C1 authority payload and in the partner picker (the page shows it
    # immediately, no optimistic fake).
    model = vm.build_view_model()
    assert any(a["id"] == "AGT-MINHPHAT" for a in model["authority"]["agents"])
    assert any(o["key"] == "AGT-MINHPHAT" and o["master"]
               for o in model["partnerContext"]["options"])


def test_authority_agent_edit_updates_same_id_without_duplicate(staging, event_seq):
    """7. EDIT updates the SAME agent id — one record before and after."""
    from core.database import load_audit_logs, load_authority_agents

    create = _dispatch_c1(event_seq, "authority_agent_save", dict(_AGENT_PAYLOAD))
    assert create["ok"], create["error"]

    edit = _dispatch_c1(event_seq, "authority_agent_save", dict(
        _AGENT_PAYLOAD, phone="0912999888", legalName="CÔNG TY TNHH ĐẠI LÝ MINH PHÁT (MỚI)",
        requestId="AGX-REQ-2"))
    assert edit["ok"], edit["error"]

    agents = load_authority_agents() or {}
    matching = [a for a in agents.values() if a.get("agent_id") == "AGT-MINHPHAT"]
    assert len(matching) == 1, "an edit must never create a second record"
    assert matching[0]["phone"] == "0912999888"
    assert matching[0]["legal_name"] == "CÔNG TY TNHH ĐẠI LÝ MINH PHÁT (MỚI)"
    actions = [row.get("action") for row in load_audit_logs("authority_agent", "AGT-MINHPHAT", limit=6)]
    assert "update" in actions, "the canonical writer must record the edit"


def test_canonical_fields_round_trip(staging, event_seq):
    """8. Every canonical master field survives save → read → projection."""
    out = _dispatch_c1(event_seq, "authority_agent_save", dict(_AGENT_PAYLOAD))
    assert out["ok"], out["error"]

    from core.database import load_authority_agents

    doc = (load_authority_agents() or {})["AGT-MINHPHAT"]
    expected_doc = {
        "agent_id": "AGT-MINHPHAT",
        "legal_name": "CÔNG TY TNHH ĐẠI LÝ MINH PHÁT",
        "legal_code": "0101234567",
        "legal_address": "Số 1, Đường Test, Hà Nội",
        "legal_representative": "Nguyễn Minh Phát",
        "representative_title": "Giám đốc",
        "phone": "0912000111",
        "email": "phat@dailymn.vn",
        "bank_account_holder": "ĐẠI LÝ MINH PHÁT",
        "bank_account_number": "1111222233",
        "bank_name": "Vietcombank",
        "bank_branch": "CN Hà Nội",
    }
    for key, value in expected_doc.items():
        assert doc.get(key) == value, f"field {key} did not round-trip"

    # The same 12 fields projected through the canonical party view.
    view = logi_c1._party_view(doc, "agent")
    expected_view = {
        "id": "AGT-MINHPHAT",
        "legalName": "CÔNG TY TNHH ĐẠI LÝ MINH PHÁT",
        "legalCode": "0101234567",
        "legalAddress": "Số 1, Đường Test, Hà Nội",
        "representative": "Nguyễn Minh Phát",
        "representativeTitle": "Giám đốc",
        "phone": "0912000111",
        "email": "phat@dailymn.vn",
        "bankAccountHolder": "ĐẠI LÝ MINH PHÁT",
        "bankAccountNumber": "1111222233",
        "bankName": "Vietcombank",
        "bankBranch": "CN Hà Nội",
    }
    assert view == expected_view


def test_unauthorized_agent_save_is_refused(staging, event_seq):
    """9. Viewer/unauthorized: the backend refuses and persists nothing."""
    from core.database import load_authority_agents

    _as("VIEWER", "viewer.user")
    out = _dispatch_c1(event_seq, "authority_agent_save",
                       dict(_AGENT_PAYLOAD, agentId="AGT-HACK", requestId="AGX-REQ-HACK"))
    assert not out["ok"]
    assert "RBAC" in out["error"] and "sales_write" in out["error"]
    assert "AGT-HACK" not in (load_authority_agents() or {}), \
        "a refused save must never persist"

    # The canonical writer itself is the security boundary too (double guard).
    from core.database import save_authority_agent

    assert save_authority_agent({"agent_id": "AGT-HACK2", "legal_name": "X"}) is False
    assert "AGT-HACK2" not in (load_authority_agents() or {})


def test_agent_save_allowed_roles(staging, event_seq):
    """9b. sales_write: Admin, Support and Sale may save; the dispatcher and
    the canonical writer agree."""
    from core.auth import can_operate_business
    from core.database import load_authority_agents

    for i, role in enumerate(("ADMIN", "SUPPORT", "SALE")):
        _as(role, f"user.{role.lower()}")
        assert can_operate_business("sales_write") is True
        out = _dispatch_c1(event_seq, "authority_agent_save", dict(
            _AGENT_PAYLOAD, agentId=f"AGT-RBAC-{role}", requestId=f"AGX-RBAC-{i}"))
        assert out["ok"], f"{role} must be allowed: {out['error']}"
        assert f"AGT-RBAC-{role}" in (load_authority_agents() or {})

    _as("VIEWER", "viewer.user")
    assert can_operate_business("sales_write") is False


def test_authority_agent_save_is_on_the_existing_c1_surface(staging):
    """The new event lives on the EXISTING C1 dispatcher — no new router/API."""
    assert "authority_agent_save" in logi_c1.C1_EVENTS
    assert logi_c1.C1_EVENTS <= vm.ALL_EVENTS, "the shell must surface the event"
    assert "authority_agent_save" in logi_c1._HANDLERS


def test_partner_context_projection_still_backed_after_agent_write(staging, event_seq):
    """11 (backend half): after an agent save the existing read-only context
    projection still works — options include the seeded master AND the new one."""
    _dispatch_c1(event_seq, "authority_agent_save", dict(_AGENT_PAYLOAD))
    model = vm.build_view_model()
    keys = {o["key"] for o in model["partnerContext"]["options"]}
    assert "AGT-PHUANH" in keys, "the seeded master must remain"
    assert "AGT-MINHPHAT" in keys, "the saved master must appear"
    # The slice stays a read-only projection over the existing readers.
    assert model["partnerContext"]["readOnly"] is True
