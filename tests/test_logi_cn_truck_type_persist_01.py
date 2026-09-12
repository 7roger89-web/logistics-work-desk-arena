"""LOGI_CN_TRUCK_TYPE_PERSIST_01 — acceptance evidence for the Owner-approved
CN pickup truck type/size fact (approved 2026-09-12).

The ruling, restated as executable assertions:

 1. ``data.1.2.pickup_truck_type`` is the canonical free-text fact describing
    the CN pickup truck type/size of the shipment itself.
 2. Exactly that ONE key joins the component write whitelist ``FIELD_PATHS``.
 3. It is operator-keyed text: never derived, never calculated.
 4. Untouched → omitted; edited → sent verbatim; cleared → explicit ``""``
    removes the stale value (backend half; the UI half is pinned by the DOM
    acceptance step, mirroring the GNT CLEAR_FIX).
 5. Unrelated facts (``container_no``, ``truck_no``) are untouched by the save.
 6. Finance, ledger, schema, database and infrastructure are untouched.

Every write assertion re-reads the shipment from the database
(``views.logi_view_model.read_shipment``), never from frontend state.
Transport: the isolated staging database (mongomock); production is never used.
"""

from __future__ import annotations

import pytest

from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm

TRUCK = "17.5m · rộng 3m · tải ≤30t"


# ---------------------------------------------------------------------------
# Fixtures (same harness as tests/test_logi_gnt_canonical_fields_01.py)
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    """A clean isolated staging database + a deterministic staging actor."""
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


# ---------------------------------------------------------------------------
# Rule 2 — the whitelist grew by EXACTLY the one approved key
# ---------------------------------------------------------------------------

def test_whitelist_gained_exactly_the_one_approved_key():
    """FIELD_PATHS = the 29 prior keys + exactly ``pickup_truck_type``."""
    assert vm.FIELD_PATHS["pickup_truck_type"] == ("data", "1.2", "pickup_truck_type")
    assert len(vm.FIELD_PATHS) == 30

    # No smuggled extra field under the transport section: the nine
    # pre-existing 1.2 keys plus the one the Owner has now ruled on.
    under_12 = {k for k, p in vm.FIELD_PATHS.items() if p[1:2] == ("1.2",)}
    assert under_12 == {
        "booking_no", "carrier", "mbl", "hbl", "vessel", "etd",
        "pol", "pod", "container_no", "qty_pkg", "pickup_truck_type",
    }


def test_coercion_is_plain_trimmed_text():
    """No numeric/date parser: the fact is stored exactly as keyed."""
    assert vm._coerce("pickup_truck_type", "  " + TRUCK + "  ") == TRUCK
    assert vm._coerce("pickup_truck_type", "") == ""
    assert vm._coerce("pickup_truck_type", None) is None


# ---------------------------------------------------------------------------
# Rules 1 & 3 — canonical save, then an INDEPENDENT fresh readback
# ---------------------------------------------------------------------------

def test_truck_type_save_and_fresh_readback(staging, event_seq):
    """The slice end to end: enter → canonical save → fresh read → truthful UI."""
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0306",
        "fields": {"pickup_truck_type": TRUCK},
    })
    assert out["ok"], out["error"]

    fresh = vm.read_shipment("LO-0306")
    assert fresh["data"]["1.2"]["pickup_truck_type"] == TRUCK

    # The dispatcher's readback and an independent projection agree.
    assert out["readback"]["pickup"]["truckType"] == TRUCK
    assert rd.shipment_projection(fresh)["pickup"]["truckType"] == TRUCK


def test_truck_type_survives_reopen(staging, event_seq):
    """A later independent read (reopen) still returns the stored value."""
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0307",
        "fields": {"pickup_truck_type": TRUCK},
    })
    assert out["ok"], out["error"]

    reopened = vm.read_shipment("LO-0307")
    assert rd.shipment_projection(reopened)["pickup"]["truckType"] == TRUCK


def test_untouched_save_preserves_truck_type(staging, event_seq):
    """A save that omits the field (untouched) never overwrites it."""
    first = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0306",
        "fields": {"pickup_truck_type": TRUCK},
    })
    assert first["ok"], first["error"]

    # An ordinary pickup save that does not mention the truck type.
    second = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0306",
        "fields": {"pol": "Bằng Tường"},
    })
    assert second["ok"], second["error"]

    fresh = vm.read_shipment("LO-0306")
    assert fresh["data"]["1.2"]["pickup_truck_type"] == TRUCK
    assert rd.shipment_projection(fresh)["pickup"]["truckType"] == TRUCK


def test_explicit_clear_removes_stale_value(staging, event_seq):
    """An actively cleared field travels as ``""`` and the stale value dies."""
    first = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0306",
        "fields": {"pickup_truck_type": TRUCK},
    })
    assert first["ok"], first["error"]

    cleared = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0306",
        "fields": {"pickup_truck_type": ""},
    })
    assert cleared["ok"], cleared["error"]

    fresh = vm.read_shipment("LO-0306")
    assert fresh["data"]["1.2"].get("pickup_truck_type") in ("", None)
    # The UI renders the honest blank state, not the stale value.
    assert rd.shipment_projection(fresh)["pickup"]["truckType"] == ""
    assert cleared["readback"]["pickup"]["truckType"] == ""


def test_blank_truck_type_stays_unknown_not_zero(staging, event_seq):
    """A shipment without the fact projects a blank, never a fabricated value."""
    fresh = vm.read_shipment("LO-0306")
    assert "pickup_truck_type" not in fresh["data"]["1.2"]
    assert rd.shipment_projection(fresh)["pickup"]["truckType"] == ""


def test_unrelated_truck_facts_are_untouched(staging, event_seq):
    """The CN plate identifier and the VN delivery truck survive the save."""
    before = vm.read_shipment("LO-0306")
    plate_before = before["data"]["1.2"].get("container_no")
    vn_before = before["data"]["2.7"].get("truck_no")

    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0306",
        "fields": {"pickup_truck_type": TRUCK},
    })
    assert out["ok"], out["error"]

    after = vm.read_shipment("LO-0306")
    assert after["data"]["1.2"].get("container_no") == plate_before
    assert after["data"]["2.7"].get("truck_no") == vn_before
