"""Bounded Home -> Journey routing (issue #208 / LOGI-199).

A manual task has a shipment binding but NO canonical stage binding in the
tasks schema. It must therefore open its own lot instead of a guessed
``?tab=lay-hang`` export destination; free text is never a stage authority.
Work Modules keep their authoritative node/anchorStage route.
"""
from copy import deepcopy
from datetime import date

import pytest

from tests.test_support_attention_now_166 import row
from tests.test_visual_shipment_workspace import document, event, project, staging  # noqa: F401
from views import logi_view_model as vm
from views.support_attention import build_attention_projection


@pytest.mark.parametrize("content", [
    "Thu nốt công nợ", "Chốt xe và giờ lấy hàng", "Khai tờ khai nhập khẩu",
    "SI / VGM", "Việc không có công đoạn đã xác nhận",
])
def test_unbound_manual_task_opens_its_shipment_without_inventing_export_stage(content):
    shipment = row()
    shipment["id"] = "FCL/199?A&B"
    task = {"task_id": "T199", "shipment_id": shipment["id"], "content": content,
            "deadline": "2026-10-01", "assignee": "sale.test", "done": False,
            "route": "https://untrusted.invalid/lo-hang/OTHER"}
    original = deepcopy(task)
    attention = build_attention_projection([shipment], [task], today=date(2026, 10, 16))[0]
    expected_route = "/lo-hang/FCL%2F199%3FA%26B"
    assert attention["route"] == expected_route
    assert attention["shipmentId"] == shipment["id"]
    assert attention["unknown"] is False  # known task; missing stage is navigation metadata
    assert "Chưa gắn công đoạn" in attention["reason"]
    assert attention["action"] == content
    assert attention["band"] == "OVERDUE"  # missing stage does not erase a real deadline
    assert attention["owner"] == "sale.test"
    # Home attention and the task list must point at the same honest destination.
    assert vm._task_projection([shipment], {"tasks": [task]})[0]["route"] == expected_route
    assert task == original  # projection never mutates the raw task


def test_missing_stage_does_not_promote_known_task_into_manager_unknown_metrics():
    from views.operations_control_tower import build_operations_control_tower

    shipment = row()
    task = {"task_id": "T199", "shipment_id": shipment["id"], "content": "Thu công nợ"}
    attention = build_attention_projection([shipment], [task], today=date(2026, 10, 16))
    item = next(item for item in attention if item["sourceType"] == "TASK")
    assert item["band"] == "ACTION"
    assert "Chưa gắn công đoạn" in item["reason"]
    tower = build_operations_control_tower([shipment], attention, today=date(2026, 10, 16))
    assert tower["scope"]["unknownShipmentCount"] == 0
    assert not tower["interventionQueue"]


def test_work_module_with_authoritative_anchor_keeps_its_exact_stage_route():
    shipment = row()
    shipment["journey"] = {
        "currentStageId": "transit",
        "nodes": [
            {"id": "customs-import", "targetTab": "nhap"},
            {"id": "wm-M1-result", "targetTab": "nhap", "moduleId": "M1"},
        ],
        "modules": [{
            "instanceId": "M1",
            "templateId": "DEMO",
            "templateVersion": 1,
            "name": "Demo",
            "status": "BLOCKING",
            "summary": "0/1 bước",
            "nextStepId": "result",
            "nextStep": "Kết quả",
            "anchorStage": "customs-import",
            "steps": [{"id": "result", "label": "Kết quả", "completed": False}],
            "gate": {"label": "Chờ kết quả"},
        }],
    }
    item = next(
        item for item in build_attention_projection([shipment], [], today=date(2026, 10, 16))
        if item["sourceType"] == "WORK_MODULE"
    )
    assert item["route"] == "/lo-hang/S1?tab=nhap&stage=wm-M1-result&work=info"
    assert item["unknown"] is False


