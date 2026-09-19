#!/usr/bin/env python3
"""Generate the LOGI_SHIPMENT_EXECUTION_PROFILE_01 DOM-acceptance fixture.

Same contract as the other fixture generators in this repo: boot the ISOLATED
mongomock staging transport (never production), drive every state through the
REAL bounded dispatcher (and therefore through the REAL canonical writers +
audit + fresh read), and dump the resulting ``build_view_model()`` payloads.

States:

  ``before``          LO-0306 exactly as seeded: ``mode=Truck`` + ``incoterm=DAP``
                      and NOTHING else. The projection must call this
                      ``PROFILE_INCOMPLETE`` (missing Incoterms version, named
                      place, service scope, insurance) and must not invent any
                      of them.
  ``seaMode``         LO-0307 switched to Sea through the EXISTING
                      ``shipment_field_save`` + a real Sea leg with TWO
                      containers saved through ``shipment_transport_save``.
  ``cfrAlias``        ``shipment_profile_save`` with the contract wording
                      ``CNF``: the stored canonical code must be ``CFR`` while
                      the raw label survives as evidence.
  ``seaFclSaved``     the CIF 2020 / Hai Phong Port / FCL profile (equipment read
                      from the existing container units; CIF obligation present,
                      actual insurance still UNKNOWN — the two facts stay
                      distinct).
  ``insuranceNo``     a second save stating the ACTUAL insurance as "NO": every
                      stale policy detail is cleared.
  ``roadLtlSaved``    FCA 2020 / Pingxiang Warehouse / ROAD + LTL: no truck
                      profile is demanded, the LTL note is rendered.
  ``roadFtlTruck``    the same lot switched to FTL and given ``17.5m`` through the
                      EXISTING ``shipment_field_save {pickup_truck_type}`` — proof
                      that the truck profile reuses the canonical field.
  ``configCheck``     LO-0306 given the historical impossible pair FOB + ROAD
                      through the existing scalar field save (a real legacy desk
                      edit): the profile must render CẤU HÌNH CẦN KIỂM TRA and
                      must NOT mutate the stored document.
  ``viewerRefused``   a VIEWER attempt at the profile save: refused by RBAC with
                      the data genuinely unchanged.

Run:  python3 scripts/gen_shipment_execution_profile_fixture.py
Out:  tests/component/fixtures/view_model_execution_profile.json
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUT = ROOT / "tests" / "component" / "fixtures" / "view_model_execution_profile.json"

LEGACY_LOT = "LO-0306"
SEA_LOT = "LO-0307"
ROAD_LOT = "LO-0308"


def main() -> None:
    import streamlit as st

    from views import logi_sandbox
    from views import logi_view_model as vm

    logi_sandbox.reset_backend()
    transport = logi_sandbox.ensure_backend()
    assert transport == logi_sandbox.SANDBOX_TRANSPORT, "fixture must not touch production"
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)
    st.session_state.pop(vm.LAST_WRITES_KEY, None)

    seq = {"n": 0}

    def dispatch(name: str, payload: dict) -> dict:
        seq["n"] += 1
        result = {name: {"seq": seq["n"], "event": name, "payload": payload}}
        outcomes = vm.consume_phase_b_triggers({"seq": 0}, result)
        assert len(outcomes) == 1, (name, outcomes)
        return outcomes[0]

    def state(_name: str, outcomes: list[dict] | None = None) -> dict:
        st.session_state[vm.LAST_WRITES_KEY] = list(outcomes or [])
        return vm.build_view_model()

    before = state("before")

    # --- LO-0307: an honest Sea / FCL lot, written through existing events ----
    mode_out = dispatch("shipment_field_save", {"shipmentId": SEA_LOT, "fields": {"mode": "Sea"}})
    assert mode_out["ok"], mode_out["error"]
    legs_out = dispatch("shipment_transport_save", {
        "shipmentId": SEA_LOT,
        "transportLegs": [{
            "id": "leg-sea-1", "sequence": 1, "mode": "Sea",
            "origin": "Shenzhen", "destination": "Hải Phòng",
            "carrier": "Maersk", "etd": "2026-09-05", "eta": "2026-09-12",
            "atd": "", "ata": "",
            "booking_no": "BKG-0307", "mbl": "MBL-0307", "hbl": "HBL-0307",
            "vessel": "MAERSK HANOI", "voyage": "512W",
            "mawb": "", "hawb": "", "flight_no": "",
            "units": [
                {"id": "unit-c1", "kind": "container", "number": "MSKU1234567",
                 "type_size": "40HC", "seal_no": "SEAL-01", "driver_name": "", "driver_phone": ""},
                {"id": "unit-c2", "kind": "container", "number": "MSKU7654321",
                 "type_size": "20GP", "seal_no": "SEAL-02", "driver_name": "", "driver_phone": ""},
            ],
        }],
    })
    assert legs_out["ok"], legs_out["error"]
    sea_mode = state("seaMode", [mode_out, legs_out])

    # --- the contract wrote CNF: canonical CFR + preserved raw wording --------
    alias_out = dispatch("shipment_profile_save", {
        "shipmentId": SEA_LOT, "requestId": "REQ-PROFILE-CNF",
        "mode": "Sea", "incoterm": "CNF", "incotermVersion": "2020",
        "namedPlace": "Shenzhen", "loadModel": "FCL",
        "serviceScope": ["MAIN_CARRIAGE", "IMPORT_CUSTOMS", "DESTINATION_TRUCKING", "FINAL_DELIVERY"],
        "serviceScopeConfirmed": True,
        "cargoInsurance": {"status": "UNKNOWN"},
    })
    assert alias_out["ok"], alias_out["error"]
    cfr_alias = state("cfrAlias", [alias_out])

    # --- the real CIF 2020 / FCL profile -------------------------------------
    sea_out = dispatch("shipment_profile_save", {
        "shipmentId": SEA_LOT, "requestId": "REQ-PROFILE-SEA",
        "mode": "Sea", "incoterm": "CIF", "incotermVersion": "2020",
        "namedPlace": "Hai Phong Port", "loadModel": "FCL",
        "serviceScope": ["IMPORT_CUSTOMS", "DESTINATION_TRUCKING", "FINAL_DELIVERY"],
        "serviceScopeConfirmed": True,
        "cargoInsurance": {"status": "UNKNOWN"},
    })
    assert sea_out["ok"], sea_out["error"]
    sea_fcl_saved = state("seaFclSaved", [sea_out])

    # --- actual insurance stated NO: stale policy details must be cleared -----
    ins_out = dispatch("shipment_profile_save", {
        "shipmentId": SEA_LOT, "requestId": "REQ-PROFILE-INS",
        "cargoInsurance": {
            "status": "NO",
            "arrangedBy": "Trường Thành", "insurerName": "PJICO",
            "policyNo": "POLICY-OLD", "coverageNote": "Nhóm C",
        },
    })
    assert ins_out["ok"], ins_out["error"]
    insurance_no = state("insuranceNo", [ins_out])

    # --- ROAD + LTL: no dedicated truck is required ---------------------------
    ltl_out = dispatch("shipment_profile_save", {
        "shipmentId": ROAD_LOT, "requestId": "REQ-PROFILE-LTL",
        "mode": "Truck", "incoterm": "FCA", "incotermVersion": "2020",
        "namedPlace": "Pingxiang Warehouse", "loadModel": "LTL",
        "serviceScope": ["ORIGIN_TERMINAL_OR_BORDER", "CROSS_BORDER_COORDINATION",
                         "IMPORT_CUSTOMS", "FINAL_DELIVERY"],
        "serviceScopeConfirmed": True,
        "cargoInsurance": {"status": "NO"},
    })
    assert ltl_out["ok"], ltl_out["error"]
    road_ltl_saved = state("roadLtlSaved", [ltl_out])

    ftl_out = dispatch("shipment_profile_save", {
        "shipmentId": ROAD_LOT, "requestId": "REQ-PROFILE-FTL",
        "loadModel": "FTL",
    })
    assert ftl_out["ok"], ftl_out["error"]
    truck_out = dispatch("shipment_field_save",
                         {"shipmentId": ROAD_LOT, "fields": {"pickup_truck_type": "17.5m"}})
    assert truck_out["ok"], truck_out["error"]
    road_ftl_truck = state("roadFtlTruck", [ftl_out, truck_out])

    # --- a real legacy edit that produced an impossible pair ------------------
    fob_out = dispatch("shipment_field_save", {"shipmentId": LEGACY_LOT, "fields": {"incoterm": "FOB"}})
    assert fob_out["ok"], fob_out["error"]
    config_check = state("configCheck", [fob_out])

    # --- RBAC refusal: a VIEWER may not write the profile ---------------------
    st.session_state["current_user"] = {"username": "viewer.profile", "role": "VIEWER",
                                        "user_id": "U-VIEWER"}
    refused = dispatch("shipment_profile_save", {
        "shipmentId": LEGACY_LOT, "requestId": "REQ-PROFILE-VIEWER",
        "mode": "Sea", "incoterm": "CIF", "incotermVersion": "2020",
        "namedPlace": "Hai Phong Port", "loadModel": "FCL", "serviceScopeConfirmed": True,
        "cargoInsurance": {"status": "YES"},
    })
    assert not refused["ok"], refused
    viewer_refused = state("viewerRefused", [refused])
    st.session_state["current_user"] = dict(logi_sandbox.STAGING_ACTOR)

    # --- an impossible NEW configuration is refused, not repaired -------------
    invalid = dispatch("shipment_profile_save", {
        "shipmentId": SEA_LOT, "requestId": "REQ-PROFILE-INVALID",
        "mode": "Truck", "incoterm": "CIF", "incotermVersion": "2020",
        "namedPlace": "Hai Phong Port", "loadModel": "FTL", "serviceScopeConfirmed": True,
        "cargoInsurance": {"status": "NO"},
    })
    assert not invalid["ok"], invalid
    invalid_refused = state("invalidRefused", [invalid])

    st.session_state.pop(vm.LAST_WRITES_KEY, None)

    def shipment_row(model: dict, sid: str) -> dict:
        return next((row for row in model["shipments"] if row["id"] == sid), {})

    payload = {
        "generatedFrom": "scripts/gen_shipment_execution_profile_fixture.py — isolated mongomock staging",
        "legacyLot": LEGACY_LOT,
        "seaLot": SEA_LOT,
        "roadLot": ROAD_LOT,
        "before": before,
        "seaMode": sea_mode,
        "cfrAlias": cfr_alias,
        "seaFclSaved": sea_fcl_saved,
        "insuranceNo": insurance_no,
        "roadLtlSaved": road_ltl_saved,
        "roadFtlTruck": road_ftl_truck,
        "configCheck": config_check,
        "viewerRefused": viewer_refused,
        "invalidRefused": invalid_refused,
        "outcomes": {
            "cfrAlias": alias_out, "seaFclSaved": sea_out, "insuranceNo": ins_out,
            "roadLtlSaved": ltl_out, "roadFtlTruck": truck_out,
            "viewerRefused": refused, "invalidRefused": invalid,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    def report(name: str, model: dict, sid: str) -> None:
        profile = shipment_row(model, sid).get("executionProfile") or {}
        print(f"{name:14s} {sid} state={profile.get('state')} "
              f"incoterm={profile.get('incoterm')}/{profile.get('incotermVersion')} "
              f"mode={profile.get('mode')} load={profile.get('loadModel')} "
              f"next={((profile.get('nextAction') or {}).get('label') or '')[:48]}")

    for name, model, sid in (
        ("before", before, LEGACY_LOT),
        ("seaMode", sea_mode, SEA_LOT),
        ("cfrAlias", cfr_alias, SEA_LOT),
        ("seaFclSaved", sea_fcl_saved, SEA_LOT),
        ("insuranceNo", insurance_no, SEA_LOT),
        ("roadLtlSaved", road_ltl_saved, ROAD_LOT),
        ("roadFtlTruck", road_ftl_truck, ROAD_LOT),
        ("configCheck", config_check, LEGACY_LOT),
        ("viewerRefused", viewer_refused, LEGACY_LOT),
        ("invalidRefused", invalid_refused, SEA_LOT),
    ):
        report(name, model, sid)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
