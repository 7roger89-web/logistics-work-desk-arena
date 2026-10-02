import copy
import unittest
from datetime import date

from views.support_attention import build_attention_projection


def row(priority="BinhThuong", journey=None, support="Last Writer"):
    return {
        "id": "S1",
        "customer": "ABC",
        "sale": "Sale A",
        "support": support,
        "status": "Đang vận chuyển",
        "priority": priority,
        "nextAction": "Nộp chứng từ",
        "nextActionDetail": "Việc được giao",
        "nextRoute": "/lo-hang/S1?tab=nhap",
        "missingDocs": [],
        "journey": journey or {"currentStageId": "transit", "nodes": [], "modules": []},
    }


def module_journey(gated=True, status=None, blocked_by=None):
    instance = "M1" if gated else "M2"
    step = "result" if gated else "prepare"
    state = status or ("BLOCKING" if gated else "WAITING")
    return {
        "currentStageId": "transit",
        "nodes": [
            {"id": "customs-import", "targetTab": "nhap"},
            {"id": f"wm-{instance}-{step}", "targetTab": "nhap", "moduleId": instance},
        ],
        "modules": [{
            "instanceId": instance,
            "templateId": "DEMO",
            "templateVersion": 1,
            "name": "Demo",
            "status": state,
            "summary": "0/1 bước",
            "nextStep": "Result received",
            "nextStepId": step,
            "steps": [{"id": step, "blockedBy": list(blocked_by or [])}],
            "gate": {"stage": "delivery", "label": "DELIVERY", "type": "BLOCKING"} if gated else {},
            "gateText": "Chặn DELIVERY" if gated and state == "BLOCKING" else "",
            "blocker": "Không đọc được phiên bản" if state == "UNKNOWN" else "",
            "anchorStage": "customs-import",
        }],
    }


class Attention166Tests(unittest.TestCase):
    def test_blocking_and_gate_less_module_semantics(self):
        blocked = build_attention_projection(
            [row(journey=module_journey(True))],
            [],
            today=date(2026, 10, 2),
        )[0]
        self.assertEqual((blocked["band"], blocked["blockedGate"]), ("BLOCKING", "DELIVERY"))
        self.assertIn("stage=wm-M1-result", blocked["route"])

        plain = build_attention_projection(
            [row(journey=module_journey(False))],
            [],
            today=date(2026, 10, 2),
        )[0]
        self.assertEqual((plain["band"], plain["blockedGate"]), ("ACTION", ""))

    def test_gate_less_step_blocked_by_dependency_is_not_falsely_actionable(self):
        items = build_attention_projection(
            [row(journey=module_journey(False, blocked_by=["prepare-parent"]))],
            [],
            today=date(2026, 10, 2),
        )
        self.assertEqual(items, [])

    def test_task_owner_and_deadline_are_authoritative(self):
        tasks = [
            {
                "task_id": "T1",
                "shipment_id": "S1",
                "content": "Over",
                "assignee": "Support A",
                "deadline": "2026-10-01",
                "done": False,
            },
            {
                "task_id": "T2",
                "shipment_id": "S1",
                "content": "Free",
                "assignee": "Support A",
                "deadline": "ASAP",
                "done": False,
            },
        ]
        items = build_attention_projection(
            [row(support="Support B")],
            tasks,
            today=date(2026, 10, 2),
        )
        by_ref = {item["sourceRef"]: item for item in items}
        self.assertEqual(by_ref["TASK:T1"]["owner"], "Support A")
        self.assertEqual(by_ref["TASK:T1"]["band"], "OVERDUE")
        self.assertEqual(by_ref["TASK:T2"]["band"], "ACTION")
        self.assertEqual(by_ref["TASK:T2"]["deadline"], "")

    def test_exact_identity_only_and_physical_position_unchanged(self):
        shipment = row(priority="CanXuLy")
        before = copy.deepcopy(shipment)
        task = {
            "task_id": "T1",
            "shipment_id": "S1",
            "content": "Nộp chứng từ",
            "assignee": "A",
            "deadline": "",
            "done": False,
        }
        items = build_attention_projection(
            [shipment],
            [task, copy.deepcopy(task)],
            today=date(2026, 10, 2),
        )
        self.assertEqual(sum(i["sourceType"] == "TASK" for i in items), 1)
        self.assertEqual(sum(i["sourceType"] == "PRIMARY_ACTION" for i in items), 1)
        self.assertEqual(shipment, before)
        self.assertEqual(shipment["journey"]["currentStageId"], "transit")

    def test_done_unknown_and_empty_are_truthful(self):
        done = module_journey(False, "DONE")
        self.assertEqual(
            build_attention_projection([row(journey=done)], [], today=date(2026, 10, 2)),
            [],
        )

        unknown = module_journey(False, "UNKNOWN")
        item = build_attention_projection(
            [row(journey=unknown)],
            [],
            today=date(2026, 10, 2),
        )[0]
        self.assertTrue(item["unknown"])
        self.assertNotEqual(item["band"], "BLOCKING")

        self.assertEqual(
            build_attention_projection([row()], [], today=date(2026, 10, 2)),
            [],
        )


if __name__ == "__main__":
    unittest.main()
