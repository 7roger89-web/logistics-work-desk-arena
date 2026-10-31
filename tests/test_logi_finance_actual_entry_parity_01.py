"""LOGI_FINANCE_ACTUAL_ENTRY_PARITY_01 — practical Finance Actual entry parity.

Owner outcome: Lô Hàng → Tài chính / Công nợ regains the old app's operational
service-line entry (canonical service picker + full line fields + edit of the
SAME row), on top of the EXISTING canonical model:

    core.config.GETFLY_SERVICES_LIST          (the ONE service catalog)
      → views.logi_real_data.finance_service_catalog()   (read-only projection)
    data["3.4"]["details"]                    (the ONE Finance Actual truth)
      → finance_actual_save                   (the ONE write event)
      → RBAC → fresh shipment → apply_financial_snapshot
      → save_shipment_atomic → audit → fresh readback

No new table, collection, API, ledger or service layer, and no second catalog:
every assertion below reads the canonical document back from the database.

UNKNOWN != ZERO is proven on the WRITER path: a blank cost / price / VAT is
REFUSED (with a Vietnamese message the operator can act on) instead of being
normalised into a booked ``0``; an explicit ``0`` stays a valid answer.

Transport: the isolated staging database (mongomock). Production
``logistics_db`` and the pilot snapshot are never connected or mutated.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm

SHIPMENT = "LO-0308"

#: The component source tree — used to prove the catalog is projected by the
#: backend and NOT copied into React.
COMPONENT_SRC = pathlib.Path(__file__).resolve().parents[1] / "component" / "src"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    """Clean isolated staging database + the deterministic staging actor."""
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


def _dispatch(event_seq, name, payload):
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, event_seq(name, payload))
    assert len(outcomes) == 1
    return outcomes[0]


def _finance(shipment_id: str = SHIPMENT) -> dict:
    """Finance projection built from a FRESH database read."""
    return rd.shipment_projection(vm.read_shipment(shipment_id))["finance"]


def _line_payload(**overrides) -> dict:
    """One complete, operator-shaped actual line (catalog entry pre-filled)."""
    line = {
        "name": "Phí kiểm hóa",
        "code": "PKH",
        "unit": "Lần",
        "qty": 2,
        "cost": 800_000,
        "price": 1_200_000,
        "vat": 8,
        "note": "Theo thông báo của hải quan",
    }
    line.update(overrides)
    return line


# ---------------------------------------------------------------------------
# 1 — the service catalog is REUSED, not duplicated
# ---------------------------------------------------------------------------

def test_service_catalog_is_projected_from_core_config():
    """The projection carries ``core.config.GETFLY_SERVICES_LIST`` verbatim.

    LOGI cost-intelligence (78ef2d7) later gave every row a STABLE identity
    (``id`` / ``source``) so an Admin-maintained catalog entry can replace a
    legacy code by stable id instead of by position.  The canonical facts
    (code / name / unit / group), their order and the read-only contract are
    unchanged; only those two identity fields are additive.
    """
    from core.config import GETFLY_SERVICES_LIST

    catalog = rd.finance_service_catalog()

    assert catalog, "the canonical catalog must be projected, not emptied"
    assert len(catalog) == len(GETFLY_SERVICES_LIST)
    assert [entry["code"] for entry in catalog] == [item["code"] for item in GETFLY_SERVICES_LIST]
    for entry, item in zip(catalog, GETFLY_SERVICES_LIST):
        assert entry["name"] == item["name"]
        # The backend applies its documented default when the canonical
        # constant leaves a unit empty; never a silent divergence.
        assert entry["unit"] == (item["unit"] or "Lần")
        assert entry["group"] == item["group"]
        assert entry["id"] == f"LEGACY:{item['code']}"
        assert entry["source"] == "LEGACY_CONFIG"
    # Read-only projection: mutating the result cannot affect the constant.
    catalog[0]["name"] = "SỬA TRÁI PHÉP"
    assert GETFLY_SERVICES_LIST[0]["name"] != "SỬA TRÁI PHÉP"
    # …and the canonical constant cannot leak mutable rows into the next read.
    assert rd.finance_service_catalog()[0]["name"] == GETFLY_SERVICES_LIST[0]["name"]


def test_service_catalog_is_not_hardcoded_in_react():
    """React receives the catalog through the view-model; it owns no copy.

    Checked on the component source with comments stripped (prose may name the
    constant it must NOT copy): no service name, group label or code literal may
    appear in the shipped TypeScript. The only legal path for that data is the
    ``financeServiceCatalog`` slice delivered by the backend.
    """
    import re as _re

    from core.config import GETFLY_SERVICES_LIST

    sources = [
        path for path in COMPONENT_SRC.rglob("*")
        if path.suffix in {".ts", ".tsx"} and path.is_file()
    ]
    assert sources, "the component source tree must be inspectable"
    raw = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    # Strip block and line comments so a documented reference to the canonical
    # source is not mistaken for a copied list.
    code = _re.sub(r"/\*.*?\*/", "", raw, flags=_re.S)
    code = "\n".join(line.split("//", 1)[0] for line in code.splitlines())

    # A copied catalog would show up as service-name and group-label string
    # literals (codes like "EXW" double as Incoterms, so they prove nothing).
    literals = set(_re.findall(r'"([^"\n]+)"', code)) | set(_re.findall(r"'([^'\n]+)'", code))
    for item in GETFLY_SERVICES_LIST:
        for field in ("name", "group"):
            value = str(item.get(field) or "").strip()
            assert value not in literals, f"catalog {field} '{value}' is hard-coded in React"
    assert "GETFLY_SERVICES_LIST" not in code
    # And the shipped TypeScript never carries a list of services at all.
    #
    # The ONE exemption is named explicitly and is unrelated to Finance: the
    # GENERATED execution-profile catalog (LOGI_SHIPMENT_EXECUTION_PROFILE_01)
    # is a byte-for-byte projection of core.shipment_execution_profile's rule
    # matrices, with its own drift guard in the focused test suite. It is NOT a
    # "skip every generated file" rule — every generated file (this one
    # included) still passes the FINANCE literal checks above/below, and a
    # second generated file would be inspected here unless it is justified the
    # same way, by name.
    UNRELATED_GENERATED_CATALOG = "executionProfileCatalog.ts"
    code_without_rule_catalogs = "\n".join(
        text for path, text in
        ((path, _re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=_re.S))
         for path in sources)
        if path.name != UNRELATED_GENERATED_CATALOG
    )
    assert not _re.search(r"\[\s*\{[^\]]{200,}?code[^\]]*\]",
                          code_without_rule_catalogs), "React must not define its own catalog"
    # And the contract the component is allowed to rely on does exist.
    assert "financeServiceCatalog" in code


def test_view_model_carries_the_catalog_slice_to_the_component(staging):
    model = vm.build_view_model()
    assert [entry["code"] for entry in model["financeServiceCatalog"]] == [
        entry["code"] for entry in rd.finance_service_catalog()
    ]
    # JSON-serialisable (the component `data` channel is JSON only).
    json.dumps(model["financeServiceCatalog"], ensure_ascii=False)


def test_a_new_line_starts_with_no_vat_rate():
    """UNKNOWN != 8 — the form must not pre-book a rate nobody typed.

    The writer keeps the blank-vs-zero rule, so this guard protects the other
    half of the invariant: a NEW draft carries no VAT rate at all, while EDIT
    still reads back the rate stored on the row (0 included).
    """
    entry = (COMPONENT_SRC / "components" / "FinanceActualEntry.tsx").read_text(encoding="utf-8")
    draft = entry[entry.index("const BLANK_DRAFT"):entry.index("/** Prefill the editor")]
    assert 'vat: ""' in draft, "BLANK_DRAFT must leave VAT blank"
    for rate in ("0", "5", "8", "10"):
        assert f'vat: "{rate}"' not in draft, f"VAT must not default to {rate}%"
    # Blank stays refused, so a stated 0 / 8 / 10 is the only way to book one.
    assert 'label="VAT %" required' in entry
    assert '["VAT %", draft.vat]' in entry, "VAT must stay in the required-money check"
    assert 'vat: line.vat == null ? "" : String(line.vat)' in entry, \
        "editing a row must prefill the stored rate exactly, including 0"


# ---------------------------------------------------------------------------
# 2 — the read model carries the canonical fields of an existing row
# ---------------------------------------------------------------------------

def test_existing_actual_row_projects_the_canonical_fields(staging):
    """id/code/name/unit/note/qty/cost/price/vat/ccy survive the projection."""
    raw = vm.read_shipment(SHIPMENT)["data"]["3.4"]["details"][0]
    row = _finance()["actual"][0]

    assert row["id"] == str(raw["id"])
    assert row["code"] == raw["code"]
    assert row["label"] == raw["display_name"]
    assert row["name"] == raw["name_full"]
    assert row["unit"] == raw["unit"]
    assert row["note"] == raw.get("note", "")
    assert row["qty"] == float(raw["qty"])
    assert row["cost"] == float(raw["cost"])
    assert row["price"] == float(raw["price"])
    assert row["amount"] == float(raw["price"]), "`amount` stays the sell-side figure"
    assert row["vat"] == float(raw["vat_line"])
    assert row["ccy"] == _finance()["currency"]
    assert row["kind"] == "actual"


def test_legacy_row_lacking_fields_renders_honestly(staging):
    """A row without code/unit/note is projected as blank — never invented."""
    ship = vm.read_shipment(SHIPMENT)
    legacy = {
        **ship,
        "id": "LO-LEGACY-PROBE",
        "data": {**ship["data"], "3.4": {
            # Deliberately sparse: no code, no unit, no note, no vat.
            "details": [{"id": "LEGACY-1", "name_full": "Dịch vụ cũ", "qty": 1.0,
                         "price": 5_000_000.0, "cost": 4_000_000.0}],
            "payments": [], "commission": {"total": 0},
        }},
    }
    row = rd.shipment_projection(legacy)["finance"]["actual"][0]

    assert row["id"] == "LEGACY-1"
    assert row["label"] == "Dịch vụ cũ"
    assert row["code"] == ""
    assert row["unit"] == ""
    assert row["note"] == ""
    assert row["price"] == 5_000_000.0
    assert row["cost"] == 4_000_000.0
    # No fabricated VAT: a genuinely absent rate stays UNKNOWN, never 0.
    assert row["vat"] is None


def test_legacy_imported_row_survives_the_canonical_reader_for_editing():
    """Old ``price_out``/``price_in``/``vat``/``name`` rows stay editable.

    ``core.database.repair_data`` is the read normalizer every screen uses: it
    mints the missing ``id``, mirrors the legacy amount spellings onto the
    canonical keys and never drops the row.  The projection must therefore show
    the SAME figures the document holds, so the operator can fix the row in
    place instead of appending a second one.
    """
    from core.database import repair_data

    doc = {
        "id": "LO-LEGACY-IMPORT",
        "customer": "Minh Đức JSC",
        "currency": "VND",
        "status": "wait",
        "data": {"3.4": {"details": [
            {"name": "Cước xe TQ Đông Bằng", "qty": 2, "price_out": 3_000_000,
             "price_in": 2_500_000, "vat": 8},
        ], "payments": []}},
    }
    repaired = repair_data({"LO-LEGACY-IMPORT": doc})["LO-LEGACY-IMPORT"]
    row = rd.shipment_projection(repaired)["finance"]["actual"][0]

    assert row["id"], "the reader must give the row an id so SỬA can target it"
    assert row["label"] == "Cước xe TQ Đông Bằng"
    assert row["name"] == "Cước xe TQ Đông Bằng"
    assert row["qty"] == 2.0, "the booked quantity is never overwritten"
    assert row["price"] == 3_000_000.0 and row["amount"] == 3_000_000.0
    assert row["cost"] == 2_500_000.0
    assert row["vat"] == 8.0
    assert row["unit"] == "", "a unit the document never carried stays blank"
    # Same row, edited by the id the reader minted — still ONE row.
    assert len(repaired["data"]["3.4"]["details"]) == 1


# ---------------------------------------------------------------------------
# 3 — CREATE one actual line, round-tripping every operator field
# ---------------------------------------------------------------------------

def test_create_actual_line_round_trips_exactly(staging, event_seq):
    before = _finance()
    lines_before = len(vm.read_shipment(SHIPMENT)["data"]["3.4"]["details"])

    out = _dispatch(event_seq, "finance_actual_save",
                    {"shipmentId": SHIPMENT, "line": _line_payload()})
    assert out["ok"], out["error"]

    fresh = vm.read_shipment(SHIPMENT)
    details = fresh["data"]["3.4"]["details"]
    assert len(details) == lines_before + 1
    saved = next(d for d in details if d["id"] == out["lineId"])

    assert saved["name_full"] == "Phí kiểm hóa"
    assert saved["display_name"] == "Phí kiểm hóa"
    assert saved["code"] == "PKH"
    assert saved["unit"] == "Lần"
    assert saved["qty"] == 2.0
    assert saved["cost"] == 800_000.0
    assert saved["price"] == 1_200_000.0
    assert saved["vat_line"] == 8.0 and saved["vat"] == 8.0
    assert saved["price_in"] == 800_000.0 and saved["price_out"] == 1_200_000.0
    assert saved["note"] == "Theo thông báo của hải quan"

    # And the same facts come back through the read model.
    row = next(r for r in _finance()["actual"] if r["id"] == out["lineId"])
    assert (row["code"], row["unit"], row["qty"], row["cost"], row["price"],
            row["vat"], row["note"]) == ("PKH", "Lần", 2.0, 800_000.0, 1_200_000.0,
                                         8.0, "Theo thông báo của hải quan")

    # core.logic re-derived the shipment snapshot from the booked line only.
    fin = _finance()
    assert fin["receivableNet"] == before["receivableNet"] + 2 * 1_200_000
    assert fin["payable"] == before["payable"] + 2 * 800_000
    assert fin["receivable"] == fin["receivableNet"] + fin["outputVat"]
    assert fresh["data"]["3.4"]["out"] == out["persisted"]["receivable"]
    assert fresh["data"]["3.4"]["in"] == out["persisted"]["cost"]


# ---------------------------------------------------------------------------
# 4 — EDIT the same line id: the canonical row is updated, never duplicated
# ---------------------------------------------------------------------------

def test_edit_same_line_id_updates_that_row_and_never_duplicates(staging, event_seq):
    created = _dispatch(event_seq, "finance_actual_save",
                        {"shipmentId": SHIPMENT, "line": _line_payload(name="Phí lưu ca xe",
                                                                        code="LCX")})
    assert created["ok"], created["error"]
    line_id = created["lineId"]
    ids_before = [d["id"] for d in vm.read_shipment(SHIPMENT)["data"]["3.4"]["details"]]

    updated = _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": SHIPMENT,
        "line": _line_payload(id=line_id, name="Phí lưu ca xe", code="LCX", qty=4,
                              cost=950_000, price=1_400_000, vat=10,
                              note="Sửa sau khi có hóa đơn"),
    })
    assert updated["ok"], updated["error"]
    assert updated["lineId"] == line_id

    details = vm.read_shipment(SHIPMENT)["data"]["3.4"]["details"]
    ids_after = [d["id"] for d in details]
    assert len(ids_after) == len(ids_before), "an edit must not append a row"
    assert ids_after.count(line_id) == 1
    assert sorted(ids_after) == sorted(ids_before), "the same rows, updated in place"

    saved = next(d for d in details if d["id"] == line_id)
    assert saved["qty"] == 4.0
    assert saved["cost"] == 950_000.0
    assert saved["price"] == 1_400_000.0
    assert saved["vat_line"] == 10.0
    assert saved["note"] == "Sửa sau khi có hóa đơn"


def test_edit_with_an_unknown_line_id_is_refused(staging, event_seq):
    """A stale screen must not mint a row from a client-supplied id."""
    lines_before = len(vm.read_shipment(SHIPMENT)["data"]["3.4"]["details"])

    out = _dispatch(event_seq, "finance_actual_save", {
        "shipmentId": SHIPMENT,
        "line": _line_payload(id="PAY-LINE-DOES-NOT-EXIST"),
    })
    assert out["ok"] is False
    assert "Không tìm thấy dòng thực tế cần sửa" in out["error"]
    assert len(vm.read_shipment(SHIPMENT)["data"]["3.4"]["details"]) == lines_before


# ---------------------------------------------------------------------------
# 5 + 6 + 7 — blank money is refused, NOT booked as zero
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field,caption", [
    ("cost", "Giá vốn"),
    ("price", "Giá bán"),
    ("vat", "VAT"),
])
def test_blank_actual_money_is_refused(staging, event_seq, field, caption):
    lines_before = len(vm.read_shipment(SHIPMENT)["data"]["3.4"]["details"])

    out = _dispatch(event_seq, "finance_actual_save",
                    {"shipmentId": SHIPMENT, "line": _line_payload(**{field: ""})})
    assert out["ok"] is False, f"a blank {field} must not be booked"
    assert "Chưa nhập" in out["error"]
    assert caption in out["error"]
    # Nothing half-written: the canonical row count and totals are untouched.
    assert len(vm.read_shipment(SHIPMENT)["data"]["3.4"]["details"]) == lines_before
    assert out["readback"] is None


@pytest.mark.parametrize("field", ["cost", "price", "vat"])
def test_missing_actual_money_is_refused_too(staging, event_seq, field):
    """Absence behaves like a blank: there is no zero-filling fallback left."""
    out = _dispatch(event_seq, "finance_actual_save",
                    {"shipmentId": SHIPMENT, "line": _line_payload(**{field: None})})
    assert out["ok"] is False
    assert "Chưa nhập" in out["error"]


def test_thousands_separated_input_is_accepted_as_a_number(staging, event_seq):
    """The real input style of the desk ("1.200.000") is a number, not garbage."""
    out = _dispatch(event_seq, "finance_actual_save",
                    {"shipmentId": SHIPMENT, "line": _line_payload(price="1.200.000")})
    assert out["ok"], out["error"]
    saved = next(d for d in vm.read_shipment(SHIPMENT)["data"]["3.4"]["details"]
                 if d["id"] == out["lineId"])
    assert saved["price"] == 1_200_000.0


def test_unparsable_amount_is_refused_with_a_clear_message(staging, event_seq):
    out = _dispatch(event_seq, "finance_actual_save",
                    {"shipmentId": SHIPMENT, "line": _line_payload(cost="abc")})
    assert out["ok"] is False
    assert "không hợp lệ" in out["error"]


# ---------------------------------------------------------------------------
# 8 — an explicit zero is a deliberate, valid answer
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field", ["vat", "price", "cost"])
def test_explicit_zero_is_accepted_and_stays_zero(staging, event_seq, field):
    out = _dispatch(event_seq, "finance_actual_save",
                    {"shipmentId": SHIPMENT, "line": _line_payload(**{field: 0})})
    assert out["ok"], out["error"]

    saved = next(d for d in vm.read_shipment(SHIPMENT)["data"]["3.4"]["details"]
                 if d["id"] == out["lineId"])
    assert saved[field] == 0.0
    # A booked zero is still a booked fact: the projection reports 0, not "—".
    row = next(r for r in _finance()["actual"] if r["id"] == out["lineId"])
    assert (row["vat"] if field == "vat" else row[field]) == 0.0


# ---------------------------------------------------------------------------
# 9 — quantity semantics
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("qty", [0, -1, "0"])
def test_non_positive_qty_is_rejected(staging, event_seq, qty):
    lines_before = len(vm.read_shipment(SHIPMENT)["data"]["3.4"]["details"])
    out = _dispatch(event_seq, "finance_actual_save",
                    {"shipmentId": SHIPMENT, "line": _line_payload(qty=qty)})
    assert out["ok"] is False
    assert "Số lượng phải lớn hơn 0" in out["error"]
    assert len(vm.read_shipment(SHIPMENT)["data"]["3.4"]["details"]) == lines_before


def test_qty_defaults_to_one_only_when_not_stated(staging, event_seq):
    out = _dispatch(event_seq, "finance_actual_save",
                    {"shipmentId": SHIPMENT, "line": _line_payload(qty="")})
    assert out["ok"], out["error"]
    saved = next(d for d in vm.read_shipment(SHIPMENT)["data"]["3.4"]["details"]
                 if d["id"] == out["lineId"])
    assert saved["qty"] == 1.0

    bad = _dispatch(event_seq, "finance_actual_save",
                    {"shipmentId": SHIPMENT, "line": _line_payload(qty="một")})
    assert bad["ok"] is False
    assert "Số lượng không hợp lệ" in bad["error"]


# ---------------------------------------------------------------------------
# 10 — RBAC is the backend's, not the UI's
# ---------------------------------------------------------------------------

def test_finance_write_rbac_is_enforced_on_entry_and_on_edit(staging, event_seq):
    """A read-only role can neither create nor edit an actual line."""
    import streamlit as st

    from core.auth import can_operate_business

    assert can_operate_business("finance_write") is True
    created = _dispatch(event_seq, "finance_actual_save",
                        {"shipmentId": SHIPMENT, "line": _line_payload()})
    assert created["ok"], created["error"]
    line_id = created["lineId"]

    st.session_state["current_user"] = {"username": "viewer.user", "role": "VIEWER",
                                        "user_id": "U-VIEWER"}
    assert can_operate_business("finance_write") is False
    lines_before = len(vm.read_shipment(SHIPMENT)["data"]["3.4"]["details"])

    denied_create = _dispatch(event_seq, "finance_actual_save",
                              {"shipmentId": SHIPMENT, "line": _line_payload(name="Dòng ghi lậu")})
    assert denied_create["ok"] is False
    assert "quyền" in denied_create["error"]

    denied_edit = _dispatch(event_seq, "finance_actual_save",
                            {"shipmentId": SHIPMENT,
                             "line": _line_payload(id=line_id, price=999_000_000)})
    assert denied_edit["ok"] is False
    assert "quyền" in denied_edit["error"]

    fresh = vm.read_shipment(SHIPMENT)
    details = fresh["data"]["3.4"]["details"]
    assert len(details) == lines_before
    assert not [d for d in details if d.get("name_full") == "Dòng ghi lậu"]
    assert next(d for d in details if d["id"] == line_id)["price"] == 1_200_000.0


# ---------------------------------------------------------------------------
# 11 — the fresh view-model shows the line; totals are backend readback
# ---------------------------------------------------------------------------

def test_fresh_view_model_shows_the_saved_line_and_backend_totals(staging, event_seq):
    out = _dispatch(event_seq, "finance_actual_save",
                    {"shipmentId": SHIPMENT, "line": _line_payload(name="Cước biển FCL")})
    assert out["ok"], out["error"]

    import streamlit as st

    st.cache_data.clear()
    model = vm.build_view_model()
    row = next(r for r in model["shipments"] if r["id"] == SHIPMENT)["finance"]
    saved = next(r for r in row["actual"] if r["id"] == out["lineId"])

    assert saved["name"] == "Cước biển FCL"
    assert saved["code"] == "PKH"
    assert row["receivable"] == out["persisted"]["receivable"]
    assert row["payable"] == out["persisted"]["cost"]
    assert row["hasActualLines"] is True
    # The event outcome itself carries the authoritative readback (the same
    # object ``dispatch`` hands to the component through ``lastWrites``), and
    # the canonical writer audited the mutation.
    assert out["event"] == "finance_actual_save" and out["shipmentId"] == SHIPMENT
    readback_line = next(r for r in out["readback"]["finance"]["actual"]
                         if r["id"] == out["lineId"])
    assert readback_line["price"] == 1_200_000.0
    assert any(a["action"] == "update" for a in out["audit"])


# ---------------------------------------------------------------------------
# 12 + 13 — the surrounding finance capability is untouched
# ---------------------------------------------------------------------------

def test_quote_estimate_and_partner_ledger_are_untouched_by_an_actual_save(staging, event_seq):
    """The restored entry cannot rewrite the neighbouring finance capability."""
    from core.database import load_quotes

    quotes = load_quotes() or {}
    lot = "LO-0306"  # the seeded lot that DOES carry an accepted quote

    def _fin() -> dict:
        return rd.shipment_projection(vm.read_shipment(lot), quotes=quotes)["finance"]

    before = _fin()
    assert before["quote"], "seed precondition: this lot has a Quote Estimate"

    out = _dispatch(event_seq, "finance_actual_save",
                    {"shipmentId": lot, "line": _line_payload()})
    assert out["ok"], out["error"]

    after = _fin()
    # Quote Estimate is a separate object: never merged, never rewritten.
    assert after["quote"] == before["quote"]
    # Customer receipts and the partner payable ledger keep their own truth.
    assert after["payments"] == before["payments"]
    assert after["partner"] == before["partner"]
    assert set(after["partner"]) >= {"partnerId", "payable", "paid", "remaining", "payments"}
    # Only the ACTUAL side moved, and it moved by exactly the booked line.
    assert after["receivableNet"] == before["receivableNet"] + 2 * 1_200_000
    assert after["payable"] == before["payable"] + 2 * 800_000


def test_receipt_flow_still_works_next_to_the_new_entry(staging, event_seq):
    """A booked actual line is immediately collectable through the AR path."""
    created = _dispatch(event_seq, "finance_actual_save",
                        {"shipmentId": SHIPMENT, "line": _line_payload(qty=1, price=5_000_000,
                                                                        cost=4_000_000, vat=0)})
    assert created["ok"], created["error"]

    receipt = _dispatch(event_seq, "payment_record", {
        "shipmentId": SHIPMENT, "amount": 5_000_000,
        "requestId": "REQ-FINENTRY-1", "date": "2026-09-15", "note": "Thu tiền khách",
    })
    assert receipt["ok"], receipt["error"]

    fin = _finance()
    assert fin["received"] == 5_000_000.0
    assert fin["outstanding"] == fin["receivable"] - fin["received"]
    assert fin["payments"][0]["requestId"] == "REQ-FINENTRY-1"


# ---------------------------------------------------------------------------
# Scope guard — this slice adds no store, only a projection and a repair
# ---------------------------------------------------------------------------

def test_no_new_database_or_collection_is_introduced(staging, event_seq):
    db = logi_sandbox._state["client"][logi_sandbox.STAGING_DB_NAME]
    collections_before = set(db.list_collection_names())

    out = _dispatch(event_seq, "finance_actual_save",
                    {"shipmentId": SHIPMENT, "line": _line_payload()})
    assert out["ok"], out["error"]

    assert set(db.list_collection_names()) == collections_before
    # The new event is still the ONE existing write event.
    assert "finance_actual_save" in vm.PHASE_B_EVENTS
