"""Pure per-currency opening and cutover-draft tests for LOG-C06."""

from __future__ import annotations

import unittest
from pathlib import Path

from core.historical_opening import (
    ALLOWED_DRAFT_STATUSES,
    build_cutover_draft,
    build_draft_opening_position,
    reconcile_checkpoints,
)


def _row(
    source_item_id: str,
    amount: float,
    *,
    status: str = "CONFIRMED",
    currency: str = "CNY",
    event_type: str = "payable_to_a_bo",
    bucket: str | None = None,
    proposal_extra: dict | None = None,
) -> dict:
    proposal = {
        "amount": amount,
        "currency": currency,
        "event_type": event_type,
        "candidate_bucket": bucket,
        "anomalies": [],
    }
    proposal.update(proposal_extra or {})
    return {
        "source_item_id": source_item_id,
        "source_file_hash": "fixture-hash",
        "sheet": "Sheet2",
        "source_row": int(source_item_id.rsplit("-", 1)[-1].strip("abc")) if source_item_id.rsplit("-", 1)[-1].strip("abc").isdigit() else 1,
        "source_cell_range": "D1:D1",
        "source_reference": f"Sheet2!D{source_item_id}",
        "raw_amount": amount,
        "review_status": status,
        "anomaly_flags": [],
        "proposal": proposal,
    }


