"""LOGI-GOOD Phase C1 — the business-contracts vertical slice.

Acceptance evidence for the C1 write contract in the frozen Logi-good shell:

    KHÁCH HÀNG → BÁO GIÁ → THỎA THUẬN/BÀN GIAO → HỢP ĐỒNG
      → HÀNG HÓA HỢP ĐỒNG → HDNT/PL/HDMB → LINK SHIPMENT → DOWNLOAD/HISTORY.

Every write goes: typed event → bounded dispatcher → current RBAC
  → existing writer/service → audit → fresh backend read.

Transport: the isolated staging database (mongomock) running the CURRENT
canonical writers unchanged. The production database is never touched.
"""

from __future__ import annotations

import base64
import io
import zipfile

import pytest

from views import logi_c1
from views import logi_sandbox
from views import logi_view_model as vm


@pytest.fixture()
def staging():
    import streamlit as st

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    yield transport
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


@pytest.fixture()
def event_seq():
    state = {"n": 0}

    def _make(name: str, payload: dict) -> dict:
        state["n"] += 1
        return {name: {"seq": state["n"], "event": name, "payload": payload}}

    return _make


def _dispatch(seq_fn, name, payload):
    outcomes = logi_c1.consume_c1_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1
    return outcomes[0]


def _as(role: str, username: str):
    import streamlit as st

    st.session_state["current_user"] = {
        "username": username, "full_name": username, "role": role, "user_id": f"ID-{username}",
    }


def test_c1_payload_is_wired_into_view_model(staging):
    """The C1 collections surface on the view-model data channel."""
    assert logi_c1.C1_EVENTS <= vm.ALL_EVENTS
    model = vm.build_view_model()
    assert any(c["id"] == "CUST-ANPHAT" for c in model["customers"])
    assert any(c["id"] == "HDMB-0306" for c in model["contracts"])
    assert any(q["id"] == "BG-0306" for q in model["quotes"])
    assert model["authority"]["companies"]
    assert model["authority"]["agents"]


def test_customer_create_edit_and_archive_rbac(staging, event_seq):
    out = _dispatch(event_seq, "customer_create", {
        "id": "CUST-E2E", "name": "Khách E2E", "phone": "0987000111",
        "email": "e2e@example.com", "contactPerson": "Ngọc",
        "taxCode": "0107777666", "address": "KCN Test",
    })
    assert out["ok"], out
    assert out["readback"]["id"] == "CUST-E2E"
    assert out["readback"]["mst"] == "0107777666"

    out = _dispatch(event_seq, "customer_edit", {
        "id": "CUST-E2E", "name": "Khách E2E (đổi tên)", "tax_code": "0107777666",
    })
    assert out["ok"], out
    assert out["readback"]["name"] == "Khách E2E (đổi tên)"

    # Archive is admin-only (support has no customer_delete).
    out = _dispatch(event_seq, "customer_archive", {"id": "CUST-E2E", "reason": "kiểm thử"})
    assert not out["ok"]
    assert "Admin" in out["error"]

    # Import path.
    out = _dispatch(event_seq, "customer_import", {
        "rows": [{"id": "CUST-IMP", "name": "Khách Import", "taxCode": "0108888999"}],
    })
    assert out["ok"], out
    assert out["created"] == 1


