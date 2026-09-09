"""Tasks, Shipments, Shipment detail, Customers, Sales pages — all .format() to avoid f-string issues."""
from __future__ import annotations

import streamlit as st

from . import design, icons, store, ui


LEVEL_BADGE = {
    "Khan": ("Khẩn", "red"),
    "CanXuLy": ("Cần xử lý", "amber"),
    "BinhThuong": ("Bình thường", "gray"),
}


def render_tasks():
    tasks = store.get_tasks()
    c1, c2 = st.columns([3, 1])
    with c1:
        q = st.text_input("", placeholder="Lọc theo mã lô, khách hàng, người phụ trách…", key="tasks_q", label_visibility="collapsed")
    with c2:
        filter_level = st.selectbox("", options=["ALL", "Khan", "CanXuLy", "BinhThuong"], key="tasks_filter", label_visibility="collapsed", format_func=lambda x: "Tất cả (10)" if x == "ALL" else ("Khẩn (3)" if x == "Khan" else ("Cần xử lý (4)" if x == "CanXuLy" else "Bình thường (3)")))

    filtered = [t for t in tasks if (filter_level == "ALL" or t.get("level") == filter_level) and (not q or q.lower() in (t.get("lot", "") + t.get("customer", "") + t.get("job", "") + t.get("assignee", "")).lower())]

    header_html = """
<div class="lg-card" style="margin-bottom:16px">
  <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0 0 6px">Việc Cần Xử Lý</h2>
  <p style="font-size:13.5px;color:#64748b;margin:0">Hiện trạng → việc thiếu → bấm XỬ LÝ NGAY để tới đúng ô cần nhập. Làm mục Khẩn trước 17:00.</p>
</div>
"""
    st.markdown(header_html, unsafe_allow_html=True)

    if filtered:
        rows = []
        for t in filtered:
            lvl, color = LEVEL_BADGE.get(t.get("level", ""), ("—", "gray"))
            if color == "red":
                level_badge = '<span style="display:inline-block;background:#dc2626;color:#fff;font-size:12.5px;font-weight:800;border-radius:999px;padding:4px 10px">{}</span>'.format(lvl)
            elif color == "amber":
                level_badge = '<span style="display:inline-block;background:#f59e0b;color:#fff;font-size:12.5px;font-weight:800;border-radius:999px;padding:4px 10px">{}</span>'.format(lvl)
            else:
                level_badge = '<span style="display:inline-block;background:#e2e8f0;color:#475569;font-size:12.5px;font-weight:800;border-radius:999px;padding:4px 10px">{}</span>'.format(lvl)
            action_link = '<a class="lg-btn primary sm" data-to="{0}">XỬ LÝ NGAY →</a>'.format(t.get("route", "/"))
            lot_link = '<a class="lg-link" data-to="{0}">{1}</a>'.format(t.get("route", "/"), t.get("lot", ""))
            due_html = '<span style="color:#dc2626;font-weight:700">{0}</span><br><span style="font-size:12.5px;color:#64748b">{1}</span>'.format(t.get("due", ""), t.get("dueNote", ""))
            status_badge = '<span class="lg-badge {0} sm">{1}</span>'.format(t.get("statusTone", "gray"), t.get("status", ""))
            rows.append([level_badge, lot_link, t.get("customer", ""), "<b>{0}</b>".format(t.get("job", "")), t.get("assignee", ""), due_html, status_badge, action_link])
        headers = ["Ưu tiên", "Mã lô", "Khách hàng", "Việc cần làm", "Người phụ trách", "Hạn", "Trạng thái", "Hành động"]
        _render_table(headers, rows, min_width="980px")
    else:
        st.info("Không có việc nào khớp.")

    tip_html = """
<div class="lg-card" style="margin-top:12px;border-style:dashed;border-color:#cbd5e1">
  <div style="display:flex;align-items:flex-start;gap:10px;font-size:14px;color:#64748b">
    <span style="color:#64748b">{icon}</span>
    <p style="margin:0"><b>Mẹo cho người mới:</b> xử lý theo thứ tự <b>Khẩn → Cần xử lý → Bình thường</b>. Mỗi dòng đều có nút XỬ LÝ NGAY dẫn tới đúng ô nhập liệu.</p>
  </div>
</div>
""".format(icon=icons.filter_icon(19, "#64748b"))
    st.markdown(tip_html, unsafe_allow_html=True)

    ui._install_goto_bridge()


def _render_table(headers, rows, min_width="980px"):
    head = "".join("<th>{0}</th>".format(h) for h in headers)
    body = ""
    for r in rows:
        body += "<tr>" + "".join("<td>{0}</td>".format(c) for c in r) + "</tr>"
    html = """
<div class="lg-tbl-wrap">
  <div style="overflow-x:auto">
    <table class="lg-tbl" style="min-width:{mw}">
      <thead><tr>{h}</tr></thead>
      <tbody>{b}</tbody>
    </table>
  </div>
</div>
""".format(mw=min_width, h=head, b=body)
    st.markdown(html, unsafe_allow_html=True)


