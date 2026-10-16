from __future__ import annotations

from copy import deepcopy
from datetime import date

import mongomock
import pytest

from core import auth, database
from core.shipment_journey import task_stage_nodes
from core.users import build_user_document, public_identity
from tests.test_visual_shipment_workspace import document
from views.logi_task_navigation import task_destination
from views.logi_view_model import (
    ALL_EVENTS,
    PHASE_B_EVENTS,
    _task_assignment_projection,
    _task_projection,
    consume_phase_b_triggers,
)
from views.support_attention import build_attention_projection


SHIPMENT_ID = "FLOW199-FCL"


@pytest.fixture
def task_env(monkeypatch):
    client = mongomock.MongoClient()
    db = client["isolated_task_routing_199"]
    sea = document()
    sea["id"] = SHIPMENT_ID
    sea["customer"] = "An Phát JSC"
    sea["customer_id"] = "CUST-ANPHAT"
    db.shipments.insert_one(deepcopy(sea))

    sale_doc = build_user_document(
        "sale.task199", "ephemeral-test-password", "Sale Tester", "sale", created_by="fixture"
    )
    support_doc = build_user_document(
        "support.task199", "ephemeral-test-password", "Support Tester", "support", created_by="fixture"
    )
    # Legacy/preview Viewer identity: role is not creatable by the canonical
    # user-management form, but the permission matrix still denies shipment_edit.
    viewer_doc = {
        "user_id": "viewer-task199",
        "username": "viewer.task199",
        "display_name": "Viewer Tester",
        "role": "viewer",
        "active": True,
        "password_hash": "test-only-not-projected",
    }
    db.users.insert_many([sale_doc, support_doc, viewer_doc])

    actor = public_identity(sale_doc)
    monkeypatch.setattr(database, "get_db", lambda: db)
    monkeypatch.setattr(auth, "current_user", lambda: actor)
    return {"db": db, "sale": actor, "support": public_identity(support_doc),
            "viewer": public_identity(viewer_doc), "sea": sea}


def _projected_row(shipment: dict) -> dict:
    return {
        "id": shipment["id"],
        "customer": shipment.get("customer", "—"),
        "sale": "Sale Tester",
        "support": "Support Tester",
        "status": "Đang vận chuyển",
        "priority": "BinhThuong",
        "nextAction": "Kiểm tra lô",
        "nextActionDetail": "",
        "nextRoute": f"/lo-hang/{shipment['id']}?tab=van-tai",
        "missingDocs": [],
        "journey": {"nodes": task_stage_nodes(shipment), "modules": [], "currentStageId": ""},
    }


def test_stage_choices_are_current_base_nodes_for_shipment_mode():
    sea = document()
    sea_nodes = {node["id"]: node for node in task_stage_nodes(sea)}
    assert "si-vgm" in sea_nodes
    assert sea_nodes["si-vgm"]["targetTab"] == "van-tai"
    assert all(not node.get("moduleId") for node in sea_nodes.values())

    air = document(mode="Air", load="DIRECT")
    air["data"]["0.0"]["execution_profile"]["service_scope"] = [
        "MAIN_CARRIAGE", "IMPORT_CUSTOMS", "FINAL_DELIVERY",
    ]
    air_nodes = {node["id"]: node for node in task_stage_nodes(air)}
    assert "si-vgm" not in air_nodes
    assert "AIR_DOCUMENTS" in air_nodes
    assert air_nodes["AIR_DOCUMENTS"]["targetTab"] == "van-tai"


