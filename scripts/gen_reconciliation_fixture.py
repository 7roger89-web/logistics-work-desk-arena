#!/usr/bin/env python3
"""Generate the LOGI_RECONCILIATION_DESK_01 DOM-acceptance fixture.

Same contract as gen_partner_context_fixture.py: boot the ISOLATED mongomock
staging transport (never production) and dump the real ``build_view_model()``
payload verbatim, so the React bundle is driven by genuine backend truth rather
than a hand-written mock. Every obligation and payment below is recorded through
the SAME canonical C2B/C2D handlers the UI drives.

Four states, one per shipment so the allocation outcome is deterministic (the
payment handler allocates to the first OPEN obligation of that shipment):

  ``empty``            — before any canonical record exists: the desk is EMPTY
                         with no rows and no totals (UNKNOWN != ZERO — never a
                         balanced 0 book).
  ``journey``          — MATCHED (LO-0308 paid in full), PARTIAL (LO-0307 part
                         paid), UNMATCHED (LO-0306 unpaid) in VND, plus a CNY
                         obligation on LO-0299 so currency separation is visible.
  ``matchedOnly``      — the same ledger after ONE bounded read-only
                         ``reconciliation_filter`` intent (state=MATCHED).
  ``cnyOnly``          — the same ledger after a currency=CNY filter, proving
                         currencies are never summed together.

Run:  python scripts/gen_reconciliation_fixture.py
Out:  tests/component/fixtures/view_model_reconciliation.json
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PARTNER = "AGT-PHUANH"
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_reconciliation.json"

# (shipment, obligation request id, amount, currency, payment amount or None)
CASES = [
    ("LO-0308", "REC-FIX-OBL-MATCHED", 10_000_000, "VND", 10_000_000),   # MATCHED
    ("LO-0307", "REC-FIX-OBL-PARTIAL", 50_000_000, "VND", 20_000_000),   # PARTIAL
    ("LO-0306", "REC-FIX-OBL-UNMATCHED", 7_000_000, "VND", None),        # UNMATCHED
    ("LO-0299", "REC-FIX-OBL-CNY", 3_000, "CNY", 1_000),                 # PARTIAL, CNY
]


def main() -> None:
    import streamlit as st

    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "this fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.RECONCILIATION_FILTER_KEY, None)

    # UNKNOWN != ZERO: nothing recorded yet, so the desk must be EMPTY, not 0.
    empty = vm.build_view_model()

    seq = {"n": 0}

    def dispatch(name: str, payload: dict) -> list:
        seq["n"] += 1
        return vm.consume_phase_b_triggers(
            {"seq": 0}, {name: {"seq": seq["n"], "event": name, "payload": payload}}
        )

    for shipment, request_id, amount, currency, paid in CASES:
        obligation = dispatch("partner_payable_record", {
            "shipmentId": shipment, "partnerId": PARTNER, "requestId": request_id,
            "amount": amount, "currency": currency,
            "note": "Phải trả chi phí đối tác theo thực tế lô",
        })[0]
        assert obligation["ok"], obligation["error"]
        if paid is None:
            continue
        payment = dispatch("partner_payment_record", {
            "shipmentId": shipment, "partnerId": PARTNER,
            "requestId": f"{request_id}:PAY", "amount": paid, "currency": currency,
            "date": "2026-09-10", "note": "Chuyển khoản thanh toán đối tác",
        })[0]
        assert payment["ok"], payment["error"]

    journey = vm.build_view_model()

    # The filters go through the SAME bounded read-only dispatcher the UI uses,
    # so each fixture carries exactly what a live tap would deliver.
    def apply_filter(seq_no: int, payload: dict) -> dict:
        outcomes = vm.consume_reconciliation_triggers(
            {"seq": 0},
            {"reconciliation_filter": {"seq": seq_no, "event": "reconciliation_filter", "payload": payload}},
        )
        assert outcomes and outcomes[0]["ok"], outcomes
        return vm.build_view_model()

    matched_only = apply_filter(901, {"query": "", "currency": "ALL", "state": "MATCHED", "side": "obligation"})
    cny_only = apply_filter(902, {"query": "", "currency": "CNY", "state": "ALL", "side": "ALL"})
    st.session_state.pop(vm.RECONCILIATION_FILTER_KEY, None)

    payload = {
        "generatedFrom": "scripts/gen_reconciliation_fixture.py — isolated mongomock staging",
        "partner": PARTNER,
        "empty": empty,
        "journey": journey,
        "matchedOnly": matched_only,
        "cnyOnly": cny_only,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    def report(label: str, model: dict) -> None:
        view = model["reconciliation"]
        states = sorted({r["matchState"] for r in view["rows"] if r["matchState"]})
        print(f"  {label}: status={view['status']} visible={view['visibleCount']}/{view['totalCount']} "
              f"currencies={view['currencies']} states={states}")
        for row in view["rows"]:
            print(f"    {row['shipmentId']} {row['side']:10} {row['currency']:7} "
                  f"amount={row['amount']} allocated={row['allocated']} remaining={row['remaining']} "
                  f"state={row['matchState']} tx={row['transactionIds']} canOpen={row['canOpen']}")

    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  empty: status={empty['reconciliation']['status']} "
          f"rows={len(empty['reconciliation']['rows'])} totals={empty['reconciliation']['totals']}")
    report("journey", journey)
    report("matchedOnly", matched_only)
    report("cnyOnly", cny_only)


if __name__ == "__main__":
    main()
