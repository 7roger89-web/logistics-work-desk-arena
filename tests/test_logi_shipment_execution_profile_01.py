"""LOGI_SHIPMENT_EXECUTION_PROFILE_01 (issue #76) — focused acceptance evidence.

The Owner's ruling, restated as executable assertions: a shipment workflow is
NOT universal. Which stages exist — and which facts are even relevant — is
derived from the shipment's execution profile:

    Incoterms code + VERSION + named place
      × Trường Thành SERVICE SCOPE (a separate, operator-confirmed truth)
      × mode × load model / equipment
      × ACTUAL cargo insurance (persisted, distinct from the Incoterm obligation)
      + persisted facts
        → the relevant stages (each with its reason) → the next action

What this file proves, in order:

 A. the Incoterms 2020 / 2010 / legacy-2000 matrices and their mode scope;
 B. CNF / C&F normalize onto CFR while the raw contract wording survives;
 C. a bare rule without a named place is incomplete, and a blank place stays
    blank (never fabricated);
 D. impossible combinations are REFUSED on write and never mutate a stored
    document, while a historical impossible document renders CONFIG_CHECK;
 E. service scope is independent of the Incoterm (no buyer duty becomes a
    Trường Thành task by implication);
 F. SEA FCL/LCL, ROAD FTL/LTL, AIR profiles and the operational presets — with
    the multi-container authority staying on the EXISTING transport legs;
 G. the derived insurance obligation vs the persisted actual insurance state,
    including CIP 2020 Clause A never being projected back onto 2010;
 H. workflow derivation: only relevant stages exist, each carrying its reason,
    and the next action comes from those stages alone;
 I. backward compatibility: a legacy document (mode + incoterm only) still reads,
    honestly as PROFILE_INCOMPLETE, with UNKNOWN preserved;
 J. the bounded write path: RBAC, audit, fresh authoritative readback, no
    forked truth, no new whitelist key;
 K. the generated client catalog cannot drift from the Python authority;
 L. PR74 latency invariants (one handler per intent, ONE view-model build, no
    explicit second rerun) and ZERO added database reads for the projection.

Every write assertion re-reads the shipment from the database
(``views.logi_view_model.read_shipment``), never from front-end state. The
transport is the isolated mongomock staging database; production is never used.
"""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

from core import auth as core_auth
from core import database as core_database
from core import shipment_execution_profile as ep
from views import logi_sandbox
from views import logi_view_model as vm

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOT = "LO-0306"          # seeded legacy lot: mode=Truck, incoterm=DAP, nothing else
SEA_LOT = "LO-0307"      # seeded lot used for the sea scenarios
ROAD_LOT = "LO-0308"     # seeded lot used for the road scenarios


# ---------------------------------------------------------------------------
# Harness (the same isolated staging transport every focused slice uses)
# ---------------------------------------------------------------------------

@pytest.fixture()
def staging():
    import streamlit as st

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)
    yield transport
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    logi_sandbox.reset_backend()


def _dispatch(name: str, payload: dict, *, seq: int = 1) -> dict:
    result = {name: {"seq": seq, "event": name, "payload": payload}}
    outcomes = vm.consume_phase_b_triggers({"seq": seq - 1}, result)
    assert len(outcomes) == 1, (name, outcomes)
    return outcomes[0]


def _profile(shipment_id: str) -> dict:
    """The profile the API actually serves for a stored shipment."""

    from views.logi_real_data import shipment_projection

    shipment = vm.read_shipment(shipment_id)
    assert shipment is not None
    return shipment_projection(shipment)["executionProfile"]


def _stored_block(shipment_id: str) -> dict:
    shipment = vm.read_shipment(shipment_id)
    return dict(((shipment.get("data") or {}).get("0.0") or {}).get("execution_profile") or {})


def _doc(shipment_id: str) -> dict:
    shipment = vm.read_shipment(shipment_id)
    assert shipment is not None
    return shipment


def _profile_of(document: dict) -> dict:
    return ep.build_execution_profile(document)


def _valid_sea_profile(**overrides) -> dict:
    payload = {
        "mode": "Sea", "incoterm": "CIF", "incotermVersion": "2020",
        "namedPlace": "Hai Phong Port", "loadModel": "FCL",
        "serviceScope": ["IMPORT_CUSTOMS", "DESTINATION_TRUCKING", "FINAL_DELIVERY"],
        "serviceScopeConfirmed": True,
        "cargoInsurance": {"status": "UNKNOWN"},
    }
    payload.update(overrides)
    return payload


def _valid_road_profile(**overrides) -> dict:
    payload = {
        "mode": "Truck", "incoterm": "FCA", "incotermVersion": "2020",
        "namedPlace": "Pingxiang Warehouse", "loadModel": "FTL",
        "serviceScope": ["ORIGIN_PICKUP", "EXPORT_CUSTOMS", "IMPORT_CUSTOMS",
                         "DESTINATION_TRUCKING", "FINAL_DELIVERY"],
        "serviceScopeConfirmed": True,
        "cargoInsurance": {"status": "NO"},
    }
    payload.update(overrides)
    return payload


# ===========================================================================
# A. Incoterms matrices
# ===========================================================================

def test_incoterms_2020_matrix_is_the_icc_2020_rule_set():
    assert ep.codes_for_version("2020") == (
        "EXW", "FCA", "CPT", "CIP", "DAP", "DPU", "DDP",
        "FAS", "FOB", "CFR", "CIF",
    )
    for code in ("FAS", "FOB", "CFR", "CIF"):
        assert ep.rule_scope("2020", code) == ep.SCOPE_SEA_ONLY
    for code in ("EXW", "FCA", "CPT", "CIP", "DAP", "DPU", "DDP"):
        assert ep.rule_scope("2020", code) == ep.SCOPE_ANY_MODE
    assert "DAT" not in ep.codes_for_version("2020")


def test_incoterms_2010_matrix_has_dat_and_no_dpu():
    assert ep.codes_for_version("2010") == (
        "EXW", "FCA", "CPT", "CIP", "DAT", "DAP", "DDP",
        "FAS", "FOB", "CFR", "CIF",
    )
    assert ep.versions_defining("DAT") == ("2010",)
    assert ep.versions_defining("DPU") == ("2020",)
    assert "DPU" not in ep.codes_for_version("2010")


def test_legacy_2000_terms_exist_only_in_the_legacy_version():
    assert ep.codes_for_version(ep.VERSION_LEGACY_2000) == ("DAF", "DDU")
    assert "DAF" not in ep.codes_for_version("2010")
    assert "DAF" not in ep.codes_for_version("2020")
    assert "DDU" not in ep.codes_for_version("2010")
    assert ep.versions_defining("DAF") == (ep.VERSION_LEGACY_2000,)
    assert ep.versions_defining("DDU") == (ep.VERSION_LEGACY_2000,)


@pytest.mark.parametrize("version,code", [
    ("2020", "DAT"), ("2010", "DPU"), ("2020", "DAF"), ("2010", "DDU"),
    ("2020", "DDU"), ("2010", "DAF"),
])
def test_version_mismatches_are_reported_not_rewritten(version, code):
    facts = {"incoterm": code, "incotermVersion": version, "mode": "SEA"}
    issues = ep.validate_profile(facts, for_write=True)
    assert any(issue["code"] == ep.ISSUE_VERSION_MISMATCH for issue in issues), issues


def test_dat_is_explained_as_the_2010_rule_renamed_in_2020():
    issues = ep.validate_profile({"incoterm": "DAT", "incotermVersion": "2020"}, for_write=True)
    message = next(i["message"] for i in issues if i["code"] == ep.ISSUE_VERSION_MISMATCH)
    assert "2010" in message and "DPU" in message


# ===========================================================================
# B. CNF / C&F → CFR, raw evidence preserved
# ===========================================================================

@pytest.mark.parametrize("raw", ["CNF", "C&F", "cnf", "C and F", "C.N.F.", "C&f"])
def test_business_aliases_normalize_onto_cfr(raw):
    normalized = ep.normalize_incoterm(raw)
    assert normalized["code"] == "CFR"
    assert normalized["rawLabel"] == raw       # the contract wording is evidence
    assert "CFR" in normalized["aliasNote"]


def test_unknown_contract_terms_are_never_guessed():
    normalized = ep.normalize_incoterm("theo hợp đồng cũ")
    assert normalized["code"] == ""
    assert normalized["recognized"] is False
    issues = ep.validate_profile({"incoterm": normalized["code"], "incotermRawInput": "theo hợp đồng cũ"},
                                 for_write=True)
    assert any(i["code"] == ep.ISSUE_UNKNOWN_INCOTERM for i in issues)


