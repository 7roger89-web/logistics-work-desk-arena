"""Donor layout: persistent left sidebar (>=720px), header, mobile drawer + bottom nav.

Navigation is real Streamlit state driven (``st.session_state['lg_page']`` and
``st.session_state['lg_mobile_nav_open']``) — no raw HTML anchors/query-params.
"""
from __future__ import annotations

import streamlit as st

from .helpers import actor, set_page
from .theme import CSS

# (label, emoji, slug) rows grouped by header
NAV_GROUPS: list[tuple[str, list[tuple[str, str, str]]]] = [
    ("VẬN HÀNH", [
        ("Tổng Quan", "🏠", "home"),
        ("Việc Cần Xử Lý", "✅", "tasks"),
        ("Lô Hàng", "📦", "shipments"),
        ("Tạo Lô Mới", "➕", "new_shipment"),
        ("Theo Dõi Vận Chuyển", "🛰", "tracking"),
    ]),
    ("KINH DOANH", [
        ("Khách Hàng", "🧑‍💼", "customers"),
        ("Ngữ Cảnh", "🧭", "context"),
        ("Kinh Doanh-Báo Giá", "💱", "quote"),
        ("Thỏa Thuận", "🤝", "agreement"),
        ("Hợp Đồng", "📄", "contracts"),
    ]),
    ("TÀI CHÍNH", [
        ("Thu Tiền-Công Nợ", "💰", "receive"),
        ("Đối Soát Tài Chính", "🧮", "reconcile"),
        ("Công Nợ Đối Tác", "🏢", "partner_debt"),
        ("Báo Cáo CEO", "📊", "ceo"),
    ]),
    ("CÔNG CỤ", [
        ("Tra Cứu Thuế-HS", "🧾", "tariff"),
        ("Sổ Tay", "📒", "notebook"),
        ("Dịch Thuật", "🌐", "translate"),
    ]),
    ("QUẢN TRỊ", [
        ("Người Dùng", "👥", "admin"),
    ]),
]

_FLAT = [(g, l, e, s) for g, rows in NAV_GROUPS for (l, e, s) in rows]


def _nav_button(group: str, label: str, emoji: str, slug: str) -> None:
    cur = st.session_state.get("lg_page", "home")
    active = slug == cur or (slug == "shipments" and cur in ("shipment_detail", "new_shipment"))
    btn = st.button(
        f"{emoji} {label}",
        key=f"nav_{slug}_{group}_{label}",
        use_container_width=True,
        type="secondary" if not active else "primary",
        on_click=set_page,
        args=(slug,),
    )


def _render_nav() -> None:
    for group, rows in NAV_GROUPS:
        st.markdown(
            f'<div style="font-size:11px;font-weight:800;color:#64748b;'
            f'text-transform:uppercase;letter-spacing:.05em;padding:8px 6px 4px">{group}</div>',
            unsafe_allow_html=True,
        )
        for label, emoji, slug in rows:
            _nav_button(group, label, emoji, slug)


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:10px;padding:6px 4px 14px">'
            '<div style="width:40px;height:40px;border-radius:12px;background:#0f2a4a;color:#fff;'
            'display:grid;place-items:center;font-weight:800">LP</div>'
            '<div><div style="font-weight:800;color:#0f2a4a;font-size:16px">LOGISTICS PRO</div>'
            '<div style="font-size:12px;color:#64748b">Quản lý vận hành & công nợ</div></div></div>',
            unsafe_allow_html=True,
        )
        _render_nav()
        st.markdown("<hr>", unsafe_allow_html=True)
        u = actor()
        st.caption(f"👤 {u['display_name']} · {u['role'].upper()}")


def render_header(page_label: str, page_sub: str = "") -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    # Custom hamburger opens a mobile drawer (real Streamlit state).
    col_h, col_b, col_r = st.columns([0.6, 2.6, 2.0])
    with col_h:
        if st.button("☰", key="hamburger_toggle", help="Mở menu"):
            st.session_state["lg_mobile_nav_open"] = not st.session_state.get(
                "lg_mobile_nav_open", False
            )
            st.rerun()
    with col_b:
        st.markdown(
            f'<div style="padding:4px 0"><div style="font-size:18px;font-weight:800;color:#0f2a4a">'
            f'{page_label}</div>'
            f'<div style="font-size:12.5px;color:#64748b">{page_sub}</div></div>',
            unsafe_allow_html=True,
        )
    with col_r:
        u = actor()
        st.markdown(
            '<div style="text-align:right;padding:4px 0">'
            f'<div style="font-weight:700;color:#1f2937;font-size:14px">👤 {u["display_name"]}</div>'
            f'<div style="font-size:12px;color:#64748b">Hôm nay · {_today_vi()}</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)


def _today_vi() -> str:
    from datetime import date

    d = date.today()
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def render_mobile_drawer() -> None:
    """Show a drawer when the hamburger state is open (mobile / narrow)."""
    if not st.session_state.get("lg_mobile_nav_open"):
        return
    st.markdown(
        '<div style="font-size:11px;font-weight:800;color:#64748b;'
        'text-transform:uppercase;letter-spacing:.05em;padding:4px 2px 2px;'
        'border-bottom:1px solid #e2e8f0">MENU ĐIỀU HƯỚNG</div>',
        unsafe_allow_html=True,
    )
    for group, rows in NAV_GROUPS:
        st.markdown(
            f'<div style="font-size:11px;font-weight:800;color:#94a3b8;'
            f'text-transform:uppercase;letter-spacing:.04em;padding:6px 2px 2px">{group}</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(1)
        for label, emoji, slug in rows:
            cur = st.session_state.get("lg_page", "home")
            active = slug == cur
            if st.button(
                f"{emoji} {label}",
                key=f"drw_{slug}",
                use_container_width=True,
                type="primary" if active else "secondary",
                on_click=_open_drawer_page,
                args=(slug,),
            ):
                pass
    if st.button("✕ Đóng menu", key="drawer_close", use_container_width=True):
        st.session_state["lg_mobile_nav_open"] = False
        st.rerun()


def _open_drawer_page(slug: str) -> None:
    set_page(slug)
    st.session_state["lg_mobile_nav_open"] = False


def render_bottom_nav() -> None:
    items = [
        ("home", "🏠", "Tổng quan"),
        ("tasks", "✅", "Việc cần"),
        ("shipments", "📦", "Lô hàng"),
        ("contracts", "📄", "Hợp đồng"),
        ("receive", "💰", "Thu tiền"),
    ]
    # Bottom nav is rendered as normal widgets in a small area (mobile).
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:11px;font-weight:800;color:#64748b;'
        'text-transform:uppercase;letter-spacing:.05em">ĐIỀU HƯỚNG NHANH</div>',
        unsafe_allow_html=True,
    )
    cur = st.session_state.get("lg_page", "home")
    cols = st.columns(len(items))
    for c, (slug, emoji, label) in zip(cols, items):
        active = slug == cur or (slug == "shipments" and cur in ("shipment_detail", "new_shipment"))
        with c:
            st.button(
                f"{emoji} {label}",
                key=f"bottom_{slug}",
                use_container_width=True,
                type="primary" if active else "secondary",
                on_click=set_page,
                args=(slug,),
            )
