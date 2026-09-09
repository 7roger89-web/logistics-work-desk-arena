"""Donor-structured pages wired to the real core builders / services."""
from __future__ import annotations

import streamlit as st

from core.readiness import get_all_readiness, derive_next_action, CRITICAL, ACTION, WAITING, INFO, OK
from core.shipment_dashboard import STATUS_LABELS  # noqa: F401  (re-export safety)

from . import svc, widgets as w
from .helpers import actor, fmt_date, fmt_date_blank, money, to_text, UNKNOWN
from .shell import render_mobile_drawer, render_header, render_sidebar, render_bottom_nav
from .widgets import fmt_money


# ====================================================================== HOME
def home_page():
    render_header("Tổng Quan", "Bức tranh vận hành toàn công ty")
    rows = svc.dashboard_rows()
    summary = svc.build_summary()
    demo = svc.demo_mode()
    _maybe_demo_banner(demo)

    needs = []
    for r in rows:
        if r.get("has_alert"):
            needs.append(r)
    needs = sorted(needs, key=lambda r: str(r.get("top_alert") or {}).lower())[:6]

    today_total = summary.get("total", 0)
    actives = summary.get("active", 0)
    pending = summary.get("pending", 0)
    done = summary.get("done", 0)
    attention = summary.get("attention", 0)

    if not rows:
        _hero_no_data(demo)
        return

    st.markdown(
        '<div class="lg-hero"><span class="dec" style="width:160px;height:160px;top:-40px;right:-30px"></span>'
        '<p class="kicker">Bảng điều khiển vận hành</p>'
        f'<h1>Chào {actor()["display_name"]}</h1>'
        '<p class="desc">Theo dõi các lô hàng đang xử lý, việc cần làm và trạng thái tài chính '
        'tập trung trên một màn hình duy nhất.</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    c = st.columns(4)
    c[0].markdown(w.kpi("📦", "Tổng lô hàng", str(today_total), "trong dữ liệu vận hành"), unsafe_allow_html=True)
    c[1].markdown(w.kpi("🟡", "Đang xử lý", str(actives), "cần theo dõi"), unsafe_allow_html=True)
    c[2].markdown(w.kpi("🔔", "Cần xử lý", str(attention), "có cảnh báo / việc tiếp theo"), unsafe_allow_html=True)
    c[3].markdown(w.kpi("✅", "Hoàn tất", str(done), "đã giao"), unsafe_allow_html=True)

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.5, 1])
    with left:
        _home_table(rows)
    with right:
        _home_next_cards(needs)


def _home_no_data():
    st.markdown(
        '<div class="lg-card" style="text-align:center;padding:40px 20px">'
        '<div style="font-size:40px">📭</div>'
        '<h3 style="color:#0f2a4a;margin:8px 0 4px">Chưa có lô hàng nào</h3>'
        '<p style="color:#64748b">Tạo lô mới để bắt đầu theo dõi vận hành.</p></div>',
        unsafe_allow_html=True,
    )


def _hero_no_data(demo):
    st.markdown(
        '<div class="lg-hero"><p class="kicker">Bảng điều khiển vận hành</p>'
        f'<h1>Chào {actor()["display_name"]}</h1>'
        '<p class="desc">Hệ thống đang sẵn sàng. Thêm dữ liệu để bắt đầu.</p></div>',
        unsafe_allow_html=True,
    )
    _home_no_data()


def _maybe_demo_banner(demo: bool):
    if demo:
        st.markdown(
            '<div style="background:#ecfdf5;border:1px solid #a7f3d0;border-radius:12px;'
            'padding:10px 14px;font-size:13px;margin-bottom:10px">🧪 <b>Chế độ dữ liệu mẫu (DEV)</b> — '
            'Chưa kết nối MongoDB thật, đang hiển thị dữ liệu demo cục bộ để duyệt giao diện.</div>',
            unsafe_allow_html=True,
        )