def render_shipments():
    ships = store.get_shipments()
    c1, c2 = st.columns([5, 1])
    with c1:
        q = st.text_input("", placeholder="Nhập mã lô (LO-0306), khách (An Phát), hợp đồng…", key="ships_q", label_visibility="collapsed")
    with c2:
        show_filter = st.button("⚙ Lọc", key="ships_filter_btn", use_container_width=True)

    if show_filter:
        st.session_state["ships_filter_open"] = not st.session_state.get("ships_filter_open", False)

    status = "ALL"
    if st.session_state.get("ships_filter_open"):
        statuses = ["ALL"] + sorted({s["status"] for s in ships})
        sel = st.radio("", options=statuses, horizontal=True, key="ships_status", label_visibility="collapsed")
        status = sel

    filtered = [s for s in ships if (status == "ALL" or s.get("status") == status) and (not q or q.lower() in (s["id"] + s.get("customer", "") + s.get("contract", "") + s.get("route", "")).lower())]

    found_suffix = (' cho "' + q + '"') if q else ""
    header_html = """
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{icon}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Lô Hàng</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Tìm theo mã lô · khách · container · hợp đồng · trạng thái · Sale · Support · tuyến · cửa khẩu</p>
      </div>
    </div>
    <a class="lg-btn primary" data-to="/tao-lo-moi" style="min-width:auto">＋ Tạo lô mới</a>
  </div>
  <p style="font-size:13.5px;color:#64748b;margin:8px 0 0">Tìm thấy <b style="color:#0f2a4a">{n} lô</b>{suffix} · Mỗi lô hiển thị: hiện trạng → việc tiếp theo → nút xử lý.</p>
</div>
""".format(icon=icons.package(20, "#fff"), n=len(filtered), suffix=found_suffix)
    st.markdown(header_html, unsafe_allow_html=True)

    if filtered:
        rows = []
        for s in filtered:
            id_link = '<a class="lg-link" data-to="/lo-hang-detail?id={0}" style="font-size:15px;font-weight:800">{1}</a><br><span style="font-size:12px;color:#94a3b8">Cập nhật {2}</span>'.format(s["id"], s["id"], s.get("updated", ""))
            contract_route = '<span style="font-size:13px;font-weight:600;color:#475569">{0}</span><br><span style="font-size:13px;color:#64748b">{1}</span>'.format(s.get("contract", ""), s.get("route", ""))
            status_badge = '<span class="lg-badge {0} sm">{1}</span>'.format(s.get("statusTone", "gray"), s.get("status", ""))
            next_action = '<b style="font-size:13.5px">{0}</b>'.format(s.get("nextAction", "—"))
            sale_sp = '<span style="font-size:13px">Sale: <b>{0}</b></span><br><span style="font-size:13px">SP: <b>{1}</b></span>'.format(s.get("sale", ""), s.get("support", ""))
            next_route = s.get("nextRoute", "/lo-hang-detail?id=" + s["id"])
            action_html = '<div style="display:flex;gap:6px"><a class="lg-btn primary sm" data-to="{0}">XỬ LÝ</a><a class="lg-btn ghost sm" data-to="/lo-hang-detail?id={1}">{2} 360°</a></div>'.format(next_route, s["id"], icons.eye(15, "#0f2a4a"))
            rows.append([id_link, '<b>{0}</b>'.format(s.get("customerShort", "")), contract_route, status_badge, next_action, sale_sp, action_html])
        _render_table(["Mã lô", "Khách hàng", "Hợp đồng · Tuyến", "Trạng thái", "Việc tiếp theo", "Sale · Support", "Hành động"], rows, min_width="1080px")
    else:
        empty_html = """
<div class="lg-card" style="text-align:center;padding:48px">
  <p style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Không tìm thấy lô nào</p>
  <p style="font-size:14px;color:#64748b;margin:6px 0 16px">Thử từ khóa khác hoặc tạo lô mới.</p>
  <a class="lg-btn primary" data-to="/tao-lo-moi">＋ Tạo lô mới</a>
</div>
"""
        st.markdown(empty_html, unsafe_allow_html=True)

    ui._install_goto_bridge()


SHIPMENT_TABS = [
    {"id": "lay-hang", "label": "Lấy hàng & Xuất khẩu", "short": "Lấy hàng"},
    {"id": "nhap", "label": "Nhập khẩu & Giao hàng", "short": "Nhập & Giao"},
    {"id": "tai-chinh", "label": "Tài chính / Công nợ", "short": "Tài chính"},
    {"id": "chung-tu", "label": "Chứng từ & PXK", "short": "Chứng từ"},
    {"id": "lich-su", "label": "Lịch sử", "short": "Lịch sử"},
]


def render_shipment_detail():
    sid = store.get_shipment_id() or st.query_params.get("id") or "LO-0306"
    s = store.find_shipment(sid)
    if not s:
        st.markdown('<div class="lg-card" style="text-align:center;padding:48px"><p style="font-size:19px;font-weight:800">Không tìm thấy lô {0}</p></div>'.format(sid), unsafe_allow_html=True)
        return

    st.markdown('<a class="lg-link" data-to="/lo-hang" style="display:inline-flex;align-items:center;gap:6px;margin-bottom:8px;font-size:14.5px">← Quay lại</a>', unsafe_allow_html=True)

    tab = st.query_params.get("tab", "lay-hang")
    if tab not in [t["id"] for t in SHIPMENT_TABS]:
        tab = "lay-hang"

    missing_count = len(s.get("missingDocs", [])) + len([d for d in s.get("docs", []) if not d.get("ok")])
    missing_badge = '<span class="lg-badge red"><span class="lg-dot red"></span>Thiếu {0} thông tin</span>'.format(missing_count) if missing_count else ""
    header_html = """
<div class="lg-card" style="padding:0;overflow:hidden">
  <div style="height:6px;background:linear-gradient(90deg,#0f2a4a,#1e5aa8,#10b981)"></div>
  <div style="padding:20px 24px">
    <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px">
      <h1 style="font-size:24px;font-weight:800;color:#0f2a4a;margin:0">{sid}</h1>
      <span class="lg-badge {st_tone}">{status}</span>
      {missing}
      <span style="margin-left:auto;font-size:12.5px;color:#94a3b8;display:flex;align-items:center;gap:4px">{clock} Cập nhật {updated}</span>
    </div>
    <p style="font-size:15.5px;font-weight:600;margin:6px 0 0">{cust} <span style="color:#94a3b8;font-weight:400">· MST {mst}</span></p>
    <div class="lg-cols-4" style="margin-top:12px">
      <div><p style="font-size:13.5px;color:#64748b;font-weight:500;margin:0">Tuyến</p><p style="font-size:14.5px;font-weight:600;color:#1e293b;margin:2px 0 0">{route}</p></div>
      <div><p style="font-size:13.5px;color:#64748b;font-weight:500;margin:0">Cửa khẩu</p><p style="font-size:14.5px;font-weight:600;color:#1e293b;margin:2px 0 0">{border}</p></div>
      <div><p style="font-size:13.5px;color:#64748b;font-weight:500;margin:0">Hợp đồng</p><p style="font-size:14.5px;font-weight:600;margin:2px 0 0"><a class="lg-link" data-to="/hop-dong-detail?id={contract}">{contract}</a></p></div>
      <div><p style="font-size:13.5px;color:#64748b;font-weight:500;margin:0">Sale · Support</p><p style="font-size:14.5px;font-weight:600;color:#1e293b;margin:2px 0 0">{sale} · {support}</p></div>
    </div>
  </div>
  <div style="padding:0 20px 20px">
    {next_action}
  </div>
  <div class="lg-tabs" id="workspace-tabs">
    {tabs}
  </div>
</div>
""".format(
        sid=s["id"],
        st_tone=s.get("statusTone", "gray"),
        status=s.get("status", ""),
        missing=missing_badge,
        clock=icons.clock(14, "#94a3b8"),
        updated=s.get("updated", ""),
        cust=s.get("customer", ""),
        mst=s.get("customerMST", ""),
        route=s.get("route", "—"),
        border=s.get("borderVN", "—"),
        contract=s.get("contract", ""),
        sale=s.get("sale", ""),
        support=s.get("support", ""),
        next_action=ui._next_action_banner_html(s),
        tabs=_shipment_tabs_html(tab),
    )
    st.markdown(header_html, unsafe_allow_html=True)

    if s.get("missingDocs") and tab != "chung-tu":
        missing_boxes = "".join(_missing_box_html(s, m) for m in s["missingDocs"])
        missing_html = """
<div class="lg-card" style="border:2px solid #fecaca;background:#fff7ed;margin-top:12px">
  <p style="font-size:15px;font-weight:800;color:#991b1b;display:flex;align-items:center;gap:6px;margin:0 0 8px">{icon} Đang thiếu {n} thông tin — bấm để bổ sung ngay:</p>
  <div class="lg-cols-2">
    {boxes}
  </div>
</div>
""".format(icon=icons.circle_alert(18, "#991b1b"), n=len(s["missingDocs"]), boxes=missing_boxes)
        st.markdown(missing_html, unsafe_allow_html=True)

    if tab == "lay-hang":
        _render_shipment_tab_layhang(s)
    elif tab == "nhap":
        _render_shipment_tab_nhap(s)
    elif tab == "tai-chinh":
        _render_shipment_tab_finance(s)
    elif tab == "chung-tu":
        _render_shipment_tab_chungtu(s)
    elif tab == "lich-su":
        _render_shipment_tab_history(s)

    ui._install_goto_bridge()


