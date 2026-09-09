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

from core.auth import current_user, has_permission, has_write_permission, logout, require_login
from core.config import AUTH_REQUIRED
from core.database import load_archived_data
from core.state import initialize_state, refresh_core_data
from views.ui_kit import COMPONENT_CSS

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
    Route("Dịch Thuật DeepL", "🌐", "translation", "views.translation", "ui_translation"),
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
        ("Tra Cứu Thuế", "Sổ Tay Kinh Nghiệm", "Dịch Thuật DeepL"),
    ),
    (
        "QUẢN TRỊ",
        ("Người Dùng",),
    ),
)


SIDEBAR_WIDTH = 268

# Donor visual language (logistics-demo) expressed as CSS design tokens. The
# legacy ``--ops-*`` variables stay defined because Level B views still
# reference them (readiness card in agreements.py, a few badges elsewhere).
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&display=swap');
:root {
    --lg-navy-900: #061024; --lg-navy-800: #0b2545; --lg-navy-700: #123168; --lg-navy-600: #1c4482;
    --lg-navy-500: #2c5aa0; --lg-blue-500: #2f6fed; --lg-blue-600: #1d54c9;
    --lg-green: #16a34a; --lg-amber: #d97706; --lg-red: #dc2626;
    --lg-bg: #eef2f8; --lg-surface: #ffffff; --lg-line: #e2e8f0;
    --lg-ink: #0f1c33; --lg-muted: #4b5b72; --lg-faint: #8695a8;
    --lg-font: 'Be Vietnam Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    --lg-header-h: 60px; --lg-sidebar-w: 268px;
    /* legacy aliases used by Level B views */
    --ops-ink: #0f1c33; --ops-muted: #4b5b72; --ops-navy: #0b2545; --ops-navy-2: #123168; --ops-blue: #2f6fed;
    --ops-bg: #eef2f8; --ops-surface: #ffffff; --ops-line: #e2e8f0; --ops-amber: #d97706; --ops-red: #dc2626; --ops-green: #16a34a;
}
html, body, .stApp, [data-testid="stAppViewContainer"], .stMarkdown, button, input, textarea, select {
    font-family: var(--lg-font);
}
.stApp { background: var(--lg-bg); color: var(--lg-ink); }
h1, h2, h3, h4, h5, h6 { color: var(--lg-navy-800); font-family: var(--lg-font); letter-spacing: -0.01em; }
h1 { font-size: 1.6rem !important; font-weight: 800 !important; }
h2 { font-size: 1.3rem !important; font-weight: 700 !important; }
h3 { font-size: 1.1rem !important; font-weight: 700 !important; }
a { color: var(--lg-blue-600); }

/* ---------- main column ---------- */
[data-testid="stMainBlockContainer"] {
    max-width: 1440px; padding: calc(var(--lg-header-h) + 1rem) 2rem 3.5rem !important; margin: 0 auto;
}
[data-testid="stMain"] { background: var(--lg-bg); }

