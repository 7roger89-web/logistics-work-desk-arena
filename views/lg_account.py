"""LOGI-GOOD EXACT — Tài khoản & Người dùng."""
from __future__ import annotations

import streamlit as st

from core.auth import current_user, has_permission, logout
from core.config import ENV_IDENTITY
from views.lg_core import esc, link_url, section_title, text


def account_page() -> None:
    user = current_user() or {}
    display = text(user.get("display_name") or user.get("username"), "Người dùng")
    role = str(user.get("role") or "").upper()
    roles_vi = {"ADMIN": "Quản trị hệ thống", "SUPPORT": "Điều hành vận hành", "SALE": "Kinh doanh"}
    st.markdown(section_title("👤", "Tài khoản của tôi", f"Vai trò: {roles_vi.get(role, role)} · {role}"),
                unsafe_allow_html=True)
    st.markdown(
        f"<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;'>"
        f"{_box('Tên hiển thị', display)}{_box('Tên đăng nhập', esc(user.get('username') or '—'))}"
        f"{_box('Vai trò', f'{roles_vi.get(role, role)} ({role})')}"
        f"{_box('Môi trường', esc(ENV_IDENTITY or 'production'))}"
        f"</div>",
        unsafe_allow_html=True,
    )
    if str(ENV_IDENTITY).upper() in ("PREVIEW", "STAGING"):
        st.warning("Môi trường PREVIEW/STAGING — dữ liệu chỉ dùng để kiểm thử giao diện, không ghi lời thực.")
    else:
        st.caption("Đang ở môi trường dữ liệu thật — mọi thay đổi đều đi qua audit log hệ thống.")
    if has_permission("admin"):
        st.markdown("---")
        st.markdown("#### Quản trị")
        st.markdown(
            f"<a class='lg-btn' href='{link_url('users')}' style='min-height:44px;'>👤 Quản lý người dùng</a>",
            unsafe_allow_html=True,
        )
    st.markdown("---")
    if st.button("Đăng xuất", type="secondary", use_container_width=False):
        logout()


def users_page() -> None:
    st.markdown(section_title("👤", "Người Dùng (Admin)",
                              "Chỉ quản trị viên — tạo/vô hiệu hóa tài khoản đều được ghi audit"), unsafe_allow_html=True)
    from views.web_app import _render_user_management  # noqa: PLC0415

    _render_user_management()


def _box(label: str, value: str) -> str:
    return (
        "<div style='background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:14px 16px;'>"
        f"<p style='margin:0;font-size:12px;font-weight:800;letter-spacing:.05em;color:#94a3b8;'>{esc(label)}</p>"
        f"<p style='margin:4px 0 0;font-size:17px;font-weight:800;color:#0f2a4a;'>{value}</p></div>"
    )
