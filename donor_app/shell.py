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


def _resolve_page_key(route: str) -> str:
    mapping = {
        "/": "home",
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
        "/so-tay": "handbook",
        "/dich-thuat": "translate",
        "/nguoi-dung": "users",
    }
    return mapping.get(route, "home")


def set_route(route: str):
    """Switch the active page by route string."""
    store.set_active_page(_resolve_page_key(route))
    # also stash the raw route so detail pages can read it
    st.session_state["active_route"] = route


def get_route() -> str:
    return st.session_state.get("active_route", "/")


# ============================================================================
# SHELL RENDER
# ============================================================================

def render_shell():
    """Inject the global shell (header, sidebar, mobile nav) and any open sheets."""
    # Inject CSS first
    st.markdown(design.DONOR_CSS, unsafe_allow_html=True)

    role = store.get_role()
    user = store.get_user()
    active_page = store.get_active_page()

    # ----- HEADER -----
    _render_header(role, user)

    # ----- SEARCH (expanded) -----
    if st.session_state.get("donor_search_open"):
        _render_search_dropdown()

    # ----- SIDEBAR (desktop) -----
    _render_sidebar(active_page)

    # ----- MOBILE NAV (bottom) -----
    _render_mobile_nav(active_page)

    # ----- DRAWERS / SHEETS -----
    if st.session_state.get("donor_nav_open"):
        _render_drawer(active_page)
    if st.session_state.get("donor_quick_add"):
        _render_quick_add()
    if st.session_state.get("donor_notif_open"):
        _render_notif_drawer()

    # ----- TOASTS -----
    _render_toasts()