/* ---------- Streamlit header: keep only the sidebar toggle button ---------- */
header[data-testid="stHeader"] { background: transparent !important; pointer-events: none; box-shadow: none; }
header[data-testid="stHeader"] button { pointer-events: auto; }
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapseButton"] button {
    color: var(--lg-navy-800) !important; background: var(--lg-surface) !important;
    border: 1px solid var(--lg-line) !important; border-radius: 8px !important;
}
[data-testid="stSidebarCollapseButton"] button { color: #e2e8f0 !important; background: rgba(255,255,255,.08) !important; border-color: rgba(255,255,255,.15) !important; }
[data-testid="stDecoration"] { display: none; }

/* ---------- fixed top header (donor) ---------- */
.st-key-lg_topbar {
    position: fixed; top: 0 !important; left: 0; width: 100% !important; height: var(--lg-header-h);
    margin: 0 !important; z-index: 999989; background: var(--lg-surface); border-bottom: 1px solid var(--lg-line);
    padding: 0 1.25rem 0 1.25rem; box-sizing: border-box; box-shadow: 0 1px 2px rgba(6, 16, 36, .04);
    gap: .75rem !important; flex-wrap: nowrap !important;
}
.stApp:has([data-testid="stExpandSidebarButton"]) .st-key-lg_topbar { padding-left: 3.6rem; }
.st-key-lg_topbar > [data-testid="stElementContainer"], .st-key-lg_topbar > [data-testid="stLayoutWrapper"] { min-width: 0; }
.st-key-lg_topbar .lg-topbar-title { color: var(--lg-navy-800); font-weight: 800; font-size: 1rem; letter-spacing: -.01em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.2; }
.st-key-lg_topbar .lg-topbar-crumb { color: var(--lg-faint); font-size: .68rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; white-space: nowrap; }
.st-key-lg_topbar .lg-topbar-user { display: flex; align-items: center; gap: .5rem; white-space: nowrap; }
.st-key-lg_topbar .lg-avatar { width: 32px; height: 32px; border-radius: 999px; background: var(--lg-navy-800); color: #fff; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: .8rem; }
.st-key-lg_topbar .lg-user-name { color: var(--lg-ink); font-weight: 700; font-size: .82rem; line-height: 1.15; }
.st-key-lg_topbar .lg-user-role { color: var(--lg-faint); font-size: .68rem; text-transform: uppercase; letter-spacing: .06em; }
.st-key-lg_topbar [data-testid="stTextInput"] { max-width: 520px; }
.st-key-lg_topbar [data-testid="stTextInputRootElement"] { background: #f4f7fc; border-radius: 999px !important; }
.st-key-lg_topbar [data-testid="stTextInputRootElement"] input { font-size: .86rem; }
.st-key-lg_topbar [data-testid="stMarkdownContainer"] p { margin: 0; }
.st-key-lg_topbar [data-testid="stPopover"] button { border-radius: 999px !important; }
@media (min-width: 769px) {
    .stApp:has(section[data-testid="stSidebar"][aria-expanded="true"]) .st-key-lg_topbar { left: var(--lg-sidebar-w); width: calc(100% - var(--lg-sidebar-w)) !important; }
}
@media (max-width: 768px) {
    .st-key-lg_topbar { padding-right: .75rem; gap: .5rem !important; overflow: hidden; }
    .st-key-lg_topbar .lg-topbar-crumb { display: none; }
    .st-key-lg_topbar .lg-topbar-user > div { display: none; }
    .st-key-lg_topbar .lg-topbar-title { font-size: .92rem; max-width: 34vw; }
    .st-key-lg_topbar [data-testid="stTextInput"] { min-width: 0; }
    .st-key-lg_topbar .st-key-lg_topbar_title { flex: 0 1 auto !important; min-width: 0; }
    .st-key-lg_topbar .st-key-lg_topbar_user { flex: 0 0 auto !important; }
}
/* the fixed topbar / bottom nav leave zero-height wrappers in the flow: cancel their flex gap */
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:has(> .st-key-lg_topbar),
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:has(> .st-key-lg_bottom_nav),
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(> .stMarkdown > div > [data-testid="stMarkdownContainer"] > style:only-child) { height: 0; margin-bottom: -16px; overflow: visible; }
/* the global-search results panel */
.st-key-lg_search_results { position: fixed; top: var(--lg-header-h); right: 1rem; width: min(520px, calc(100vw - 2rem)); z-index: 999988; background: var(--lg-surface); border: 1px solid var(--lg-line); border-top: 0; border-radius: 0 0 12px 12px; padding: .5rem .75rem .75rem; box-shadow: 0 12px 30px rgba(6,16,36,.14); }

/* ---------- sidebar (donor: navy, 268px) ---------- */
section[data-testid="stSidebar"] {
    background: var(--lg-navy-800) !important; border-right: 1px solid var(--lg-navy-600) !important;
    width: var(--lg-sidebar-w) !important; min-width: var(--lg-sidebar-w) !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] { width: 0 !important; min-width: 0 !important; }
[data-testid="stSidebarContent"] { padding: .35rem .6rem 0 !important; }
[data-testid="stSidebarUserContent"] { padding: .35rem .5rem 1.5rem !important; }
[data-testid="stSidebarHeader"] { padding: .35rem .2rem 0 !important; }
[data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { color: #e2e8f0; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.12); margin: .6rem 0; }
.lg-brand { display: flex; align-items: center; gap: .7rem; padding: .35rem .15rem .9rem; border-bottom: 1px solid rgba(255,255,255,.12); margin-bottom: .6rem; }
.lg-brand-mark { width: 38px; height: 38px; border-radius: 10px; background: var(--lg-blue-500); color: #fff; display: inline-flex; align-items: center; justify-content: center; font-size: 22px; flex: 0 0 auto; }
.lg-brand-title { color: #fff !important; font-size: 1.05rem; font-weight: 800; letter-spacing: -.01em; line-height: 1.15; }
.lg-brand-sub { color: #9fb3d6 !important; font-size: .68rem; letter-spacing: .1em; text-transform: uppercase; font-weight: 700; margin-top: .15rem; }
.lg-nav-group { color: #9fb3d6 !important; font-size: .64rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; margin: .9rem 0 .3rem .25rem; }
.lg-env-pill { display: inline-flex; align-items: center; gap: .3rem; background: rgba(217,119,6,.18); color: #fcd34d !important; border: 1px solid rgba(252,211,77,.4); border-radius: 999px; padding: .12rem .55rem; font-size: .66rem; font-weight: 800; letter-spacing: .08em; margin-bottom: .5rem; }
.lg-env-note { color: #fcd34d !important; font-size: .68rem; line-height: 1.35; background: rgba(217,119,6,.12); border: 1px solid rgba(252,211,77,.3); border-radius: 8px; padding: .4rem .55rem; margin: 0 0 .5rem; }
.lg-sidebar-user { display: flex; align-items: center; gap: .6rem; padding: .55rem .6rem; background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.1); border-radius: 10px; margin: .2rem 0 .6rem; }
.lg-sidebar-user .lg-avatar { width: 32px; height: 32px; border-radius: 999px; background: var(--lg-blue-500); color: #fff; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: .8rem; flex: 0 0 auto; }
.lg-sidebar-user-name { color: #fff !important; font-weight: 700; font-size: .84rem; line-height: 1.15; }
.lg-sidebar-user-role { color: #9fb3d6 !important; font-size: .66rem; text-transform: uppercase; letter-spacing: .08em; }
/* nav buttons */
[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(> .stButton) { margin-bottom: 0; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .2rem; }
[data-testid="stSidebar"] .stButton, [data-testid="stSidebar"] .stButton > div { width: 100% !important; }
[data-testid="stSidebar"] .stButton button {
    width: 100% !important; justify-content: flex-start !important; text-align: left; min-height: 40px; padding: .35rem .7rem;
    border-radius: 8px !important; border: 1px solid transparent !important; background: transparent !important;
    color: #d6e0f0 !important; font-weight: 500; box-shadow: none !important; transition: background .12s ease;
}
[data-testid="stSidebar"] .stButton button:hover { background: rgba(255,255,255,.08) !important; color: #fff !important; }
[data-testid="stSidebar"] .stButton button:focus-visible { outline: 2px solid var(--lg-blue-500) !important; outline-offset: 1px; }
[data-testid="stSidebar"] .stButton button[kind="primary"] { background: var(--lg-blue-500) !important; color: #fff !important; font-weight: 700; box-shadow: 0 4px 12px rgba(47,111,237,.35) !important; }
[data-testid="stSidebar"] .stButton button[kind="primary"]:hover { background: var(--lg-blue-600) !important; }
[data-testid="stSidebar"] .stButton button p, [data-testid="stSidebar"] .stButton button span { color: inherit !important; font-size: .86rem; }
[data-testid="stSidebar"] .stButton button [data-testid="stIconMaterial"] { font-size: 20px; margin-right: .45rem; color: inherit !important; }
[data-testid="stSidebar"] .stButton button[kind="secondary"] [data-testid="stIconMaterial"] { color: #9fb3d6 !important; }
[data-testid="stSidebar"] .stButton button > div { width: 100%; justify-content: flex-start; }
[data-testid="stSidebar"] .stButton button > div > span { align-items: center; justify-content: flex-start; width: 100%; }
[data-testid="stSidebar"] .stButton button p { text-align: left; white-space: normal; line-height: 1.25; }
/* utility rows */
[data-testid="stSidebar"] .st-key-lg_side_utils .stButton button { border: 1px solid rgba(255,255,255,.14) !important; background: rgba(255,255,255,.04) !important; min-height: 36px; font-size: .8rem; }
[data-testid="stSidebar"] .stAlert { border-radius: 8px; }
[data-testid="stSidebar"] .stAlert p { color: #0f1c33; }

/* ---------- buttons ---------- */
.stButton button, [data-testid="stFormSubmitButton"] button, [data-testid="stDownloadButton"] button, [data-testid="stPopover"] button {
    border-radius: 8px !important; font-weight: 600 !important; min-height: 40px; box-shadow: none; font-family: var(--lg-font);
}
[data-testid="stMain"] button[kind="primary"], [data-testid="stMain"] button[data-testid="stBaseButton-primaryFormSubmit"] {
    background: var(--lg-navy-800) !important; border: 1px solid var(--lg-navy-800) !important; color: #fff !important; font-weight: 700 !important;
}
[data-testid="stMain"] button[kind="primary"]:hover, [data-testid="stMain"] button[data-testid="stBaseButton-primaryFormSubmit"]:hover { background: var(--lg-navy-700) !important; border-color: var(--lg-navy-700) !important; }
[data-testid="stMain"] button[kind="primary"] p, [data-testid="stMain"] button[kind="primary"] span, [data-testid="stMain"] button[data-testid="stBaseButton-primaryFormSubmit"] p { color: #fff !important; }
[data-testid="stMain"] button[kind="secondary"], [data-testid="stMain"] button[data-testid="stBaseButton-secondaryFormSubmit"] {
    background: var(--lg-surface) !important; border: 1px solid var(--lg-line) !important; color: var(--lg-navy-800) !important;
}
[data-testid="stMain"] button[kind="secondary"]:hover, [data-testid="stMain"] button[data-testid="stBaseButton-secondaryFormSubmit"]:hover { border-color: var(--lg-navy-500) !important; background: #f4f7fc !important; color: var(--lg-navy-800) !important; }
[data-testid="stMain"] button[kind="secondary"] p, [data-testid="stMain"] button[kind="secondary"] span { color: var(--lg-navy-800) !important; }
[data-testid="stMain"] button[kind="tertiary"] { color: var(--lg-blue-600) !important; }
[data-testid="stMain"] button:disabled, [data-testid="stMain"] button:disabled p, [data-testid="stMain"] button:disabled span { opacity: .55; cursor: not-allowed; }
button:focus-visible, input:focus-visible, textarea:focus-visible, [role="combobox"]:focus-visible { outline: 3px solid rgba(47,111,237,.35) !important; outline-offset: 2px !important; }

/* ---------- cards, forms, inputs ---------- */
[data-testid="stMain"] [data-testid="stVerticalBlock"][overflow="visible"]:has(> [data-testid="stElementContainer"]),
[data-testid="stMain"] [data-testid="stForm"], [data-testid="stMain"] [data-testid="stColumn"][overflow="visible"] {
    border-color: var(--lg-line);
}
[data-testid="stMain"] [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"][overflow="visible"] { border-radius: 10px; }
[data-testid="stMain"] [data-testid="stVerticalBlock"][overflow="visible"] { background: var(--lg-surface); }
[data-testid="stMain"] [data-testid="stForm"] { background: var(--lg-surface); border-radius: 10px; }
[data-testid="stMain"] [data-testid="stVerticalBlock"][overflow="visible"] [data-testid="stVerticalBlock"][overflow="visible"] { background: #f8fafc; }
[data-testid="stMain"] [data-testid="stMetric"] { background: var(--lg-surface); border: 1px solid var(--lg-line); border-radius: 10px; padding: .75rem .9rem; box-shadow: 0 1px 2px rgba(6,16,36,.04); }
[data-testid="stMetricLabel"] p { color: var(--lg-muted) !important; font-size: .7rem !important; font-weight: 800 !important; letter-spacing: .06em; text-transform: uppercase; }
[data-testid="stMetricValue"] { color: var(--lg-navy-800); font-weight: 800; font-size: 1.45rem !important; }
[data-testid="stMain"] [data-testid="stTextInputRootElement"], [data-testid="stMain"] [data-testid="stNumberInputContainer"], [data-testid="stMain"] [data-baseweb="select"] > div, [data-testid="stMain"] [data-testid="stTextArea"] textarea, [data-testid="stMain"] [data-baseweb="input"] {
    border-radius: 8px !important; background: var(--lg-surface);
}
[data-testid="stMain"] [data-testid="stWidgetLabel"] p { color: var(--lg-muted) !important; font-size: .78rem !important; font-weight: 700 !important; }
[data-testid="stMain"] [data-testid="stExpander"] details { background: var(--lg-surface); border: 1px solid var(--lg-line); border-radius: 10px; }
[data-testid="stMain"] [data-testid="stExpander"] summary { font-weight: 700; color: var(--lg-navy-800); }
[data-testid="stMain"] [data-testid="stExpander"] summary:hover { color: var(--lg-blue-600); }
[data-testid="stMain"] [data-testid="stDataFrame"], [data-testid="stMain"] [data-testid="stDataEditor"] { border-radius: 10px; overflow: hidden; }
[data-testid="stMain"] .stCaption, [data-testid="stMain"] [data-testid="stCaptionContainer"] p { color: var(--lg-muted) !important; }
[data-testid="stMain"] hr { border-color: var(--lg-line); margin: 1rem 0; }

/* ---------- tabs ---------- */
[data-testid="stTabs"] [role="tablist"] { gap: .25rem; border-bottom: 1px solid var(--lg-line); overflow-x: auto; scrollbar-width: thin; }
[data-testid="stTab"] { padding: .55rem .85rem !important; border-radius: 8px 8px 0 0; color: var(--lg-muted) !important; font-weight: 600; white-space: nowrap; }
[data-testid="stTab"] p { font-size: .86rem !important; font-weight: 700 !important; }
[data-testid="stTab"][aria-selected="true"] { color: var(--lg-navy-800) !important; background: var(--lg-surface); }
[data-testid="stTab"][aria-selected="true"] p { color: var(--lg-navy-800) !important; }
[data-testid="stTabs"] .react-aria-SelectionIndicator, [data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: var(--lg-navy-800) !important; height: 3px; border-radius: 3px 3px 0 0; }

/* ---------- alerts / toasts / dialogs / popovers ---------- */
[data-testid="stAlert"] { border-radius: 10px; }
[data-testid="stAlert"] [data-testid="stAlertContainer"] { border-radius: 10px; border: 1px solid transparent; }
[data-testid="stAlertContentInfo"] { color: #1e3a8a; }
[data-testid="stAlertContentSuccess"] { color: #14532d; }
[data-testid="stAlertContentWarning"] { color: #7c4a03; }
[data-testid="stAlertContentError"] { color: #991b1b; }
[data-testid="stAlert"]:has([data-testid="stAlertContentInfo"]) [data-testid="stAlertContainer"] { background: #eef4ff; border-color: #c7d7fb; }
[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) [data-testid="stAlertContainer"] { background: #ecfdf3; border-color: #a6e3bd; }
[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) [data-testid="stAlertContainer"] { background: #fff7ed; border-color: #fed7aa; }
[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) [data-testid="stAlertContainer"] { background: #fef2f2; border-color: #fecaca; }
[data-testid="stToast"] { background: var(--lg-navy-800) !important; color: #fff !important; border-radius: 10px !important; border: 1px solid var(--lg-navy-600) !important; box-shadow: 0 10px 30px rgba(6,16,36,.35) !important; }
[data-testid="stToast"] p, [data-testid="stToast"] span { color: #fff !important; }
[data-testid="stDialog"] [role="dialog"] { border-radius: 14px; border: 1px solid var(--lg-line); box-shadow: 0 24px 60px rgba(6,16,36,.3); font-family: var(--lg-font); }
[data-testid="stDialog"] h2[slot="title"] p { color: var(--lg-navy-800); font-weight: 800; }
[data-testid="stPopoverBody"], [data-baseweb="popover"] > div { border-radius: 12px; border: 1px solid var(--lg-line); }
[data-testid="stBottomBlockContainer"] { background: var(--lg-bg); }

/* ---------- mobile bottom navigation (donor) ---------- */
@media (min-width: 769px) { .st-key-lg_bottom_nav { display: none !important; } }
@media (max-width: 768px) {
    [data-testid="stMainBlockContainer"] { padding-left: 1rem !important; padding-right: 1rem !important; padding-bottom: 6.5rem !important; }
    .st-key-lg_bottom_nav {
        position: fixed; left: 0; right: 0; bottom: 0; width: 100% !important; margin: 0 !important; z-index: 999989;
        background: var(--lg-surface); border-top: 1px solid var(--lg-line); box-shadow: 0 -6px 20px rgba(6,16,36,.08);
        padding: 6px 4px calc(6px + env(safe-area-inset-bottom)); gap: 0 !important; flex-wrap: nowrap !important;
    }
    .st-key-lg_bottom_nav [data-testid="stElementContainer"] { flex: 1 1 0 !important; min-width: 0; width: auto !important; }
    .st-key-lg_bottom_nav button { min-height: 52px; border: 0 !important; background: transparent !important; box-shadow: none !important; padding: 4px 2px !important; border-radius: 10px !important; }
    .st-key-lg_bottom_nav button > div > span { flex-direction: column; gap: 2px; align-items: center; }
    .st-key-lg_bottom_nav button p { font-size: 10.5px !important; font-weight: 600 !important; margin: 0; white-space: nowrap !important; }
    .st-key-lg_bottom_nav button [data-testid="stMarkdownContainer"] { overflow: visible; }
    .st-key-lg_bottom_nav button [data-testid="stIconMaterial"] { font-size: 22px; }
    .st-key-lg_bottom_nav button[kind="primary"] { background: #eef4ff !important; }
    .st-key-lg_bottom_nav button[kind="primary"] * { color: var(--lg-blue-600) !important; }
    .st-key-lg_bottom_nav button[kind="secondary"] * { color: var(--lg-muted) !important; }
    /* phone layout: one-column forms, large touch targets, no hover-only actions */
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; }
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100% !important; width: 100% !important; min-width: 100% !important; }
    [data-testid="stMain"] .stButton button { min-height: 44px; }
    h1 { font-size: 1.35rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.25rem !important; }
}
@media (min-width: 769px) and (max-width: 1024px) {
    [data-testid="stMainBlockContainer"] { padding-left: 1.25rem !important; padding-right: 1.25rem !important; }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition-duration: .01ms !important; animation-duration: .01ms !important; } }
</style>
"""


def _configure_page() -> None:
    st.set_page_config(
        page_title="LOGISTICS PRO",
        layout="wide",
        page_icon="⚓",
        initial_sidebar_state=SIDEBAR_WIDTH,
    )
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    st.markdown(GLOBAL_CSS + "<style>" + COMPONENT_CSS + "</style>", unsafe_allow_html=True)


def _search_results(term: str) -> list[tuple[str, str, str]]:
    """LG08: federated lookup across shipments and customers (RBAC-safe: the
    destination route still enforces access at the route boundary)."""
    results: list[tuple[str, str, str]] = []  # (label, primary_id, context)
    shipments = st.session_state.get("db_shipments", {})
    for sid, sdata in shipments.items():
        sid_str = str(sid)
        haystack = sid_str.lower() + " " + str((sdata or {}).get("customer") or "").lower()
        if term in haystack:
            results.append(("Lô hàng", sid_str, str((sdata or {}).get("customer") or "Chưa có khách hàng")))
            if len(results) >= 5:
                break
    customers = st.session_state.get("db_customers", {})
    for cid, cdata in customers.items():
        cname = str((cdata or {}).get("name", "")).lower()
        if term in cname or term in str(cid).lower():
            results.append(("Khách hàng", str((cdata or {}).get("name") or cid), f"Mã KH {cid}"))
            if len(results) >= 8:
                break
    return results


def _render_global_search(routes: list[Route]) -> None:
    """LG08: Global/federated search across shipments, customers.

    Rendered inside the fixed top header; results drop down under it."""
    search_term = st.text_input(
        "🔍 Tìm nhanh",
        placeholder="Tìm mã lô, khách hàng, container...",
        key="global_search_input",
        label_visibility="collapsed",
        icon=":material/search:",
        width="stretch",
    )
    if not search_term or len(search_term.strip()) < 2:
        return

    term = search_term.strip().lower()
    results = _search_results(term)
    with st.container(key="lg_search_results"):
        if not results:
            st.caption("Không tìm thấy kết quả phù hợp.")
            return
        st.caption(f"{len(results)} kết quả cho “{search_term.strip()}”")
        for r_type, r_id, r_ctx in results[:8]:
            icon_name = ":material/local_shipping:" if r_type == "Lô hàng" else ":material/group:"
            if st.button(f"{r_type}: {r_id} · {r_ctx}", key=f"gs_btn_{r_type}_{r_id}", icon=icon_name, use_container_width=True):
                if r_type == "Lô hàng":
                    st.session_state.active_shipment_id = r_id
                    st.session_state.dashboard_active_shipment_id = r_id
                    st.session_state.active_page = "Tổng Quan Công Việc"
                else:
                    st.session_state.active_page = "Khách Hàng"
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


ROUTE_ICONS: dict[str, str] = {
    "Tổng Quan Công Việc": "dashboard",
    "Việc Cần Xử Lý": "checklist",
    "Tạo Lô Mới": "add_box",
    "Theo Dõi Vận Chuyển": "travel_explore",
    "Khách Hàng": "group",
    "Ngữ Cảnh Đối Tác": "hub",
    "Kinh Doanh & Báo Giá": "request_quote",
    "Thỏa Thuận & Bàn Giao": "handshake",
    "Hợp Đồng": "description",
    "Đối Soát Tài Chính": "fact_check",
    "Thu Tiền & Công Nợ": "payments",
    "Công Nợ A Bò": "account_balance_wallet",
    "Báo Cáo CEO": "monitoring",
    "Tra Cứu Thuế": "manage_search",
    "Sổ Tay Kinh Nghiệm": "menu_book",
    "Dịch Thuật DeepL": "translate",
    "Người Dùng": "manage_accounts",
}

# Donor mobile bottom navigation: 5 slots mapped onto existing route labels.
MOBILE_NAV: tuple[tuple[str, str, str | None], ...] = (
    ("Tổng quan", "dashboard", "Tổng Quan Công Việc"),
    ("Lô hàng", "local_shipping", "Việc Cần Xử Lý"),
    ("Hợp đồng", "description", "Hợp Đồng"),
    ("Tài chính", "payments", "Thu Tiền & Công Nợ"),
    ("Thêm", "more_horiz", None),
)

_GROUP_ICONS = {
    "VẬN HÀNH": "local_shipping",
    "KINH DOANH & ĐỐI TÁC": "handshake",
    "TÀI CHÍNH & ĐỐI SOÁT": "payments",
    "CÔNG CỤ & THAM KHẢO": "construction",
    "QUẢN TRỊ": "admin_panel_settings",
    "MORE": "more_horiz",
}


def _nav_key(label: str) -> str:
    return "nav_button_" + re.sub(r"[^a-z0-9]+", "_", label.casefold()).strip("_")


def _go(label: str) -> None:
    st.session_state.active_page = label
    st.rerun()


def _initials(name: str) -> str:
    parts = [part for part in re.split(r"\s+", str(name or "").strip()) if part]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _group_of(label: str) -> str:
    for group_name, labels in NAVIGATION_GROUPS:
        if label in labels:
            return group_name
    return "MORE"


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
        from html import escape as _esc

        st.markdown(
            "<div class='lg-brand'><span class='lg-brand-mark'>⚓</span><div>"
            "<div class='lg-brand-title'>LOGISTICS PRO</div>"
            "<div class='lg-brand-sub'>Bàn làm việc vận hành</div></div></div>",
            unsafe_allow_html=True,
        )
        if ENV_IDENTITY in ("STAGING", "PREVIEW"):
            st.markdown("<span class='lg-env-pill'>🛠️ PREVIEW / STAGING · KHÔNG PHẢI APP NHÂN VIÊN</span>", unsafe_allow_html=True)
            st.error("Dữ liệu STAGING - Không ghi lời thực")
        st.markdown(
            f"<div class='lg-sidebar-user'><span class='lg-avatar'>{_esc(_initials(current_user.get('display_name', '')))}</span>"
            f"<div><div class='lg-sidebar-user-name'>{_esc(str(current_user.get('display_name', '')))}</div>"
            f"<div class='lg-sidebar-user-role'>{_esc(str(current_user.get('role', '')))}</div></div></div>",
            unsafe_allow_html=True,
        )
        if not AUTH_REQUIRED:
            st.markdown(
                "<div class='lg-env-note'>⚠️ Đang chạy Local Admin. Bật AUTH_REQUIRED khi triển khai nhiều người dùng.</div>",
                unsafe_allow_html=True,
            )

        selected_label = st.session_state.get("active_page", labels[0])
        for group_name, group_routes in _visible_navigation_groups(routes):
            st.markdown(f"<div class='lg-nav-group'>{group_name}</div>", unsafe_allow_html=True)
            for route in group_routes:
                icon_name = ROUTE_ICONS.get(route.label)
                if st.button(
                    route.label,
                    key=_nav_key(route.label),
                    icon=f":material/{icon_name}:" if icon_name else None,
                    use_container_width=True,
                    type="primary" if route.label == active else "secondary",
                ):
                    _go(route.label)

        st.divider()
        with st.container(key="lg_side_utils"):
            if st.button("Reload Data", key="side_reload_data", icon=":material/refresh:", use_container_width=True):
                st.session_state.needs_refresh = True
                refresh_core_data(force=True)
                st.rerun()
            if st.button("Nạp kho lưu trữ", key="side_load_archive", icon=":material/inventory_2:", use_container_width=True):
                st.session_state.db_archive = load_archived_data()
                st.toast("Đã nạp dữ liệu lưu trữ.")
            if AUTH_REQUIRED and st.button("Đăng xuất", key="side_logout", icon=":material/logout:", use_container_width=True):
                logout()
        st.caption("LOG-C07 · 3.1.3-router-hotfix · hybrid-ui")

    return next(route for route in routes if route.label == selected_label)


def _render_top_header(current_user: dict[str, str], routes: list[Route], route: Route) -> None:
    """Donor top header: breadcrumb + page title, global search, user chip."""
    from html import escape as _esc

    with st.container(key="lg_topbar", horizontal=True, wrap=False, vertical_alignment="center", gap="medium"):
        with st.container(key="lg_topbar_title", width="content"):
            st.markdown(
                f"<div class='lg-topbar-crumb'>{_esc(_group_of(route.label))}</div>"
                f"<div class='lg-topbar-title'>{_esc(route.label)}</div>",
                unsafe_allow_html=True,
            )
        _render_global_search(routes)
        with st.container(key="lg_topbar_user", width="content"):
            st.markdown(
                f"<div class='lg-topbar-user'><span class='lg-avatar'>{_esc(_initials(current_user.get('display_name', '')))}</span>"
                f"<div><div class='lg-user-name'>{_esc(str(current_user.get('display_name', '')))}</div>"
                f"<div class='lg-user-role'>{_esc(str(current_user.get('role', '')))}</div></div></div>",
                unsafe_allow_html=True,
            )


@st.dialog("Thêm")
def _mobile_more_dialog(routes: list[Route], active: str) -> None:
    """Phone “Thêm” sheet: every permitted route, grouped like the sidebar."""
    st.caption("Tất cả màn hình bạn có quyền mở.")
    for group_name, group_routes in _visible_navigation_groups(routes):
        st.markdown(f"**{group_name}**")
        for route in group_routes:
            icon_name = ROUTE_ICONS.get(route.label)
            if st.button(
                route.label,
                key=f"more_{_nav_key(route.label)}",
                icon=f":material/{icon_name}:" if icon_name else None,
                use_container_width=True,
                type="primary" if route.label == active else "secondary",
            ):
                _go(route.label)
    if AUTH_REQUIRED and st.button("Đăng xuất", key="more_logout", icon=":material/logout:", use_container_width=True):
        logout()


def _render_mobile_nav(routes: list[Route], active: str) -> None:
    """Donor bottom navigation (CSS shows it only ≤768px)."""
    allowed = {route.label for route in routes}
    with st.container(key="lg_bottom_nav", horizontal=True, wrap=False, gap="small"):
        for label, icon_name, target in MOBILE_NAV:
            if target is not None and target not in allowed:
                continue
            is_active = target == active
            if st.button(
                label,
                key=f"mnav_{icon_name}",
                icon=f":material/{icon_name}:",
                width="stretch",
                type="primary" if is_active else "secondary",
            ):
                if target is None:
                    _mobile_more_dialog(routes, active)
                else:
                    _go(target)


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
    _render_top_header(current_user, routes, route)
    # Bottom nav is position:fixed (phone only) — render before the route so it
    # stays available even when a view calls st.stop().
    _render_mobile_nav(routes, route.label)
    _assert_route_access(current_user, route)
    if route.label == "Người dùng":
        _render_user_management()
    else:
        _render_route(route)

