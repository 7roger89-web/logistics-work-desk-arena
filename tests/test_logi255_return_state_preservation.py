"""LOGI-255-RETURN-STATE-PRESERVATION-20261102 — focused regression: a real
setSearchParams (tab switch) inside ShipmentDetail must NOT wipe location.state,
so "Về danh sách lô" still returns to the exact filtered list.

SPEC_REF: Issue #254 / PR #255 (acceptance B with a genuine setSp navigation
before the return; acceptance C direct-entry fallback).

WRONG_PASS guarded here: on the pre-fix bundle (cb1870f) the DOM lane fails at
"a tab switch (setSp) must not wipe location.state" — data-return-to collapses
from the full filtered /lo-hang?... URL to "/lo-hang" after one tab click.

Scope note: this is the DOM contract on the shipped bundle. The browser's own
Back button is a MemoryRouter limitation measured separately with real Chromium
(evidence/issue254/09-return-state/); it is never inferred from this lane.
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


def test_tab_switch_in_detail_preserves_the_remembered_list(staging):
    """open lot -> switch tab (setSp) -> return keeps q/status/period/from/to/archive."""
    import streamlit as st

    from views import logi_view_model as vm

    st.session_state["current_user"] = dict(SUPPORT_ACTOR)
    support_view = vm.build_view_model()
    shipment_ids = [row["id"] for row in support_view.get("shipments") or []]
    assert len(shipment_ids) >= 2, f"staging view-model must expose several lots, got {shipment_ids}"

    payload = {
        "supportView": support_view,
        "shipmentIds": shipment_ids,
        "queryShipmentId": shipment_ids[0],
    }
    proc = subprocess.run(
        ["node", str(ROOT / "tests/component/dom_acceptance_issue255_return_state.mjs")],
        input=json.dumps(payload, ensure_ascii=False, default=str),
        text=True,
        capture_output=True,
        cwd=str(ROOT),
        timeout=120,
        check=False,
    )
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "DOM_ACCEPTANCE_ISSUE255_RETURN_STATE=PASS" in proc.stdout, proc.stdout
