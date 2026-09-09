"""LOGI-GOOD EXACT — Streamlit shell (theme CSS + chrome + router).

Renders the Logi-good visual shell: top header, desktop sidebar, mobile
bottom navigation, drawer/search/quick-add/notifications overlays, and
dispatches to page renderers.  Real RBAC is enforced through core.auth before
any page render.
"""
from __future__ import annotations

import importlib
import logging
from typing import Any, Callable, Mapping

import streamlit as st

from core.auth import current_user, has_permission
from core.config import ENV_IDENTITY
from views.lg_core import esc, link_url

LOGGER = logging.getLogger("logistics_pro.lg")

# ---------------------------------------------------------------------------
# Pages registry  key -> (label, icon, permission, module, function)
# ---------------------------------------------------------------------------
PAGES: dict[str, tuple[str, str, str, str, str]] = {
    "home": ("Tổng Quan Công Việc", "🏠", "dashboard", "views.lg_pages", "home_page"),
    "tasks": ("Việc Cần Xử Lý", "🧭", "dashboard", "views.lg_pages", "tasks_page"),
    "shipments": ("Lô Hàng", "📦", "dashboard", "views.lg_pages", "shipments_page"),
    "new": ("Tạo Lô Mới", "➕", "shipment_create", "views.lg_pages", "newlot_page"),
    "tracking": ("Theo Dõi Vận Chuyển", "🌐", "tracking", "views.lg_pages", "tracking_page"),
    "customers": ("Khách Hàng", "👥", "customers", "views.lg_pages", "customers_page"),
    "partner": ("Ngữ Cảnh Đối Tác", "🧭", "dashboard", "views.lg_pages", "partner_page"),
    "quotes": ("Kinh Doanh & Báo Giá", "🤝", "sales", "views.lg_pages", "quotes_page"),
    "agreements": ("Thỏa Thuận & Bàn Giao", "🤝", "sales", "views.lg_pages", "agreements_page"),
    "contracts": ("Hợp Đồng", "📜", "contracts", "views.lg_pages", "contracts_page"),
    "finance": ("Thu Tiền & Công Nợ", "💰", "receivables", "views.lg_pages", "finance_page"),
    "reconcile": ("Đối Soát Tài Chính", "⚖️", "receivables", "views.lg_pages", "reconcile_page"),
    "partnerdebt": ("Công Nợ Đối Tác", "🧾", "receivables", "views.lg_pages", "partnerdebt_page"),
    "reports": ("Báo Cáo CEO", "📊", "reports", "views.lg_pages", "reports_page"),
    "tariff": ("Tra Cứu Thuế / HS", "🔎", "tariff", "views.lg_pages", "tariff_page"),
    "handbook": ("Sổ Tay Kinh Nghiệm", "📔", "knowledge", "views.lg_pages", "handbook_page"),
    "translate": ("Dịch Thuật", "🌐", "translation", "views.lg_pages", "translate_page"),
    "users": ("Người Dùng (Admin)", "👤", "admin", "views.lg_account", "users_page"),
    "account": ("Tài Khoản", "👤", "dashboard", "views.lg_account", "account_page"),
    "getfly": ("Nhập Dữ Liệu GetFly", "📤", "dashboard", "views.lg_pages", "intake_page"),
}

# Nav groups mirrored from Logi-good layout (permissions stay authoritative)
NAV_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("VẬN HÀNH", ("home", "tasks", "shipments", "new", "tracking")),
    ("KINH DOANH & ĐỐI TÁC", ("customers", "partner", "quotes", "agreements", "contracts")),
    ("TÀI CHÍNH & ĐỐI SOÁT", ("finance", "reconcile", "partnerdebt", "reports")),
    ("CÔNG CỤ & THAM KHẢO", ("tariff", "handbook", "translate")),
    ("QUẢN TRỊ", ("users",)),
)

MOBILE_BOTTOM: tuple[tuple[str, str, str], ...] = (
    ("home", "Tổng quan", "🏠"),
    ("shipments", "Lô hàng", "📦"),
    ("contracts", "Hợp đồng", "📜"),
    ("finance", "Tài chính", "💰"),
)

# Legacy label navigation (labels of the old route table)
LEGACY_LABEL_PAGE: dict[str, str] = {
    "Tổng Quan Công Việc": "home",
    "Việc Cần Xử Lý": "tasks",
    "Lô Hàng": "shipments",
    "Tạo Lô Mới": "new",
    "Khách Hàng": "customers",
    "Ngữ Cảnh Đối Tác": "partner",
    "Kinh Doanh & Báo Giá": "quotes",
    "Thỏa Thuận & Bàn Giao": "agreements",
    "Hợp Đồng": "contracts",
    "Thu Tiền & Công Nợ": "finance",
    "Đối Soát Tài Chính": "reconcile",
    "Công Nợ A Bò": "partnerdebt",
    "Báo Cáo CEO": "reports",
    "Tra Cứu Thuế": "tariff",
    "Theo Dõi Vận Chuyển": "tracking",
    "Sổ Tay Kinh Nghiệm": "handbook",
    "Dịch Thuật DeepL": "translate",
    "Người Dùng": "users",
}


