"""LOG-LG04 QA — đơn giản hóa không gian làm việc lô hàng.

Kiểm tra UI không gian làm việc (W1-W6): việc tiếp theo nổi bật, 3 thẻ việc
chính, khối đối tác thu gọn + giải thích, form dịch vụ kẻ khung, hành trình
4 bước, UNKNOWN != ZERO giữ nguyên ở tài chính.
"""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


def _base_view(**overrides) -> dict:
    view = {
        "shipment_id": "S-001",
        "customer": "Khách thử",
        "customer_id": "CUST-001",
        "route": {
            "pol": "Cát Lái", "pod": "Port Klang", "mode": "Sea",
            "incoterm": "FOB", "booking": "BK-001", "carrier": "CMA",
            "vessel": "V123", "container": "MSKU1234",
        },
        "operational_status_label": "Đang lấy hàng",
        "financial_status": "Chưa đóng",
        "financial_label": "Còn thu",
        "owner": "admin",
        "required_date": "2026-08-25",
        "planned_date": "2026-08-24",
        "free_time_remaining": 1.5,
        "free_time_expiry": "2026-08-19",
        "next_action": {
            "code": "NEED_PICKUP_CONFIRM",
            "severity": "warning",
            "label": "Xác nhận lấy hàng với nhà máy",
            "detail": "Nhà máy báo sẵn hàng, cần chốt xe trước 17h nay.",
            "who": "Support vận hành",
            "source": "Trạng thái lô hàng",
        },
        "alerts": [],
        "context": {
            "supplier": "Nhà máy mẫu",
            "agent": "Đại lý mẫu",
            "pickup_contact": "0909-000-001",
            "pickup_address": "KCN ABC",
            "delivery_address": "Kho XYZ",
            "receiver": "Người nhận mẫu",
        },
        "factory_lots": [],
        "documents": [],
        "documents_status": "Chưa có dữ liệu",
        "timeline": [],
    }
    view.update(overrides)
    return view


_WORKSPACE_PAGE = """
import json
import streamlit as st
from views.shipment_360 import render_shipment_workspace
VIEW = json.loads(r'{{VIEW_JSON}}')
render_shipment_workspace(VIEW)
"""


def _stop_patches(patches):
    for p in patches:
        p.stop()


