"""Acceptance evidence for LOGI_SHIPMENT_OPERATIONAL_DATA_V1.

All writes run against the existing isolated mongomock staging transport and
through the production dispatcher/RBAC/save_shipment_atomic/audit/readback
path.  No production Mongo URI or production data is used.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from core.shipment_operations import (
    compatibility_facts,
    normalize_cargo_summary,
    normalize_transport_legs,
    transport_legs_for_read,
)
from views import logi_real_data as rd
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

    def make(name: str, payload: dict) -> dict:
        state["n"] += 1
        return {name: {"seq": state["n"], "event": name, "payload": payload}}

    return make


def dispatch(seq_fn, name: str, payload: dict) -> dict:
    outcomes = vm.consume_phase_b_triggers({"seq": 0}, seq_fn(name, payload))
    assert len(outcomes) == 1
    return outcomes[0]


def truck_unit(number: str, suffix: str) -> dict:
    return {
        "id": f"truck-{suffix}",
        "kind": "truck",
        "number": number,
        "type_size": f"Type {suffix}",
        "driver_name": f"Driver {suffix}",
        "driver_phone": f"0900{suffix.zfill(6)}",
    }


def container_unit(number: str, suffix: str) -> dict:
    return {
        "id": f"container-{suffix}",
        "kind": "container",
        "number": number,
        "type_size": f"{suffix}HC",
        "seal_no": f"SEAL-{suffix}",
    }


def test_scenario_a_three_cn_trucks_and_two_vn_delivery_trucks_survive_reopen(
    staging, event_seq
):
    sid = "LO-0306"
    before = vm.read_shipment(sid)
    old_scalar = before["data"]["1.2"]["container_no"]
    finance_before = deepcopy(before["data"]["3.4"])
    customs_before = deepcopy(before["data"]["2.4"])

    legs = [
        {
            "id": "leg-cn-pickup",
            "sequence": 1,
            "mode": "Truck",
            "origin": "Nam Ninh",
            "destination": "Hữu Nghị",
            "carrier": "CN Road Partner",
            "etd": "2026-09-20",
            "eta": "2026-09-21",
            "atd": "",
            "ata": "",
            "units": [
                truck_unit("桂A-10001", "CN1"),
                truck_unit("桂A-10002", "CN2"),
                truck_unit("桂A-10003", "CN3"),
            ],
        },
        {
            "id": "leg-vn-delivery",
            "sequence": 2,
            "mode": "Truck",
            "origin": "Hữu Nghị",
            "destination": "Kho An Phát, Bắc Ninh",
            "carrier": "VN Delivery Partner",
            "etd": "2026-09-22",
            "eta": "2026-09-22",
            "atd": "",
            "ata": "",
            "units": [
                truck_unit("29H-100.01", "VN1"),
                truck_unit("29H-100.02", "VN2"),
            ],
        },
    ]
    out = dispatch(event_seq, "shipment_transport_save", {
        "shipmentId": sid,
        "transportLegs": legs,
    })
    assert out["ok"], out["error"]

    # Independent fresh read + independent reopen projection.
    fresh = vm.read_shipment(sid)
    stored = fresh["data"]["1.2"]["transport_legs"]
    assert [unit["number"] for unit in stored[0]["units"]] == [
        "桂A-10001", "桂A-10002", "桂A-10003"
    ]
    assert [unit["number"] for unit in stored[1]["units"]] == ["29H-100.01", "29H-100.02"]
    assert len({unit["id"] for leg in stored for unit in leg["units"]}) == 5

    reopened = rd.shipment_projection(vm.read_shipment(sid))
    assert reopened["transportLegsStructured"] is True
    assert reopened["transportLegs"] == out["readback"]["transportLegs"]
    assert reopened["pickup"]["plate"] == "桂A-10001"
    assert reopened["pickup"]["driverPhone"] == "0900000CN1"
    assert reopened["importInfo"]["plateVN"] == "29H-100.01"
    assert reopened["importInfo"]["driverVN"] == "Driver VN1"

    # Legacy scalars remain compatibility evidence, but structured facts win.
    assert fresh["data"]["1.2"]["container_no"] == old_scalar
    assert reopened["pickup"]["plate"] != old_scalar
    # Finance/customs are outside this bounded save and remain unchanged.
    assert fresh["data"]["3.4"] == finance_before
    assert fresh["data"]["2.4"] == customs_before
    assert out["version"] > before["version"]
    assert "update" in {row["action"] for row in out["audit"]}


def test_scenario_b_three_sea_containers_survive_readback_and_reopen(staging, event_seq):
    sid = "LO-0307"
    legs = [{
        "id": "leg-sea-1",
        "sequence": 1,
        "mode": "Sea",
        "origin": "Yantian",
        "destination": "Cát Lái",
        "carrier": "ONE",
        "etd": "2026-10-01",
        "eta": "2026-10-05",
        "atd": "",
        "ata": "",
        "booking_no": "ONE-BKG-7788",
        "mbl": "ONEYTN7788",
        "hbl": "HBL-7788",
        "vessel": "ONE INNOVATION",
        "voyage": "V.092S",
        "units": [
            container_unit("OOLU1000011", "20"),
            container_unit("OOLU1000022", "40"),
            container_unit("OOLU1000033", "45"),
        ],
    }]
    out = dispatch(event_seq, "shipment_transport_save", {
        "shipmentId": sid,
        "transportLegs": legs,
    })
    assert out["ok"], out["error"]

    fresh = vm.read_shipment(sid)
    sea = fresh["data"]["1.2"]["transport_legs"][0]
    assert sea["booking_no"] == "ONE-BKG-7788"
    assert sea["carrier"] == "ONE"
    assert sea["vessel"] == "ONE INNOVATION"
    assert sea["voyage"] == "V.092S"
    assert sea["mbl"] == "ONEYTN7788"
    assert sea["hbl"] == "HBL-7788"
    assert [(unit["number"], unit["type_size"], unit["seal_no"]) for unit in sea["units"]] == [
        ("OOLU1000011", "20HC", "SEAL-20"),
        ("OOLU1000022", "40HC", "SEAL-40"),
        ("OOLU1000033", "45HC", "SEAL-45"),
    ]
    reopened = rd.shipment_projection(vm.read_shipment(sid))
    assert reopened["transportLegs"][0]["units"] == out["readback"]["transportLegs"][0]["units"]
    assert reopened["transport"]["containerNo"] == "OOLU1000011"


def test_scenario_c_air_facts_remain_exact(staging, event_seq):
    sid = "LO-0308"
    legs = [{
        "id": "leg-air-1",
        "sequence": 1,
        "mode": "Air",
        "origin": "CAN",
        "destination": "HAN",
        "carrier": "Vietnam Airlines",
        "etd": "2026-10-09",
        "eta": "2026-10-09",
        "atd": "",
        "ata": "",
        "mawb": "738-12345675",
        "hawb": "PA-HAN-00991",
        "flight_no": "VN507",
        "units": [],
    }]
    out = dispatch(event_seq, "shipment_transport_save", {
        "shipmentId": sid,
        "transportLegs": legs,
    })
    assert out["ok"], out["error"]

    fresh = vm.read_shipment(sid)
    air = fresh["data"]["1.2"]["transport_legs"][0]
    assert {key: air[key] for key in (
        "mode", "origin", "destination", "carrier", "flight_no", "mawb", "hawb", "etd", "eta"
    )} == {
        "mode": "Air",
        "origin": "CAN",
        "destination": "HAN",
        "carrier": "Vietnam Airlines",
        "flight_no": "VN507",
        "mawb": "738-12345675",
        "hawb": "PA-HAN-00991",
        "etd": "2026-10-09",
        "eta": "2026-10-09",
    }
    reopened = rd.shipment_projection(vm.read_shipment(sid))["transportLegs"][0]
    assert reopened["flightNo"] == "VN507"
    assert reopened["mawb"] == "738-12345675"
    assert reopened["hawb"] == "PA-HAN-00991"
    assert reopened["units"] == []


def test_cargo_summary_persists_and_blank_numeric_stays_unknown(staging, event_seq):
    sid = "LO-0308"
    out = dispatch(event_seq, "shipment_transport_save", {
        "shipmentId": sid,
        "cargoSummary": {
            "goods_description": "Linh kiện máy đóng gói",
            "package_count": "12",
            "package_type": "Pallet",
            "gross_weight_kg": "",
            "cbm": "8.75",
            "dimensions": "120 × 80 × 110 cm / pallet",
            "note": "Không chồng quá 2 tầng",
        },
    })
    assert out["ok"], out["error"]

    fresh = vm.read_shipment(sid)
    cargo = fresh["data"]["1.2"]["cargo_summary"]
    assert cargo == {
        "goods_description": "Linh kiện máy đóng gói",
        "package_type": "Pallet",
        "dimensions": "120 × 80 × 110 cm / pallet",
        "note": "Không chồng quá 2 tầng",
        "package_count": 12,
        "gross_weight_kg": None,
        "cbm": 8.75,
    }
    reopened = rd.shipment_projection(vm.read_shipment(sid))["cargo"]
    assert reopened["goodsDescription"] == "Linh kiện máy đóng gói"
    assert reopened["packs"] == 12.0
    assert reopened["weight"] is None
    assert reopened["cbm"] == 8.75


def test_old_scalar_shipment_opens_without_migration_and_cn_vn_are_separate(staging):
    sid = "LO-0299"
    fresh = vm.read_shipment(sid)
    assert "transport_legs" not in fresh["data"]["1.2"]

    projection = rd.shipment_projection(fresh)
    assert projection["transportLegsStructured"] is False
    assert projection["transportLegs"][0]["id"] == "legacy-primary-leg"
    assert projection["transportLegs"][0]["units"][0]["number"] == fresh["data"]["1.2"]["container_no"]
    assert projection["transportLegs"][1]["id"] == "legacy-delivery-leg"
    assert projection["transportLegs"][1]["units"][0]["number"] == fresh["data"]["2.7"]["truck_no"]
    assert projection["pickup"]["plate"] != projection["importInfo"]["plateVN"]
    assert projection["cargo"]["packs"] is None
    assert projection["cargo"]["qtyPkg"] == fresh["data"]["1.2"]["qty_pkg"]


def test_structured_empty_leg_list_is_authoritative_over_legacy_scalars():
    shipment = {
        "data": {
            "0.0": {"mode": "Sea"},
            "1.2": {
                "transport_legs": [],
                "pol": "LEGACY POL",
                "pod": "LEGACY POD",
                "container_no": "LEGACY-CONT",
            },
        },
    }

    legs, structured = transport_legs_for_read(shipment)
    facts = compatibility_facts(shipment)
    assert structured is True
    assert legs == []
    assert facts["mode"] == ""
    assert facts["origin"] == ""
    assert facts["container_no"] == ""


def test_legacy_sea_pickup_type_and_delivery_truck_remain_distinct_facts():
    shipment = {
        "data": {
            "0.0": {"mode": "Sea"},
            "1.2": {
                "pol": "Yantian",
                "pod": "Cát Lái",
                "carrier": "ONE",
                "etd": "2026-10-01",
                "booking_no": "BKG-1",
                "container_no": "CONT-1",
                "pickup_truck_type": "17.5m / 30t",
            },
            "2.6": {"arrival_date": "2026-10-05"},
            "2.7": {
                "truck_no": "29H-123.45",
                "seal_no": "Nguyễn Văn A · 0909000000",
                "addr": "Kho Bắc Ninh",
                "delivery_date": "2026-10-06",
            },
        },
    }

    legs, structured = transport_legs_for_read(shipment)
    assert structured is False
    assert [(leg["id"], leg["mode"]) for leg in legs] == [
        ("legacy-pickup-leg", "Truck"),
        ("legacy-primary-leg", "Sea"),
        ("legacy-delivery-leg", "Truck"),
    ]
    facts = compatibility_facts(shipment)
    assert facts["pickup_unit"]["type_size"] == "17.5m / 30t"
    assert facts["container_no"] == "CONT-1"
    assert facts["delivery_unit"]["number"] == "29H-123.45"
    assert facts["delivery_unit"]["driver_name"] == "Nguyễn Văn A · 0909000000"
    assert facts["origin"] == "Yantian"
    assert facts["destination"] == "Kho Bắc Ninh"
    assert facts["etd"] == "2026-10-01"
    assert facts["eta"] == "2026-10-05"


def test_unknown_sea_container_is_not_filled_from_pickup_truck():
    shipment = {
        "data": {
            "0.0": {"mode": "Truck"},
            "1.2": {"transport_legs": [
                {
                    "id": "pickup", "sequence": 1, "mode": "Truck",
                    "origin": "Factory", "destination": "Port", "carrier": "",
                    "etd": "", "eta": "", "atd": "", "ata": "",
                    "units": [truck_unit("CN-PLATE", "PICKUP")],
                },
                {
                    "id": "sea", "sequence": 2, "mode": "Sea",
                    "origin": "Port", "destination": "Destination", "carrier": "",
                    "etd": "", "eta": "", "atd": "", "ata": "", "units": [],
                },
            ]},
        },
    }

    facts = compatibility_facts(shipment)
    assert facts["pickup_unit"]["number"] == "CN-PLATE"
    assert facts["container_no"] == ""


def test_cargo_only_save_does_not_implicitly_migrate_legacy_transport(staging, event_seq):
    sid = "LO-0299"
    before = vm.read_shipment(sid)
    scalar_before = deepcopy(before["data"]["1.2"])

    out = dispatch(event_seq, "shipment_transport_save", {
        "shipmentId": sid,
        "cargoSummary": {
            "goods_description": "Hàng fixture",
            "package_count": "",
            "package_type": "",
            "gross_weight_kg": "",
            "cbm": "",
            "dimensions": "",
            "note": "",
        },
    })
    assert out["ok"], out["error"]
    fresh = vm.read_shipment(sid)
    assert "transport_legs" not in fresh["data"]["1.2"]
    for key, value in scalar_before.items():
        assert fresh["data"]["1.2"][key] == value


def test_strict_collection_validation_rejects_competing_or_ambiguous_shapes():
    with pytest.raises(ValueError, match="Trùng id chặng"):
        normalize_transport_legs([
            {"id": "same", "sequence": 1, "mode": "Truck", "units": []},
            {"id": "same", "sequence": 2, "mode": "Truck", "units": []},
        ])
    with pytest.raises(ValueError, match="Trùng thứ tự chặng"):
        normalize_transport_legs([
            {"id": "l1", "sequence": 1, "mode": "Truck", "units": []},
            {"id": "l2", "sequence": 1, "mode": "Truck", "units": []},
        ])
    with pytest.raises(ValueError, match="mode phải là"):
        normalize_transport_legs([
            {"id": "l1", "sequence": 1, "mode": "Barge", "units": []},
        ])
    with pytest.raises(ValueError, match="Trùng id phương tiện"):
        normalize_transport_legs([
            {"id": "l1", "sequence": 1, "mode": "Truck", "units": [truck_unit("A", "X")]},
            {"id": "l2", "sequence": 2, "mode": "Truck", "units": [truck_unit("B", "X")]},
        ])
    with pytest.raises(ValueError, match="chỉ nhận kind=container"):
        normalize_transport_legs([
            {"id": "sea", "sequence": 1, "mode": "Sea", "units": [truck_unit("A", "X")]},
        ])
    with pytest.raises(ValueError, match="không nhận xe/container"):
        normalize_transport_legs([
            {"id": "air", "sequence": 1, "mode": "Air", "units": [truck_unit("A", "X")]},
        ])
    with pytest.raises(ValueError, match="số nguyên"):
        normalize_cargo_summary({"package_count": "1.5"})


@pytest.mark.parametrize("customer_payload,error_text", [
    ({"customer": "An Phát JSC"}, "chọn khách hàng"),
    ({"customerId": "CUST-KHONGCO", "customer": "Tên giả"}, "đang hoạt động"),
])
def test_create_requires_an_active_directory_customer_id_without_writing(
    staging, event_seq, customer_payload, error_text
):
    from core.database import get_db

    db = get_db()
    assert db is not None
    sid = "LO-G1-NO-CUSTOMER-ID"
    audits_before = db.audit_logs.count_documents({"entity_type": "shipment", "entity_id": sid})

    out = dispatch(event_seq, "shipment_create", {"shipmentId": sid, **customer_payload})

    assert not out["ok"]
    assert error_text in out["error"].lower()
    assert db.shipments.find_one({"id": sid}) is None
    assert db.audit_logs.count_documents({"entity_type": "shipment", "entity_id": sid}) == audits_before


def test_create_refuses_an_archived_customer_before_writing(staging, event_seq):
    from core.database import get_db

    db = get_db()
    assert db is not None
    db.customers.update_one({"id": "CUST-ANPHAT"}, {"$set": {"is_deleted": True}})
    sid = "LO-G1-ARCHIVED-CUSTOMER"

    out = dispatch(event_seq, "shipment_create", {
        "shipmentId": sid,
        "customerId": "CUST-ANPHAT",
        "customer": "Tên giả từ browser",
    })

    assert not out["ok"]
    assert "đang hoạt động" in out["error"].lower()
    assert db.shipments.find_one({"id": sid}) is None
    assert db.audit_logs.count_documents({"entity_type": "shipment", "entity_id": sid}) == 0


@pytest.mark.parametrize("mode", ["Sea", "Truck", "Air"])
def test_create_uses_directory_name_and_keeps_sea_road_air_working(staging, event_seq, mode):
    sid = f"LO-G1-{mode.upper()}"
    out = dispatch(event_seq, "shipment_create", {
        "shipmentId": sid,
        "customerId": "CUST-ANPHAT",
        "customer": "Tên giả từ browser",
        "transport": {"mode": mode, "pol": "ORIGIN", "pod": "DESTINATION"},
    })

    assert out["ok"], out["error"]
    fresh = vm.read_shipment(sid)
    assert fresh["customer_id"] == "CUST-ANPHAT"
    assert fresh["customer"] == fresh["client"] == "An Phát JSC"
    assert fresh["customer"] != "Tên giả từ browser"
    assert fresh["data"]["1.2"]["transport_legs"][0]["mode"] == mode


def test_lightweight_create_starts_one_canonical_leg_and_navigable_detail_data(staging, event_seq):
    out = dispatch(event_seq, "shipment_create", {
        "shipmentId": "LO-OPS-V1",
        "customerId": "CUST-ANPHAT",
        "contractId": "HDMB-0306",
        "transport": {
            "mode": "Air",
            "incoterm": "FCA",
            "pol": "CAN",
            "pod": "HAN",
        },
    })
    assert out["ok"], out["error"]
    fresh = vm.read_shipment("LO-OPS-V1")
    assert fresh["data"]["1.2"]["pol"] == "CAN"  # compatibility field retained
    legs = fresh["data"]["1.2"]["transport_legs"]
    assert len(legs) == 1
    assert legs[0]["id"].startswith("leg-")
    assert legs[0]["mode"] == "Air"
    assert legs[0]["origin"] == "CAN"
    assert legs[0]["destination"] == "HAN"
    assert out["readback"]["transportLegsStructured"] is True


def test_component_exposes_progressive_mode_specific_operational_editor():
    source = open("component/src/components/ShipmentOperations.tsx", encoding="utf-8").read()
    detail = open("component/src/pages/ShipmentDetail.tsx", encoding="utf-8").read()
    create = open("component/src/pages/CreateShipment.tsx", encoding="utf-8").read()

    for label in (
        "HÀNG HÓA", "CÁC CHẶNG VẬN CHUYỂN", "+ THÊM CHẶNG",
        "Mô tả hàng", "Số kiện", "Loại kiện", "GW (kg)", "CBM",
        "Kích thước", "Ghi chú", "Thêm xe", "Thêm container",
        "Booking", "Vessel", "Voyage", "MBL", "HBL", "Flight no",
        "MAWB", "HAWB", "Sân bay đi", "Sân bay đến",
    ):
        assert label in source
    assert "window.confirm" in source
    assert "moveLeg" in source and "resequence" in source
    assert 'dispatch("shipment_transport_save"' in source
    assert '<details key={leg.id}' in source  # progressive disclosure per leg
    assert 'tab === "van-tai"' in detail
    assert "readOnly" in detail  # old scalar truck summary is not a competing editor
    assert "-- Bổ sung sau --" in create
    assert "Ngày khởi hành (ETD)" not in create
    assert "Địa chỉ giao hàng" not in create
    assert "?tab=van-tai" in create


def test_event_is_bounded_by_existing_shipment_edit_rbac(staging, event_seq):
    import streamlit as st

    st.session_state["current_user"] = {
        "username": "readonly",
        "display_name": "Read only",
        "role": "viewer",
        "permissions": [],
    }
    out = dispatch(event_seq, "shipment_transport_save", {
        "shipmentId": "LO-0306",
        "transportLegs": [],
    })
    assert out["ok"] is False
    assert "RBAC" in out["error"]
    assert "transport_legs" not in vm.read_shipment("LO-0306")["data"]["1.2"]