def _shipment_tabs_html(active):
    parts = []
    for t in SHIPMENT_TABS:
        cls = "lg-tab active" if t["id"] == active else "lg-tab"
        parts.append('<button class="{0}" data-tab="{1}">{2}</button>'.format(cls, t["id"], t["label"]))
    return "".join(parts)


def _missing_box_html(s, m):
    if "tờ khai" in m or "VN" in m:
        target_tab = "nhap"
    elif "Biển số" in m or "giờ lấy" in m or "Packing" in m:
        target_tab = "lay-hang"
    else:
        target_tab = "tai-chinh"
    to = "/lo-hang-detail?id={0}&tab={1}".format(s["id"], target_tab)
    return """
<div class="lg-missing" style="margin-bottom:8px">
  <span class="body">
    <h5>Thiếu {0}</h5>
  </span>
  <a class="btn" data-to="{1}">{2} Bổ sung ngay</a>
</div>
""".format(m, to, icons.pen(16, "#fff"))


def _render_shipment_tab_layhang(s):
    pickup = s.get("pickup", {})
    cargo = s.get("cargo", {})
    export = s.get("exportInfo", {})
    docs = s.get("docs", [])

    factory_html = """
<div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:14px">
  <p style="font-size:15px;font-weight:700;margin:0">{0}</p>
  <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">{1}</p>
  <p style="font-size:14px;margin:6px 0 0;display:flex;align-items:center;gap:6px">{2} {3} · {4}</p>
</div>
""".format(pickup.get("factory", "—"), pickup.get("address", "—"), icons.phone(15, "#94a3b8"), pickup.get("contact", "—"), pickup.get("phone", "—"))

    missing_pickup_err = "Thiếu giờ lấy — nhà máy cần báo trước 24h" if not pickup.get("pickupTime") else None
    missing_xe_html = ('<div class="lg-missing" style="margin-bottom:8px"><span class="body"><h5>Thiếu biển số + tài xế xe TQ</h5><p>Chưa đặt được xe — bổ sung để nhà máy cho hàng lên xe</p></span><a class="btn" data-to="/lo-hang-detail?id={0}&tab=lay-hang">Nhập xe ngay</a></div>'.format(s["id"])) if not (pickup.get("plate") and pickup.get("driver")) else ''

    left = """
<div class="lg-card" style="display:flex;flex-direction:column;gap:16px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;display:flex;align-items:center;gap:8px;margin:0">{0} Nhà máy & lịch lấy hàng</h3>
  {1}
  {2}
  {3}
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;display:flex;align-items:center;gap:8px;margin:0">{4} Xe Trung Quốc</h3>
  {5}
  {6}
  {7}
  {8}
  <div class="lg-cols-2">
    {9}
    {10}
  </div>
  <button class="lg-btn primary full" onclick="window.parent.postMessage({{'type':'donor','action':'save_pickup','sid':'{11}'}},'*')">💾 LƯU THÔNG TIN LẤY HÀNG</button>
</div>
""".format(
        icons.map_pin(19, "#1e5aa8"),
        factory_html,
        _field("Thời gian lấy hàng", required=not pickup.get("pickupTime"), value=pickup.get("pickupTime", ""), placeholder="VD: 10/09/2026 09:00", error=missing_pickup_err, key="fld_pickup_time"),
        _field("Loại / kích thước xe", value=pickup.get("truckType", ""), key="fld_truck_type"),
        icons.truck(19, "#1e5aa8"),
        missing_xe_html,
        _field("Biển số xe", required=not pickup.get("plate"), value=pickup.get("plate", ""), placeholder="VD: 粤A·88T36", key="fld_plate"),
        _field("Tài xế", required=not pickup.get("driver"), value=pickup.get("driver", ""), placeholder="Tên tài xế", key="fld_driver"),
        _field("SĐT tài xế", value=pickup.get("driverPhone", ""), placeholder="+86…", key="fld_driver_phone"),
        _field("Ngày dự kiến", value=pickup.get("eta", ""), key="fld_eta"),
        _field("Ngày thực tế", value=pickup.get("ata", ""), placeholder="—", key="fld_ata"),
        s["id"],
    )

    cargo_items = [
        ("Số kiện", str(cargo.get("packs", ""))),
        ("Trọng lượng", cargo.get("weight", "")),
        ("CBM", str(cargo.get("cbm", ""))),
        ("Kích thước", cargo.get("dims", "")),
        ("Loại hàng", cargo.get("type", "")),
    ]
    cargo_cells = "".join(
        '<div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:12px"><p style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#94a3b8;margin:0">{0}</p><p style="font-size:15px;font-weight:700;color:#0f2a4a;margin:2px 0 0">{1}</p></div>'.format(k, v)
        for k, v in cargo_items
    )
    cargo_html = '<div class="lg-cols-3">' + cargo_cells + '</div>'
    note_html = ('<p style="margin-top:10px;font-size:13.5px;background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:12px">📌 Ghi chú: {0}</p>'.format(cargo.get("note", ""))) if cargo.get("note") else ""

    export_state = export.get("state", "—")
    export_tone = "green" if "Đã" in export_state else "amber"

    checklist = "".join(_doc_row(s, d) for d in docs)

    right = """
<div style="display:flex;flex-direction:column;gap:16px">
  <div class="lg-card">
    <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;display:flex;align-items:center;gap:8px;margin:0 0 12px">{0} Hàng hóa</h3>
    {1}
    {2}
  </div>
  <div class="lg-card">
    <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Xuất khẩu — {3}</h3>
    <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">Đơn vị khai</span><span style="font-weight:600">{4}</span></div>
    <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">Ngày dự kiến / thực tế</span><span style="font-weight:600">{5} / {6}</span></div>
    <div style="display:flex;justify-content:space-between;padding:8px 0"><span style="font-size:13.5px;color:#64748b">Trạng thái</span><span class="lg-badge {7} sm">{8}</span></div>
  </div>
  <div class="lg-card">
    <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 4px">Checklist chứng từ xuất khẩu</h3>
    <p style="font-size:13px;color:#64748b;margin:0 0 12px">Hiện trạng → thiếu gì → bấm để bổ sung. Không có cảnh báo cụt.</p>
    <div style="display:flex;flex-direction:column;gap:8px">{9}</div>
  </div>
</div>
""".format(icons.package(19, "#1e5aa8"), cargo_html, note_html, export.get("border", ""), export.get("declarant", ""), export.get("eta", ""), export.get("ata", "chưa có"), export_tone, export_state, checklist)

    st.markdown('<div class="lg-2col" style="margin-top:16px">{0}{1}</div>'.format(left, right), unsafe_allow_html=True)


