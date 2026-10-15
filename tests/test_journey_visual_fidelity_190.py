"""Issue #190 — approved Journey fidelity + compact support-sale triage.

These source-contract checks pin the Owner's production review:
- urgency is driven by canonical Attention bands, never text heuristics;
- canonical shipment owner is shown as responsibility, updated_by stays secondary;
- zero-node Journey is a full-width map-first empty state with no fake nodes;
- full-lot workspace keeps the map beside existing forms (Owner 13/10);
- completion review is compact by default and explicitly not create-lot input.
Real Chromium comparison against the Owner reference remains mandatory before acceptance.
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
    def test_customs_panel_order_and_fixed_footer_contract(self):
        next_action = JOURNEY.index('data-testid="ci-next-action"')
        registration = JOURNEY.index('data-testid="ci-registration-clearance"')
        self.assertLess(next_action, registration)
        self.assertEqual(JOURNEY.count('data-testid="ci-primary-cta"'), 1)
        self.assertEqual(JOURNEY.count('data-testid="ci-open-workspace"'), 1)
        self.assertIn('data-testid="ci-scroll-region"', JOURNEY)
        self.assertIn('data-testid="ci-footer"', JOURNEY)
        self.assertIn('className="min-h-0 flex-1 space-y-3 overflow-auto', JOURNEY)
        self.assertIn('className="shrink-0 border-t border-slate-300', JOURNEY)
        self.assertNotIn('className="h-full overflow-auto p-4" data-testid="journey-customs-import-panel"', JOURNEY)

    def test_map_first_layout_and_zero_state_have_no_legacy_split(self):
        self.assertIn('.journey-split.journey-map-first .journey-canvas', CSS)
        self.assertIn('.journey-zero-map-first { position: relative; width: 100%; }', CSS)
        self.assertIn('.journey-zero-notice', CSS)
        self.assertNotIn('.journey-split-small-map', CSS)
        self.assertIn('min-width: 0', CSS)
        self.assertIn('@media (max-width: 1100px)', CSS)
        # Existing populated-path modules and optional attachment stay reachable.
        self.assertIn('(modules.length > 0 || attachOpen)', JOURNEY)
        self.assertIn('data-testid="journey-add-module"', JOURNEY)
        self.assertIn('setAttachOpen(true)', JOURNEY)

    def test_fresh_zero_node_shell_is_full_width_and_truthful(self):
        zero = JOURNEY.split('function ZeroNodeJourney', 1)[1].split('export default function ShipmentJourney', 1)[0]
        self.assertIn('data-testid="journey-zero-map-first"', zero)
        self.assertIn('data-layout="full-width"', zero)
        self.assertIn('journey-map-first journey-zero-map-first', zero)
        self.assertIn('<JourneyMap shipment={s} nodes={[]}', zero)
        self.assertIn('Chưa có sơ đồ Journey', zero)
        self.assertIn('Đang ở: Chưa xác định', zero)
        self.assertIn('Hồ sơ lô còn thiếu', zero)
        self.assertEqual(zero.count('data-testid="journey-zero-primary-cta"'), 1)
        self.assertNotIn('journey-zero-panel', zero)
        self.assertNotIn('journey-split-small-map', zero)
        self.assertNotIn('journey-phase-strip', zero)
        self.assertIn('{children}', zero)  # Global Workspace keeps the editor reachable

    def test_global_workspace_reuses_collapsed_map_rail(self):
        # SUPERSEDED: Owner explicitly rejected collapsing to a list rail.
        global_open = JOURNEY.split('const openGlobal =', 1)[1].split('// Issue #190', 1)[0]
        self.assertIn("setPanelMode('global');", global_open)
        self.assertNotIn('setMapCollapsed', global_open)
        self.assertIn('collapsed={false}', JOURNEY)
        self.assertIn('data-testid="journey-global-workspace"', JOURNEY)
        self.assertIn("label:'Nhập & Giao'", JOURNEY)
        self.assertIn('{children}', JOURNEY)

    def test_populated_default_restores_original_composition(self):
        # SUPERSEDED summary cards; persistent map + overview, then stage panels.
        populated = JOURNEY.split("export default function ShipmentJourney", 1)[1]
        self.assertNotIn('data-testid="journey-phase-strip"', populated)
        self.assertNotIn('data-testid="journey-summary-cards"', populated)
        self.assertIn("globalActive ? 'global' : 'overview'", populated)
        self.assertIn('data-testid="journey-overview-panel"', populated)
        self.assertIn('data-testid="journey-stage-workspace"', populated)
        self.assertIn("setPanelMode('quick')", populated)
        # Canonical facts drive status/action, not summary card position.
        self.assertIn('journey?.primaryAction.text', populated)
        self.assertIn("n.state === 'PROBLEM'", populated)


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