def page_label(key: str) -> str:
    meta = PAGES.get(key)
    return meta[0] if meta else key


# ---------------------------------------------------------------------------
# CSS — Logi-good design tokens applied over Streamlit + custom chrome
# ---------------------------------------------------------------------------
def _css() -> str:
    return """
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700;800&display=swap');
:root {
  --lg-navy-950:#0a1f3a; --lg-navy-900:#0f2a4a; --lg-navy-800:#14365e;
  --lg-navy-700:#1a4d8f; --lg-navy-600:#1e5aa8; --lg-navy-100:#dbe7f5; --lg-navy-50:#eef4fb;
  --lg-bg:#eef1f6; --lg-ink:#1a2433; --lg-muted:#5b6b82; --lg-line:#e4e9f1;
}
html, body, [data-testid="stAppViewContainer"] { font-family:'Be Vietnam Pro','Segoe UI',system-ui,-apple-system,sans-serif; }
.stApp { background:var(--lg-bg); color:var(--lg-ink); }
.stApp a { color:#1e5aa8; }
h1,h2,h3,h4,[data-testid="stMarkdown"] h1,[data-testid="stMarkdown"] h2,[data-testid="stMarkdown"] h3 {
  font-family:'Be Vietnam Pro','Segoe UI',system-ui,sans-serif; color:var(--lg-navy-900); letter-spacing:-.01em; }
[data-testid="stMarkdown"] p { font-size:15px; line-height:1.55; color:#1e293b; }
/* ---------- hide native chrome: we render our own ---------- */
header[data-testid="stHeader"] { display:none !important; }
[data-testid="stSidebar"] { display:none !important; }
#MainMenu, footer, [data-testid="stStatusWidget"], [data-testid="stToolbar"] { visibility:hidden; height:0; }
[data-testid="stMainBlockContainer"] { max-width:1560px; padding-top:96px; padding-bottom:100px; }
@media (min-width:1200px) {
  [data-testid="stMainBlockContainer"] { margin-left:276px; max-width:calc(100vw - 276px); }
}
/* ---------- inputs ---------- */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input, [data-testid="stDateInput"] input {
  background:#fff !important; border:2px solid #e2e8f0 !important; border-radius:12px !important;
  min-height:48px; padding:8px 14px; font-size:15px; color:#1e293b;
}
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus,
[data-testid="stNumberInput"] input:focus, [data-testid="stDateInput"] input:focus { border-color:#1e5aa8 !important; box-shadow:none !important; }
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
  background:#fff !important; border:2px solid #e2e8f0 !important; border-radius:12px !important;
  min-height:48px; font-size:15px;
}
[data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div { border-color:#1e5aa8 !important; }
/* ---------- buttons ---------- */
.stButton > button, [data-testid="stBaseButton-secondary"], [data-testid="stFormSubmitButton"] button {
  border-radius:12px !important; font-weight:700 !important; min-height:44px !important;
  padding:6px 16px !important; border:2px solid #e2e8f0 !important; background:#fff !important;
  color:#0f2a4a !important; font-size:14.5px !important;
}
button[kind="primary"], [data-testid="stBaseButton-primary"] {
  background:#0f2a4a !important; color:#fff !important; border:2px solid #0f2a4a !important;
  box-shadow:0 6px 14px -8px rgba(15,42,74,.6) !important;
}
button[kind="primary"]:hover { background:#14365e !important; border-color:#14365e !important; }
.stButton > button:hover { border-color:#1e5aa8 !important; background:#f8fafc !important; }
button:disabled { opacity:.55 !important; }
[data-testid="stDownloadButton"] button {
  background:#0f2a4a !important; color:#fff !important; border-radius:12px !important;
  border:2px solid #0f2a4a !important; font-weight:700 !important; min-height:44px !important;
}
/* ---------- surfaces ---------- */
[data-testid="stVerticalBlockBorderWrapper"], [data-testid="stExpander"] {
  background:#fff !important; border:1px solid #e2e8f0 !important; border-radius:16px !important;
}
[data-testid="stExpander"] summary { font-weight:800; color:#0f2a4a; }
[data-testid="stMetric"] {
  background:#fff; border:1px solid #e2e8f0; border-radius:16px; padding:12px 14px; }
[data-testid="stMetricValue"] { font-weight:800; color:#0f2a4a; }
/* ---------- tabs (used by real modules) ---------- */
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap:6px; border-bottom:1px solid #e4e9f1; }
[data-testid="stTabs"] [data-baseweb="tab"] {
  background:#fff; border:2px solid #e2e8f0; border-radius:12px; padding:8px 16px;
  font-weight:700; font-size:14px; color:#475569; margin-right:6px;
}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
  background:#0f2a4a !important; border-color:#0f2a4a !important; color:#fff !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"], [data-testid="stTabs"] [data-baseweb="tab-border"] { display:none !important; }
[data-testid="stTabs"] [data-baseweb="tab-panel"] { padding-top:16px; }
[data-testid="stAlert"] { border-radius:14px !important; border-width:1px !important; }
/* ---------- custom chrome ---------- */
.lg-header { position:fixed; top:0; left:0; right:0; z-index:1200; height:64px; background:#fff;
  border-bottom:1px solid #e2e8f0; box-shadow:0 1px 12px rgba(15,42,74,.08); display:flex; align-items:center;
  gap:10px; padding:0 16px; }
.lg-brand { display:flex; align-items:center; gap:10px; min-width:0; text-decoration:none !important; }
.lg-brand-badge { width:40px; height:40px; border-radius:14px; flex:0 0 auto;
  background:linear-gradient(135deg,#1e5aa8,#0a1f3a); color:#fff; display:grid; place-items:center;
  font-size:18px; font-weight:800; box-shadow:0 2px 8px rgba(15,42,74,.35); }
.lg-brand-name { line-height:1.15; min-width:0; }
.lg-brand-name b { display:block; font-size:15px; color:#0f2a4a; white-space:nowrap; }
.lg-brand-name span { display:block; font-size:11.5px; color:#64748b; white-space:nowrap; }
.lg-proto { font-size:10px; font-weight:800; letter-spacing:.08em; background:#ede9fe; color:#6d28d9;
  border:1px solid #ddd6fe; border-radius:6px; padding:2px 6px; white-space:nowrap; }
.lg-header-right { margin-left:auto; display:flex; align-items:center; gap:6px; }
.lg-iconbtn { display:grid; place-items:center; width:44px; height:44px; border-radius:14px; color:#0f2a4a;
  text-decoration:none !important; font-size:20px; position:relative; }
.lg-iconbtn:hover { background:#f1f5f9; }
.lg-badge-dot { position:absolute; top:6px; right:6px; min-width:18px; height:18px; padding:0 4px; border-radius:999px;
  background:#dc2626; color:#fff; font-size:10.5px; font-weight:800; display:grid; place-items:center; }
.lg-userchip { display:flex; align-items:center; gap:8px; border:2px solid #e2e8f0; border-radius:14px;
  padding:4px 10px 4px 5px; min-height:44px; text-decoration:none !important; }
.lg-userchip:hover { border-color:#1e5aa8; }
.lg-avatar { width:32px; height:32px; border-radius:10px; display:grid; place-items:center; color:#fff;
  font-weight:800; font-size:13px; background:#1e5aa8; }
.lg-userchip span b { display:block; font-size:13px; color:#0f2a4a; line-height:1.1; }
.lg-userchip span small { font-size:11px; color:#64748b; }
.lg-search-pill { display:none; align-items:center; gap:10px; flex:1; max-width:560px; margin:0 auto;
  border:2px solid #e2e8f0; background:#f8fafc; border-radius:14px; padding:10px 14px; min-height:46px;
  color:#94a3b8; font-size:14.5px; text-decoration:none !important; }
.lg-search-pill:hover { border-color:#1e5aa8; }
.lg-btn-quick { display:inline-flex; align-items:center; gap:8px; background:#0f2a4a; color:#fff !important;
  border-radius:12px; font-weight:700; font-size:14.5px; padding:10px 16px; min-height:44px; text-decoration:none !important; }
.lg-btn-quick:hover { background:#14365e; }
@media (min-width:900px){ .lg-search-pill{ display:flex; } }
@media (min-width:1200px){ .lg-hamburger{ display:none !important; } }
@media (max-width:899px){ .lg-quickdesk{ display:none !important; } .lg-userchip .lg-user-meta{ display:none; } }
/* sidebar */
.lg-side { position:fixed; top:64px; left:0; bottom:0; width:264px; z-index:1100; background:#fff;
  border-right:1px solid #e2e8f0; overflow-y:auto; display:none; padding:12px 10px 24px; }
@media (min-width:1200px){ .lg-side{ display:block; } }
.lg-group-label { padding:8px 12px 4px; font-size:11.5px; font-weight:800; letter-spacing:.08em; color:#94a3b8; }
.lg-nav-item { display:flex; align-items:center; gap:10px; padding:10px 12px; border-radius:12px; margin-bottom:2px;
  color:#334155; text-decoration:none !important; font-size:14.5px; font-weight:500; line-height:1.3; }
.lg-nav-item:hover { background:#f1f5f9; color:#0f2a4a; }
.lg-nav-item.active { background:#0f2a4a; color:#fff; box-shadow:0 4px 10px -4px rgba(15,42,74,.6); font-weight:700; }
.lg-nav-item .lg-ic { width:22px; text-align:center; flex:0 0 auto; font-size:17px; }
.lg-help { margin:14px 8px 0; border-radius:18px; padding:16px; color:#fff;
  background:linear-gradient(135deg,#0f2a4a,#1e5aa8); }
.lg-help p { margin:0; }
.lg-help b { font-size:14px; }
.lg-help span { display:block; font-size:12.5px; color:#bfdbfe; margin-top:4px; }
.lg-help a { display:inline-flex; align-items:center; gap:6px; margin-top:10px; background:#fff; color:#0f2a4a;
  font-size:13px; font-weight:800; border-radius:10px; padding:8px 14px; text-decoration:none !important; }
/* mobile bottom nav */
.lg-bnav { position:fixed; left:0; right:0; bottom:0; z-index:1200; background:#fff; border-top:1px solid #e2e8f0;
  box-shadow:0 -4px 20px rgba(0,0,0,.06); display:grid; grid-template-columns:repeat(5,1fr);
  padding-bottom:env(safe-area-inset-bottom); }
@media (min-width:900px){ .lg-bnav{ display:none; } }
.lg-bnav a { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:2px;
  padding:8px 2px 6px; color:#94a3b8; text-decoration:none !important; font-size:11px; font-weight:700; min-height:58px; }
.lg-bnav a.active { color:#0f2a4a; }
.lg-bnav a .ic { font-size:21px; line-height:1; }
.lg-bnav a .dot { width:26px; height:4px; border-radius:99px; background:#0f2a4a; margin-top:1px; display:none; }
.lg-bnav a.active .dot { display:block; }
.lg-bnav .plus { width:48px; height:34px; margin-top:-8px; border-radius:16px 16px 8px 8px; background:#0f2a4a; color:#fff;
  display:grid; place-items:center; font-size:22px; box-shadow:0 6px 14px -6px rgba(15,42,74,.7); }
/* overlays */
.lg-sheet { position:fixed; inset:0; z-index:1500; background:rgba(15,23,42,.5); }
.lg-sheet .panel { position:absolute; background:#fff; box-shadow:-12px 0 40px rgba(0,0,0,.18); }
.lg-sheet.left .panel { left:0; top:0; bottom:0; width:min(320px,88vw); border-radius:0 20px 20px 0; overflow-y:auto; }
.lg-sheet.right .panel { right:0; top:0; bottom:0; width:min(420px,94vw); border-radius:20px 0 0 20px; overflow-y:auto; }
.lg-sheet.bottom .panel { left:0; right:0; bottom:0; max-width:640px; margin:0 auto; border-radius:22px 22px 0 0;
  max-height:88vh; overflow-y:auto; }
.lg-sheet .head { display:flex; align-items:center; justify-content:space-between; padding:16px 16px 8px;
  position:sticky; top:0; background:#fff; z-index:5; }
.lg-sheet .head b { font-size:17px; color:#0f2a4a; }
.lg-sheet .x { width:42px; height:42px; border-radius:12px; display:grid; place-items:center; color:#0f2a4a;
  text-decoration:none !important; font-size:20px; }
.lg-sheet .x:hover { background:#f1f5f9; }
.lg-sheet .body { padding:8px 16px 24px; }
/* generic helpers used by pages */
.lg-card { background:#fff; border:1px solid #e2e8f0; border-radius:18px; box-shadow:0 1px 2px rgba(15,42,74,.05); }
.lg-grid { display:grid; gap:12px; }
.lg-actioncard { display:flex; flex-direction:column; background:#fff; border:1px solid #e2e8f0; border-radius:16px;
  overflow:hidden; text-decoration:none !important; color:inherit; min-height:96px; }
.lg-actioncard:hover { transform:translateY(-2px); box-shadow:0 10px 28px -10px rgba(15,42,74,.22); }
.lg-actioncard .bar { height:4px; flex:0 0 auto; }
.lg-actioncard .inner { padding:13px 14px; display:flex; flex-direction:column; flex:1; gap:6px; }
.lg-actioncard .ttl { display:flex; align-items:center; gap:8px; font-weight:800; font-size:14.5px; color:#0f2a4a; }
.lg-actioncard .desc { font-size:12.5px; color:#64748b; line-height:1.4; }
.lg-actioncard .cta { font-size:13px; font-weight:700; color:#1e5aa8; }
.lg-rowlink { display:flex; align-items:center; gap:12px; background:#fff; border:1px solid #e2e8f0;
  border-radius:14px; padding:11px 14px; text-decoration:none !important; color:inherit; }
.lg-rowlink:hover { border-color:#1e5aa8; }
.lg-hero { position:relative; overflow:hidden; border-radius:22px; padding:22px 24px; color:#fff;
  background:linear-gradient(120deg,#0a1f3a 0%,#0f2a4a 55%,#1e5aa8 100%); }
.lg-hero .kicker { font-size:12.5px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:#93c5fd; }
.lg-hero h1 { color:#fff !important; margin:6px 0 8px; font-size:clamp(21px,3vw,29px); font-weight:800; line-height:1.2; }
.lg-hero p { color:#dbeafe; font-size:14.5px; max-width:660px; }
.lg-hero .actions { display:flex; gap:10px; margin-top:14px; flex-wrap:wrap; }
.lg-hero .btn-white { background:#fff; color:#0f2a4a !important; border-radius:12px; font-weight:800; font-size:15px;
  padding:12px 20px; min-height:48px; text-decoration:none !important; display:inline-flex; align-items:center; gap:8px; }
.lg-hero .btn-ghost { border:2px solid rgba(255,255,255,.4); color:#fff !important; border-radius:12px; font-weight:700;
  font-size:15px; padding:10px 18px; min-height:48px; text-decoration:none !important; display:inline-flex; align-items:center; gap:8px; }
.lg-banner { border:2px solid; border-radius:16px; padding:14px 16px; display:flex; align-items:center; gap:14px;
  flex-wrap:wrap; margin-bottom:12px; }
.lg-banner.red { border-color:#fecaca; background:linear-gradient(90deg,#fef2f2,#fff7ed); }
.lg-banner.amber { border-color:#fcd34d; background:linear-gradient(90deg,#fffbeb,#ffedd5); }
.lg-banner.green { border-color:#a7f3d0; background:linear-gradient(90deg,#ecfdf5,#ccfbf1); }
.lg-banner .ic { width:44px; height:44px; border-radius:14px; color:#fff; display:grid; place-items:center;
  font-size:21px; flex:0 0 auto; }
.lg-banner .txt { flex:1; min-width:200px; }
.lg-banner .txt small { display:block; font-size:11.5px; font-weight:800; letter-spacing:.1em; text-transform:uppercase;
  color:#64748b; }
.lg-banner .txt b { display:block; font-size:16px; color:#0f2a4a; line-height:1.35; }
.lg-banner .txt span { display:block; font-size:13.5px; color:#475569; margin-top:2px; }
.lg-btn { display:inline-flex; align-items:center; justify-content:center; gap:8px; border-radius:12px;
  background:#0f2a4a; color:#fff !important; font-weight:800; font-size:14.5px; min-height:48px; padding:10px 18px;
  text-decoration:none !important; border:0; cursor:pointer; }
.lg-btn:hover { background:#14365e; }
.lg-empty { border:2px dashed #cbd5e1; border-radius:16px; padding:34px 18px; text-align:center; color:#64748b; background:#fff; }
.tbl th { font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:#5b6b82; font-weight:700;
  background:#f8fafc; text-align:left; padding:11px 14px; border-bottom:1px solid #e4e9f1; }
.tbl td { padding:12px 14px; border-bottom:1px solid #eef2f7; vertical-align:middle; font-size:14px; }
@media (max-width:480px){ .lg-hide-mobile{ display:none !important; } }
"""


