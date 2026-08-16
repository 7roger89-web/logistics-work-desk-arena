"""Focused tests for the LOG-C06 P6 blocker reconstruction."""

from __future__ import annotations

import unittest

from core.historical_cutover_sufficiency import (
    CATEGORY_POST_REVIEW,
    CATEGORY_REFERENCE,
    VERIFIED_SOURCE_HASH,
    build_cutover_sufficiency,
)
from core.log_c06_p6_reconciliation import build_p6_reconciliation


def _item(source_row: int, *, status: str = "REVIEW_REQUIRED", raw_values=None, raw_date=None):
    return {
        "source_item_id": f"p6-{source_row}",
        "source_file_hash": VERIFIED_SOURCE_HASH,
        "sheet": "Sheet2",
        "source_row": source_row,
        "source_reference": f"Sheet2!row {source_row}",
        "raw_date": raw_date,
        "inherited_date_context": raw_date,
        "raw_values": raw_values or {},
        "review_status": status,
        "raw_text": "fixture",
        "raw_note": "fixture",
        "proposal": {
            "amount": None,
            "currency": "UNKNOWN",
            "classification": "unknown",
            "event_type": "unknown",
        },
    }


class LogC06P6ReconciliationTests(unittest.TestCase):
    def test_goods_detail_is_reference_only_and_not_material(self):
        goods_amounts = [507, 1713.36, 295.1, 6749.6, 4102.8, 3456.7, 105]
        rows = [
            _item(
                row,
                status="NOT_APPLICABLE",
                raw_values={f"I{row + 1}": amount, f"O{row + 1}": "Thành"},
            )
            for row, amount in zip(range(213, 220), goods_amounts)
        ]
        rows.append(
            _item(
                224,
                raw_values={"H225": "thành", "I225": 16929.56},
            )
        )

        result = build_cutover_sufficiency(rows)
        by_row = {item["source_row"]: item for item in result["items"]}
        self.assertTrue(all(by_row[row]["category"] == CATEGORY_REFERENCE for row in range(213, 220)))
        self.assertTrue(all(by_row[row]["amount"] is None for row in range(213, 220)))
        self.assertEqual(result["unresolved_material_count"], 0)
        self.assertEqual(result["p6_reconciliation"]["goods_213_219"]["subtotal_amount"], 16929.56)
        self.assertTrue(result["p6_reconciliation"]["goods_213_219"]["subtotal_exact_match"])

    def test_transfer_table_keeps_c_and_d_legs_separate(self):
        rows = [
            _item(
                row,
                raw_date="2026-05-29" if row == 201 else "2026-05-30",
                raw_values={
                    f"B{row + 1}": 46171 if row == 201 else 46172,
                    f"C{row + 1}": f"{vnd} VND",
                    f"D{row + 1}": converted,
                    **({f"E{row + 1}": on_behalf} if on_behalf is not None else {}),
                },
            )
            for row, vnd, converted, on_behalf in (
                (201, 400000000, 102616.72652642381, 102695),
                (202, 300000000, 76962.54489481785, 205391),
                (203, 500000000, 128270.90815802976, None),
                (204, 330200000, 84710.10774756286, 84704),
                (205, 920000, 236.01847101077476, None),
            )
        ]
        reconstruction = build_p6_reconciliation(rows)["transfer_201_205"]
        self.assertEqual(reconstruction["totals"]["chuyen_ho_cny"], 392790.0)
        self.assertEqual(reconstruction["totals"]["vnd_input"], 1531120000.0)
        self.assertNotEqual(
            reconstruction["totals"]["hach_ra_tien_te_cny"],
            reconstruction["totals"]["chuyen_ho_cny"],
        )
        self.assertEqual(len(reconstruction["groups"]), 3)

    def test_freight_rows_reconstruct_one_subtotal_and_unknown_currency(self):
        rows = [
            _item(
                229,
                raw_date="2026-06-10",
                raw_values={"D230": 46183, "E230": "Bàn làm việc", "N230": 5610, "O230": "Thành"},
            ),
            _item(
                230,
                raw_date="2026-06-22",
                raw_values={"D231": 46195, "E231": "1 thùng gỗ", "N231": 1450, "O231": "Thành"},
            ),
        ]
        rows.append(_item(235, raw_values={"M236": "thành", "N236": 7060}))
        result = build_p6_reconciliation(rows)
        freight = result["freight_229_230"]
        self.assertEqual(freight["row_total_sum"], 7060.0)
        self.assertTrue(freight["subtotal_exact_match"])
        self.assertEqual(freight["currency"], "UNKNOWN")
        self.assertEqual(freight["direction"], "UNKNOWN")

        sufficiency = build_cutover_sufficiency(rows[:2])
        by_row = {item["source_row"]: item for item in sufficiency["items"]}
        self.assertTrue(all(by_row[row]["category"] == CATEGORY_POST_REVIEW for row in (229, 230)))
        self.assertIn("OPENING_CURRENCY_UNKNOWN", sufficiency["readiness_reasons"])

    def test_p6_owner_pack_has_two_grouped_questions_and_no_mutation(self):
        result = build_p6_reconciliation([])
        pack = result["beginner_owner_decision_pack"]
        self.assertEqual(pack["decision_count"], 2)
        self.assertTrue(pack["only_genuine_unresolved_items"])
        self.assertEqual(result["canonical_mutation_oracle"]["canonical_writes"], 0)
        self.assertFalse(result["canonical_mutation_oracle"]["opening_published"])
        self.assertEqual(result["temporal_boundary"]["proposed_opening_as_of_date"], "2026-05-28")
        self.assertEqual(result["residual_1572_vs_1578_5474"]["opening_effect"], 0.0)


if __name__ == "__main__":
    unittest.main()