def test_alias_is_stored_as_cfr_with_the_source_wording_kept(staging):
    out = _dispatch("shipment_profile_save", dict(
        {"shipmentId": SEA_LOT, "requestId": "REQ-CNF"}, **_valid_sea_profile(incoterm="CNF", namedPlace="Shenzhen")))
    assert out["ok"], out["error"]

    document = _doc(SEA_LOT)
    assert document["data"]["0.0"]["incoterm"] == "CFR"           # canonical code
    assert _stored_block(SEA_LOT)["incoterm_raw_label"] == "CNF"  # raw evidence kept
    profile = _profile(SEA_LOT)
    assert profile["incoterm"] == "CFR"
    assert profile["incotermRawLabel"] == "CNF"
    assert "CFR" in profile["incotermAliasNote"]
    assert any("hợp đồng ghi: CNF" in line for line in profile["summaryLines"])


def test_a_place_written_inside_the_contract_term_is_offered_as_evidence_only():
    normalized = ep.normalize_incoterm("FOB Shenzhen")
    assert (normalized["code"], normalized["inlinePlace"]) == ("FOB", "Shenzhen")
    # Reading it never writes it: the stored place stays blank until confirmed.
    profile = _profile_of({"data": {"0.0": {"mode": "Sea", "incoterm": "FOB Shenzhen"}}})
    assert profile["incotermNamedPlace"] == "Shenzhen"
    assert profile["incotermPlaceSource"] == "CONTRACT_LABEL"


# ===========================================================================
# C. Named place
# ===========================================================================

def test_write_refuses_a_bare_rule_without_a_named_place(staging):
    out = _dispatch("shipment_profile_save",
                    {"shipmentId": LOT, "mode": "Truck", "incoterm": "FCA", "incotermVersion": "2020",
                     "namedPlace": "", "loadModel": "FTL", "serviceScopeConfirmed": True,
                     "cargoInsurance": {"status": "NO"}})
    assert out["ok"] is False
    assert "Pingxiang" in out["error"] or "địa điểm" in out["error"]
    assert any(issue["code"] == ep.ISSUE_MISSING_PLACE for issue in out["issues"])
    # Nothing was written.
    assert _stored_block(LOT) == {}
    assert _doc(LOT)["data"]["0.0"]["incoterm"] == "DAP"


def test_named_place_is_persisted_and_read_back(staging):
    out = _dispatch("shipment_profile_save", dict({"shipmentId": SEA_LOT}, **_valid_sea_profile()))
    assert out["ok"], out["error"]
    assert _stored_block(SEA_LOT)["incoterm_named_place"] == "Hai Phong Port"
    profile = _profile(SEA_LOT)
    assert profile["incotermNamedPlace"] == "Hai Phong Port"
    assert profile["incotermPlaceSource"] == "CONFIRMED"
    assert "Hai Phong Port" in profile["summaryLines"]


def test_clearing_the_named_place_is_refused_rather_than_silently_kept(staging):
    assert _dispatch("shipment_profile_save", dict({"shipmentId": SEA_LOT}, **_valid_sea_profile()))["ok"]
    out = _dispatch("shipment_profile_save", {"shipmentId": SEA_LOT, "namedPlace": ""}, seq=2)
    assert out["ok"] is False
    assert _stored_block(SEA_LOT)["incoterm_named_place"] == "Hai Phong Port"


# ===========================================================================
# D. Impossible combinations
# ===========================================================================

@pytest.mark.parametrize("mode,code", [
    ("Truck", "FOB"), ("Truck", "CIF"), ("Truck", "CFR"), ("Truck", "FAS"),
    ("Air", "FOB"), ("Air", "CIF"), ("Air", "CFR"), ("Air", "FAS"),
    ("Rail", "FOB"), ("Rail", "CIF"),
])
def test_maritime_rules_are_refused_for_non_maritime_modes(mode, code):
    facts = {"mode": ep.canonical_mode(mode), "incoterm": code, "incotermVersion": "2020",
             "incotermNamedPlace": "Somewhere", "loadModel": "", "serviceScopeConfirmed": True}
    issues = ep.validate_profile(facts, for_write=True)
    assert any(i["code"] == ep.ISSUE_INVALID_COMBINATION for i in issues), (mode, code, issues)


@pytest.mark.parametrize("mode,code", [
    ("Truck", "EXW"), ("Truck", "FCA"), ("Truck", "CPT"), ("Truck", "CIP"),
    ("Truck", "DAP"), ("Truck", "DPU"), ("Truck", "DDP"),
    ("Air", "FCA"), ("Air", "CPT"), ("Air", "CIP"), ("Air", "DAP"),
    ("Rail", "FCA"), ("Rail", "DAP"), ("Sea", "CIF"), ("Sea", "FOB"), ("Sea", "FAS"),
])
def test_possible_combinations_are_accepted(mode, code):
    family = {"Truck": "FTL", "Sea": "FCL", "Air": "DIRECT", "Rail": ""}[mode]
    facts = {"mode": ep.canonical_mode(mode), "incoterm": code, "incotermVersion": "2020",
             "incotermNamedPlace": "Somewhere", "loadModel": family, "serviceScopeConfirmed": True,
             "cargoInsuranceStatus": "UNKNOWN"}
    assert ep.validate_profile(facts, for_write=True) == []


def test_write_refuses_fob_road_and_leaves_the_document_untouched(staging):
    before = _doc(LOT)
    out = _dispatch("shipment_profile_save",
                    {"shipmentId": LOT, "mode": "Truck", "incoterm": "FOB", "incotermVersion": "2020",
                     "namedPlace": "Shenzhen", "loadModel": "FTL", "serviceScopeConfirmed": True,
                     "cargoInsurance": {"status": "NO"}})
    assert out["ok"] is False and out["gate"] == "PROFILE_REFUSED"
    assert "đường biển" in out["error"]
    after = _doc(LOT)
    assert after["data"]["0.0"] == before["data"]["0.0"]
    assert after["version"] == before["version"], "a refused write must not bump the version"


def test_a_historical_impossible_document_still_opens_and_is_flagged(staging):
    assert _dispatch("shipment_field_save", {"shipmentId": LOT, "fields": {"incoterm": "FOB"}})["ok"]
    profile = _profile(LOT)
    assert profile["state"] == ep.STATE_CONFIG_CHECK
    assert profile["stateLabel"] == "CẤU HÌNH CẦN KIỂM TRA"
    assert any(i["code"] == ep.ISSUE_INVALID_COMBINATION for i in profile["issues"])
    assert profile["nextAction"]["code"] == "CONFIG_CHECK"
    # The stored evidence is exactly what the operator wrote — never repaired.
    assert _doc(LOT)["data"]["0.0"]["incoterm"] == "FOB"
    assert _doc(LOT)["data"]["0.0"]["mode"] == "Truck"


# ===========================================================================
# E. Service scope is independent of the Incoterm
# ===========================================================================

def test_cif_obligation_does_not_add_a_single_service_scope_segment():
    document = {"data": {"0.0": {"mode": "Sea", "incoterm": "CIF", "execution_profile": {
        "incoterm_version": "2020", "incoterm_named_place": "Hai Phong Port", "load_model": "FCL",
        "service_scope": ["IMPORT_CUSTOMS", "FINAL_DELIVERY"], "service_scope_confirmed": True,
        "cargo_insurance": {"status": "UNKNOWN"}}}}}
    profile = _profile_of(document)
    assert profile["serviceScope"] == ["IMPORT_CUSTOMS", "FINAL_DELIVERY"]
    codes = [stage["code"] for stage in profile["stages"]]
    assert "ORIGIN_PICKUP" not in codes
    assert "EXPORT_CUSTOMS" not in codes


def test_a_buyer_side_scope_never_grows_a_factory_pickup_stage():
    document = {"data": {"0.0": {"mode": "Sea", "incoterm": "FOB", "execution_profile": {
        "incoterm_version": "2020", "incoterm_named_place": "Shenzhen", "load_model": "FCL",
        "service_scope": ["IMPORT_CUSTOMS", "DESTINATION_TRUCKING", "FINAL_DELIVERY"],
        "service_scope_confirmed": True, "cargo_insurance": {"status": "NO"}}}}}
    profile = _profile_of(document)
    codes = [stage["code"] for stage in profile["stages"]]
    # FCL equipment comes from the LOAD MODEL (not from the Incoterm and not
    # from the scope); everything else here is scope-owned and buyer-side only.
    assert codes == ["SEA_EQUIPMENT", "IMPORT_CUSTOMS", "DELIVERY"]
    assert "ORIGIN_PICKUP" not in codes
    by_code = {stage["code"]: stage for stage in profile["stages"]}
    assert by_code["SEA_EQUIPMENT"]["reason"] == ep.REASON_LOAD_MODEL_REQUIREMENT
    assert all(by_code[code]["reason"] == ep.REASON_SERVICE_SCOPE
               for code in ("IMPORT_CUSTOMS", "DELIVERY"))


