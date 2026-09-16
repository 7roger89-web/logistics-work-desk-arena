#!/usr/bin/env python3
"""Generate the payment-correction DOM-acceptance fixture from the REAL backend.

Same contract as ``gen_c2b_fixture.py``: the component DOM test must drive the
built bundle with genuine backend truth, so this script:

  1. boots the isolated staging transport (mongomock — never production),
  2. records TWO real customer receipts on ``LO-0308`` through the canonical
     ``payment_record`` path (raw VN-formatted amounts),
  3. captures ``before`` — the view-model the sheet starts from,
  4. runs ONE real ``payment_correction`` (canonical reversal with evidence)
     through the same dispatcher against the second receipt,
  5. captures ``afterReversal`` — the fresh read model showing the row marked
     reversed and the derived totals moved by the backend,

and dumps both plus the outcome shapes the DOM test replays as the
authoritative ``lastWrites`` echo (the real backend messages, not invented
strings).

Run:  python scripts/gen_payment_correction_fixture.py
Out:  tests/component/fixtures/view_model_payment_correction.json
"""

from __future__ import annotations

import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SHIPMENT = "LO-0308"
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_payment_correction.json"


def _dispatch(vm, state, name, payload, expect_ok=True):
    state["n"] += 1
    event = {name: {"seq": state["n"], "event": name, "payload": payload}}
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, event)
    assert len(outcomes) == 1, outcomes
    if expect_ok:
        assert outcomes[0]["ok"], f"{name} failed: {outcomes[0]['error']}"
    return outcomes[0]


def main() -> None:
    import streamlit as st

    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "this fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    seq = {"n": 0}

    # --- two real receipts through the canonical write path ------------------
    first = _dispatch(vm, seq, "payment_record", {
        "shipmentId": SHIPMENT, "amount": "150.000.000",
        "requestId": "CORRUI-FIX-PAY-1", "date": "2026-09-08",
        "note": "Thu tiền khách",
    })
    second = _dispatch(vm, seq, "payment_record", {
        "shipmentId": SHIPMENT, "amount": "40.000.000",
        "requestId": "CORRUI-FIX-PAY-2", "date": "2026-09-09",
        "note": "Thu nốt công nợ",
    })
    corrected_id = first["paymentId"]   # the DOM journey reverses THIS row
    live_id = second["paymentId"]       # stays living for reopen/new-intent checks

    before = copy.deepcopy(vm.build_view_model())

    # --- the real correction: canonical reversal with optional evidence ------
    correction = _dispatch(vm, seq, "payment_correction", {
        "shipmentId": SHIPMENT,
        "paymentId": corrected_id,
        "correctionRequestId": "CORRUI-FIX-REQ-1",
        "reason": "Khách chuyển khoản sai nội dung — hoàn tác để ghi nhận lại",
        "amount": "1.200.000",
        "date": "10/09/2026",
        "note": "UNC 45 ngày 10/09",
    })
    after = copy.deepcopy(vm.build_view_model())

    # refusal replayed by the DOM test: the writer's OWN message for a second
    # new request against an already-reversed payment (no invented strings)
    refusal = _dispatch(vm, seq, "payment_correction", {
        "shipmentId": SHIPMENT,
        "paymentId": corrected_id,
        "correctionRequestId": "CORRUI-FIX-REQ-2",
        "reason": "Thử hoàn tác lần hai",
    }, expect_ok=False)

    payload = {
        "generatedFrom": "scripts/gen_payment_correction_fixture.py — isolated mongomock staging",
        "shipment": SHIPMENT,
        "paymentIds": {"corrected": corrected_id, "live": live_id},
        "before": before,
        "afterReversal": after,
        "successOutcome": {k: v for k, v in correction.items() if k != "readback"},
        "refusalOutcome": {k: v for k, v in refusal.items() if k != "readback"},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8"
    )

    fin_before = next(r for r in before["shipments"] if r["id"] == SHIPMENT)["finance"]
    fin_after = next(r for r in after["shipments"] if r["id"] == SHIPMENT)["finance"]
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  before: payments={[(p['id'], p['amount'], p['reversed']) for p in fin_before['payments']]} "
          f"received={fin_before['received']} outstanding={fin_before['outstanding']}")
    print(f"  after : payments={[(p['id'], p['amount'], p['reversed']) for p in fin_after['payments']]} "
          f"received={fin_after['received']} outstanding={fin_after['outstanding']}")
    print(f"  refusal message: {refusal['error']}")

    # sanity: the fixture must carry exactly the honest read-model facts the
    # UI shows — original row PRESERVED (reversed flag on), totals moved.
    ids_after = {p["id"]: p for p in fin_after["payments"]}
    assert corrected_id in ids_after and ids_after[corrected_id]["reversed"] is True
    assert ids_after[corrected_id]["amount"] == 150_000_000.0
    assert ids_after[live_id]["reversed"] is False


if __name__ == "__main__":
    main()
