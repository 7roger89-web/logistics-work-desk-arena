#!/usr/bin/env python3
"""Generate the LOGI_CEO_REPORT_01 DOM-acceptance fixture.

The fixture is produced from the real, isolated mongomock staging view-model —
never from hand-written browser data and never from production. It captures:

* ``empty``: normal operational/C2C data but no canonical C2D/reconciliation
  record, which the CEO page must describe as missing/unknown rather than 0;
* ``journey``: canonical VND and CNY obligations/payments recorded through the
  existing C2D handlers, so currency separation and match-state passthrough are
  visible in the production React bundle.

Run:  .venv/bin/python scripts/gen_ceo_report_fixture.py
Out:  tests/component/fixtures/view_model_ceo_report.json
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_ceo_report.json"

PARTNER = "AGT-PHUANH"

# (shipment, obligation request id, amount, currency, payment amount or None)
CASES = (
    ("LO-0308", "CEO-FIX-MATCHED", 10_000_000, "VND", 10_000_000),
    ("LO-0307", "CEO-FIX-PARTIAL", 50_000_000, "VND", 20_000_000),
    ("LO-0306", "CEO-FIX-UNMATCHED", 3_000, "CNY", None),
)


def main() -> None:
    import streamlit as st

    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.RECONCILIATION_FILTER_KEY, None)

    empty = vm.build_view_model()
    assert empty["ceoReport"]["payables"]["hasCanonicalRecords"] is False
    assert empty["ceoReport"]["reconciliation"]["status"] == "EMPTY"

    sequence = {"value": 0}

    def dispatch(event: str, payload: dict) -> dict:
        sequence["value"] += 1
        outcomes = vm.consume_phase_b_triggers(
            {"seq": 0},
            {event: {"seq": sequence["value"], "event": event, "payload": payload}},
        )
        assert len(outcomes) == 1
        assert outcomes[0]["ok"], outcomes[0].get("error")
        return outcomes[0]

    for shipment_id, request_id, amount, currency, payment_amount in CASES:
        dispatch("partner_payable_record", {
            "shipmentId": shipment_id,
            "partnerId": PARTNER,
            "requestId": request_id,
            "amount": amount,
            "currency": currency,
            "note": "Phải trả chi phí đối tác theo thực tế lô",
        })
        if payment_amount is not None:
            dispatch("partner_payment_record", {
                "shipmentId": shipment_id,
                "partnerId": PARTNER,
                "requestId": f"{request_id}:PAY",
                "amount": payment_amount,
                "currency": currency,
                "date": "2026-09-10",
                "note": "Chuyển khoản thanh toán đối tác",
            })

    journey = vm.build_view_model()
    report = journey["ceoReport"]
    assert {row["currency"] for row in report["payables"]["positions"]} == {"VND", "CNY"}
    assert report["reconciliation"]["available"] is True

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "generatedFrom": "scripts/gen_ceo_report_fixture.py — isolated mongomock staging",
                "empty": empty,
                "journey": journey,
            },
            ensure_ascii=False,
            indent=1,
            default=str,
        ),
        encoding="utf-8",
    )

    print(f"wrote {OUT.relative_to(ROOT)}")
    print(
        "  empty: "
        f"shipments={empty['ceoReport']['operations']['totalShipmentCount']} "
        f"receivableCurrencies={[r['currency'] for r in empty['ceoReport']['receivables']['positions']]} "
        f"payableRecords={empty['ceoReport']['payables']['recordCount']} "
        f"reconciliation={empty['ceoReport']['reconciliation']['status']}"
    )
    print(
        "  journey: "
        f"payableCurrencies={[r['currency'] for r in report['payables']['positions']]} "
        f"obligations={report['reconciliation']['obligations']} "
        f"money={report['reconciliation']['money']}"
    )

    logi_sandbox.reset_backend()


if __name__ == "__main__":
    main()
