"""LOGI_GNT_CANONICAL_FIELDS_01 — acceptance evidence for the Owner-approved
minimum import-tax business truth (approved 2026-09-12).

The ruling, restated as executable assertions:

 1. ``data.2.4.tk_date`` is the canonical customs declaration date for new data.
 2. ``data.2.4.import_duty_amount`` is the ACTUAL import duty in VND, keyed by
    the operator from the real customs notice / GNT.
 3. ``data.2.4.import_vat_amount`` is the ACTUAL import VAT in VND, same source.
 4. Exactly those three keys join the component write whitelist ``FIELD_PATHS``,
    with the matching numeric / date coercion.
 5. Nothing is calculated: no rate, no HS lookup, no FX, no arithmetic.
 6. ``reg_date`` is NOT writable — read fallback for legacy documents only.
 7. ``data.2.4.gnt.ds_thue[]`` stays legacy evidence, NOT a source of truth.
 8. Finance Actual, ledger, schema, database and infrastructure are untouched.

Every write assertion re-reads the shipment from the database
(``views.logi_view_model.read_shipment``), never from frontend state.
Transport: the isolated staging database (mongomock); production is never used.
"""

from __future__ import annotations

import pytest

from views import logi_real_data as rd
from views import logi_sandbox
from views import logi_view_model as vm


# ---------------------------------------------------------------------------
# Fixtures (same harness as tests/test_phase_b_real_data.py)
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    """A clean isolated staging database + a deterministic staging actor."""
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
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1
    return outcomes[0]


def _set_raw(shipment_id: str, section: str, fields: dict) -> None:
    """Simulate a document written BEFORE the ruling (legacy data on disk).

    Read-modify-write of the whole ``data`` subdocument: the canonical section
    keys are literally ``"2.4"``, so a dotted ``$set`` path such as
    ``data.2.4.reg_date`` would be split by Mongo into ``data → 2 → 4``. The
    app itself never uses dotted paths (``save_shipment_atomic`` ``$set``s the
    entire document), and neither may this helper.
    """
    from core.database import get_db

    collection = get_db().shipments
    doc = collection.find_one({"id": shipment_id}, {"_id": 0})
    assert doc is not None, f"seed shipment {shipment_id} missing"
    data = doc.get("data") or {}
    _merge(data.setdefault(section, {}), fields)
    collection.update_one({"id": shipment_id}, {"$set": {"data": data}})


def _merge(target: dict, patch: dict) -> None:
    """Deep-merge so seeding one field never destroys unrelated seeded facts."""
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _merge(target[key], value)
        else:
            target[key] = value


# ---------------------------------------------------------------------------
# Rule 4 — the whitelist grew by EXACTLY the three approved keys
# ---------------------------------------------------------------------------

def test_whitelist_gained_exactly_the_three_approved_keys():
    """FIELD_PATHS = the 26 pre-existing keys + exactly these three.

    LOGI_CN_TRUCK_TYPE_PERSIST_01 (Owner-approved 2026-09-12) later added one
    further key (``pickup_truck_type``), so the total was 30;
    LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 adds exactly one more —
    ``created_at``, the lot's own header date under ``data/0.0`` — so the total
    is now 31. The customs block below still pins that THIS ruling contributed
    exactly its three.
    """
    assert vm.FIELD_PATHS["tk_date"] == ("data", "2.4", "tk_date")
    assert vm.FIELD_PATHS["import_duty_amount"] == ("data", "2.4", "import_duty_amount")
    assert vm.FIELD_PATHS["import_vat_amount"] == ("data", "2.4", "import_vat_amount")
    assert len(vm.FIELD_PATHS) == 31

    # Every customs/tax-adjacent key under 2.4 is one of the five the Owner
    # has now ruled on — no smuggled extra field.
    under_24 = {k: p for k, p in vm.FIELD_PATHS.items() if p[1:2] == ("2.4",)}
    assert set(under_24) == {
        "tk_no", "customs_status", "phan_luong",
        "tk_date", "import_duty_amount", "import_vat_amount",
    }


