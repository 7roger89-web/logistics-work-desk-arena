#!/usr/bin/env python3
"""Generate the LOGI-195 DOM acceptance fixture.

The payload is never hand-written: it is produced by the SAME staging stack
the app runs (logi_sandbox mongomock, the real dispatcher, the real
persistence and the real bounded projections).

Two shipments are baked in:
  SEA-160  — the canonical populated Journey (11 nodes), WITH customer_id.
  SEA-195  — the same shape but WITHOUT customer_id while keeping the exact
             master customer name, so Issue #197 proves one-click legacy
             identity repair instead of asking for the same customer twice.

The picker catalog is recomputed with the REAL server function
``core.shipment_document_catalog.project_catalog`` with
pxk_template_available=False, i.e. the honest "generator currently
unavailable" state the server itself produces when the template asset is
missing — selection must stay allowed while generation stays blocked.

Run:  python3 scripts/gen_logi195_dom_fixture.py --fixture /tmp/logi195-dom.json
Then: node tests/component/dom_acceptance_logi195_compact_journey_smooth.mjs /tmp/logi195-dom.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import runpy
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="/tmp/logi195-dom.json")
    args = parser.parse_args()

    import streamlit as st

    from core.database import save_shipment_atomic
    from core.shipment_document_catalog import project_catalog
    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    helper = runpy.run_path(str(ROOT / "tests/test_visual_shipment_workspace.py"))
    doc = helper["document"]()
    doc.pop("version", None)
    assert save_shipment_atomic(doc, actor="issue195-browser-fixture")

    # Legacy name-only twin: the canonical id is missing, but the stored name
    # still exactly identifies ONE customer master. Issue #197 must reuse that
    # identity on the commercial-flow save instead of forcing a second picker.
    doc2 = helper["document"]()
    doc2["id"] = "SEA-195"
    doc2.pop("version", None)
    doc2.pop("customer_id", None)
    doc2["customer"] = "An Phát JSC"
    doc2["client"] = "An Phát JSC"
    assert save_shipment_atomic(doc2, actor="issue195-browser-fixture")
    st.session_state[vm.LAST_WRITES_KEY] = []

    model = vm.build_view_model()
    model["lastWrites"] = []

    # Honest unavailable-generator state through the real server projection.
    picker = dict(model["shipmentDocumentPicker"])
    picker["catalog"] = project_catalog(
        contract_templates_available=True,
        pxk_template_available=False,
        storage_configured=True,
        catalog=vm._effective_document_catalog(),
    )
    model["shipmentDocumentPicker"] = picker

    node_ids = [n["id"] for n in next(
        r for r in model["shipments"] if r["id"] == "SEA-160")["journey"]["nodes"]]
    no_cust = next(r for r in model["shipments"] if r["id"] == "SEA-195")
    assert not no_cust.get("customerId"), "SEA-195 must lack customer_id"

    payload = {
        "viewModel": model,
        "expected": {
            "shipmentId": "SEA-160",
            "noCustomerShipmentId": "SEA-195",
            "nodeIds": node_ids,
            "unavailableTemplateId": "PXK",
        },
    }
    pathlib.Path(args.fixture).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {args.fixture}: {len(node_ids)} journey nodes, "
          f"catalog={len(picker['catalog'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
