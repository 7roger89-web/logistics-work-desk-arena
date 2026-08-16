"""Focused opening-impact gates for the LOG-C06 cutover review."""

from __future__ import annotations

import unittest

from core.historical_cutover_sufficiency import (
    CATEGORY_EMBEDDED,
    CATEGORY_MATERIAL,
    CATEGORY_NON_MATERIAL,
    CATEGORY_POST_CONFIRMED,
    CATEGORY_POST_REVIEW,
    CATEGORY_REFERENCE,
    VERIFIED_BASE_AMOUNT,
    VERIFIED_SOURCE_HASH,
    build_cutover_sufficiency,
)


def _item(
    source_row: int,
    amount: float | None,
    *,
    status: str = "REVIEW_REQUIRED",
    currency: str = "CNY",
    event_type: str = "unknown",
    raw_values: dict[str, object] | None = None,
    source_file_hash: str = VERIFIED_SOURCE_HASH,
    shipment_id: str | None = None,
) -> dict:
    return {
        "source_item_id": f"sufficiency-{source_row}",
        "source_file_hash": source_file_hash,
        "sheet": "Sheet2",
        "source_row": source_row,
        "source_reference": f"Sheet2!row {source_row}",
        "raw_amount": amount,
        "raw_currency": currency,
        "raw_values": raw_values or {},
        "raw_date": None,
        "inherited_date_context": None,
        "raw_note": "fixture",
        "raw_text": "fixture",
        "review_status": status,
        "proposal": {
            "amount": amount,
            "currency": currency,
            "event_type": event_type,
            "shipment_id": shipment_id,
        },
    }


class HistoricalCutoverSufficiencyTests(unittest.TestCase):
    def test_embedded_pre_base_row_does_not_block(self):
        result = build_cutover_sufficiency(
            [_item(50, 24576, raw_values={"C50": "Thành"})]
        )
        self.assertEqual(result["items"][0]["category"], CATEGORY_EMBEDDED)
        self.assertEqual(result["unresolved_material_count"], 0)
        self.assertNotIn("UNRESOLVED_MATERIAL_ITEMS", result["readiness_reasons"])

    def test_reference_checkpoint_does_not_block(self):
        result = build_cutover_sufficiency([_item(129, 134973)])
        self.assertEqual(result["items"][0]["category"], CATEGORY_REFERENCE)
        self.assertEqual(result["supersession_graph"]["checkpoint_events_counted"], 0)

    def test_superseded_checkpoint_is_not_applied_as_an_event(self):
        result = build_cutover_sufficiency([_item(86, 99824.43)])
        self.assertEqual(result["items"][0]["category"], CATEGORY_REFERENCE)
        self.assertEqual(result["candidate_opening"]["amount"], float(VERIFIED_BASE_AMOUNT))
        graph = result["supersession_graph"]
        self.assertEqual(graph["checkpoint_events_counted"], 0)
        self.assertIn("SUPERSEDED_M89_170374_18739944347", {node["id"] for node in graph["nodes"]})

    def test_post_base_confirmed_event_changes_candidate_once(self):
        result = build_cutover_sufficiency([_item(201, 100, status="CONFIRMED")])
        self.assertEqual(result["items"][0]["category"], CATEGORY_POST_CONFIRMED)
        self.assertEqual(result["candidate_opening"]["amount"], float(VERIFIED_BASE_AMOUNT + 100))
        self.assertEqual(len(result["post_base_confirmed_events"]), 1)

    def test_post_base_unresolved_material_event_blocks_readiness(self):
        result = build_cutover_sufficiency([_item(201, 100)])
        self.assertEqual(result["items"][0]["category"], CATEGORY_POST_REVIEW)
        self.assertEqual(result["unresolved_material_count"], 0)
        self.assertIn("POST_BASE_REVIEW_REQUIRED", result["readiness_reasons"])
        self.assertEqual(result["readiness"], "NOT_READY")

    def test_pre_base_unresolved_metadata_does_not_block(self):
        result = build_cutover_sufficiency([_item(96, 10, currency="UNKNOWN")])
        self.assertEqual(result["items"][0]["category"], CATEGORY_NON_MATERIAL)
        self.assertEqual(result["unresolved_material_count"], 0)
        self.assertNotIn("OPENING_CURRENCY_UNKNOWN", result["readiness_reasons"])

    def test_unknown_shipment_link_alone_does_not_block(self):
        result = build_cutover_sufficiency(
            [_item(102, 62464, status="CONFIRMED", shipment_id="UNKNOWN")]
        )
        self.assertEqual(result["items"][0]["category"], CATEGORY_EMBEDDED)
        self.assertEqual(result["unresolved_material_count"], 0)
        self.assertNotIn("POST_BASE_REVIEW_REQUIRED", result["readiness_reasons"])

    def test_unknown_currency_blocks_only_when_opening_material(self):
        nonmaterial = build_cutover_sufficiency([_item(96, 10, currency="UNKNOWN")])
        material = build_cutover_sufficiency(
            [_item(229, 5610, currency="UNKNOWN", raw_values={"N229": 5610, "O229": "Thành"})]
        )
        self.assertNotIn("OPENING_CURRENCY_UNKNOWN", nonmaterial["readiness_reasons"])
        self.assertEqual(material["items"][0]["category"], CATEGORY_POST_REVIEW)
        self.assertIn("OPENING_CURRENCY_UNKNOWN", material["readiness_reasons"])

    def test_candidate_formula_reproducible_for_increase_and_reduction(self):
        result = build_cutover_sufficiency(
            [
                _item(201, 100, status="CONFIRMED"),
                _item(202, -20, status="CONFIRMED"),
            ]
        )
        self.assertEqual(result["candidate_opening"]["verified_base"], float(VERIFIED_BASE_AMOUNT))
        self.assertEqual(result["candidate_opening"]["post_base_confirmed_increases"], 100.0)
        self.assertEqual(result["candidate_opening"]["post_base_confirmed_reductions"], 20.0)
        self.assertEqual(result["candidate_opening"]["amount"], float(VERIFIED_BASE_AMOUNT + 80))

    def test_canonical_mutation_oracle_is_zero(self):
        result = build_cutover_sufficiency([_item(201, 100, status="CONFIRMED")])
        self.assertEqual(result["canonical_mutation_oracle"]["canonical_writes"], 0)
        self.assertEqual(result["canonical_mutation_oracle"]["canonical_collections_touched"], [])
        self.assertFalse(result["canonical_mutation_oracle"]["opening_published"])
        self.assertEqual(result["cutover_lock"], "NOT_APPROVED / NOT_LIVE")


if __name__ == "__main__":
    unittest.main()