def _home_table(rows):
    st.markdown(w.section_title("📦", "Lô hàng gần đây", "Mã lô · khách · tuyến · trạng thái"),
                unsafe_allow_html=True)
    head = ("<tr><th>Lô hàng</th><th>Khách hàng</th><th>Tuyến</th>"
            "<th>Trạng thái</th><th>Tài chính</th><th>Hạn / ETA</th><th></th></tr>")
    body = []
    for r in rows[:8]:
        route = f'{to_text(r.get("pol"),"?")} → {to_text(r.get("pod"),"?")}'
        op_tone = _tone(r.get("operational_status"))
        fi_tone = {"ok": "green", "open": "amber", "review": "blue", "unknown": "gray"}.get(
            r.get("financial_flag") or "unknown", "gray")
        body.append(
            f'<tr><td><b style="color:#0f2a4a">{w._esc(r.get("shipment_id"))}</b>'
            f'<div class="lg-muted" style="font-size:12px">cập nhật {w._esc(r.get("last_update_label"))}</div></td>'
            f'<td>{w._esc(r.get("customer"))}<div class="lg-muted" style="font-size:12px">'
            f'Sale: {w._esc(r.get("owner"))}</div></td>'
            f'<td>{w._esc(route)}</td>'
            f'<td>{w.badge_html(r.get("operational_status_label"), op_tone)}</td>'
            f'<td>{w.badge_html(r.get("financial_label"), fi_tone)}</td>'
            f'<td>{w._esc(r.get("free_time_expiry_label") or r.get("arrival_date_label"))}</td>'
            f'<td>{w._esc(r.get("next_action",{}).get("label",""))}</td></tr>')
    html = (f'<div class="lg-tablewrap"><table class="lg-tbl"><thead>{head}</thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')
    st.markdown(html, unsafe_allow_html=True)
    if st.button("Xem tất cả lô hàng →", key="home_go_ship", type="secondary"):
        _set_page("shipments")


def _home_next_cards(needs):
    st.markdown(w.section_title("🔔", "Việc cần xử lý", "Các lô có cảnh báo / bước tiếp theo"),
                unsafe_allow_html=True)
    if not needs:
        st.markdown('<div class="lg-card" style="color:#64748b;font-size:14px">Không có việc cần xử lý ngay.</div>',
                    unsafe_allow_html=True)
        return
    for r in needs[:5]:
        na = r.get("next_action") or {}
        tone = "red" if na.get("severity") == "critical" else ("amber" if na.get("severity") == "warning" else "blue")
        _row_to_open(r, na, tone)
    if st.button("Mở Việc Cần Xử Lý →", key="home_go_tasks", type="secondary"):
        _set_page("tasks")


def _row_to_open(r, na, tone):
    sid = r.get("shipment_id")
    if st.button(f'{w._esc(r.get("shipment_id"))} — {w._esc(na.get("label", "Mở lô"))}',
                 key=f"open_{sid}", use_container_width=True, type="secondary"):
        st.session_state["lg_shipment"] = sid
        st.session_state["lg_page"] = "shipment_detail"
        st.rerun()


def _tone(status) -> str:
    s = (status or "").lower()
    return {"done": "green", "cancel": "red"}.get(s,
           "green" if s == "done" else "blue")


def _set_page(slug):
    from .helpers import set_page

    set_page(slug)


# ====================================================================== TASKS
def tasks_page():
    render_header("Việc Cần Xử Lý", "Danh sách công việc ưu tiên theo từng lô")
    render_mobile_drawer()
    rows = svc.dashboard_rows()
    items = []
    for r in rows:
        na = r.get("next_action") or {}
        if not na or r.get("is_complete"):
            continue
        items.append((r, na))
    items.sort(key=lambda t: _sev_idx(t[1].get("severity", "")))
    if not items:
        st.markdown(w.card("", "✅ Không có việc cần xử lý. Mọi lô đang ở trạng thái tốt.", emoji=""),
                    unsafe_allow_html=True)
        return
    for r, na in items:
        tone = "red" if na.get("severity") == "critical" else ("amber" if na.get("severity") in ("warning", "action") else "blue")
        detail = na.get("detail") or na.get("recommended_action") or ""
        kicker = f'{r.get("shipment_id")} · {r.get("customer")}'
        title = na.get("label") or "Xử lý lô"
        st.markdown(w.na_banner(tone, kicker, title, detail, icon="▶"), unsafe_allow_html=True)
        if st.button(f"Mở lô {r.get('shipment_id')} →", key=f"t_{r.get('shipment_id')}",
                     use_container_width=True, type="secondary"):
            st.session_state["lg_shipment"] = r.get("shipment_id")
            st.session_state["lg_page"] = "shipment_detail"
            st.rerun()
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)


