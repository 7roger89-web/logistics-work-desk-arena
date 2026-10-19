"""Goal #199 — evidence for MAWB/HAWB + flight, not sea MBL/HBL.

Pure read-model tests; no Streamlit, MongoDB, writes or live logistics data.
"""
import pytest

from core import shipment_execution_profile as ep


def _air_shipment(transport, *, owned=True, structured=False):
    profile = {
        "incoterm_version": "2020",
        "incoterm_named_place": "Noi Bai cargo terminal",
        "load_model": "DIRECT",
        "service_scope": ["MAIN_CARRIAGE"] if owned else [],
        "service_scope_confirmed": True,
        "cargo_insurance": {"status": "UNKNOWN"},
    }
    if structured:
        main = {
            "id": "air-main-01", "sequence": 1, "mode": "Air",
            "origin": "HAN", "destination": "FRA",
            "carrier": "", "etd": "", "eta": "", "atd": "", "ata": "",
            "mawb": "", "hawb": "", "flight_no": "", "units": [],
            **transport,
        }
        transport = {"transport_legs": [main]}
    return {
        "data": {
            "0.0": {"mode": "Air", "incoterm": "CPT", "execution_profile": profile},
            "1.2": transport,
        }
    }


def _air_stage(shipment):
    profile = ep.build_execution_profile(shipment)
    codes = {stage["code"] for stage in profile["stages"]}
    assert "AIR_DOCUMENTS" in codes
    assert "SEA_DOCUMENTS" not in codes
    assert "SEA_EQUIPMENT" not in codes
    assert "SEA_CONSOLIDATION" not in codes
    return next(stage for stage in profile["stages"] if stage["code"] == "AIR_DOCUMENTS")


@pytest.mark.parametrize("facts,done,missing", [
    ({"carrier": "VN Cargo", "mbl": "SEA-BL-NOT-AIR", "hbl": "SEA-HBL-NOT-AIR"},
     False, ("MAWB/HAWB", "số chuyến bay")),
    ({"carrier": "VN Cargo", "mawb": "180-11111111"},
     False, ("số chuyến bay",)),
    ({"carrier": "VN Cargo", "flight_no": "VN335"},
     False, ("MAWB/HAWB",)),
    ({"hawb": "HAWB-123", "flight_no": "VN335"},
     True, ()),
    ({"mawb": "180-11111111", "flight_no": "VN335"},
     True, ()),
])
def test_owned_air_document_stage_requires_airway_bill_and_flight(facts, done, missing):
    shipment = _air_shipment(facts)
    projected = ep.persisted_facts(shipment)
    assert projected["mawb"] == facts.get("mawb", "")
    assert projected["hawb"] == facts.get("hawb", "")
    assert projected["flightNo"] == facts.get("flight_no", "")
    stage = _air_stage(shipment)
    assert stage["done"] is done
    if done:
        assert stage["missing"] == ""
    else:
        assert all(label in stage["missing"] for label in missing), stage


def test_air_canonical_transport_leg_is_source_of_airway_bill_and_flight():
    shipment = _air_shipment(
        {"mawb": "180-22222222", "flight_no": "VN335", "carrier": "VN Cargo"},
        structured=True,
    )
    facts = ep.persisted_facts(shipment)
    assert facts["structuredTransport"] is True
    assert facts["mawb"] == "180-22222222"
    assert facts["flightNo"] == "VN335"
    assert _air_stage(shipment)["done"] is True


def test_air_documents_remain_visible_as_read_only_evidence_when_main_not_owned():
    # Service scope is never inferred from Incoterms or an observed air waybill.
    shipment = _air_shipment(
        {"hawb": "HAWB-321", "flight_no": "VN335"},
        owned=False,
    )
    profile = ep.build_execution_profile(shipment)
    assert "MAIN_CARRIAGE" not in profile["serviceScope"]
    stage = _air_stage(shipment)
    assert stage["reason"] == ep.REASON_PERSISTED_FACT_DEPENDENCY
    assert stage["done"] is True


