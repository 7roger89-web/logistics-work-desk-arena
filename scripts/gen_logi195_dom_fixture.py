#!/usr/bin/env python3
"""Generate the LOGI-195 DOM acceptance fixture.

The payload is never hand-written: it is produced by the SAME staging stack
the app runs (logi_sandbox mongomock, the real dispatcher, the real
persistence and the real bounded projections).

Two shipments are baked in:
  SEA-160  — the canonical populated Journey (11 nodes), WITH customer_id.
  SEA-195  — the same shape but WITHOUT customer_id, so the CUSTOMER_SELF
             recovery path is exercised against real backend truth.

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
import hashlib
import json
import pathlib
import runpy
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="/tmp/logi195-dom.json")
    # Opt-in: attach distinct metadata rows through the canonical writer so a
    # DOM lane can challenge node-scoped document filtering with REAL
    # documentIds computed by the same backend projection. Off by default so
    # every existing fixture consumer keeps its old payload.
    parser.add_argument("--with-attachments", action="store_true")
    # Opt-in: add one TT_ENTRUSTED_SUB shipment whose legal importer is a real
    # authority_companies row (A) while the contract agent is a different
    # authority_agents row (B), plus its historical twin with no company link.
    parser.add_argument("--entrusted-sub", action="store_true")
    args = parser.parse_args()

    import streamlit as st

    from core.database import (
        save_authority_agent,
        save_authority_company,
        save_shipment_attachment,
        save_shipment_atomic,
    )
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

    attachment_ids: list[str] = []
    if args.with_attachments:
        for category in ("si", "vgm", "booking", "transport", "customs"):
            attachment_id = f"fixture-{category}-199"
            assert save_shipment_attachment({
                "id": attachment_id,
                "shipment_id": doc["id"],
                "original_name": f"only-{category}-199.pdf",
                "sha256": hashlib.sha256(category.encode()).hexdigest(),
                "storage_file_id": f"fixture-storage-{category}",
                "storage_backend": "gridfs",
                "category": category,
                "original_size": 100,
                "stored_size": 100,
                "uploaded_at": "2026-10-16T00:00:00Z",
                "uploaded_by": "fixture",
            }), category
            attachment_ids.append(attachment_id)

    # The customer-less twin: identical journey shape, but only a typed name
    # with NO canonical customer_id — the real reachable state the CUSTOMER_SELF
    # identity gate guards (a typed name never becomes a legal identity).
    doc2 = helper["document"]()
    doc2["id"] = "SEA-195"
    doc2.pop("version", None)
    doc2.pop("customer_id", None)
    doc2["customer"] = "Khách lẻ chưa vào danh bạ"
    assert save_shipment_atomic(doc2, actor="issue195-browser-fixture")

    if args.entrusted_sub:
        # Explicit FIXTURE masters only — never claims about real companies.
        assert save_authority_company({
            "company_id": "FIX-TT",
            "legal_name": "CÔNG TY TNHH TRƯỜNG THÀNH (FIXTURE)",
            "tax_or_legal_code": "0109988776",
        })
        assert save_authority_company({
            "company_id": "FIX-IMP-A",
            "legal_name": "CÔNG TY TNHH ĐỐI TÁC NHẬP KHẨU HỘ A (FIXTURE)",
            "tax_or_legal_code": "0317000001",
        })
        assert save_authority_agent({
            "agent_id": "FIX-CONTRACT-B",
            "legal_name": "CÔNG TY TNHH ĐẠI LÝ HỢP ĐỒNG B (FIXTURE)",
            "legal_code": "0317000002",
        })
        from core import database as core_database

        db = core_database.get_db()
        for shipment_id, flow in (
            ("SEA-160", {
                "mode": "TT_ENTRUSTED_SUB",
                "confirmed": True,
                "company_id": "FIX-TT",
                "sub_agent_id": "FIX-CONTRACT-B",
                "importer_company_id": "FIX-IMP-A",
            }),
            # Historical shape: confirmed SUB, only the agent relation saved.
            ("SEA-195", {
                "mode": "TT_ENTRUSTED_SUB",
                "confirmed": True,
                "company_id": "FIX-TT",
                "sub_agent_id": "FIX-CONTRACT-B",
            }),
        ):
            stored = db["shipments"].find_one({"id": shipment_id})
            assert stored is not None, shipment_id
            stored.setdefault("data", {}).setdefault("0.0", {})["commercial_flow"] = flow
            db["shipments"].replace_one({"id": shipment_id}, stored)

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
            "attachmentIds": attachment_ids,
            "entrustedSub": {
                "shipmentId": "SEA-160",
                "legacyShipmentId": "SEA-195",
                "signingCompanyId": "FIX-TT",
                "importerCompanyId": "FIX-IMP-A",
                "importerName": "CÔNG TY TNHH ĐỐI TÁC NHẬP KHẨU HỘ A (FIXTURE)",
                "importerTaxCode": "0317000001",
                "contractAgentId": "FIX-CONTRACT-B",
                "contractAgentName": "CÔNG TY TNHH ĐẠI LÝ HỢP ĐỒNG B (FIXTURE)",
            } if args.entrusted_sub else {},
        },
    }
    pathlib.Path(args.fixture).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {args.fixture}: {len(node_ids)} journey nodes, "
          f"catalog={len(picker['catalog'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