class Lg04WorkspaceUITests(unittest.TestCase):
    def _render(self, **overrides) -> AppTest:
        page_src = _WORKSPACE_PAGE.replace("{{VIEW_JSON}}", json.dumps(_base_view(**overrides), ensure_ascii=False))
        patches = [
            patch("core.database.init_connection", return_value=None),
            patch("views.shipment.load_proxy_payments", return_value={}),
            patch("views.shipment.load_entrustments", return_value={}),
            patch("views.shipment.load_audit_logs", return_value=[]),
        ]
        for p in patches:
            p.start()
        self.addCleanup(_stop_patches, patches)
        test = AppTest.from_string(page_src, default_timeout=60)
        test.run()
        return test

    def test_primary_work_cards_render_three_labels(self) -> None:
        test = self._render()
        self.assertFalse(test.exception, msg=str(test.exception))
        joined = "\n".join(m.value or "" for m in test.markdown)
        for expected in ("Lấy hàng & Xuất khẩu", "Nhập khẩu & Giao hàng", "Chi phí & Công nợ"):
            self.assertIn(expected, joined, f"Missing label: {expected}")
        # 3 nút nhảy tới khối nhập liệu (label "Mở ...")
        btn_labels = {b.label for b in test.button if b.label}
        for expected in ("Mở Xuất khẩu", "Mở Nhập khẩu & Giao hàng", "Mở Chi phí"):
            self.assertIn(expected, btn_labels, f"Missing button: {expected}")

    def test_next_action_card_prominent_with_action(self) -> None:
        test = self._render()
        self.assertFalse(test.exception, msg=str(test.exception))
        joined = "\n".join(m.value or "" for m in test.markdown)
        self.assertIn("VIỆC TIẾP THEO", joined)
        self.assertIn("Xác nhận lấy hàng với nhà máy", joined)
        # Card có viền 3px theo severity + nút Xử lý ngay
        keys = {b.key for b in test.button}
        self.assertIn("lg04_next_action_jump_lg04_tab_export", keys)
        self.assertTrue(any("border: 3px solid" in (m.value or "") for m in test.markdown))

    def test_free_time_expiring_overrides_next_action(self) -> None:
        test = self._render(free_time_remaining=-2, next_action={"severity": "info"})
        self.assertFalse(test.exception, msg=str(test.exception))
        joined = "\n".join(m.value or "" for m in test.markdown)
        self.assertIn("Đã quá hạn free time", joined)

    def test_partner_block_collapsed_with_explanation(self) -> None:
        test = self._render()
        self.assertFalse(test.exception, msg=str(test.exception))
        labels = [e.label for e in test.expander if e.label]
        self.assertIn("👥 Ai tham gia lô hàng này", labels)
        # Khối hàng từ nhà máy ẩn khi không có dữ liệu (Ý 6) — chỉ hiện expander lịch sử + đối tác
        self.assertNotIn("🏭 Hàng từ nhà máy (0)", labels)
        # Work-jump buttons phải hiện đầy đủ 3 mục (Ý 1)
        keys = {b.key for b in test.button}
        self.assertIn("lg04_work_jump_lg04_tab_export", keys)
        self.assertIn("lg04_work_jump_lg04_tab_import", keys)
        self.assertIn("lg04_work_jump_lg04_tab_finance", keys)

    def test_partner_expander_contains_plain_vietnamese_explainer(self) -> None:
        test = self._render()
        self.assertFalse(test.exception, msg=str(test.exception))
        joined = "\n".join((c.value or "") for c in test.caption)
        self.assertIn("Thông tin liên hệ của các bên", joined)

    def test_unknown_free_time_still_marks_unknown(self) -> None:
        test = self._render(free_time_remaining=None, free_time_expiry=None)
        self.assertFalse(test.exception, msg=str(test.exception))
        joined = "\n".join((m.value or "") for m in test.markdown)
        self.assertIn("UNKNOWN", joined)

    def test_tabs_jump_to_finance_when_section_requested(self) -> None:
        """Nhấn 'Mở Chi phí' ở workspace phải mở đúng tab FINANCE."""
        patches = [
            patch("core.database.init_connection", return_value=None),
            patch("views.shipment.load_proxy_payments", return_value={}),
            patch("views.shipment.load_entrustments", return_value={}),
            patch("views.shipment.load_audit_logs", return_value=[]),
        ]
        for p in patches:
            p.start()
        self.addCleanup(_stop_patches, patches)
        page_src = r"""
import streamlit as st
from views.shipment import ui_shipment_detail_tabs
st.session_state.active_shipment_section = "finance"
fake_shipment = {"id": "S-001", "customer": "Khách thử", "customer_id": "CUST-001",
                 "contact": "", "phone": "", "email": "", "created_at": "",
                 "status": "BOOKING", "required_date": "", "incoterm": "FOB",
                 "factory": "", "factory_contact": "", "factory_phone": "",
                 "packages": "", "cbm": "", "weight": "", "pickup_address": "",
                 "contract_id": "", "is_deleted": False}
ui_shipment_detail_tabs("S-001", fake_shipment)
"""
        test = AppTest.from_string(page_src, default_timeout=60)
        test.run()
        self.assertFalse(test.exception, msg=str(test.exception))
        # FINANCE tab mở mặc định khi section=finance (subheader nằm trong tab content)
        subheaders = [s.value for s in test.subheader if s.value]
        self.assertTrue(
            any("nhập chi phí và giá bán" in str(v) for v in subheaders),
            msg=f"Finance subheader not visible; subheaders: {subheaders}",
        )


class Lg04QuoteFormUITests(unittest.TestCase):
    def test_quote_form_has_bordered_service_rows(self) -> None:
        page_src = r"""
import streamlit as st
from views.quotations import _render_new_quote
st.session_state.db_customers = {"CUST-001": {"name": "Khách thử"}}
_render_new_quote()
"""
        test = AppTest.from_string(page_src, default_timeout=60)
        test.run()
        self.assertFalse(test.exception, msg=str(test.exception))
        # Số dòng dịch vụ mặc định = 3 → 3 khối kẻ khung (đếm div, trừ style block)
        styled = [m.value for m in test.markdown if m.value and "lg04-quote-line" in str(m.value) and not str(m.value).strip().startswith("<style>")]
        self.assertEqual(len(styled), 3)
        # Cài đặt nâng cao nằm trong 1 expander duy nhất
        labels = [e.label for e in test.expander if e.label]
        self.assertEqual(len([l for l in labels if "Cài đặt nâng cao" in str(l)]), 1)


class Lg04AgreementJourneyUITests(unittest.TestCase):
    def test_journey_card_and_plain_labels(self) -> None:
        page_src = r"""
import streamlit as st
from views.agreements import ui_agreements_module
st.session_state.db_agreements = {}
ui_agreements_module()
"""
        test = AppTest.from_string(page_src, default_timeout=60)
        test.run()
        self.assertFalse(test.exception, msg=str(test.exception))
        joined = "\n".join((m.value or "") for m in test.markdown)
        for phrase in ("Báo giá", "Khách chốt", "Thỏa thuận", "Bàn giao cho Support"):
            self.assertIn(phrase, joined, f"Missing journey step: {phrase}")
        self.assertEqual(len(test.tabs), 3)


if __name__ == "__main__":
    unittest.main()