def test_add_task_validates_stage_and_preserves_existing_task_history_and_assignment(task_env):
    db = task_env["db"]
    support = task_env["support"]

    assert database.add_task(
        "Confirm SI with customer",
        support["display_name"],
        "15/10/2026",
        assignee_user_id=support["user_id"],
        assigned_by_user_id=task_env["sale"]["user_id"],
        shipment_id=SHIPMENT_ID,
        task_scope="STAGE",
        stage_id="si-vgm",
        task_id="TASK-STAGE-199",
    )
    saved = next(row for row in database.load_tasks(db=db) if row["task_id"] == "TASK-STAGE-199")
    assert saved["shipment_id"] == SHIPMENT_ID
    assert saved["task_scope"] == "STAGE"
    assert saved["stage_id"] == "si-vgm"
    assert saved["assignee"] == "Support Tester"
    assert saved["assignee_user_id"] == support["user_id"]
    assert saved["assigned_by_user_id"] == task_env["sale"]["user_id"]
    assert saved["deadline"] == "15/10/2026"
    assert saved["created_by"] == "sale.task199"
    assert saved["created_by_user_id"] == task_env["sale"]["user_id"]
    assert saved["created_by_role"] == "sale"

    audit = database.load_audit_logs("task", "TASK-STAGE-199", db=db)
    assert len(audit) == 1
    assert audit[0]["action"] == "create"
    assert audit[0]["actor"] == "sale.task199"
    assert audit[0]["actor_user_id"] == task_env["sale"]["user_id"]
    assert audit[0]["after"]["stage_id"] == "si-vgm"

    # The same maritime node cannot be attached to a current Air Journey.
    air = document(mode="Air", load="DIRECT")
    air["id"] = "FLOW199-AIR"
    air["data"]["0.0"]["execution_profile"]["service_scope"] = [
        "MAIN_CARRIAGE", "IMPORT_CUSTOMS", "FINAL_DELIVERY",
    ]
    db.shipments.insert_one(air)
    assert not database.add_task(
        "Text may mention SI/VGM, but the route is not guessed",
        shipment_id="FLOW199-AIR",
        task_scope="STAGE",
        stage_id="si-vgm",
        task_id="TASK-INVALID-AIR-199",
    )
    assert database.get_last_db_error() == "Công đoạn không hợp lệ với Journey hiện tại của lô."
    assert db.tasks.count_documents({"task_id": "TASK-INVALID-AIR-199"}) == 0


def test_task_creation_dispatch_reads_back_authorship_and_canonical_assignee(task_env, monkeypatch):
    payload = {
        "requestId": "TASK-CREATE-199-1",
        "content": "Confirm SI with customer",
        "assigneeUserId": task_env["support"]["user_id"],
        "deadline": "2026-10-15",
        "shipmentId": SHIPMENT_ID,
        "taskScope": "STAGE",
        "stageId": "si-vgm",
    }
    assert "task_create" in PHASE_B_EVENTS
    assert "task_create" in ALL_EVENTS
    session = {}
    outcomes = consume_phase_b_triggers(session, {
        "task_create": {"seq": 1, "event": "task_create", "payload": payload},
    })
    assert len(outcomes) == 1
    outcome = outcomes[0]
    assert outcome["event"] == "task_create"
    assert outcome["ok"] is True
    assert outcome["requestId"] == "TASK-CREATE-199-1"
    # Existing sequence guard still prevents a replay from creating another task.
    assert consume_phase_b_triggers(session, {
        "task_create": {"seq": 1, "event": "task_create", "payload": payload},
    }) == []
    readback = outcome["readback"]
    assert readback["taskId"]
    assert readback["shipmentId"] == SHIPMENT_ID
    assert readback["taskScope"] == "STAGE"
    assert readback["stageId"] == "si-vgm"
    assert readback["assignee"] == "Support Tester"
    assert readback["assigneeUserId"] == task_env["support"]["user_id"]
    assert readback["deadline"] == "15/10/2026"
    assert readback["createdBy"] == "sale.task199"

    saved_tasks = database.load_tasks(db=task_env["db"])
    saved = next(row for row in saved_tasks if row["task_id"] == readback["taskId"])
    assert saved["done"] is False
    assert database.load_audit_logs("task", readback["taskId"], db=task_env["db"])[0]["action"] == "create"

    # Fresh database readback feeds both the Task desk and Home Attention from
    # the same authoritative task metadata; wording remains deliberately
    # unrelated to the Journey node.
    shipment_row = _projected_row(task_env["sea"])
    projected_task = next(
        row for row in _task_projection([shipment_row], {"tasks": saved_tasks})
        if row["id"] == readback["taskId"]
    )
    assert projected_task["route"] == f"/lo-hang/{SHIPMENT_ID}?tab=van-tai&stage=si-vgm&work=info"
    home_item = next(
        item for item in build_attention_projection([shipment_row], saved_tasks, today=date(2026, 10, 15))
        if item["sourceRef"] == f"TASK:{readback['taskId']}"
    )
    assert home_item["route"] == projected_task["route"]
    assert home_item["navigationStatus"] == "STAGE"

    # UI choices expose only active public identities, never credential material.
    policy = _task_assignment_projection(list(database.load_users(db=task_env["db"]).values()))
    assert policy["canCreate"] is True
    assert {entry["userId"] for entry in policy["assignees"]} == {
        "", task_env["support"]["user_id"], task_env["viewer"]["user_id"],
    }
    assert all("password" not in str(entry).lower() for entry in policy["assignees"])

    # Existing role matrix still denies a Viewer through the same dispatcher;
    # the UI capability is not the authorization boundary.
    monkeypatch.setattr(auth, "current_user", lambda: task_env["viewer"])
    denied_rows = consume_phase_b_triggers(session, {
        "task_create": {
            "seq": 2,
            "event": "task_create",
            "payload": {**payload, "requestId": "TASK-CREATE-199-DENIED"},
        },
    })
    assert len(denied_rows) == 1
    assert denied_rows[0]["ok"] is False
    assert "shipment_edit" in denied_rows[0]["error"]
    assert task_env["db"].tasks.count_documents({}) == 1