def _doc_row(s, d):
    if d.get("ok"):
        return """
<div style="display:flex;align-items:center;gap:12px;border:2px solid #bbf7d0;background:#f0fdf4;border-radius:12px;padding:12px">
  <span style="width:32px;height:32px;border-radius:999px;background:#10b981;color:#fff;display:grid;place-items:center;font-weight:800">✓</span>
  <div style="flex:1"><p style="font-size:14.5px;font-weight:700;margin:0">{0} — <span style="color:#047857">✅ Đủ</span></p><p style="font-size:13px;color:#475569;margin:2px 0 0">{1}</p></div>
</div>
""".format(d["name"], d.get("note", ""))
    return """
<div style="display:flex;align-items:center;gap:12px;border:2px solid #fcd34d;background:#fffbeb;border-radius:12px;padding:12px">
  <span style="width:32px;height:32px;border-radius:999px;background:#f59e0b;color:#fff;display:grid;place-items:center;font-weight:800">!</span>
  <div style="flex:1"><p style="font-size:14.5px;font-weight:700;margin:0">{0} — <span style="color:#b45309">Thiếu</span></p><p style="font-size:13px;color:#475569;margin:2px 0 0">{1}</p></div>
  <a class="lg-btn" style="background:#f59e0b;color:#fff;min-height:44px;padding:8px 14px" data-to="/lo-hang-detail?id={2}&tab=chung-tu">Bổ sung</a>
</div>
""".format(d["name"], d.get("note", ""), s["id"])


def _render_shipment_tab_nhap(s):
    info = s.get("importInfo", {})

    if not info.get("declarationNo"):
        missing_left = '<div class="lg-missing" style="margin-bottom:12px"><span class="body"><h5>Thiếu số tờ khai nhập khẩu</h5><p>Hàng đang chờ ở bãi VN — có số TK mới nộp thuế & phân luồng được</p></span><a class="btn" data-to="/lo-hang-detail?id={0}&tab=nhap">Nhập số TK</a></div>'.format(s["id"])
    else:
        missing_left = ""

    success_banner = ('<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:12px;font-size:13.5px;color:#1e3a8a">✅ Đã có số TK <b>{0}</b>. Tiếp theo: nộp thuế rồi bấm "Thông quan" khi có kết quả phân luồng.</div>'.format(info.get("declarationNo", ""))) if info.get("declarationNo") else ""

    left = """
<div class="lg-card" style="display:flex;flex-direction:column;gap:16px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0">Tờ khai & thuế nhập khẩu — {border}</h3>
  {missing}
  <div class="lg-cols-2">
    {f1}
    {f2}
    {f3}
    {f4}
    {f5}
    {f6}
  </div>
  <button class="lg-btn primary full" onclick="window.parent.postMessage({{'type':'donor','action':'save_import','sid':'{sid}'}},'*')">💾 LƯU TỜ KHAI & THUẾ</button>
  {ok}
</div>
""".format(
        border=info.get("borderVN", ""),
        missing=missing_left,
        f1=_field("Số tờ khai", required=not info.get("declarationNo"), value=info.get("declarationNo", ""), placeholder="12 số tờ khai…", error="Nhập 12 số tờ khai — VD: 105588421330" if not info.get("declarationNo") else None, key="fld_tk"),
        f2=_field("Ngày đăng ký", value=info.get("regDate", ""), placeholder="VD: 09/09/2026", key="fld_regdate"),
        f3=_field("Thuế nhập khẩu (VND)", value=str(info.get("tax", "") or ""), placeholder="VD: 48200000", key="fld_tax"),
        f4=_field("VAT hàng nhập (VND)", value=str(info.get("vat", "") or ""), placeholder="VD: 96400000", key="fld_vat"),
        f5=_field("Phân luồng / kiểm hóa", value=info.get("inspection", ""), key="fld_insp"),
        f6=_field("Giấy phép chuyên ngành", value=info.get("license", ""), key="fld_license"),
        sid=s["id"],
        ok=success_banner,
    )

    if not info.get("delivered") and (not info.get("driverVN") or not info.get("plateVN")):
        missing_right = '<div class="lg-missing" style="margin-bottom:12px"><span class="body"><h5>Thiếu xe VN + tài xế</h5><p>Chưa đặt xe — đặt trước giờ giao ít nhất 4 tiếng</p></span><a class="btn" data-to="/lo-hang-detail?id={0}&tab=nhap">Đặt xe ngay</a></div>'.format(s["id"])
    else:
        missing_right = ""

    if info.get("delivered"):
        delivered_block = """
<div style="background:#ecfdf5;border:2px solid #bbf7d0;border-radius:12px;padding:16px;text-align:center">
  <p style="font-size:17px;font-weight:800;color:#065f46;margin:0">✅ ĐÃ GIAO HÀNG XONG</p>
  <p style="font-size:13.5px;color:#047857;margin:2px 0 0">{0} · Sang tab Chứng từ để xuất PXK →</p>
  <a class="lg-btn success" style="margin-top:10px" data-to="/lo-hang-detail?id={1}&tab=chung-tu">SANG XUẤT PHIẾU XUẤT KHO →</a>
</div>
""".format(info.get("actualDelivery", ""), s["id"])
    else:
        delivered_block = '<button class="lg-btn success full" style="font-size:17px;min-height:56px" onclick="window.parent.postMessage({{&quot;type&quot;:&quot;donor&quot;,&quot;action&quot;:&quot;confirm_delivery&quot;,&quot;sid&quot;:&quot;{0}&quot;}},"*")">✅ XÁC NHẬN ĐÃ GIAO HÀNG</button>'.format(s["id"])

    actual_html = ('<p style="font-size:14px;color:#047857;font-weight:700;margin:4px 0 0">✅ Đã giao: {0}</p>'.format(info.get("actualDelivery", ""))) if info.get("actualDelivery") else ""

    right = """
<div class="lg-card" style="display:flex;flex-direction:column;gap:16px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;display:flex;align-items:center;gap:8px;margin:0">{0} Xe Việt Nam & giao hàng</h3>
  {1}
  <div class="lg-cols-2">
    {2}
    {3}
    {4}
    {5}
  </div>
  <div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:14px">
    <p style="font-size:12.5px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#94a3b8;margin:0">Địa chỉ giao</p>
    <p style="font-size:15px;font-weight:700;margin:2px 0 0">{6}</p>
    <p style="font-size:14px;color:#475569;margin:4px 0 0">Người nhận: <b>{7}</b> · {8}</p>
    {9}
  </div>
  {10}
</div>
""".format(
        icons.truck(19, "#1e5aa8"),
        missing_right,
        _field("Loại xe VN", value=info.get("truckVN", ""), key="fld_truckvn"),
        _field("Biển số VN", value=info.get("plateVN", ""), placeholder="VD: 29H-481.36", key="fld_platevn"),
        _field("Tài xế VN", value=info.get("driverVN", ""), placeholder="Tên tài xế", key="fld_drivervn"),
        _field("Lịch giao", value=info.get("schedule", ""), key="fld_schedule"),
        info.get("deliveryAddr", ""),
        info.get("receiver", ""),
        info.get("receiverPhone", ""),
        actual_html,
        delivered_block,
    )

    st.markdown('<div class="lg-2col" style="margin-top:16px">{0}{1}</div>'.format(left, right), unsafe_allow_html=True)


