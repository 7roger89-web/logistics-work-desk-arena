"""Äiá»ƒm Ä‘iá»u phá»‘i giao diá»‡n Streamlit cá»§a LOGISTICS PRO.

Má»i mÃ£ render Ä‘Æ°á»£c Ä‘áº·t trong ``main()``. Launcher pháº£i gá»i ``main()`` á»Ÿ má»—i
láº§n Streamlit rerun; khÃ´ng dÃ¹ng ``from views.web_app import *`` vÃ¬ Python cache
module sáº½ khiáº¿n trang tráº¯ng sau láº§n tÆ°Æ¡ng tÃ¡c Ä‘áº§u tiÃªn.
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

from core.auth import has_permission, logout, require_login
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
    Route("Dashboard", "ðŸ ", "dashboard", "views.dashboard", "ui_dashboard"),
    Route("Review Queue", "ðŸ§­", "dashboard", "views.review_queue", "ui_review_queue"),
    Route("Táº¡o LÃ´ Má»›i", "âž•", "shipment_create", "views.shipment", "ui_create_new_shipment"),
    Route("KhÃ¡ch HÃ ng", "ðŸ‘¥", "customers", "views.customers", "ui_customers"),
    Route("Entity Context", "ðŸ§­", "dashboard", "views.entity_context", "ui_entity_context"),
    Route("Sales & BÃ¡o GiÃ¡", "ðŸ¤", "sales", "views.quotations", "ui_sales_module"),
    Route("Há»£p Äá»“ng", "ðŸ“œ", "contracts", "views.contracts", "ui_contracts_management"),
    Route("Thu Tiá»n & CÃ´ng Ná»£", "ðŸ’°", "receivables", "views.finance", "ui_receivables_management"),
    Route("Finance Review", "FR", "receivables", "views.finance_review", "ui_finance_review"),
    Route("CÃ´ng ná»£ A BÃ²", "ðŸ§¾", "receivables", "views.partner_reconciliation", "ui_partner_reconciliation_desk"),
    Route("BÃ¡o CÃ¡o CEO", "ðŸ“Š", "reports", "views.reports", "ui_reports_dashboard"),
    Route("Tra Cá»©u Thuáº¿", "ðŸ”Ž", "tariff", "views.tariff", "ui_super_tariff_hub"),
    Route("Tracking", "ðŸŒ", "tracking", "views.tracking", "ui_tracking_tool"),
    Route("Sá»• Tay Kinh Nghiá»‡m", "ðŸ“”", "knowledge", "views.knowledge_base", "ui_knowledge_base"),
)


# The route labels remain stable so existing permissions, deep links, and
# session state keep working.  The grouping is presentation-only: operations
# is the front door, while finance and partner review stay available behind it.
NAVIGATION_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "OPERATIONS",
        ("Dashboard", "Review Queue", "Táº¡o LÃ´ Má»›i", "Tracking"),
    ),
    (
        "COMMERCIAL CONTEXT",
        ("KhÃ¡ch HÃ ng", "Entity Context", "Sales & BÃ¡o GiÃ¡", "Há»£p Äá»“ng"),
    ),
    (
        "FINANCE & REVIEW",
        ("Finance Review", "Thu Tiá»n & CÃ´ng Ná»£", "CÃ´ng ná»£ A BÃ²", "BÃ¡o CÃ¡o CEO"),
    ),
    (
        "TOOLS & REFERENCE",
        ("Tra Cá»©u Thuáº¿", "Sá»• Tay Kinh Nghiá»‡m"),
    ),
)


def _configure_page() -> None:
    st.set_page_config(page_title="LOGISTICS PRO", layout="wide", page_icon="âš“")
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
        raise RuntimeError("TÃ i khoáº£n hiá»‡n táº¡i khÃ´ng cÃ³ quyá»n truy cáº­p mÃ n hÃ¬nh nÃ o.")

    active = st.session_state.get("active_page", labels[0])
    if active not in labels:
        active = labels[0]
        st.session_state.active_page = active

    with st.sidebar:
        st.markdown(
            "<div class='ops-brand'><div class='ops-brand-kicker'>SHIPMENT OPERATIONS</div><div class='ops-brand-title'>âš“ LOGISTICS PRO</div><div class='ops-brand-status'>Daily control room Â· local workspace</div></div>",
            unsafe_allow_html=True,
        )
        st.caption(f"{current_user['display_name']} Â· {current_user['role']}")
        if not AUTH_REQUIRED:
            st.warning(
                "Äang cháº¡y Local Admin. Báº­t AUTH_REQUIRED khi triá»ƒn khai nhiá»u ngÆ°á»i dÃ¹ng.",
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
        if st.button("ðŸ”„ Reload Data", use_container_width=True):
            st.session_state.needs_refresh = True
            refresh_core_data(force=True)
            st.rerun()
        if st.button("ðŸ“¦ Náº¡p kho lÆ°u trá»¯", use_container_width=True):
            st.session_state.db_archive = load_archived_data()
            st.toast("ÄÃ£ náº¡p dá»¯ liá»‡u lÆ°u trá»¯.")
        if AUTH_REQUIRED and st.button("ÄÄƒng xuáº¥t", use_container_width=True):
            logout()
        st.caption("LOG-C07 Â· 3.1.3-router-hotfix")

    return next(route for route in routes if route.label == selected_label)


def _load_view(route: Route) -> Callable[[], None]:
    module = importlib.import_module(route.module)
    view = getattr(module, route.function, None)
    if view is None or not callable(view):
        raise AttributeError(
            f"KhÃ´ng tÃ¬m tháº¥y hÃ m {route.function} trong module {route.module}."
        )
    return view


def _render_route(route: Route) -> None:
    try:
        _load_view(route)()
    except Exception as exc:
        LOGGER.exception("Cannot render route %s", route.label)
        st.error(f"KhÃ´ng thá»ƒ má»Ÿ mÃ n hÃ¬nh **{route.label}**.")
        st.caption(
            "Lá»—i Ä‘Ã£ Ä‘Æ°á»£c giá»¯ láº¡i trÃªn trang thay vÃ¬ lÃ m giao diá»‡n tráº¯ng. "
            "CÃ³ thá»ƒ sao chÃ©p chi tiáº¿t dÆ°á»›i Ä‘Ã¢y Ä‘á»ƒ kiá»ƒm tra."
        )
        st.exception(exc)
        with st.expander("Chi tiáº¿t ká»¹ thuáº­t", expanded=False):
            st.code(traceback.format_exc(), language="text")
        def go_dashboard() -> None:
            st.session_state.active_page = "Dashboard"

        def request_reload() -> None:
            st.session_state.needs_refresh = True

        c1, c2 = st.columns(2)
        c1.button(
            "Vá» Dashboard",
            use_container_width=True,
            key="route_error_dashboard",
            on_click=go_dashboard,
        )
        c2.button(
            "Táº£i láº¡i dá»¯ liá»‡u",
            use_container_width=True,
            key="route_error_reload",
            on_click=request_reload,
        )


def main() -> None:
    """Render toÃ n bá»™ á»©ng dá»¥ng trong má»—i láº§n Streamlit rerun."""
    _configure_page()
    initialize_state()

    current_user = require_login()
    if current_user is None:
        st.stop()

    try:
        with st.spinner("Äang Ä‘á»“ng bá»™ dá»¯ liá»‡u há»‡ thá»‘ng..."):
            refresh_core_data()
    except Exception as exc:
        LOGGER.exception("Core data refresh failed")
        st.session_state.last_db_error = str(exc)

    if st.session_state.get("last_db_error"):
        st.error(f"CÆ¡ sá»Ÿ dá»¯ liá»‡u chÆ°a sáºµn sÃ ng: {st.session_state.last_db_error}")

    routes = _visible_routes()
    route = _render_sidebar(current_user, routes)
    _render_route(route)

