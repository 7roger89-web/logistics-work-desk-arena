"""Điểm điều phối giao diện Streamlit của LOGISTICS PRO.

Mọi mã render được đặt trong ``main()``. Launcher phải gọi ``main()`` ở mỗi
lần Streamlit rerun; không dùng ``from views.web_app import *`` vì Python cache
module sẽ khiến trang trắng sau lần tương tác đầu tiên.
"""
from __future__ import annotations

import importlib
import logging
import traceback
import re
import urllib3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import streamlit as st

from core.auth import has_permission, has_write_permission, logout, require_login
from core.config import AUTH_REQUIRED
from core.database import load_archived_data
from core.state import initialize_state, refresh_core_data

LOGGER = logging.getLogger("logistics_pro.ui")


@dataclass(frozen=True)
class Route:
    label: str
    icon: str
    permission: str
    module: str
    function: str


ROUTES: tuple[Route, ...] = (
    Route("Dashboard", "🏠", "dashboard", "views.dashboard", "ui_dashboard"),
    Route("Review Queue", "🧭", "dashboard", "views.review_queue", "ui_review_queue"),
    Route("Tạo Lô Mới", "➕", "shipment_create", "views.shipment", "ui_create_new_shipment"),
    Route("Khách Hàng", "👥", "customers", "views.customers", "ui_customers"),
    Route("Entity Context", "🧭", "dashboard", "views.entity_context", "ui_entity_context"),
    Route("Sales & Báo Giá", "🤝", "sales", "views.quotations", "ui_sales_module"),
    Route("Thỏa Thuận & Bàn Giao", "🤝", "sales", "views.agreements", "ui_agreements_module"),
    Route("Hợp Đồng", "📜", "contracts", "views.contracts", "ui_contracts_management"),
    Route("Thu Tiền & Công Nợ", "💰", "receivables", "views.finance", "ui_receivables_management"),
    Route("Finance Review", "FR", "receivables", "views.finance_review", "ui_finance_review"),
    Route("Công nợ A Bò", "🧾", "receivables", "views.partner_reconciliation", "ui_partner_reconciliation_desk"),
    Route("Báo Cáo CEO", "📊", "reports", "views.reports", "ui_reports_dashboard"),
    Route("Tra Cứu Thuế", "🔎", "tariff", "views.tariff", "ui_super_tariff_hub"),
    Route("Tracking", "🌐", "tracking", "views.tracking", "ui_tracking_tool"),
    Route("Sổ Tay Kinh Nghiệm", "📔", "knowledge", "views.knowledge_base", "ui_knowledge_base"),
    # Màn hình quản lý tài khoản, chỉ dành cho vai trò admin.
    Route("Người Dùng", "👤", "admin", "views.web_app", "_render_user_management"),
)


# The route labels remain stable so existing permissions, deep links, and
# session state keep working.  The grouping is presentation-only: operations
# is the front door, while finance and partner review stay available behind it.
NAVIGATION_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "OPERATIONS",
        ("Dashboard", "Review Queue", "Tạo Lô Mới", "Tracking"),
    ),
    (
        "COMMERCIAL CONTEXT",
        ("Khách Hàng", "Entity Context", "Sales & Báo Giá", "Thỏa Thuận & Bàn Giao", "Hợp Đồng"),
    ),
    (
        "FINANCE & REVIEW",
        ("Finance Review", "Thu Tiền & Công Nợ", "Công nợ A Bò", "Báo Cáo CEO"),
    ),
    (
        "TOOLS & REFERENCE",
        ("Tra Cứu Thuế", "Sổ Tay Kinh Nghiệm"),
    ),
    (
        "ADMINISTRATION",
        ("Người Dùng",),
    ),
)


