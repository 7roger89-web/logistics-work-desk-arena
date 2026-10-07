"""Issue #188 — production parity for a brand-new shipment.

The bug was an early return in ShipmentJourney: a truthful zero-node Journey
removed the whole approved cockpit and exposed the legacy vertical shipment
page. These source-contract tests pin the fail-closed UI shape; real browser
acceptance is still mandatory before merge.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
JOURNEY = (ROOT / "component/src/components/ShipmentJourney.tsx").read_text(encoding="utf-8")
DETAIL = (ROOT / "component/src/pages/ShipmentDetail.tsx").read_text(encoding="utf-8")


class FreshShipmentCockpitContract(unittest.TestCase):
    def test_zero_nodes_keep_the_cockpit_shell(self):
        self.assertIn("function FreshShipmentCockpit", JOURNEY)
        self.assertIn('data-empty-journey="true"', JOURNEY)
        self.assertIn('data-testid="journey-empty-canvas"', JOURNEY)
        self.assertIn('data-testid="journey-phase-strip"', JOURNEY)
        self.assertIn('data-testid="journey-side-panel"', JOURNEY)
        self.assertNotIn("Chưa có công đoạn phù hợp. Bổ sung phạm vi dịch vụ", JOURNEY)

    def test_empty_state_has_six_universal_phases_and_one_profile_action(self):
        for label in ["HỒ SƠ", "ĐẦU ĐI", "CHẶNG CHÍNH", "NHẬP KHẨU", "GIAO HÀNG", "HOÀN TẤT"]:
            self.assertIn(f"label: '{label}'", JOURNEY)
        self.assertIn('data-testid="journey-empty-primary-cta"', JOURNEY)
        self.assertIn("onClick={runPrimary}", JOURNEY)
        self.assertIn("data-state={actionable ? 'ACTION' : 'UNKNOWN'}", JOURNEY)
        self.assertIn("disabled={!actionable}", JOURNEY)

    def test_empty_state_does_not_fabricate_mode_specific_detailed_nodes(self):
        start = JOURNEY.index("function FreshShipmentCockpit")
        end = JOURNEY.index("export default function ShipmentJourney")
        empty = JOURNEY[start:end]
        for detailed in ["booking", "si-vgm", "gate-in", "customs-import", "on-board"]:
            self.assertNotIn(f"id: '{detailed}'", empty)

    def test_cockpit_precedes_completion_review_on_the_page(self):
        attention = DETAIL.index("<AttentionNow")
        journey = DETAIL.index("<ShipmentJourney")
        goals = DETAIL.index("<ShipmentCompletionGoals")
        self.assertLess(attention, journey)
        self.assertLess(journey, goals)


if __name__ == "__main__":
    unittest.main()
