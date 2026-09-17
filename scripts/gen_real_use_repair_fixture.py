#!/usr/bin/env python3
"""Generate the LOGI_UAT_REAL_USE_REPAIR_02 DOM-acceptance fixture.

Same contract as scripts/gen_create_shipment_fixture.py: boot the ISOLATED
mongomock staging transport (never production) and dump real
``build_view_model()`` payloads. Every write goes through the SAME bounded
dispatcher the UI drives, and its outcome is stored under
``st.session_state["logi_last_writes"]`` exactly like
``views.logi_view_model.dispatch()`` does, so ``lastWrites`` in each state is
the genuine backend readback.

States:

  1. ``initial``          — before any customer create: CUST-UAT02 absent,
                            no lastWrites.
  2. ``createOk``         — after ONE real ``customer_create`` went through
                            RBAC → save_customer_to_cloud → audit → fresh
                            read: the fresh view-model CONTAINS the customer
                            and lastWrites carries ok=True WITH the echoed
                            requestId.
  3. ``duplicateError``   — the SAME id submitted again: the canonical
                            duplicate refusal (ok=False) the modal must show
                            verbatim while keeping the operator's data.
  4. ``rbacError``        — a VIEWER attempt refused by RBAC (ok=False).
  5. ``unrelatedChange``  — an UNRELATED backend write lands while the create
                            intent is still unanswered: the version genuinely
                            changes, yet NO customer_create outcome for the
                            pending requestId exists — this must NOT be
                            treated as success.

The DOM test rewrites each state's ``requestId`` to the one the real click
produced before invoking, exactly matching live behaviour.

Run:  python scripts/gen_real_use_repair_fixture.py
Out:  tests/component/fixtures/view_model_real_use_repair.json
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CUSTOMER_ID = "CUST-UAT02"
CUSTOMER_NAME = "Khách UAT02"
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_real_use_repair.json"


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
        assert len(outcomes) == 1, outcomes
        return outcomes[0]

    def dispatch_phase_b(name: str, payload: dict) -> dict:
        seq["n"] += 1
        outcomes = vm.consume_phase_b_triggers(
            {"seq": 0},
            {name: {"seq": seq["n"], "event": name, "payload": payload}},
        )
        assert len(outcomes) == 1, outcomes
        return outcomes[0]

    # 1. initial — the customer page before any create intent.
    initial = vm.build_view_model()
    assert not any(c["id"] == CUSTOMER_ID for c in initial["customers"])
    assert initial["lastWrites"] == []

    create_payload = {
        "id": CUSTOMER_ID,
        "name": CUSTOMER_NAME,
        "phone": "0900000002",
        "email": "uat02@example.com",
        "contactPerson": "Chị Hai",
        "taxCode": "0102030402",
        "address": "KCN UAT, Bắc Ninh",
        "note": "fixture UAT02",
        "requestId": "CUST-FIX-OK-1",
    }

    # 2. createOk — the ONE real create, end to end.
    ok_out = dispatch_c1("customer_create", dict(create_payload))
    assert ok_out["ok"], ok_out["error"]
    assert ok_out.get("requestId") == "CUST-FIX-OK-1", \
        "the backend MUST echo the requestId so the UI can correlate the outcome"
    st.session_state[vm.LAST_WRITES_KEY] = [ok_out]
    create_ok = vm.build_view_model()
    assert any(c["id"] == CUSTOMER_ID for c in create_ok["customers"]), \
        "the fresh view-model must contain the newly created customer"

    # 5. unrelatedChange — an UNRELATED write (field save on a shipment) lands
    #    while a create intent is still in flight: the version really changes
    #    but lastWrites carries NO customer_create outcome for that requestId.
    unrelated_out = dispatch_phase_b("shipment_field_save", {
        "shipmentId": "LO-0307",
        "fields": {"carrier": "Bộ (đường bộ TQ–VN) — unrelated regression write"},
        "requestId": "CUST-FIX-UNRELATED-1",
    })
    assert unrelated_out["ok"], unrelated_out["error"]
    st.session_state[vm.LAST_WRITES_KEY] = [unrelated_out]
    unrelated_change = vm.build_view_model()
    assert unrelated_change["version"] != create_ok["version"], \
        "the unrelated write must genuinely change the payload version"
    assert not any(w.get("event") == "customer_create"
                   for w in unrelated_change["lastWrites"]), \
        "no customer_create outcome may be present in the unrelated state"

    # 3. duplicateError — same id again: canonical refusal, nothing new written.
    dup_out = dispatch_c1("customer_create", dict(create_payload, requestId="CUST-FIX-DUP-1"))
    assert not dup_out["ok"] and "đã tồn tại" in dup_out["error"], dup_out
    assert dup_out.get("requestId") == "CUST-FIX-DUP-1"
    st.session_state[vm.LAST_WRITES_KEY] = [dup_out]
    duplicate_error = vm.build_view_model()

    # 4. rbacError — a VIEWER attempt refused by RBAC.
    st.session_state["current_user"] = {"username": "viewer.user", "role": "VIEWER",
                                        "user_id": "U-VIEWER"}
    rbac_out = dispatch_c1("customer_create",
                           dict(create_payload, id="CUST-UAT02B", requestId="CUST-FIX-RBAC-1"))
    assert not rbac_out["ok"] and "RBAC" in rbac_out["error"], rbac_out
    st.session_state[vm.LAST_WRITES_KEY] = [rbac_out]
    rbac_error = vm.build_view_model()
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)

    # The shipment the tab/handoff assertions run against: it must genuinely
    # carry a hyphenated nextRoute tab and a linked contract.
    shipments = create_ok["shipments"]
    hyphen_rows = [s for s in shipments if "?tab=" in s["nextRoute"]
                   and "-" in s["nextRoute"].split("?tab=")[1]]
    assert hyphen_rows, "no shipment carries a hyphenated nextRoute tab in this staging data"
    linked_rows = [s for s in shipments if s.get("contract")]
    assert linked_rows, "no shipment carries a linked contract in this staging data"

    payload = {
        "generatedFrom": "scripts/gen_real_use_repair_fixture.py — isolated mongomock staging",
        "customerId": CUSTOMER_ID,
        "customerName": CUSTOMER_NAME,
        "hyphenTabShipment": hyphen_rows[0]["id"],
        "hyphenTabRoute": hyphen_rows[0]["nextRoute"],
        "linkedContractShipment": linked_rows[0]["id"],
        "linkedContractId": linked_rows[0]["contract"],
        "initial": initial,
        "createOk": create_ok,
        "duplicateError": duplicate_error,
        "rbacError": rbac_error,
        "unrelatedChange": unrelated_change,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  initial: customers={len(initial['customers'])} lastWrites={len(initial['lastWrites'])}")
    print(f"  createOk: lastWrites={[(w['event'], w['ok'], w.get('requestId')) for w in create_ok['lastWrites']]}")
    print(f"  duplicateError: {duplicate_error['lastWrites'][0]['error']}")
    print(f"  rbacError: {rbac_error['lastWrites'][0]['error']}")
    print(f"  hyphen tab row: {payload['hyphenTabShipment']} → {payload['hyphenTabRoute']}")
    print(f"  linked contract row: {payload['linkedContractShipment']} → {payload['linkedContractId']}")

    logi_sandbox.reset_backend()


if __name__ == "__main__":
    main()
