import json
import unittest
from datetime import date

from views.operations_control_tower import build_operations_control_tower
from views.support_attention import build_attention_projection


def shipment(sid, *, customer="ABC", status="TRANSIT", sale="Sale A", support="Last Writer"):
    return {
        "id": sid,
        "customer": customer,
        "status": status,
        "sale": sale,
        "support": support,
        "priority": "BinhThuong",
        "nextAction": "Theo dõi lô",
        "nextActionDetail": "",
        "nextRoute": f"/lo-hang/{sid}",
        "missingDocs": [],
        "journey": {"nodes": [], "modules": [], "currentStageId": "transit"},
    }


def attention(
    aid,
    sid,
    *,
    band="ACTION",
    owner="",
    deadline_date="",
    deadline="",
    blocked_gate="",
    source_type="TASK",
    unknown=False,
    source_priority="",
    customer_context="",
    module_template="",
    module_name="",
):
    return {
        "id": aid,
        "shipmentId": sid,
        "sourceType": source_type,
        "sourceRef": f"{source_type}:{aid}",
        "band": band,
        "reason": "Lý do",
        "action": f"Việc {aid}",
        "context": customer_context,
        "route": f"/lo-hang/{sid}?tab=nhap",
        "owner": owner,
        "deadline": deadline,
        "deadlineDate": deadline_date,
        "blockedGate": blocked_gate,
        "primary": source_type == "PRIMARY_ACTION",
        "sourcePriority": source_priority,
        "moduleTemplateId": module_template,
        "moduleName": module_name,
        "provenance": "test",
        "unknown": unknown,
    }


