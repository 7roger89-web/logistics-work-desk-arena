#!/usr/bin/env python3
"""Generate the C2A DOM-acceptance fixture from the REAL Logistics backend.

The component DOM test must drive the built bundle with genuine backend truth
rather than a hand-written mock, so this script:

  1. boots the isolated staging transport (mongomock — never production),
  2. runs the real C2A journey on ONE existing shipment through the canonical
     writers (``finance_actual_save`` then ``payment_record``),
  3. dumps the resulting ``build_view_model()`` payload,
  4. adds two in-memory probes built with the SAME projection code:
       * ``emptyBook`` — no booked actual line, to prove UNKNOWN != ZERO,
       * ``usd``       — a non-VND shipment, to prove currency explicitness
                         with no invented FX conversion.

Run:  python scripts/gen_c2a_fixture.py
Out:  tests/component/fixtures/view_model_c2a.json
"""

from __future__ import annotations

import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SHIPMENT = "LO-0308"
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_c2a.json"


def _dispatch(vm, state, name, payload):
    outcome = _dispatch_raw(vm, state, name, payload)
    assert outcome["ok"], f"{name} failed: {outcome['error']}"
    return outcome


def _dispatch_raw(vm, state, name, payload):
    """Run ONE event through the real bounded dispatcher, WITHOUT requiring ok.

    The journey uses the writer's genuine refusals too, so the fixture carries
    the backend's own Vietnamese validation message instead of an invented one.
    """
    state["n"] += 1
    event = {name: {"seq": state["n"], "event": name, "payload": payload}}
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, event)
    assert len(outcomes) == 1, outcomes
    return outcomes[0]


def main() -> None:
    import streamlit as st

    from views import logi_real_data as rd
    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "this fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    seq = {"n": 0}

    # --- the real journey: two actual lines, then one receipt ----------------
    _dispatch(vm, seq, "finance_actual_save", {
        "shipmentId": SHIPMENT,
        "line": {"name": "Phí nâng hạ container (thực tế)", "qty": 2,
                 "price": 1_500_000, "cost": 1_100_000, "vat": 8, "unit": "Lần"},
    })
    # LOGI_FINANCE_ACTUAL_ENTRY_PARITY_01 — a line entered through the restored
    # service picker: the canonical catalog supplies code + unit, and the note
    # is the operator's own. So the fixture carries one row WITH a service code
    # (the DOM test reads the code/unit/note back off the shipped projection).
    _dispatch(vm, seq, "finance_actual_save", {
        "shipmentId": SHIPMENT,
        "line": {"name": "Phí kiểm hóa", "code": "PKH", "unit": "Lần", "qty": 1,
                 "price": 1_200_000, "cost": 800_000, "vat": 0,
                 "note": "Theo thông báo của hải quan"},
    })
    _dispatch(vm, seq, "payment_record", {
        "shipmentId": SHIPMENT, "amount": 40_000_000,
        "requestId": "REQ-C2A-FIXTURE-1", "date": "2026-09-10",
        "note": "Thu tạm ứng đợt 1",
    })

    # The REAL refusal the repaired writer produces for a blank amount. The DOM
    # acceptance replays it through `lastWrites` to prove the UI shows the
    # backend's own message instead of pretending the line was saved.
    refusal = _dispatch_raw(vm, seq, "finance_actual_save", {
        "shipmentId": SHIPMENT,
        "line": {"name": "Phí làm hàng", "code": "DVK", "unit": "Lần", "qty": 1,
                 "price": "", "cost": "", "vat": ""},
    })
    assert refusal["ok"] is False, "the writer must refuse a blank actual amount"

    st.session_state[vm.LAST_WRITES_KEY] = []
    journey = vm.build_view_model()
    # A refused write books nothing, so the state the operator sees afterwards is
    # the SAME fresh view model with only `lastWrites` carrying the writer's real
    # outcome. That is asserted below instead of shipping a second full model.
    st.session_state[vm.LAST_WRITES_KEY] = [refusal]
    after_refusal = vm.build_view_model()
    assert after_refusal["shipments"] == journey["shipments"], \
        "a refused actual line must not change any shipment projection"
    # Only the authoritative outcome is carried; the DOM acceptance splices it
    # onto `journey` as `lastWrites`, because the refusal changed nothing else.
    refusal_outcome = after_refusal["lastWrites"][0]

    # --- probes: same projection code, in-memory only ------------------------
    base_ship = vm.read_shipment(SHIPMENT)

    def _variant(**overrides):
        ship = copy.deepcopy(base_ship)
        ship.update(overrides)
        return ship

    # Same shipment id in every variant so the DOM test can open the same
    # route (/lo-hang/LO-0308) against each backend state.
    empty_doc = _variant(data={
        **base_ship["data"],
        "3.4": {"details": [], "payments": [], "commission": {"total": 0}}})
    usd_doc = _variant(currency="USD", data={
        **base_ship["data"],
        "3.4": {"details": [{
            "id": "USD-1", "name_full": "Ocean freight HCM → LA",
            "display_name": "Ocean freight HCM → LA", "unit": "Cont",
            "qty": 1, "price": 4200.0, "cost": 3600.0, "vat_line": 0.0}],
            "payments": [], "commission": {"total": 0}}})

    def _model_for(doc):
        model = copy.deepcopy(journey)
        for index, row in enumerate(model["shipments"]):
            if row["id"] == SHIPMENT:
                fresh = rd.shipment_projection(doc, history=rd.timeline_projection(SHIPMENT))
                model["shipments"][index] = fresh
                break
        return model

    payload = {
        "generatedFrom": "scripts/gen_c2a_fixture.py — isolated mongomock staging",
        "shipment": SHIPMENT,
        "journey": journey,
        "emptyBook": _model_for(empty_doc),
        "usd": _model_for(usd_doc),
        # The bounded dispatcher's own outcome for a blank actual line: the real
        # refusal (ok=false + Vietnamese message) the operator must be shown.
        "refusal": refusal_outcome,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    fin = next(r for r in journey["shipments"] if r["id"] == SHIPMENT)["finance"]
    print(f"wrote {OUT.relative_to(OUT.parents[3])}")
    print(f"  journey  currency={fin['currency']} receivable={fin['receivable']} "
          f"received={fin['received']} outstanding={fin['outstanding']} "
          f"profit={fin['profit']} margin={fin['profitMargin']}%")
    efin = next(r for r in payload["emptyBook"]["shipments"] if r["id"] == SHIPMENT)["finance"]
    ufin = next(r for r in payload["usd"]["shipments"] if r["id"] == SHIPMENT)["finance"]
    print(f"  emptyBook profit={efin['profit']} margin={efin['profitMargin']} hasActualLines={efin['hasActualLines']}")
    print(f"  usd      currency={ufin['currency']} receivableNet={ufin['receivableNet']} profit={ufin['profit']}")
    print(f"  refusal  ok={refusal_outcome['ok']} error={refusal_outcome['error']}")


if __name__ == "__main__":
    main()
