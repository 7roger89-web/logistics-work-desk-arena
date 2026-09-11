#!/usr/bin/env python3
"""Generate the LOGI_PARTNER_CONTEXT_WORKSPACE_01 DOM-acceptance fixture.

Same contract as gen_c2d_fixture.py: boot the ISOLATED mongomock staging
transport (never production) and dump the real ``build_view_model()`` payload
verbatim, so the React bundle is driven by genuine backend truth rather than a
hand-written mock. This generator produces three states:

  1. ``empty``          — before any canonical payable exists: the picker has a
                          real partner (the authority_agents master record) but
                          NO finance row at all (UNKNOWN != ZERO proof),
  2. ``journey``        — after ONE partner obligation + ONE payment are recorded
                          through the SAME canonical C2B handlers the UI drives,
                          with ``AGT-PHUANH`` selected through the bounded
                          read-only dispatcher: real linked shipment + real
                          payable/paid/remaining per currency,
  3. ``unknownPartner`` — the same selection path for a partner key that does
                          not exist: the honest ``PARTNER_NOT_FOUND`` state.

Run:  python scripts/gen_partner_context_fixture.py
Out:  tests/component/fixtures/view_model_partner_context.json
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SHIPMENT = "LO-0308"
PARTNER = "AGT-PHUANH"
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_partner_context.json"


def main() -> None:
    import streamlit as st

    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "this fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.PARTNER_CONTEXT_KEY, None)

    # UNKNOWN != ZERO: a real partner exists, yet no payable is reported as 0.
    empty = vm.build_view_model()

    # Same partner, selected, BEFORE any canonical obligation exists: the finance
    # panel must say "chưa xác định", never 0.
    st.session_state[vm.PARTNER_CONTEXT_KEY] = PARTNER
    no_finance = vm.build_view_model()
    st.session_state.pop(vm.PARTNER_CONTEXT_KEY, None)

    seq = {"n": 0}

    def dispatch(name: str, payload: dict) -> list:
        seq["n"] += 1
        return vm.consume_phase_b_triggers(
            {"seq": 0}, {name: {"seq": seq["n"], "event": name, "payload": payload}}
        )

    obl = dispatch("partner_payable_record", {
        "shipmentId": SHIPMENT, "partnerId": PARTNER, "requestId": "PCX-FIX-OBL-1",
        "amount": 57_000_000, "currency": "VND",
        "note": "Phải trả chi phí đối tác theo thực tế lô",
    })[0]
    assert obl["ok"], obl["error"]
    pay = dispatch("partner_payment_record", {
        "shipmentId": SHIPMENT, "partnerId": PARTNER, "requestId": "PCX-FIX-PAY-1",
        "amount": 20_000_000, "currency": "VND", "date": "2026-09-10",
        "note": "Chuyển khoản thanh toán đối tác",
    })[0]
    assert pay["ok"], pay["error"]

    # The selection goes through the SAME bounded read-only dispatcher the UI
    # uses, so the fixture carries exactly what a live click would deliver.
    chosen = vm.consume_partner_context_triggers({"seq": 0}, {"partner_context_select": {
        "seq": 900, "event": "partner_context_select", "payload": {"entityKey": f"  {PARTNER}  "},
    }})
    assert chosen[0]["ok"], chosen[0]["error"]
    journey = vm.build_view_model()

    st.session_state[vm.PARTNER_CONTEXT_KEY] = "AGT-KHONG-TON-TAI"
    missing = vm.build_view_model()
    st.session_state.pop(vm.PARTNER_CONTEXT_KEY, None)

    payload = {
        "generatedFrom": "scripts/gen_partner_context_fixture.py — isolated mongomock staging",
        "shipment": SHIPMENT,
        "partner": PARTNER,
        "journey": journey,
        "empty": empty,
        "noFinance": no_finance,
        "unknownPartner": missing,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    view = journey["partnerContext"]
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  status={view['status']} options={view['optionCount']} "
          f"linked={view['shipmentCount']} canOpen={[r['canOpen'] for r in view['shipments']]}")
    for row in view["finance"]["rows"]:
        print(f"    {row['shipmentId']} {row['currency']} payable={row['payable']} "
              f"paid={row['paid']} remaining={row['remaining']} status={row['status']}")
    print(f"  empty: status={empty['partnerContext']['status']} "
          f"financeRows={len(empty['partnerContext'].get('finance', {}).get('rows', []))} "
          f"payables={len(empty['payables']['rows'])}")
    nf = no_finance["partnerContext"]
    print(f"  noFinance: status={nf['status']} financeRows={len(nf['finance']['rows'])} "
          f"financeStatus={nf['finance']['status']} gaps={len(nf['gaps'])}")
    print(f"  unknown: status={missing['partnerContext']['status']}")


if __name__ == "__main__":
    main()
