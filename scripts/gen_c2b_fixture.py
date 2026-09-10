#!/usr/bin/env python3
"""Generate the C2B DOM-acceptance fixture from the REAL Logistics backend.

Same contract as ``gen_c2a_fixture.py``: the component DOM test must drive the
built bundle with genuine backend truth, so this script:

  1. boots the isolated staging transport (mongomock — never production),
  2. runs the real C2B journey on ONE existing shipment (``LO-0308``) and ONE
     existing partner (``AGT-PHUANH``) through the canonical writers —
     ``partner_payable_record`` then ``partner_payment_record``,
  3. dumps the resulting ``build_view_model()`` payload,
  4. adds one in-memory probe built with the SAME projection code:
       * ``noLedger`` — the same shipment before any canonical obligation or
         payment record exists, to prove UNKNOWN != ZERO in the partner block.

Run:  python scripts/gen_c2b_fixture.py
Out:  tests/component/fixtures/view_model_c2b.json
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SHIPMENT = "LO-0308"
PARTNER = "AGT-PHUANH"
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_c2b.json"


def _dispatch(vm, state, name, payload):
    state["n"] += 1
    event = {name: {"seq": state["n"], "event": name, "payload": payload}}
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, event)
    assert len(outcomes) == 1, outcomes
    assert outcomes[0]["ok"], f"{name} failed: {outcomes[0]['error']}"
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

    # --- probe state FIRST: the shipment BEFORE any canonical ledger row -----
    # finance_projection reads the canonical ledger by shipment id, so the
    # no-ledger variant must be captured before the journey writes anything.
    no_ledger = vm.build_view_model()

    # --- the real journey: one partner payable, then one real payment --------
    _dispatch(vm, seq, "partner_payable_record", {
        "shipmentId": SHIPMENT, "partnerId": PARTNER,
        "requestId": "REQ-C2B-FIXTURE-OBL-1", "amount": 57_000_000,
        "currency": "VND", "note": "Phải trả cước xe TQ theo chi phí thực tế",
    })
    _dispatch(vm, seq, "partner_payment_record", {
        "shipmentId": SHIPMENT, "partnerId": PARTNER,
        "requestId": "REQ-C2B-FIXTURE-PAY-1", "amount": 20_000_000,
        "currency": "VND", "date": "2026-09-10",
        "note": "Chuyển khoản thanh toán đối tác đợt 1",
    })

    journey = vm.build_view_model()

    payload = {
        "generatedFrom": "scripts/gen_c2b_fixture.py — isolated mongomock staging",
        "shipment": SHIPMENT,
        "partner": PARTNER,
        "journey": journey,
        "noLedger": no_ledger,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    fin = next(r for r in journey["shipments"] if r["id"] == SHIPMENT)["finance"]["partner"]
    print(f"wrote {OUT.relative_to(OUT.parents[3])}")
    print(f"  journey  partner={fin['partnerId']} ({fin['partnerName']}) "
          f"payable={fin['payable']} paid={fin['paid']} remaining={fin['remaining']} "
          f"currency={fin['currency']} payments={len(fin['payments'])}")
    none_fin = next(r for r in payload["noLedger"]["shipments"] if r["id"] == SHIPMENT)["finance"]["partner"]
    print(f"  noLedger payable={none_fin['payable']} paid={none_fin['paid']} "
          f"remaining={none_fin['remaining']} suggested={none_fin['suggested']}")


if __name__ == "__main__":
    main()