def _render_shipment_tab_finance(s):
    fin = s.get("finance", {})
    recv = fin.get("receivable", 0)
    received = fin.get("received", 0)
    payable = fin.get("payable", 0)
    paid = fin.get("paid", 0)
    quote = fin.get("quote", [])
    actual = fin.get("actual", [])
    payments = fin.get("payments", [])

    def fmt_m(v, ccy="VND"):
        return design.fmt_money(v, ccy)

    quote_rows = "".join(
        '<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">{0}</span><span style="font-weight:700;font-size:16px">{1} <span style="font-size:12px;font-weight:700;color:#7c3aed">{2}</span></span></div>'.format(c["label"], fmt_m(c["amount"], c.get("ccy", "VND")), c.get("ccy", "VND"))
        for c in quote
    )
    actual_rows = "".join(
        '<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">{0}</span><span style="font-weight:700;font-size:16px">{1} <span style="font-size:12px;font-weight:700;color:#047857">{2}</span></span></div>'.format(c["label"], fmt_m(c["amount"], c.get("ccy", "VND")), c.get("ccy", "VND"))
        for c in actual
    )

    quote_block = """
<div class="lg-card" style="border:2px dashed #c4b5fd;background:#faf5ff">
  <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;color:#5b21b6;background:#ede9fe;display:inline-block;padding:2px 8px;border-radius:6px">Báo giá / Dự kiến — chưa phải số thực thu/chi</span>
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:8px 0 12px">Chi phí dự kiến theo báo giá</h3>
  {rows}
  <p style="font-size:12.5px;color:#94a3b8;margin:8px 0 0">Mỗi đồng tiền ghi rõ VND / USD / CNY — không gộp chung.</p>
</div>
""".format(rows=quote_rows or '<p style="font-size:14px;color:#64748b">Chưa gắn báo giá. <a class="lg-link" data-to="/kinh-doanh-bao-gia">Mở báo giá →</a></p>')

    actual_block = """
<div class="lg-card" style="border:2px solid #bbf7d0;background:#f0fdf4">
  <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;color:#047857;background:#d1fae5;display:inline-block;padding:2px 8px;border-radius:6px">Thực tế — đã phát sinh, có chứng từ</span>
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:8px 0 12px">Chi phí thực tế</h3>
  {rows}
</div>
""".format(rows=actual_rows or '<p style="font-size:14px;color:#64748b">Chưa phát sinh chi phí thực tế.</p>')

    st.markdown('<div class="lg-cols-2" style="margin-top:16px">{0}{1}</div>'.format(quote_block, actual_block), unsafe_allow_html=True)

    recv_m = recv / 1e6
    received_m = received / 1e6
    rec_due_m = (recv - received) / 1e6
    payable_m = payable / 1e6
    paid_m = paid / 1e6
    pay_due_m = (payable - paid) / 1e6

    receivable_block = """
<div class="lg-card">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;display:flex;align-items:center;gap:8px;margin:0 0 8px">{0} Phải thu khách hàng (VND)</h3>
  <div class="lg-cols-3" style="text-align:center">
    <div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:12px"><p style="font-size:12px;color:#64748b;font-weight:600;margin:0">Phải thu</p><p style="font-size:17px;font-weight:800;margin:4px 0 0">{1:.1f} tr</p></div>
    <div style="background:#ecfdf5;border:1px solid #bbf7d0;border-radius:12px;padding:12px"><p style="font-size:12px;color:#047857;font-weight:600;margin:0">Đã thu</p><p style="font-size:17px;font-weight:800;color:#047857;margin:4px 0 0">{2:.1f} tr</p></div>
    <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:12px"><p style="font-size:12px;color:#dc2626;font-weight:600;margin:0">Còn phải thu</p><p style="font-size:17px;font-weight:800;color:#b91c1c;margin:4px 0 0">{3:.1f} tr</p></div>
  </div>
  <button class="lg-btn success full" style="margin-top:12px" onclick="window.parent.postMessage({{'type':'donor','action':'pay_dialog','sid':'{4}'}},'*')">＋ GHI NHẬN THANH TOÁN</button>
</div>
""".format(icons.wallet(19, "#059669"), recv_m, received_m, rec_due_m, s["id"])

    payable_block = """
<div class="lg-card">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 8px">Phải trả đối tác (VND)</h3>
  <div class="lg-cols-3" style="text-align:center">
    <div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:12px"><p style="font-size:12px;color:#64748b;font-weight:600;margin:0">Phải trả</p><p style="font-size:17px;font-weight:800;margin:4px 0 0">{0:.1f} tr</p></div>
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:12px"><p style="font-size:12px;color:#1e40af;font-weight:600;margin:0">Đã trả</p><p style="font-size:17px;font-weight:800;color:#1e40af;margin:4px 0 0">{1:.1f} tr</p></div>
    <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:12px"><p style="font-size:12px;color:#b45309;font-weight:600;margin:0">Còn phải trả</p><p style="font-size:17px;font-weight:800;color:#b45309;margin:4px 0 0">{2:.1f} tr</p></div>
  </div>
  <a class="lg-btn ghost full" style="margin-top:12px" data-to="/tai-chinh/doi-soat">MỞ ĐỐI SOÁT</a>
</div>
""".format(payable_m, paid_m, pay_due_m)

    st.markdown('<div class="lg-cols-2" style="margin-top:16px">{0}{1}</div>'.format(receivable_block, payable_block), unsafe_allow_html=True)

    pay_rows = ""
    for p in payments:
        note_p = (" · " + p["note"]) if p.get("note") else ""
        pay_rows += """
<div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px;border:1px solid #e4e9f1;border-radius:12px;padding:12px">
  <span style="font-size:12.5px;font-weight:700;color:#94a3b8;min-width:92px">{0}</span>
  <span style="flex:1;min-width:160px"><span style="display:block;font-weight:700;font-size:14.5px">{1}</span><span style="display:block;font-size:12.5px;color:#64748b">{2}{3}</span></span>
  <span style="font-weight:800;font-size:15.5px">{4} <span style="font-size:11.5px;color:#94a3b8">{5}</span></span>
  <button style="height:40px;padding:0 12px;border:1px solid #e4e9f1;border-radius:10px;background:#fff;font-size:13px;font-weight:700;color:#1e5aa8;cursor:pointer">Điều chỉnh</button>
</div>
""".format(p.get("date", ""), p.get("kind", ""), p.get("by", ""), note_p, fmt_m(p.get("amount", 0), p.get("ccy", "VND")), p.get("ccy", "VND"))

    history_html = """
<div class="lg-card" style="margin-top:16px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Lịch sử thu / chi — sửa bằng điều chỉnh, không xóa</h3>
  <div style="display:flex;flex-direction:column;gap:8px">{0}</div>
</div>
""".format(pay_rows or '<p style="font-size:14px;color:#64748b">Chưa ghi nhận khoản nào.</p>')
    st.markdown(history_html, unsafe_allow_html=True)


