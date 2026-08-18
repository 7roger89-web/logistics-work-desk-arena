"""Chẩn đoán tạm thời cho AppTest LG04 — xóa sau khi sửa xong."""

import json
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from tests.test_lg04_daily_work_ui import _base_view, _WORKSPACE_PAGE

page = _WORKSPACE_PAGE.replace("{{VIEW_JSON}}", json.dumps(_base_view(), ensure_ascii=False))
t = AppTest.from_string(page, default_timeout=60)
t.run()
print("=== workspace ===")
print("exception:", t.exception)
joined = "\n".join(m.value or "" for m in t.markdown)
for lbl in ("Lấy hàng & Xuất khẩu", "Nhập khẩu & Giao hàng", "Chi phí & Công nợ"):
    print(lbl, "->", lbl in joined)
# tìm các dòng chứa 'Xuất khẩu'
for m in t.markdown:
    v = m.value or ""
    if "Xuất khẩu" in v or "Nhập khẩu" in v or "Công nợ" in v:
        print(repr(v[:200]))

patches = [
    patch("core.database.init_connection", return_value=None),
    patch("views.shipment.load_proxy_payments", return_value={}),
    patch("views.shipment.load_entrustments", return_value={}),
    patch("views.shipment.load_audit_logs", return_value=[]),
]
for p in patches:
    p.start()
t2 = AppTest.from_string(r"""
import streamlit as st
from views.shipment import ui_shipment_detail_tabs
st.session_state.active_shipment_section = "finance"
fake = {"id": "S-001", "customer": "Khách thử", "customer_id": "CUST-001",
        "contact": "", "phone": "", "email": "", "created_at": "",
        "status": "BOOKING", "required_date": "", "incoterm": "FOB",
        "factory": "", "factory_contact": "", "factory_phone": "",
        "packages": "", "cbm": "", "weight": "", "pickup_address": "",
        "contract_id": "", "is_deleted": False}
ui_shipment_detail_tabs("S-001", fake)
""", default_timeout=60)
print("(patches active)"), 
t2.run()
print("=== tabs jump ===")
print("exception:", t2.exception)
print("subheaders:", [s.value for s in t2.subheader if s.value])
for m in t2.markdown:
    v = m.value or ""
    if "chi phí" in v.lower() or "tài chính" in v.lower() or "dịch vụ" in v.lower():
        print(repr(v[:200]))
