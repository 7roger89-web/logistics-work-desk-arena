#!/usr/bin/env python3
"""Generate the LOGI_CUSTOMER_CREATE_TRUTHFULNESS_01 DOM-acceptance fixture.

Same contract as gen_create_shipment_fixture.py: boot the ISOLATED mongomock
staging transport (never production) and dump real ``build_view_model()``
payloads. Every write goes through the SAME bounded C1 dispatcher the UI drives
(``logi_c1.consume_c1_triggers``), and its outcome is stored under
``st.session_state["logi_last_writes"]`` exactly like
``views.logi_view_model.dispatch()`` does, so ``lastWrites`` in each state is
the genuine backend readback:

  1. ``initial``        — before any create: the 5 staging customers, no
                          lastWrites.
  2. ``duplicateError`` — a ``customer_create`` for the EXISTING CUST-ANPHAT:
                          the canonical duplicate refusal (ok=False) the form
                          must display verbatim while keeping the entered data.
  3. ``createOk``       — ONE real ``customer_create`` for CUST-MOI went
                          through RBAC → duplicate check →
                          save_customer_to_cloud → audit → fresh read: the
                          fresh view-model CONTAINS the new customer and
                          lastWrites carries the ok=True outcome (with the
                          echoed requestId).
  4. ``unrelatedChange`` — an UNRELATED write (a customer_edit on a DIFFERENT
                          customer) delivered while a create intent is still
                          unanswered: the version genuinely changes, yet
                          lastWrites carries NO customer_create outcome — this
                          must NOT be treated as success.

The DOM test rewrites each state's ``requestId`` to the one the real click
produced before invoking, exactly matching live behaviour.

Run:  python scripts/gen_customer_create_fixture.py
Out:  tests/component/fixtures/view_model_customer_create.json
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DUPLICATE_ID = "CUST-ANPHAT"
NEW_ID = "CUST-MOI"
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_customer_create.json"


def main() -> None:
    import streamlit as st

    from views import logi_c1, logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "this fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)

    seq = {"n": 0}

    def dispatch_c1(name: str, payload: dict) -> dict:
        seq["n"] += 1
        outcomes = logi_c1.consume_c1_triggers(
            {"seq": 0},
            {name: {"seq": seq["n"], "event": name, "payload": payload}},
        )
        assert len(outcomes) == 1
        return outcomes[0]

    # 1. initial — the customers page before any create intent.
    initial = vm.build_view_model()
    assert any(c["id"] == DUPLICATE_ID for c in initial["customers"])
    assert initial["lastWrites"] == []

    # 2. duplicateError — an existing id submitted: canonical refusal.
    dup_out = dispatch_c1("customer_create", {
        "id": DUPLICATE_ID, "name": "An Phát JSC (bản thử trùng)",
        "requestId": "CCT-FIX-DUP-1",
    })
    assert not dup_out["ok"] and "đã tồn tại" in dup_out["error"], dup_out
    assert dup_out.get("requestId") == "CCT-FIX-DUP-1", "the refusal must echo the requestId"
    st.session_state[vm.LAST_WRITES_KEY] = [dup_out]
    duplicate_error = vm.build_view_model()
    assert not any(c["id"] == "CUST-MOI" for c in duplicate_error["customers"])

    # 3. createOk — the ONE real create, end to end.
    ok_out = dispatch_c1("customer_create", {
        "id": NEW_ID, "name": "Công ty Mới (fixture)",
        "taxCode": "0109998877", "contactPerson": "Hà (fixture)",
        "phone": "0987654321", "address": "KCN Quế Võ, Bắc Ninh",
        "requestId": "CCT-FIX-OK-1",
    })
    assert ok_out["ok"], ok_out["error"]
    assert ok_out.get("requestId") == "CCT-FIX-OK-1", "the outcome must echo the requestId"
    assert ok_out["readback"]["id"] == NEW_ID
    st.session_state[vm.LAST_WRITES_KEY] = [ok_out]
    create_ok = vm.build_view_model()
    assert any(c["id"] == NEW_ID for c in create_ok["customers"]), \
        "the fresh view-model must contain the newly created customer"

    # 4. unrelatedChange — an UNRELATED write (edit on a different customer)
    #    lands while a create intent is still in flight: the version really
    #    changes and lastWrites carries only the customer_edit outcome, so it
    #    must never be consumed as the answer to a pending create.
    st.session_state.pop(vm.LAST_WRITES_KEY, None)
    baseline = vm.build_view_model()
    unrelated_out = dispatch_c1("customer_edit", {
        "id": "CUST-DUCLONG", "note": "ghi chú liên quan regression — không phải create",
        "requestId": "CCT-FIX-UNRELATED-1",
    })
    assert unrelated_out["ok"], unrelated_out["error"]
    assert unrelated_out["event"] == "customer_edit"
    st.session_state[vm.LAST_WRITES_KEY] = [unrelated_out]
    unrelated_change = vm.build_view_model()
    assert unrelated_change["version"] != baseline["version"], \
        "the unrelated write must genuinely change the payload version"
    assert not any(w.get("event") == "customer_create"
                   for w in unrelated_change["lastWrites"]), \
        "no customer_create outcome may be present in the unrelated state"

    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)

    payload = {
        "generatedFrom": "scripts/gen_customer_create_fixture.py — isolated mongomock staging",
        "duplicateId": DUPLICATE_ID,
        "newId": NEW_ID,
        "initial": initial,
        "duplicateError": duplicate_error,
        "createOk": create_ok,
        "unrelatedChange": unrelated_change,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  initial: customers={len(initial['customers'])} lastWrites={len(initial['lastWrites'])}")
    print(f"  duplicateError: {duplicate_error['lastWrites'][0]['error']} "
          f"requestId={duplicate_error['lastWrites'][0].get('requestId')}")
    print(f"  createOk: hasNew={any(c['id'] == NEW_ID for c in create_ok['customers'])} "
          f"lastWrites={[(w['event'], w['ok'], w.get('requestId')) for w in create_ok['lastWrites']]}")
    print(f"  unrelatedChange: version_changed="
          f"{unrelated_change['version'] != baseline['version']} "
          f"lastWrites={[(w.get('event'), w.get('ok')) for w in unrelated_change['lastWrites']]}")

    logi_sandbox.reset_backend()


if __name__ == "__main__":
    main()
