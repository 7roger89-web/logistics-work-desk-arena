"""Donor-exact global shell: header, sidebar, mobile nav, quick-add, search."""
from __future__ import annotations

import streamlit as st

from . import design, icons, store

ROLE_LABELS = {"ADMIN": "Quản trị viên", "SUPPORT": "Điều phối", "SALE": "Kinh doanh"}
ROLE_LABELS_FULL = {
    "ADMIN": "Quản trị viên · Toàn quyền",
    "SUPPORT": "Điều phối · Vận hành & Chứng từ",
    "SALE": "Kinh doanh · Khách hàng & Báo giá",
}

# Donor sidebar navigation groups (exact labels)
NAV = [
    {
        "group": "VẬN HÀNH",
        "items": [
            {"to": "home", "label": "Tổng Quan Công Việc", "icon": "layout", "route": "/", "count": 0},
            {"to": "tasks", "label": "Việc Cần Xử Lý", "icon": "clock", "route": "/viec-can-xu-ly", "count": 6},
            {"to": "shipments", "label": "Lô Hàng", "icon": "package", "route": "/lo-hang", "count": 0},
            {"to": "new_shipment", "label": "Tạo Lô Mới", "icon": "plus_circle", "route": "/tao-lo-moi", "count": 0},
            {"to": "tracking", "label": "Theo Dõi Vận Chuyển", "icon": "truck", "route": "/theo-doi", "count": 0},
        ],
    },
    {
        "group": "KINH DOANH & ĐỐI TÁC",
        "items": [
            {"to": "customers", "label": "Khách Hàng", "icon": "users", "route": "/khach-hang", "count": 0},
            {"to": "partner_context", "label": "Ngữ Cảnh Đối Tác", "icon": "building", "route": "/ngu-canh-doi-tac", "count": 0},
            {"to": "quotes", "label": "Kinh Doanh & Báo Giá", "icon": "calculator", "route": "/kinh-doanh-bao-gia", "count": 0},
            {"to": "agreements", "label": "Thỏa Thuận & Bàn Giao", "icon": "handshake", "route": "/thoa-thuan-ban-giao", "count": 0},
            {"to": "contracts", "label": "Hợp Đồng", "icon": "file_text", "route": "/hop-dong", "count": 0},
        ],
    },
    {
        "group": "TÀI CHÍNH & ĐỐI SOÁT",
        "items": [
            {"to": "collect", "label": "Thu Tiền & Công Nợ", "icon": "wallet", "route": "/tai-chinh/thu-tien", "count": 0},
            {"to": "reconcile", "label": "Đối Soát Tài Chính", "icon": "scale", "route": "/tai-chinh/doi-soat", "count": 0},
            {"to": "partner_debt", "label": "Công Nợ Đối Tác", "icon": "building", "route": "/tai-chinh/cong-no-doi-tac", "count": 0},
            {"to": "ceo", "label": "Báo Cáo CEO", "icon": "bar_chart", "route": "/bao-cao-ceo", "count": 0},
        ],
    },
    {
        "group": "CÔNG CỤ",
        "items": [
            {"to": "hs_lookup", "label": "Tra Cứu Thuế / HS", "icon": "search", "route": "/tra-cuu-thue", "count": 0},
            {"to": "handbook", "label": "Sổ Tay Kinh Nghiệm", "icon": "book", "route": "/so-tay", "count": 0},
            {"to": "translate", "label": "Dịch Thuật", "icon": "lang", "route": "/dich-thuat", "count": 0},
        ],
    },
    {
        "group": "QUẢN TRỊ",
        "items": [
            {"to": "users", "label": "Người Dùng", "icon": "shield", "route": "/nguoi-dung", "count": 0},
        ],
    },
]