def _render_shipment_tab_chungtu(s):
    s_id = s["id"]
    linked = store.find_contract(s.get("contract", ""))
    info = s.get("importInfo", {})
    pxk = s.get("pxk", {})

    if not info.get("delivered"):
        missing = '<div class="lg-missing" style="margin:0 0 12px"><span class="body"><h5>Thiếu xác nhận đã giao hàng</h5><p>Phải giao xong mới được xuất PXK</p></span><a class="btn" data-to="/lo-hang-detail?id={0}&tab=nhap">Sang xác nhận giao</a></div>'.format(s_id)
    else:
        missing = ""

    if linked:
        contract_html = """
<div class="lg-card" style="border:2px solid #e4e9f1">
  <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px">
    <span style="font-size:17px;font-weight:800;color:#0f2a4a">{0}</span>
    <span class="lg-badge {1} sm">{2}</span>
  </div>
  <p style="font-size:14px;color:#475569;margin:6px 0 0">{3} · Giá trị {4}</p>
  <div class="lg-cols-2" style="margin-top:12px">
    <a class="lg-btn ghost" data-to="/hop-dong-detail?id={5}">{6} MỞ HỢP ĐỒNG</a>
    <button class="lg-btn primary" onclick="window.parent.postMessage({{'type':'donor','action':'download_contract','id':'{7}'}},'*')">{8} TẢI HỢP ĐỒNG</button>
  </div>
</div>
""".format(linked["id"], linked.get("statusTone", "gray"), linked.get("status", ""), linked.get("companyLegal", ""), design.fmt_vnd(linked.get("value", 0)), linked["id"], icons.eye(16, "#0f2a4a"), linked["id"], icons.download(16, "#fff"))
    else:
        contract_html = '<p style="font-size:14px;color:#64748b">Lô chưa gắn hợp đồng. <a class="lg-link" data-to="/hop-dong">Chọn hợp đồng →</a></p>'

    docs_html = ""
    for d in s.get("docs", []):
        if d.get("ok"):
            docs_html += """
<div style="display:flex;align-items:center;gap:10px;border:1px solid #e4e9f1;border-radius:12px;padding:10px">
  <span style="width:28px;height:28px;border-radius:999px;background:#10b981;color:#fff;display:grid;place-items:center;font-weight:800;font-size:13px">✓</span>
  <span style="flex:1;font-weight:600;font-size:14px">{0}</span>
  <button class="lg-btn ghost sm">{1} Tải</button>
</div>
""".format(d["name"], icons.download(14, "#0f2a4a"))
        else:
            docs_html += """
<div style="display:flex;align-items:center;gap:10px;border:1px solid #e4e9f1;border-radius:12px;padding:10px">
  <span style="width:28px;height:28px;border-radius:999px;background:#f59e0b;color:#fff;display:grid;place-items:center;font-weight:800;font-size:13px">!</span>
  <span style="flex:1;font-weight:600;font-size:14px">{0}</span>
  <button class="lg-btn sm" style="background:#f59e0b;color:#fff">＋ Bổ sung</button>
</div>
""".format(d["name"])

    left = """
<div class="lg-card">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;display:flex;align-items:center;gap:8px;margin:0 0 12px">{0} Hợp đồng liên kết</h3>
  {1}
  <div style="margin-top:16px">
    <h4 style="font-size:14.5px;font-weight:700;margin:0 0 8px">Chứng từ lô hàng — bấm để tải / bổ sung</h4>
    <div style="display:flex;flex-direction:column;gap:8px">{2}</div>
  </div>
</div>
""".format(icons.file_text(19, "#1e5aa8"), contract_html, docs_html)

    delivered_label = ("✅ Rồi — " + info.get("actualDelivery", "")) if info.get("delivered") else "❌ Chưa"
    delivered_color = "#047857" if info.get("delivered") else "#dc2626"
    src_default = pxk.get("source") or s.get("contract", "")

    if pxk.get("done"):
        pxk_action_html = """
<div style="margin-top:12px;background:#ecfdf5;border:2px solid #bbf7d0;border-radius:12px;padding:16px;text-align:center">
  <p style="font-weight:800;color:#065f46;margin:0">✅ ĐÃ XUẤT {0}</p>
  <button class="lg-btn success" style="margin-top:10px" onclick="window.parent.postMessage({{'type':'donor','action':'export_pxk','sid':'{1}'}},'*')">{2} TẢI LẠI PXK</button>
</div>
""".format(pxk.get("number", ""), s_id, icons.download(17, "#fff"))
    else:
        pxk_action_html = '<button class="lg-btn success full" style="margin-top:12px;font-size:16px;min-height:56px" onclick="window.parent.postMessage({{&quot;type&quot;:&quot;donor&quot;,&quot;action&quot;:&quot;export_pxk&quot;,&quot;sid&quot;:&quot;{0}&quot;}},"*")">🖨 XUẤT PHIẾU XUẤT KHO</button>'.format(s_id)

    right = """
<div class="lg-card" style="border:2px solid #0f2a4a">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 4px">Phiếu xuất kho (PXK) — theo từng lô</h3>
  <p style="font-size:13px;color:#64748b;margin:0 0 12px">PXK gắn với lô đã giao, nguồn từ {0}. Mỗi lô 1 PXK riêng.</p>
  {1}
  <div class="lg-cols-2">
    {2}
    {3}
    {4}
    {5}
    {6}
    {7}
  </div>
  <div style="margin-top:12px;background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:12px;font-size:13.5px">
    <p style="margin:0">Đã giao hàng xong: <b style="color:{8}">{9}</b></p>
    <p style="margin:4px 0 0">Ngày giao: <b>{10}</b></p>
  </div>
  {11}
</div>
""".format(
        src_default,
        missing,
        _field("Số PXK", value=pxk.get("number", ""), placeholder="Tự sinh khi xuất", key="fld_pxk_no"),
        _field("Ngày PXK", value=pxk.get("date", "") or "09/09/2026", key="fld_pxk_date"),
        _field("Địa điểm nhận", value=pxk.get("place", "") or info.get("deliveryAddr", ""), key="fld_pxk_place"),
        _field("Người nhận", value=pxk.get("receiver", "") or info.get("receiver", ""), key="fld_pxk_receiver"),
        _field("Chức vụ người nhận", value=pxk.get("role", "") or "Thủ kho", key="fld_pxk_role"),
        _field("Nguồn (HDMB/PL)", value=pxk.get("source", "") or s.get("contract", ""), key="fld_pxk_source"),
        delivered_color,
        delivered_label,
        info.get("actualDelivery") or info.get("schedule") or "—",
        pxk_action_html,
    )

    st.markdown('<div class="lg-2col" style="margin-top:16px">{0}{1}</div>'.format(left, right), unsafe_allow_html=True)