# ---------------------------------------------------------------------------
# Chrome pieces
# ---------------------------------------------------------------------------
def _header_html(user: Mapping[str, Any], urgent_count: int, env_tag: str) -> str:
    display = str(user.get("display_name") or user.get("username") or "Người dùng")
    role = str(user.get("role") or "").upper()
    initial = display[:1].upper()
    role_label = {"ADMIN": "Quản trị", "SUPPORT": "Điều hành", "SALE": "Kinh doanh"}.get(role, role)
    proto = f"<span class='lg-proto'>{esc(env_tag)}</span>" if env_tag else ""
    urgent_html = f"<span class='lg-badge-dot'>{urgent_count}</span>" if urgent_count else ""
    return f"""
<div class='lg-header'>
  <a class='lg-iconbtn lg-hamburger' href='{link_url('home', ov='menu')}' style='font-size:22px;'>&#9776;</a>
  <a class='lg-brand' href='{link_url('home')}'>
    <span class='lg-brand-badge'>L</span>
    <span class='lg-brand-name'><b>LOGISTICS PRO</b><span>Trường Thành · Phú Anh · Nội bộ</span></span>
    {proto}
  </a>
  <a class='lg-search-pill' href='{link_url('home', ov='search')}'>🔍&nbsp; Tìm mã lô · khách hàng · hợp đồng…</a>
  <div class='lg-header-right'>
    <a class='lg-iconbtn' href='{link_url('home', ov='search')}' title='Tìm kiếm'>&#128269;</a>
    <a class='lg-iconbtn' href='{link_url('home', ov='notif')}' title='Thông báo'>&#128276;{urgent_html}</a>
    <a class='lg-userchip' href='{link_url('account')}'>
      <span class='lg-avatar'>{esc(initial)}</span>
      <span class='lg-user-meta'><b>{esc(display)}</b><small>{esc(role_label)} · {role}</small></span>
    </a>
    <a class='lg-btn-quick' href='{link_url('home', ov='quick')}'>＋ <span>Thêm</span></a>
  </div>
</div>"""


