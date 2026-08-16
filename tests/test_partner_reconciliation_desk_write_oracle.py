"""Read-only render oracle for the LOG-C04 desk.

The renderer is exercised with an in-memory canonical projection and a tiny
Streamlit recorder.  No live database or workbook is opened; any financial
write method call would fail the test.
"""

from __future__ import annotations

from contextlib import contextmanager
import unittest
from unittest.mock import patch

from core.financial_ledger import project_partner_financial_position
from tests.test_reconciliation_desk import ABO, _fixture_history
from views import partner_reconciliation as desk
from views.web_app import ROUTES


class _ColumnRecorder:
    def __init__(self, parent: "_StreamlitRecorder") -> None:
        self.parent = parent

    def metric(self, *args, **kwargs) -> None:
        self.parent.calls.append(("metric", args, kwargs))

    def caption(self, *args, **kwargs) -> None:
        self.parent.calls.append(("caption", args, kwargs))

    def warning(self, *args, **kwargs) -> None:
        self.parent.calls.append(("warning", args, kwargs))

    def text_input(self, *args, **kwargs):
        return self.parent.text_input(*args, **kwargs)

    def date_input(self, *args, **kwargs):
        return self.parent.date_input(*args, **kwargs)


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
            if name == "text_input":
                label = str(args[0] if args else kwargs.get("label", ""))
                if "Mã shipment" in label:
                    return "62464"
                return ""
            if name == "date_input":
                return kwargs.get("value")
            if name == "selectbox":
                options = args[1] if len(args) > 1 else kwargs.get("options", [])
                return next(iter(options), "")
            return None

        return record

    @contextmanager
    def spinner(self, *args, **kwargs):
        yield

    @contextmanager
    def expander(self, *args, **kwargs):
        yield


class PartnerReconciliationDeskWriteOracleTests(unittest.TestCase):
    def test_route_points_to_dedicated_read_only_desk(self) -> None:
        route = next(route for route in ROUTES if route.module == "views.partner_reconciliation")
        self.assertEqual(route.function, "ui_partner_reconciliation_desk")
        self.assertEqual(route.permission, "receivables")

    def test_render_search_trace_period_and_reported_inputs_do_not_write(self) -> None:
        obligations, transactions, allocations = _fixture_history()
        position = project_partner_financial_position(
            ABO,
            obligations,
            transactions,
            allocations,
            internal_sale_owner="Thành",
        )
        recorder = _StreamlitRecorder()
        with patch.object(desk, "st", recorder), patch.object(
            desk,
            "build_partner_financial_position",
            return_value=position,
        ):
            desk.ui_partner_reconciliation_desk()

        self.assertEqual(recorder.financial_write_count, 0)
        self.assertTrue(any(name == "dataframe" for name, _, _ in recorder.calls))
        self.assertTrue(any(name == "json" for name, _, _ in recorder.calls))
        self.assertTrue(any(name == "date_input" for name, _, _ in recorder.calls))


if __name__ == "__main__":
    unittest.main()