def _render_shipment_tab_history(s):
    timeline = s.get("timeline", [])
    rows = ""
    for t in timeline:
        tone = t.get("tone", "blue")
        dot_color = {"green": "#10b981", "amber": "#f59e0b", "red": "#dc2626", "blue": "#2563eb"}.get(tone, "#2563eb")
        desc = ('<p style="font-size:13.5px;color:#475569;margin:2px 0 0">{0}</p>'.format(t.get("desc", ""))) if t.get("desc") else ""
        rows += """
<div style="position:relative;padding:0 0 16px 24px">
  <span style="position:absolute;left:-4px;top:4px;width:18px;height:18px;border-radius:999px;background:{0};border:3px solid #fff;box-shadow:0 0 0 1px #cbd5e1"></span>
  <p style="font-size:12.5px;font-weight:700;color:#94a3b8;margin:0">{1}</p>
  <p style="font-size:15px;font-weight:700;color:#0f2a4a;margin:2px 0 0">{2}</p>
  {3}
</div>
""".format(dot_color, t.get("time", ""), t.get("title", ""), desc)

    history_html = """
<div class="lg-card" style="margin-top:16px;max-width:800px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 16px">Dòng thời gian — {0}</h3>
  <div style="position:relative;padding-left:14px;border-left:2px solid #cbd5e1">{1}</div>
</div>
""".format(s["id"], rows or '<p style="font-size:14px;color:#64748b">Chưa có sự kiện nào.</p>')
    st.markdown(history_html, unsafe_allow_html=True)


def _field(label, required=False, value="", placeholder="", error=None, key=None):
    star = '<span style="color:#dc2626">*</span>' if required else ""
    error_html = ('<p class="lg-field-error">⚠ ' + error + '</p>') if error else ""
    missing_cls = " missing" if (required and not value) else ""
    return """
<div class="lg-field">
  <label class="lg-field-label">{0} {1}</label>
  <input class="lg-input{2}" placeholder="{3}" value="{4}" />
  {5}
</div>
""".format(label, star, missing_cls, placeholder, value, error_html)


def render_customers():
    customers = list(store.get_customers().values())
    q = st.text_input("", placeholder="Tìm tên công ty, MST, liên hệ…", key="cust_q", label_visibility="collapsed")
    filtered = [c for c in customers if not q or q.lower() in (c["name"] + c["mst"] + c.get("contact", "")).lower()]

    header_html = """
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{0}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Khách Hàng</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Hiện trạng công nợ → hành động: tạo báo giá, tạo lô, xem hợp đồng</p>
      </div>
    </div>
  </div>
</div>
""".format(icons.users(20, "#fff"))
    st.markdown(header_html, unsafe_allow_html=True)

    if filtered:
        rows = []
        for c in filtered:
            if c.get("debt"):
                debt_html = '<span style="font-weight:800;color:#b91c1c">{0}</span>'.format(design.fmt_vnd(c["debt"]))
            else:
                debt_html = '<span style="font-weight:700;color:#047857">Hết nợ ✓</span>'
            action_html = '<div style="display:flex;gap:6px;flex-wrap:wrap"><a class="lg-btn primary sm" data-to="/kinh-doanh-bao-gia">＋ Báo giá</a><a class="lg-btn ghost sm" data-to="/tao-lo-moi">＋ Lô</a><a class="lg-btn ghost sm" data-to="/hop-dong">Hợp đồng</a></div>'
            rows.append([
                '<b>{0}</b>'.format(c["name"]),
                '<span style="font-weight:600">{0}</span><br><span style="font-size:13px;color:#64748b">{1}</span>'.format(c["mst"], c.get("contact", "")),
                c.get("sale", ""),
                '<b style="text-align:center;display:block">{0}</b>'.format(c.get("lots", 0)),
                debt_html,
                '<span style="font-size:13px;color:#64748b">{0}</span>'.format(c.get("updated", "")),
                action_html,
            ])
        _render_table(["Khách hàng", "MST · Liên hệ", "Sale", "Số lô", "Công nợ", "Cập nhật", "Hành động"], rows, min_width="960px")

    ui._install_goto_bridge()


def render_quotes():
    quotes = store.get_quotes()
    top_html = """
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{0}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Kinh Doanh & Báo Giá</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Lập dự toán → gửi khách → khách chốt → tạo thỏa thuận. Mọi số đều ghi rõ BÁO GIÁ / DỰ KIẾN.</p>
      </div>
    </div>
    <a class="lg-btn primary" data-to="action:open_quick_add">＋ Tạo báo giá</a>
  </div>
  <div class="lg-cols-4">
""".format(icons.calculator(20, "#fff"))
    st.markdown(top_html, unsafe_allow_html=True)

    stTone = {"ACCEPTED": ("ĐÃ CHỐT", "green"), "SENT": ("ĐÃ GỬI", "blue"), "REJECTED": ("TỪ CHỐI", "red"), "DRAFT": ("NHÁP", "gray")}
    cards = ""
    for q in quotes:
        lbl, tone = stTone.get(q["status"], (q["status"], "gray"))
        price_html = ("{0:.1f}tr".format(q["price"] / 1e6)) if q.get("price") else "—"
        cost_html = ("{0:.1f}tr".format(q["cost"] / 1e6)) if q.get("cost") else "—"
        if q["status"] == "DRAFT":
            action_html = '<button class="lg-btn primary sm full" onclick="window.parent.postMessage({type:&quot;donor&quot;,action:&quot;send_quote&quot;,id:&quot;' + q["id"] + '&quot;},&apos;*&apos;)">GỬI KHÁCH</button>'
        elif q["status"] == "SENT":
            action_html = '<button class="lg-btn success sm full" onclick="window.parent.postMessage({type:&quot;donor&quot;,action:&quot;accept_quote&quot;,id:&quot;' + q["id"] + '&quot;},&apos;*&apos;)">KHÁCH ĐÃ CHỐT</button>'
        elif q["status"] == "ACCEPTED":
            action_html = '<a class="lg-btn success sm full" data-to="/thoa-thuan-ban-giao">Lập thỏa thuận</a>'
        else:
            action_html = ""
        cards += """
<div style="border:2px solid #e4e9f1;border-radius:16px;padding:16px">
  <div style="display:flex;align-items:center;gap:6px"><span style="font-size:15px;font-weight:800;color:#0f2a4a">{0}</span><span class="lg-badge {1} sm">{2}</span></div>
  <p style="font-size:14px;font-weight:600;margin:4px 0 0">{3}</p>
  <p style="font-size:12.5px;color:#64748b;margin:2px 0 0">{4} · {5}</p>
  <div class="lg-cols-3" style="text-align:center;font-size:12px;margin-top:10px">
    <div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:8px;padding:6px"><p style="color:#64748b;margin:0">Chi phí</p><b>{6}</b></div>
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:6px"><p style="color:#64748b;margin:0">Giá bán</p><b>{7}</b></div>
    <div style="background:#ecfdf5;border:1px solid #bbf7d0;border-radius:8px;padding:6px"><p style="color:#64748b;margin:0">Margin</p><b style="color:#047857">{8}</b></div>
  </div>
  <div class="lg-cols-2" style="margin-top:10px">{9}<button class="lg-btn ghost sm">Chi tiết</button></div>
</div>
""".format(q["id"], tone, lbl, q["customer"], q["route"], q.get("goods", ""), cost_html, price_html, q.get("margin", "—"), action_html)

    st.markdown(cards, unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)
    ui._install_goto_bridge()


