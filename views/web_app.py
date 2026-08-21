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
    Route("Tổng Quan Công Việc", "🏠", "dashboard", "views.dashboard", "ui_dashboard"),
    Route("Việc Cần Xử Lý", "🧭", "dashboard", "views.review_queue", "ui_review_queue"),
    Route("Tạo Lô Mới", "➕", "shipment_create", "views.shipment", "ui_create_new_shipment"),
    Route("Khách Hàng", "👥", "customers", "views.customers", "ui_customers"),
    Route("Ngữ Cảnh Đối Tác", "🧭", "dashboard", "views.entity_context", "ui_entity_context"),
    Route("Kinh Doanh & Báo Giá", "🤝", "sales", "views.quotations", "ui_sales_module"),
    Route("Thỏa Thuận & Bàn Giao", "🤝", "sales", "views.agreements", "ui_agreements_module"),
    Route("Hợp Đồng", "📜", "contracts", "views.contracts", "ui_contracts_management"),
    Route("Thu Tiền & Công Nợ", "💰", "receivables", "views.finance", "ui_receivables_management"),
    Route("Đối Soát Tài Chính", "FR", "receivables", "views.finance_review", "ui_finance_review"),
    Route("Công Nợ A Bò", "🧾", "receivables", "views.partner_reconciliation", "ui_partner_reconciliation_desk"),
    Route("Báo Cáo CEO", "📊", "reports", "views.reports", "ui_reports_dashboard"),
    Route("Tra Cứu Thuế", "🔎", "tariff", "views.tariff", "ui_super_tariff_hub"),
    Route("Theo Dõi Vận Chuyển", "🌐", "tracking", "views.tracking", "ui_tracking_tool"),
    Route("Sổ Tay Kinh Nghiệm", "📔", "knowledge", "views.knowledge_base", "ui_knowledge_base"),
    # Màn hình quản lý tài khoản, chỉ dành cho vai trò admin.
    Route("Người Dùng", "👤", "admin", "views.web_app", "_render_user_management"),
)


