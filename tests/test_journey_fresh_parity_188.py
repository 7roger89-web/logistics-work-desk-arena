"""Issue #188 — production parity for a brand-new shipment.

The bug was an early return in ShipmentJourney: a truthful zero-node Journey
removed the whole approved cockpit and exposed the legacy vertical shipment
page. These source-contract tests pin the fail-closed UI shape; real browser
acceptance is still mandatory before merge.
"""
from pathlib import Path
import json
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parent.parent
JOURNEY = (ROOT / "component/src/components/ShipmentJourney.tsx").read_text(encoding="utf-8")
DETAIL = (ROOT / "component/src/pages/ShipmentDetail.tsx").read_text(encoding="utf-8")
FRESH_FIXTURE = ROOT / "tests/component/fixtures/view_model_journey_fresh_188.json"
FRESH_DOM_LANE = ROOT / "tests/component/dom_acceptance_journey_fresh_188.mjs"
DIST = ROOT / "component/dist/logi-shell.js"


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


class ZeroNodeRenderLane(unittest.TestCase):
    """Issue #188 root cause C: the zero-node render path must actually EXECUTE.

    The source contracts above prove labels exist. This lane mounts the exact
    committed ``component/dist`` bundle over a real fresh-shipment projection
    (created through the canonical ``shipment_create`` handler on isolated
    mongomock staging) and executes the production shape that was never
    rendered. It skips only when the local toolchain cannot run it at all.
    """

    def test_fresh_fixture_is_a_truthful_zero_node_shipment(self):
        fixture = json.loads(FRESH_FIXTURE.read_text(encoding="utf-8"))
        meta = fixture["meta"]
        self.assertEqual(meta["journeyNodes"], 0)
        self.assertIs(meta["serviceScopeConfirmed"], False)
        self.assertEqual(meta["serviceScope"], [])
        self.assertEqual(meta["firstMode"], "")
        self.assertEqual(meta["incoterm"], "")
        self.assertEqual(meta["transportLegs"], 0)
        self.assertEqual(meta["profileState"], "PROFILE_INCOMPLETE")
        self.assertTrue(meta["persisted"])
        row = next(s for s in fixture["before"]["shipments"] if s["id"] == meta["shipmentId"])
        self.assertEqual(row["journey"]["nodes"], [])

    def test_zero_node_render_keeps_the_cockpit_in_a_dom(self):
        node = shutil.which("node")
        if node is None:  # pragma: no cover - environment without node
            self.skipTest("node unavailable")
        if not (ROOT / "component/node_modules/jsdom").exists():  # pragma: no cover
            self.skipTest("component dev dependencies not installed (run npm ci in component/)")
        if not DIST.exists():  # pragma: no cover
            self.skipTest("component dist not built")
        proc = subprocess.run(
            [node, str(FRESH_DOM_LANE), str(FRESH_FIXTURE), str(DIST)],
            cwd=str(ROOT), capture_output=True, text=True, timeout=300,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("PASS journey fresh 188", proc.stdout)


if __name__ == "__main__":
    unittest.main()
