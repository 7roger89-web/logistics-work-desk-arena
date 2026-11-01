"""LOGI-255-RETURN-TO-LIST — focused regression for the in-app return control.

SPEC_REF: Issue #254 (LOGI-255 continuation — "return to the list keeps filters").

Owner outcome: an operator filters /lo-hang, opens a lot's Tài chính / Công nợ,
and gets back to the SAME list with the SAME filters.

WRONG_PASS guarded here: filters q + status + period(khác, from/to) + archive are
set, the debt cluster is opened, and returning lands on the plain list (or on an
empty "Tháng này" list) with every filter discarded.

Scope note (stated so a green run is not over-read): this lane is the DOM
contract on the shipped bundle. It cannot exercise the browser's own Back
button, because the shell router is a MemoryRouter; NATIVE_BROWSER_BACK is
measured separately with real Chromium in playwright/issue255_return_nav.py.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from views import logi_sandbox

ROOT = Path(__file__).resolve().parents[1]

SUPPORT_ACTOR = {
    "username": "staging.support",
    "full_name": "Support (Test)",
    "role": "support",
    "user_id": "STAGING-SUPPORT",
}


@pytest.fixture()
def staging():
    import streamlit as st

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(SUPPORT_ACTOR)
    yield transport
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


def test_detail_screen_returns_to_the_filtered_list(staging):
    """The shipped bundle keeps q/status/period/from/to/archive on the way back."""
    import streamlit as st

    from views import logi_view_model as vm

    st.session_state["current_user"] = dict(SUPPORT_ACTOR)
    support_view = vm.build_view_model()
    shipment_ids = [row["id"] for row in support_view.get("shipments") or []]
    assert len(shipment_ids) >= 2, f"staging view-model must expose several lots, got {shipment_ids}"

    payload = {
        "supportView": support_view,
        "shipmentIds": shipment_ids,
        # isolate one lot by its own id: the q filter is asserted against a real row
        "queryShipmentId": shipment_ids[0],
    }
    proc = subprocess.run(
        ["node", str(ROOT / "tests/component/dom_acceptance_issue255_return_to_list.mjs")],
        input=json.dumps(payload, ensure_ascii=False, default=str),
        text=True,
        capture_output=True,
        cwd=str(ROOT),
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "DOM_ACCEPTANCE_ISSUE255_RETURN=PASS" in proc.stdout, proc.stdout