def _configure_page() -> None:
    st.set_page_config(page_title="LOGISTICS PRO", layout="wide", page_icon="⚓")
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    st.markdown(
        """
<style>
    :root {
        --ops-ink: #16202A;
        --ops-muted: #667085;
        --ops-navy: #102A43;
        --ops-navy-2: #173B5E;
        --ops-blue: #0B6E99;
        --ops-bg: #F7F8FA;
        --ops-surface: #FFFFFF;
        --ops-line: #D9E2EC;
        --ops-amber: #9A6700;
        --ops-red: #B42318;
        --ops-green: #18794E;
    }
    .stApp { background: var(--ops-bg); color: var(--ops-ink); }
    h1, h2, h3, h4 { color: var(--ops-navy); font-family: 'Segoe UI', system-ui, sans-serif; letter-spacing: -0.015em; }
    .block-container { max-width: 1680px; padding-top: 1.1rem; padding-bottom: 3rem; }
    .stTextInput input, .stNumberInput input, .stSelectbox [data-baseweb="select"] { border-radius: 6px; }
    div[data-testid="stMetric"] {
        background: var(--ops-surface); border: 1px solid var(--ops-line);
        padding: 12px; border-radius: 8px; box-shadow: 0 1px 2px rgba(16, 42, 67, 0.04);
    }
    button:focus-visible, input:focus-visible, textarea:focus-visible, [role="combobox"]:focus-visible {
        outline: 3px solid rgba(11, 110, 153, 0.35) !important;
        outline-offset: 2px !important;
    }
    [data-testid="stSidebar"] {
        background: var(--ops-navy);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #D9E7F2; }
    .ops-brand {
        padding: 0.35rem 0.2rem 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.12);
        margin-bottom: 0.85rem;
    }
    .ops-brand-kicker { color: #8FB7D3; font-size: 0.66rem; font-weight: 800; letter-spacing: 0.14em; }
    .ops-brand-title { color: #FFFFFF; font-size: 1.22rem; font-weight: 800; letter-spacing: -0.02em; margin-top: 0.15rem; }
    .ops-brand-status { color: #A9C6D9; font-size: 0.72rem; margin-top: 0.3rem; }
    .ops-nav-group {
        color: #8FB7D3;
        font-size: 0.64rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        margin: 1rem 0 0.35rem;
    }
    [data-testid="stSidebar"] button {
        background: transparent;
        color: #D9E7F2;
        border: 1px solid transparent;
        text-align: left;
        transition: background-color 120ms ease, color 120ms ease;
    }
    [data-testid="stSidebar"] button:hover { background: rgba(255, 255, 255, 0.08); border-color: rgba(255, 255, 255, 0.12); color: #FFFFFF; }
    [data-testid="stSidebar"] button[kind="primary"] {
        background: #E8F1F7;
        color: var(--ops-navy);
        font-weight: 800;
        box-shadow: inset 3px 0 0 #5EA9C9;
    }
    [data-testid="stSidebar"] button[kind="primary"] p { color: var(--ops-navy); }
    [data-testid="stSidebar"] button[kind="secondary"] p { color: #D9E7F2; }
    [data-testid="stSidebar"] hr { border-color: rgba(255, 255, 255, 0.12); }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; }
    }
</style>
""",
        unsafe_allow_html=True,
    )


def _visible_routes() -> list[Route]:
    return [route for route in ROUTES if has_permission(route.permission)]


def _visible_navigation_groups(routes: list[Route]) -> list[tuple[str, list[Route]]]:
    route_by_label = {route.label: route for route in routes}
    grouped: list[tuple[str, list[Route]]] = []
    for group_name, labels in NAVIGATION_GROUPS:
        group_routes = [route_by_label[label] for label in labels if label in route_by_label]
        if group_routes:
            grouped.append((group_name, group_routes))
    grouped_labels = {route.label for _, group_routes in grouped for route in group_routes}
    ungrouped = [route for route in routes if route.label not in grouped_labels]
    if ungrouped:
        grouped.append(("MORE", ungrouped))
    return grouped


