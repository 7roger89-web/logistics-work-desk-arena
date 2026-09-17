"""LOGI_UAT_REAL_USE_REPAIR_02 — backend contracts behind three real-use repairs.

Run against the ISOLATED staging database (mongomock). Production is never
touched.

Proven here:

P0-A  CUSTOMER CREATE AUTHORITATIVE OUTCOME
      The customer-create/edit outcomes travel through the EXISTING lastWrites
      correlation mechanism (the same one shipment_create and
      authority_agent_save already use): the backend echoes the caller's
      ``requestId`` on SUCCESS and on EVERY refusal (validation / RBAC /
      duplicate / writer failure), and a success carries the canonical fresh
      readback. Without the echo the UI cannot tell its own outcome from
      someone else's, which is exactly what made "transport handled" look like
      "write succeeded".
      TRANSPORT_SUCCESS != PERSISTENCE_SUCCESS is proven negatively too: when
      the canonical writer returns True but the readback does not carry the
      customer, the outcome is ok=False.

P1-A  NEXT WORK TAB
      The backend genuinely emits hyphenated tabs in ``nextRoute``
      (lay-hang / tai-chinh / van-tai / chung-tu), and every tab it emits is a
      tab the shipment workdesk actually renders. This is the data half of the
      `\\w`-truncation defect; the parsing half is challenged in
      tests/component/dom_acceptance_real_use_repair.mjs against the real
      bundle.

P1-C  RESPONSIBILITY SEMANTICS
      ``support`` is ``updated_by`` (last writer), NOT an assignment, and the
      derived ops worklist rows now carry the CANONICAL owner resolution
      (core.shipment_dashboard._owner, projected as ``sale``) instead of the
      last writer. Rows that come from the real tasks collection keep their own
      canonical ``tasks.assignee``.
"""

from __future__ import annotations

import re

import pytest

from views import logi_c1
from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm


CUSTOMER_ID = "CUST-UATREPAIR02"


@pytest.fixture()
def staging():
    """Clean isolated staging database + deterministic staging actor."""
    import streamlit as st

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)
    yield transport
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


@pytest.fixture()
def c1_event():
    state = {"n": 0}

    def _make(name: str, payload: dict) -> dict:
        state["n"] += 1
        outcomes = logi_c1.consume_c1_triggers(
            {"seq": 0},
            {name: {"seq": state["n"], "event": name, "payload": payload}},
        )
        assert len(outcomes) == 1, outcomes
        return outcomes[0]

    return _make


def _payload(**over) -> dict:
    base = {
        "id": CUSTOMER_ID,
        "name": "Khách UAT Repair 02",
        "phone": "0900000009",
        "email": "repair02@example.com",
        "contactPerson": "Anh Ba",
        "taxCode": "0102030409",
        "address": "KCN UAT, Hưng Yên",
        "note": "pytest",
        "requestId": "REQ-1",
    }
    base.update(over)
    return base


# ---------------------------------------------------------------------------
# P0-A — authoritative, correlated customer-create outcome
# ---------------------------------------------------------------------------

def test_customer_create_success_echoes_request_id_and_returns_fresh_readback(staging, c1_event):
    out = c1_event("customer_create", _payload(requestId="REQ-OK"))

    assert out["ok"], out["error"]
    assert out["event"] == "customer_create"
    # The echo is what lets ONE click recognise ITS OWN outcome.
    assert out["requestId"] == "REQ-OK"
    # Success is backed by the canonical readback, not by the writer's return.
    assert out["readback"]["id"] == CUSTOMER_ID
    assert out["persisted"] == {"id": CUSTOMER_ID, "name": "Khách UAT Repair 02"}
    # …and the customer is genuinely in the fresh view-model the UI will read.
    model = vm.build_view_model()
    assert any(c["id"] == CUSTOMER_ID for c in model["customers"])


@pytest.mark.parametrize(
    "case,payload_over,expect_in_error",
    [
        ("validation", {"name": ""}, "bắt buộc"),
        ("duplicate", {}, "đã tồn tại"),
    ],
)
def test_every_customer_create_refusal_still_echoes_the_request_id(
    staging, c1_event, case, payload_over, expect_in_error
):
    """A refusal that cannot be correlated is exactly how a false success happens."""
    if case == "duplicate":
        first = c1_event("customer_create", _payload(requestId="REQ-SEED"))
        assert first["ok"], first["error"]

    out = c1_event("customer_create", _payload(requestId="REQ-REFUSED", **payload_over))

    assert out["ok"] is False
    assert expect_in_error in out["error"]
    assert out["requestId"] == "REQ-REFUSED"


def test_rbac_refusal_echoes_the_request_id_and_writes_nothing(staging, c1_event):
    import streamlit as st

    st.session_state["current_user"] = {"username": "viewer.user", "role": "VIEWER",
                                        "user_id": "U-VIEWER"}
    out = c1_event("customer_create", _payload(requestId="REQ-RBAC"))

    assert out["ok"] is False
    assert "RBAC" in out["error"]
    assert out["requestId"] == "REQ-RBAC"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    assert not any(c["id"] == CUSTOMER_ID for c in vm.build_view_model()["customers"])