def test_an_origin_scope_that_really_exists_does_grow_the_pickup_stage():
    document = {"data": {"0.0": {"mode": "Truck", "incoterm": "EXW", "execution_profile": {
        "incoterm_version": "2020", "incoterm_named_place": "Bằng Tường", "load_model": "FTL",
        "service_scope": ["ORIGIN_PICKUP", "EXPORT_CUSTOMS", "IMPORT_CUSTOMS", "FINAL_DELIVERY"],
        "service_scope_confirmed": True, "cargo_insurance": {"status": "NO"}}}}}
    profile = _profile_of(document)
    pickup = next(stage for stage in profile["stages"] if stage["code"] == "ORIGIN_PICKUP")
    assert pickup["reason"] == ep.REASON_SERVICE_SCOPE
    # FTL owns the truck-type requirement, so the same persisted fact is asked
    # for exactly ONCE — through the load-model stage, with its own label.
    truck = next(stage for stage in profile["stages"] if stage["code"] == "ROAD_TRUCK_PROFILE")
    assert pickup["missing"] == "" and not pickup["done"]
    assert truck["missing"] and truck["reason"] == ep.REASON_LOAD_MODEL_REQUIREMENT
    assert profile["nextAction"]["code"] == "ROAD_TRUCK_PROFILE"
    assert "Xác nhận loại xe" in profile["nextAction"]["label"]


def test_service_scope_must_be_confirmed_before_anything_is_written(staging):
    out = _dispatch("shipment_profile_save", dict(
        {"shipmentId": SEA_LOT}, **_valid_sea_profile(serviceScopeConfirmed=False)))
    assert out["ok"] is False
    assert any(i["code"] == ep.ISSUE_MISSING_SERVICE_SCOPE for i in out["issues"])
    assert _stored_block(SEA_LOT) == {}


def test_unknown_scope_codes_are_dropped_and_order_is_canonical():
    assert ep.normalize_service_scope(["FINAL_DELIVERY", "NOPE", "ORIGIN_PICKUP"]) == [
        "ORIGIN_PICKUP", "FINAL_DELIVERY"]


# ===========================================================================
# F. Load models, equipment and operating presets
# ===========================================================================

def test_sea_fcl_equipment_comes_from_the_existing_container_units(tmp_path):
    document = {"data": {
        "0.0": {"mode": "Sea", "incoterm": "CIF", "execution_profile": {
            "incoterm_version": "2020", "incoterm_named_place": "Hai Phong Port",
            "load_model": "FCL", "service_scope": ["IMPORT_CUSTOMS"], "service_scope_confirmed": True,
            "cargo_insurance": {"status": "UNKNOWN"}}},
        "1.2": {"transport_legs": [{
            "id": "leg-1", "sequence": 1, "mode": "Sea", "origin": "Shenzhen",
            "destination": "Hai Phong", "carrier": "Maersk", "booking_no": "BKG-1",
            "mbl": "MBL-1", "hbl": "HBL-1", "vessel": "V-1", "etd": "2026-09-01", "eta": "",
            "atd": "", "ata": "",
            "units": [
                {"id": "u1", "kind": "container", "number": "MSKU1", "type_size": "40HC", "seal_no": ""},
                {"id": "u2", "kind": "container", "number": "MSKU2", "type_size": "40HC", "seal_no": ""},
                {"id": "u3", "kind": "container", "number": "MSKU3", "type_size": "20GP", "seal_no": ""},
            ]}]}}}
    profile = _profile_of(document)
    assert profile["equipment"]["count"] == 3, "every container must be read, not one string"
    assert profile["equipment"]["presets"] == [{"code": "20GP", "count": 1}, {"code": "40HC", "count": 2}]
    assert profile["stages"] and any(s["code"] == "SEA_EQUIPMENT" and s["done"] for s in profile["stages"])
    assert any("1 × 20GP, 2 × 40HC" in line for line in profile["summaryLines"])


def test_sea_fcl_without_equipment_asks_for_the_container_type():
    """FCL: the container type comes BEFORE the booking it makes possible."""

    document = {"data": {
        "0.0": {"mode": "Sea", "incoterm": "CIF", "execution_profile": {
            "incoterm_version": "2020", "incoterm_named_place": "Hai Phong Port", "load_model": "FCL",
            "service_scope": ["MAIN_CARRIAGE", "IMPORT_CUSTOMS"], "service_scope_confirmed": True,
            "cargo_insurance": {"status": "NO"}}}}}
    profile = _profile_of(document)
    assert profile["nextAction"]["code"] == "SEA_EQUIPMENT"
    assert "Bổ sung loại container" in profile["nextAction"]["label"]
    assert profile["nextAction"]["reason"] == ep.REASON_LOAD_MODEL_REQUIREMENT

    # With the equipment recorded, the SAME document moves on to the carriage
    # documents — the container requirement really was the blocker.
    document["data"]["1.2"] = {"carrier": "Maersk", "booking_no": "", "mbl": "", "hbl": ""}
    document["data"]["0.0"]["execution_profile"]["cargo_insurance"] = {"status": "NO"}
    document["data"]["1.2"]["transport_legs"] = [{
        "id": "leg-1", "sequence": 1, "mode": "Sea", "origin": "Shenzhen", "destination": "Hai Phong",
        "carrier": "Maersk", "booking_no": "BKG-1", "mbl": "", "hbl": "", "vessel": "", "etd": "",
        "eta": "", "atd": "", "ata": "", "units": [
            {"id": "u1", "kind": "container", "number": "MSKU1", "type_size": "40HC", "seal_no": ""}]}]
    after = _profile_of(document)
    assert after["nextAction"]["code"] == "SEA_DOCUMENTS"
    assert "vận đơn" in after["nextAction"]["label"]


def test_sea_lcl_never_demands_a_container_number():
    document = {"data": {"0.0": {"mode": "Sea", "incoterm": "CIF", "execution_profile": {
        "incoterm_version": "2020", "incoterm_named_place": "Hai Phong Port", "load_model": "LCL",
        "service_scope": ["MAIN_CARRIAGE", "IMPORT_CUSTOMS", "FINAL_DELIVERY"],
        "service_scope_confirmed": True, "cargo_insurance": {"status": "NO"}}}}}
    profile = _profile_of(document)
    codes = [stage["code"] for stage in profile["stages"]]
    assert "SEA_EQUIPMENT" not in codes
    consolidation = next(s for s in profile["stages"] if s["code"] == "SEA_CONSOLIDATION")
    assert "không sở hữu nguyên container" in consolidation["detail"]
    assert all("container" not in (stage["missing"] or "") for stage in profile["stages"])


@pytest.mark.parametrize("preset", ["17.5m", "13.5m", "9.6m", "6.8m"])
def test_road_ftl_operating_presets_are_recognised(preset):
    document = {"data": {
        "0.0": {"mode": "Truck", "incoterm": "FCA", "execution_profile": {
            "incoterm_version": "2020", "incoterm_named_place": "Bình Tường", "load_model": "FTL",
            "service_scope": ["ORIGIN_PICKUP", "FINAL_DELIVERY"], "service_scope_confirmed": True,
            "cargo_insurance": {"status": "NO"}}},
        "1.2": {"pickup_truck_type": preset}}}
    profile = _profile_of(document)
    assert profile["truck"]["preset"] == preset
    assert profile["truck"]["known"] is True
    truck_stage = next(s for s in profile["stages"] if s["code"] == "ROAD_TRUCK_PROFILE")
    assert truck_stage["done"] and truck_stage["reason"] == ep.REASON_LOAD_MODEL_REQUIREMENT


def test_road_ftl_without_a_truck_asks_to_confirm_the_truck_type():
    document = {"data": {"0.0": {"mode": "Truck", "incoterm": "FCA", "execution_profile": {
        "incoterm_version": "2020", "incoterm_named_place": "Bình Tường", "load_model": "FTL",
        "service_scope": ["ORIGIN_PICKUP"], "service_scope_confirmed": True,
        "cargo_insurance": {"status": "NO"}}}}}
    profile = _profile_of(document)
    assert profile["nextAction"]["code"] == "ROAD_TRUCK_PROFILE"
    assert "Xác nhận loại xe" in profile["nextAction"]["label"]


def test_road_ltl_demands_no_truck_length_at_all():
    document = {"data": {"0.0": {"mode": "Truck", "incoterm": "FCA", "execution_profile": {
        "incoterm_version": "2020", "incoterm_named_place": "Pingxiang Warehouse", "load_model": "LTL",
        "service_scope": ["ORIGIN_TERMINAL_OR_BORDER", "IMPORT_CUSTOMS", "FINAL_DELIVERY"],
        "service_scope_confirmed": True, "cargo_insurance": {"status": "NO"}}}}}
    profile = _profile_of(document)
    codes = [stage["code"] for stage in profile["stages"]]
    assert "ROAD_TRUCK_PROFILE" not in codes
    assert "SEA_EQUIPMENT" not in codes
    assert profile["nextAction"]["code"] != "ROAD_TRUCK_PROFILE"
    facts = ep.persisted_facts(document)
    assert ep.truck_profile(facts)["known"] is False


