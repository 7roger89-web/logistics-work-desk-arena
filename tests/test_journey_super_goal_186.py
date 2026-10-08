"""Issue #186 — Journey Cockpit V3 terminal integration source contracts.

These tests pin the bounded UI architecture: six beginner phases overlay the
existing detailed Journey, Completion Goals stay read-only/non-scoring, and the
validated Customs Import panel remains the specialized truth surface.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
JOURNEY = (ROOT / "component/src/components/ShipmentJourney.tsx").read_text(encoding="utf-8")
GOALS = (ROOT / "component/src/components/ShipmentCompletionGoals.tsx").read_text(encoding="utf-8")
DETAIL = (ROOT / "component/src/pages/ShipmentDetail.tsx").read_text(encoding="utf-8")
MAP = (ROOT / "component/src/components/JourneyMap.tsx").read_text(encoding="utf-8")


class SixPhaseContract(unittest.TestCase):
    def test_exact_beginner_phase_labels_exist(self):
        labels = ["HỒ SƠ", "ĐẦU ĐI", "CHẶNG CHÍNH", "NHẬP KHẨU", "GIAO HÀNG", "HOÀN TẤT"]
        positions = [JOURNEY.index(f"label: '{label}'") for label in labels]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('data-testid="journey-phase-strip"', JOURNEY)

    def test_detailed_nodes_are_not_replaced(self):
        for node in ["booking", "customs-export", "si-vgm", "gate-in", "etd",
                     "on-board", "transit", "arrival", "customs-import", "delivery"]:
            self.assertIn(f"'{node}'", JOURNEY)
        self.assertIn("<JourneyMap", JOURNEY)


class CustomsImportPreservation(unittest.TestCase):
    def test_specialized_truth_panel_survives_visual_reconciliation(self):
        self.assertIn("function CustomsImportQuickPanel", JOURNEY)
        self.assertIn("selected.id === 'customs-import'", JOURNEY)
        for marker in [
            "ci-registration-clearance", "ci-primary-cta", "ci-partners",
            "ci-partner-suggested", "ci-open-workspace",
        ]:
            self.assertIn(marker, JOURNEY)
        self.assertIn("no canonical", JOURNEY)
        self.assertIn("invoice prerequisite", JOURNEY)


class CompletionGoalsContract(unittest.TestCase):
    def test_cockpit_is_mounted_before_completion_review(self):
        attention = DETAIL.index("<AttentionNow")
        journey = DETAIL.index("<ShipmentJourney")
        goals = DETAIL.index("<ShipmentCompletionGoals")
        self.assertLess(attention, journey)
        self.assertLess(journey, goals)

    def test_read_only_goal_dimensions_exist(self):
        for goal_id in [
            "profile", "origin", "main", "import-delivery", "documents", "finance", "modules"
        ]:
            self.assertIn(f"id: '{goal_id}'", GOALS)
        for state in ["EVIDENCED", "ACTION", "UNKNOWN", "NOT_APPLICABLE"]:
            self.assertIn(state, GOALS)

    def test_no_fake_close_or_percentage_contract(self):
        self.assertIn("không phải % hoàn thành hay trạng thái CLOSED", GOALS)
        self.assertIn("UNKNOWN được giữ nguyên, không đổi thành 0/đã trả", GOALS)
        self.assertNotIn("completionPercent", GOALS)
        self.assertNotIn("healthScore", GOALS)

    def test_open_or_unknown_finance_is_not_green_by_presence_alone(self):
        self.assertIn("customerOutstanding !== 0", GOALS)
        self.assertIn("knownPartnerRemaining.some(v => v !== 0)", GOALS)
        self.assertIn("state: financeOpen ? 'ACTION' : partnerUnknown ? 'UNKNOWN'", GOALS)

    def test_journey_terminal_is_review_not_fake_whole_shipment_completion(self):
        self.assertNotIn("terminalComplete", MAP)
        self.assertNotIn(">COMPLETED</span>", MAP)
        self.assertIn("RÀ SOÁT HOÀN TẤT", MAP)


class BeginnerQuickPanelContract(unittest.TestCase):
    def test_required_operator_questions_are_visible(self):
        quick = (ROOT / "component/src/components/JourneyQuickPanel.tsx").read_text(encoding="utf-8")
        for label in ["CẦN LÀM", "CẦN CÓ", "HẠN", "CHỜ AI", "NGƯỜI THEO", "DONE WHEN", "BLOCKER"]:
            self.assertIn(label, quick)
        self.assertIn("journey-open-workspace", quick)


if __name__ == "__main__":
    unittest.main()