def _render_header(role: str, user: dict):
    notifs = store.get_notifs()
    unread = len([n for n in notifs if n.get("tone") in ("red", "amber")])
    initials = (user.get("name") or user.get("display_name") or "U")[0].upper()
    role_color = {"ADMIN": "#7c3aed", "SUPPORT": "#1e5aa8", "SALE": "#059669"}.get(role, "#1e5aa8")

    st.markdown(f"""
<div class="lg-header">
  <div class="lg-header-inner">
    <button class="lg-icon-btn" id="lg-menu-btn" onclick="window.parent.postMessage({{'type':'donor','action':'open_nav'}}, '*')" aria-label="Mở menu">{icons.menu(22, "#0f2a4a")}</button>
    <a class="lg-logo" href="?p=home">
      <span class="lg-logo-mark">T</span>
      <span class="lg-logo-text">
        <span class="lg-logo-title">TRƯỜNG THÀNH</span>
        <span class="lg-logo-sub">Phú Anh Logistics · Nội bộ</span>
      </span>
      <span class="lg-pill">PROTOTYPE</span>
    </a>
    <div class="lg-search">
      <div class="lg-search-input">
        <span class="lg-search-icon">{icons.search(19, "#94a3b8")}</span>
        <input type="text" placeholder="Tìm mã lô · khách hàng · hợp đồng · container · báo giá…" onfocus="window.parent.postMessage({{'type':'donor','action':'open_search'}}, '*')" />
      </div>
    </div>
    <button class="lg-icon-btn" id="lg-search-mobile" onclick="window.parent.postMessage({{'type':'donor','action':'open_search'}}, '*')" aria-label="Tìm kiếm">{icons.search(21, "#0f2a4a")}</button>
    <div class="lg-role-chip" id="lg-role-chip" onclick="window.parent.postMessage({{'type':'donor','action':'toggle_role'}}, '*')" style="cursor:pointer">
      <span class="lg-role-avatar" style="background:{role_color}">{initials}</span>
      <span>
        <span class="lg-role-name">{user.get("name", "User")}</span>
        <span class="lg-role-meta">{ROLE_LABELS_FULL.get(role, role)}</span>
      </span>
    </div>
    <button class="lg-icon-btn" id="lg-bell" onclick="window.parent.postMessage({{'type':'donor','action':'open_notif'}}, '*')" aria-label="Thông báo">
      {icons.bell(21, "#0f2a4a")}
      <span class="lg-badge">{unread}</span>
    </button>
    <button class="lg-add-btn" onclick="window.parent.postMessage({{'type':'donor','action':'open_quick_add'}}, '*')">{icons.plus(18, "#fff")} Thêm</button>
  </div>
</div>
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
<a class="lg-search-row" onclick="window.parent.postMessage({{'type':'donor','action':'goto','to':'/lo-hang-detail?id={s['id']}'}}, '*')">
  <span class="ico" style="background:#dbeafe;color:#1e40af">{icons.package(17, "#1e5aa8")}</span>
  <span><span class="title">{s['id']} · {s['customerShort']}</span><span class="meta">Lô hàng — {s['status']}</span></span>
</a>"""
    for c in cts:
        rows += f"""
<a class="lg-search-row" onclick="window.parent.postMessage({{'type':'donor','action':'goto','to':'/hop-dong-detail?id={c['id']}'}}, '*')">
  <span class="ico" style="background:#d1fae5;color:#047857">{icons.file_text(17, "#059669")}</span>
  <span><span class="title">{c['id']} · {c['company']}</span><span class="meta">Hợp đồng — {c['status']}</span></span>
</a>"""
    for c in cus:
        rows += f"""
<a class="lg-search-row" onclick="window.parent.postMessage({{'type':'donor','action':'goto','to':'/khach-hang'}}, '*')">
  <span class="ico" style="background:#fef3c7;color:#b45309">{icons.truck(17, "#b45309")}</span>
  <span><span class="title">{c['short']} · MST {c['mst']}</span><span class="meta">Khách hàng</span></span>
</a>"""
    for qq in quo:
        rows += f"""
<a class="lg-search-row" onclick="window.parent.postMessage({{'type':'donor','action':'goto','to':'/kinh-doanh-bao-gia'}}, '*')">
  <span class="ico" style="background:#ede9fe;color:#5b21b6">{icons.calculator(17, "#5b21b6")}</span>
  <span><span class="title">{qq['id']} · {qq['customer']}</span><span class="meta">Báo giá — {qq['status']}</span></span>
</a>"""
    if not rows:
        rows = f'<p style="padding:14px;font-size:14.5px;color:#64748b">Không tìm thấy "{q}". Thử mã lô <b>LO-0306</b>, <b>An Phát</b> hoặc <b>HDMB</b>.</p>'

    st.markdown(f"""
<div class="lg-shell" style="position:relative">
  <div style="flex:1;min-width:0;padding-top:0;position:relative">
    <div class="lg-search-results">
      {rows}
      <p style="text-align:center;padding:8px;color:#94a3b8;font-size:13px;font-weight:500;margin:0">Nhấn ra ngoài để đóng</p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


def _render_sidebar(active_page: str):
    # Build nav HTML
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
            # build data-href so the bridge handler can navigate
            html += f'<a class="{cls}" data-to="{it["route"]}"><span>{icon}</span><span style="flex:1">{it["label"]}</span>{count_badge}</a>'
        html += '</div>'
    # help card
    html += """
<div class="lg-help-card">
  <h4>Cần hỗ trợ thao tác?</h4>
  <p>Sổ tay hướng dẫn từng bước cho Sale & Support mới.</p>
  <a data-to="/so-tay">Mở sổ tay →</a>
</div>
"""
    html += '</nav></aside>'

    # Use st.components.v1.html so we can attach an event listener that posts
    # back to the Streamlit app. We embed a small script that wires up the
    # click handlers.
    from streamlit.components.v1 import html as components_html

    components_html(f"""
<!DOCTYPE html>
<html><head><style>html,body{{margin:0;padding:0;background:transparent;}}</style></head>
<body>
{html}
<script>
  // Forward all sidebar link clicks to the parent Streamlit document.
  document.querySelectorAll('[data-to]').forEach(el => {{
    el.addEventListener('click', (e) => {{
      e.preventDefault();
      const to = el.getAttribute('data-to');
      window.parent.postMessage({{type:'donor', action:'goto', to: to}}, '*');
    }});
  }});
</script>
</body></html>
""", height=720, scrolling=False)


def _render_mobile_nav(active_page: str):
    """Render fixed mobile bottom nav via a component for click routing."""
    items = [
        {"to": "home", "label": "Tổng quan", "icon": "layout", "route": "/"},
        {"to": "shipments", "label": "Lô hàng", "icon": "package", "route": "/lo-hang"},
        {"to": "contracts", "label": "Hợp đồng", "icon": "file_text", "route": "/hop-dong"},
        {"to": "collect", "label": "Tài chính", "icon": "wallet", "route": "/tai-chinh/thu-tien"},
    ]
    # Build a tiny component
    from streamlit.components.v1 import html as components_html
    parts = []
    for it in items:
        active = active_page == it["to"]
        cls = "active" if active else ""
        ico = icons.NAV_ICONS.get(it["icon"], icons.package)(22, "currentColor")
        bar = '<span class="active-bar"></span>' if active else ''
        parts.append(
            f'<a class="{cls}" data-to="{it["route"]}">{ico}<span>{it["label"]}</span>{bar}</a>'
        )
    # Thêm button
    parts.append('<button data-action="open_quick_add"><span class="add-pill">{}</span><span>Thêm</span></button>'.format(icons.plus(22, "#fff")))

    components_html(f"""
<style>
.lg-mobile-nav {{ display:none !important; }}
@media (max-width:1023px) {{
  .lg-mobile-nav {{ display:grid !important; grid-template-columns:repeat(5,1fr); }}
}}
.lg-mobile-nav {{ position:fixed; left:0; right:0; bottom:0; background:#fff; border-top:1px solid #e2e8f0; box-shadow:0 -4px 20px rgba(0,0,0,.08); z-index:40; padding-bottom:env(safe-area-inset-bottom); }}
.lg-mobile-nav a, .lg-mobile-nav button {{ background:transparent; border:none; padding:8px 4px 6px; display:flex; flex-direction:column; align-items:center; gap:2px; text-decoration:none; color:#94a3b8; font-size:11.5px; font-weight:600; cursor:pointer; font-family:inherit; }}
.lg-mobile-nav a.active {{ color:#0f2a4a; }}
.lg-mobile-nav a.active svg {{ stroke-width:2.4; }}
.lg-mobile-nav .active-bar {{ width:32px; height:4px; border-radius:999px; background:#0f2a4a; margin-top:2px; display:block; }}
.lg-mobile-nav .add-pill {{ width:44px; height:32px; margin-top:-12px; border-radius:16px; background:#0f2a4a; color:#fff; display:grid; place-items:center; box-shadow:0 4px 12px rgba(15,42,74,.28); }}
</style>
<nav class="lg-mobile-nav">{"".join(parts)}</nav>
<script>
  document.querySelectorAll('.lg-mobile-nav [data-to]').forEach(el => {{
    el.addEventListener('click', (e) => {{
      e.preventDefault();
      const to = el.getAttribute('data-to');
      window.parent.postMessage({{type:'donor', action:'goto', to: to}}, '*');
    }});
  }});
  document.querySelectorAll('.lg-mobile-nav [data-action]').forEach(el => {{
    el.addEventListener('click', (e) => {{
      e.preventDefault();
      window.parent.postMessage({{type:'donor', action: el.getAttribute('data-action')}}, '*');
    }});
  }});
</script>
""", height=70)


def _render_drawer(active_page: str):
    role = store.get_role()
    from streamlit.components.v1 import html as components_html
    nav_html = ""
    for g in NAV:
        nav_html += '<div class="lg-nav-group">'
        nav_html += f'<p class="lg-nav-heading">{g["group"]}</p>'
        for it in g["items"]:
            active = active_page == it["to"]
            cls = "lg-nav-item" + (" active" if active else "")
            ico = icons.NAV_ICONS.get(it["icon"], icons.package)(20, "currentColor")
            count = f'<span class="lg-nav-count">{it["count"]}</span>' if it.get("count") else ""
            nav_html += f'<a class="{cls}" data-to="{it["route"]}">{ico}<span style="flex:1">{it["label"]}</span>{count}</a>'
        nav_html += '</div>'

    components_html(f"""
<style>
  .lg-drawer-mask {{ position:fixed; inset:0; background:rgba(15,23,42,.5); z-index:50; }}
  .lg-drawer {{ position:fixed; left:0; top:0; bottom:0; width:300px; max-width:85vw; background:#fff; box-shadow:0 10px 40px rgba(0,0,0,.18); z-index:51; overflow-y:auto; font-family:'Be Vietnam Pro', system-ui, sans-serif; }}
  .lg-drawer-header {{ display:flex; align-items:center; justify-content:space-between; padding:14px 16px; border-bottom:1px solid #e4e9f1; background:#fff; position:sticky; top:0; z-index:2; }}
  .lg-drawer-header h4 {{ font-size:15px; font-weight:800; color:#0f2a4a; margin:0; }}
  .lg-drawer-close {{ width:44px; height:44px; display:grid; place-items:center; border:none; background:transparent; border-radius:12px; cursor:pointer; color:#0f2a4a; }}
  .lg-drawer-close:hover {{ background:#f1f5f9; }}
  .lg-drawer-inner {{ padding:12px; }}
  .role-pills {{ display:flex; gap:6px; margin-bottom:10px; }}
  .role-pills button {{ flex:1; height:44px; border-radius:12px; border:2px solid #e4e9f1; background:#fff; font-size:13px; font-weight:700; color:#475569; cursor:pointer; font-family:inherit; }}
  .role-pills button.active {{ border-color:#0f2a4a; background:#0f2a4a; color:#fff; }}
  .role-pills button:hover:not(.active) {{ background:#f8fafc; }}
  .nav-heading {{ padding:0 12px 6px; font-size:11.5px; font-weight:800; letter-spacing:.04em; color:#94a3b8; text-transform:uppercase; margin:0; }}
  .nav-item {{ display:flex; align-items:center; gap:10px; padding:12px 12px; border-radius:12px; font-size:15px; font-weight:500; color:#334155; text-decoration:none; margin-bottom:2px; }}
  .nav-item:hover {{ background:#f1f5f9; color:#0f2a4a; }}
  .nav-item.active {{ background:#0f2a4a; color:#fff; }}
  .nav-count {{ margin-left:auto; background:#dc2626; color:#fff; border-radius:999px; font-size:11px; font-weight:800; min-width:22px; height:22px; padding:0 6px; display:grid; place-items:center; }}
  .nav-group {{ margin-bottom:12px; }}
  .help {{ margin:10px 4px 0; padding:16px; border-radius:16px; background:linear-gradient(135deg,#0f2a4a,#1e5aa8); color:#fff; }}
  .help h4 {{ font-size:14px; font-weight:700; margin:0 0 4px; }}
  .help p {{ font-size:12.5px; color:#bfdbfe; margin:0 0 10px; }}
  .help a {{ display:inline-flex; align-items:center; gap:4px; background:#fff; color:#0f2a4a; padding:8px 12px; border-radius:8px; font-size:13.5px; font-weight:700; text-decoration:none; }}
  .user {{ padding:0 8px 8px; font-size:12px; color:#64748b; margin:0; }}
  .user b {{ color:#0f2a4a; }}
</style>
<div class="lg-drawer-mask" id="drawer-mask"></div>
<aside class="lg-drawer">
  <div class="lg-drawer-header">
    <h4>Menu điều hành</h4>
    <button class="lg-drawer-close" id="drawer-close" aria-label="Đóng">✕</button>
  </div>
  <div class="lg-drawer-inner">
    <div class="role-pills" id="role-pills">
      <button data-role="ADMIN" class="{ 'active' if role=='ADMIN' else '' }">ADMIN</button>
      <button data-role="SUPPORT" class="{ 'active' if role=='SUPPORT' else '' }">SUPPORT</button>
      <button data-role="SALE" class="{ 'active' if role=='SALE' else '' }">SALE</button>
    </div>
    <p class="user">Đang dùng: <b>{store.get_user().get('name', 'User')}</b> · {ROLE_LABELS.get(role, role)}</p>
    {nav_html}
    <div class="help">
      <h4>Cần hỗ trợ thao tác?</h4>
      <p>Sổ tay hướng dẫn từng bước cho Sale & Support mới.</p>
      <a href="#" data-to="/so-tay">Mở sổ tay →</a>
    </div>
  </div>
</aside>
<script>
  document.getElementById('drawer-mask').addEventListener('click', () => {{
    window.parent.postMessage({{type:'donor', action:'close_nav'}}, '*');
  }});
  document.getElementById('drawer-close').addEventListener('click', () => {{
    window.parent.postMessage({{type:'donor', action:'close_nav'}}, '*');
  }});
  document.querySelectorAll('[data-to]').forEach(el => {{
    el.addEventListener('click', (e) => {{
      e.preventDefault();
      const to = el.getAttribute('data-to');
      window.parent.postMessage({{type:'donor', action:'goto', to: to}}, '*');
    }});
  }});
  document.querySelectorAll('[data-role]').forEach(el => {{
    el.addEventListener('click', (e) => {{
      e.preventDefault();
      const r = el.getAttribute('data-role');
      window.parent.postMessage({{type:'donor', action:'set_role', role: r}}, '*');
    }});
  }});
</script>
""", height=600)


def _render_quick_add():
    from streamlit.components.v1 import html as components_html
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
        # Map item.to back to a route
        route_map = {
            "new_shipment": "/tao-lo-moi",
            "new_contract": "/hop-dong/moi",
            "quotes": "/kinh-doanh-bao-gia",
            "collect": "/tai-chinh/thu-tien",
            "hs_lookup": "/tra-cuu-thue",
        }
        route = route_map.get(it["to"], "/")
        parts.append(
            f'<button class="lg-sheet-row" data-to="{route}">'
            f'<span class="ico" style="background:{bg};color:{fg}">{ico}</span>'
            f'<span style="flex:1;text-align:left"><span class="ttl">{it["label"]}</span><span class="dsc">{it["desc"]}</span></span>'
            f'<span style="color:#cbd5e1">{icons.chevron_right(19, "#cbd5e1")}</span>'
            f'</button>'
        )

    components_html(f"""
<style>
  .lg-sheet-mask {{ position:fixed; inset:0; background:rgba(15,23,42,.5); z-index:60; }}
  .lg-sheet {{ position:fixed; left:0; right:0; bottom:0; background:#fff; border-top-left-radius:24px; border-top-right-radius:24px; padding:20px 20px calc(env(safe-area-inset-bottom) + 20px); z-index:61; max-height:90vh; overflow-y:auto; box-shadow:0 -10px 30px rgba(0,0,0,.18); font-family:'Be Vietnam Pro', system-ui, sans-serif; }}
  @media (min-width:640px) {{ .lg-sheet {{ left:50%; transform:translateX(-50%); right:auto; width:520px; max-width:92vw; bottom:auto; top:50%; transform:translate(-50%,-50%); border-radius:24px; padding:20px; }} }}
  .lg-sheet-grab {{ width:48px; height:6px; background:#cbd5e1; border-radius:999px; margin:0 auto 12px; display:block; }}
  .lg-sheet h3 {{ font-size:18px; font-weight:800; color:#0f2a4a; margin:0 0 4px; }}
  .lg-sheet p.hint {{ font-size:13.5px; color:#64748b; margin:0 0 12px; }}
  .lg-sheet-row {{ display:flex; align-items:center; gap:12px; padding:14px; border:2px solid #f1f5f9; border-radius:16px; background:#fff; cursor:pointer; text-align:left; width:100%; margin-bottom:8px; font-family:inherit; }}
  .lg-sheet-row:hover {{ border-color:#1e5aa8; }}
  .lg-sheet-row .ico {{ width:44px; height:44px; border-radius:12px; display:grid; place-items:center; flex-shrink:0; }}
  .lg-sheet-row .ttl {{ font-size:15px; font-weight:700; color:#0f2a4a; display:block; }}
  .lg-sheet-row .dsc {{ font-size:13px; color:#64748b; display:block; }}
  .lg-sheet-close {{ position:absolute; top:12px; right:12px; width:44px; height:44px; display:grid; place-items:center; border:none; background:transparent; border-radius:12px; cursor:pointer; color:#0f2a4a; }}
  .lg-sheet-close:hover {{ background:#f1f5f9; }}
  .lg-sheet-header {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; }}
</style>
<div class="lg-sheet-mask" id="sheet-mask"></div>
<div class="lg-sheet">
  <div class="lg-sheet-grab"></div>
  <div class="lg-sheet-header">
    <h3>Thêm mới nhanh</h3>
    <button class="lg-sheet-close" id="sheet-close" aria-label="Đóng">✕</button>
  </div>
  <p class="hint">Chọn việc muốn làm — mỗi nút dẫn thẳng tới màn hình nhập liệu.</p>
  {''.join(parts)}
</div>
<script>
  document.getElementById('sheet-mask').addEventListener('click', () => {{
    window.parent.postMessage({{type:'donor', action:'close_quick_add'}}, '*');
  }});
  document.getElementById('sheet-close').addEventListener('click', () => {{
    window.parent.postMessage({{type:'donor', action:'close_quick_add'}}, '*');
  }});
  document.querySelectorAll('[data-to]').forEach(el => {{
    el.addEventListener('click', (e) => {{
      e.preventDefault();
      const to = el.getAttribute('data-to');
      window.parent.postMessage({{type:'donor', action:'goto', to: to}}, '*');
    }});
  }});
</script>
""", height=520)


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
      <h5>{n['title']}</h5>
      <p>{n['desc']}</p>
      <time>{n['time']}</time>
    </div>
  </div>
</div>"""

    from streamlit.components.v1 import html as components_html
    components_html(f"""
<style>
  .lg-sheet-mask {{ position:fixed; inset:0; background:rgba(15,23,42,.5); z-index:60; }}
  .lg-notif {{ position:fixed; right:0; top:0; bottom:0; width:380px; max-width:92vw; background:#fff; box-shadow:0 10px 30px rgba(0,0,0,.18); z-index:61; display:flex; flex-direction:column; font-family:'Be Vietnam Pro', system-ui, sans-serif; }}
  .lg-notif-header {{ display:flex; align-items:center; justify-content:space-between; padding:14px 16px; border-bottom:1px solid #e4e9f1; }}
  .lg-notif-header h4 {{ font-size:16px; font-weight:800; color:#0f2a4a; margin:0; }}
  .lg-notif-header button {{ width:44px; height:44px; display:grid; place-items:center; border:none; background:transparent; border-radius:12px; cursor:pointer; color:#0f2a4a; }}
  .lg-notif-header button:hover {{ background:#f1f5f9; }}
  .lg-notif-list {{ flex:1; overflow-y:auto; padding:10px; }}
  .lg-notif-item {{ background:#fff; border:1px solid #e4e9f1; border-radius:16px; padding:12px; margin-bottom:8px; transition:box-shadow .15s, transform .15s; }}
  .lg-notif-item:hover {{ box-shadow:0 4px 14px rgba(15,42,74,.06); transform:translateY(-1px); }}
  .lg-notif-item h5 {{ font-size:14.5px; color:#0f2a4a; font-weight:700; margin:0; }}
  .lg-notif-item p {{ font-size:13.5px; color:#475569; margin:2px 0 0; }}
  .lg-notif-item time {{ font-size:12px; color:#94a3b8; }}
  .lg-notif-foot {{ padding:10px; border-top:1px solid #e4e9f1; }}
  .lg-notif-foot button {{ width:100%; height:52px; border-radius:12px; background:#0f2a4a; color:#fff; font-weight:700; border:none; cursor:pointer; font-family:inherit; font-size:15px; }}
  .dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; margin-top:6px; display:inline-block; }}
</style>
<div class="lg-sheet-mask" id="notif-mask"></div>
<aside class="lg-notif">
  <div class="lg-notif-header">
    <h4>Thông báo · {len([n for n in notifs if n.get('tone') in ('red','amber')])} chưa đọc</h4>
    <button id="notif-close" aria-label="Đóng">✕</button>
  </div>
  <div class="lg-notif-list">
    {items_html}
  </div>
  <div class="lg-notif-foot">
    <button data-to="/viec-can-xu-ly">Mở Việc Cần Xử Lý</button>
  </div>
</aside>
<script>
  document.getElementById('notif-mask').addEventListener('click', () => {{
    window.parent.postMessage({{type:'donor', action:'close_notif'}}, '*');
  }});
  document.getElementById('notif-close').addEventListener('click', () => {{
    window.parent.postMessage({{type:'donor', action:'close_notif'}}, '*');
  }});
  document.querySelectorAll('[data-to]').forEach(el => {{
    el.addEventListener('click', (e) => {{
      e.preventDefault();
      window.parent.postMessage({{type:'donor', action:'goto', to: el.getAttribute('data-to')}}, '*');
    }});
  }});
</script>
""", height=620)


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
  <button class="close" data-toast-id="{t['id']}" aria-label="Đóng">✕</button>
</div>"""

    from streamlit.components.v1 import html as components_html
    components_html(f"""
<style>
  .lg-toast-stack {{ position:fixed; left:12px; right:12px; bottom:90px; z-index:70; display:flex; flex-direction:column; gap:8px; pointer-events:none; }}
  @media (min-width:768px) {{ .lg-toast-stack {{ left:auto; right:24px; bottom:24px; width:380px; }} }}
  .lg-toast {{ background:#0f2a4a; color:#fff; padding:14px 16px; border-radius:16px; display:flex; align-items:flex-start; gap:10px; box-shadow:0 10px 30px rgba(0,0,0,.2); pointer-events:auto; font-family:'Be Vietnam Pro', system-ui, sans-serif; }}
  .lg-toast .ico {{ width:36px; height:36px; border-radius:10px; display:grid; place-items:center; flex-shrink:0; color:#fff; font-weight:800; font-size:15px; }}
  .lg-toast .body {{ flex:1; min-width:0; }}
  .lg-toast .body h5 {{ font-size:14.5px; margin:0; font-weight:700; }}
  .lg-toast .body p {{ font-size:13px; color:#bfdbfe; margin:2px 0 0; }}
  .lg-toast .close {{ background:rgba(255,255,255,.1); border:none; width:32px; height:32px; border-radius:8px; color:#fff; cursor:pointer; }}
</style>
<div class="lg-toast-stack">
  {rows}
</div>
<script>
  document.querySelectorAll('[data-toast-id]').forEach(el => {{
    el.addEventListener('click', (e) => {{
      e.preventDefault();
      window.parent.postMessage({{type:'donor', action:'dismiss_toast', id: el.getAttribute('data-toast-id')}}, '*');
    }});
  }});
</script>
""", height=180)


# ============================================================================
# BRIDGE — listen for postMessage events from the embedded components
# ============================================================================

def install_bridge():
    """Install a tiny script that listens for postMessage from the embedded
    components and converts those events into Streamlit query-param changes
    we then pick up on the next rerun.
    """
    from streamlit.components.v1 import html as components_html
    components_html("""
<script>
(function() {
  function post(to) {
    // Update window.location.search so the parent Streamlit rerun picks up the new query
    const url = new URL(window.parent.location);
    url.searchParams.set('p', to);
    window.parent.history.pushState({}, '', url.toString());
    // Trigger a synthetic popstate so Streamlit re-reads
    window.parent.dispatchEvent(new PopStateEvent('popstate'));
  }
  window.addEventListener('message', (e) => {
    const d = (e.data || {});
    if (d.type !== 'donor') return;
    if (d.action === 'goto') {
      post(d.to);
    } else if (d.action === 'open_nav' || d.action === 'open_search' || d.action === 'open_quick_add' || d.action === 'open_notif' || d.action === 'close_nav' || d.action === 'close_quick_add' || d.action === 'close_notif' || d.action === 'set_role' || d.action === 'dismiss_toast' || d.action === 'toggle_role') {
      // Action flags ride via session state
      const url = new URL(window.parent.location);
      url.searchParams.set('_a', d.action + (d.role ? ':' + d.role : '') + (d.id ? ':' + d.id : '') + ':' + Date.now());
      window.parent.history.pushState({}, '', url.toString());
      window.parent.dispatchEvent(new PopStateEvent('popstate'));
    }
  });
})();
</script>
""", height=0)


# ============================================================================
# ACTION DISPATCHER — process the encoded action from query params
# ============================================================================

def process_actions():
    """Read query string and dispatch to handlers. Called by main() on every rerun."""
    qp = st.query_params
    raw_action = qp.get("_a", "")
    if not raw_action:
        return
    # Consume the action so it doesn't fire twice
    qp.pop("_a", None)
    parts = raw_action.split(":")
    action = parts[0] if parts else ""
    extra = parts[1] if len(parts) > 1 else ""
    if action == "open_nav":
        st.session_state["donor_nav_open"] = True
    elif action == "open_search":
        st.session_state["donor_search_open"] = True
    elif action == "open_quick_add":
        st.session_state["donor_quick_add"] = True
    elif action == "open_notif":
        st.session_state["donor_notif_open"] = True
    elif action == "close_nav":
        st.session_state["donor_nav_open"] = False
    elif action == "close_search":
        st.session_state["donor_search_open"] = False
    elif action == "close_quick_add":
        st.session_state["donor_quick_add"] = False
    elif action == "close_notif":
        st.session_state["donor_notif_open"] = False
    elif action == "set_role":
        if extra in ("ADMIN", "SUPPORT", "SALE"):
            store.set_role(extra)
            store.push_toast(f"Đã chuyển sang vai trò {ROLE_LABELS.get(extra, extra)}", ROLE_LABELS_FULL.get(extra, ""), "blue")
    elif action == "toggle_role":
        cur = store.get_role()
        nxt = {"ADMIN": "SUPPORT", "SUPPORT": "SALE", "SALE": "ADMIN"}[cur]
        store.set_role(nxt)
        store.push_toast(f"Đã chuyển sang vai trò {ROLE_LABELS.get(nxt, nxt)}", ROLE_LABELS_FULL.get(nxt, ""), "blue")
    elif action == "dismiss_toast":
        # extra is the toast id
        store.dismiss_toast(extra)

    # Goto: parse the `p` param and route
    p = qp.get("p", None)
    if p:
        qp.pop("p", None)
        if p.startswith("/lo-hang-detail"):
            # /lo-hang-detail?id=LO-0306
            import re as _re
            m = _re.search(r"id=([^&]+)", p)
            if m:
                store.set_shipment_id(m.group(1))
                set_route("/lo-hang-detail")
                return
        if p.startswith("/hop-dong-detail"):
            import re as _re
            m = _re.search(r"id=([^&]+)", p)
            if m:
                store.set_shipment_id(m.group(1))
                set_route("/hop-dong-detail")
                return
        if p == "/lo-hang":
            set_route("/lo-hang")
        elif p == "/hop-dong":
            set_route("/hop-dong")
        elif p == "/tai-chinh/thu-tien":
            set_route("/tai-chinh/thu-tien")
        else:
            set_route(p)


def init_session_state():
    """Initialise the global shell state flags."""
    st.session_state.setdefault("donor_nav_open", False)
    st.session_state.setdefault("donor_search_open", False)
    st.session_state.setdefault("donor_quick_add", False)
    st.session_state.setdefault("donor_notif_open", False)
    st.session_state.setdefault("donor_search_query", "")
    st.session_state.setdefault("active_route", "/")
    # Page is home by default
    store.set_active_page("home")
