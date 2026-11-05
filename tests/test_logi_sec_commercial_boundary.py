"""LOGI-SEC-COMMERCIAL-BOUNDARY-20261105 — commercial payload boundary.

The bounded security fix: commercial quote data and internal Excel source
data must reach the React payload ONLY through the grants that permit them,
independently of ``finance_view``:

* ``model["quotes"]`` / ``shipments[].finance.quote`` — a C1 quote is
  commercial data. Accounting holds ``finance_view`` but NOT
  ``commercial_view`` and must receive NO quote (while keeping actual
  finance). Operations holds neither and receives no quote either.
* ``model["agreements"]`` — the commercial snapshot is a copy of quote
  data: its money goes for actors without ``commercial_view``; only the
  estimated margin is internal for actors with ``commercial_view`` but
  without ``commercial_write``.
* Cost/margin/internal Excel data (per-line costUnit/costTotal/costVnd,
  estimatedCostVnd/estimatedMarginVnd, excelQuote.source_costs, option
  service-line cost_unit) belong to ``commercial_write``: Viewer and legacy
  Sales (``commercial_view`` only) keep sell prices but lose them.
* Stale session outcomes (lastWrites) are re-checked against the CURRENT
  role: a quote/agreement readback or an export/source document recorded
  under Support must not replay its figures or bytes to a downgraded actor.

Proven here, on the isolated staging database (mongomock), through the REAL
``build_view_model`` path and the REAL C1 handlers — no mocked view model,
no fake renderer payload. Production database is never touched.

Sentinels are distinct integers that do not collide with the staging bank
account numbers (0123456789 / 9876543210) or with each other, so a scan for
one sentinel cannot mistake another field for it:

    QCOST=27182818, QCOST_TOTAL=14142135, QSELL=31415926,
    QCOST_SUM=11235813, QMARGIN=16180339, EXCOST=24681357,
    OPTCOST=22334455, AG_MARGIN=13579246, AG_SELL=11223344,
    goods unit_price 777001.

Classification decisions pinned here (see COVERAGE-TABLE.md):
* excelQuote.goods (customer-sheet goods table) and source_facts stay for
  ``commercial_view`` holders — the parser prefers the explicit customer
  sheet and ``customer_quote_snapshot`` treats the goods table as
  customer-facing data. Only the parsed supplier cost rows (source_costs)
  and cost units are internal.
* costIntelligence (supplier-rate snapshots), contract goods values and
  contract docgen documents are policy UNKNOWN: recorded in ACCEPTANCE.md,
  deliberately NOT blocked in this round.
"""

from __future__ import annotations

import base64
import copy
import json
from io import BytesIO

import pytest
from openpyxl import load_workbook

from scripts.make_luc_giac_quote_fixture import build_luc_giac_fixture
from views import logi_c1, logi_sandbox
from views import logi_view_model as vm

# Distinct sentinels (see module docstring for the collision rule).
QCOST = 27182818
QCOST_TOTAL = 14142135
QCOST2 = 33445566
QSELL = 31415926
QSELL2 = 44556677
QCOST_SUM = 11235813
QMARGIN = 16180339
EXCOST = 24681357
EXCOST_LABEL = "COST-SENTINEL-VC"
OPTCOST = 22334455
AG_MARGIN = 13579246
AG_SELL = 11223344
GOODS_UNIT = 777001
ACTUAL = 123456789
DUTY = 222222222
VAT = 333333333
SHIPMENT = "LO-SEC-0306"
SOURCE_SHIPMENT = "LO-0306"

QUOTE_ID = "Q-SEC-COMM-01"
AGREEMENT_ID = "AGR-SEC-COMM-01"

