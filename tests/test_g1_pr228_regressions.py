"""G1 PR #228 negative & positive regression suite for BL-1, BL-2, BL-3, and React outcomes."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import mongomock
import pytest

from core import customer_portal as cp
from core.entity_context import build_customer_context, build_entity_context
from core.shipment_document_workflow import (
    FLOW_CUSTOMER_SELF,
    project_commercial_flow,
    validate_flow_write,
)
from views import logi_c1 as c1
from views import logi_sandbox as sb
from views import logi_view_model as vm

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def staging():
    import streamlit as st

    sb.reset_backend()
    transport = sb.ensure_backend()
    assert transport == sb.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(sb.STAGING_ACTOR)
    yield transport
    st.session_state["current_user"] = dict(sb.STAGING_ACTOR)
    sb.reset_backend()


@pytest.fixture()
def seq():
    counter = {"n": 0}

    def _next(name: str, payload: dict[str, Any]) -> dict[str, Any]:
        counter["n"] += 1
        return {name: {"seq": counter["n"], "event": name, "payload": payload}}

    return _next


def _dispatch(next_seq, event: str, payload: dict[str, Any]) -> dict[str, Any]:
    out = vm.consume_phase_b_triggers({"seq": 0}, next_seq(event, payload))
    assert len(out) == 1, out
    return out[0]


def _stored_shipment(sid: str) -> dict[str, Any]:
    return vm.read_shipment(sid) or {}


# ---------------------------------------------------------------------------
# BL-1: Fresh DB read in shipment_customer_save (no stale load_customers cache)
# ---------------------------------------------------------------------------

def test_bl1_shipment_customer_save_reads_fresh_db_when_load_customers_cache_is_stale(staging, seq, monkeypatch):
    import core.database as core_db

    db = core_db.get_db()
    assert db is not None

    db.customers.insert_one({
        "id": "CUST-BL1-FRESH",
        "name": "Công Ty Tươi Dưới 30 Giây",
        "tax_code": "0105556667",
        "is_deleted": False,
    })

    # Force load_customers() to return a stale snapshot missing CUST-BL1-FRESH,
    # reproducing the <30s @st.cache_data(ttl=30) window on real Streamlit runtime.
    monkeypatch.setattr(core_db, "load_customers", lambda: {})

    out = _dispatch(seq, "shipment_customer_save", {
        "shipmentId": "LO-0306",
        "customerId": "CUST-BL1-FRESH",
        "requestId": "REQ-BL1-OK",
    })
    assert out["ok"] is True, out
    assert out["requestId"] == "REQ-BL1-OK"
    assert out["persisted"] == {
        "customer": "Công Ty Tươi Dưới 30 Giây",
        "customerId": "CUST-BL1-FRESH",
    }
    assert _stored_shipment("LO-0306")["customer_id"] == "CUST-BL1-FRESH"

    # Negative case: customer is soft-deleted in DB while load_customers() cache
    # still claims it is active -> shipment_customer_save MUST refuse!
    stale_active = {"CUST-BL1-FRESH": {"id": "CUST-BL1-FRESH", "name": "Công Ty Tươi Dưới 30 Giây"}}
    monkeypatch.setattr(core_db, "load_customers", lambda: stale_active)
    db.customers.update_one({"id": "CUST-BL1-FRESH"}, {"$set": {"is_deleted": True}})

    refused = _dispatch(seq, "shipment_customer_save", {
        "shipmentId": "LO-0308",
        "customerId": "CUST-BL1-FRESH",
        "requestId": "REQ-BL1-ARCHIVED",
    })
    assert refused["ok"] is False
    assert refused["requestId"] == "REQ-BL1-ARCHIVED"
    assert _stored_shipment("LO-0308")["customer_id"] != "CUST-BL1-FRESH"


# ---------------------------------------------------------------------------
# BL-2: Exact mixed-case customerId preservation across ROAD/SEA/AIR & flows
# ---------------------------------------------------------------------------

def test_bl2_mixed_case_customer_id_preserved_and_wrong_case_refused(staging, seq):
    from core.database import get_db, load_customers

    db = get_db()
    assert db is not None
    db.customers.insert_one({
        "id": "Cust-Excel-01",
        "name": "Công Ty Mixed Case G1",
        "tax_code": "0107778889",
        "is_deleted": False,
    })

    # Negative: uppercased or lowercased variant does NOT exist and MUST be refused.
    for wrong_id in ("CUST-EXCEL-01", "cust-excel-01"):
        bad = _dispatch(seq, "shipment_customer_save", {
            "shipmentId": "LO-0306",
            "customerId": wrong_id,
            "requestId": f"REQ-WRONG-{wrong_id}",
        })
        assert bad["ok"] is False, bad
        assert _stored_shipment("LO-0306")["customer_id"] != wrong_id

    # Positive across ROAD (Truck), SEA (Sea), and AIR (Air) shipments:
    for mode_code in ("Truck", "Sea", "Air"):
        sid = f"LO-G1-{mode_code.upper()}"
        created = _dispatch(seq, "shipment_create", {
            "shipmentId": sid,
            "customerId": "Cust-Excel-01",
            "mode": mode_code,
            "requestId": f"CREATE-{mode_code}",
        })
        assert created["ok"] is True, created
        doc = _stored_shipment(sid)
        assert doc["customer_id"] == "Cust-Excel-01"
        assert doc["customer"] == "Công Ty Mixed Case G1"

    # Re-assigning an existing shipment via shipment_customer_save preserves exact case:
    switched = _dispatch(seq, "shipment_customer_save", {
        "shipmentId": "LO-0306",
        "customerId": "Cust-Excel-01",
        "requestId": "REQ-SWITCH-MIXED",
    })
    assert switched["ok"] is True, switched
    assert switched["persisted"]["customerId"] == "Cust-Excel-01"
    stored = _stored_shipment("LO-0306")
    assert stored["customer_id"] == "Cust-Excel-01"

    # Commercial flow validation & projection preserve exact mixed-case customer_id:
    flow_block, errors = validate_flow_write(shipment=stored, mode=FLOW_CUSTOMER_SELF)
    assert errors == [] and flow_block is not None
    stored_with_flow = {
        **stored,
        "data": {**(stored.get("data") or {}), "0.0": {**((stored.get("data") or {}).get("0.0") or {}), "commercial_flow": flow_block}},
    }
    projected = project_commercial_flow(stored_with_flow, customers=load_customers() or {})
    assert projected["legalImporterId"] == "Cust-Excel-01"
    assert projected["legalImporterName"] == "Công Ty Mixed Case G1"

    # Contract customer update also preserves exact mixed-case customerId without cache lag:
    any_contract = db.contracts.find_one({}, {"_id": 0})
    if any_contract and any_contract.get("id"):
        cid = str(any_contract["id"])
        c_out = c1._handle_contract_save({
            "id": cid,
            "customerId": "Cust-Excel-01",
        })
        assert c_out["ok"] is True, c_out
        saved_contract = db.contracts.find_one({"id": cid}, {"_id": 0}) or {}
        assert saved_contract["customer_id"] == "Cust-Excel-01"


# ---------------------------------------------------------------------------
# BL-3: Strict ID-only profile/portal linkage; ID-less records go to reconciliation
# ---------------------------------------------------------------------------

def test_bl3_missing_or_corrupt_customer_id_never_grants_profile_or_portal_access():
    customers = {
        "CUST-A": {"id": "CUST-A", "name": "Công Ty Song Sinh"},
        "CUST-B": {"id": "CUST-B", "name": "Công Ty Song Sinh"},
    }
    shipments = {
        "LO-LINKED-A": {"id": "LO-LINKED-A", "shipment_id": "LO-LINKED-A", "customer": "Công Ty Song Sinh", "customer_id": "CUST-A", "status": "pending"},
        "LO-EMPTY": {"id": "LO-EMPTY", "shipment_id": "LO-EMPTY", "customer": "Công Ty Song Sinh", "customer_id": "", "status": "pending"},
        "LO-NONE": {"id": "LO-NONE", "shipment_id": "LO-NONE", "customer": "Công Ty Song Sinh", "status": "pending"},
        "LO-NONSTR": {"id": "LO-NONSTR", "shipment_id": "LO-NONSTR", "customer": "Công Ty Song Sinh", "customer_id": ["CUST-B"], "status": "pending"},
    }
    quotes = {
        "Q-LINKED-A": {"id": "Q-LINKED-A", "quote_no": "BG-A", "customer_name": "Công Ty Song Sinh", "customer_id": "CUST-A", "status": "APPROVED",
                       "calculation": {"selling_price_total_vnd": 88_000_000, "estimated_margin_vnd": 18_000_000}},
        "Q-NOID": {"id": "Q-NOID", "quote_no": "BG-NOID", "customer_name": "Công Ty Song Sinh", "customer_id": "", "status": "APPROVED",
                   "calculation": {"selling_price_total_vnd": 777_000_000, "estimated_margin_vnd": 123_000_000}},
    }
    agreements = {
        "AGR-NOID": {"agreement_id": "AGR-NOID", "agreement_no": "TT-NOID", "customer_name": "Công Ty Song Sinh", "customer_id": "", "status": "ACTIVE"},
    }
    contracts = {
        "HD-NOID": {"id": "HD-NOID", "contract_no": "HD-NOID-01", "client": "Công Ty Song Sinh", "customer_id": None, "status": "active", "value": 555_000_000},
    }

    ctx_b = build_entity_context(
        "customer",
        "CUST-B",
        customers=customers,
        shipments=shipments,
        quotes=quotes,
        agreements=agreements,
        contracts=contracts,
    )
    assert ctx_b["shipments"] == []
    assert ctx_b["quotations"] == []
    assert ctx_b["agreements"] == []
    assert ctx_b["contracts"] == []
    assert all(not row["auto_linked"] and not row["portal_grant"] for row in ctx_b["reconciliation_candidates"])
    assert "777000000" not in json.dumps(ctx_b)
    assert "555000000" not in json.dumps(ctx_b)

    # Portal access for CUST-B stays strictly empty; ID-less lots never leak by name.
    portal_db = mongomock.MongoClient()["g1_pr228_portal"]
    portal_db.customers.insert_many([
        {"id": "CUST-A", "name": "Công Ty Song Sinh", cp.PORTAL_ACCESS_EMAIL_FIELD: "a@songsinh.vn", "is_deleted": False},
        {"id": "CUST-B", "name": "Công Ty Song Sinh", cp.PORTAL_ACCESS_EMAIL_FIELD: "b@songsinh.vn", "is_deleted": False},
    ])
    portal_db.shipments.insert_many(list(shipments.values()))
    principal_b = cp.build_customer_principal(verified_email="b@songsinh.vn", db=portal_db)
    view_b = cp.load_customer_dashboard(principal_b, db=portal_db)
    assert view_b.cards == ()

    # Non-string corrupt customer_id neither links nor enters name-only reconciliation:
    ctx_a = build_customer_context("CUST-A", customers["CUST-A"], shipments, quotes=quotes, agreements=agreements, contracts=contracts, customers=customers)
    assert [row["shipment_id"] for row in ctx_a["shipments"]] == ["LO-LINKED-A"]
    assert [row["quote_id"] for row in ctx_a["quotations"]] == ["Q-LINKED-A"]
    assert "LO-NONSTR" not in {row["record_id"] for row in ctx_a["reconciliation_candidates"]}


# ---------------------------------------------------------------------------
# React DOM negative & positive outcomes on real production bundle
# ---------------------------------------------------------------------------

def test_react_header_customer_save_requires_matching_request_id_ok_and_readback():
    proc = subprocess.run(
        ["node", "tests/component/dom_acceptance_g1_customer_save_outcomes.mjs"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "PASSED" in proc.stdout
