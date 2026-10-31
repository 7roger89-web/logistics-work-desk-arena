"""Phase A backend acceptance (secondary to real-browser checks).

Verifies:
  * the Streamlit script boots the single v2 component without exceptions
  * the sandbox view-model has the expected Phase A shape
  * the ONE bounded dispatcher (pure ``consume_triggers``) merges a
    ``shipment_update`` event delivered through the real ComponentResult
    type, and ignores stale seqs / unknown ids / unbounded event names
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from streamlit.components.v2.bidi_component.state import ComponentResult  # noqa: E402
from views import logi_seed  # noqa: E402
from views import logi_view_model  # noqa: E402


def _session() -> dict:
    state = logi_seed.build_seed_state()
    return {"seq": 0, "shipments": state["shipments"]}


def _trigger_result(seq: int, event: str, payload) -> ComponentResult:
    """Build the exact result shape the v2 runtime produces for a trigger."""
    return ComponentResult({}, {event: {"seq": seq, "event": event, "payload": payload}})


# ---------------------------------------------------------------------------
# View-model shape (sandbox seed, no production DB)
# ---------------------------------------------------------------------------


def test_seed_shape():
    state = logi_seed.build_seed_state()
    assert len(state["shipments"]) == 5
    assert {s["id"] for s in state["shipments"].values()} == {
        "LO-0306", "LO-0307", "LO-0308", "LO-0299", "LO-0295",
    }
    levels = [t["level"] for t in state["tasks"]]
    assert levels.count("Khan") == 3
    assert levels.count("CanXuLy") == 4
    assert levels.count("BinhThuong") == 3


def test_view_model_shape_via_app():
    from unittest.mock import patch

    from streamlit.testing.v1 import AppTest

    # The host is authenticated before the first run: ``require_login``
    # re-derives the session identity from the canonical store on every rerun,
    # so the store must contain THIS user. Without it the run correctly stops at
    # the login screen and builds no view-model (nothing to assert).
    fixture_user = {
        "username": "fixture", "display_name": "Fixture", "role": "admin",
        "active": True, "user_id": "U-FIXTURE", "email": "",
    }
    at = AppTest.from_file(str(REPO_ROOT / "app.py"), default_timeout=120)
    at.session_state["current_user"] = dict(fixture_user)
    with patch("core.database.load_users",
               return_value={"fixture": dict(fixture_user)}):
        at.run()
    assert not at.exception, f"app raised: {[str(e.value) for e in at.exception]}"
    assert logi_view_model.STATE_KEY in at.session_state

    vm = at.session_state[logi_view_model.STATE_KEY]
    for key in ("version", "shipments", "tasks", "contracts",
                "customers", "quotes", "notifications"):
        assert key in vm
    s = next(x for x in vm["shipments"].values() if x["id"] == "LO-0306")
    for key in ("pickup", "cargo", "exportInfo", "importInfo", "finance", "pxk",
                "timeline", "docs", "missingDocs", "nextRoute"):
        assert key in s
    # component `data` channel payload must be JSON-serializable
    json.dumps(vm, ensure_ascii=False)


# ---------------------------------------------------------------------------
# The ONE bounded dispatcher — pure, driven by the real ComponentResult type
# ---------------------------------------------------------------------------


def test_shipment_update_merges():
    session = _session()
    shipment = copy.deepcopy(session["shipments"]["LO-0299"])
    shipment["status"] = "Đã giao"
    shipment["statusTone"] = "green"
    logi_view_model.consume_triggers(session, _trigger_result(1, "shipment_update", {"shipment": shipment}))
    merged = session["shipments"]["LO-0299"]
    assert merged["status"] == "Đã giao"
    assert merged["statusTone"] == "green"
    # untouched keys preserved
    assert merged["customer"] == "Hồng Hà"
    assert merged["contract"] == "HDMB-0299"
    assert session["seq"] == 1


def test_stale_seq_ignored():
    session = _session()
    logi_view_model.consume_triggers(session, _trigger_result(5, "shipment_update", {"shipment": {"id": "LO-0299", "status": "OK"}}))
    assert session["seq"] == 5
    logi_view_model.consume_triggers(session, _trigger_result(5, "shipment_update", {"shipment": {"id": "LO-0299", "status": "MÃI XỬ"}}))
    logi_view_model.consume_triggers(session, _trigger_result(3, "shipment_update", {"shipment": {"id": "LO-0299", "status": "MÃI XỬ"}}))
    assert session["shipments"]["LO-0299"]["status"] == "OK"
    assert session["seq"] == 5


def test_unknown_shipment_ignored():
    session = _session()
    logi_view_model.consume_triggers(session, _trigger_result(1, "shipment_update", {"shipment": {"id": "LO-9999", "status": "X"}}))
    assert "LO-9999" not in session["shipments"]
    assert session["seq"] == 1


def test_unbounded_event_ignored():
    session = _session()
    logi_view_model.consume_triggers(session, _trigger_result(100, "some_other_event", {}))
    assert session["seq"] == 0  # not consumed
    logi_view_model.consume_triggers(session, _trigger_result(200, "navigate", {"path": "/lo-hang"}))
    assert session["seq"] == 200  # navigate is in the bounded set (no-op backend-wise)


def test_nested_payload_update():
    session = _session()
    shipment = copy.deepcopy(session["shipments"]["LO-0306"])
    shipment["importInfo"] = {**shipment["importInfo"], "declarationNo": "105588421330"}
    shipment["missingDocs"] = []
    logi_view_model.consume_triggers(session, _trigger_result(1, "shipment_update", {"shipment": shipment}))
    merged = session["shipments"]["LO-0306"]
    assert merged["importInfo"]["declarationNo"] == "105588421330"
    assert merged["missingDocs"] == []
    # other shipments untouched
    assert session["shipments"]["LO-0299"]["id"] == "LO-0299"


def test_malformed_payloads_ignored():
    session = _session()
    # non-dict payload
    logi_view_model.consume_triggers(session, ComponentResult({}, {"shipment_update": "garbage"}))
    # missing seq
    logi_view_model.consume_triggers(session, ComponentResult({}, {"shipment_update": {"event": "shipment_update", "payload": {}}}))
    # seq present but payload missing
    logi_view_model.consume_triggers(session, ComponentResult({}, {"shipment_update": {"seq": 1}}))
    assert session["seq"] == 1
    assert session["shipments"]["LO-0306"]["status"] != "X"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
