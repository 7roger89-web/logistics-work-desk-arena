"""LG03 UX release QA gate (read-only QA, no production mutation).

Runs mounted Streamlit AppTest checks against the real app.py with all database
layers mocked so nothing touches production. Verifies:
1. Navigation labels are Vietnamese-first.
2. Pilot screens render Vietnamese titles/kickers without exceptions.
3. RBAC: sale/support see only their permitted menu items; admin sees all.
4. Mojibake-free (no double-encoded markers) in rendered text.

Exit code 0 = all gates passed; prints a per-check verdict table.
"""
from __future__ import annotations

import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

APP_PATH = Path(__file__).resolve().parents[4] / "app.py"

MOJIBAKE_MARKERS = ("Ã", "Â·", "Ä\x90", "á»", "áº")  # common double-encoding chars

VI_NAV_LABELS = [
    "Tổng Quan Công Việc",
    "Việc Cần Xử Lý",
    "Tạo Lô Mới",
    "Khách Hàng",
    "Ngữ Cảnh Đối Tác",
    "Kinh Doanh & Báo Giá",
    "Thỏa Thuận & Bàn Giao",
    "Hợp Đồng",
    "Thu Tiền & Công Nợ",
    "Đối Soát Tài Chính",
    "Công Nợ A Bò",
    "Báo Cáo CEO",
    "Tra Cứu Thuế",
    "Theo Dõi Vận Chuyển",
    "Sổ Tay Kinh Nghiệm",
    "Người Dùng",
]

EN_NAV_LABELS_FORBIDDEN = [
    "Dashboard",
    "Review Queue",
    "Entity Context",
    "Finance Review",
    "Knowledge Base",
    "Tariff Lookup",
]


class _FakeShipment(dict):
    def __init__(self) -> None:
        super().__init__(
            {
                "id": "QA-001",
                "shipment_id": "QA-001",
                "customer": "Acme QA",
                "customer_id": "CUS-QA",
                "status": "wait",
                "owner": "sale_qa",
                "currency": "VND",
                "client": "Acme QA",
                "data": {
                    "0.0": {"created_at": "2026-08-18", "mode": "Sea", "incoterm": "EXW"},
                    "1.2": {},
                    "2.4": {},
                    "2.6": {},
                    "2.7": {},
                    "3.4": {"details": [], "commission": {"list": [], "total": 0}, "payments": []},
                    "entrustment": {"active": False},
                },
            }
        )


class _FakeCustomers(dict):
    def __init__(self) -> None:
        super().__init__(
            {"CUS-QA": {"id": "CUS-QA", "name": "Acme QA", "contact_person": "QA Tester"}}
        )


def _collect(app: AppTest) -> str:
    """Gather every user-visible text element rendered by the page."""
    parts: list[str] = []
    for items in (
        app.title,
        app.subheader,
        app.markdown,
        app.header,
        app.text,
        app.button,
        app.selectbox,
        app.radio,
        app.checkbox,
    ):
        for item in items:
            value = getattr(item, "value", None)
            label = getattr(item, "label", None)
            for candidate in (value, label):
                if isinstance(candidate, str):
                    parts.append(candidate)
    return "\n".join(parts)


def _run_app(page: str, role: str) -> AppTest:
    app = AppTest.from_file(str(APP_PATH), default_timeout=120)
    app.session_state.active_page = page
    app.session_state.db_shipments = {"QA-001": _FakeShipment()}
    app.session_state.db_customers = _FakeCustomers()
    app.session_state.entity_context_request = {"entity_type": "customer", "entity_key": "CUS-QA"}
    app.session_state.current_user = {
        "username": f"qa_{role}",
        "role": role,
        "display_name": f"QA {role}",
        "user_id": f"qa_{role}",
        "email": "",
    }
    return app


def _patch_stack() -> ExitStack:
    stack = ExitStack()
    stack.enter_context(patch("views.web_app.refresh_core_data", return_value=None))
    stack.enter_context(patch("views.dashboard.cached_load_data", return_value={"QA-001": _FakeShipment()}))
    stack.enter_context(patch("views.dashboard.load_tasks", return_value=[]))
    stack.enter_context(patch("views.shipment.load_proxy_payments", return_value={}))
    stack.enter_context(patch("views.shipment.load_entrustments", return_value={}))
    stack.enter_context(patch("views.shipment.load_audit_logs", return_value=[]))
    return stack


