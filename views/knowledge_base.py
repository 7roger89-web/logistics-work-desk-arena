from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import streamlit as st

from core.database import delete_knowledge_entry, load_knowledge_base, save_knowledge_entry
from core.auth import has_permission

CATEGORIES = [
    "🏛️ Hải Quan",
    "🚢 Cước Biển / Hàng Không",
    "📄 Chứng Từ (Docs)",
    "🚚 Vận Tải Nội Địa",
    "👥 Khách Hàng / Công Nợ",
    "⚙️ Khác",
]


def ui_knowledge_base():
    st.title("📔 SỔ TAY KINH NGHIỆM LOGISTICS")
    st.caption("Dữ liệu được lưu tập trung trên MongoDB và dùng chung cho toàn đội.")

    if "kb_data" not in st.session_state or st.session_state.get("kb_refresh"):
        st.session_state.kb_data = load_knowledge_base()
        st.session_state.kb_refresh = False

    left, right = st.columns([1, 2.4])
    with left:
        st.markdown("### ➕ Thêm ghi chú")
        with st.form("add_kb_form", clear_on_submit=True):
            title = st.text_input("Tiêu đề / Tình huống")
            category = st.selectbox("Phân loại nghiệp vụ", CATEGORIES)
            content = st.text_area("Nội dung kinh nghiệm / Cách xử lý", height=260)
            tags = st.text_input("Từ khóa", placeholder="hải quan, bill gốc, dem-det")
            submitted = st.form_submit_button("Lưu kinh nghiệm", type="primary", use_container_width=True)
        if submitted:
            if not title.strip() or not content.strip():
                st.error("Tiêu đề và nội dung không được để trống.")
            else:
                entry = {
                    "id": str(uuid4()),
                    "title": title.strip(),
                    "category": category,
                    "content": content.strip(),
                    "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
                    "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                }
                if save_knowledge_entry(entry):
                    st.session_state.kb_refresh = True
                    st.success("Đã lưu kinh nghiệm.")
                    st.rerun()
                else:
                    st.error("Không thể lưu dữ liệu vào MongoDB.")

    with right:
        st.markdown("### 🔎 Tra cứu")
        search = st.text_input("Tìm theo tiêu đề, nội dung hoặc từ khóa", label_visibility="collapsed").strip().lower()
        selected_categories = st.multiselect("Lọc phân loại", CATEGORIES)
        entries = st.session_state.kb_data
        filtered = []
        for entry in entries:
            haystack = " ".join([
                str(entry.get("title", "")),
                str(entry.get("content", "")),
                " ".join(entry.get("tags", [])),
            ]).lower()
            if search and search not in haystack:
                continue
            if selected_categories and entry.get("category") not in selected_categories:
                continue
            filtered.append(entry)

        if not filtered:
            st.info("Chưa có nội dung phù hợp.")
            return

        for entry in filtered:
            with st.expander(f"{entry.get('category', '⚙️ Khác')} · {entry.get('title', '')}"):
                st.caption(f"Cập nhật: {entry.get('date', entry.get('updated_at', ''))}")
                st.write(entry.get("content", ""))
                if entry.get("tags"):
                    st.caption("Từ khóa: " + ", ".join(entry["tags"]))
                if st.button("Xóa ghi chú", key=f"kb_delete_{entry.get('id')}", disabled=not has_permission("knowledge_delete")):
                    if delete_knowledge_entry(str(entry.get("id"))):
                        st.session_state.kb_refresh = True
                        st.rerun()
                    st.error("Không thể xóa ghi chú.")