def _sidebar_html(active: str) -> str:
    rows: list[str] = []
    for group_name, keys in NAV_GROUPS:
        visible = []
        for key in keys:
            meta = PAGES.get(key)
            if meta is None or not has_permission(meta[2]):
                continue
            visible.append((key, meta))
        if not visible:
            continue
        rows.append(f"<p class='lg-group-label'>{esc(group_name)}</p>")
        for key, (label, icon, _perm, _mod, _fn) in visible:
            active_cls = " active" if key == active else ""
            rows.append(
                f"<a class='lg-nav-item{active_cls}' href='{link_url(key)}'>"
                f"<span class='lg-ic'>{icon}</span><span>{esc(label)}</span></a>"
            )
    support = (
        "<div class='lg-help'><p><b>Cần hỗ trợ thao tác?</b></p>"
        "<span>Sổ tay hướng dẫn từng bước cho Sale & Support mới.</span>"
        f"<a href='{link_url('handbook')}'>Mở sổ tay →</a></div>"
    )
    return f"<aside class='lg-side'><nav>{''.join(rows)}{support}</nav></aside>"


def _bottom_nav_html(active: str) -> str:
    items: list[str] = []
    for key, label, icon in MOBILE_BOTTOM:
        meta = PAGES.get(key)
        if meta is None or not has_permission(meta[2]):
            continue
        cls = " active" if key == active else ""
        items.append(
            f"<a class='{cls}' href='{link_url(key)}'>"
            f"<span class='ic'>{icon}</span>{label}<span class='dot'></span></a>"
        )
    plus = (
        f"<a href='{link_url('home', ov='quick')}' style='display:flex;flex-direction:column;align-items:center;"
        f"text-decoration:none;color:#64748b;font-size:11px;font-weight:700;padding-top:2px;'>"
        f"<span class='plus'>＋</span><span style='margin-top:2px;'>Thêm</span></a>"
    )
    return f"<nav class='lg-bnav'>{''.join(items)}{plus}</nav>"