class HistoricalOpeningTests(unittest.TestCase):
    def test_confirmed_components_are_currency_separated_and_explicitly_bucketed(self):
        items = [
            _row("cny-payable-1", 100),
            _row("cny-credit-2", 20, event_type="refund_return_credit"),
            _row("cny-received-3", 30, event_type="received_on_behalf"),
            _row("cny-paid-4", -10, event_type="paid_on_behalf"),
            _row("usd-unallocated-5", 7, currency="USD", event_type="unallocated"),
            _row("vnd-fx-6", 25297.2426, currency="CNY", event_type="fx_conversion_context", proposal_extra={"related_amount": 100000000, "related_currency": "VND", "fx_rate": 3953}),
            _row("unknown-7", 99, currency="UNKNOWN"),
            _row("review-8", 999, status="REVIEW_REQUIRED"),
            _row("checkpoint-9", 50, proposal_extra={"checkpoint_key": "THANH_ACCUMULATED", "restriction": "historical_checkpoint"}),
        ]
        position = build_draft_opening_position(items)
        cny = position["currencies"]["CNY"]["buckets"]
        usd = position["currencies"]["USD"]["buckets"]
        self.assertEqual(cny["payable_to_a_bo"]["amount"], 100.0)
        self.assertEqual(cny["held_credit"]["amount"], 20.0)
        self.assertEqual(cny["received_on_behalf_available"]["amount"], 30.0)
        self.assertEqual(cny["paid_on_behalf_settled"]["amount"], -10.0)
        self.assertEqual(cny["restricted_confirmed"]["amount"], 25297.2426)
        self.assertEqual(usd["unallocated_confirmed"]["amount"], 7.0)
        self.assertIsNone(position["cross_currency_total"])
        self.assertIn("checkpoint-9", position["excluded_source_item_ids"])
        self.assertIn("unknown-7", position["excluded_source_item_ids"])
        self.assertEqual(position["counts"]["confirmed_components"], 6)

    def test_proposed_unknown_and_checkpoint_rows_never_enter_confirmed_position(self):
        items = [
            _row("confirmed-1", 10),
            _row("proposed-2", 20, status="PROPOSED"),
            _row("unknown-event-3", 30, proposal_extra={"event_type": "unknown"}),
            _row("checkpoint-4", 40, proposal_extra={"checkpoint_key": "THANH_ACCUMULATED"}),
        ]
        position = build_draft_opening_position(items)
        self.assertEqual(position["counts"]["confirmed_components"], 1)
        excluded = {item["source_item_id"]: item["reason"] for item in position["excluded"]}
        self.assertEqual(excluded["proposed-2"], "PROPOSED_NOT_CONFIRMED")
        self.assertEqual(excluded["unknown-event-3"], "UNKNOWN_OR_UNALLOCATED_EVENT")
        self.assertEqual(excluded["checkpoint-4"], "CHECKPOINT_NOT_COMPONENT")

    def test_checkpoint_reconciliation_requires_explicit_linkage_and_formula(self):
        components = [_row("component-1", 10), _row("component-2", 20)]
        exact_checkpoint = _row(
            "checkpoint-3",
            30,
            status="REVIEW_REQUIRED",
            event_type="adjustment",
            proposal_extra={
                "checkpoint_key": "THANH_ACCUMULATED",
                "checkpoint_component_ids": ["component-1", "component-2"],
                "checkpoint_operation": "sum",
            },
        )
        exact = reconcile_checkpoints(components + [exact_checkpoint])
        self.assertEqual(exact[0]["status"], "EXACT_MATCH")
        self.assertEqual(exact[0]["difference"], 0.0)

        difference_checkpoint = dict(exact_checkpoint)
        difference_checkpoint["source_item_id"] = "checkpoint-4"
        difference_checkpoint["proposal"] = dict(exact_checkpoint["proposal"])
        difference_checkpoint["proposal"]["amount"] = 31
        difference = reconcile_checkpoints(components + [difference_checkpoint])
        self.assertEqual(difference[0]["status"], "DIFFERENCE")
        self.assertEqual(difference[0]["difference"], -1.0)

        unknown_checkpoint = _row(
            "checkpoint-5",
            30,
            status="REVIEW_REQUIRED",
            event_type="adjustment",
            proposal_extra={"checkpoint_key": "THANH_ACCUMULATED"},
        )
        unknown = reconcile_checkpoints(components + [unknown_checkpoint])
        self.assertEqual(unknown[0]["status"], "UNKNOWN_SEMANTICS")

    def test_cutover_draft_is_reproducible_and_never_approved_or_live(self):
        items = [_row("confirmed-1", 10), _row("confirmed-2", 20, currency="USD")]
        first = build_cutover_draft(
            items,
            proposed_cutover_date="2026-04-01",
            generated_by="local-review",
            draft_version=2,
            generated_at="2026-08-15T02:00:00+00:00",
        )
        second = build_cutover_draft(
            items,
            proposed_cutover_date="2026-04-01",
            generated_by="another-render",
            draft_version=2,
            generated_at="2026-08-15T03:00:00+00:00",
        )
        self.assertEqual(first["snapshot_hash"], second["snapshot_hash"])
        self.assertEqual(first["draft_id"], second["draft_id"])
        self.assertEqual(first["cutover_readiness"], "READY")
        self.assertEqual(first["status"], "READY_FOR_OWNER_REVIEW")
        self.assertIn(first["status"], ALLOWED_DRAFT_STATUSES)
        self.assertEqual(first["canonical_mutations"], 0)
        self.assertTrue(first["owner_confirmation_required"])
        self.assertEqual(first["approval_status"], "NOT_APPROVED")
        self.assertEqual(first["live_status"], "NOT_LIVE")
        self.assertEqual(first["position_by_currency"]["CNY"]["buckets"]["held_credit"]["amount"], 0.0)

    def test_cutover_with_review_or_unknown_currency_is_not_ready_but_remains_a_draft(self):
        items = [
            _row("confirmed-1", 10),
            _row("review-2", 20, status="REVIEW_REQUIRED"),
            _row("unknown-3", 30, currency="UNKNOWN"),
        ]
        draft = build_cutover_draft(
            items,
            proposed_cutover_date="2026-04-01",
            generated_by="local-review",
        )
        self.assertEqual(draft["cutover_readiness"], "NOT_READY")
        self.assertEqual(draft["status"], "DRAFT")
        self.assertIn("REVIEW_REQUIRED_ITEMS_REMAIN", draft["readiness_reasons"])
        self.assertIn("UNKNOWN_CURRENCY_REMAINS", draft["readiness_reasons"])
        self.assertNotIn("APPROVED", draft["allowed_statuses"])
        self.assertNotIn("LIVE", draft["allowed_statuses"])

    def test_opening_module_has_no_database_or_canonical_ledger_dependency(self):
        source = Path(__file__).resolve().parents[1] / "core" / "historical_opening.py"
        text = source.read_text(encoding="utf-8")
        self.assertNotIn("core.database", text)
        self.assertNotIn("financial_ledger", text)
        self.assertNotIn("get_db", text)


if __name__ == "__main__":
    unittest.main()
