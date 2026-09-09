"""Logistics view-model for the Logi-good component (Phase A).

Phase A: sandbox seed only (views/logi_seed.py). No production DB, no
credentials. The view-model is the single source of truth pushed to the
ONE Streamlit Components v2 component root; Phase B swaps the sandbox
source for real Logistics readers behind the same shape.

Sandbox session state:
    st.session_state["logi_state"]  — copy of the seed (mutable per session)
    st.session_state["logi_seq"]    — last consumed component event seq
"""

from __future__ import annotations

import copy
import hashlib
import json

import streamlit as st

from views import logi_seed

STATE_KEY = "logi_state"
SEQ_KEY = "logi_seq"


def _state() -> dict:
    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = logi_seed.build_seed_state()
    return st.session_state[STATE_KEY]


def build_view_model() -> dict:
    """Assemble the JSON payload for the component `data` channel."""
    state = _state()
    vm = {
        "version": _payload_version(state),
        "user": copy.deepcopy(logi_seed.USER),
        "shipments": list(state["shipments"].values()),
        "tasks": state["tasks"],
        "contracts": state["contracts"],
        "customers": state["customers"],
        "quotes": state["quotes"],
        "notifications": state["notifications"],
    }
    return vm


def _payload_version(state: dict) -> str:
    """Deterministic content version: changes only when data actually
    changes (keeps the component element identity stable across reruns)."""
    raw = json.dumps(
        {
            "s": state["shipments"],
            "t": state["tasks"],
            "c": state["contracts"],
            "q": state["quotes"],
            "n": state["notifications"],
        },
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# The ONE bounded event dispatcher (Phase A event set).
# ---------------------------------------------------------------------------

ALLOWED_EVENTS = {"shipment_update", "navigate"}


def dispatch(result) -> None:
    """Streamlit-facing entry: consume component trigger values from one
    script run. Thin wrapper over the pure :func:`consume_triggers`."""
    state = _state()
    session = {"seq": st.session_state.get(SEQ_KEY, 0), "shipments": state["shipments"]}
    consume_triggers(session, result)
    st.session_state[SEQ_KEY] = session["seq"]
    # state["shipments"] is mutated in place by the pure function.


def consume_triggers(session: dict, result) -> None:
    """The ONE bounded event dispatcher (Phase A event set).

    Pure over an explicit ``session`` dict so it is testable without a
    Streamlit runtime:

        session = {"seq": int, "shipments": {id: shipment_dict}}

    `result` is the ComponentResult (dict-like) returned by the single v2
    component mount. Only the bounded Phase A event set is handled;
    everything else is ignored. Consumed events advance ``session["seq"]``.
    """
    for event_name in ALLOWED_EVENTS:
        payload = result.get(event_name) if hasattr(result, "get") else None
        if payload is None:
            continue
        if not isinstance(payload, dict):
            continue
        seq = payload.get("seq")
        if not isinstance(seq, int):
            continue
        last = session.get("seq", 0)
        if seq <= last:
            continue  # already consumed (trigger values are transient, but be safe)
        session["seq"] = seq
        data = payload.get("payload")
        if event_name == "shipment_update" and isinstance(data, dict):
            _apply_shipment_update(session.get("shipments", {}), data.get("shipment"))
        # "navigate": backend-only navigation is a no-op in Phase A —
        # ordinary page navigation never requires a Python rerun.


def _apply_shipment_update(shipments: dict, shipment: dict | None) -> None:
    if not isinstance(shipment, dict):
        return
    sid = shipment.get("id")
    if not isinstance(sid, str) or sid not in shipments:
        return
    # Bounded merge: accept only known top-level keys (payload comes from
    # our own typed component — the TS contract fixes the shape).
    server = shipments[sid]
    for key in (
        "status",
        "statusTone",
        "priority",
        "nextAction",
        "nextActionDetail",
        "nextLabel",
        "nextRoute",
        "updated",
        "missingDocs",
        "docs",
        "pickup",
        "cargo",
        "exportInfo",
        "importInfo",
        "finance",
        "pxk",
        "timeline",
    ):
        if key in shipment:
            server[key] = copy.deepcopy(shipment[key])