def _drawer_html() -> str:
    rows: list[str] = []
    for group_name, keys in NAV_GROUPS:
        visible = [(key, PAGES[key]) for key in keys if key in PAGES and has_permission(PAGES[key][2])]
        if not visible:
            continue
        rows.append(f"<p class='lg-group-label'>{esc(group_name)}</p>")
        for key, (label, icon, _perm, _mod, _fn) in visible:
            rows.append(
                f"<a class='lg-nav-item' href='{link_url(key)}'>"
                f"<span class='lg-ic'>{icon}</span><span>{esc(label)}</span></a>"
            )
    return f"""
<div class='lg-sheet left'><div class='panel'>
  <div class='head'><b>Menu điều hành</b><a class='x' href='{link_url('home')}'>&#10005;</a></div>
  <div class='body'>{''.join(rows)}
    <div class='lg-help'><p><b>Cần hỗ trợ thao tác?</b></p><span>Sổ tay hướng dẫn từng bước.</span>
    <a href='{link_url('handbook')}'>Mở sổ tay →</a></div>
  </div>
</div></div>"""


def _quick_html() -> str:
    actions = [
        ("Tạo lô hàng mới", "Từ báo giá đã chốt hoặc nhập tay", "📦", "new", "bg:#eff6ff"),
        ("Tạo hợp đồng mới", "HDMB / HDNT + phụ lục", "📜", "contracts", "bg:#ecfdf5"),
        ("Tạo báo giá", "Dự toán chi phí & giá bán", "🤝", "quotes", "bg:#f5f3ff"),
        ("Ghi nhận thanh toán", "Thu tiền khách / trả đối tác", "💰", "finance", "bg:#fffbeb"),
        ("Tra cứu thuế / HS", "Mã HS, thuế NK, VAT", "🔎", "tariff", "bg:#f1f5f9"),
    ]
    body = "".join(
        f"<a href='{link_url(page)}' style='display:flex;align-items:center;gap:12px;background:#fff;"
        f"border:2px solid #f1f5f9;border-radius:16px;padding:12px 14px;margin-bottom:8px;text-decoration:none;"
        f"color:inherit;'><span style='width:44px;height:44px;border-radius:12px;display:grid;place-items:center;"
        f"{style};font-size:20px;'>{icon}</span>"
        f"<span style='flex:1;'><b style='color:#0f2a4a;font-size:15px;display:block;'>{esc(label)}</b>"
        f"<small style='color:#64748b;font-size:13px;'>{esc(desc)}</small></span><span style='color:#cbd5e1;'>→</span></a>"
        for label, desc, icon, page, style in actions
    )
    return f"""
<div class='lg-sheet bottom'><div class='panel'>
  <div class='head'><b>Thêm mới nhanh</b><a class='x' href='{link_url('home')}'>&#10005;</a></div>
  <div class='body'>{body}</div>
</div></div>"""


