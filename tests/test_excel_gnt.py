import unittest

# Stub Streamlit because the pure helper does not use UI.
try:
    import streamlit  # noqa: F401
except ImportError:
    import sys
    import types
    streamlit = types.ModuleType("streamlit")
    sys.modules["streamlit"] = streamlit

from core.excel_gnt import parse_tax_amount_vnd


class GntMoneyTests(unittest.TestCase):
    def test_streamlit_float_is_not_multiplied(self):
        self.assertEqual(parse_tax_amount_vnd(1_000_000.0), 1_000_000)

    def test_vietnamese_formatted_money(self):
        self.assertEqual(parse_tax_amount_vnd("1.234.567"), 1_234_567)


if __name__ == "__main__":
    unittest.main()