def test_coercion_matches_the_field_type():
    """The two amounts are numeric, the date is canonical ISO, blank stays blank."""
    assert vm._coerce("import_duty_amount", "5000000") == 5000000.0
    assert vm._coerce("import_vat_amount", "800000") == 800000.0
    assert vm._coerce("tk_date", "15/08/2026") == "2026-08-15"
    assert vm._coerce("tk_date", "2026-08-15") == "2026-08-15"
    # UNKNOWN != ZERO — a blank is never coerced into 0.
    assert vm._coerce("import_duty_amount", "") == ""
    assert vm._coerce("import_vat_amount", None) is None
    assert vm._coerce("tk_date", "") == ""


# ---------------------------------------------------------------------------
# Rule 6 & 7 — what is deliberately STILL not writable
# ---------------------------------------------------------------------------

def test_reg_date_is_not_writable(staging, event_seq):
    """Rule 6: reg_date is a read fallback only; the whitelist rejects it."""
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0307", "fields": {"tk_no": "105588421330",
                                            "reg_date": "15/08/2026"},
    })
    assert out["ok"], out["error"]
    assert "reg_date" in out["rejected"]
    fresh = vm.read_shipment("LO-0307")
    assert "reg_date" not in fresh["data"]["2.4"]
    assert fresh["data"]["2.4"]["tk_no"] == "105588421330"


def test_gnt_ds_thue_is_not_writable(staging, event_seq):
    """Rule 7: the legacy line-item list is not promoted to a write target."""
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0307",
        "fields": {"tk_no": "105588421330",
                   "ds_thue": [{"ten": "Thuế NK", "ndkt": "1901", "tien": 5000000}]},
    })
    assert out["ok"], out["error"]
    assert "ds_thue" in out["rejected"]
    fresh = vm.read_shipment("LO-0307")
    assert "ds_thue" not in fresh["data"]["2.4"]


# ---------------------------------------------------------------------------
# Rules 1-3 — canonical save, then an INDEPENDENT fresh readback
# ---------------------------------------------------------------------------

def test_import_tax_save_and_fresh_readback(staging, event_seq):
    """The slice end to end: enter → canonical save → fresh read → truthful UI."""
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0307",
        "fields": {"tk_no": "105588421330", "tk_date": "15/08/2026",
                   "import_duty_amount": "5000000", "import_vat_amount": "800000"},
    })
    assert out["ok"], out["error"]

    fresh = vm.read_shipment("LO-0307")
    customs = fresh["data"]["2.4"]
    assert customs["tk_no"] == "105588421330"
    assert customs["tk_date"] == "2026-08-15"          # canonical ISO on disk
    assert customs["import_duty_amount"] == 5000000.0  # VND, as keyed
    assert customs["import_vat_amount"] == 800000.0

    # The dispatcher's readback and an independent projection agree.
    ii = out["readback"]["importInfo"]
    assert ii["declarationNo"] == "105588421330"
    assert ii["regDate"] == "15/08/2026"
    assert ii["tax"] == 5000000.0
    assert ii["vat"] == 800000.0
    assert rd.shipment_projection(fresh)["importInfo"]["tax"] == 5000000.0
    assert rd.shipment_projection(fresh)["importInfo"]["vat"] == 800000.0


def test_tax_is_saved_verbatim_not_derived(staging, event_seq):
    """Rule 5: an odd, non-round, 'wrong-looking' amount is stored unchanged.

    If any rate/HS/FX arithmetic existed on this path it would round, scale or
    re-derive the figure. It must survive byte-for-byte as the operator's fact.
    """
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0306",
        "fields": {"tk_no": "105579900211", "tk_date": "2026-08-03",
                   "import_duty_amount": "1234567", "import_vat_amount": "98761"},
    })
    assert out["ok"], out["error"]
    fresh = vm.read_shipment("LO-0306")
    assert fresh["data"]["2.4"]["import_duty_amount"] == 1234567.0
    assert fresh["data"]["2.4"]["import_vat_amount"] == 98761.0
    # And they are NOT in any 8%/10% relation to each other or to a rate table.
    assert out["readback"]["importInfo"]["tax"] == 1234567.0
    assert out["readback"]["importInfo"]["vat"] == 98761.0