def test_truck_length_never_implies_capacity():
    """The presets are company operating profiles, not capacity regulations.

    Asserted on the PROJECTION (the values a caller can actually read), not on
    the source text: a disclaimer mentioning the word "tonnes" is the opposite
    of an inference.
    """

    assert [code for code, _ in ep.TRUCK_PRESETS] == ["17.5m", "13.5m", "9.6m", "6.8m", "OTHER"]
    profile = ep.truck_profile({"pickupTruckType": "17.5m"})
    assert set(profile) == {"pickupTruckType", "unitTypes", "known", "preset", "presetLabel"}
    serialized = json.dumps(ep.projection_options(), ensure_ascii=False).lower()
    for forbidden in ("tonne", "tấn", "cbm", "payload", "max_weight", "maxweight", "price", "giá"):
        assert forbidden not in serialized, forbidden


@pytest.mark.parametrize("load_model,expected", [
    ("DIRECT", "Hàng nguyên / chuyến trực tiếp"),
    ("CONSOLIDATED", "Hàng lẻ / ghép lô"),
])
def test_air_service_profiles(load_model, expected):
    document = {"data": {"0.0": {"mode": "Air", "incoterm": "CPT", "execution_profile": {
        "incoterm_version": "2020", "incoterm_named_place": "Sân bay Nội Bài", "load_model": load_model,
        "service_scope": ["MAIN_CARRIAGE", "IMPORT_CUSTOMS", "FINAL_DELIVERY"],
        "service_scope_confirmed": True, "cargo_insurance": {"status": "UNKNOWN"}}}}}
    profile = _profile_of(document)
    assert profile["mode"] == "AIR"
    assert profile["loadModel"] == load_model
    assert profile["loadModelLabel"] == expected
    assert ep.validate_profile(ep.profile_facts(document), for_write=False) == []
    codes = [stage["code"] for stage in profile["stages"]]
    assert "SEA_EQUIPMENT" not in codes and "ROAD_TRUCK_PROFILE" not in codes


def test_air_never_offers_maritime_rules_or_road_truck_presets():
    codes = [code for code, _ in ep.load_models_for_mode(ep.MODE_AIR)]
    assert codes == ["DIRECT", "CONSOLIDATED", "OTHER"]
    assert ep.load_models_for_mode(ep.MODE_RAIL) == ()
    facts = {"mode": "AIR", "incoterm": "CIF", "incotermVersion": "2020",
             "incotermNamedPlace": "Nội Bài", "serviceScopeConfirmed": True}
    assert any(i["code"] == ep.ISSUE_INVALID_COMBINATION
               for i in ep.validate_profile(facts, for_write=True))


def test_rail_is_never_forced_into_road_sea_or_air_assumptions():
    document = {"data": {"0.0": {"mode": "Rail", "incoterm": "DAP", "execution_profile": {
        "incoterm_version": "2020", "incoterm_named_place": "Ga Đông Anh",
        "service_scope": ["MAIN_CARRIAGE", "IMPORT_CUSTOMS"], "service_scope_confirmed": True,
        "cargo_insurance": {"status": "NO"}}}}}
    profile = _profile_of(document)
    assert profile["mode"] == "RAIL"
    assert profile["loadModel"] == "", "rail has no load-model family in this slice"
    codes = [stage["code"] for stage in profile["stages"]]
    assert codes == ["MAIN_CARRIAGE", "RAIL_CARRIAGE", "IMPORT_CUSTOMS"]
    assert ep.validate_profile(ep.profile_facts(document), for_write=False) == []


def test_mode_vocabulary_reuses_the_existing_shipment_mode_field(staging):
    assert _dispatch("shipment_profile_save", dict({"shipmentId": SEA_LOT}, **_valid_sea_profile()))["ok"]
    stored = _doc(SEA_LOT)
    assert stored["data"]["0.0"]["mode"] == "Sea", "the existing mode vocabulary is kept"
    assert _profile(SEA_LOT)["mode"] == "SEA", "the canonical profile mode is the display vocabulary"
    assert ep.STORED_MODE_BY_CANONICAL == {"ROAD": "Truck", "SEA": "Sea", "AIR": "Air", "RAIL": "Rail"}


# ===========================================================================
# G. Insurance — two distinct truths
# ===========================================================================

def test_cif_2020_seller_obligation_keeps_institute_cargo_clauses_c():
    obligation = ep.incoterm_insurance("CIF", "2020")
    assert obligation["obligation"] == ep.INSURANCE_SELLER_REQUIRED
    assert obligation["clause"] == ep.CLAUSE_C
    assert "Nhóm C" in obligation["note"]


def test_cif_2010_keeps_the_same_minimum_clause():
    assert ep.incoterm_insurance("CIF", "2010")["clause"] == ep.CLAUSE_C


def test_cip_2020_raises_the_default_cover_to_clauses_a():
    obligation = ep.incoterm_insurance("CIP", "2020")
    assert obligation["obligation"] == ep.INSURANCE_SELLER_REQUIRED
    assert obligation["clause"] == ep.CLAUSE_A
    assert "Nhóm A" in obligation["note"]


def test_cip_2010_is_never_projected_as_2020_clause_a():
    obligation = ep.incoterm_insurance("CIP", "2010")
    assert obligation["obligation"] == ep.INSURANCE_SELLER_REQUIRED
    assert obligation["clause"] != ep.CLAUSE_A
    assert obligation["clause"] == ep.CLAUSE_2010_MINIMUM
    assert "KHÔNG áp dụng Nhóm A" in obligation["note"]
    # …and the 2010 lot's own projection must not claim Clause A either.
    document = {"data": {"0.0": {"mode": "Sea", "incoterm": "CIP", "execution_profile": {
        "incoterm_version": "2010", "incoterm_named_place": "Hai Phong Port", "load_model": "FCL",
        "service_scope": ["IMPORT_CUSTOMS"], "service_scope_confirmed": True,
        "cargo_insurance": {"status": "UNKNOWN"}}}}}
    profile = _profile_of(document)
    projected = profile["insurance"]
    assert projected["clause"] != ep.CLAUSE_A
    assert projected["clause"] == ep.CLAUSE_2010_MINIMUM
    assert projected["clauseLabel"] != ep.CLAUSE_LABELS[ep.CLAUSE_A]
    lines = "    ".join(profile["summaryLines"])
    assert "không áp dụng Nhóm A" in lines, "the projection must say Clause A is NOT applied"


def test_unknown_incoterms_version_never_claims_clause_a_for_cip():
    obligation = ep.incoterm_insurance("CIP", "")
    assert obligation["obligation"] == ep.INSURANCE_SELLER_REQUIRED
    assert obligation["clause"] == ep.CLAUSE_UNKNOWN


@pytest.mark.parametrize("code", ["EXW", "FCA", "FOB", "CPT", "DAP", "DDP", "DPU", "FAS", "CFR"])
def test_other_rules_say_only_that_the_seller_is_not_obliged(code):
    obligation = ep.incoterm_insurance(code, "2020")
    assert obligation["obligation"] == ep.INSURANCE_NOT_REQUIRED_BY_INCOTERM
    assert obligation["note"] == "Incoterm không bắt buộc người bán thu xếp bảo hiểm."
    assert "không có bảo hiểm" not in obligation["note"].lower()


@pytest.mark.parametrize("status", ["UNKNOWN", "NO", "YES"])
def test_actual_insurance_states_round_trip(staging, status):
    insurance = {"status": status}
    if status == "YES":
        insurance.update({"arrangedBy": "Khách hàng", "insurerName": "PJICO",
                          "policyNo": "POL-2026-1", "coverageNote": "Nhóm C"})
    out = _dispatch("shipment_profile_save", dict(
        {"shipmentId": SEA_LOT}, **_valid_sea_profile(cargoInsurance=insurance)))
    assert out["ok"], out["error"]
    stored = _stored_block(SEA_LOT)["cargo_insurance"]
    assert stored["status"] == status
    profile = _profile(SEA_LOT)
    assert profile["insurance"]["actualStatus"] == status
    assert profile["insurance"]["actualStatusStated"] is True


def test_unknown_actual_insurance_is_not_the_same_as_no(staging):
    assert _dispatch("shipment_profile_save", dict({"shipmentId": SEA_LOT}, **_valid_sea_profile(
        cargoInsurance={"status": "UNKNOWN"})))["ok"]
    unknown = _stored_block(SEA_LOT)["cargo_insurance"]["status"]
    assert _dispatch("shipment_profile_save", dict(
        {"shipmentId": SEA_LOT}, **_valid_sea_profile(cargoInsurance={"status": "NO"})), seq=2)["ok"]
    stated_no = _stored_block(SEA_LOT)["cargo_insurance"]["status"]
    assert (unknown, stated_no) == ("UNKNOWN", "NO")