QUICK_ADD_ITEMS = [
    {"to": "new_shipment", "label": "Tạo lô hàng mới", "desc": "Từ báo giá đã chốt hoặc nhập tay", "icon": "package", "bg": "bg-blue-50 text-blue-700"},
    {"to": "new_contract", "label": "Tạo hợp đồng mới", "desc": "HDMB / HDNT + phụ lục", "icon": "file_text", "bg": "bg-emerald-50 text-emerald-700"},
    {"to": "quotes", "label": "Tạo báo giá", "desc": "Dự toán chi phí & giá bán", "icon": "calculator", "bg": "bg-violet-50 text-violet-700"},
    {"to": "collect", "label": "Ghi nhận thanh toán", "desc": "Thu tiền khách / trả đối tác", "icon": "wallet", "bg": "bg-amber-50 text-amber-700"},
    {"to": "hs_lookup", "label": "Tra cứu thuế / HS", "desc": "Mã HS, thuế NK, VAT", "icon": "search", "bg": "bg-slate-100 text-slate-700"},
]


PAGE_ROUTES = {
    "/": "home",
    "/home": "home",
    "/trang-chu": "home",
    "/viec-can-xu-ly": "tasks",
    "/lo-hang": "shipments",
    "/lo-hang-detail": "shipment_detail",
    "/tao-lo-moi": "new_shipment",
    "/theo-doi": "tracking",
    "/khach-hang": "customers",
    "/ngu-canh-doi-tac": "partner_context",
    "/kinh-doanh-bao-gia": "quotes",
    "/thoa-thuan-ban-giao": "agreements",
    "/hop-dong": "contracts",
    "/hop-dong/moi": "new_contract",
    "/hop-dong-detail": "contract_detail",
    "/tai-chinh/thu-tien": "collect",
    "/tai-chinh/doi-soat": "reconcile",
    "/tai-chinh/cong-no-doi-tac": "partner_debt",
    "/bao-cao-ceo": "ceo",
    "/tra-cuu-thue": "hs_lookup",
    "/cong-cu/hs": "hs_lookup",
    "/so-tay": "handbook",
    "/cong-cu/so-tay": "handbook",
    "/dich-thuat": "translate",
    "/cong-cu/dich-thuat": "translate",
    "/nguoi-dung": "users",
    "/admin/users": "users",
}


def _resolve_page_key(route: str) -> str:
    base = route.split("?")[0] if "?" in route else route
    return PAGE_ROUTES.get(base, "home")


def set_route(route: str):
    """Switch the active page by route string."""
    page_key = _resolve_page_key(route)
    store.set_active_page(page_key)
    st.session_state["active_route"] = route


def get_route() -> str:
    return st.session_state.get("active_route", "/")


# ============================================================================
# SHELL RENDER
# ============================================================================

def render_header_and_overlays():
    """Inject the global CSS, top header, drawers, search, and toasts."""
    # Inject CSS
    st.markdown(design.DONOR_CSS, unsafe_allow_html=True)

    role = store.get_role()
    user = store.get_user()
    active_page = store.get_active_page()

    # Top sticky Header
    _render_header(role, user)

    # Search (expanded)
    if st.session_state.get("donor_search_open"):
        _render_search_dropdown()

    # Drawers / Sheets
    if st.session_state.get("donor_nav_open"):
        _render_drawer(active_page)
    if st.session_state.get("donor_quick_add"):
        _render_quick_add()
    if st.session_state.get("donor_notif_open"):
        _render_notif_drawer()

    # Toasts
    _render_toasts()