def _notif_html(items: list[dict[str, Any]]) -> str:
    if not items:
        body = "<div class='lg-empty'>Không có cảnh báo nào đang chờ bạn. 🎉</div>"
    else:
        parts = []
        for item in items[:12]:
            tone_dot = {"red": "#ef4444", "amber": "#f59e0b", "blue": "#3b82f6", "green": "#10b981"}.get(
                item.get("tone", "blue"), "#3b82f6"
            )
            parts.append(
                f"<a href='{item.get('href', link_url('home'))}' style='display:flex;gap:10px;background:#fff;"
                f"border:1px solid #e2e8f0;border-radius:14px;padding:12px;margin-bottom:8px;text-decoration:none;color:inherit;'>"
                f"<span style='width:10px;height:10px;border-radius:99px;margin-top:5px;flex:0 0 auto;background:{tone_dot};'></span>"
                f"<span><b style='color:#0f2a4a;font-size:14px;'>{esc(item.get('title'))}</b>"
                f"<span style='display:block;color:#64748b;font-size:13px;'>{esc(item.get('desc'))}</span>"
                f"<small style='color:#94a3b8;font-size:12px;'>{esc(item.get('time'))}</small></span></a>"
            )
        body = "".join(parts)
    return f"""
<div class='lg-sheet right'><div class='panel'>
  <div class='head'><b>Thông báo · {len(items)}</b><a class='x' href='{link_url('home')}'>&#10005;</a></div>
  <div class='body'>{body}
    <a href='{link_url('tasks')}' class='lg-btn block' style='margin-top:6px;'>Mở Việc Cần Xử Lý →</a>
  </div>
</div></div>"""