def _render_sidebar(current_user: dict[str, str], routes: list[Route]) -> Route:
    labels = [route.label for route in routes]
    if not labels:
        raise RuntimeError("Tài khoản hiện tại không có quyền truy cập màn hình nào.")

    active = st.session_state.get("active_page", labels[0])
    if active not in labels:
        active = labels[0]
        st.session_state.active_page = active

    with st.sidebar:
        st.markdown(
            "<div class='ops-brand'><div class='ops-brand-kicker'>SHIPMENT OPERATIONS</div><div class='ops-brand-title'>⚓ LOGISTICS PRO</div><div class='ops-brand-status'>Daily control room · local workspace</div></div>",
            unsafe_allow_html=True,
        )
        st.caption(f"{current_user['display_name']} · {current_user['role']}")
        if not AUTH_REQUIRED:
            st.warning(
                "Đang chạy Local Admin. Bật AUTH_REQUIRED khi triển khai nhiều người dùng.",
                icon=None,
            )

        for group_name, group_routes in _visible_navigation_groups(routes):
            st.markdown(f"<div class='ops-nav-group'>{group_name}</div>", unsafe_allow_html=True)
            for route in group_routes:
                button_key = "nav_button_" + re.sub(r"[^a-z0-9]+", "_", route.label.casefold()).strip("_")
                if st.button(
                    f"{route.icon}  {route.label}",
                    key=button_key,
                    use_container_width=True,
                    type="primary" if route.label == active else "secondary",
                ):
                    st.session_state.active_page = route.label
                    st.rerun()
        selected_label = st.session_state.get("active_page", labels[0])

        st.divider()
        if st.button("🔄 Reload Data", use_container_width=True):
            st.session_state.needs_refresh = True
            refresh_core_data(force=True)
            st.rerun()
        if st.button("📦 Nạp kho lưu trữ", use_container_width=True):
            st.session_state.db_archive = load_archived_data()
            st.toast("Đã nạp dữ liệu lưu trữ.")
        if AUTH_REQUIRED and st.button("Đăng xuất", use_container_width=True):
            logout()
        st.caption("LOG-C07 · 3.1.3-router-hotfix")

    return next(route for route in routes if route.label == selected_label)


def _load_view(route: Route) -> Callable[[], None]:
    module = importlib.import_module(route.module)
    view = getattr(module, route.function, None)
    if view is None or not callable(view):
        raise AttributeError(
            f"Không tìm thấy hàm {route.function} trong module {route.module}."
        )
    return view


def _render_route(route: Route) -> None:
    try:
        _load_view(route)()
    except Exception as exc:
        LOGGER.exception("Cannot render route %s", route.label)
        st.error(f"Không thể mở màn hình **{route.label}**.")
        st.caption(
            "Lỗi đã được giữ lại trên trang thay vì làm giao diện trắng. "
            "Có thể sao chép chi tiết dưới đây để kiểm tra."
        )
        st.exception(exc)
        with st.expander("Chi tiết kỹ thuật", expanded=False):
            st.code(traceback.format_exc(), language="text")
        def go_dashboard() -> None:
            st.session_state.active_page = "Dashboard"

        def request_reload() -> None:
            st.session_state.needs_refresh = True

        c1, c2 = st.columns(2)
        c1.button(
            "Về Dashboard",
            use_container_width=True,
            key="route_error_dashboard",
            on_click=go_dashboard,
        )
        c2.button(
            "Tải lại dữ liệu",
            use_container_width=True,
            key="route_error_reload",
            on_click=request_reload,
        )


def _assert_route_access(current_user: dict[str, str], route: Route) -> None:
    """Kiểm soát quyền tuyến tuyện quyền tại biên giao diện.

    sidebar chỉ hiển thị các tuyến được phép, nhưng người dùng có thể cố
    gắng thay đổi ``st.session_state.active_page`` trực tiếp. Kiểm tra này từ chối
    truy cập khi tài khoản không có quyền tuyến, không quan trọng trang thậ
    trên được lựa chọn như thế nào.
    """
    user = current_user or {}
    role = str(user.get("role", "viewer")).lower()
    if has_write_permission(route.permission) or has_permission(route.permission):
        return
    if role == "admin" or (user.get("username") and route.permission in ("dashboard", "tariff", "tracking", "knowledge")):
        return
    st.error(
        f"Tài khoản **{user.get('display_name', user.get('username', '?'))}** "
        f"không có quyền mở màn hình **{route.label}**. "
        "Liên hệ người quản trị nếu cần truy cập."
    )
    if st.button("Về Dashboard", key="route_access_denied_home"):
        st.session_state.active_page = "Dashboard"
        st.rerun()
    st.stop()