def test_a_legacy_document_without_an_insurance_answer_stays_unknown():
    profile = _profile_of({"data": {"0.0": {"mode": "Sea", "incoterm": "CIF"}}})
    insurance = profile["insurance"]
    assert insurance["obligation"] == ep.INSURANCE_SELLER_REQUIRED
    assert insurance["actualStatus"] == "UNKNOWN"
    assert insurance["actualStatusStated"] is False
    lines = " ".join(profile["summaryLines"])
    assert "Chứng từ bảo hiểm: Chưa xác nhận" in lines


def test_cif_obligation_with_actual_unknown_asks_for_the_certificate():
    """The Incoterm obligation ALONE makes the document check relevant.

    Nothing in the configured scope says "we arrange insurance": the only
    reason the stage exists is the CIF seller obligation — and UNKNOWN is not
    evidence, so the check stays outstanding.
    """

    def _doc_block(delivered: bool) -> dict:
        document = {"data": {
            "0.0": {"mode": "Sea", "incoterm": "CIF", "execution_profile": {
                "incoterm_version": "2020", "incoterm_named_place": "Hai Phong Port",
                "load_model": "LCL", "service_scope": ["IMPORT_CUSTOMS"],
                "service_scope_confirmed": True, "cargo_insurance": {"status": "UNKNOWN"}}},
            "2.4": {"tk_no": "105588421330", "customs_status": True}}}
        if delivered:
            document["data"]["2.7"] = {"is_delivered": True, "addr": "Bắc Ninh"}
        return document

    profile = _profile_of(_doc_block(False))
    assert profile["insurance"]["obligation"] == ep.INSURANCE_SELLER_REQUIRED
    assert profile["insurance"]["actualStatus"] == "UNKNOWN"
    evidence = next(stage for stage in profile["stages"] if stage["code"] == "INSURANCE_EVIDENCE")
    assert evidence["reason"] == ep.REASON_INCOTERM_EXPECTATION, "not a scope task — an Incoterm one"
    assert evidence["missing"] == "Kiểm tra chứng từ bảo hiểm."
    assert profile["nextAction"]["code"] == "INSURANCE_EVIDENCE"

    # Delivered, but the profile still owes the evidence it was configured to
    # obtain: "done" and "unknown" are different statements.
    after = _profile_of(_doc_block(True))
    assert after["nextAction"]["code"] == "INSURANCE_EVIDENCE"
    assert after["nextAction"]["label"] == "Kiểm tra chứng từ bảo hiểm."

    # …and an explicit "no insurance" under a CIF obligation is NOT the end of
    # the workflow either: it is a CONFIRMED MISMATCH (section G2 below).
    stated_no = _doc_block(True)
    stated_no["data"]["0.0"]["execution_profile"]["cargo_insurance"] = {"status": "NO"}
    mismatch = _profile_of(stated_no)
    assert mismatch["nextAction"]["code"] == "INSURANCE_EVIDENCE"
    assert mismatch["nextAction"]["label"] == ep.INSURANCE_MISMATCH_INCOTERM
    assert mismatch["nextAction"]["code"] != "DONE"


def test_cif_never_sets_the_actual_insurance_by_itself(staging):
    assert _dispatch("shipment_profile_save", dict(
        {"shipmentId": SEA_LOT}, **_valid_sea_profile(incoterm="CIF")))["ok"]
    assert _stored_block(SEA_LOT)["cargo_insurance"]["status"] == "UNKNOWN"


def test_insurance_evidence_is_required_before_any_write(staging):
    payload = _valid_sea_profile()
    payload.pop("cargoInsurance")
    out = _dispatch("shipment_profile_save", {**payload, "shipmentId": SEA_LOT})
    assert out["ok"] is False
    assert any(i["code"] == ep.ISSUE_INSURANCE_EVIDENCE for i in out["issues"])


def test_policy_details_are_dropped_when_the_actual_status_is_not_yes(staging):
    yes = {"status": "YES", "insurerName": "PJICO", "policyNo": "POL-1", "arrangedBy": "Khách"}
    assert _dispatch("shipment_profile_save", dict(
        {"shipmentId": SEA_LOT}, **_valid_sea_profile(cargoInsurance=yes)))["ok"]
    assert _stored_block(SEA_LOT)["cargo_insurance"]["policy_or_certificate_number"] == "POL-1"
    out = _dispatch("shipment_profile_save", {"shipmentId": SEA_LOT,
                                              "cargoInsurance": {"status": "NO"}}, seq=2)
    assert out["ok"], out["error"]
    stored = _stored_block(SEA_LOT)["cargo_insurance"]
    assert stored["status"] == "NO"
    assert stored["policy_or_certificate_number"] == ""
    assert stored["insurer_name"] == ""
    # A partial update that omits the insurance block leaves it alone.
    assert _dispatch("shipment_profile_save", {"shipmentId": SEA_LOT, "namedPlace": "Hải Phòng"},
                     seq=3)["ok"]
    assert _stored_block(SEA_LOT)["cargo_insurance"]["status"] == "NO"


# ===========================================================================
# G2. Insurance — the CONFIRMED MISMATCH (CIF/CIP NO) and the settled NO
# ===========================================================================

def _insurance_doc(*, incoterm: str, version: str = "2020", status: str,
                   scope: list[str] | None = None, delivered: bool = False,
                   mode: str = "Sea", load_model: str = "LCL") -> dict:
    """One shipment document with the SAME everything except the insurance."""

    document = {"data": {
        "0.0": {"mode": mode, "incoterm": incoterm, "execution_profile": {
            "incoterm_version": version, "incoterm_named_place": "Hai Phong Port",
            "load_model": load_model,
            "service_scope": ["IMPORT_CUSTOMS"] if scope is None else scope,
            "service_scope_confirmed": True, "cargo_insurance": {"status": status}}},
        "2.4": {"tk_no": "105588421330", "customs_status": True}}}
    if delivered:
        document["data"]["2.7"] = {"is_delivered": True, "addr": "Bắc Ninh"}
    return document


def _insurance_stage(profile: dict) -> dict:
    return next(stage for stage in profile["stages"] if stage["code"] == "INSURANCE_EVIDENCE")


def test_cif_2020_with_unknown_asks_to_check_the_certificate():
    profile = _profile_of(_insurance_doc(incoterm="CIF", status="UNKNOWN"))
    stage = _insurance_stage(profile)
    assert stage["done"] is False and stage["mismatch"] is False
    assert stage["missing"] == "Kiểm tra chứng từ bảo hiểm."
    assert profile["nextAction"]["code"] == "INSURANCE_EVIDENCE"
    assert profile["nextAction"]["label"] == "Kiểm tra chứng từ bảo hiểm."


def test_cif_2020_with_actual_no_is_a_confirmed_mismatch_not_done():
    """NO is EVIDENCE, not completion: CIF required cover and the lot says none."""

    profile = _profile_of(_insurance_doc(incoterm="CIF", status="NO"))
    stage = _insurance_stage(profile)
    assert stage["done"] is False, "an explicit NO must not satisfy the CIF obligation"
    assert stage["mismatch"] is True
    assert stage["missing"] == ep.INSURANCE_MISMATCH_INCOTERM
    assert "KHÔNG CÓ" in stage["missing"]
    # A clear exception, not a routine amber gap.
    assert profile["nextAction"]["code"] == "INSURANCE_EVIDENCE"
    assert profile["nextAction"]["label"] == ep.INSURANCE_MISMATCH_INCOTERM
    assert profile["nextAction"]["tone"] == "red"
    assert ep.INSURANCE_MISMATCH_LABEL in profile["summaryLines"]
    # The persisted fact itself is never rewritten into UNKNOWN.
    assert profile["insurance"]["actualStatus"] == "NO"
    assert profile["insurance"]["actualStatusStated"] is True


def test_cif_2020_with_actual_yes_satisfies_the_insurance_stage():
    profile = _profile_of(_insurance_doc(incoterm="CIF", status="YES"))
    stage = _insurance_stage(profile)
    assert stage["done"] is True and stage["missing"] == "" and stage["mismatch"] is False
    assert profile["nextAction"]["code"] != "INSURANCE_EVIDENCE"
    assert ep.INSURANCE_MISMATCH_LABEL not in profile["summaryLines"]


def test_cip_2020_with_actual_no_is_also_a_mismatch():
    profile = _profile_of(_insurance_doc(incoterm="CIP", status="NO"))
    stage = _insurance_stage(profile)
    assert stage["mismatch"] is True and stage["done"] is False
    assert profile["nextAction"]["label"] == ep.INSURANCE_MISMATCH_INCOTERM
    assert profile["insurance"]["clause"] == ep.CLAUSE_A, "CIP 2020 keeps Clause A"