# ---------------------------------------------------------------------------
# Page dispatch
# ---------------------------------------------------------------------------
def _visible_page_keys() -> list[str]:
    return [key for key, meta in PAGES.items() if has_permission(meta[2])]


def _resolve_page() -> tuple[str, Mapping[str, Any]]:
    """Decide which page to render from query params + session (legacy compat)."""
    params: dict[str, Any] = {}
    qp = st.query_params
    requested = ""
    if "lg" in qp:
        requested = str(qp.get("lg") or "")
    overlay = str(qp.get("ov") or "") if "ov" in qp else ""

    legacy = st.session_state.get("active_page")
    if legacy and not requested:
        requested = LEGACY_LABEL_PAGE.get(str(legacy).strip(), "")

    if not requested:
        requested = "home"

    if "sid" in qp:
        params["sid"] = str(qp.get("sid") or "")
    if "tab" in qp:
        params["tab"] = str(qp.get("tab") or "")

    # Legacy deep link: module set dashboard_active_shipment_id then went "home".
    active_sid = st.session_state.get("dashboard_active_shipment_id") or st.session_state.get("active_shipment_id")
    if requested == "home" and active_sid and not params.get("sid") and not overlay:
        requested = "shipment"
        params["sid"] = str(active_sid)
    return requested, {"overlay": overlay, **params}


def _counts_for_nav(ships: Mapping[str, Any]) -> int:
    """Number of urgent (critical/action) active shipments — real readiness."""
    if not ships:
        return 0
    urgent = 0
    try:
        from core.readiness import get_all_readiness, derive_next_action  # noqa: PLC0415
        from core.shipment_dashboard import build_shipment_summary  # noqa: PLC0415

        for ship in ships.values():
            if not isinstance(ship, Mapping):
                continue
            status = str(ship.get("status") or "").strip().casefold()
            if status in ("done", "cancel"):
                continue
            try:
                action = derive_next_action(ship, get_all_readiness(ship, build_shipment_summary(ship)))
                if action.severity in ("critical", "action"):
                    urgent += 1
            except Exception:  # noqa: BLE001
                continue
    except Exception:  # noqa: BLE001
        return 0
    return min(urgent, 99)