def test_authoritative_primary_action_keeps_exact_route_and_unknown_facts():
    shipment = project(document(scope=["ORIGIN_PICKUP", "EXPORT_HANDLING", "EXPORT_CUSTOMS",
                                       "ORIGIN_TERMINAL_OR_BORDER", "MAIN_CARRIAGE"]))
    original = deepcopy(shipment)
    attention = build_attention_projection([shipment], [], today=date(2026, 10, 16))
    action = next(item for item in attention if item["sourceType"] == "PRIMARY_ACTION")
    assert action["route"] == shipment["nextRoute"] == shipment["journey"]["primaryAction"]["route"]
    assert action["route"].endswith("?tab=van-tai&stage=si-vgm&work=info")
    assert action["unknown"] is False  # stage destination is known, not stage completion
    node = next(n for n in shipment["journey"]["nodes"] if n["id"] == "si-vgm")
    assert node["factState"] == "UNKNOWN"
    assert node["completed"] is False
    assert shipment == original


def test_saved_stage_fact_survives_a_fresh_projection_reload(staging):  # noqa: F811
    """Save -> backend readback -> fresh page-load projection (isolated DB).

    ``build_view_model`` is the same projection a reloaded page computes; it
    re-reads the canonical document instead of reusing the write outcome.
    """
    from core.database import get_db

    before = vm.read_shipment("SEA-160")
    saved = event("shipment_sea_facts_save", {
        "shipmentId": "SEA-160",
        "requestId": "FLOW199-SAVE",
        "expectedVersion": before["version"],
        "fields": {"on_board_at": "2026-10-05"},
    })
    assert saved["ok"], saved
    assert saved["persisted"]["on_board_at"] == "2026-10-05"
    stored = get_db().shipments.find_one({"id": "SEA-160"}, {"_id": 0})
    assert stored["data"]["1.2"]["sea_export"]["on_board_at"] == "2026-10-05"
    assert stored["version"] == before["version"] + 1

    reloaded = next(row for row in vm.build_view_model()["shipments"] if row["id"] == "SEA-160")
    assert reloaded["journey"]["seaFacts"]["on_board_at"] == "2026-10-05"
    on_board = next(n for n in reloaded["journey"]["nodes"] if n["id"] == "on-board")
    assert on_board["evidence"].startswith("On-board: 2026-10-05") or "2026-10-05" in on_board["evidence"]


def test_attachment_metadata_never_completes_a_stage(staging):  # noqa: F811
    """A recorded file is linked to its node but never accepted as evidence."""
    from core.database import save_shipment_attachment

    assert save_shipment_attachment({
        "id": "fixture-si-only",
        "shipment_id": "SEA-160",
        "original_name": "si-only-199.pdf",
        "sha256": "a" * 64,
        "storage_file_id": "fixture-storage-si-only",
        "storage_backend": "gridfs",
        "category": "si",
        "original_size": 100,
        "stored_size": 100,
        "uploaded_at": "2026-10-16T00:00:00Z",
        "uploaded_by": "fixture",
    })
    reloaded = next(row for row in vm.build_view_model()["shipments"] if row["id"] == "SEA-160")
    si = next(n for n in reloaded["journey"]["nodes"] if n["id"] == "si-vgm")
    assert si["documentIds"] == ["fixture-si-only"]  # linked to the node
    assert si["factState"] == "UNKNOWN"              # but not accepted
    assert si["completed"] is False


@pytest.mark.parametrize("mode,load", [("Air", "FCL"), ("Road", "FTL")])
def test_air_and_road_never_inherit_sea_fcl_document_categories(mode, load):
    row = project(document(mode=mode, load=load))
    node_ids = {node["id"] for node in row["journey"]["nodes"]}
    assert not ({"si-vgm", "gate-in", "on-board", "transit", "arrival"} & node_ids)
    for node in row["journey"]["nodes"]:
        assert not ({"si", "vgm"} & set(node["documentCategories"])), node["id"]
