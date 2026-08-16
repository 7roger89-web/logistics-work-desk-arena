"""Mounted LOG-C05 report/debit render and no-financial-write oracle."""

from __future__ import annotations

from contextlib import contextmanager
import unittest
from unittest.mock import patch

from core.financial_ledger import project_partner_financial_position
from tests.test_reconciliation_desk import ABO, _fixture_history
from views import partner_reconciliation as desk


class _ColumnRecorder:
    def __init__(self, parent: "_StreamlitRecorder") -> None:
        self.parent = parent

    def metric(self, *args, **kwargs):
        self.parent.calls.append(("metric", args, kwargs))

    def button(self, *args, **kwargs):
        return self.parent.button(*args, **kwargs)


class _StreamlitRecorder:
    FINANCIAL_WRITE_NAMES = {
        "save_obligation",
        "save_transaction",
        "allocate_transaction",
        "reverse_allocation",
        "insert_one",
        "update_one",
        "delete_one",
        "bulk_write",
    }

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []
        self.financial_write_count = 0

    def __getattr__(self, name: str):
        if name in self.FINANCIAL_WRITE_NAMES:
            self.financial_write_count += 1
            raise AssertionError(f"financial write method reached: {name}")

        def record(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            if name == "columns":
                count = args[0] if args else 1
                return [_ColumnRecorder(self) for _ in range(count)]
            if name == "button":
                return False
            if name == "selectbox":
                options = args[1] if len(args) > 1 else kwargs.get("options", [])
                return next(iter(options), "")
            return None

        return record

    @contextmanager
    def expander(self, *args, **kwargs):
        self.calls.append(("expander", args, kwargs))
        yield

    @contextmanager
    def spinner(self, *args, **kwargs):
        yield


class LogC05PartnerDeskWriteOracleTests(unittest.TestCase):
    def setUp(self) -> None:
        obligations, transactions, allocations = _fixture_history()
        self.position = project_partner_financial_position(
            ABO,
            obligations,
            transactions,
            allocations,
            internal_sale_owner="Thành",
        )

    def _render_mode(self, mode: str) -> _StreamlitRecorder:
        recorder = _StreamlitRecorder()

        def state_get(key, default=None):
            return mode if key == desk._VIEW_STATE_KEY else default

        with patch.object(desk, "st", recorder), patch.object(
            desk,
            "build_partner_financial_position",
            return_value=self.position,
        ), patch.object(desk, "get_db", return_value=None), patch.object(desk, "_state_get", side_effect=state_get):
            desk.ui_partner_reconciliation_desk()
        return recorder

    def test_report_action_renders_summary_explanation_and_shipments(self) -> None:
        recorder = self._render_mode("report")
        rendered_text = " ".join(str(args[0]) for name, args, _ in recorder.calls if name in {"title", "caption", "markdown", "write", "expander"} and args)
        self.assertIn("BÁO CÁO CÔNG NỢ A BÒ", rendered_text)
        self.assertIn("DIỄN GIẢI SỐ LIỆU", rendered_text)
        self.assertIn("Shipment quan trọng", rendered_text)
        self.assertEqual(recorder.financial_write_count, 0)

    def test_debit_action_renders_formula_inclusions_exclusions_and_no_snapshot_without_db(self) -> None:
        recorder = self._render_mode("debit")
        rendered_text = " ".join(str(args[0]) for name, args, _ in recorder.calls if name in {"title", "caption", "markdown", "write", "info", "warning", "expander"} and args)
        self.assertIn("DEBIT DRAFT", rendered_text)
        self.assertIn("Vì sao debit ra số này?", rendered_text)
        self.assertIn("Dòng được cộng vào Debit", rendered_text)
        self.assertIn("Dòng bị loại khỏi Debit", rendered_text)
        button_calls = [kwargs for name, _, kwargs in recorder.calls if name == "button"]
        self.assertTrue(any(call.get("disabled") is True for call in button_calls))
        self.assertEqual(recorder.financial_write_count, 0)


if __name__ == "__main__":
    unittest.main()