def _render_header(role: str, user: dict):
    notifs = store.get_notifs()
    unread = len([n for n in notifs if n.get("tone") in ("red", "amber")])
    initials = (user.get("name") or user.get("display_name") or "U")[0].upper()
    role_color = {"ADMIN": "#7c3aed", "SUPPORT": "#1e5aa8", "SALE": "#059669"}.get(role, "#1e5aa8")
    query = st.session_state.get("donor_search_query", "")

    st.markdown(f"""
<header class="lg-header">
  <div class="lg-header-inner">
    <a class="lg-icon-btn" id="lg-menu-btn" href="?action=open_nav" target="_self" aria-label="Mở menu">{icons.menu(22, "#0f2a4a")}</a>
    <a class="lg-logo" href="?p=/" target="_self">
      <span class="lg-logo-mark">T</span>
      <span class="lg-logo-text">
        <span class="lg-logo-title">TRƯỜNG THÀNH</span>
        <span class="lg-logo-sub">Phú Anh Logistics · Nội bộ</span>
      </span>
      <span class="lg-pill">PROTOTYPE</span>
    </a>
    <div class="lg-search">
      <form method="GET" action="" style="margin:0;width:100%">
        <div class="lg-search-input">
          <span class="lg-search-icon">{icons.search(19, "#94a3b8")}</span>
          <input type="text" name="q" value="{query}" placeholder="Tìm mã lô · khách hàng · hợp đồng · container · báo giá…" autocomplete="off" />
        </div>
      </form>
    </div>
    <a class="lg-icon-btn" id="lg-search-mobile" href="?action=open_search" target="_self" aria-label="Tìm kiếm">{icons.search(21, "#0f2a4a")}</a>
    <a class="lg-role-chip" id="lg-role-chip" href="?action=toggle_role" target="_self" style="text-decoration:none">
      <span class="lg-role-avatar" style="background:{role_color}">{initials}</span>
      <span>
        <span class="lg-role-name">{user.get("name", "User")}</span>
        <span class="lg-role-meta">{ROLE_LABELS_FULL.get(role, role)}</span>
      </span>
    </a>
    <a class="lg-icon-btn" id="lg-bell" href="?action=open_notif" target="_self" aria-label="Thông báo">
      {icons.bell(21, "#0f2a4a")}
      <span class="lg-badge">{unread}</span>
    </a>
    <a class="lg-add-btn" href="?action=open_quick_add" target="_self" style="text-decoration:none">{icons.plus(18, "#fff")} Thêm</a>
  </div>
</header>
""", unsafe_allow_html=True)


def _render_search_dropdown():
    q = st.session_state.get("donor_search_query", "").strip().lower()
    ships = store.get_shipments()
    contracts = store.get_contracts()
    customers = list(store.get_customers().values())
    quotes = store.get_quotes()
    lots = [s for s in ships if q in (s["id"] + s["customer"] + s.get("contract", "")).lower()][:4]
    cts = [c for c in contracts if q in (c["id"] + c["company"] + c.get("agent", "")).lower()][:3]
    cus = [c for c in customers if q in (c["name"] + c["mst"] + c.get("contact", "")).lower()][:3]
    quo = [q_ for q_ in quotes if q in (q_["id"] + q_["customer"]).lower()][:2]

    rows = ""
    for s in lots:
        rows += f"""
<a class="lg-search-row" href="?p=/lo-hang-detail&id={s['id']}&action=close_search" target="_self">
  <span class="ico" style="background:#dbeafe;color:#1e40af">{icons.package(17, "#1e5aa8")}</span>
  <span><span class="title">{s['id']} · {s['customerShort']}</span><span class="meta">Lô hàng — {s['status']}</span></span>
</a>"""
    for c in cts:
        rows += f"""
<a class="lg-search-row" href="?p=/hop-dong-detail&id={c['id']}&action=close_search" target="_self">
  <span class="ico" style="background:#d1fae5;color:#047857">{icons.file_text(17, "#059669")}</span>
  <span><span class="title">{c['id']} · {c['company']}</span><span class="meta">Hợp đồng — {c['status']}</span></span>
</a>"""
    for c in cus:
        rows += f"""
<a class="lg-search-row" href="?p=/khach-hang&action=close_search" target="_self">
  <span class="ico" style="background:#fef3c7;color:#b45309">{icons.truck(17, "#b45309")}</span>
  <span><span class="title">{c['short']} · MST {c['mst']}</span><span class="meta">Khách hàng</span></span>
</a>"""
    for qq in quo:
        rows += f"""
<a class="lg-search-row" href="?p=/kinh-doanh-bao-gia&action=close_search" target="_self">
  <span class="ico" style="background:#ede9fe;color:#5b21b6">{icons.calculator(17, "#5b21b6")}</span>
  <span><span class="title">{qq['id']} · {qq['customer']}</span><span class="meta">Báo giá — {qq['status']}</span></span>
</a>"""
    if not rows:
        rows = f'<p style="padding:14px;font-size:14.5px;color:#64748b">Không tìm thấy "{q}". Thử mã lô <b>LO-0306</b>, <b>An Phát</b> hoặc <b>HDMB</b>.</p>'

    st.markdown(f"""
<div style="position:relative;max-width:1600px;margin:0 auto">
  <div class="lg-search-results">
    {rows}
    <a href="?action=close_search" target="_self" style="display:block;text-align:center;padding:8px;color:#94a3b8;font-size:13px;font-weight:500;text-decoration:none">Nhấn để đóng kết quả tìm kiếm</a>
  </div>
</div>
""", unsafe_allow_html=True)


