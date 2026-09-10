#!/usr/bin/env python3
"""Generate the C2D DOM-acceptance fixture from the REAL Logistics backend.

The component DOM test must drive the built bundle with genuine backend truth
rather than a hand-written mock, so this script:

  1. boots the isolated staging transport (mongomock — never production),
  2. builds the real ``build_view_model()`` payload,
  3. establishes ONE partner payable + ONE real partner payment for ``LO-0308``
     through the SAME canonical C2B handlers the UI drives, then rebuilds the
     view model so the global ``payables`` worklist carries real rows,
  4. keeps the pre-write payload as ``empty`` to prove UNKNOWN != ZERO (no
     canonical payable ⇒ NO row, never a 0 payable).

Run:  python scripts/gen_c2d_fixture.py
Out:  tests/component/fixtures/view_model_c2d.json
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SHIPMENT = "LO-0308"
PARTNER = "AGT-PHUANH"
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_c2d.json"


def main() -> None:
    import streamlit as st

    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "this fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    # UNKNOWN != ZERO: before any canonical payable, the worklist is empty.
    empty = vm.build_view_model()

    seq = {"n": 0}

    def dispatch(name: str, payload: dict) -> list:
        seq["n"] += 1
        return vm.consume_phase_b_triggers(
            {"seq": 0}, {name: {"seq": seq["n"], "event": name, "payload": payload}}
        )

    obl = dispatch("partner_payable_record", {
        "shipmentId": SHIPMENT, "partnerId": PARTNER, "requestId": "C2D-FIX-OBL-1",
        "amount": 57_000_000, "currency": "VND",
        "note": "Phải trả chi phí đối tác theo thực tế lô",
    })[0]
    assert obl["ok"], obl["error"]
    pay = dispatch("partner_payment_record", {
        "shipmentId": SHIPMENT, "partnerId": PARTNER, "requestId": "C2D-FIX-PAY-1",
        "amount": 20_000_000, "currency": "VND", "date": "2026-09-10",
        "note": "Chuyển khoản thanh toán đối tác",
    })[0]
    assert pay["ok"], pay["error"]

    journey = vm.build_view_model()

    payload = {
        "generatedFrom": "scripts/gen_c2d_fixture.py — isolated mongomock staging",
        "shipment": SHIPMENT,
        "partner": PARTNER,
        "journey": journey,
        "empty": empty,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    payables = journey["payables"]
    print(f"wrote {OUT.relative_to(OUT.parents[3])}")
    print(f"  rows={len(payables['rows'])} totals={payables['totals']}")
    for row in payables["rows"]:
        print(f"    {row['shipmentId']} {row['partnerId']} {row['currency']} "
              f"pay={row['payable']} paid={row['paid']} rem={row['remaining']}")
    print(f"  empty rows={len(empty['payables']['rows'])}")


if __name__ == "__main__":
    main()