def test_a_non_insurance_term_with_actual_no_is_a_settled_factual_state():
    """FCA owes nothing: the operator's explicit NO is a complete answer."""

    profile = _profile_of(_insurance_doc(incoterm="FCA", status="NO", mode="Truck",
                                         load_model="LTL", scope=["IMPORT_CUSTOMS", "FINAL_DELIVERY"]))
    assert profile["insurance"]["obligation"] == ep.INSURANCE_NOT_REQUIRED_BY_INCOTERM
    assert [stage["code"] for stage in profile["stages"] if stage["code"] == "INSURANCE_EVIDENCE"] == []
    assert profile["nextAction"]["code"] != "INSURANCE_EVIDENCE"
    assert ep.INSURANCE_MISMATCH_LABEL not in profile["summaryLines"]
    assert "Bảo hiểm hàng hóa: Không có bảo hiểm" in " ".join(profile["summaryLines"])


def test_the_confirmed_insurance_scope_is_not_complete_while_the_lot_says_no():
    """Trường Thành was hired to arrange cover — an explicit NO cannot finish it."""

    scope = ["CARGO_INSURANCE_ARRANGEMENT", "IMPORT_CUSTOMS"]
    profile = _profile_of(_insurance_doc(incoterm="FCA", status="NO", mode="Truck",
                                         load_model="LTL", scope=scope))
    stage = _insurance_stage(profile)
    assert stage["reason"] == ep.REASON_SERVICE_SCOPE
    assert stage["done"] is False and stage["mismatch"] is True
    assert stage["missing"] == ep.INSURANCE_MISMATCH_SCOPE
    assert profile["nextAction"]["code"] == "INSURANCE_EVIDENCE"
    assert profile["nextAction"]["tone"] == "red"

    # The same scope with YES really settles it.
    done = _profile_of(_insurance_doc(incoterm="FCA", status="YES", mode="Truck",
                                      load_model="LTL", scope=scope))
    assert _insurance_stage(done)["done"] is True


def test_a_delivered_cif_lot_with_actual_no_is_never_done():
    profile = _profile_of(_insurance_doc(incoterm="CIF", status="NO", delivered=True))
    assert profile["persisted"]["delivered"] is True
    assert profile["nextAction"]["code"] != "DONE"
    assert profile["nextAction"]["label"] == ep.INSURANCE_MISMATCH_INCOTERM
    assert profile["nextAction"]["tone"] == "red"

    # …while the same delivered lot with YES is finished.
    finished = _profile_of(_insurance_doc(incoterm="CIF", status="YES", delivered=True))
    assert finished["nextAction"]["code"] == "DONE"
    assert finished["nextAction"]["label"] == "Hoàn thành"


# ===========================================================================
# H. Workflow derivation and next action
# ===========================================================================

def test_every_stage_carries_a_reason_from_the_allowed_categories():
    document = {"data": {
        "0.0": {"mode": "Truck", "incoterm": "EXW", "execution_profile": {
            "incoterm_version": "2020", "incoterm_named_place": "Bằng Tường", "load_model": "FTL",
            "service_scope": ["ORIGIN_PICKUP", "EXPORT_CUSTOMS", "ORIGIN_TERMINAL_OR_BORDER",
                              "IMPORT_CUSTOMS", "DESTINATION_TRUCKING", "FINAL_DELIVERY"],
            "service_scope_confirmed": True, "cargo_insurance": {"status": "UNKNOWN"}}},
        "1.2": {"pickup_truck_type": "17.5m", "tk_no": "102030405060"},
        "2.4": {"tk_no": "102030405060", "customs_status": True},
        "2.7": {"is_delivered": True, "addr": "Bắc Ninh"}}}
    profile = _profile_of(document)
    assert profile["stages"], "a full scope must derive stages"
    for stage in profile["stages"]:
        assert stage["reason"] in {
            ep.REASON_INCOTERM_EXPECTATION, ep.REASON_SERVICE_SCOPE,
            ep.REASON_MODE_REQUIREMENT, ep.REASON_LOAD_MODEL_REQUIREMENT,
            ep.REASON_PERSISTED_FACT_DEPENDENCY}
        assert stage["reasonLabel"]


def test_irrelevant_branches_never_produce_a_next_action():
    document = {"data": {"0.0": {"mode": "Truck", "incoterm": "FCA", "execution_profile": {
        "incoterm_version": "2020", "incoterm_named_place": "Pingxiang Warehouse", "load_model": "LTL",
        "service_scope": ["ORIGIN_TERMINAL_OR_BORDER", "FINAL_DELIVERY"],
        "service_scope_confirmed": True, "cargo_insurance": {"status": "NO"}}}}}
    profile = _profile_of(document)
    labels = " ".join([profile["nextAction"]["label"], profile["nextAction"]["detail"]]
                      + [stage["missing"] for stage in profile["stages"]])
    for irrelevant in ("Xác nhận loại xe", "container", "xe giao", "booking", "tời khai"):
        assert irrelevant not in labels, f"irrelevant branch leaked: {irrelevant}"


def test_delivered_shipment_is_finished():
    document = {"data": {
        "0.0": {"mode": "Truck", "incoterm": "DAP", "execution_profile": {
            "incoterm_version": "2020", "incoterm_named_place": "Bắc Ninh", "load_model": "LTL",
            "service_scope": ["IMPORT_CUSTOMS", "FINAL_DELIVERY"], "service_scope_confirmed": True,
            "cargo_insurance": {"status": "NO"}}},
        "2.7": {"is_delivered": True, "addr": "Bắc Ninh"}}}
    profile = _profile_of(document)
    assert profile["nextAction"]["code"] == "DONE"
    assert profile["nextAction"]["label"] == "Hoàn thành"


def test_a_sea_document_stage_is_only_demanded_when_the_carriage_is_ours():
    """FOB/CIF/CFR: the seller's booking is the seller's work, not ours.

    Same document (carrier recorded, booking/MBL blank) — only the confirmed
    Trường Thành scope differs. When the main carriage is NOT ours the blank
    booking is read-only evidence and can never become a next action.
    """

    import copy

    base = {"data": {
        "0.0": {"mode": "Sea", "incoterm": "CIF", "execution_profile": {
            "incoterm_version": "2020", "incoterm_named_place": "Hai Phong Port",
            "load_model": "LCL", "service_scope": ["MAIN_CARRIAGE"],
            "service_scope_confirmed": True, "cargo_insurance": {"status": "NO"}}},
        "1.2": {"transport_legs": [{
            "id": "leg-1", "sequence": 1, "mode": "Sea", "origin": "Shenzhen",
            "destination": "Hai Phong", "carrier": "Maersk", "booking_no": "", "mbl": "",
            "hbl": "", "vessel": "", "etd": "", "eta": "", "atd": "", "ata": "",
            "mawb": "", "hawb": "", "flight_no": "", "units": []}]}}}

    theirs = copy.deepcopy(base)
    theirs["data"]["0.0"]["execution_profile"]["service_scope"] = ["IMPORT_CUSTOMS", "FINAL_DELIVERY"]

    our_profile = _profile_of(base)
    assert our_profile["nextAction"]["code"] == "SEA_DOCUMENTS"
    assert "booking" in our_profile["nextAction"]["label"]

    their_profile = _profile_of(theirs)
    their_codes = [stage["code"] for stage in their_profile["stages"]]
    assert "SEA_DOCUMENTS" in their_codes, "the recorded documents stay visible as evidence"
    evidence = next(stage for stage in their_profile["stages"] if stage["code"] == "SEA_DOCUMENTS")
    assert evidence["done"] and not evidence["missing"]
    assert evidence["reason"] == ep.REASON_PERSISTED_FACT_DEPENDENCY
    assert their_profile["nextAction"]["code"] != "SEA_DOCUMENTS"
    assert "booking" not in (their_profile["nextAction"]["label"] + their_profile["nextAction"]["detail"])


# ===========================================================================
# I. Backward compatibility / UNKNOWN
# ===========================================================================

def test_a_legacy_document_opens_and_is_honestly_incomplete(staging):
    profile = _profile(LOT)
    assert profile["state"] == ep.STATE_INCOMPLETE
    assert profile["stateLabel"] == "Hồ sơ lô còn thiếu"
    assert profile["incoterm"] == "DAP"
    assert profile["incotermVersion"] == ""
    assert profile["incotermNamedPlace"] == ""
    assert profile["loadModel"] == ""
    assert profile["serviceScope"] == []
    assert profile["serviceScopeConfirmed"] is False
    assert profile["insurance"]["actualStatus"] == "UNKNOWN"
    assert profile["nextAction"]["code"] == "PROFILE_INCOMPLETE"
    assert profile["mode"] == "ROAD" and profile["storedMode"] == "Truck"


def test_unknown_stays_unknown_and_never_becomes_a_default(staging):
    out = _dispatch("shipment_profile_save", {
        "shipmentId": SEA_LOT, "mode": "Sea", "incoterm": "CIF", "incotermVersion": "",
    })
    assert out["ok"] is False, "a version-less new configuration must be refused"
    assert _stored_block(SEA_LOT) == {}
    assert _doc(SEA_LOT)["data"]["0.0"]["incoterm"] == "DAP", "nothing was silently upgraded"


