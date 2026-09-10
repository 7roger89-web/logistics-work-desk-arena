#!/usr/bin/env python3
"""Generate the C2C DOM-acceptance fixture from the REAL Logistics backend.

The component DOM test must drive the built bundle with genuine backend truth
rather than a hand-written mock, so this script:

  1. boots the isolated staging transport (mongomock — never production),
  2. builds the real ``build_view_model()`` payload (which now carries the
     global ``receivables`` worklist),
  3. adds one in-memory probe — ``emptyBook``, a shipment with no booked actual
     line — built with the SAME projection code, to prove UNKNOWN != ZERO in
     the worklist.

Run:  python scripts/gen_c2c_fixture.py
Out:  tests/component/fixtures/view_model_c2c.json
"""

from __future__ import annotations

import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SHIPMENT = "LO-0308"
OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_c2c.json"


def main() -> None:
    import streamlit as st

    from views import logi_real_data as rd
    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "this fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    journey = vm.build_view_model()

    # --- probe: empty actual book on the same shipment ----------------------
    base_ship = vm.read_shipment(SHIPMENT)
    empty_doc = copy.deepcopy(base_ship)
    empty_doc["data"]["3.4"] = {"details": [], "payments": [], "commission": {"total": 0}}

    empty_book = copy.deepcopy(journey)
    for index, row in enumerate(empty_book["shipments"]):
        if row["id"] == SHIPMENT:
            empty_book["shipments"][index] = rd.shipment_projection(
                empty_doc, history=rd.timeline_projection(SHIPMENT)
            )
            break
    # Recompute the worklist from the modified shipment rows (same code path).
    empty_book["receivables"] = rd.receivables_projection(empty_book["shipments"])

    payload = {
        "generatedFrom": "scripts/gen_c2c_fixture.py — isolated mongomock staging",
        "shipment": SHIPMENT,
        "journey": journey,
        "emptyBook": empty_book,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    rec = journey["receivables"]
    print(f"wrote {OUT.relative_to(OUT.parents[3])}")
    print(f"  rows={len(rec['rows'])} totals={rec['totals']}")
    for row in rec["rows"]:
        print(f"    {row['id']} {row['customer']} {row['currency']} "
              f"recv={row['receivable']} rcvd={row['received']} out={row['outstanding']}")
    erow = next(r for r in empty_book["receivables"]["rows"] if r["id"] == SHIPMENT)
    print(f"  emptyBook row: receivable={erow['receivable']} outstanding={erow['outstanding']} "
          f"hasActualLines={erow['hasActualLines']}")


if __name__ == "__main__":
    main()
