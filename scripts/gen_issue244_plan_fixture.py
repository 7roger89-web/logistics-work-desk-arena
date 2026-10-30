#!/usr/bin/env python3
"""Generate the Issue #244 (Node 00 KẾ HOẠCH) DOM-acceptance fixture.

The DOM test must drive the REAL built bundle with REAL backend truth, so this
script:

  1. boots the isolated staging transport (mongomock — never production),
  2. builds the real ``build_view_model()`` payload,
  3. replaces three existing shipment rows with projections built by the SAME
     ``views.logi_real_data.shipment_projection`` over three explicit cases:

     * ``planEntrusted`` — LO-0306: TWO quotes for the same customer while the
       lot points at exactly one, a customer contract WITHOUT signature
       evidence, a TT↔sub-agent purchase contract that must never be reported
       as the customer contract, a confirmed ``TT_ENTRUSTED_DIRECT`` flow and
       two unclassified receipts.
     * ``planCustomerSelf`` — LO-0307: no quote at all, confirmed
       ``CUSTOMER_SELF`` flow (advance "Không áp dụng").
     * ``planUnknownFlow`` — LO-0308: no quote, no contract, import form NOT
       confirmed (advance "Chưa xác nhận hình thức nhập khẩu").

No write path is exercised: this fixture is read-only by construction.

Run:  python scripts/gen_issue244_plan_fixture.py
Out:  tests/component/fixtures/view_model_issue244_plan.json
"""

from __future__ import annotations

import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_issue244_plan.json"

ENTRUSTED = "LO-0306"
CUSTOMER_SELF = "LO-0307"
UNKNOWN_FLOW = "LO-0308"

#: The two same-customer quotes: the lot points at BG-244B, so BG-244A must
#: never appear anywhere in the rendered plan.
QUOTES = {
    "BG-244A": {
        "id": "BG-244A", "quote_no": "BG-244A", "customer_id": "CUST-ANPHAT",
        "status": "ACCEPTED", "total": 999_000_000, "currency": "VND",
    },
    "BG-244B": {
        "id": "BG-244B", "quote_no": "BG-244B", "customer_id": "CUST-ANPHAT",
        "status": "SENT", "total": 385_000_000, "currency": "VND",
    },
}

CUSTOMER_CONTRACT = {
    "id": "HDMB-244", "contract_no": "HDMB-244", "shipment_ids": [ENTRUSTED],
    "customer_id": "CUST-ANPHAT", "customer": "An Phát JSC", "status": "active",
}
SUB_AGENT_CONTRACT = {
    "id": "HDMB-SUB-244", "contract_no": "HDMB-SUB-244", "shipment_ids": [ENTRUSTED],
    "agent_id": "AGT-PHUANH", "company_id": "TT-COMPANY", "status": "active",
}
CONTRACTS = {row["id"]: row for row in (CUSTOMER_CONTRACT, SUB_AGENT_CONTRACT)}


def _plan_doc(shipment: dict, mode: str, *, quote_id: str = "") -> dict:
    """Apply ONE explicit plan scenario to a copy of a real shipment document."""
    doc = copy.deepcopy(shipment)
    doc["quote_id"] = quote_id
    head = doc.setdefault("data", {}).setdefault("0.0", {})
    if mode:
        head["commercial_flow"] = {
            "mode": mode, "confirmed": True,
            "company_id": "TT-COMPANY" if mode.startswith("TT_") else "",
            "sub_agent_id": "",
        }
    else:
        head.pop("commercial_flow", None)
    return doc


def main() -> None:
    import streamlit as st

    from views import logi_real_data as rd
    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "this fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    from core.database import _load_contracts_impl, _load_customers_impl
    from core.financial_ledger import load_ledger_snapshot

    model = vm.build_view_model()
    from core.database import get_db

    db = get_db()
    shipments = vm.load_shipments(db=db)
    customers = _load_customers_impl(db=db) or {}
    ledger = load_ledger_snapshot(db)

    def project(shipment_id: str, *, quote_id: str, mode: str,
                contracts: dict | None = None) -> dict:
        doc = _plan_doc(shipments[shipment_id], mode, quote_id=quote_id)
        contracts = contracts or {}
        linked = {shipment_id: contracts} if contracts else {}
        payments = [
            {"id": "P-244-1", "amount": 20_000_000, "note": "Khoản thu chưa phân loại",
             "date": "2026-10-20", "created_by": "sale1"},
        ] if shipment_id == ENTRUSTED else []
        doc.setdefault("data", {}).setdefault("3.4", {})["payments"] = payments
        row = rd.shipment_projection(
            doc,
            customers=customers,
            contracts=contracts,
            quotes=QUOTES if quote_id else {},
            linked_contracts=linked,
            agreements={},
            ledger=ledger,
            agents=agents,
            companies=companies,
            history=rd.timeline_projection(shipment_id, db=db),
        )
        return row

    from core.database import load_authority_agents, load_authority_companies

    agents = load_authority_agents(db=db) or {}
    companies = load_authority_companies(db=db) or {}
    rows = {
        ENTRUSTED: project(ENTRUSTED, quote_id="BG-244B", mode="TT_ENTRUSTED_DIRECT",
                           contracts=CONTRACTS),
        CUSTOMER_SELF: project(CUSTOMER_SELF, quote_id="", mode="CUSTOMER_SELF"),
        UNKNOWN_FLOW: project(UNKNOWN_FLOW, quote_id="", mode=""),
    }
    for index, row in enumerate(model["shipments"]):
        if row["id"] in rows:
            model["shipments"][index] = rows[row["id"]]

    payload = {
        "generatedFrom": "scripts/gen_issue244_plan_fixture.py — isolated mongomock staging",
        "cases": {
            "entrusted": ENTRUSTED,
            "customerSelf": CUSTOMER_SELF,
            "unknownFlow": UNKNOWN_FLOW,
        },
        "siblingQuoteThatMustNeverRender": "BG-244A",
        "journey": model,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    for key, shipment_id in payload["cases"].items():
        plan = next(r for r in model["shipments"] if r["id"] == shipment_id)["plan"]
        print(f"  {key:14s} {shipment_id}  node={plan['state']:8s} "
              f"quote={plan['items'][0]['state']:10s} "
              f"contract={plan['items'][1]['state']:9s} "
              f"advance={plan['items'][2]['state']}")
    print(f"wrote {OUT.relative_to(OUT.parents[2])}")


if __name__ == "__main__":
    main()
