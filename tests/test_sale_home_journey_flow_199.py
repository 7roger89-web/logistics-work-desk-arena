"""Bounded Home -> Journey routing; no stage guessing from free-text tasks."""
from copy import deepcopy
from datetime import date

import pytest

from tests.test_support_attention_now_166 import row
from tests.test_visual_shipment_workspace import document, project
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
    assert vm._task_projection([shipment], {"tasks": [task]})[0]["route"] == expected_route
    assert task == original


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


def test_authoritative_stage_action_keeps_exact_route_and_unknown_facts():
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