class LG03UxGateTests(unittest.TestCase):
    def _gate(self, page: str, role: str, *, check_labels: bool = True) -> AppTest:
        app = _run_app(page, role)
        with _patch_stack():
            app.run()
        self.assertEqual(
            len(app.exception),
            0,
            f"[{role}/{page}] app exception: {[str(e)[:200] for e in app.exception]}",
        )
        if check_labels:
            sidebar_texts = _collect(app)
            for forbidden in EN_NAV_LABELS_FORBIDDEN:
                self.assertNotIn(
                    forbidden,
                    sidebar_texts,
                    f"[{role}/{page}] English navigation label found: {forbidden}",
                )
            for vi in VI_NAV_LABELS:
                self.assertIn(vi, sidebar_texts, f"[{role}/{page}] missing VI label: {vi}")
            rendered = " ".join(str(item.value) for item in app.markdown)
            rendered += " " + " ".join(str(item.value) for item in app.subheader)
            for marker in MOJIBAKE_MARKERS:
                self.assertNotIn(marker, rendered, f"[{role}/{page}] mojibake marker present: {marker!r}")
        return app

    def test_navigation_vietnamese_first(self) -> None:
        self._gate("Tổng Quan Công Việc", "admin")

    def test_dashboard_vietnamese(self) -> None:
        app = self._gate("Tổng Quan Công Việc", "admin")
        rendered = " ".join(str(item.value) for item in app.markdown)
        for required in ("BẢNG VIỆC CHÍNH", "TÀI CHÍNH CẦN THEO DÕI"):
            self.assertIn(required, rendered, "dashboard missing VI kicker")

    def test_review_queue_vietnamese(self) -> None:
        app = self._gate("Việc Cần Xử Lý", "admin")
        rendered = " ".join(str(item.value) for item in app.markdown)
        rendered += " " + " ".join(str(item.value) for item in app.subheader)
        rendered += " " + " ".join(str(item.value) for item in app.title)
        self.assertTrue(
            "Việc Cần Xử Lý" in rendered or "Chứng Từ" in rendered,
            "review queue missing Vietnamese title content",
        )

    def test_shipment_create_vietnamese(self) -> None:
        app = self._gate("Tạo Lô Mới", "admin")
        titles = [str(item.value) for item in app.title]
        self.assertTrue(
            any("TẠO LÔ HÀNG MỚI" in t or "Tạo Lô" in t for t in titles),
            f"shipment create title not Vietnamese: {titles}",
        )

    def test_finance_review_vietnamese(self) -> None:
        app = self._gate("Đối Soát Tài Chính", "admin")
        titles = [str(item.value) for item in app.title]
        self.assertTrue(
            any("Đối Soát" in t for t in titles),
            f"finance review title not Vietnamese: {titles}",
        )

    def test_entity_context_vietnamese(self) -> None:
        app = self._gate("Ngữ Cảnh Đối Tác", "admin")
        rendered = " ".join(str(item.value) for item in app.subheader)
        rendered += " " + " ".join(str(item.value) for item in app.title)
        rendered += " " + " ".join(str(item.value) for item in app.markdown)
        self.assertIn("Khách hàng 360", rendered, "entity context header not Vietnamese")

    def test_rbac_sale_role(self) -> None:
        app = _run_app("Tổng Quan Công Việc", "sale")
        with _patch_stack():
            app.run()
        self.assertEqual(len(app.exception), 0, [str(e)[:200] for e in app.exception])
        sidebar_texts = _collect(app)
        allowed = [
            "Tổng Quan Công Việc",
            "Tạo Lô Mới",
            "Khách Hàng",
            "Kinh Doanh & Báo Giá",
            "Hợp Đồng",
            "Tra Cứu Thuế",
            "Theo Dõi Vận Chuyển",
            "Sổ Tay Kinh Nghiệm",
            "Ngữ Cảnh Đối Tác",
        ]
        for label in allowed:
            self.assertIn(label, sidebar_texts, f"sale missing allowed label: {label}")
        for forbidden in ["Người Dùng", "Báo Cáo CEO", "Đối Soát Tài Chính", "Công Nợ A Bò", "Thu Tiền & Công Nợ"]:
            self.assertNotIn(forbidden, sidebar_texts, f"sale sees forbidden label: {forbidden}")

    def test_rbac_support_role(self) -> None:
        app = _run_app("Tổng Quan Công Việc", "support")
        with _patch_stack():
            app.run()
        self.assertEqual(len(app.exception), 0, [str(e)[:200] for e in app.exception])
        sidebar_texts = _collect(app)
        allowed = [
            "Tổng Quan Công Việc",
            "Việc Cần Xử Lý",
            "Khách Hàng",
            "Ngữ Cảnh Đối Tác",
            "Hợp Đồng",
            "Tra Cứu Thuế",
            "Theo Dõi Vận Chuyển",
            "Sổ Tay Kinh Nghiệm",
        ]
        for label in allowed:
            self.assertIn(label, sidebar_texts, f"support missing allowed label: {label}")
        for forbidden in ["Người Dùng", "Kinh Doanh & Báo Giá", "Báo Cáo CEO", "Tạo Lô Mới"]:
            self.assertNotIn(forbidden, sidebar_texts, f"support sees forbidden label: {forbidden}")


if __name__ == "__main__":
    unittest.main()
