#!/usr/bin/env python3
"""Generate the LOGI_REAL_USE_CREATE_SHIPMENT_AGENT_MASTER_01 create-shipment
DOM-acceptance fixture.

Same contract as gen_partner_context_fixture.py: boot the ISOLATED mongomock
staging transport (never production) and dump real ``build_view_model()``
payloads. Every write goes through the SAME bounded dispatcher the UI drives,
and its outcome is stored under ``st.session_state["logi_last_writes"]``
exactly like ``views.logi_view_model.dispatch()`` does, so ``lastWrites`` in
each state is the genuine backend readback:

  1. ``initial``        — before any create: no LO-0470, no lastWrites.
  2. ``createOk``       — after ONE ``shipment_create`` for LO-0470 went
                          through RBAC → validate_shipment →
                          save_shipment_atomic → audit → fresh read: the fresh
                          view-model CONTAINS the new shipment and lastWrites
                          carries the ok=True outcome (with requestId).
  3. ``duplicateError`` — the SAME id submitted again: the canonical duplicate
                          refusal (ok=False) the form must display verbatim.
  4. ``rbacError``      — a VIEWER attempt refused by RBAC (ok=False).

CONTROL_TOWER_REPAIR_01 additionally generates the regression states for the
"pre-existing duplicate must never false-navigate" scenario:

  5. ``preexistingInitial`` — boot state where LO-0470 ALREADY EXISTS before
                          any submit (fresh view-model, no lastWrites).
  6. ``unrelatedChange``  — an UNRELATED backend write (a field save on
                          another shipment) delivered while the create intent
                          is still unanswered: the version genuinely changes
                          and LO-0470 is present, yet NO shipment_create
                          outcome for the pending requestId exists — this must
                          NOT be treated as success.

The DOM test rewrites each state's ``requestId`` to the one the real click
produced before invoking, exactly matching live behaviour.

Run:  python scripts/gen_create_shipment_fixture.py
Out:  tests/component/fixtures/view_model_create_shipment.json
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SHIPMENT = "LO-0470"
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_create_shipment.json"


def main() -> None:
    import streamlit as st

    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "this fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)

    seq = {"n": 0}

    def dispatch(payload: dict) -> dict:
        seq["n"] += 1
        outcomes = vm.consume_phase_b_triggers(
            {"seq": 0},
            {"shipment_create": {"seq": seq["n"], "event": "shipment_create",
                                 "payload": payload}},
        )
        assert len(outcomes) == 1
        return outcomes[0]

    def dispatch_named(name: str, payload: dict) -> dict:
        seq["n"] += 1
        outcomes = vm.consume_phase_b_triggers(
            {"seq": 0},
            {name: {"seq": seq["n"], "event": name, "payload": payload}},
        )
        assert len(outcomes) == 1
        return outcomes[0]

    # 1. initial — the form page before any create intent.
    initial = vm.build_view_model()
    assert not any(s["id"] == SHIPMENT for s in initial["shipments"])
    assert initial["lastWrites"] == []

    # 2. createOk — the ONE real create, end to end.
    create_payload = {
        "shipmentId": SHIPMENT,
        "customerId": "CUST-ANPHAT",
        "customer": "An Phát",
        "contractId": "",
        "currency": "VND",
        "requestId": "CSX-FIX-OK-1",
        "transport": {"mode": "Truck", "incoterm": "DAP",
                      "pol": "Bằng Tường (Quảng Tây)", "pod": "Hữu Nghị (Lạng Sơn)"},
    }
    ok_out = dispatch(dict(create_payload))
    assert ok_out["ok"], ok_out["error"]
    st.session_state[vm.LAST_WRITES_KEY] = [ok_out]
    create_ok = vm.build_view_model()
    assert any(s["id"] == SHIPMENT for s in create_ok["shipments"]), \
        "the fresh view-model must contain the newly created shipment"

    # -------------------------------------------------------------------
    # CONTROL_TOWER_REPAIR_01 — pre-existing-duplicate regression states.
    # The id already exists BEFORE any submit; the create intent stays
    # unanswered while an UNRELATED backend write changes the version.
    # Neither may be mistaken for a successful create.
    # -------------------------------------------------------------------

    # 5. preexistingInitial — the id exists, but NO outcome is pending yet.
    st.session_state.pop(vm.LAST_WRITES_KEY, None)
    preexisting_initial = vm.build_view_model()
    assert any(s["id"] == SHIPMENT for s in preexisting_initial["shipments"])
    assert preexisting_initial["lastWrites"] == []

    # 6. unrelatedChange — an UNRELATED write (field save on another shipment)
    #    lands while the create intent is still in flight: the version really
    #    changes and the id is present, yet lastWrites carries NO
    #    shipment_create outcome for the pending requestId.
    unrelated_out = dispatch_named("shipment_field_save", {
        "shipmentId": "LO-0307",
        "fields": {"carrier": "Bộ (đường bộ TQ–VN) — unrelated regression write"},
        "requestId": "CSX-FIX-UNRELATED-1",
    })
    assert unrelated_out["ok"], unrelated_out["error"]
    assert unrelated_out["event"] == "shipment_field_save"
    st.session_state[vm.LAST_WRITES_KEY] = [unrelated_out]
    unrelated_change = vm.build_view_model()
    assert any(s["id"] == SHIPMENT for s in unrelated_change["shipments"])
    assert unrelated_change["version"] != preexisting_initial["version"], \
        "the unrelated write must genuinely change the payload version"
    assert not any(w.get("event") == "shipment_create"
                   for w in unrelated_change["lastWrites"]), \
        "no shipment_create outcome may be present in the unrelated state"

    # 3. duplicateError — same id again: canonical refusal, nothing new written.
    dup_out = dispatch(dict(create_payload, requestId="CSX-FIX-DUP-1"))
    assert not dup_out["ok"] and "đã tồn tại" in dup_out["error"], dup_out
    st.session_state[vm.LAST_WRITES_KEY] = [dup_out]
    duplicate_error = vm.build_view_model()

    # 4. rbacError — a VIEWER attempt refused by RBAC.
    st.session_state["current_user"] = {"username": "viewer.user", "role": "VIEWER",
                                        "user_id": "U-VIEWER"}
    rbac_out = dispatch(dict(create_payload, shipmentId="LO-0471", requestId="CSX-FIX-RBAC-1"))
    assert not rbac_out["ok"] and "RBAC" in rbac_out["error"], rbac_out
    st.session_state[vm.LAST_WRITES_KEY] = [rbac_out]
    rbac_error = vm.build_view_model()
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)

    payload = {
        "generatedFrom": "scripts/gen_create_shipment_fixture.py — isolated mongomock staging",
        "shipment": SHIPMENT,
        "initial": initial,
        "createOk": create_ok,
        "duplicateError": duplicate_error,
        "rbacError": rbac_error,
        "preexistingInitial": preexisting_initial,
        "unrelatedChange": unrelated_change,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  initial: shipments={len(initial['shipments'])} lastWrites={len(initial['lastWrites'])}")
    print(f"  createOk: shipments={len(create_ok['shipments'])} "
          f"lastWrites={[(w['ok'], w.get('requestId')) for w in create_ok['lastWrites']]}")
    print(f"  duplicateError: {duplicate_error['lastWrites'][0]['error']}")
    print(f"  rbacError: {rbac_error['lastWrites'][0]['error']}")
    print(f"  preexistingInitial: hasLO0470={any(s['id'] == SHIPMENT for s in preexisting_initial['shipments'])} "
          f"lastWrites={len(preexisting_initial['lastWrites'])}")
    print(f"  unrelatedChange: version_changed="
          f"{unrelated_change['version'] != preexisting_initial['version']} "
          f"lastWrites={[(w.get('event'), w.get('ok')) for w in unrelated_change['lastWrites']]}")

    logi_sandbox.reset_backend()


if __name__ == "__main__":
    main()