def render_sidebar_content(active_page: str):
    """Render the desktop sidebar directly in the main document DOM."""
    html = '<aside class="lg-sidebar"><nav>'
    for g in NAV:
        html += '<div class="lg-nav-group">'
        html += f'<p class="lg-nav-heading">{g["group"]}</p>'
        for it in g["items"]:
            active = active_page == it["to"]
            cls = "lg-nav-item" + (" active" if active else "")
            icon = icons.NAV_ICONS.get(it["icon"], icons.package)(19, "currentColor")
            count_badge = ""
            if it.get("count"):
                count_badge = f'<span class="lg-nav-count">{it["count"]}</span>'
            html += f'<a class="{cls}" href="?p={it["route"]}" target="_self"><span>{icon}</span><span style="flex:1">{it["label"]}</span>{count_badge}</a>'
        html += '</div>'
    # help card
    html += """
<div class="lg-help-card">
  <h4>Cần hỗ trợ thao tác?</h4>
  <p>Sổ tay hướng dẫn từng bước cho Sale & Support mới.</p>
  <a href="?p=/so-tay" target="_self">Mở sổ tay →</a>
</div>
"""
    html += '</nav></aside>'
    st.markdown(html, unsafe_allow_html=True)


def render_mobile_nav(active_page: str):
    """Render fixed mobile bottom navigation directly in DOM."""
    items = [
        {"to": "home", "label": "Tổng quan", "icon": "layout", "route": "/"},
        {"to": "shipments", "label": "Lô hàng", "icon": "package", "route": "/lo-hang"},
        {"to": "contracts", "label": "Hợp đồng", "icon": "file_text", "route": "/hop-dong"},
        {"to": "collect", "label": "Tài chính", "icon": "wallet", "route": "/tai-chinh/thu-tien"},
    ]
    parts = []
    for it in items:
        active = active_page == it["to"]
        cls = "active" if active else ""
        ico = icons.NAV_ICONS.get(it["icon"], icons.package)(22, "currentColor")
        bar = '<span class="active-bar"></span>' if active else ''
        parts.append(
            f'<a class="{cls}" href="?p={it["route"]}" target="_self">{ico}<span>{it["label"]}</span>{bar}</a>'
        )
    parts.append(
        f'<a href="?action=open_quick_add" target="_self" style="text-decoration:none"><span class="add-pill">{icons.plus(22, "#fff")}</span><span>Thêm</span></a>'
    )
    st.markdown(f'<nav class="lg-mobile-nav">{"".join(parts)}</nav>', unsafe_allow_html=True)