def test_blank_tax_stays_unknown_not_zero(staging, event_seq):
    """UNKNOWN != ZERO — a declaration without tax figures renders as unknown."""
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0306",
        "fields": {"tk_no": "105579900211", "tk_date": "03/08/2026"},
    })
    assert out["ok"], out["error"]
    fresh = vm.read_shipment("LO-0306")
    assert "import_duty_amount" not in fresh["data"]["2.4"]
    assert "import_vat_amount" not in fresh["data"]["2.4"]
    ii = out["readback"]["importInfo"]
    assert ii["tax"] is None       # None, never 0
    assert ii["vat"] is None
    assert ii["regDate"] == "03/08/2026"


def test_nothing_infers_tax_from_an_existing_declaration(staging, event_seq):
    """Rule 5: a shipment that already has a TK number still shows no tax."""
    fresh = vm.read_shipment("LO-0307")
    assert fresh["data"]["2.4"]["tk_no"]            # seeded declaration exists
    ii = rd.shipment_projection(fresh)["importInfo"]
    assert ii["declarationNo"] == "105588421330"
    assert ii["tax"] is None and ii["vat"] is None  # ...but no invented amount


# ---------------------------------------------------------------------------
# Rule 6 — legacy read fallback, and the new field winning
# ---------------------------------------------------------------------------

def test_legacy_reg_date_still_displays(staging):
    """A document written before the ruling still shows its declaration date."""
    _set_raw("LO-0308", "2.4", {"reg_date": "2026-07-30"})
    ii = rd.shipment_projection(vm.read_shipment("LO-0308"))["importInfo"]
    assert ii["regDate"] == "30/07/2026"


def test_tk_date_wins_over_legacy_reg_date(staging, event_seq):
    """When both exist, the canonical new field is authoritative."""
    _set_raw("LO-0308", "2.4", {"reg_date": "2026-07-30"})
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0308",
        "fields": {"tk_no": "105500000001", "tk_date": "11/08/2026"},
    })
    assert out["ok"], out["error"]
    assert out["readback"]["importInfo"]["regDate"] == "11/08/2026"
    fresh = vm.read_shipment("LO-0308")
    assert fresh["data"]["2.4"]["tk_date"] == "2026-08-11"
    assert fresh["data"]["2.4"]["reg_date"] == "2026-07-30"   # legacy untouched


def test_timeline_and_import_tab_agree_on_the_declaration_date(staging, event_seq):
    """One fact, one helper: the milestone date can never drift from the tab."""
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0307",
        "fields": {"tk_no": "105588421330", "tk_date": "15/08/2026"},
    })
    assert out["ok"], out["error"]
    tracking = rd.tracking_projection(vm.read_shipment("LO-0307"))
    milestone = next(m for m in tracking["milestones"]
                     if m["title"] == "Đăng ký tờ khai nhập khẩu")
    assert milestone["time"] == out["readback"]["importInfo"]["regDate"] == "15/08/2026"


# ---------------------------------------------------------------------------
# Rule 7 — legacy GNT evidence stays evidence, not truth
# ---------------------------------------------------------------------------

def test_legacy_gnt_lines_do_not_become_the_tax_truth(staging):
    """ds_thue totals are still readable as evidence, but never projected as tax."""
    from core.shipment_360 import _tax_summary

    _set_raw("LO-0308", "2.4", {"gnt": {"ds_thue": [
        {"ten": "Thuế Nhập khẩu", "ndkt": "1901", "tien": 5000000},
        {"ten": "Thuế GTGT hàng NK", "ndkt": "1701", "tien": 800000},
    ]}})
    fresh = vm.read_shipment("LO-0308")

    # The legacy evidence reader still works and is unchanged...
    assert _tax_summary(fresh["data"])["value"] == 5800000.0
    # ...but the UI's import tax/VAT stays UNKNOWN until an operator records it.
    ii = rd.shipment_projection(fresh)["importInfo"]
    assert ii["tax"] is None and ii["vat"] is None


def test_recorded_amount_and_legacy_gnt_lines_coexist_without_merging(staging, event_seq):
    """Writing the canonical amounts never rewrites or reads back ds_thue."""
    from core.shipment_360 import _tax_summary

    _set_raw("LO-0306", "2.4", {"gnt": {"ds_thue": [
        {"ten": "Thuế Nhập khẩu", "ndkt": "1901", "tien": 111}]}})
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0306",
        "fields": {"tk_no": "105579900211", "import_duty_amount": "5000000"},
    })
    assert out["ok"], out["error"]
    fresh = vm.read_shipment("LO-0306")
    assert fresh["data"]["2.4"]["import_duty_amount"] == 5000000.0
    assert fresh["data"]["2.4"]["gnt"]["ds_thue"][0]["tien"] == 111   # untouched
    assert _tax_summary(fresh["data"])["value"] == 111.0              # still 111
    assert out["readback"]["importInfo"]["tax"] == 5000000.0          # not 111


