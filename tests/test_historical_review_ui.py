"""Recorder-based UI and route tests for the LOG-C06 Historical Review desk."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date
import unittest
from pathlib import Path
from unittest.mock import patch

from core.historical_staging import SALE_OWNER
from views import historical_review as review
from views import partner_reconciliation as desk


class _Column:
    def __init__(self, parent: "_Recorder"):
        self.parent = parent

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def metric(self, *args, **kwargs):
        self.parent.record("metric", args, kwargs)

    def button(self, *args, **kwargs):
        return self.parent.button(*args, **kwargs)


class _Recorder:
    def __init__(self, *, search: str = "", click_confirm: bool = False):
        self.calls: list[tuple[str, tuple, dict]] = []
        self.session_state: dict = {}
        self.search = search
        self.click_confirm = click_confirm

    def record(self, name, args, kwargs):
        self.calls.append((name, args, kwargs))

    def columns(self, count, *args, **kwargs):
        self.record("columns", (count,), kwargs)
        return [_Column(self) for _ in range(count)]

    def button(self, label, *args, **kwargs):
        self.record("button", (label,) + args, kwargs)
        key = str(kwargs.get("key") or "")
        return self.click_confirm and "_confirm_" in key

    def text_input(self, label, *args, **kwargs):
        self.record("text_input", (label,) + args, kwargs)
        key = str(kwargs.get("key") or "")
        if key == "log_c06_search":
            return self.search
        if key.startswith("log_c06_reason_"):
            return "Đã đối chiếu source row."
        return ""

    def selectbox(self, label, options, *args, **kwargs):
        self.record("selectbox", (label, options) + args, kwargs)
        return next(iter(options), "")

    def date_input(self, label, *args, **kwargs):
        self.record("date_input", (label,) + args, kwargs)
        return date(2026, 4, 1)

    def rerun(self):
        self.record("rerun", (), {})

    @contextmanager
    def expander(self, *args, **kwargs):
        self.record("expander", args, kwargs)
        yield

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.record(name, args, kwargs)
            return None

        return record


def _item(source_item_id: str, amount: float, status: str) -> dict:
    return {
        "source_item_id": source_item_id,
        "source_file": "fixture.xls",
        "source_file_hash": "fixture-hash",
        "sheet": "Sheet2",
        "source_row": int(source_item_id),
        "source_cell_range": f"D{source_item_id}:D{source_item_id}",
        "source_reference": f"Sheet2!D{source_item_id}",
        "raw_values": {f"D{source_item_id}": amount},
        "raw_cell_types": {f"D{source_item_id}": 2},
        "raw_text": f"historical row {source_item_id} amount {amount}",
        "raw_note": f"historical row {source_item_id}",
        "raw_date": "2026-03-12",
        "raw_date_serial": 46093.0,
        "inherited_date_context": None,
        "raw_sale": "" if source_item_id == "62464" else SALE_OWNER,
        "raw_customer": "fixture party",
        "raw_reference": [],
        "raw_amount": amount,
        "raw_currency": "CNY",
        "parser_version": "fixture-v1",
        "imported_at": "2026-08-15T00:00:00+00:00",
        "review_status": status,
        "proposal": {
            "internal_sale_owner": None if source_item_id == "62464" else SALE_OWNER,
            "candidate_internal_sale_owner": SALE_OWNER if source_item_id == "62464" else None,
            "sale_evidence": "free_text_only" if source_item_id == "62464" else "explicit_sale_field",
            "currency": "CNY",
            "amount": amount,
            "event_type": "received_on_behalf",
            "candidate_bucket": "received_on_behalf",
            "anomalies": ["MISSING_SALE"] if source_item_id == "62464" else [],
        },
        "review_reason": "needs owner review" if status == "REVIEW_REQUIRED" else "",
        "anomaly_flags": ["MISSING_SALE"] if source_item_id == "62464" else [],
        "review_history": [],
        "review_version": 0,
    }


def _batch() -> dict:
    return {
        "source_file": "fixture.xls",
        "source_file_hash": "fixture-hash",
        "parser_version": "fixture-v1",
        "item_count": 3,
        "items": [
            _item("62464", 62464, "REVIEW_REQUIRED"),
            _item("1572", 1572, "REVIEW_REQUIRED"),
            _item("1687", 1687, "PROPOSED"),
        ],
    }


class HistoricalReviewUiTests(unittest.TestCase):
    def test_business_review_map_exposes_owner_decisions_without_live_controls(self):
        recorder = _Recorder()
        analysis = {
            "analysis_version": "fixture-analysis",
            "review_required_count": 1,
            "cluster_count": 1,
            "owner_review_state_counts": {
                "READY_FOR_OWNER_CONFIRMATION": 1,
                "REVIEW_REQUIRED": 0,
                "UNKNOWN": 0,
            },
            "golden_items": [
                {
                    "source_row": 16,
                    "source_reference": "Sheet2!D17:E17",
                    "amount": 24576.0,
                    "currency": "CNY",
                    "current_review_status": "PROPOSED",
                    "owner_review_state": "READY_FOR_OWNER_CONFIRMATION",
                    "business": {
                        "title": "A Bò còn phải trả 24,576 CNY",
                        "money_from": "Lục Giác",
                        "money_location": "Phần còn lại theo workbook",
                        "business_meaning": "Nghĩa vụ cần Owner xác nhận",
                        "shipment_or_customer": "Lục Giác",
                        "certainty": "Cao về arithmetic",
                        "recommendation": "Giữ candidate, chưa opening",
                        "owner_question": "Có phải opening obligation không?",
                    },
                }
            ],
            "clusters": [
                {
                    "cluster_key": "CHECKPOINT_OR_SUMMARY",
                    "label": "Checkpoint / tổng thủ công",
                    "count": 1,
                    "amounts_by_currency": {"CNY": 134973.0},
                    "ready_count": 1,
                    "unknown_count": 0,
                    "one_owner_rule": True,
                    "owner_question": "Xác nhận component set",
                    "rule_resolution": "Không cộng summary lần hai",
                }
            ],
            "owner_decision_pack": {
                "cutover_lock": "DRAFT / NOT_APPROVED / NOT_LIVE",
                "decisions": [
                    {
                        "decision_id": "GOLDEN-16",
                        "title": "A Bò còn phải trả 24,576 CNY",
                        "evidence": {
                            "source_reference": "Sheet2!D17:E17",
                            "amount": 24576.0,
                            "currency": "CNY",
                            "current_review_status": "PROPOSED",
                        },
                        "recommended": "Giữ candidate",
                        "financial_effect_if_confirmed": "Có thể xem xét component",
                        "owner_question": "Xác nhận business meaning",
                    }
                ],
            },
            "checkpoint_reconstruction": {
                "reason": "Unique exact sum",
                "candidate_components": [
                    {"source_row": 103, "source_reference": "Sheet2!B104:J104", "amount": 4900.0, "currency": "CNY"}
                ],
                "candidate_component_amount": 134973.0,
                "difference": 0.0,
                "exact_solution_count": 1,
                "context_exclusion_rows": [{"source_row": 109}],
            },
        }
        with patch.object(review, "st", recorder), patch.object(review, "get_db", return_value=None), patch.object(
            review, "stage_workbook", return_value=_batch()
        ), patch.object(review, "build_review_analysis", return_value=analysis):
            review.ui_historical_review()
        rendered = " ".join(
            str(value)
            for name, args, kwargs in recorder.calls
            if name in {"title", "caption", "subheader", "info", "warning", "write", "markdown", "expander"}
            for value in args
        )
        self.assertIn("Business review map", rendered)
        self.assertIn("6 golden items", rendered)
        self.assertIn("Owner Decision Pack", rendered)
        self.assertIn("134,973 CNY", rendered)
        self.assertIn("READY_FOR_OWNER_CONFIRMATION", rendered)
        self.assertIn("DRAFT / NOT_APPROVED / NOT_LIVE", rendered)

    def test_session_fallback_search_and_source_evidence_are_visible(self):
        recorder = _Recorder(search="62464")
        with patch.object(review, "st", recorder), patch.object(review, "get_db", return_value=None), patch.object(
            review, "stage_workbook", return_value=_batch()
        ):
            review.ui_historical_review()
        rendered = " ".join(
            str(value)
            for name, args, kwargs in recorder.calls
            if name in {"title", "caption", "subheader", "info", "warning", "write", "json", "expander"}
            for value in args
        )
        self.assertIn("Historical Review", rendered)
        self.assertIn("session-only", rendered)
        self.assertIn("62464", rendered)
        self.assertIn("Sheet2!D62464", rendered)
        self.assertEqual(len(recorder.session_state[review._SESSION_STAGING_KEY]), 3)

    def test_confirm_action_updates_session_staging_only(self):
        recorder = _Recorder(search="1687", click_confirm=True)
        with patch.object(review, "st", recorder), patch.object(review, "get_db", return_value=None), patch.object(
            review, "stage_workbook", return_value=_batch()
        ):
            review.ui_historical_review()
        staged = {
            item["source_item_id"]: item
            for item in recorder.session_state[review._SESSION_STAGING_KEY]
        }
        self.assertEqual(staged["1687"]["review_status"], "CONFIRMED")
        self.assertEqual(len(recorder.session_state[review._SESSION_ACTIONS_KEY]), 1)
        self.assertTrue(any(name == "rerun" for name, _, _ in recorder.calls))

    def test_partner_desk_enters_historical_review_before_canonical_projection(self):
        recorder = _Recorder()

        def state_get(key, default=None):
            return "historical_review" if key == desk._VIEW_STATE_KEY else default

        with patch.object(desk, "st", recorder), patch.object(desk, "_state_get", side_effect=state_get), patch.object(
            desk, "ui_historical_review", return_value=None
        ) as historical, patch.object(
            desk, "build_partner_financial_position", side_effect=AssertionError("canonical projection should not run")
        ):
            desk.ui_partner_reconciliation_desk()
        historical.assert_called_once_with()
        self.assertFalse(any(name == "spinner" for name, _, _ in recorder.calls))

    def test_ui_module_has_no_canonical_financial_writer_import(self):
        source = Path(__file__).resolve().parents[1] / "views" / "historical_review.py"
        text = source.read_text(encoding="utf-8")
        self.assertNotIn("financial_ledger", text)
        self.assertNotIn("save_obligation", text)
        self.assertNotIn("save_transaction", text)
        self.assertNotIn("allocate_transaction", text)


if __name__ == "__main__":
    unittest.main()