def _render_drawer(active_page: str):
    role = store.get_role()
    nav_html = ""
    for g in NAV:
        nav_html += '<div class="lg-nav-group">'
        nav_html += f'<p class="lg-nav-heading">{g["group"]}</p>'
        for it in g["items"]:
            active = active_page == it["to"]
            cls = "lg-nav-item" + (" active" if active else "")
            ico = icons.NAV_ICONS.get(it["icon"], icons.package)(20, "currentColor")
            count = f'<span class="lg-nav-count">{it["count"]}</span>' if it.get("count") else ""
            nav_html += f'<a class="{cls}" href="?p={it["route"]}&action=close_nav" target="_self">{ico}<span style="flex:1">{it["label"]}</span>{count}</a>'
        nav_html += '</div>'

    html = f"""
<a class="lg-drawer-mask" href="?action=close_nav" target="_self"></a>
<aside class="lg-drawer">
  <div class="lg-drawer-header">
    <h4>Menu điều hành</h4>
    <a class="lg-drawer-close" href="?action=close_nav" target="_self" aria-label="Đóng">✕</a>
  </div>
  <div class="lg-drawer-inner" style="padding:12px">
    <div class="role-pills" style="display:flex;gap:6px;margin-bottom:10px">
      <a href="?action=set_role&role=ADMIN" target="_self" class="lg-btn {'primary' if role=='ADMIN' else 'ghost'} sm" style="flex:1;text-decoration:none">ADMIN</a>
      <a href="?action=set_role&role=SUPPORT" target="_self" class="lg-btn {'primary' if role=='SUPPORT' else 'ghost'} sm" style="flex:1;text-decoration:none">SUPPORT</a>
      <a href="?action=set_role&role=SALE" target="_self" class="lg-btn {'primary' if role=='SALE' else 'ghost'} sm" style="flex:1;text-decoration:none">SALE</a>
    </div>
    <p style="padding:0 8px 8px;font-size:12px;color:#64748b;margin:0">Đang dùng: <b style="color:#0f2a4a">{store.get_user().get('name', 'User')}</b> · {ROLE_LABELS.get(role, role)}</p>
    {nav_html}
    <div class="lg-help-card" style="margin-top:10px">
      <h4>Cần hỗ trợ thao tác?</h4>
      <p>Sổ tay hướng dẫn từng bước cho Sale & Support mới.</p>
      <a href="?p=/so-tay&action=close_nav" target="_self">Mở sổ tay →</a>
    </div>
  </div>
</aside>
"""
    st.markdown(html, unsafe_allow_html=True)


def _render_quick_add():
    parts = []
    for it in QUICK_ADD_ITEMS:
        ico = icons.NAV_ICONS.get(it["icon"], icons.plus)(21, "currentColor")
        bg_map = {
            "bg-blue-50 text-blue-700": ("#eff6ff", "#1e40af"),
            "bg-emerald-50 text-emerald-700": ("#ecfdf5", "#047857"),
            "bg-violet-50 text-violet-700": ("#ede9fe", "#5b21b6"),
            "bg-amber-50 text-amber-700": ("#fff7ed", "#b45309"),
            "bg-slate-100 text-slate-700": ("#f1f5f9", "#334155"),
        }
        bg, fg = bg_map.get(it["bg"], ("#f1f5f9", "#334155"))
        route_map = {
            "new_shipment": "/tao-lo-moi",
            "new_contract": "/hop-dong/moi",
            "quotes": "/kinh-doanh-bao-gia",
            "collect": "/tai-chinh/thu-tien",
            "hs_lookup": "/tra-cuu-thue",
        }
        route = route_map.get(it["to"], "/")
        parts.append(
            f'<a class="lg-sheet-row" href="?p={route}&action=close_quick_add" target="_self">'
            f'<span class="ico" style="background:{bg};color:{fg}">{ico}</span>'
            f'<span style="flex:1;text-align:left"><span class="ttl">{it["label"]}</span><span class="dsc">{it["desc"]}</span></span>'
            f'<span style="color:#cbd5e1">{icons.chevron_right(19, "#cbd5e1")}</span>'
            f'</a>'
        )

    html = f"""
<a class="lg-sheet-mask" href="?action=close_quick_add" target="_self"></a>
<div class="lg-sheet">
  <div class="lg-sheet-grab"></div>
  <div class="lg-sheet-header" style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
    <h3 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Thêm mới nhanh</h3>
    <a class="lg-sheet-close" href="?action=close_quick_add" target="_self" aria-label="Đóng" style="text-decoration:none;display:grid;place-items:center;width:44px;height:44px;border-radius:12px;color:#0f2a4a">✕</a>
  </div>
  <p class="hint">Chọn việc muốn làm — mỗi nút dẫn thẳng tới màn hình nhập liệu.</p>
  {''.join(parts)}
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


def _render_notif_drawer():
    notifs = store.get_notifs()
    items_html = ""
    for n in notifs:
        dot_color = {"red": "#dc2626", "amber": "#f59e0b", "blue": "#2563eb"}.get(n["tone"], "#94a3b8")
        pulse = "animation: lgPulse 1.6s ease-in-out infinite;" if n["tone"] == "red" else ""
        items_html += f"""