def test_quote_flow_accepts_only_by_business_rule(staging, event_seq):
    out = _dispatch(event_seq, "quote_create", {
        "customerId": "CUST-ANPHAT", "salesOwner": "Minh Tú",
        "origin": "Bằng Tường", "destination": "KCN Quế Võ", "route": "Hữu Nghị",
        "incoterm": "DAP", "transportMode": "Road", "goodsDescription": "Linh kiện",
        "expectedDeliveryDate": "2026-09-20",
        "serviceLines": [
            {"code": "DV-VC-TQ", "serviceName": "Cước xe", "unit": "Lần", "qty": 1,
             "currency": "VND", "costUnit": 26000000, "sellUnit": 28500000, "taxPct": 8},
        ],
    })
    assert out["ok"], out
    qid = out["id"]
    assert out["readback"]["status"] == "DRAFT"
    assert out["readback"]["sellingPriceTotalVnd"] is not None

    # Agreement may only be created from an ACCEPTED quote.
    out = _dispatch(event_seq, "agreement_create", {"quoteId": qid})
    assert not out["ok"]
    assert "ACCEPTED" in out["error"]

    for target in ("READY_FOR_REVIEW", "ACCEPTED"):
        out = _dispatch(event_seq, "quote_transition", {"id": qid, "nextStatus": target})
        assert out["ok"], out
    assert out["readback"]["status"] == "ACCEPTED"

    out = _dispatch(event_seq, "agreement_create", {"quoteId": qid})
    assert out["ok"], out
    aid = out["id"]
    assert out["readback"]["status"] == "DRAFT"
    for target in ("REVIEWING", "AGREED"):
        out = _dispatch(event_seq, "agreement_transition", {"id": aid, "nextStatus": target})
        assert out["ok"], out
    assert out["readback"]["status"] == "AGREED"
    assert out["readback"]["handoff"]["state"] in {"READY_FOR_OPERATIONS", "NEEDS_COMMERCIAL_REVIEW"}


def test_contract_goods_threshold_and_docgen(staging, event_seq):
    cid = "HD-C1-E2E"
    assert _dispatch(event_seq, "contract_create", {"id": cid, "customerId": "CUST-ANPHAT", "kind": "HDNT"})["ok"]
    out = _dispatch(event_seq, "contract_save", {
        "id": cid, "company_id": "TT-COMPANY", "agent_id": "AGT-PHUANH",
        "hdnt_no": "HDNT-C1-001", "hdnt_date": "2026-09-10",
        "valid_from": "2026-01-01", "valid_to": "2027-12-31",
        "pl_no": "PL-C1-001", "pl_date": "2026-09-11",
        "hdmb_no": "HDMB-C1-001", "hdmb_date": "2026-09-12",
    })
    assert out["ok"], out
    assert out["readback"]["company"] and out["readback"]["agent"]

    # Goods: 10×1M + 5×2M = 20M → after-VAT 21.6M < 50M → HDNT + PL path.
    out = _dispatch(event_seq, "contract_goods_save", {
        "id": cid,
        "goodsLines": [
            {"description": "Linh kiện A", "unit": "Bộ", "quantity": "10", "unitPrice": "1000000"},
            {"description": "Linh kiện B", "unit": "Bộ", "quantity": "5", "unitPrice": "2000000"},
            {"description": "", "unit": "", "quantity": "", "unitPrice": ""},
        ],
    })
    assert out["ok"], out
    totals = out["readback"]["goodsTotals"]
    assert totals["subtotal"] == 20_000_000
    assert totals["total_after_vat"] == 21_600_000
    assert len(out["readback"]["goodsLines"]) == 2  # blank row dropped

    # Pass 1: HDNT produced; PL blocked (no valid HDNT parent yet).
    out = _dispatch(event_seq, "contract_docgen_generate", {"id": cid})
    assert out["ok"], out
    produced = {p["documentType"] for p in out["produced"]}
    assert "HDNT" in produced
    assert all(p["isOfficeFile"] for p in out["produced"])
    blocked = {b["documentType"] for b in out.get("blocked", [])}
    assert "PL" in blocked

    # Pass 2: PL now generated by reusing the freshly persisted valid HDNT.
    out = _dispatch(event_seq, "contract_docgen_generate", {"id": cid})
    assert out["ok"], out
    produced = {p["documentType"] for p in out["produced"]}
    assert "PL" in produced

    # Generated files are real OOXML containers held on the session store.
    outputs = logi_c1.stored_outputs(cid)
    assert outputs
    for entry in outputs.values():
        raw = entry["bytes"]
        assert raw[:2] == b"PK"
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            assert "[Content_Types].xml" in zf.namelist()

    # Issue the HDNT (support has operations_write).
    model = vm.build_view_model()
    contract = next(c for c in model["contracts"] if c["id"] == cid)
    hdnt = next(d for d in contract["documents"] if d["documentType"] == "HDNT")
    assert hdnt["downloadAvailable"]
    assert base64.b64decode(hdnt["downloadBase64"])[:2] == b"PK"
    out = _dispatch(event_seq, "contract_docgen_issue",
                    {"documentId": hdnt["documentId"], "revision": hdnt["revision"]})
    assert out["ok"], out
    assert out["persisted"]["status"] == "ISSUED"

    # N:M shipment linkage.
    out = _dispatch(event_seq, "contract_shipment_link", {"id": cid, "shipmentId": "LO-0306"})
    assert out["ok"], out
    assert "LO-0306" in out["linkedShipmentIds"]

    # Fresh view-model readback proves the slice end to end.
    model = vm.build_view_model()
    contract = next(c for c in model["contracts"] if c["id"] == cid)
    assert any(s["id"] == "LO-0306" and s["to"] == "/lo-hang/LO-0306" for s in contract["linkedShipments"])
    assert {"HDNT", "PL"} <= {d["documentType"] for d in contract["documents"]}
    assert any(c["id"] == "HDNT-C1-001" for c in model["contracts"])
    assert any(c["id"] == "PL-C1-001" for c in model["contracts"])