def test_destination_projection_routes_by_explicit_scope_not_task_words(task_env):
    shipment = _projected_row(task_env["sea"])
    tasks = [
        {"task_id": "T-STAGE", "shipment_id": SHIPMENT_ID, "content": "Any text",
         "task_scope": "STAGE", "stage_id": "si-vgm", "done": False},
        {"task_id": "T-FINANCE", "shipment_id": SHIPMENT_ID, "content": "Export customs wording",
         "task_scope": "FINANCE", "done": False},
        {"task_id": "T-LOT", "shipment_id": SHIPMENT_ID, "content": "Collect customer debt",
         "task_scope": "SHIPMENT", "done": False},
        {"task_id": "T-UNKNOWN", "shipment_id": SHIPMENT_ID, "content": "SI / VGM",
         "done": False},
        {"task_id": "T-STALE", "shipment_id": SHIPMENT_ID, "content": "Finance",
         "task_scope": "STAGE", "stage_id": "old-node", "done": False},
        {"task_id": "T-GENERAL", "content": "General task", "done": False},
    ]
    by_task = {row["id"]: row for row in _task_projection([shipment], {"tasks": tasks})}
    assert by_task["T-STAGE"]["route"] == f"/lo-hang/{SHIPMENT_ID}?tab=van-tai&stage=si-vgm&work=info"
    assert by_task["T-FINANCE"]["route"] == f"/lo-hang/{SHIPMENT_ID}?tab=tai-chinh"
    assert by_task["T-LOT"]["route"] == f"/lo-hang/{SHIPMENT_ID}"
    assert by_task["T-UNKNOWN"]["route"] == f"/lo-hang/{SHIPMENT_ID}"
    assert "Chưa gắn công đoạn" in by_task["T-UNKNOWN"]["dueNote"]
    assert by_task["T-STALE"]["route"] == f"/lo-hang/{SHIPMENT_ID}"
    assert "chưa hợp lệ" in by_task["T-STALE"]["dueNote"]
    assert by_task["T-GENERAL"]["lot"] == "—"
    assert by_task["T-GENERAL"]["route"] == "/lo-hang"

    attention = build_attention_projection(
        [shipment], tasks, today=date(2026, 10, 2),
    )
    by_ref = {item["sourceRef"]: item for item in attention if item["sourceType"] == "TASK"}
    assert by_ref["TASK:T-STAGE"]["navigationStatus"] == "STAGE"
    assert by_ref["TASK:T-FINANCE"]["route"].endswith("?tab=tai-chinh")
    assert by_ref["TASK:T-LOT"]["route"] == f"/lo-hang/{SHIPMENT_ID}"
    assert by_ref["TASK:T-UNKNOWN"]["route"] == f"/lo-hang/{SHIPMENT_ID}"
    assert "mở workspace lô" in by_ref["TASK:T-UNKNOWN"]["reason"].lower()


def test_legacy_records_are_not_migrated_and_explicit_whole_lot_routes_stay_exact(task_env):
    db = task_env["db"]
    db.tasks.insert_one({"task_id": "LEGACY-199", "content": "Thu công nợ", "done": False})
    legacy = next(row for row in database.load_tasks(db=db) if row["task_id"] == "LEGACY-199")
    assert "shipment_id" not in legacy
    assert "task_scope" not in legacy
    assert "stage_id" not in legacy
    assert task_destination(legacy, None) == {
        "route": "/lo-hang", "navigationStatus": "GENERAL", "notice": "",
    }

    route = task_destination(
        {"shipment_id": SHIPMENT_ID, "task_scope": "SHIPMENT", "content": "Finance"},
        _projected_row(task_env["sea"]),
    )
    assert route["route"] == f"/lo-hang/{SHIPMENT_ID}"
    assert route["navigationStatus"] == "SHIPMENT"