def test_a_document_with_no_profile_block_at_all_never_crashes():
    for document in ({}, {"data": None}, {"data": {"0.0": {}}}, {"data": {"0.0": {"mode": "Sea"}}}):
        profile = ep.build_execution_profile(document)
        assert profile["state"] in {ep.STATE_INCOMPLETE, ep.STATE_CONFIG_CHECK}
        assert profile["summaryLines"]


def test_the_profile_projection_adds_no_forbidden_duplicate_field():
    """No ``mode_v2`` / ``new_incoterm`` / ``sea_incoterm`` twin may exist."""

    for twin in ("mode_v2", "new_incoterm", "sea_incoterm", "road_incoterm",
                 "truck_type_v2", "customs_v2", "incoterm_profile_v2"):
        assert twin not in vm.FIELD_PATHS, twin
    source = (ROOT / "core" / "shipment_execution_profile.py").read_text(encoding="utf-8")
    for twin in ("mode_v2", "new_incoterm", "sea_incoterm", "road_incoterm", "customs_v2"):
        assert twin not in source, twin
    # The transport-field whitelist is untouched by this slice.
    assert "incoterm_version" not in vm.FIELD_PATHS
    assert "load_model" not in vm.FIELD_PATHS


# ===========================================================================
# J. The bounded write path — RBAC, audit, fresh readback
# ===========================================================================

def test_write_event_is_registered_in_the_one_dispatcher():
    assert "shipment_profile_save" in vm.PHASE_B_EVENTS
    assert vm._HANDLERS["shipment_profile_save"] is vm._handle_shipment_profile_save


def test_rbac_denies_the_profile_write_for_a_viewer(staging):
    import streamlit as st

    before = _doc(LOT)
    st.session_state["current_user"] = {"username": "viewer.profile", "role": "VIEWER", "user_id": "U-V"}
    out = _dispatch("shipment_profile_save", dict({"shipmentId": LOT}, **_valid_sea_profile()))
    assert out["ok"] is False
    assert "RBAC" in out["error"]
    after = _doc(LOT)
    assert after["data"]["0.0"] == before["data"]["0.0"] and after["version"] == before["version"]


def test_an_unknown_shipment_is_refused(staging):
    out = _dispatch("shipment_profile_save", dict({"shipmentId": "LO-NOPE"}, **_valid_sea_profile()))
    assert out["ok"] is False and "Không tìm thấy lô" in out["error"]


def test_write_persists_audits_and_reads_back_authoritatively(staging):
    out = _dispatch("shipment_profile_save", dict(
        {"shipmentId": SEA_LOT, "requestId": "REQ-AUDIT"}, **_valid_sea_profile()))
    assert out["ok"] is True
    assert out["requestId"] == "REQ-AUDIT"
    assert out["audit"], "the canonical writer must have written an audit row"
    # The readback is the FRESH document's own projection, not an echo.
    stored = _stored_block(SEA_LOT)
    assert stored["incoterm_version"] == "2020"
    assert stored["incoterm_named_place"] == "Hai Phong Port"
    assert stored["load_model"] == "FCL"
    assert stored["service_scope"] == ["IMPORT_CUSTOMS", "DESTINATION_TRUCKING", "FINAL_DELIVERY"]
    assert stored["service_scope_confirmed"] is True
    assert out["persisted"]["executionProfile"] == stored
    readback = out["readback"]["executionProfile"]
    assert readback["incoterm"] == "CIF" and readback["state"] == ep.STATE_READY
    assert _profile(SEA_LOT)["insurance"]["actualStatus"] == "UNKNOWN"
    # The write bumped the document version exactly once.
    assert out["version"] == _doc(SEA_LOT)["version"]


def test_a_no_op_save_reports_the_stored_truth_instead_of_a_false_change(staging):
    payload = dict({"shipmentId": SEA_LOT}, **_valid_sea_profile())
    first = _dispatch("shipment_profile_save", payload)
    assert first["ok"], first["error"]
    version = _doc(SEA_LOT)["version"]
    second = _dispatch("shipment_profile_save", payload, seq=2)
    assert second["ok"] is True and second["noop"] is True
    assert second["error"] == "Không có thay đổi để lưu."
    assert _doc(SEA_LOT)["version"] == version, "a no-op must not bump the version"


def test_unknown_payload_keys_are_rejected_and_nothing_is_written_for_them(staging):
    out = _dispatch("shipment_profile_save", dict(
        {"shipmentId": SEA_LOT, "totally_unknown": "x"}, **_valid_sea_profile()))
    assert out["ok"], out["error"]
    assert out["rejected"] == ["totally_unknown"]
    assert "totally_unknown" not in json.dumps(_doc(SEA_LOT), default=str)


def test_write_refuses_an_invalid_load_model_family_for_the_mode(staging):
    out = _dispatch("shipment_profile_save", dict(
        {"shipmentId": SEA_LOT}, **_valid_sea_profile(loadModel="FTL")))
    assert out["ok"] is False
    assert any(i["code"] == ep.ISSUE_INVALID_LOAD_MODEL for i in out["issues"])
    assert _stored_block(SEA_LOT) == {}


def test_company_identity_is_untouched_by_this_slice():
    for path in ("core/shipment_execution_profile.py",
                 "component/src/components/ShipmentExecutionProfile.tsx"):
        text = (ROOT / path).read_text(encoding="utf-8")
        assert "Phú Anh" not in text
        assert "Trường Thành" in text


# ===========================================================================
# K. The generated client catalog cannot drift
# ===========================================================================

def test_generated_client_catalog_matches_the_python_authority():
    sys.path.insert(0, str(ROOT / "scripts"))
    import gen_execution_profile_catalog as generator  # noqa: PLC0415

    committed = (ROOT / "component" / "src" / "lib" / "executionProfileCatalog.ts").read_text(encoding="utf-8")
    assert generator.render() == committed, (
        "component/src/lib/executionProfileCatalog.ts drifted from "
        "core/shipment_execution_profile.py — regenerate it with "
        "python3 scripts/gen_execution_profile_catalog.py"
    )
    payload = json.loads(committed.split("= ", 1)[1].rsplit(" as const;", 1)[0])
    assert payload == ep.projection_options()


# ===========================================================================
# L. PR74 latency invariants
# ===========================================================================

_DB_OPS = ("find", "find_one", "count_documents", "aggregate", "distinct", "insert_one",
           "update_one", "replace_one", "find_one_and_update", "delete_one", "delete_many",
           "insert_many", "update_many", "find_one_and_replace", "bulk_write")


def _counting_db(db, counter):
    class _Collection:
        def __init__(self, real):
            self._real = real

        def __getattr__(self, name):
            real = getattr(self._real, name)
            if name not in _DB_OPS or not callable(real):
                return real

            def _wrapped(*args, **kwargs):
                counter["ops"] += 1
                counter["by_name"][name] = counter["by_name"].get(name, 0) + 1
                return real(*args, **kwargs)
            return _wrapped

    class _DB:
        def __init__(self, real):
            self._real = real

        def __getattr__(self, name):
            return _Collection(getattr(self._real, name))

    return _DB(db)


def test_profile_projection_issues_zero_database_reads(monkeypatch):
    """The profile is a PURE projection: no reader, no query, nothing cached."""

    calls = {"ops": 0, "by_name": {}}
    real_get_db = core_database.get_db
    monkeypatch.setattr(core_database, "get_db",
                        lambda: _counting_db(real_get_db(), calls))
    monkeypatch.setattr(core_database, "_UNSET_DB", None, raising=False)
    document = {"data": {"0.0": {"mode": "Sea", "incoterm": "CIF", "execution_profile": {
        "incoterm_version": "2020", "incoterm_named_place": "Hai Phong Port", "load_model": "FCL",
        "service_scope": ["IMPORT_CUSTOMS"], "service_scope_confirmed": True,
        "cargo_insurance": {"status": "UNKNOWN"}}}}}
    profile = ep.build_execution_profile(document)
    assert profile["state"] == ep.STATE_READY
    assert calls["ops"] == 0, f"the projection must not read the database: {calls}"