def test_blank_goods_quantity_is_unknown_not_zero(staging, event_seq):
    cid = "HD-BLANK-E2E"
    assert _dispatch(event_seq, "contract_create", {"id": cid, "customerId": "CUST-ANPHAT"})["ok"]
    out = _dispatch(event_seq, "contract_goods_save", {
        "id": cid,
        "goodsLines": [{"description": "Hàng chưa biết giá", "unit": "Bộ", "quantity": "", "unitPrice": ""}],
    })
    assert out["ok"], out
    line = out["readback"]["goodsLines"][0]
    assert line["quantity"] is None
    assert line["unitPrice"] is None
    assert line["amount"] is None
    # Unknown totals never collapse to a fabricated 0 decision.
    assert out["readback"]["goodsTotals"]["total_after_vat"] == 0
    assert out["readback"]["applicableDocuments"] == []


def test_rbac_boundary_is_backend_enforced(staging, event_seq):
    # SALE cannot issue documents (operations_write is support/admin-only).
    cid = "HD-RBAC-E2E"
    assert _dispatch(event_seq, "contract_create", {"id": cid, "customerId": "CUST-ANPHAT"})["ok"]
    out = _dispatch(event_seq, "contract_save", {
        "id": cid, "company_id": "TT-COMPANY", "agent_id": "AGT-PHUANH",
        "hdnt_no": "HDNT-RBAC-1", "hdnt_date": "2026-09-10",
        "valid_from": "2026-01-01", "valid_to": "2027-12-31",
    })
    assert out["ok"]
    _dispatch(event_seq, "contract_goods_save", {
        "id": cid, "goodsLines": [{"description": "Hàng", "unit": "Bộ", "quantity": "1", "unitPrice": "1000000"}],
    })
    out = _dispatch(event_seq, "contract_docgen_generate", {"id": cid})
    assert out["ok"]
    model = vm.build_view_model()
    hdnt = next(d for d in next(c for c in model["contracts"] if c["id"] == cid)["documents"]
                if d["documentType"] == "HDNT")

    _as("SALE", "minhtu")
    out = _dispatch(event_seq, "contract_docgen_issue", {"documentId": hdnt["documentId"], "revision": hdnt["revision"]})
    assert not out["ok"]
    assert "operations_write" in out["error"]

    _as("VIEWER", "viewer")
    out = _dispatch(event_seq, "customer_create", {"id": "CUST-X", "name": "X"})
    assert not out["ok"]
    assert "customers" in out["error"]

    _as("SUPPORT", "staging.support")