ROLE_USERS = {
    "admin": {"username": "admin.user", "role": "admin", "user_id": "U-ADMIN"},
    "support": {"username": "support.user", "role": "support", "user_id": "U-SUPPORT"},
    "viewer": {"username": "viewer.user", "role": "viewer", "user_id": "U-VIEWER"},
    "sale": {"username": "sale.user", "role": "sale", "user_id": "U-SALE"},
    "sales": {"username": "sales.user", "role": "sales", "user_id": "U-SALES"},
    "operations": {"username": "ops.user", "role": "operations", "user_id": "U-OPS"},
    "accounting": {"username": "acct.user", "role": "accounting", "user_id": "U-ACCT"},
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    """Clean isolated staging database + deterministic staging actor."""
    import streamlit as st

    from core.database import get_db

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    db = get_db()
    db.customers.insert_one({"id": "CUST-LUCGIAC-TEST", "name": "Công ty Lục Giác"})
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _as_role(role: str) -> None:
    import streamlit as st

    st.session_state["current_user"] = dict(ROLE_USERS[role])


def _as_anonymous() -> None:
    import streamlit as st

    st.session_state["current_user"] = {}


def _dispatch_c1(seq_fn, name, payload):
    outcomes = logi_c1.consume_c1_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1, outcomes
    return outcomes[0]


def _dispatch_phase_b(seq_fn, name, payload):
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1, outcomes
    return outcomes[0]


def _pick_costed_quote():
    """A staging quote with 2 costed service lines. IDs are generated per
    reset (date + random suffix), so they must be discovered, never
    hard-coded."""
    from core.database import load_quotes

    for q in load_quotes().values():
        if len(q.get("service_lines") or []) == 2 and (q.get("calculation") or {}).get("estimated_margin_vnd") is not None:
            return q
    raise AssertionError("no costed staging quote found")


def _pick_ready_quote():
    from core.database import load_quotes

    for q in load_quotes().values():
        if str(q.get("status") or "").upper() == "READY_FOR_REVIEW":
            return q
    raise AssertionError("no READY_FOR_REVIEW staging quote found")


def _pick_agreement():
    from core.database import load_agreements

    for a in load_agreements().values():
        if (a.get("commercial_snapshot") or {}).get("calculation_summary"):
            return a
    raise AssertionError("no staging agreement found")


def _seed_commercial_quote() -> None:
    """Clone the staging quote with 2 costed lines, then stamp distinct
    cost/margin/Excel-source sentinels. Seeded as Support (sales_write)."""
    from core.database import load_quotes, save_quotes_to_cloud

    base = copy.deepcopy(_pick_costed_quote())
    base["id"] = QUOTE_ID
    base["quote_no"] = "BG-SEC-COMM-01"
    base["status"] = "DRAFT"
    base["version"] = 1
    lines = base["service_lines"]
    lines[0].update({"cost_unit": QCOST, "cost_total": QCOST_TOTAL, "cost_vnd": QCOST_TOTAL,
                     "sell_unit": QSELL, "sell_total": QSELL, "sell_vnd": QSELL})
    lines[1].update({"cost_unit": QCOST2, "cost_total": QCOST2, "cost_vnd": QCOST2,
                     "sell_unit": QSELL2, "sell_total": QSELL2, "sell_vnd": QSELL2})
    base["calculation"].update({
        "estimated_cost_vnd": QCOST_SUM, "estimated_margin_vnd": QMARGIN,
        "selling_price_total_vnd": QSELL + QSELL2,
    })
    base["excel_quote"] = {
        "schema": "V1",
        "supplier": "Sentinel Supplier",
        "source": {"file_name": "sentinel.xlsx", "sha256": "x" * 64,
                   "sheet_names": ["Khach gui"], "goods_sheet": "Khach gui"},
        "source_costs": [{"label": EXCOST_LABEL, "amount": EXCOST,
                          "source_sheet": "Chi phi", "condition": "UNCONFIRMED"}],
        "source_facts": {"equipment": "40GP"},
        "source_warnings": [],
        "goods": [{"id": "row-6", "description": "Sentinel goods", "model": "", "material": "",
                   "note": "", "length_mm": 100, "width_mm": 100, "height_mm": 100,
                   "qty": 2, "unit_price": GOODS_UNIT, "currency": "CNY",
                   "source_sheet": "Khach gui", "source_row": 6}],
        "options": {"A": {"scope": "Sentinel scope", "service_lines": [
            {"service_name": "Sentinel service", "cost_unit": OPTCOST,
             "currency": "VND", "qty": 1, "unit": "Lần"}]},
                    "B": {"scope": "", "service_lines": []}},
        "disclosures": [],
        "active_option": "A",
    }
    assert save_quotes_to_cloud({QUOTE_ID: base}), "seeded commercial quote must save"
    fresh = load_quotes()[QUOTE_ID]
    assert fresh["calculation"]["estimated_margin_vnd"] == QMARGIN
    assert fresh["excel_quote"]["source_costs"][0]["amount"] == EXCOST


def _seed_commercial_agreement() -> None:
    """Clone the staging agreement, then stamp a distinct margin sentinel
    into its calculation summary. Seeded as Support (commercial_write)."""
    from core.database import load_agreements, save_agreements_to_cloud

    base = copy.deepcopy(_pick_agreement())
    base["id"] = AGREEMENT_ID
    base["agreement_id"] = AGREEMENT_ID
    base["agreement_no"] = "AGR-SEC-COMM-01"
    base["status"] = "DRAFT"
    base["version"] = 1
    base["commercial_snapshot"]["calculation_summary"] = {
        "selling_price_total_vnd": AG_SELL, "estimated_margin_vnd": AG_MARGIN,
        "base_currency": "VND", "not_finance_ledger": True,
        "source": "Calculation snapshot của báo giá đã chốt; không phải Finance Ledger.",
    }
    assert save_agreements_to_cloud({AGREEMENT_ID: base}), "seeded agreement must save"
    fresh = load_agreements()[AGREEMENT_ID]
    assert fresh["commercial_snapshot"]["calculation_summary"]["estimated_margin_vnd"] == AG_MARGIN


def _find_quote(model, qid=QUOTE_ID):
    found = [q for q in model["quotes"] if q.get("id") == qid]
    assert len(found) == 1, f"quote {qid} must appear exactly once, got {len(found)}"
    return found[0]


def _find_agreement(model, aid=AGREEMENT_ID):
    found = [a for a in model["agreements"] if a.get("id") == aid]
    assert len(found) == 1, f"agreement {aid} must appear exactly once, got {len(found)}"
    return found[0]


def _seed_sentinel_shipment(seq_fn) -> None:
    """Local copy of the finance-payload fixture: LO-0306 clone with actual
    sentinel 123456789. Needed here to prove accounting keeps actual finance
    while losing only the quote."""
    from core.database import save_shipment_atomic

    source = vm.read_shipment(SOURCE_SHIPMENT)
    assert source is not None, "seed shipment LO-0306 must exist"
    ship = copy.deepcopy(source)
    ship["id"] = SHIPMENT
    ship["shipment_id"] = SHIPMENT
    ship["version"] = 0
    ship["data"]["3.4"]["details"] = [{
        "id": "SEC-LINE-1", "name_full": "Cước xe sentinel", "display_name": "Cước xe sentinel",
        "code": "DV-SEC", "unit": "Lần", "qty": 1, "price": ACTUAL, "cost": ACTUAL,
        "vat_line": 0, "note": "",
    }]
    assert save_shipment_atomic(ship, expected_version=0), "sentinel shipment must save"
    ship2 = copy.deepcopy(vm.read_shipment(SHIPMENT))
    ship2["data"].setdefault("2.4", {})["import_duty_amount"] = DUTY
    ship2["data"]["2.4"]["import_vat_amount"] = VAT
    assert save_shipment_atomic(ship2, expected_version=int(ship2.get("version") or 0))
    fresh = vm.read_shipment(SHIPMENT)
    assert fresh["data"]["2.4"]["import_duty_amount"] == DUTY
    assert fresh["data"]["2.4"]["import_vat_amount"] == VAT


def _import_excel_quote(seq_fn):
    """Real import path: fixture workbook -> GridFS source -> quote_create.
    Returns (quote_id, source_bytes). Run as Support (sales_write)."""
    source = build_luc_giac_fixture()
    out = _dispatch_c1(seq_fn, "quote_import_excel", {
        "customerId": "CUST-LUCGIAC-TEST", "fileName": "luc-giac-fixture.xlsx",
        "base64": base64.b64encode(source).decode(), "requestId": "SEC-IMP-1"})
    assert out["ok"], out
    details = out["readback"]
    assert details["source_costs"], "fixture must parse real source_costs"
    details["options"]["A"]["service_lines"] = [{
        "id": "fee-a", "service_name": "Vận chuyển", "qty": 1, "unit": "Lần",
        "currency": "VND", "cost_unit": 31800000, "sell_unit": None,
        "sell_confirmed": False, "tax_pct": None}]
    created = _dispatch_c1(seq_fn, "quote_create", {
        "customerId": "CUST-LUCGIAC-TEST", "salesOwner": "Sale test",
        "goodsDescription": "Bàn họp văn phòng", "incoterm": "EXW",
        "transportMode": "Sea", "excelQuote": details, "fx": {},
        "requestId": "SEC-CREATE-1"})
    assert created["ok"], created
    return created["id"], source


def _store_last_writes(outcomes) -> None:
    import streamlit as st

    st.session_state["logi_last_writes"] = list(outcomes)


def _last_write(model, event):
    rows = [r for r in model["lastWrites"] if r.get("event") == event]
    assert len(rows) == 1, f"exactly one {event} outcome expected, got {len(rows)}"
    return rows[0]

# ---------------------------------------------------------------------------
# Tests — model paths (table rows 1-3, 9-10)
# ---------------------------------------------------------------------------

def test_role_matrix_commercial_quotes_and_agreements(staging, event_seq):
    """Every role's model["quotes"]/["agreements"] follows its grants.

    Admin/Support/Sale (commercial_view + commercial_write): full quote
    (cost, margin, source_costs) and full agreement (margin).
    Viewer/legacy Sales (commercial_view, no commercial_write): sell prices
    kept, cost/margin/source_costs stripped (None/[], never 0); goods table
    kept (documented classification decision).
    Accounting (finance_view, no commercial_view): NO quotes at all, but
    actual finance + tax stay; agreement shell without quote money.
    Operations (neither): NO quotes, agreement shell without quote money,
    no tax (F-1 preserved), journey/declaration kept.
    """
    _as_role("support")
    _seed_commercial_quote()
    _seed_commercial_agreement()
    _seed_sentinel_shipment(event_seq)

    for role in ("admin", "support", "sale"):
        _as_role(role)
        model = vm.build_view_model()
        quote = _find_quote(model)
        assert quote["serviceLines"][0]["costUnit"] == QCOST, role
        assert quote["serviceLines"][0]["costTotal"] == QCOST_TOTAL, role
        assert quote["serviceLines"][0]["sellUnit"] == QSELL, role
        assert quote["estimatedCostVnd"] == QCOST_SUM, role
        assert quote["estimatedMarginVnd"] == QMARGIN, role
        assert quote["excelQuote"]["source_costs"][0]["amount"] == EXCOST, role
        assert quote["excelQuote"]["options"]["A"]["service_lines"][0]["cost_unit"] == OPTCOST, role
        agreement = _find_agreement(model)
        assert agreement["commercialSnapshot"]["calculationSummary"]["estimated_margin_vnd"] == AG_MARGIN, role
        assert agreement["commercialSnapshot"]["calculationSummary"]["selling_price_total_vnd"] == AG_SELL, role

    for role in ("viewer", "sales"):
        _as_role(role)
        model = vm.build_view_model()
        quote = _find_quote(model)
        assert quote["serviceLines"][0]["costUnit"] is None, role
        assert quote["serviceLines"][0]["costTotal"] is None, role
        assert quote["serviceLines"][0]["costVnd"] is None, role
        assert quote["serviceLines"][0]["sellUnit"] == QSELL, role
        assert quote["estimatedCostVnd"] is None, role
        assert quote["estimatedMarginVnd"] is None, role
        assert quote["excelQuote"]["source_costs"] == [], role
        assert quote["excelQuote"]["options"]["A"]["service_lines"][0]["cost_unit"] is None, role
        # Documented classification: customer-sheet goods stay.
        assert quote["excelQuote"]["goods"][0]["unit_price"] == GOODS_UNIT, role
        assert quote["excelQuote"]["source_facts"]["equipment"] == "40GP", role
        agreement = _find_agreement(model)
        summary = agreement["commercialSnapshot"]["calculationSummary"]
        assert summary["estimated_margin_vnd"] is None, role
        assert summary["selling_price_total_vnd"] == AG_SELL, role
        assert agreement["commercialSnapshot"]["serviceLines"], role

    _as_role("accounting")
    model = vm.build_view_model()
    assert model["quotes"] == [], "accounting must receive no C1 quotes"
    agreement = _find_agreement(model)
    assert agreement["commercialSnapshot"]["serviceLines"] == []
    assert agreement["commercialSnapshot"]["calculationSummary"] == {}
    assert agreement["paymentTerms"] is not None  # contract shell survives
    row = next(r for r in model["shipments"] if r["id"] == SHIPMENT)
    assert row["finance"]["quote"] == [], "accounting finance keeps actuals, loses only the quote"
    assert str(ACTUAL) in json.dumps(row["finance"], default=str), "accounting keeps actual finance"
    assert row["importInfo"]["tax"] == DUTY and row["importInfo"]["vat"] == VAT, "accounting keeps tax (finance_view)"

    _as_role("operations")
    model = vm.build_view_model()
    assert model["quotes"] == [], "operations must receive no C1 quotes"
    agreement = _find_agreement(model)
    assert agreement["commercialSnapshot"]["serviceLines"] == []
    assert agreement["commercialSnapshot"]["calculationSummary"] == {}
    row = next(r for r in model["shipments"] if r["id"] == SHIPMENT)
    assert row["finance"]["quote"] == []
    assert row["importInfo"]["tax"] is None and row["importInfo"]["vat"] is None, "F-1 preserved"
    assert row["importInfo"]["gnt"]["payer"] == "An Phát JSC", "GNT/declaration identity kept"
    assert row["finance"]["hasActualLines"] is False


def test_anonymous_gates_fail_closed(staging):
    """Anonymous: all three payload gates are False. (A full anonymous
    build is not asserted: ensure_backend() promotes an empty session to
    the staging actor, so the build itself cannot model anonymous.)"""
    _as_anonymous()
    assert vm._can_view_finance() is False
    assert vm._can_view_commercial() is False
    assert vm._can_view_commercial_write() is False


# ---------------------------------------------------------------------------
# Tests — lastWrites replay (table rows 4-7)
# ---------------------------------------------------------------------------

def test_downgrade_quote_transition_readback(staging, event_seq):
    """A quote_transition outcome recorded as Support must not replay its
    cost/margin figures to a downgraded actor."""
    _as_role("support")
    target = _pick_ready_quote()
    target_cost = target["service_lines"][0]["cost_unit"]
    target_sell = target["service_lines"][0]["sell_unit"]
    out = _dispatch_c1(event_seq, "quote_transition", {
        "id": target["id"], "nextStatus": "DRAFT", "requestId": "SEC-TR-1"})
    assert out["ok"], out
    assert out["readback"]["serviceLines"][0]["costUnit"] == target_cost
    _store_last_writes([out])

    _as_role("operations")
    model = vm.build_view_model()
    assert _last_write(model, "quote_transition")["readback"] == {}

    _as_role("accounting")
    model = vm.build_view_model()
    assert _last_write(model, "quote_transition")["readback"] == {}

    _as_role("viewer")
    model = vm.build_view_model()
    readback = _last_write(model, "quote_transition")["readback"]
    assert readback["serviceLines"][0]["costUnit"] is None
    assert readback["estimatedMarginVnd"] is None
    assert readback["serviceLines"][0]["sellUnit"] == target_sell
    row = _last_write(model, "quote_transition")
    assert row["ok"] is True and row["requestId"] == "SEC-TR-1"


def test_downgrade_agreement_transition_readback(staging, event_seq):
    """An agreement_transition outcome recorded as Support must not replay
    its margin to a downgraded actor."""
    _as_role("support")
    _seed_commercial_agreement()
    out = _dispatch_c1(event_seq, "agreement_transition", {
        "id": AGREEMENT_ID, "nextStatus": "REVIEWING", "requestId": "SEC-AGR-1"})
    assert out["ok"], out
    assert out["readback"]["commercialSnapshot"]["calculationSummary"]["estimated_margin_vnd"] == AG_MARGIN
    _store_last_writes([out])

    _as_role("operations")
    model = vm.build_view_model()
    readback = _last_write(model, "agreement_transition")["readback"]
    assert readback["commercialSnapshot"]["serviceLines"] == []
    assert readback["commercialSnapshot"]["calculationSummary"] == {}
    assert readback["id"] == AGREEMENT_ID  # shell identity survives

    _as_role("viewer")
    model = vm.build_view_model()
    readback = _last_write(model, "agreement_transition")["readback"]
    summary = readback["commercialSnapshot"]["calculationSummary"]
    assert summary["estimated_margin_vnd"] is None
    assert summary["selling_price_total_vnd"] == AG_SELL
    assert readback["commercialSnapshot"]["serviceLines"]


def test_downgrade_export_document_stripped(staging, event_seq):
    """A quote_export_xlsx outcome (real generated XLSX bytes) recorded as
    Support must not replay its bytes to Operations; Viewer keeps them."""
    _as_role("support")
    qid, _source = _import_excel_quote(event_seq)
    out = _dispatch_c1(event_seq, "quote_export_xlsx", {"id": qid, "requestId": "SEC-EXP-1"})
    assert out["ok"], out
    raw = base64.b64decode(out["document"]["downloadBase64"])
    assert raw[:4] == b"PK\x03\x04", "export must be a real XLSX"
    wb = load_workbook(BytesIO(raw))
    text = "\n".join(str(c.value or "") for ws in wb for row in ws for c in row)
    assert "31800000" not in text, "customer XLSX must not carry source costs"
    _store_last_writes([out])

    _as_role("operations")
    model = vm.build_view_model()
    doc = _last_write(model, "quote_export_xlsx")["document"]
    assert doc["downloadBase64"] is None
    assert doc["downloadAvailable"] is False
    assert doc["fileName"], "document identity survives"
    row = _last_write(model, "quote_export_xlsx")
    assert row["ok"] is True and row["requestId"] == "SEC-EXP-1"

    _as_role("viewer")
    model = vm.build_view_model()
    doc = _last_write(model, "quote_export_xlsx")["document"]
    assert base64.b64decode(doc["downloadBase64"])[:4] == b"PK\x03\x04"


def test_downgrade_source_download_and_workbook_view_stripped(staging, event_seq):
    """A quote_source_download outcome (raw supplier workbook bytes) recorded
    as Support must not replay to Viewer (commercial_view, no write); Sale
    (commercial_write) keeps it. A source-workbook view readback keeps its
    metadata for Viewer but loses the raw-cell page."""
    _as_role("support")
    qid, source = _import_excel_quote(event_seq)
    out = _dispatch_c1(event_seq, "quote_source_download", {"id": qid, "requestId": "SEC-DL-1"})
    assert out["ok"], out
    assert base64.b64decode(out["document"]["downloadBase64"]) == source
    view = logi_c1._HANDLERS["quote_source_workbook_view"](
        {"id": qid, "sheet": "Khach gui", "requestId": "SEC-WB-1"})
    assert view["ok"], view
    assert view["readback"]["page"] is not None
    _store_last_writes([out, view])

    _as_role("viewer")
    model = vm.build_view_model()
    doc = _last_write(model, "quote_source_download")["document"]
    assert doc["downloadBase64"] is None
    assert doc["downloadAvailable"] is False
    assert doc["fileName"], "document identity survives"
    readback = _last_write(model, "quote_source_workbook_view")["readback"]
    assert readback["page"] is None, "raw source cells must not replay to a non-write actor"
    assert readback["overview"]["sheet_names"], "workbook metadata survives"

    _as_role("sale")
    model = vm.build_view_model()
    doc = _last_write(model, "quote_source_download")["document"]
    assert base64.b64decode(doc["downloadBase64"]) == source
    readback = _last_write(model, "quote_source_workbook_view")["readback"]
    assert readback["page"] is not None


def test_real_excel_import_viewer_gets_no_source_costs(staging, event_seq):
    """Real parsed Excel data (not a hand-built fixture): the fixture
    workbook's source_costs reach Sale but never Viewer."""
    _as_role("support")
    qid, _source = _import_excel_quote(event_seq)
    from core.database import load_quotes

    stored = load_quotes()[qid]
    assert stored["excel_quote"]["source_costs"], "imported quote must carry real source_costs"
    assert any(c["amount"] == 31800000 for c in stored["excel_quote"]["source_costs"])

    _as_role("sale")
    model = vm.build_view_model()
    quote = _find_quote(model, qid)
    assert any(c["amount"] == 31800000 for c in quote["excelQuote"]["source_costs"])

    _as_role("viewer")
    model = vm.build_view_model()
    quote = _find_quote(model, qid)
    assert quote["excelQuote"]["source_costs"] == []
    assert quote["excelQuote"]["goods"], "customer-sheet goods stay for Viewer"
    assert quote["serviceLines"][0]["costUnit"] is None
    # The fixture fee was never confirmed, so its sell price stays None in
    # the stored quote itself (fixture fact, not a restriction).


# ---------------------------------------------------------------------------
# Tests — echo-None in the real UI flow + payload shape
# ---------------------------------------------------------------------------

def test_ui_save_never_echoes_redacted_tax_but_explicit_null_overwrites(staging, event_seq):
    """The real UI customs form (ShipmentDetail.tsx saveImport) sends
    import_duty_amount ONLY when the operator typed into the duty field
    (form starts {}, touched-state discriminator): an ordinary save of an
    unrelated field never echoes the redacted tax value, so no data is lost
    in the real UI flow. At the API level an EXPLICIT null in the fields
    dict still overwrites the stored figure (blank-stays-blank semantics,
    by design — write policy unchanged; this half documents that behavior).
    """
    _as_role("support")
    _seed_sentinel_shipment(event_seq)
    _as_role("operations")
    out = _dispatch_phase_b(event_seq, "shipment_field_save", {
        "shipmentId": SHIPMENT, "requestId": "SEC-TK-1",
        "fields": {"tk_no": "TK-SEC-01"}})
    assert out["ok"], out["error"]
    stored = vm.read_shipment(SHIPMENT)
    assert stored["data"]["2.4"]["tk_no"] == "TK-SEC-01"
    assert stored["data"]["2.4"]["import_duty_amount"] == DUTY, "ordinary UI save must not touch tax"
    assert stored["data"]["2.4"]["import_vat_amount"] == VAT

    out = _dispatch_phase_b(event_seq, "shipment_field_save", {
        "shipmentId": SHIPMENT, "requestId": "SEC-TK-2",
        "fields": {"tk_no": "TK-SEC-01", "import_duty_amount": None}})
    assert out["ok"], out["error"]
    stored = vm.read_shipment(SHIPMENT)
    assert stored["data"]["2.4"]["import_duty_amount"] is None, "explicit null overwrites (API-level, by design)"
    assert stored["data"]["2.4"]["import_vat_amount"] == VAT, "untouched VAT survives"


def test_restricted_payload_ui_shape(staging, event_seq):
    """Restricted payloads stay UI-safe: lists stay lists, restricted money
    is None (never a fabricated 0), identity fields survive, no crash."""
    _as_role("support")
    _seed_commercial_quote()
    _seed_commercial_agreement()

    for role in ("operations", "accounting", "viewer", "sale"):
        _as_role(role)
        model = vm.build_view_model()
        assert isinstance(model["quotes"], list)
        assert isinstance(model["agreements"], list)
        for quote in model["quotes"]:
            assert isinstance(quote["serviceLines"], list)
            assert quote["estimatedMarginVnd"] is None or isinstance(quote["estimatedMarginVnd"], (int, float))
            assert quote["estimatedMarginVnd"] != 0 or quote["estimatedMarginVnd"] is None
            assert quote["id"] and quote["quoteNo"] and quote["status"]
        for agreement in model["agreements"]:
            assert isinstance(agreement["commercialSnapshot"]["serviceLines"], list)
            assert isinstance(agreement["commercialSnapshot"]["calculationSummary"], dict)
            assert agreement["id"] and agreement["status"]
