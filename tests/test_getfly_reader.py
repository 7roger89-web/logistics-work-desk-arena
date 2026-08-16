import io
import sys
import types
import unittest

import pandas as pd

try:
    import streamlit  # noqa: F401
except ImportError:
    streamlit = types.ModuleType("streamlit")
    sys.modules["streamlit"] = streamlit

from core.getfly_reader import process_getfly_excel


class GetFlyReaderTests(unittest.TestCase):
    def test_vietnamese_money_and_forward_fill(self):
        source = pd.DataFrame(
            {
                "Mã ĐH": ["GF-001", None],
                "Ngày đặt hàng": ["29/07/2026", None],
                "Tên KH": ["Công ty ABC", None],
                "Tên SP": ["Dịch vụ A", "Dịch vụ B"],
                "Số lượng": ["1", "2"],
                "Giá vốn": ["1.000.000", "500,000"],
                "Đơn giá bán": ["1.500.000", "750,000"],
                "Thành tiền": ["1.500.000", "1.500.000"],
            }
        )
        buffer = io.BytesIO()
        source.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)

        parsed, error = process_getfly_excel(buffer)
        self.assertIsNone(error)
        self.assertEqual(parsed.loc[1, "order_id"], "GF-001")
        self.assertEqual(parsed.loc[0, "cost"], 1_000_000)
        self.assertEqual(parsed.loc[1, "price"], 750_000)
        self.assertEqual(parsed["revenue"].sum(), 3_000_000)


if __name__ == "__main__":
    unittest.main()