def test_the_execution_profile_is_not_a_second_view_model_build(staging, monkeypatch):
    """ONE intent → ONE handler → ONE fresh read → ONE view-model build."""

    from streamlit.components.v2.bidi_component.state import ComponentResult  # noqa: PLC0415

    from views import logi_shell, web_app
    import streamlit as st

    builds: list[dict] = []
    reruns: list[int] = []
    real_build = vm.build_view_model

    def _timed_build():
        model = real_build()
        builds.append(model)
        return model

    monkeypatch.setattr(vm, "build_view_model", _timed_build)
    monkeypatch.setattr(st, "rerun", lambda *a, **k: reruns.append(1))
    monkeypatch.setattr(logi_shell, "_renderer", lambda: (lambda **kw: ComponentResult({}, trigger)))
    monkeypatch.setattr(core_auth, "AUTH_REQUIRED", True)
    monkeypatch.setattr(st, "set_page_config", lambda *a, **k: None)

    trigger = {"shipment_profile_save": {
        "seq": 5, "event": "shipment_profile_save",
        "payload": dict({"shipmentId": SEA_LOT, "requestId": "REQ-LAT"}, **_valid_sea_profile()),
    }}
    # The component callback revalidates the session against the canonical user
    # store, so the replay runs as the seeded SUPPORT operator (role "support",
    # exactly like tests/test_logi_interaction_latency_finalize_02.py does).
    st.session_state["current_user"] = {"username": "thuhang", "role": "support",
                                        "user_id": "thuhang"}
    st.session_state[logi_shell.COMPONENT_KEY] = trigger
    st.session_state.pop(logi_shell.CALLBACK_DISPATCHED_FLAG, None)
    st.session_state[vm.SEQ_KEY] = 4

    logi_shell._on_component_event()
    web_app.main()

    outcomes = [row for row in (st.session_state.get(vm.LAST_WRITES_KEY) or [])
                if row.get("event") == "shipment_profile_save"]
    assert len(outcomes) == 1, "exactly one handler outcome per intent"
    assert outcomes[0]["ok"] is True, outcomes[0].get("error")
    assert len(builds) == 1, "ONE view-model build per intent"
    assert reruns == [], "no explicit second rerun"
    assert builds[0]["shipments"], "the fresh payload really carries the lots"
    # The fresh payload already shows the persisted profile — no second read.
    row = next(s for s in builds[0]["shipments"] if s["id"] == SEA_LOT)
    assert row["executionProfile"]["incoterm"] == "CIF"
    assert row["executionProfile"]["state"] == ep.STATE_READY


# ===========================================================================
# M. Create path — a blank Incoterm stays blank (never a fabricated EXW)
# ===========================================================================

def _create(sid: str, **transport) -> dict:
    payload = {
        "shipmentId": sid,
        "customerId": "CUST-ANPHAT",
        "customer": "An Phát JSC",
        "contractId": "",
        "currency": "VND",
        "requestId": f"REQ-{sid}",
        "transport": dict(transport),
    }
    return _dispatch("shipment_create", payload)


def _created_head(sid: str) -> dict:
    """The FRESH authoritative read of a just-created shipment."""

    return dict((_doc(sid).get("data") or {}).get("0.0") or {})


def test_create_without_a_contract_term_persists_a_blank_incoterm(staging):
    """UNKNOWN stays UNKNOWN: no implicit EXW may be written to MongoDB."""

    out = _create("LO-0491", mode="Truck", pol="Bằng Tường (Quảng Tây)")
    assert out["ok"], out["error"]

    head = _created_head("LO-0491")
    assert head["incoterm"] == "", f"the blank term must stay blank, got {head['incoterm']!r}"
    assert head["incoterm"] != "EXW", "EXW may never be fabricated at creation"
    assert head["mode"] == "Truck", "the stated mode is untouched"
    # …and the stored blank projects honestly as an unknown term.
    profile = _profile("LO-0491")
    assert profile["incoterm"] == "" and profile["incotermRawLabel"] == ""
    assert profile["state"] == ep.STATE_INCOMPLETE


def test_create_with_an_explicit_contract_term_persists_that_term(staging):
    out = _create("LO-0492", mode="Truck", incoterm="EXW", pol="Bằng Tường (Quảng Tây)")
    assert out["ok"], out["error"]
    head = _created_head("LO-0492")
    assert head["incoterm"] == "EXW", "a stated term is persisted verbatim"
    assert _profile("LO-0492")["incoterm"] == "EXW"


def test_create_with_a_complete_profile_writes_the_profile_block(staging):
    out = _dispatch("shipment_create", {
        "shipmentId": "LO-0493", "customerId": "CUST-ANPHAT", "customer": "An Phát JSC",
        "contractId": "", "currency": "VND", "requestId": "REQ-LO-0493",
        "transport": {"mode": "Sea", "incoterm": "CIF", "incotermVersion": "2020",
                      "namedPlace": "Hai Phong Port", "loadModel": "LCL",
                      "serviceScope": ["IMPORT_CUSTOMS"], "serviceScopeConfirmed": True,
                      "cargoInsurance": {"status": "YES", "insurerName": "PJICO",
                                         "policyNo": "POL-0493"}},
    })
    assert out["ok"], out["error"]
    head = _created_head("LO-0493")
    assert head["incoterm"] == "CIF" and head["mode"] == "Sea"
    assert head["execution_profile"]["incoterm_version"] == "2020"
    assert head["execution_profile"]["incoterm_named_place"] == "Hai Phong Port"
    assert head["execution_profile"]["cargo_insurance"]["status"] == "YES"
    assert _profile("LO-0493")["state"] in {ep.STATE_READY, ep.STATE_INCOMPLETE}


def test_create_with_a_half_stated_profile_still_creates_the_lot(staging):
    """A fact not stated YET is not a conflict — the lot is still created.

    The profile block is simply not written; nothing is guessed for the
    operator (and the missing Incoterm never becomes EXW on the way through).
    """

    out = _dispatch("shipment_create", {
        "shipmentId": "LO-0494", "customerId": "CUST-ANPHAT", "customer": "An Phát JSC",
        "contractId": "", "currency": "VND", "requestId": "REQ-LO-0494",
        "transport": {"mode": "Sea", "incotermVersion": "2020", "loadModel": "LCL"},
    })
    assert out["ok"], out["error"]
    head = _created_head("LO-0494")
    assert head["incoterm"] == "", "the profile's own term field is never invented"
    assert "execution_profile" not in head, "a half-stated profile is never half-written"
    assert _profile("LO-0494")["state"] == ep.STATE_INCOMPLETE


def test_create_refuses_a_structural_conflict_even_without_a_place(staging):
    out = _dispatch("shipment_create", {
        "shipmentId": "LO-0495", "customerId": "CUST-ANPHAT", "customer": "An Phát JSC",
        "contractId": "", "currency": "VND", "requestId": "REQ-LO-0495",
        "transport": {"mode": "Truck", "incoterm": "FOB", "incotermVersion": "2020",
                      "namedPlace": "Shenzhen", "loadModel": "LTL",
                      "serviceScope": ["IMPORT_CUSTOMS"], "serviceScopeConfirmed": True,
                      "cargoInsurance": {"status": "NO"}},
    })
    assert out["ok"] is False
    assert any(i["code"] == ep.ISSUE_INVALID_COMBINATION for i in out["issues"])
    assert vm.read_shipment("LO-0495") is None, "a refused create writes nothing"


def test_the_create_path_keeps_no_implicit_incoterm_default():
    """The guard for the exact defect: no ``or "EXW"`` may come back."""

    source = (ROOT / "views" / "logi_view_model.py").read_text(encoding="utf-8")
    handler = source[source.index("def _handle_shipment_create"):]
    handler = handler[:handler.index("\ndef ", 10)]
    assert 'or "EXW"' not in handler, "an implicit EXW default must never return to create"
    assert 'transport.get("incoterm")' in handler
    # The legacy warehouse repair keeps its own semantics (pinned elsewhere);
    # what matters is that the CREATED document states the term explicitly, so
    # the repair can never fill in a blank the operator really left blank.
    assert '"incoterm": rd.text(transport.get("incoterm"))' in handler


def test_the_state_banner_and_the_next_action_always_agree(staging):
    """CONFIG_CHECK is a banner AND a next action — never one without the other."""

    documents = {
        # A conflict the operator really stated.
        "fob_road": {"data": {"0.0": {"mode": "Truck", "incoterm": "FOB", "execution_profile": {
            "incoterm_version": "2020", "incoterm_named_place": "Shenzhen"}}}},
        # A term nobody can recognize.
        "typo": {"data": {"0.0": {"mode": "Sea", "incoterm": "C1F", "execution_profile": {
            "incoterm_version": "2020", "incoterm_named_place": "Hai Phong Port"}}}},
        # Blank / legacy / partial — open questions, never conflicts.
        "blank": {"data": {"0.0": {"mode": "Sea", "incoterm": ""}}},
        "legacy": {"data": {"0.0": {"mode": "Truck", "incoterm": "DAP"}}},
        "no_head": {"data": {"0.0": {}}},
    }
    for label, document in documents.items():
        profile = _profile_of(document)
        conflicted = profile["state"] == ep.STATE_CONFIG_CHECK
        assert conflicted == (profile["nextAction"]["code"] == "CONFIG_CHECK"), label
        if label in {"blank", "legacy", "no_head"}:
            assert profile["state"] == ep.STATE_INCOMPLETE, label
            assert profile["incotermRawLabel"] == "", label
    # An unrecognized term is preserved verbatim as evidence — never rewritten.
    assert _profile_of(documents["typo"])["incotermRawLabel"] == "C1F"