def render_agreements():
    ags = store.get_agreements()
    steps = ["1 · Báo giá", "2 · Khách chốt", "3 · Thỏa thuận", "4 · Bàn giao Support"]
    steps_html = '<div style="border-radius:16px;background:#fff;border:1px solid #e4e9f1;padding:16px;display:flex;align-items:center;gap:6px;overflow-x:auto">'
    for i, s in enumerate(steps):
        if i < 3:
            steps_html += '<span style="background:#10b981;color:#fff;border-radius:12px;padding:10px 14px;font-size:13.5px;font-weight:800;white-space:nowrap">✓ {0}</span><span style="color:#cbd5e1">→</span>'.format(s)
        else:
            steps_html += '<span style="background:#f1f5f9;color:#64748b;border-radius:12px;padding:10px 14px;font-size:13.5px;font-weight:800;white-space:nowrap">{0}</span>'.format(s)
    steps_html += '</div>'

    header_html = """
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{0}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Thỏa Thuận & Bàn Giao</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Báo giá chốt → thỏa thuận điều khoản → bàn giao Support kèm bằng chứng</p>
      </div>
    </div>
  </div>
  {1}
</div>
""".format(icons.handshake(20, "#fff"), steps_html)
    st.markdown(header_html, unsafe_allow_html=True)

    toneMap = {"AGREED": "green", "REVIEWING": "amber", "VOID": "red"}
    cards = ""
    for a in ags:
        tone = toneMap.get(a["status"], "blue")
        if a["status"] != "AGREED":
            agree_btn = '<button class="lg-btn success" onclick="window.parent.postMessage({type:&quot;donor&quot;,action:&quot;agree&quot;,id:&quot;{0}&quot;},&apos;*&apos;)">KHÁCH ĐÃ CHỐT ĐIỀU KHOẢN</button>'.format(a["id"])
        else:
            agree_btn = ""
        handover_btn = '<button class="lg-btn primary" onclick="window.parent.postMessage({type:&quot;donor&quot;,action:&quot;handover&quot;,id:&quot;' + a["id"] + '&quot;},&apos;*&apos;)">BÀN GIAO SUPPORT</button>'
        cards += """
<div class="lg-card" style="margin-bottom:12px">
  <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px">
    <span style="font-size:16px;font-weight:800;color:#0f2a4a">{0}</span>
    <span class="lg-badge {1} sm">{2}</span>
    <span style="font-size:13px;color:#64748b">Báo giá {3} · {4}</span>
  </div>
  <div class="lg-cols-2" style="margin-top:10px;font-size:14px">
    <p style="margin:0"><span style="color:#64748b">Incoterm:</span> <b>{5}</b></p>
    <p style="margin:0"><span style="color:#64748b">Thanh toán:</span> <b>{6}</b></p>
    <p style="margin:0;grid-column:1 / -1"><span style="color:#64748b">Phạm vi:</span> {7}</p>
    <p style="margin:0;grid-column:1 / -1"><span style="color:#64748b">Bàn giao:</span> <b>{8}</b></p>
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px">
    {9}{10}<a class="lg-btn ghost" data-to="/hop-dong/moi">Lập hợp đồng →</a>
  </div>
</div>
""".format(a["id"], tone, a["status"], a.get("quote", ""), a.get("customer", ""), a.get("incoterm", ""), a.get("payment", ""), a.get("scope", ""), a.get("handover", ""), agree_btn, handover_btn)
    st.markdown(cards, unsafe_allow_html=True)
    ui._install_goto_bridge()


def render_partner_context():
    header_html = """
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{0}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Ngữ Cảnh Đối Tác</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Đại lý & cửa khẩu — ai làm gì, liên hệ ai, số dư ra sao</p>
      </div>
    </div>
  </div>
</div>
""".format(icons.building(20, "#fff"))
    st.markdown(header_html, unsafe_allow_html=True)

    body_html = """
<div class="lg-2col">
  <div class="lg-card">
    <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Đại lý: Phú Anh Logistics Việt Nam</h3>
    <div style="font-size:14px;display:flex;flex-direction:column;gap:6px">
      <p style="margin:0"><span style="color:#64748b">Pháp lý:</span> <b>CÔNG TY TNHH PHÚ ANH LOGISTICS VIỆT NAM</b></p>
      <p style="margin:0"><span style="color:#64748b">MST:</span> 0108123456 · <span style="color:#64748b">Đại diện:</span> Nguyễn Phú Anh (Giám đốc)</p>
      <p style="margin:0"><span style="color:#64748b">Đầu TQ:</span> chi nhánh Bằng Tường — Mr. Lưu (+86 139 2611 8899)</p>
      <p style="margin:0"><span style="color:#64748b">Kho VN:</span> Lạng Sơn + Bắc Ninh — Thu Hằng điều phối</p>
      <p style="margin:0"><span style="color:#64748b">TK:</span> 0451000412345 · Vietcombank Thanh Xuân</p>
    </div>
    <div style="margin-top:12px;background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:12px;font-size:13.5px">Số dư phải trả Bằng Tường: <b>73.800.000 ₫</b> + <b>27.700 CNY</b> — <a class="lg-link" data-to="/tai-chinh/doi-soat">Đối soát →</a></div>
  </div>
  <div class="lg-card">
    <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Cửa khẩu & tuyến trọng điểm</h3>
    <div style="display:flex;flex-direction:column;gap:10px">
      <div style="border:1px solid #e4e9f1;border-radius:12px;padding:12px"><p style="font-weight:700;font-size:14.5px;margin:0">Hữu Nghị (TQ↔VN)</p><p style="font-size:13px;color:#64748b;margin:2px 0 0">Cont 40HQ · 6–8 tiếng · LO-0306, 0308 đang đi</p></div>
      <div style="border:1px solid #e4e9f1;border-radius:12px;padding:12px"><p style="font-weight:700;font-size:14.5px;margin:0">Tân Thanh (TQ↔VN)</p><p style="font-size:13px;color:#64748b;margin:2px 0 0">Xe tải · 3–5 tiếng · LO-0307, 0299 đang đi</p></div>
    </div>
    <button class="lg-btn ghost full" style="margin-top:12px">＋ Thêm ghi chú đối tác</button>
  </div>
</div>
"""
    st.markdown(body_html, unsafe_allow_html=True)
    ui._install_goto_bridge()