def _sev_idx(s) -> int:
    return {"critical": 0, "warning": 1, "action": 2, "info": 3, "waiting": 4}.get(s or "", 5)


# ====================================================================== SHIPMENTS
def shipments_page():
    render_header("Lô Hàng", "Tìm theo mã lô · khách · container · hợp đồng · trạng thái · Sale · Support")
    render_mobile_drawer()

    if st.button("＋ Tạo lô mới", key="ship_new", type="primary"):
        _set_page("new_shipment")

    rows = svc.dashboard_rows()
    if not rows:
        _shipments_empty()
        return

    q = st.text_input("Tìm kiếm", key="ship_search", placeholder="Mã lô / khách / container / trạng thái…")
    q = (q or "").strip().lower()
    if q:
        def hit(r):
            blob = " ".join([str(r.get("shipment_id", "")), str(r.get("customer", "")),
                             str((r.get("route") or {}).get("container", "")),
                             str(r.get("operational_status_label", "")),
                             str((r.get("route") or {}).get("booking", ""))]).lower()
            return q in blob
        rows = [r for r in rows if hit(r)]

    rows = sorted(rows, key=lambda r: str(r.get("last_update") or ""), reverse=True)
    st.markdown(f"<div style='color:#64748b;font-size:13px;margin-bottom:8px'>Hiển thị {len(rows)} lô</div>",
                unsafe_allow_html=True)

    # Filter chips via buttons
    filters = {"Tất cả": None}
    for label, cond in filters.items():
        pass

    head = ("<tr><th>Lô hàng</th><th>Khách hàng</th><th>Tuyến</th><th>Container</th>"
            "<th>Trạng thái</th><th>Hạn / ETA</th><th></th></tr>")
    body = []
    for r in rows:
        route = (r.get("route") or {})
        op_tone = _status_tone(r.get("operational_status"))
        fi_tone = {"ok": "green", "open": "amber", "review": "blue", "unknown": "gray"}.get(
            r.get("financial_flag") or "unknown", "gray")
        body.append(
            f'<tr><td><b style="color:#0f2a4a">{w._esc(r.get("shipment_id"))}</b></td>'
            f'<td>{w._esc(r.get("customer"))}</td>'
            f'<td>{w._esc(to_text(route.get("pol"),"?") )} → {w._esc(to_text(route.get("pod"),"?"))}</td>'
            f'<td>{w._esc(to_text(route.get("container")))}</td>'
            f'<td>{w.badge_html(r.get("operational_status_label"), op_tone)}'
            f'<div class="lg-muted" style="font-size:11.5px;margin-top:3px">'
            f'{w.badge_html(r.get("financial_label"), fi_tone, size="sm")}</div></td>'
            f'<td>{w._esc(r.get("free_time_expiry_label") or r.get("arrival_date_label"))}</td>'
            f'<td></td></tr>')
    html = (f'<div class="lg-tablewrap"><table class="lg-tbl"><thead>{head}</thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')
    st.markdown(html, unsafe_allow_html=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    sel = st.selectbox(
        "Chọn lô để mở chi tiết", options=[r.get("shipment_id") for r in rows],
        format_func=lambda s: s, key="ship_select")
    if st.button("Mở chi tiết lô →", key="ship_open", type="primary"):
        if sel:
            st.session_state["lg_shipment"] = sel
            st.session_state["lg_page"] = "shipment_detail"
            st.rerun()


def _shipments_empty():
    st.markdown(
        '<div class="lg-card" style="text-align:center;padding:40px 20px">'
        '<div style="font-size:40px">📦</div>'
        '<h3 style="color:#0f2a4a;margin:8px 0 4px">Không tìm thấy lô nào</h3>'
        '<p style="color:#64748b">Thử từ khóa khác hoặc tạo lô mới.</p></div>',
        unsafe_allow_html=True,
    )
    if st.button("＋ Tạo lô mới", key="ship_empty_new", type="primary"):
        _set_page("new_shipment")


def _status_tone(status) -> str:
    s = (status or "").lower()
    if s in ("done", "hoàn thành"): return "green"
    if s in ("cancel", "đã hủy"): return "red"
    if s in ("pending", "đang xử lý"): return "blue"
    return "amber"


# ====================================================================== NEW SHIPMENT
def new_shipment_page():
    render_header("Tạo Lô Mới", "Nhập thông tin lô hàng để bắt đầu vận hành")
    render_mobile_drawer()
    import core.database as db
    if not (can_create()):
        return
    mode = st.selectbox("Loại hình", ["Import", "Export"], key="ns_mode")
    st.markdown("#### Khách hàng & tuyến")
    c1, c2 = st.columns(2)
    with c1:
        customer = st.text_input("Tên khách hàng", key="ns_customer")
    with c2:
        incoterm = st.text_input("Incoterm", value="CIF", key="ns_incoterm")
    c3, c4 = st.columns(2)
    with c3:
        pol = st.text_input("Nơi đi (POL)", key="ns_pol")
    with c4:
        pod = st.text_input("Nơi đến (POD)", key="ns_pod")
    sid = db.generate_shipment_id() if hasattr(db, "generate_shipment_id") else "SHP-NEW"
    st.caption(f"Mã lô sẽ được sinh tự động: {sid}")
    if st.button("Tạo lô mới", key="ns_submit", type="primary"):
        data0 = {"st": "wait", "mode": mode, "incoterm": incoterm, "pol": pol, "pod": pod}
        doc = {
            "id": sid, "shipment_id": sid,
            "customer": customer or "", "customer_id": "",
            "status": "wait", "data": {"0.0": data0, "1.2": {"pol": pol, "pod": pod},
                                       "2.6": {}, "2.7": {}, "3.4": {"details": [], "status": "waiting"}},
            "version": 0,
        }
        ok, err = svc.save_shipment(doc)
        if ok:
            st.session_state["lg_shipment"] = sid
            st.session_state["lg_page"] = "shipment_detail"
            st.rerun()
        else:
            st.error(f"Lỗi khi tạo lô: {err}")


def can_create():
    from .helpers import can_access
    return can_access("new_shipment")


# ====================================================================== SHIPMENT DETAIL
DETAIL_TABS = [
    ("lay-hang", "Lấy hàng & Xuất khẩu"),
    ("nhap", "Nhập khẩu & Giao hàng"),
    ("tai-chinh", "Tài chính / Công nợ"),
    ("chung-tu", "Chứng từ & PXK"),
    ("lich-su", "Lịch sử"),
]


def shipment_detail_page():
    sid = st.session_state.get("lg_shipment")
    db = svc.shipments_db()
    if not sid or sid not in db:
        st.markdown("### Lô hàng không tồn tại")
        if st.button("← Về danh sách lô hàng"):
            _set_page("shipments")
        return
    ship = db[sid]
    render_header(f"Lô Hàng · {sid}",
                  "Chi tiết vận hành, tài chính & chứng từ")
    render_mobile_drawer()
    _detail_body(sid, ship)


def _detail_body(sid, ship):
    try:
        dash = __import__("core.shipment_dashboard", fromlist=["build_shipment_dashboard_view"]).build_shipment_dashboard_view(ship)
    except Exception:  # noqa: BLE001
        dash = {}
    try:
        work = svc.workspace_view(ship)
    except Exception:  # noqa: BLE001
        work = {}

    # header summary strip
    op_tone = _status_tone(dash.get("operational_status"))
    cols = st.columns([1.6, 1, 1, 1, 1])
    cols[0].markdown(
        f'<div style="font-size:13px;color:#64748b">Khách hàng</div>'
        f'<b style="color:#0f2a4a">{w._esc(dash.get("customer","Chưa có khách hàng"))}</b>',
        unsafe_allow_html=True)
    cols[1].markdown(
        f'<div style="font-size:13px;color:#64748b">Trạng thái</div>{w.badge_html(dash.get("operational_status_label"), op_tone)}',
        unsafe_allow_html=True)
    cols[2].markdown(
        f'<div style="font-size:13px;color:#64748b">EIA / Hạn</div>'
        f'<b>{w._esc(dash.get("free_time_expiry_label") or dash.get("arrival_date_label"))}</b>',
        unsafe_allow_html=True)
    cols[3].markdown(
        f'<div style="font-size:13px;color:#64748b">Sale</div>'
        f'<b>{w._esc(work.get("owner") or dash.get("owner"))}</b>', unsafe_allow_html=True)
    cols[4].markdown(
        f'<div style="font-size:13px;color:#64748b">Cập nhật</div>'
        f'<b>{w._esc(dash.get("last_update_label"))}</b>', unsafe_allow_html=True)

    # next action / readiness strip
    _readiness_strip(ship, dash)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    tab = st.session_state.get("lg_tab", "lay-hang") or "lay-hang"
    labels = {t: l for t, l in DETAIL_TABS}
    seg = st.segmented_control("Tab", options=[t for t, _ in DETAIL_TABS],
                               format_func=lambda t: labels[t], default=tab,
                               key=f"detail_tab_{sid}", label_visibility="collapsed")
    if seg and seg != tab:
        st.session_state["lg_tab"] = seg
        st.rerun()
    active = seg or tab or "lay-hang"

    if active == "lay-hang":
        _tab_lay_hang(sid, ship)
    elif active == "nhap":
        _tab_nhap(sid, ship)
    elif active == "tai-chinh":
        _tab_tai_chinh(sid, ship)
    elif active == "chung-tu":
        _tab_chung_tu(sid, ship)
    elif active == "lich-su":
        _tab_lich_su(sid, ship, work)


def _readiness_strip(ship, dash):
    try:
        from core.shipment_dashboard import build_shipment_summary
        summary = build_shipment_summary(ship)
        results = get_all_readiness(ship, summary)
    except Exception:  # noqa: BLE001
        results = []
    if results:
        icons = {"READY": "🟢", "NOT_READY": "🔴", "BLOCKED": "🚫", "WAITING_EXTERNAL": "🟡",
                 "REVIEW_REQUIRED": "🟠", "FUTURE": "⚪", "OK": "✅"}
        cells = "".join(
            f'<div style="flex:1;min-width:120px;background:#fff;border:1px solid #e2e8f0;'
            f'border-radius:12px;padding:10px 12px">'
            f'<div style="font-weight:800;font-size:13px;color:#0f2a4a">{icons.get(res.status,"⚪")} {w._esc(res.stage)}</div>'
            f'<div style="font-size:12px;color:#64748b">{w._esc(res.reason)}</div></div>'
            for res in results)
        st.markdown(f'<div style="display:flex;gap:8px;overflow-x:auto;margin-top:10px">{cells}</div>',
                    unsafe_allow_html=True)


def _mutate_ship(sid, ship, key, factory):
    """Return section dict under ship['data'][key], creating as needed."""
    d = ship.setdefault("data", {})
    sec = d.get(key)
    if not isinstance(sec, dict):
        sec = {}
        d[key] = sec
    return sec


def _save(sid, ship, note="Đã lưu."):
    ok, err = svc.save_shipment(ship)
    if ok:
        st.success(note)
    else:
        st.error(f"Không lưu được: {err}")


def _section_value(doc, key, field, default=""):
    d = doc.get("data", {})
    sec = d.get(key)
    if isinstance(sec, dict):
        v = sec.get(field)
        if v is not None:
            return v
    return default


def _tab_lay_hang(sid, ship):
    st.markdown("#### 🚚 Lấy hàng & Xuất khẩu")
    st.markdown(
        '<div style="display:flex;gap:6px;flex-wrap:wrap">'
        f'{w.icon_badge("🚚","Chờ lấy hàng","blue")}'
        f'{w.icon_badge("🧾","Xuất khẩu hải quan","amber")}</div>',
        unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    st.markdown("##### Thông tin lấy hàng")
    pickup_contact = st.text_input("Liên hệ lấy hàng", value=ship.get("pickup_contact", ""), key=f"pk_c_{sid}")
    pickup_address = st.text_input("Địa chỉ lấy hàng", value=ship.get("pickup_address", ""), key=f"pk_a_{sid}")

    st.markdown("##### Xuất khẩu — tuyến / hãng")
    sec = _mutate_ship(sid, ship, "1.2", None)
    pol = st.text_input("Nơi đi (POL)", value=sec.get("pol", ""), key=f"x_pol_{sid}")
    pod = st.text_input("Nơi đến (POD)", value=sec.get("pod", ""), key=f"x_pod_{sid}")
    booking = st.text_input("Booking / vận đơn", value=sec.get("booking_no", ""), key=f"x_bk_{sid}")
    carrier = st.text_input("Hãng tàu / vận chuyển", value=sec.get("carrier", ""), key=f"x_cr_{sid}")
    vessel = st.text_input("Tàu", value=sec.get("vessel", ""), key=f"x_vs_{sid}")
    container = st.text_input("Container", value=sec.get("container_no", ""), key=f"x_ct_{sid}")

    if st.button("💾 Lưu thay đổi (lấy hàng & xuất khẩu)", key=f"sv_lh_{sid}", type="primary"):
        ship["pickup_contact"] = pickup_contact
        ship["pickup_address"] = pickup_address
        sec["pol"] = pol; sec["pod"] = pod
        sec["booking_no"] = booking; sec["carrier"] = carrier
        sec["vessel"] = vessel; sec["container_no"] = container
        _save(sid, ship, "Đã lưu lấy hàng & xuất khẩu.")


def _tab_nhap(sid, ship):
    st.markdown("#### 🚚 Nhập khẩu & Giao hàng")
    sec = _mutate_ship(sid, ship, "2.6", None)
    deliv = _mutate_ship(sid, ship, "2.7", None)
    st.markdown("##### Cập nhật ETA / free time")
    eta = st.text_input("Ngày đến (ETA) — dd/mm/yyyy", value=fmt_date_blank(sec.get("arrival_date")), key=f"n_eta_{sid}")
    ft = st.text_input("Free time (ngày)", value=(sec.get("free_time_days") if sec.get("free_time_days") is not None else ""), key=f"n_ft_{sid}")
    st.markdown("##### Giao hàng")
    is_delivered = bool(deliv.get("is_delivered"))
    delivered = st.checkbox("Đã giao hàng cho khách (ký nhận)", value=is_delivered, key=f"n_del_{sid}")
    delivery_date = st.text_input("Ngày giao", value=fmt_date_blank(deliv.get("delivery_date")), key=f"n_dd_{sid}")
    addr = st.text_input("Địa chỉ giao", value=deliv.get("addr", "") or ship.get("delivery_address", ""), key=f"n_addr_{sid}")

    if st.button("✅ Xác nhận giao hàng / Lưu", key=f"sv_n_{sid}", type="primary"):
        try:
            from core.utils import parse_date_optional
            if eta.strip():
                sec["arrival_date"] = parse_date_optional(eta).strftime("%Y-%m-%d") if parse_date_optional(eta) else eta
            if ft.strip():
                try:
                    sec["free_time_days"] = int(float(ft))
                except ValueError:
                    pass
        except Exception:  # noqa: BLE001
            sec["arrival_date"] = eta
        deliv["is_delivered"] = bool(delivered)
        if delivery_date.strip():
            try:
                from core.utils import parse_date_optional
                p = parse_date_optional(delivery_date)
                deliv["delivery_date"] = p.strftime("%Y-%m-%d") if p else delivery_date
            except Exception:  # noqa: BLE001
                deliv["delivery_date"] = delivery_date
        deliv["addr"] = addr
        ship["is_delivered"] = bool(delivered)
        if delivered:
            ship["status"] = "done"
            ship.setdefault("data", {}).setdefault("0.0", {})["st"] = "done"
        _save(sid, ship, "Đã lưu xác nhận nhập khẩu & giao hàng.")


def _tab_tai_chinh(sid, ship):
    st.markdown("#### 💰 Tài chính / Công nợ")
    try:
        from core.shipment_dashboard import build_shipment_summary
        fin = build_shipment_summary(ship)
    except Exception:  # noqa: BLE001
        fin = {}
    c = st.columns(3)
    c[0].markdown(w.kpi("💰", "Phải thu", fmt_money(fin.get("receivable")), ""), unsafe_allow_html=True)
    c[1].markdown(w.kpi("💸", "Phải trả", fmt_money(fin.get("payable")), ""), unsafe_allow_html=True)
    c[2].markdown(w.kpi("📌", "Trạng thái", to_text(fin.get("financial_status"), UNKNOWN)),
                  unsafe_allow_html=True)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div class="lg-card" style="font-size:13.5px;color:#64748b">Lịch sử thu / chi — sửa bằng '
        'điều chỉnh, không xóa. Dữ liệu tài chính chi tiết được quản lý tại màn hình '
        'Thu Tiền-Công Nợ và Đối Soát.</div>',
        unsafe_allow_html=True)


def _tab_chung_tu(sid, ship):
    st.markdown("#### 🗂 Chứng từ & PXK")
    docs = ship.get("data", {}).get("documents") or ship.get("documents") or []
    st.markdown("##### Chứng từ lô hàng")
    if not docs:
        st.markdown(w.missing_box("Chưa có chứng từ cho lô này", "Bổ sung chứng từ để đủ bộ hồ sơ", "Bổ sung"), unsafe_allow_html=True)
    else:
        head = "<tr><th>Chứng từ</th><th>Trạng thái</th><th>Ghi chú</th></tr>"
        body = []
        for doc in docs if isinstance(docs, list) else list(docs.values()):
            ok = doc.get("ok") if "ok" in doc else doc.get("status") == "ok"
            tone = "green" if ok else ("red" if doc.get("status") == "missing" else "gray")
            body.append(f'<tr><td>{w._esc(doc.get("name") or doc.get("type"))}</td>'
                        f'<td>{w.badge_html("CÓ" if ok else "THIẾU", tone)}</td>'
                        f'<td>{w._esc(doc.get("note",""))}</td></tr>')
        st.markdown(f'<div class="lg-tablewrap"><table class="lg-tbl"><thead>{head}</thead>'
                    f'<tbody>{"".join(body)}</tbody></table></div>', unsafe_allow_html=True)
    st.markdown("##### Phiếu xuất kho (PXK)")
    deliv = ship.get("data", {}).get("2.7", {})
    st.markdown(w.missing_box("Xác nhận đã giao hàng trước khi xuất PXK", "Mỗi lô 1 PXK riêng"), unsafe_allow_html=True)
    st.markdown('<div class="lg-card" style="color:#64748b;font-size:13.5px">PXK gắn với lô đã giao. '
                'Chức năng xuất file được vận hành qua màn hình chứng từ của lô.</div>', unsafe_allow_html=True)


def _tab_lich_su(sid, ship, work):
    st.markdown("#### 🕘 Lịch sử & timeline")
    tl = work.get("timeline") or []
    if not tl:
        st.markdown('<div class="lg-card" style="color:#64748b">Chưa có sự kiện lịch sử cho lô này.</div>',
                    unsafe_allow_html=True)
        return
    html = ['<div class="lg-timeline"><div class="ln"></div>']
    for ev in tl:
        tone = "background:#10b981" if ev.get("tone") == "green" else ("background:#f59e0b" if ev.get("tone") == "amber" else "background:#3b82f6")
        html.append(
            f'<div class="it"><span class="dot" style="{tone}"></span>'
            f'<b>{w._esc(ev.get("title"))}</b>'
            f'<div class="tt">{w._esc(ev.get("time"))} · {w._esc(ev.get("desc",""))}</div></div>')
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)