class OperationsControlTower170Tests(unittest.TestCase):
    def test_manager_subset_excludes_normal_action_and_preserves_attention_order(self):
        rows = [shipment("S1"), shipment("S2"), shipment("S3"), shipment("S4")]
        items = [
            attention("B", "S1", band="BLOCKING", blocked_gate="DELIVERY"),
            attention("NORMAL", "S2", band="ACTION"),
            attention("O", "S3", band="OVERDUE", deadline_date="2026-10-01"),
            attention("K", "S4", band="ACTION", source_type="PRIMARY_ACTION", source_priority="Khan"),
        ]
        tower = build_operations_control_tower(rows, items, today=date(2026, 10, 2))
        self.assertEqual(
            [item["id"] for item in tower["interventionQueue"]],
            ["B", "O", "K"],
        )
        self.assertNotIn("NORMAL", [item["id"] for item in tower["interventionQueue"]])

    def test_scope_distinguishes_attention_no_signal_and_unknown_without_health_claim(self):
        rows = [shipment("S1"), shipment("S2"), shipment("S3"), shipment("S4")]
        items = [
            attention("A1", "S1", band="BLOCKING"),
            attention("A2", "S2", band="ACTION"),
            attention("A3", "S3", unknown=True),
        ]
        scope = build_operations_control_tower(rows, items, today=date(2026, 10, 2))["scope"]
        self.assertEqual(scope["shipmentCount"], 4)
        self.assertEqual(scope["attentionShipmentCount"], 3)
        self.assertEqual(scope["noSignalShipmentCount"], 1)
        self.assertEqual(scope["unknownShipmentCount"], 1)
        self.assertNotIn("healthy", json.dumps(scope).lower())

    def test_horizon_uses_structured_date_only(self):
        rows = [shipment("S1"), shipment("S2"), shipment("S3"), shipment("S4")]
        items = [
            attention("OD", "S1", band="OVERDUE", deadline_date="2026-10-01", deadline="01/10/2026"),
            attention("TODAY", "S2", band="DUE_SOON", deadline_date="2026-10-02", deadline="02/10/2026"),
            attention("SOON", "S3", band="DUE_SOON", deadline_date="2026-10-05", deadline="05/10/2026"),
            attention("TEXT", "S4", band="DUE_SOON", deadline_date="", deadline="ASAP"),
        ]
        horizon = build_operations_control_tower(rows, items, today=date(2026, 10, 2))["horizon"]
        by_id = {bucket["id"]: bucket for bucket in horizon["buckets"]}
        self.assertEqual(by_id["OVERDUE"]["count"], 1)
        self.assertEqual(by_id["TODAY"]["count"], 1)
        self.assertEqual(by_id["NEXT_3_DAYS"]["count"], 1)
        self.assertFalse(any(item["id"] == "TEXT" for bucket in horizon["buckets"] for item in bucket["items"]))
        self.assertEqual(horizon["precision"], "DATE_ONLY")

    def test_workload_uses_attention_owner_and_keeps_unassigned_explicit(self):
        rows = [
            shipment("S1", support="Support B"),
            shipment("S2", support="Support C"),
        ]
        items = [
            attention("OWNED", "S1", band="OVERDUE", owner="Support A"),
            attention("NONE", "S2", band="BLOCKING", owner=""),
            attention("SENTINEL", "S2", band="ACTION", owner="Chưa phân công", source_priority="Khan"),
        ]
        workload = build_operations_control_tower(rows, items, today=date(2026, 10, 2))["workload"]
        self.assertEqual(workload[0]["ownerKey"], "UNASSIGNED")
        self.assertEqual(workload[0]["blocking"], 1)
        self.assertEqual(workload[0]["action"], 1)
        self.assertNotIn("Chưa phân công", [row["owner"] for row in workload])
        support_a = next(row for row in workload if row["owner"] == "Support A")
        self.assertEqual(support_a["overdue"], 1)
        self.assertNotIn("Support B", [row["owner"] for row in workload])
        self.assertNotIn("Support C", [row["owner"] for row in workload])

    def test_delivered_shipment_remains_when_attention_is_open(self):
        rows = [shipment("S1", status="Đã giao")]
        items = [attention("POD", "S1", band="OVERDUE", owner="Support A")]
        queue = build_operations_control_tower(rows, items, today=date(2026, 10, 2))["interventionQueue"]
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["shipmentStatus"], "Đã giao")

    def test_concentration_is_neutral_by_customer_gate_and_module(self):
        rows = [
            shipment("S1", customer="ABC"),
            shipment("S2", customer="ABC"),
            shipment("S3", customer="XYZ"),
        ]
        items = [
            attention(
                "M1", "S1", band="BLOCKING", blocked_gate="CUSTOMS",
                source_type="WORK_MODULE", module_template="QC", module_name="QC"
            ),
            attention(
                "M2", "S2", band="BLOCKING", blocked_gate="CUSTOMS",
                source_type="WORK_MODULE", module_template="QC", module_name="QC"
            ),
            attention("D1", "S3", band="DUE_SOON", deadline_date="2026-10-03"),
        ]
        concentration = build_operations_control_tower(rows, items, today=date(2026, 10, 2))["concentration"]
        abc = next(row for row in concentration["customers"] if row["key"] == "ABC")
        customs = next(row for row in concentration["gates"] if row["key"] == "CUSTOMS")
        qc = next(row for row in concentration["modules"] if row["key"] == "QC")
        self.assertEqual(abc["count"], 2)
        self.assertEqual(customs["blocking"], 2)
        self.assertEqual(qc["count"], 2)

    def test_shared_attention_extension_carries_date_and_module_identity_without_new_authority(self):
        rows = [shipment("S1")]
        tasks = [{
            "task_id": "T1",
            "shipment_id": "S1",
            "content": "Nộp hồ sơ",
            "assignee": "Support A",
            "deadline": "2026-10-03",
            "done": False,
        }]
        projected = build_attention_projection(rows, tasks, today=date(2026, 10, 2))
        task = next(item for item in projected if item["sourceType"] == "TASK")
        self.assertEqual(task["deadlineDate"], "2026-10-03")
        self.assertEqual(task["owner"], "Support A")

    def test_projection_preserves_exact_drilldown_and_contains_no_score_fields(self):
        rows = [shipment("S1")]
        items = [attention("B", "S1", band="BLOCKING", blocked_gate="DELIVERY")]
        tower = build_operations_control_tower(rows, items, today=date(2026, 10, 2))
        self.assertEqual(tower["interventionQueue"][0]["route"], "/lo-hang/S1?tab=nhap")
        payload = json.dumps(tower, ensure_ascii=False).lower()
        self.assertNotIn('"score"', payload)
        self.assertNotIn("overloaded", payload)
        self.assertNotIn("leaderboard", payload)


if __name__ == "__main__":
    unittest.main()
