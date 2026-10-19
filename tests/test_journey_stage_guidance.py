"""SEA Journey guidance regression: mode/scope/variant and customs truth gates.

Pure tests do not use production DB/network/UI. Writer coercion test imports the
existing viewmodel as in test_logi_gnt_canonical_fields_01.py.
"""
from __future__ import annotations

import pytest

from core.shipment_journey import build_journey
from core.stage_guidance import STAGE_GUIDANCE, guidance_for_node


FIELDS = {"why", "what_to_do", "who", "when", "needs", "done_when", "impact"}
SEA_FCL_IDS = {
    "booking", "pickup", "customs-export", "si-vgm", "gate-in", "etd",
    "on-board", "transit", "arrival", "customs-import", "delivery",
}


def _build(mode: str = "SEA", load: str = "FCL", *, owned: bool = True,
           customs_status=None, delivered: bool = False, sea_facts=None):
    codes = {
        "MAIN_CARRIAGE", "SEA_DOCUMENTS", "AIR_DOCUMENTS", "ORIGIN_HANDOFF",
        "ORIGIN_PICKUP", "EXPORT_HANDLING", "IMPORT_CUSTOMS", "DELIVERY",
    }
    scope = {
        "MAIN_CARRIAGE", "ORIGIN_PICKUP", "EXPORT_HANDLING",
        "ORIGIN_TERMINAL_OR_BORDER", "IMPORT_CUSTOMS", "DESTINATION_TRUCKING",
    } if owned else set()
    profile = {
        "mode": mode, "loadModel": load,
        "serviceScopeConfirmed": owned, "serviceScope": sorted(scope),
        "stages": [{"code": k, "label": k, "reason": "SERVICE_SCOPE"} for k in sorted(codes)],
    }
    shipment = {"id": "STAGE-GUIDANCE-TEST", "data": {
        "1.2": {"sea_export": dict(sea_facts or {}), "air_facts": {}, "road_facts": {}},
        "2.4": {"tk_no": "101", "customs_status": customs_status},
        "2.7": {"is_delivered": delivered},
    }}
    operational = {
        "main_leg": {"booking_no": "BK123", "etd": "2026-10-01",
                     "eta": "2026-10-05", "atd": "", "ata": ""},
        "pickup_leg": {},
    }
    return {n["id"]: n for n in build_journey(
        shipment, profile=profile, operational=operational,
        primary={}, dashboard={}, attachments=[],
    )["nodes"]}


def test_catalog_contains_12_real_sea_node_ids_and_seven_short_fields():
    assert set(STAGE_GUIDANCE) == SEA_FCL_IDS | {"cfs-receipt"}
    for node_id, row in STAGE_GUIDANCE.items():
        assert set(row) == FIELDS, node_id
        assert all(isinstance(v, str) and v.strip() and len(v) <= 120 for v in row.values()), node_id
    lcl = guidance_for_node("si-vgm", load_model="LCL", owned=True)
    assert lcl is not None
    assert set(lcl) == FIELDS
    assert all(len(v) <= 120 for v in lcl.values())


@pytest.mark.parametrize("mode,load,expected,excluded", [
    ("SEA", "FCL", SEA_FCL_IDS, {"cfs-receipt"}),
    ("SEA", "LCL", (SEA_FCL_IDS - {"gate-in"}) | {"cfs-receipt"}, {"gate-in"}),
])
def test_only_real_sea_nodes_get_guidance(mode, load, expected, excluded):
    nodes = _build(mode, load)
    assert expected <= set(nodes)
    assert not (excluded & set(nodes))
    for node_id in expected:
        assert set(nodes[node_id]["guidance"]) == FIELDS
        assert nodes[node_id]["guidance"]["what_to_do"]
        assert nodes[node_id]["guidance"]["done_when"]


@pytest.mark.parametrize("mode", ["AIR", "ROAD", "RAIL"])
def test_non_sea_nodes_never_receive_sea_guidance_even_with_shared_ids(mode):
    nodes = _build(mode)
    for node in nodes.values():
        assert "guidance" not in node, (mode, node["id"])
    assert {"pickup", "customs-export", "customs-import", "delivery"} <= set(nodes)


def test_fcl_lcl_si_text_and_cfs_gate_separated():
    fcl = _build("SEA", "FCL")["si-vgm"]["guidance"]
    lcl = _build("SEA", "LCL")["si-vgm"]["guidance"]
    assert "VGM" in fcl["what_to_do"] and "VGM" in fcl["done_when"]
    assert "VGM" not in lcl["what_to_do"]
    assert "không yêu cầu VGM" in lcl["done_when"]
    assert "gate_in_at" in _build("SEA", "FCL")["gate-in"]["guidance"]["done_when"]
    assert "consolidated_at" in _build("SEA", "LCL")["cfs-receipt"]["guidance"]["done_when"]


def test_unowned_guidance_is_follow_up_not_fake_assignment():
    nodes = _build("SEA", "FCL", owned=False)
    booking = nodes["booking"]
    assert booking["owned"] is False
    assert "chưa xác nhận" in booking["guidance"]["what_to_do"]
    assert "chưa xác nhận Trường Thành" in booking["guidance"]["who"]
    assert booking["completed"] is False


def test_guidance_is_copy_and_unknown_id_keeps_legacy_payload():
    assert guidance_for_node("air-booking", owned=True) is None
    a = guidance_for_node("booking", owned=True)
    b = guidance_for_node("booking", owned=True)
    assert a is not None and b is not None and a is not b
    a["done_when"] = "tampered"
    assert b["done_when"] == STAGE_GUIDANCE["booking"]["done_when"]


@pytest.mark.parametrize("raw", [None, False, 0, 1, "", "false", "True", "REGISTERED", "SUBMITTED"])
def test_customs_import_not_completed_without_canonical_boolean_true(raw):
    node = _build(customs_status=raw)["customs-import"]
    assert node["completed"] is False, raw
    assert node["state"] != "COMPLETED"


def test_explicit_customs_clearance_true_and_delivery_truth_are_independent():
    nodes = _build(customs_status=True, delivered=True)
    assert nodes["customs-import"]["completed"] is True
    assert nodes["delivery"]["completed"] is True
    assert "POD/trả rỗng" in nodes["delivery"]["guidance"]["what_to_do"]
    assert "POD/trả rỗng" in nodes["delivery"]["guidance"]["done_when"]
    assert nodes["booking"]["completed"] is False


def test_existing_writer_rejects_free_text_customs_status_without_marking_done():
    from views import logi_view_model as vm
    for raw in (False, "false", "0", "", None, 0):
        assert vm._coerce("customs_status", raw) is False
    for raw in (True, "true", "1", 1):
        assert vm._coerce("customs_status", raw) is True
    for raw in ("REGISTERED", "SUBMITTED", "PENDING", "Đã gửi"):
        with pytest.raises(ValueError):
            vm._coerce("customs_status", raw)
