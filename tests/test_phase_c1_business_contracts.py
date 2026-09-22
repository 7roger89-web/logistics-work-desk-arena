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
from decimal import Decimal

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


def test_quote_never_invents_fx_and_discloses_the_operator_rate(staging, event_seq):
    """NO FAKE FX — the quotation rate is operator input, and it is disclosed.

    LOGI_REAL_USE_READINESS_01 repair pin. ``_quote_payload`` used to bake
    ``USD 25500 / CNY 3500`` into every canonical ``fx_snapshot``, so the VND
    total shown on the desk (and carried into agreements/lots) was derived from
    a constant nobody had entered. The operator's rate drives the arithmetic and
    the projection discloses it next to the converted total.

    LOGI_QUOTE_COST_WORKFLOW_UX_01_REPAIR_02 refined the no-rate case: a missing
    rate is UNKNOWN, not an error. Nothing is converted without an entered rate
    (NO FAKE FX still holds), but the quotation is perfectly truthful in its own
    currency, so the DRAFT saves and the VND total is simply reported UNKNOWN.
    """
    import json

    cny_line = {"code": "DV-VC-TQ", "serviceName": "Cước xe TQ", "unit": "Lần", "qty": 1,
                "currency": "CNY", "costUnit": 8000, "sellUnit": 8600, "taxPct": 0}

    # (1) No rate ⇒ the quote still saves, but NOTHING is converted and no rate
    #     is invented. The VND total is UNKNOWN rather than fabricated.
    out = _dispatch(event_seq, "quote_create",
                    {"customerId": "CUST-ANPHAT", "serviceLines": [cny_line]})
    assert out["ok"], out
    unconverted = logi_c1.read_quote(out["id"])
    assert "CNY" not in unconverted["fx_snapshot"]["rates_to_vnd"]
    assert unconverted["calculation"]["selling_price_total_vnd"] is None
    assert unconverted["service_lines"][0]["sell_vnd"] is None
    assert float(unconverted["service_lines"][0]["sell_total"]) == 8600.0

    # (2) The operator's rate is stored verbatim and drives the total.
    out = _dispatch(event_seq, "quote_create",
                    {"customerId": "CUST-ANPHAT", "serviceLines": [cny_line],
                     "fx": {"CNY": 3650}})
    assert out["ok"], out
    qid = out["id"]
    doc = logi_c1.read_quote(qid)
    rates = doc["fx_snapshot"]["rates_to_vnd"]
    assert float(rates["CNY"]) == 3650.0
    assert float(rates["VND"]) == 1.0
    assert "USD" not in rates, "an unused currency must not carry an invented rate"
    assert "25500" not in json.dumps(doc, default=str), "the old hardcoded rate leaked"
    assert out["readback"]["sellingPriceTotalVnd"] == 8600 * 3650      # tax 0%
    assert doc["service_lines"][0]["currency"] == "CNY"                # currencies stay separate

    # (3) The rate behind a converted total is disclosed to the desk.
    assert out["readback"]["fxRatesToVnd"]["CNY"] == 3650.0
    assert out["readback"]["fxNeededFor"] == ["CNY"]
    assert out["readback"]["fxSource"]

    # (4) Editing the rate re-prices from the NEW operator rate.
    out = _dispatch(event_seq, "quote_edit", {"id": qid, "fx": {"CNY": 3700}})
    assert out["ok"], out
    assert out["readback"]["sellingPriceTotalVnd"] == 8600 * 3700
    assert float(logi_c1.read_quote(qid)["fx_snapshot"]["rates_to_vnd"]["CNY"]) == 3700.0


def test_doc_cards_are_normalized_so_a_deferred_card_cannot_blank_the_shell(staging):
    """Every readiness card carries the declared payload contract's keys.

    core.docgen emits the deferred DEBIT_USD card without a ``missing`` list
    (nothing is missing — it is not implemented). ``DocCard.missing`` is
    declared ``string[]`` and the contract page renders it, so the absent key
    used to take the WHOLE shell down ("Cannot read properties of undefined").
    Contract goods totals stay UNKNOWN (null) — never a fabricated 0 ₫ that the
    HDNT+PL vs HDMB threshold decision would be derived from.
    """
    model = vm.build_view_model()
    assert model["contracts"], "the staging seed must expose contracts"
    deferred = []
    for contract in model["contracts"]:
        assert contract["docCards"], "a contract must expose its readiness cards"
        for card in contract["docCards"]:
            assert isinstance(card["missing"], list)
            assert card["document_type"] and card["state"]
            if card["state"] == "DEFERRED":
                deferred.append(card)
        totals = contract["goodsTotals"]
        assert totals is None or {"subtotal", "vat_amount", "total_after_vat"} <= set(totals)
    assert deferred, "the seed carries a deferred card — it must be normalized, not dropped"
    assert all(card["missing"] == [] for card in deferred)


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
    # Unknown totals never collapse to a fabricated 0 decision: the projection
    # reports NO total at all (null), so the desk cannot render "0 ₫" and derive
    # the HDNT+PL vs HDMB threshold from a number nobody knows.
    assert out["readback"]["goodsTotals"] is None
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