# ---------------------------------------------------------------------------
# Rule 8 — Finance Actual / ledger semantics are untouched
# ---------------------------------------------------------------------------

def test_finance_actual_is_unchanged_by_a_tax_save(staging, event_seq):
    """Recording import tax moves no Finance Actual figure, currency or payment."""
    sid = "LO-0307"
    before = rd.shipment_projection(vm.read_shipment(sid))["finance"]

    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": sid,
        "fields": {"tk_no": "105588421330", "tk_date": "15/08/2026",
                   "import_duty_amount": "5000000", "import_vat_amount": "800000"},
    })
    assert out["ok"], out["error"]
    after = rd.shipment_projection(vm.read_shipment(sid))["finance"]

    assert after == before
    # Import VAT is NOT output VAT and never joins the receivable.
    assert after["outputVat"] == before["outputVat"]
    assert after["receivable"] == before["receivable"]
    assert after["profit"] == before["profit"]
    assert after["currency"] == before["currency"]


def test_no_new_event_and_no_new_ledger_write(staging, event_seq):
    """The field save reuses shipment_field_save; gnt_generate is the sole bounded generation event."""
    assert [e for e in sorted(vm.ALL_EVENTS) if "gnt" in e or "tax" in e] == ["gnt_generate"]
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0307", "fields": {"import_duty_amount": "5000000"},
    })
    assert out["event"] == "shipment_field_save"

    from core.database import get_db
    db = get_db()
    assert db["financial_obligations"].count_documents({}) == 0
    assert db["financial_transactions"].count_documents({}) == 0


def test_handbook_stage_table_picks_up_the_new_fields_automatically():
    """The /so-tay whitelist table is derived from FIELD_PATHS, so it is current."""
    from views.handbook import _stage_table

    rows = {row[0]: row[1] for row in _stage_table(vm.FIELD_PATHS)["rows"]}
    listed = rows["data.2.4"]
    for field in ("tk_date", "import_duty_amount", "import_vat_amount"):
        assert field in listed, listed
    assert "reg_date" not in listed


# ---------------------------------------------------------------------------
# CLEAR_FIX — BLANK = UNKNOWN, so an operator must be able to CLEAR a value
#
# The UI sends "" for a field the operator actively emptied. `onlyFilled`
# dropped those keys, so a cleared field never reached the backend and the
# stale number stayed canonical. These tests pin the backend half of the
# contract: "" is a real update, and it produces UNKNOWN — never 0.
# ---------------------------------------------------------------------------

def test_clearing_a_stored_import_duty_removes_the_number(staging, event_seq):
    """Acceptance 1-5: 5000000 stored, operator clears it, readback is UNKNOWN."""
    seed = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0307",
        "fields": {"tk_no": "105588421330", "import_duty_amount": "5000000"},
    })
    assert seed["ok"], seed["error"]
    assert seed["readback"]["importInfo"]["tax"] == 5000000.0

    # The operator empties the field; the UI sends the empty string explicitly.
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0307",
        "fields": {"tk_no": "105588421330", "import_duty_amount": ""},
    })
    assert out["ok"], out["error"]

    fresh = vm.read_shipment("LO-0307")
    stored = fresh["data"]["2.4"]["import_duty_amount"]
    # The numeric truth is gone — a blank, never a silent 0 and never 5000000.
    assert stored == ""
    assert not isinstance(stored, (int, float))
    assert out["readback"]["importInfo"]["tax"] is None
    assert rd.shipment_projection(fresh)["importInfo"]["tax"] is None
    # The declaration itself survives the clear.
    assert fresh["data"]["2.4"]["tk_no"] == "105588421330"


