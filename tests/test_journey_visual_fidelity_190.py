"""Issue #190 — approved Journey fidelity + compact support-sale triage.

These source-contract checks pin the Owner's production review:
- urgency is driven by canonical Attention bands, never text heuristics;
- canonical shipment owner is shown as responsibility, updated_by stays secondary;
- fresh zero-node Journey is compact;
- full-lot workspace collapses the map before embedding existing forms;
- completion review is compact by default and explicitly not create-lot input.
Real Chromium comparison against PR177 remains mandatory before acceptance.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent
SHIPMENTS = (ROOT / "component/src/pages/Shipments.tsx").read_text(encoding="utf-8")
JOURNEY = (ROOT / "component/src/components/ShipmentJourney.tsx").read_text(encoding="utf-8")
GOALS = (ROOT / "component/src/components/ShipmentCompletionGoals.tsx").read_text(encoding="utf-8")
CSS = (ROOT / "component/src/index.css").read_text(encoding="utf-8")


class ShipmentListTriage(unittest.TestCase):
    def test_alerts_use_attention_authority_not_wording(self):
        self.assertIn('const { shipments, attention } = useStore();', SHIPMENTS)
        self.assertIn('BLOCKING: 0, OVERDUE: 1, DUE_SOON: 2', SHIPMENTS)
        self.assertIn('alertByShipment', SHIPMENTS)
        self.assertNotIn('includes("free time")', SHIPMENTS.lower())

    def test_responsibility_distinguishes_owner_from_last_writer(self):
        self.assertIn('Phụ trách: <b>{s.sale}</b>', SHIPMENTS)
        self.assertIn('Cập nhật bởi: <b>{s.support || "—"}</b>', SHIPMENTS)


class JourneyDensity(unittest.TestCase):
    def test_fresh_zero_node_shell_is_compact(self):
        self.assertIn("journey-split journey-split-fresh", JOURNEY)
        self.assertIn(".journey-split-fresh { height: 500px; }", CSS)
        self.assertIn(".journey-split-fresh .journey-canvas { height: 430px; }", CSS)

    def test_global_workspace_reuses_collapsed_map_rail(self):
        self.assertIn("setPanelMode('global');", JOURNEY)
        self.assertIn("setMapCollapsed(true);", JOURNEY)
        self.assertIn("journey-split-collapsed", JOURNEY)

    def test_populated_default_restores_original_composition(self):
        populated = JOURNEY.split("export default function ShipmentJourney", 1)[1]
        self.assertNotIn('data-testid="journey-phase-strip"', populated)
        self.assertNotIn('data-testid="journey-map-toolbar"', populated)
        self.assertIn("globalActive ? 'global' : 'quick'", populated)
        self.assertIn('data-testid="journey-summary-cards"', populated)
        for idx in range(1, 6):
            self.assertIn(f'journey-summary-card-{idx}', populated)


class CompletionReviewDensity(unittest.TestCase):
    def test_completion_review_is_collapsed_by_default(self):
        self.assertIn("const [open, setOpen] = useState(false);", GOALS)
        self.assertIn('data-testid="completion-goal-toggle"', GOALS)
        self.assertIn('data-testid="completion-goal-details"', GOALS)

    def test_completion_copy_says_not_create_fields(self):
        self.assertIn("không phải các trường bắt buộc phải điền khi tạo lô", GOALS)
        self.assertIn("không phải trạng thái CLOSED", GOALS)


if __name__ == "__main__":
    unittest.main()