# ------------------------------------------------------------------ user management
def _render_user_management() -> None:
    """Màn hình quản lý tài khoản (chỉ Admin). Admin cũng có quyền toàn trọng."""
    from core.database import delete_user, load_users, update_user  # noqa: PLC0415
    from core.users import SUPPORTED_ROLES, UserError  # noqa: PLC0415

    st.subheader("Quản lý người dùng")
    st.caption(
        "Chỉ người quản trị mới xem được màn hình này. Việc tạo/vô hiệu hóa tài khoản "
        "được ghi nhận trong nhật ký kiểm toán."
    )
    users = load_users()
    if not users:
        st.info("Chưa có tài khoản nào.")
        return

    st.markdown("**Các tài khoản hiện có**")
    for uname, doc in users.items():
        if doc.get("is_deleted"):
            continue
        with st.expander(
            f"{doc.get('display_name', uname)} • {doc.get('username')} • {doc.get('role', '?')}",
            expanded=False,
        ):
            st.caption(
                f"Trạng thái: {'Hoạt động' if doc.get('active', True) else 'Vô hiệu hóa'} "
                f"· trả về cuối: {doc.get('last_login_at') or 'chưa đăng nhập'}"
            )
            new_role = st.selectbox(
                "Vai trò",
                list(SUPPORTED_ROLES),
                index=list(SUPPORTED_ROLES).index(str(doc.get("role", "support")).lower())
                if str(doc.get("role", "support")).lower() in SUPPORTED_ROLES
                else 0,
                key=f"um_role_{uname}",
            )
            active = st.checkbox("Hoạt động", value=bool(doc.get("active", True)), key=f"um_active_{uname}")
            c1, c2 = st.columns(2)
            if c1.button("Áp dụng thay đổi", key=f"um_apply_{uname}"):
                result = update_user(
                    username=uname,
                    payload={"role": new_role, "active": active},
                    actor=str(current_user().get("username", "admin")),
                )
                if result:
                    st.success("Áp dụng thành công.")
                    st.rerun()
                st.error("Không đổi được tài khoản.")
            if c2.button("Xóa tài khoản", key=f"um_del_{uname}", type="secondary"):
                if uname == str(current_user().get("username")):
                    st.warning("Không thể xóa tài khoản đang đăng nhập.")
                elif delete_user(uname, actor=str(current_user().get("username", "admin"))):
                    st.success("Có thể xóa tài khoản.")
                    st.rerun()

    with st.expander("Tạo tài khoản mới", expanded=False):
        username = st.text_input("Tên đăng nhập (3-30 ký tự, chữ thường)", key="um_new_username").strip().lower()
        display_name = st.text_input("Tên hiển thị", key="um_new_display").strip()
        email = st.text_input("Email (không bắt buộc)", key="um_new_email").strip().lower()
        role = st.selectbox("Vai trò", list(SUPPORTED_ROLES), index=1, key="um_new_role")
        password = st.text_input("Mật khảu (tối thiểu 8 ký tự)", type="password", key="um_new_password")
        confirm = st.text_input("Nhập lại mật khảu", type="password", key="um_new_confirm")
        if st.button("Tạo tài khoản", type="primary", key="um_new_submit"):
            _create_user_from_admin(username, display_name, email, role, password, confirm)


# ----------------------------------------------------------------- admin helpers
def _create_user_from_admin(
    username: str,
    display_name: str,
    email: str,
    role: str,
    password: str,
    confirm: str,
) -> bool:
    from core.database import save_user  # noqa: PLC0415
    from core.users import build_user_document, UserError  # noqa: PLC0415

    if password != confirm:
        st.error("Mật khảu xác nhận không khớp.")
        return False
    try:
        document = build_user_document(
            username=username,
            password=password,
            display_name=display_name or username,
            role=role,
            created_by=str(current_user().get("username", "admin")),
        )
        if email:
            document["email"] = email
    except UserError as exc:
        st.error(str(exc))
        return False
    if not save_user(document):
        st.error("Không lưu được tài khoản. Kiểm tra kết nốii database.")
        return False
    st.success(f"Đã tạo tài khoản **{username}** với vai trò {role}.")
    st.rerun()
    return True


def main() -> None:
    """Render toàn bộ ứng dụng trong mỗi lần Streamlit rerun."""
    _configure_page()
    initialize_state()

    current_user = require_login()
    if current_user is None:
        st.stop()

    try:
        with st.spinner("Đang đồng bộ dữ liệu hệ thống..."):
            refresh_core_data()
    except Exception as exc:
        LOGGER.exception("Core data refresh failed")
        st.session_state.last_db_error = str(exc)

    if st.session_state.get("last_db_error"):
        st.error(f"Cơ sở dữ liệu chưa sẵn sàng: {st.session_state.last_db_error}")

    routes = _visible_routes()
    route = _render_sidebar(current_user, routes)
    _assert_route_access(current_user, route)
    if route.label == "Người dùng":
        _render_user_management()
    else:
        _render_route(route)