<div class="lg-notif-item">
  <div style="display:flex;align-items:flex-start;gap:10px">
    <span class="dot" style="background:{dot_color};{pulse}"></span>
    <div>
      <h5 style="font-size:14.5px;color:#0f2a4a;font-weight:700;margin:0">{n['title']}</h5>
      <p style="font-size:13.5px;color:#475569;margin:2px 0 0">{n['desc']}</p>
      <time style="font-size:12px;color:#94a3b8">{n['time']}</time>
    </div>
  </div>
</div>"""

    unread_count = len([n for n in notifs if n.get('tone') in ('red', 'amber')])
    html = f"""
<a class="lg-sheet-mask" href="?action=close_notif" target="_self"></a>
<aside class="lg-notif">
  <div class="lg-notif-header">
    <h4 style="font-size:16px;font-weight:800;color:#0f2a4a;margin:0">Thông báo · {unread_count} chưa đọc</h4>
    <a class="lg-icon-btn" href="?action=close_notif" target="_self" aria-label="Đóng" style="text-decoration:none">✕</a>
  </div>
  <div class="lg-notif-list">
    {items_html}
  </div>
  <div class="lg-notif-foot">
    <a class="lg-btn primary full" href="?p=/viec-can-xu-ly&action=close_notif" target="_self" style="text-decoration:none">Mở Việc Cần Xử Lý</a>
  </div>
</aside>
"""
    st.markdown(html, unsafe_allow_html=True)


def _render_toasts():
    toasts = store.get_toasts()
    if not toasts:
        return
    bg_map = {
        "green": "#10b981", "red": "#dc2626", "amber": "#f59e0b", "blue": "#2563eb"
    }
    symbol_map = {"green": "✓", "red": "!", "amber": "⚠", "blue": "i"}
    rows = ""
    for t in toasts:
        rows += f"""
<div class="lg-toast">
  <span class="ico" style="background:{bg_map.get(t['tone'], '#2563eb')}">{symbol_map.get(t['tone'], 'i')}</span>
  <div class="body">
    <h5>{t['title']}</h5>
    {f'<p>{t["desc"]}</p>' if t.get('desc') else ''}
  </div>
  <a class="close" href="?action=dismiss_toast&toast_id={t['id']}" target="_self" aria-label="Đóng">✕</a>