@pytest.mark.parametrize("only_partial_evidence", [
    {"carrier": "VN Cargo"},
    {"carrier": "VN Cargo", "hawb": "HAWB-321"},
    {"carrier": "VN Cargo", "flight_no": "VN335"},
])
def test_external_carriage_keeps_unknown_air_documents_incomplete(only_partial_evidence):
    # We cannot assign the counterparty an action; equally, we cannot claim
    # that an AWB and flight both exist when only the carrier is known.
    stage = _air_stage(_air_shipment(only_partial_evidence, owned=False))
    assert stage["reason"] == ep.REASON_PERSISTED_FACT_DEPENDENCY
    assert stage["done"] is False
    assert stage["missing"] == ""  # no Trường Thành owned task is fabricated


def test_air_shipment_does_not_generate_sea_stages():
    """AIR shipments must never produce SEA_DOCUMENTS or SEA_EQUIPMENT stages."""
    # Case: owned AIR with carrier + MBL (sea docs only) → must NOT complete
    shipment = _air_shipment({"carrier": "VN Cargo", "mbl": "SEA-MBL", "hbl": "SEA-HBL"})
    stage = _air_stage(shipment)
    assert stage["done"] is False
    # Verify no SEA stages leaked in
    profile = ep.build_execution_profile(shipment)
    stage_codes = [s["code"] for s in profile["stages"]]
    assert "SEA_DOCUMENTS" not in stage_codes
    assert "SEA_EQUIPMENT" not in stage_codes
    assert "SEA_CONSOLIDATION" not in stage_codes


def test_legacy_air_shipment_reads_air_facts_from_data_1_2():
    """Legacy scalar data.1.2 fields must project correctly as AIR facts."""
    # Legacy AIR: data.1.2 has mawb/flight_no as scalar fields, not structured legs
    shipment = {
        "data": {
            "0.0": {"mode": "Air", "incoterm": "CPT", "execution_profile": {
                "incoterm_version": "2020",
                "incoterm_named_place": "Noi Bai",
                "load_model": "DIRECT",
                "service_scope": ["MAIN_CARRIAGE"],
                "service_scope_confirmed": True,
                "cargo_insurance": {"status": "UNKNOWN"},
            }},
            "1.2": {
                "carrier": "Vietnam Airlines Cargo",
                "mawb": "180-99998888",
                "hawb": "",
                "flight_no": "VN1234",
                "pol": "HAN",
                "pod": "NRT",
            },
        }
    }
    facts = ep.persisted_facts(shipment)
    # Legacy reader must pick up mawb and flight_no from the legacy leg
    assert facts["mawb"] == "180-99998888"
    assert facts["flightNo"] == "VN1234"
    assert facts["hawb"] == ""
    # AIR_DOCUMENTS should be complete: has MAWB + flight
    stage = _air_stage(shipment)
    assert stage["done"] is True


def test_legacy_air_shipment_missing_flight_means_incomplete():
    """Legacy AIR data without flight number → AIR_DOCUMENTS must be incomplete."""
    shipment = {
        "data": {
            "0.0": {"mode": "Air", "incoterm": "CPT", "execution_profile": {
                "incoterm_version": "2020",
                "incoterm_named_place": "Noi Bai",
                "load_model": "DIRECT",
                "service_scope": ["MAIN_CARRIAGE"],
                "service_scope_confirmed": True,
                "cargo_insurance": {"status": "UNKNOWN"},
            }},
            "1.2": {
                "carrier": "Vietnam Airlines Cargo",
                "mawb": "180-77776666",
                "flight_no": "",
                "pol": "HAN",
                "pod": "NRT",
            },
        }
    }
    facts = ep.persisted_facts(shipment)
    assert facts["mawb"] == "180-77776666"
    assert facts["flightNo"] == ""
    stage = _air_stage(shipment)
    assert stage["done"] is False
    assert "số chuyến bay" in stage["missing"]