def test_clearing_a_stored_import_vat_removes_the_number(staging, event_seq):
    """Acceptance 6: identical semantics for the import VAT."""
    seed = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0306",
        "fields": {"tk_no": "105579900211", "import_vat_amount": "800000"},
    })
    assert seed["ok"], seed["error"]
    assert seed["readback"]["importInfo"]["vat"] == 800000.0

    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0306",
        "fields": {"tk_no": "105579900211", "import_vat_amount": ""},
    })
    assert out["ok"], out["error"]
    fresh = vm.read_shipment("LO-0306")
    assert fresh["data"]["2.4"]["import_vat_amount"] == ""
    assert out["readback"]["importInfo"]["vat"] is None


def test_clearing_one_tax_leaves_the_other_alone(staging, event_seq):
    """A clear is scoped to the field the operator emptied."""
    _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0307",
        "fields": {"tk_no": "105588421330", "import_duty_amount": "5000000",
                   "import_vat_amount": "800000"},
    })
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0307",
        "fields": {"tk_no": "105588421330", "import_duty_amount": ""},
    })
    assert out["ok"], out["error"]
    ii = out["readback"]["importInfo"]
    assert ii["tax"] is None
    assert ii["vat"] == 800000.0


def test_clearing_tk_date_does_not_migrate_legacy_reg_date(staging, event_seq):
    """Acceptance 7: clearing writes a blank; it never copies reg_date across."""
    _set_raw("LO-0308", "2.4", {"reg_date": "2026-07-30"})
    seed = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0308",
        "fields": {"tk_no": "105500000001", "tk_date": "11/08/2026"},
    })
    assert seed["ok"], seed["error"]
    assert seed["readback"]["importInfo"]["regDate"] == "11/08/2026"

    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0308",
        "fields": {"tk_no": "105500000001", "tk_date": ""},
    })
    assert out["ok"], out["error"]

    fresh = vm.read_shipment("LO-0308")
    # The canonical field is a blank — it was NOT filled with the legacy date.
    assert fresh["data"]["2.4"]["tk_date"] == ""
    assert fresh["data"]["2.4"]["tk_date"] != fresh["data"]["2.4"]["reg_date"]
    # The legacy value is still on disk, untouched, and still only a read
    # fallback (Owner rule 6) — nothing was migrated or deleted.
    assert fresh["data"]["2.4"]["reg_date"] == "2026-07-30"
    assert out["readback"]["importInfo"]["regDate"] == "30/07/2026"


def test_untouched_fields_survive_an_ordinary_save(staging, event_seq):
    """Acceptance 8: a save that omits a field must not change it."""
    _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0307",
        "fields": {"tk_no": "105588421330", "tk_date": "15/08/2026",
                   "import_duty_amount": "5000000", "import_vat_amount": "800000"},
    })
    # The operator edits only the lane; the three approved fields are absent
    # from the payload entirely, exactly as the untouched UI keys produce.
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": "LO-0307", "fields": {"tk_no": "105588421330", "phan_luong": "Xanh"},
    })
    assert out["ok"], out["error"]
    customs = vm.read_shipment("LO-0307")["data"]["2.4"]
    assert customs["tk_date"] == "2026-08-15"
    assert customs["import_duty_amount"] == 5000000.0
    assert customs["import_vat_amount"] == 800000.0
    assert customs["phan_luong"] == "Xanh"
    ii = out["readback"]["importInfo"]
    assert (ii["regDate"], ii["tax"], ii["vat"]) == ("15/08/2026", 5000000.0, 800000.0)


def test_clearing_tax_leaves_finance_actual_untouched(staging, event_seq):
    """Acceptance 9: a clear moves no Finance Actual figure, as a write does not."""
    sid = "LO-0307"
    _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": sid,
        "fields": {"tk_no": "105588421330", "import_duty_amount": "5000000",
                   "import_vat_amount": "800000"},
    })
    before = rd.shipment_projection(vm.read_shipment(sid))["finance"]
    out = _dispatch(event_seq, "shipment_field_save", {
        "shipmentId": sid,
        "fields": {"tk_no": "105588421330", "import_duty_amount": "",
                   "import_vat_amount": ""},
    })
    assert out["ok"], out["error"]
    assert rd.shipment_projection(vm.read_shipment(sid))["finance"] == before

    from core.database import get_db
    db = get_db()
    assert db["financial_obligations"].count_documents({}) == 0
    assert db["financial_transactions"].count_documents({}) == 0