# ---------------------------------------------------------------------------
# Astra C1 acceptance gaps — the exact 50M boundary, HDMB branch, fail-closed
# retry, duplicate-link protection, fresh-session metadata, finance untouched.
# ---------------------------------------------------------------------------

def _goods_line(description: str, qty: int, unit_price: int) -> dict:
    return {"description": description, "unit": "Bộ", "quantity": str(qty), "unit_price_vnd_excl_vat": str(unit_price), "vat_rate": "0.08"}


def test_threshold_boundary_exact_after_vat_values():
    """Boundary is on the after-VAT total: < 50M → HDNT+PL; >= 50M → HDMB."""
    from core.docgen import rules
    from core.docgen.rules import HDMB, HDNT, NOT_APPLICABLE, PL, READY

    # 46,296,295 × 1.08 = 49,999,998.60 → ROUND_HALF_UP = 49,999,999  (< 50M)
    totals, _ = rules.compute_goods_totals([_goods_line("A", 1, 46_296_295)])
    assert totals.total_after_vat == Decimal("49999999")
    decision = rules.decide_applicable_documents(goods_lines=[_goods_line("A", 1, 46_296_295)])
    assert decision[HDNT].state == READY
    assert decision[PL].state == READY
    assert decision[HDMB].state == NOT_APPLICABLE

    # 46,296,296 × 1.08 = 49,999,999.68 → ROUND_HALF_UP = 50,000,000 (exactly 50M)
    totals, _ = rules.compute_goods_totals([_goods_line("B", 1, 46_296_296)])
    assert totals.total_after_vat == Decimal("50000000")
    decision = rules.decide_applicable_documents(goods_lines=[_goods_line("B", 1, 46_296_296)])
    assert decision[HDMB].state == READY
    assert decision[HDNT].state == NOT_APPLICABLE
    assert decision[PL].state == NOT_APPLICABLE

    # 46,296,297 × 1.08 = 50,000,000.76 → ROUND_HALF_UP = 50,000,001  (> 50M)
    totals, _ = rules.compute_goods_totals([_goods_line("C", 1, 46_296_297)])
    assert totals.total_after_vat == Decimal("50000001")
    decision = rules.decide_applicable_documents(goods_lines=[_goods_line("C", 1, 46_296_297)])
    assert decision[HDMB].state == READY
    assert decision[HDNT].state == NOT_APPLICABLE


def test_round_half_up_whole_vnd_is_locked():
    """VAT/amount rounding is ROUND_HALF_UP to whole VND (locked rule)."""
    from core.docgen.rules import _whole_vnd

    assert _whole_vnd(Decimal("0.5")) == Decimal("1")
    assert _whole_vnd(Decimal("1.5")) == Decimal("2")
    assert _whole_vnd(Decimal("2.5")) == Decimal("3")
    assert _whole_vnd(Decimal("0.4")) == Decimal("0")
    # The after-VAT boundary cases above embed the same half-up behaviour:
    # 49,999,998.60 → 49,999,999 and 49,999,999.68 → 50,000,000.


def test_hdmb_branch_generates_real_office_file(staging, event_seq):
    """>= 50M after VAT → HDMB only, produced as a real OOXML file."""
    cid = "HD-HDMB-E2E"
    assert _dispatch(event_seq, "contract_create", {"id": cid, "customerId": "CUST-ANPHAT"})["ok"]
    out = _dispatch(event_seq, "contract_save", {
        "id": cid, "company_id": "TT-COMPANY", "agent_id": "AGT-PHUANH",
        "hdmb_no": "HDMB-E2E-001", "hdmb_date": "2026-09-12",
    })
    assert out["ok"], out
    out = _dispatch(event_seq, "contract_goods_save", {
        "id": cid,
        "goodsLines": [{"description": "Máy móc", "unit": "Bộ", "quantity": "1", "unitPrice": "50000000"}],
    })
    assert out["ok"], out
    assert out["readback"]["goodsTotals"]["total_after_vat"] == 54_000_000
    assert out["readback"]["applicableDocuments"] == ["HDMB"]

    out = _dispatch(event_seq, "contract_docgen_generate", {"id": cid})
    assert out["ok"], out
    produced = {p["documentType"] for p in out["produced"]}
    assert produced == {"HDMB"}
    assert all(p["isOfficeFile"] for p in out["produced"])

    outputs = logi_c1.stored_outputs(cid)
    assert len(outputs) == 1
    raw = next(iter(outputs.values()))["bytes"]
    assert raw[:2] == b"PK"
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        assert "[Content_Types].xml" in zf.namelist()


