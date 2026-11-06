"""GOAL #199 T1 — SEA FCL equipment completeness is per recorded container.

A declared type for one box never proves the other boxes' equipment types.
No customs/finance writes, no Streamlit, no invented container quantities.
"""
from copy import deepcopy

from core import shipment_execution_profile as ep


def _sea_fcl_lot(types):
    units = [
        {
            "id": f"box-{i + 1}", "kind": "container",
            "number": f"CONT{i + 1:04d}", "type_size": kind, "seal_no": "",
        }
        for i, kind in enumerate(types)
    ]
    return {
        "data": {
            "0.0": {
                "mode": "Sea", "incoterm": "FOB",
                "execution_profile": {
                    "incoterm_version": "2020",
                    "incoterm_named_place": "Cai Mep Port",
                    "load_model": "FCL",
                    "service_scope": ["MAIN_CARRIAGE"],
                    "service_scope_confirmed": True,
                    "cargo_insurance": {"status": "NO"},
                },
            },
            "1.2": {
                "transport_legs": [{
                    "id": "sea-main", "sequence": 1, "mode": "Sea",
                    "origin": "Cai Mep", "destination": "Hamburg",
                    "carrier": "Ocean Carrier",
                    "booking_no": "BKG-101", "mbl": "MBL-101", "hbl": "",
                    "vessel": "Vessel A", "voyage": "VOY-1",
                    "etd": "", "eta": "", "atd": "", "ata": "",
                    "units": units,
                }],
            },
        },
    }


def _stage(profile, code):
    return next(stage for stage in profile["stages"] if stage["code"] == code)


def test_first_typed_container_does_not_complete_three_container_fcl():
    shipment = _sea_fcl_lot(["40HC", "", ""])
    before = deepcopy(shipment)
    projected = ep.build_execution_profile(shipment)
    assert shipment == before, "read-only projection must never write shipment facts"
    equipment = projected["equipment"]
    assert equipment["count"] == 3
    assert equipment["presets"] == [{"code": "40HC", "count": 1}]
    assert equipment["missingTypeCount"] == 2
    assert equipment["known"] is False
    assert _stage(projected, "SEA_EQUIPMENT")["done"] is False
    assert "2 container" in _stage(projected, "SEA_EQUIPMENT")["missing"]
    assert projected["nextAction"]["code"] == "SEA_EQUIPMENT"
    assert "2 container" in projected["nextAction"]["label"]
    assert _stage(projected, "SEA_DOCUMENTS")["done"] is True, (
        "equipment gap must not erase already evidenced booking and BL"
    )


def test_one_remaining_unknown_unit_is_not_silently_completed():
    projected = ep.build_execution_profile(_sea_fcl_lot(["40HC", "", "20GP"]))
    equipment = projected["equipment"]
    assert equipment["count"] == 3
    assert equipment["missingTypeCount"] == 1
    assert equipment["known"] is False
    assert _stage(projected, "SEA_EQUIPMENT")["done"] is False
    assert projected["nextAction"]["code"] == "SEA_EQUIPMENT"
    assert "1 container" in projected["nextAction"]["label"]


def test_all_recorded_fcl_units_typed_allows_move_to_next_work():
    projected = ep.build_execution_profile(_sea_fcl_lot(["40HC", "40HC", "20GP"]))
    equipment = projected["equipment"]
    assert equipment["known"] is True
    assert equipment["missingTypeCount"] == 0
    assert equipment["presets"] == [{"code": "20GP", "count": 1}, {"code": "40HC", "count": 2}]
    assert _stage(projected, "SEA_EQUIPMENT")["done"] is True
    assert _stage(projected, "SEA_EQUIPMENT")["missing"] == ""
    assert projected["nextAction"]["code"] != "SEA_EQUIPMENT"
    assert "1 × 20GP, 2 × 40HC" in " ".join(projected["summaryLines"])


def test_no_recorded_fcl_units_does_not_invent_a_container():
    projected = ep.build_execution_profile(_sea_fcl_lot([]))
    equipment = projected["equipment"]
    assert equipment["count"] == 0
    assert equipment["missingTypeCount"] == 0
    assert equipment["known"] is False
    assert _stage(projected, "SEA_EQUIPMENT")["done"] is False
    assert "Bổ sung loại container" in projected["nextAction"]["label"]


def test_legacy_number_without_type_stays_unknown():
    shipment = _sea_fcl_lot([])
    shipment["data"]["1.2"] = {
        "container_no": "MSKU1234567",
        "carrier": "Ocean Carrier", "booking_no": "BKG-101", "mbl": "MBL-101",
    }
    projected = ep.build_execution_profile(shipment)
    assert projected["persisted"]["structuredTransport"] is False
    assert projected["equipment"]["count"] == 1
    assert projected["equipment"]["missingTypeCount"] == 1
    assert projected["equipment"]["known"] is False
    assert projected["nextAction"]["code"] == "SEA_EQUIPMENT"


def test_container_number_or_seal_not_required_for_equipment_type_configuration():
    shipment = _sea_fcl_lot(["40HC"])
    shipment["data"]["1.2"]["transport_legs"][0]["units"][0]["number"] = ""
    projected = ep.build_execution_profile(shipment)
    assert projected["equipment"]["known"] is True
    assert _stage(projected, "SEA_EQUIPMENT")["done"] is True
    assert projected["persisted"]["containers"][0]["number"] == "", (
        "equipment plan readiness is not proof of physical container pickup"
    )