# The route labels remain stable so existing permissions, deep links, and
# session state keep working.  The grouping is presentation-only: operations
# is the front door, while finance and partner review stay available behind it.
NAVIGATION_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "VẬN HÀNH",
        ("Tổng Quan Công Việc", "Việc Cần Xử Lý", "Tạo Lô Mới", "Theo Dõi Vận Chuyển"),
    ),
    (
        "KINH DOANH & ĐỐI TÁC",
        ("Khách Hàng", "Ngữ Cảnh Đối Tác", "Kinh Doanh & Báo Giá", "Thỏa Thuận & Bàn Giao", "Hợp Đồng"),
    ),
    (
        "TÀI CHÍNH & ĐỐI SOÁT",
        ("Đối Soát Tài Chính", "Thu Tiền & Công Nợ", "Công Nợ A Bò", "Báo Cáo CEO"),
    ),
    (
        "CÔNG CỤ & THAM KHẢO",
        ("Tra Cứu Thuế", "Sổ Tay Kinh Nghiệm"),
    ),
    (
        "QUẢN TRỊ",
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
        --ops-ink: #0F172A;
        --ops-muted: #64748B;
        --ops-navy: #1E3A8A;
        --ops-navy-2: #1E40AF;
        --ops-blue: #2563EB;
        --ops-bg: #F8FAFC;
        --ops-surface: #FFFFFF;
        --ops-line: #E2E8F0;
        --ops-amber: #B45309;
        --ops-red: #DC2626;
        --ops-green: #15803D;
    }
    .stApp { background: var(--ops-bg); color: var(--ops-ink); }
    h1, h2, h3, h4 { color: var(--ops-navy); font-family: 'Segoe UI', system-ui, sans-serif; letter-spacing: -0.015em; }
    .block-container { max-width: 1680px; padding-top: 1.1rem; padding-bottom: 3rem; margin: 0 auto; }
    
    /* P2P: Responsive Content Widths */
    /* Forms and standard pages should be narrower for readability */
    .stMain .block-container { max-width: 1200px !important; }
    
    /* Shipment Workspace & Tables can be wider */
    div[data-testid="stVerticalBlock"]:has(div[data-testid="stExpander"]) .block-container,
    div[data-testid="stTable"] .block-container { 
        max-width: 1680px !important; 
    }
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
        background: #0F172A !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1rem !important; }
    
    /* P2P: Force Sidebar Text Colors - HIGH CONTRAST */
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown div,
    [data-testid="stSidebar"] [data-testid="stExpander"] summary p { 
        color: #E2E8F0 !important; /* Slate 200 - High contrast on dark bg */
        opacity: 1 !important;
    }
    
    /* Specific overrides for group headings */
    [data-testid="stSidebar"] [data-testid="stExpander"] summary p {
        color: #94A3B8 !important; /* Slate 400 for headers */
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover p {
        color: #F8FAFC !important;
    }
    
    .ops-brand {
        padding: 0.35rem 0.2rem 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.12);
        margin-bottom: 0.85rem;
    }
    .ops-brand-kicker { color: #8FB7D3; font-size: 0.66rem; font-weight: 800; letter-spacing: 0.14em; }
    .ops-brand-title { color: #FFFFFF; font-size: 1.22rem; font-weight: 800; letter-spacing: -0.02em; margin-top: 0.15rem; }
    .ops-brand-status { color: #A9C6D9; font-size: 0.72rem; margin-top: 0.3rem; }
    
    /* P2P: Expander styling for navigation groups in Sidebar */
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background: transparent !important;
        border: none !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary {
        color: #94A3B8 !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary p {
        color: #94A3B8 !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover p {
        color: #FFFFFF !important;
    }
    
    /* P2P: Sidebar Button Fix - ULTIMATE DARK OVERRIDE V3 */
    /* High specificity to ensure visibility of navigation and utility buttons */
    [data-testid="stSidebar"] button[kind="secondary"],
    [data-testid="stSidebar"] [data-testid="baseButton-secondary"],
    [data-testid="stSidebar"] [data-testid="stExpander"] button {
        background-color: rgba(255, 255, 255, 0.07) !important;
        color: #F1F5F9 !important; /* Slate 100 - Near white for max readability */
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        text-align: left !important;
        justify-content: flex-start !important;
        width: 100% !important;
        opacity: 1 !important;
    }
    
    /* Ensure icons and text inside buttons are white/bright */
    [data-testid="stSidebar"] button[kind="secondary"] p,
    [data-testid="stSidebar"] button[kind="secondary"] span {
        color: #F1F5F9 !important;
    }
    
    [data-testid="stSidebar"] button:hover {
        background-color: rgba(255, 255, 255, 0.12) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: #FFFFFF !important;
    }
    
    /* Force text color inside ALL sidebar buttons to prevent inheritance leaks */
    [data-testid="stSidebar"] button p,
    [data-testid="stSidebar"] button span,
    [data-testid="stSidebar"] button div,
    [data-testid="stSidebar"] button label {
        color: inherit !important;
        font-weight: 500 !important;
    }
    
    /* Active/Primary Navigation Item in Sidebar - High Visibility Blue */
    [data-testid="stSidebar"] button[kind="primary"],
    [data-testid="stSidebar"] [data-testid="baseButton-primary"] {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: 1px solid #3B82F6 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2) !important;
    }
    
    /* Final safety: Never allow white backgrounds in sidebar buttons */
    [data-testid="stSidebar"] button[kind="secondary"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Global Primary Buttons (Main Content Area) */
    .main button[kind="primary"] {
        background-color: #1E40AF !important;
        color: #FFFFFF !important;
        border: 1px solid #1D4ED8 !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
        border-radius: 8px !important;
    }
    .main button[kind="primary"]:hover {
        background-color: #1D4ED8 !important;
        border-color: #2563EB !important;
    }
    .main button[kind="primary"] p, 
    .main button[kind="primary"] span,
    .main button[kind="primary"] div {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    
    /* Global Secondary Buttons (Main Content Area Only) */
    /* Use .block-container to ensure these styles don't leak into the sidebar */
    .block-container button[kind="secondary"],
    .stMain button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        border: 1px solid #CBD5E1 !important;
    }
    .main button[kind="secondary"]:hover {
        background-color: #F8FAFC !important;
        border-color: #94A3B8 !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    [data-testid="stSidebar"] hr { border-color: rgba(255, 255, 255, 0.12); }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; }
    }
</style>
""",
        unsafe_allow_html=True,
    )


def _render_global_search(routes: list[Route]) -> None:
    """LG08: Global/federated search across shipments, customers, tasks.

    Results obey RBAC: only routes the user can see produce results, and the
    destination still enforces access at the route boundary."""
    search_term = st.text_input(
        "🔍 Tìm nhanh",
        placeholder="Mã lô, khách hàng, container, đơn...",
        key="global_search_input",
        label_visibility="collapsed",
    )
    if not search_term or len(search_term.strip()) < 2:
        return

    term = search_term.strip().lower()
    results: list[tuple[str, str, str]] = []  # (label, primary_id, context)

    # Shipment search — shipments are accessible to all authorized roles.
    shipments = st.session_state.get("db_shipments", {})
    for sid, sdata in shipments.items():
        sid_str = str(sid)
        if term in sid_str.lower():
            results.append(("Lô hàng", sid_str, "Tìm theo mã lô"))
            break
    # Customer search — customers visible to all authorized roles.
    customers = st.session_state.get("db_customers", {})
    for _cid, cdata in customers.items():
        cname = str(cdata.get("name", "")).lower()
        if term in cname:
            results.append(("Khách hàng", cdata.get("name", "?"), "Tìm theo tên khách"))
            if len(results) >= 5:
                break

    if not results:
        st.caption("Không tìm thấy kết quả phù hợp.")
        return

    st.caption(f"{len(results)} kết quả:")
    for r_type, r_id, r_ctx in results[:5]:
        if st.button(f"{r_type}: {r_id}", key=f"gs_btn_{r_type}_{r_id}", use_container_width=True):
            if r_type == "Lô hàng" and "shipment_id" in st.session_state:
                st.session_state.active_shipment_id = r_id
            st.session_state.active_page = "Tổng Quan Công Việc"
            st.rerun()


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
        from core.config import ENV_IDENTITY
        brand_kicker = "VẬN HÀNH LÔ HÀNG"
        brand_status = "Phòng điều khiển hàng ngày · không gian nội bộ"
        
        if ENV_IDENTITY in ("STAGING", "PREVIEW"):
            brand_kicker = "🛠️ PREVIEW / STAGING"
            brand_status = "⚠️ KHÔNG PHẢI APP NHÂN VIÊN"
            st.error("Dữ liệu STAGING - Không ghi lời thực")

        st.markdown(
            f"<div class='ops-brand'><div class='ops-brand-kicker'>{brand_kicker}</div><div class='ops-brand-title'>⚓ LOGISTICS PRO</div><div class='ops-brand-status'>{brand_status}</div></div>",
            unsafe_allow_html=True,
        )
        st.caption(f"{current_user['display_name']} · {current_user['role']}")
        # LG08: Global search entry point — one federated lookup for daily work.
        _render_global_search(routes)
        if not AUTH_REQUIRED:
            st.warning(
                "Đang chạy Local Admin. Bật AUTH_REQUIRED khi triển khai nhiều người dùng.",
                icon=None,
            )

        selected_label = st.session_state.get("active_page", labels[0])
        for group_name, group_routes in _visible_navigation_groups(routes):
            # LG08: Compact navigation — collapsible groups.
            # Auto-expand the group containing the active page; collapse others.
            group_active = selected_label in {route.label for route in group_routes}
            with st.expander(group_name, expanded=group_active):
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
            st.session_state.active_page = "Tổng Quan Công Việc"

        def request_reload() -> None:
            st.session_state.needs_refresh = True

        c1, c2 = st.columns(2)
        c1.button(
            "Về Trang Tổng Quan",
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
    """Kiểm soát quyền truy cập tuyến tại biên giao diện.

    sidebar chỉ hiển thị các tuyến được phép, nhưng người dùng có thể cố
    gắng thay đổi ``st.session_state.active_page`` trực tiếp. Kiểm tra này từ chối
    truy cập khi tài khoản không có quyền tuyến, không quan trọng trang thậ
    trên được lựa chọn như thế nào.
    """
    user = current_user or {}
    if has_permission(route.permission):
        return
    st.error(
        f"Tài khoản **{user.get('display_name', user.get('username', '?'))}** "
        f"không có quyền mở màn hình **{route.label}**. "
        "Liên hệ người quản trị nếu cần truy cập."
    )
    if st.button("Về Trang Tổng Quan", key="route_access_denied_home"):
        st.session_state.active_page = "Tổng Quan Công Việc"
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
        password = st.text_input("Mật khẩu (tối thiểu 8 ký tự)", type="password", key="um_new_password")
        confirm = st.text_input("Nhập lại mật khẩu", type="password", key="um_new_confirm")
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
        # UX-STAB P1: Only show spinner when data is NOT already loaded or needs refresh.
        # On every rerun (e.g., form close/cancel), refresh_core_data() returns
        # immediately if data_loaded=True and needs_refresh=False — but the spinner
        # was still blocking the UI visually, making the page appear "stuck".
        _needs_data_sync = not st.session_state.get("data_loaded", False) or st.session_state.get("needs_refresh", False)
        if _needs_data_sync:
            with st.spinner("Đang đồng bộ dữ liệu hệ thống..."):
                refresh_core_data()
        else:
            refresh_core_data()  # Returns immediately (cached, no DB work)
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