def _notifications(ships: Mapping[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        from datetime import datetime  # noqa: PLC0415
        from core.readiness import CRITICAL, get_all_readiness, derive_next_action  # noqa: PLC0415
        from core.shipment_dashboard import build_shipment_summary  # noqa: PLC0415

        now = datetime.now().strftime("%d/%m %H:%M")
        for ship in ships.values():
            if not isinstance(ship, Mapping):
                continue
            status = str(ship.get("status") or "").strip().casefold()
            if status in ("done", "cancel"):
                continue
            try:
                sid = str(ship.get("shipment_id") or ship.get("id") or "")
                action = derive_next_action(ship, get_all_readiness(ship, build_shipment_summary(ship)))
                if action.severity == CRITICAL:
                    items.append(
                        {
                            "tone": "red",
                            "title": f"{sid}: {action.label}",
                            "desc": action.recommended_action,
                            "time": now,
                            "href": link_url("shipment", sid=sid, tab="lay-hang"),
                        }
                    )
            except Exception:  # noqa: BLE001
                continue
    except Exception:  # noqa: BLE001
        pass
    return items[:12]


def _load_renderer(module_name: str, function_name: str) -> Callable[..., None]:
    module = importlib.import_module(module_name)
    view = getattr(module, function_name, None)
    if view is None or not callable(view):
        raise AttributeError(f"Không tìm thấy {function_name} trong {module_name}.")
    return view


def _assert_permission(page_key: str, user: Mapping[str, Any]) -> bool:
    meta = PAGES.get(page_key)
    if meta is None or has_permission(meta[2]):
        return True
    st.error(
        f"Tài khoản **{user.get('display_name', user.get('username', '?'))}** không có quyền mở "
        f"màn hình **{meta[0]}**. Liên hệ người quản trị nếu cần truy cập."
    )
    if st.button("Về Trang Tổng Quan", key="lg_access_denied_home"):
        st.session_state.active_page = "Tổng Quan Công Việc"
        st.rerun()
    return False


def render_shell() -> None:
    """Render chrome and dispatch to the current page (called from web_app.main)."""
    user = current_user() or {"username": "local-admin", "display_name": "Local Admin", "role": "admin"}

    st.markdown(f"<style>{_css()}</style>", unsafe_allow_html=True)

    page, params = _resolve_page()
    overlay = str(params.pop("overlay", "") or "")

    ships = st.session_state.get("db_shipments", {}) or {}
    if not isinstance(ships, dict):
        ships = {}
    if page == "shipment":
        sid = str(params.get("sid") or "").strip()
        if not sid or (ships and sid not in ships):
            page = "shipments"
    elif page not in PAGES:
        page = "home"
    if page not in _visible_page_keys() and page != "shipment":
        page = "home"

    # Session label mirrors the legacy route table so reruns coming from real
    # modules keep resolving to the same screen (home == workspace anchor).
    if page in ("home", "shipment"):
        st.session_state.active_page = "Tổng Quan Công Việc"
    else:
        st.session_state.active_page = page_label(page) if page in PAGES else "Tổng Quan Công Việc"

    env_tag = ""
    if str(ENV_IDENTITY).upper() in ("PREVIEW", "STAGING"):
        env_tag = "PREVIEW / STAGING"

    urgent = _counts_for_nav(ships)
    # A workspace detail keeps its parent highlighted ("Lô Hàng").
    nav_active = "shipments" if page == "shipment" else page
    st.markdown(_header_html(user, urgent, env_tag), unsafe_allow_html=True)
    st.markdown(_sidebar_html(nav_active), unsafe_allow_html=True)
    st.markdown(_bottom_nav_html(nav_active), unsafe_allow_html=True)

    if not _assert_permission(page, user):
        st.stop()

    if page == "shipment":
        from views.lg_shipment import shipment_page  # noqa: PLC0415

        shipment_page(sid=str(params.get("sid") or ""), tab=str(params.get("tab") or ""))
    else:
        meta = PAGES[page]
        renderer = _load_renderer(meta[3], meta[4])
        _run_with_boundary(page, renderer)

    # overlays
    if overlay == "menu":
        st.markdown(_drawer_html(), unsafe_allow_html=True)
    elif overlay == "quick":
        st.markdown(_quick_html(), unsafe_allow_html=True)
    elif overlay == "notif":
        st.markdown(_notif_html(_notifications(ships)), unsafe_allow_html=True)
    elif overlay == "search":
        from views.lg_search import search_page  # noqa: PLC0415

        search_page()

    st.markdown(
        "<p style='text-align:center;color:#94a3b8;font-size:12px;margin-top:26px;'>"
        "LOGISTICS PRO · Hệ thống quản lý lô hàng nội bộ — dữ liệu kiểm toán thật từ hệ thống.</p>",
        unsafe_allow_html=True,
    )


def _run_with_boundary(page: str, renderer: Callable[[], None]) -> None:
    """Run a page inside an error boundary that never blanks the app."""
    try:
        renderer()
    except Exception as exc:  # noqa: BLE001
        import traceback  # noqa: PLC0415

        LOGGER.exception("Cannot render page %s", page)
        st.error(f"Không thể mở màn hình **{page_label(page)}**.")
        st.caption("Lỗi đã được giữ lại trên trang thay vì làm giao diện trắng.")
        with st.expander("Chi tiết kỹ thuật", expanded=False):
            st.code(traceback.format_exc(), language="text")
