from __future__ import annotations

import unittest

from views.tariff import cbpg_exclusion_options, normalize_cbpg_items


class TariffEditorTests(unittest.TestCase):
    def test_rows_are_sequential_after_dynamic_edits(self):
        rows, repairs = normalize_cbpg_items([
            {"ID": 99, "Loại Hàng": "Bàn", "Ngoại trừ": "Mặt bàn hình tròn"},
            {"ID": 2, "Loại Hàng": "Ghế", "Ngoại trừ": "Chân nhôm (Ghế)"},
        ])
        self.assertEqual([row["ID"] for row in rows], [1, 2])
        self.assertEqual(repairs, [])

    def test_chair_and_table_have_different_specific_choices(self):
        chair = cbpg_exclusion_options("Ghế")
        table = cbpg_exclusion_options("Bàn")
        self.assertIn("Chân nhôm (Ghế)", chair)
        self.assertNotIn("Chân nhôm (Ghế)", table)
        self.assertIn("Mặt bàn hình tròn", table)
        self.assertNotIn("Mặt bàn hình tròn", chair)

    def test_incompatible_legacy_exception_is_cleared(self):
        rows, repairs = normalize_cbpg_items([
            {"ID": 7, "Loại Hàng": "Ghế", "Ngoại trừ": "Mặt bàn hình tròn"},
        ])
        self.assertEqual(rows[0]["Ngoại trừ"], "Không")
        self.assertTrue(repairs)


if __name__ == "__main__":
    unittest.main()