def test_writer_success_without_persistence_is_reported_as_failure(staging, c1_event, monkeypatch):
    """TRANSPORT_SUCCESS != PERSISTENCE_SUCCESS, proven adversarially.

    The canonical writer is forced to claim success while the canonical
    readback does not carry the customer. The outcome must be ok=False: a
    write nobody can read back is not a persisted customer.
    """
    monkeypatch.setattr(logi_c1, "read_customer", lambda _cid: None)
    out = c1_event("customer_create", _payload(requestId="REQ-GHOST"))

    assert out["ok"] is False
    assert "đọc lại không thấy" in out["error"]
    assert out["requestId"] == "REQ-GHOST"


def test_customer_edit_outcome_is_correlated_the_same_way(staging, c1_event):
    created = c1_event("customer_create", _payload(requestId="REQ-C"))
    assert created["ok"], created["error"]

    edited = c1_event("customer_edit", {"id": CUSTOMER_ID, "name": "Tên đã sửa",
                                        "requestId": "REQ-E"})
    assert edited["ok"], edited["error"]
    assert edited["requestId"] == "REQ-E"
    assert edited["readback"]["name"] == "Tên đã sửa"

    missing = c1_event("customer_edit", {"id": "CUST-NOT-THERE", "name": "x",
                                         "requestId": "REQ-E2"})
    assert missing["ok"] is False
    assert missing["requestId"] == "REQ-E2"


# ---------------------------------------------------------------------------
# P1-A — the backend really emits hyphenated work tabs
# ---------------------------------------------------------------------------

# The canonical shipment workdesk tab ids (component/src/pages/ShipmentDetail.tsx).
WORKDESK_TABS = {"van-tai", "lay-hang", "nhap", "tai-chinh", "chung-tu", "lich-su"}


def test_next_route_tabs_are_real_workdesk_tabs_and_include_hyphenated_ones(staging):
    model = vm.build_view_model()
    tabs = set()
    for shipment in model["shipments"]:
        match = re.search(r"[?&]tab=([^&]+)", shipment["nextRoute"])
        if match:
            tabs.add(match.group(1))

    assert tabs, "no shipment carried a nextRoute tab in staging data"
    assert tabs <= WORKDESK_TABS, f"nextRoute points at non-existent tabs: {tabs - WORKDESK_TABS}"
    # The defect only exists because real tabs contain '-'.
    assert any("-" in tab for tab in tabs), \
        "staging data no longer exercises hyphenated tabs — the P1-A challenge would be vacuous"


def test_ops_worklist_routes_also_carry_real_tabs(staging):
    model = vm.build_view_model()
    for task in model["tasks"]:
        match = re.search(r"[?&]tab=([^&]+)", task["route"])
        if match:
            assert match.group(1) in WORKDESK_TABS, task["route"]


# ---------------------------------------------------------------------------
# P1-C — responsibility semantics come from canonical fields only
# ---------------------------------------------------------------------------

def test_support_is_the_last_writer_not_an_assignment(staging):
    """`support` is documented and projected as core.database's `updated_by`."""
    model = vm.build_view_model()
    rows = model["shipments"]
    assert rows

    for row in rows:
        raw = vm.read_shipment(row["id"]) or {}
        assert row["support"] == rd.text(raw.get("updated_by"))


def test_derived_ops_rows_use_the_canonical_owner_not_the_last_writer(staging):
    """A derived ops row has no task document, so its responsible person is the
    canonical owner resolution (core.shipment_dashboard), never `updated_by`."""
    model = vm.build_view_model()
    by_id = {row["id"]: row for row in model["shipments"]}
    derived = [t for t in model["tasks"] if t["id"].startswith("OPS-")]
    assert derived, "staging data produced no derived ops rows"

    for task in derived:
        row = by_id[task["lot"]]
        assert task["assignee"] == (row["sale"] or rd.UNKNOWN_LABEL)
        # The defect: the last writer masquerading as the responsible person.
        if row["support"] and row["support"] != row["sale"]:
            assert task["assignee"] != row["support"]


def test_no_fabricated_assignment_field_was_introduced(staging, c1_event):
    """This slice must NOT invent assignment business semantics.

    No canonical shipment-assignment field/writer/permission exists in the
    repo, so nothing here may write one.
    """
    created = c1_event("customer_create", _payload(requestId="REQ-NOASSIGN"))
    assert created["ok"], created["error"]

    model = vm.build_view_model()
    for row in model["shipments"]:
        raw = vm.read_shipment(row["id"]) or {}
        for invented in ("assigned_support", "support_owner", "handled_by",
                         "support_user", "support_id"):
            assert invented not in raw, f"an assignment field was fabricated: {invented}"