def test_docgen_fails_closed_then_retry_after_fix(staging, event_seq):
    """Missing legal identity blocks generation (fail-closed, no fake file);
    after fixing identity the retry succeeds."""
    cid = "HD-RETRY-E2E"
    assert _dispatch(event_seq, "contract_create", {"id": cid, "customerId": "CUST-ANPHAT"})["ok"]
    assert _dispatch(event_seq, "contract_save", {
        "id": cid, "company_id": "TT-COMPANY", "agent_id": "AGT-PHUANH",
    })["ok"]
    _dispatch(event_seq, "contract_goods_save", {
        "id": cid, "goodsLines": [{"description": "Hàng", "unit": "Bộ", "quantity": "1", "unitPrice": "1000000"}],
    })
    out = _dispatch(event_seq, "contract_docgen_generate", {"id": cid})
    assert not out["ok"]
    assert out.get("failClosed") is True
    assert not logi_c1.stored_outputs(cid), "no fake file persisted on a blocked generation"

    out = _dispatch(event_seq, "contract_save", {
        "id": cid, "hdnt_no": "HDNT-RETRY-1", "hdnt_date": "2026-09-10",
        "valid_from": "2026-01-01", "valid_to": "2027-12-31",
    })
    assert out["ok"]
    out = _dispatch(event_seq, "contract_docgen_generate", {"id": cid})
    assert out["ok"], out
    assert "HDNT" in {p["documentType"] for p in out["produced"]}
    assert logi_c1.stored_outputs(cid)


def test_duplicate_shipment_link_is_idempotent(staging, event_seq):
    """Linking the same shipment twice keeps a single additive link."""
    cid = "HD-DUP-E2E"
    assert _dispatch(event_seq, "contract_create", {"id": cid, "customerId": "CUST-ANPHAT"})["ok"]
    first = _dispatch(event_seq, "contract_shipment_link", {"id": cid, "shipmentId": "LO-0306"})
    assert first["ok"] and first["linkedShipmentIds"] == ["LO-0306"]
    second = _dispatch(event_seq, "contract_shipment_link", {"id": cid, "shipmentId": "LO-0306"})
    assert second["ok"] and second["linkedShipmentIds"] == ["LO-0306"]
    assert len(second["readback"]["linkedShipments"]) == 1


def test_fresh_session_metadata_persists_bytes_are_session_scoped(staging, event_seq):
    """Generated metadata survives a fresh read; the binary bytes are
    session-scoped (owner storage gate) and never fabricated on re-read."""
    cid = "HD-SESSION-E2E"
    assert _dispatch(event_seq, "contract_create", {"id": cid, "customerId": "CUST-ANPHAT"})["ok"]
    assert _dispatch(event_seq, "contract_save", {
        "id": cid, "company_id": "TT-COMPANY", "agent_id": "AGT-PHUANH",
        "hdnt_no": "HDNT-SESS-1", "hdnt_date": "2026-09-10",
        "valid_from": "2026-01-01", "valid_to": "2027-12-31",
    })["ok"]
    _dispatch(event_seq, "contract_goods_save", {
        "id": cid, "goodsLines": [{"description": "Hàng", "unit": "Bộ", "quantity": "1", "unitPrice": "1000000"}],
    })
    assert _dispatch(event_seq, "contract_docgen_generate", {"id": cid})["ok"]

    same_session = next(c for c in vm.build_view_model()["contracts"] if c["id"] == cid)
    assert any(d["downloadAvailable"] for d in same_session["documents"])

    # Simulate a fresh session: the bytes store is cleared (session-only).
    import streamlit as st

    st.session_state[logi_c1._outputs_key(cid)] = {}
    fresh = next(c for c in vm.build_view_model()["contracts"] if c["id"] == cid)
    docs = {d["documentType"]: d for d in fresh["documents"]}
    assert "HDNT" in docs, "metadata (history) survives a fresh read"
    assert docs["HDNT"]["status"] == "GENERATED"
    assert docs["HDNT"]["downloadAvailable"] is False
    assert docs["HDNT"]["downloadBase64"] is None


def test_finance_actual_untouched_by_c1_flow(staging, event_seq):
    """The C1 slice performs zero Finance Actual mutations."""
    from core.database import get_db, load_contract_transactions

    db = get_db()
    before = db.shipments.find_one({"id": "LO-0306"}, {"_id": 0})

    cid = "HD-FIN-E2E"
    assert _dispatch(event_seq, "contract_create", {"id": cid, "customerId": "CUST-ANPHAT"})["ok"]
    _dispatch(event_seq, "contract_save", {
        "id": cid, "company_id": "TT-COMPANY", "agent_id": "AGT-PHUANH",
        "hdnt_no": "HDNT-FIN-1", "hdnt_date": "2026-09-10",
        "valid_from": "2026-01-01", "valid_to": "2027-12-31",
    })
    _dispatch(event_seq, "contract_goods_save", {
        "id": cid, "goodsLines": [{"description": "Hàng", "unit": "Bộ", "quantity": "1", "unitPrice": "1000000"}],
    })
    _dispatch(event_seq, "contract_docgen_generate", {"id": cid})
    _dispatch(event_seq, "contract_shipment_link", {"id": cid, "shipmentId": "LO-0306"})

    after = db.shipments.find_one({"id": "LO-0306"}, {"_id": 0})
    assert after["data"]["3.4"] == before["data"]["3.4"], "shipment finance unchanged"
    assert load_contract_transactions(cid) == {}, "no contract finance rows written"