</div>"""

    st.markdown(f'<div class="lg-toast-stack">{rows}</div>', unsafe_allow_html=True)


# ============================================================================
# ACTION DISPATCHER — process query params and navigate
# ============================================================================

def process_actions():
    """Read query parameters and apply navigation/actions. Called on every rerun."""
    qp = st.query_params

    # 1. Action parameter
    action = qp.get("action")
    if action:
        if action == "open_nav":
            st.session_state["donor_nav_open"] = True
        elif action == "close_nav":
            st.session_state["donor_nav_open"] = False
        elif action in ("open_search", "search_dropdown"):
            st.session_state["donor_search_open"] = True
        elif action == "close_search":
            st.session_state["donor_search_open"] = False
        elif action == "open_quick_add":
            st.session_state["donor_quick_add"] = True
        elif action == "close_quick_add":
            st.session_state["donor_quick_add"] = False
        elif action in ("open_notif", "notif_drawer"):
            st.session_state["donor_notif_open"] = True
        elif action == "close_notif":
            st.session_state["donor_notif_open"] = False
        elif action == "close_drawer":
            st.session_state["donor_nav_open"] = False
            st.session_state["donor_search_open"] = False
            st.session_state["donor_quick_add"] = False
            st.session_state["donor_notif_open"] = False
        elif action == "toggle_role":
            cur = store.get_role()
            nxt = {"ADMIN": "SUPPORT", "SUPPORT": "SALE", "SALE": "ADMIN"}.get(cur, "SUPPORT")
            store.set_role(nxt)
            store.push_toast(f"Đã chuyển sang vai trò {ROLE_LABELS.get(nxt, nxt)}", ROLE_LABELS_FULL.get(nxt, ""), "blue")
        elif action == "set_role":
            role = qp.get("role", "")
            if role in ("ADMIN", "SUPPORT", "SALE"):
                store.set_role(role)
                store.push_toast(f"Đã chuyển sang vai trò {ROLE_LABELS.get(role, role)}", ROLE_LABELS_FULL.get(role, ""), "blue")
        elif action == "dismiss_toast":
            tid = qp.get("toast_id", "")
            if tid:
                store.dismiss_toast(tid)
        elif action in ("pay_dialog", "open_pay"):
            sid = qp.get("sid", "LO-0306")
            st.session_state["pay_dialog_open"] = True
            st.session_state["pay_lot"] = sid
            st.session_state["pay_sid"] = sid
        elif action == "close_pay":
            st.session_state["pay_dialog_open"] = False

    # 2. Search query parameter
    if "q" in qp:
        st.session_state["donor_search_query"] = qp.get("q", "")
        if st.session_state["donor_search_query"]:
            st.session_state["donor_search_open"] = True

    # 3. Route parameter 'p' or 'page'
    p = qp.get("p") or qp.get("page")
    if p:
        if p.startswith("/lo-hang-detail") or p.startswith("/lo-hang/"):
            sid = qp.get("id")
            if not sid and "/lo-hang/" in p and not p.endswith("/lo-hang"):
                sid = p.split("/lo-hang/")[1].split("?")[0]
            if sid:
                store.set_shipment_id(sid)
            tab = qp.get("tab")
            if tab:
                st.session_state["active_tab"] = tab
            set_route("/lo-hang-detail")
        elif p.startswith("/hop-dong-detail") or p.startswith("/hop-dong/"):
            if p != "/hop-dong/moi":
                cid = qp.get("id")
                if not cid and "/hop-dong/" in p and not p.endswith("/moi"):
                    cid = p.split("/hop-dong/")[1].split("?")[0]
                if cid:
                    store.set_contract_id(cid)
                tab = qp.get("tab")
                if tab:
                    st.session_state["active_contract_tab"] = tab
                set_route("/hop-dong-detail")
            else:
                set_route("/hop-dong/moi")
        else:
            set_route(p)


def init_session_state():
    """Initialise global state flags only if not present."""
    st.session_state.setdefault("donor_nav_open", False)
    st.session_state.setdefault("donor_search_open", False)
    st.session_state.setdefault("donor_quick_add", False)
    st.session_state.setdefault("donor_notif_open", False)
    st.session_state.setdefault("donor_search_query", "")
    st.session_state.setdefault("active_route", "/")
    st.session_state.setdefault("active_page", "home")
    st.session_state.setdefault("active_shipment_id", "LO-0306")
    st.session_state.setdefault("active_contract_id", "HDMB-PA-2026-031")
    st.session_state.setdefault("active_tab", "lay-hang")
    st.session_state.setdefault("active_contract_tab", "hang-hoa")
