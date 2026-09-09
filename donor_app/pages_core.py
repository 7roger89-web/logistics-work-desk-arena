"""Tasks, Shipments, Shipment detail, Customers, Sales pages."""
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
                level_badge = f'<span style="display:inline-block;background:#dc2626;color:#fff;font-size:12.5px;font-weight:800;border-radius:999px;padding:4px 10px">{lvl}</span>'
            elif color == "amber":
                level_badge = f'<span style="display:inline-block;background:#f59e0b;color:#fff;font-size:12.5px;font-weight:800;border-radius:999px;padding:4px 10px">{lvl}</span>'
            else:
                level_badge = f'<span style="display:inline-block;background:#e2e8f0;color:#475569;font-size:12.5px;font-weight:800;border-radius:999px;padding:4px 10px">{lvl}</span>'
            route = t.get("route", "/")
            action_link = f'<a class="lg-btn primary sm" href="?p={route}" target="_self">XỬ LÝ NGAY →</a>'
            lot_link = f'<a class="lg-link" href="?p={route}" target="_self">{t.get("lot", "")}</a>'
            due_html = f'<span style="color:#dc2626;font-weight:700">{t.get("due", "")}</span><br><span style="font-size:12.5px;color:#64748b">{t.get("dueNote", "")}</span>'
            status_badge = f'<span class="lg-badge {t.get("statusTone", "gray")} sm">{t.get("status", "")}</span>'
            rows.append([level_badge, lot_link, t.get("customer", ""), f'<b>{t.get("job", "")}</b>', t.get("assignee", ""), due_html, status_badge, action_link])
        headers = ["Ưu tiên", "Mã lô", "Khách hàng", "Việc cần làm", "Người phụ trách", "Hạn", "Trạng thái", "Hành động"]
        _render_table(headers, rows, min_width="980px")
    else:
        st.info("Không có việc nào khớp.")

    tip_html = f"""
<div class="lg-card" style="margin-top:12px;border-style:dashed;border-color:#cbd5e1">
  <div style="display:flex;align-items:flex-start;gap:10px;font-size:14px;color:#64748b">
    <span style="color:#64748b">{icons.filter_icon(19, "#64748b")}</span>
    <p style="margin:0"><b>Mẹo cho người mới:</b> xử lý theo thứ tự <b>Khẩn → Cần xử lý → Bình thường</b>. Mỗi dòng đều có nút XỬ LÝ NGAY dẫn tới đúng ô nhập liệu.</p>
  </div>
</div>
"""
    st.markdown(tip_html, unsafe_allow_html=True)


def _render_table(headers, rows, min_width="980px"):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = ""
    for r in rows:
        body += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
    html = f"""
<div class="lg-tbl-wrap">
  <div style="overflow-x:auto">
    <table class="lg-tbl" style="min-width:{min_width}">
      <thead><tr>{head}</tr></thead>
      <tbody>{body}</tbody>
    </table>
  </div>
</div>
"""
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

    found_suffix = (f' cho "{q}"') if q else ""
    header_html = f"""
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{icons.package(20, "#fff")}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Lô Hàng</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Tìm theo mã lô · khách · container · hợp đồng · trạng thái · Sale · Support · tuyến · cửa khẩu</p>
      </div>
    </div>
    <a class="lg-btn primary" href="?p=/tao-lo-moi" target="_self" style="min-width:auto">＋ Tạo lô mới</a>
  </div>
  <p style="font-size:13.5px;color:#64748b;margin:8px 0 0">Tìm thấy <b style="color:#0f2a4a">{len(filtered)} lô</b>{found_suffix} · Mỗi lô hiển thị: hiện trạng → việc tiếp theo → nút xử lý.</p>
</div>
"""
    st.markdown(header_html, unsafe_allow_html=True)

    if filtered:
        rows = []
        for s in filtered:
            id_link = f'<a class="lg-link" href="?p=/lo-hang-detail&id={s["id"]}" target="_self" style="font-size:15px;font-weight:800">{s["id"]}</a><br><span style="font-size:12px;color:#94a3b8">Cập nhật {s.get("updated", "")}</span>'
            contract_route = f'<span style="font-size:13px;font-weight:600;color:#475569">{s.get("contract", "")}</span><br><span style="font-size:13px;color:#64748b">{s.get("route", "")}</span>'
            status_badge = f'<span class="lg-badge {s.get("statusTone", "gray")} sm">{s.get("status", "")}</span>'
            next_action = f'<b style="font-size:13.5px">{s.get("nextAction", "—")}</b>'
            sale_sp = f'<span style="font-size:13px">Sale: <b>{s.get("sale", "")}</b></span><br><span style="font-size:13px">SP: <b>{s.get("support", "")}</b></span>'
            next_route = s.get("nextRoute", f"/lo-hang-detail?id={s['id']}")
            action_html = f'<div style="display:flex;gap:6px"><a class="lg-btn primary sm" href="?p={next_route}" target="_self">XỬ LÝ</a><a class="lg-btn ghost sm" href="?p=/lo-hang-detail&id={s["id"]}" target="_self">{icons.eye(15, "#0f2a4a")} 360°</a></div>'
            rows.append([id_link, f'<b>{s.get("customerShort", "")}</b>', contract_route, status_badge, next_action, sale_sp, action_html])
        _render_table(["Mã lô", "Khách hàng", "Hợp đồng · Tuyến", "Trạng thái", "Việc tiếp theo", "Sale · Support", "Hành động"], rows, min_width="1080px")
    else:
        empty_html = """
<div class="lg-card" style="text-align:center;padding:48px">
  <p style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Không tìm thấy lô nào</p>
  <p style="font-size:14px;color:#64748b;margin:6px 0 16px">Thử từ khóa khác hoặc tạo lô mới.</p>
  <a class="lg-btn primary" href="?p=/tao-lo-moi" target="_self">＋ Tạo lô mới</a>
</div>
"""
        st.markdown(empty_html, unsafe_allow_html=True)


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
        st.markdown(f'<div class="lg-card" style="text-align:center;padding:48px"><p style="font-size:19px;font-weight:800">Không tìm thấy lô {sid}</p></div>', unsafe_allow_html=True)
        return

    st.markdown('<a class="lg-link" href="?p=/lo-hang" target="_self" style="display:inline-flex;align-items:center;gap:6px;margin-bottom:8px;font-size:14.5px">← Quay lại</a>', unsafe_allow_html=True)

    tab = st.session_state.get("active_tab") or st.query_params.get("tab") or "lay-hang"
    if tab not in [t["id"] for t in SHIPMENT_TABS]:
        tab = "lay-hang"

    missing_count = len(s.get("missingDocs", [])) + len([d for d in s.get("docs", []) if not d.get("ok")])
    missing_badge = f'<span class="lg-badge red"><span class="lg-dot red"></span>Thiếu {missing_count} thông tin</span>' if missing_count else ""
    contract = s.get("contract", "")
    header_html = f"""
<div class="lg-card" style="padding:0;overflow:hidden">
  <div style="height:6px;background:linear-gradient(90deg,#0f2a4a,#1e5aa8,#10b981)"></div>
  <div style="padding:20px 24px">
    <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px">
      <h1 style="font-size:24px;font-weight:800;color:#0f2a4a;margin:0">{s["id"]}</h1>
      <span class="lg-badge {s.get('statusTone', 'gray')}">{s.get('status', '')}</span>
      {missing_badge}
      <span style="margin-left:auto;font-size:12.5px;color:#94a3b8;display:flex;align-items:center;gap:4px">{icons.clock(14, "#94a3b8")} Cập nhật {s.get('updated', '')}</span>
    </div>
    <p style="font-size:15.5px;font-weight:600;margin:6px 0 0">{s.get('customer', '')} <span style="color:#94a3b8;font-weight:400">· MST {s.get('customerMST', '')}</span></p>
    <div class="lg-cols-4" style="margin-top:12px">
      <div><p style="font-size:13.5px;color:#64748b;font-weight:500;margin:0">Tuyến</p><p style="font-size:14.5px;font-weight:600;color:#1e293b;margin:2px 0 0">{s.get('route', '—')}</p></div>
      <div><p style="font-size:13.5px;color:#64748b;font-weight:500;margin:0">Cửa khẩu</p><p style="font-size:14.5px;font-weight:600;color:#1e293b;margin:2px 0 0">{s.get('borderVN', '—')}</p></div>
      <div><p style="font-size:13.5px;color:#64748b;font-weight:500;margin:0">Hợp đồng</p><p style="font-size:14.5px;font-weight:600;margin:2px 0 0"><a class="lg-link" href="?p=/hop-dong-detail&id={contract}" target="_self">{contract}</a></p></div>
      <div><p style="font-size:13.5px;color:#64748b;font-weight:500;margin:0">Sale · Support</p><p style="font-size:14.5px;font-weight:600;color:#1e293b;margin:2px 0 0">{s.get('sale', '')} · {s.get('support', '')}</p></div>
    </div>
  </div>
  <div style="padding:0 20px 20px">
    {ui._next_action_banner_html(s)}
  </div>
  <div class="lg-tabs" id="workspace-tabs">
    {_shipment_tabs_html(s['id'], tab)}
  </div>
</div>
"""
    st.markdown(header_html, unsafe_allow_html=True)

    if s.get("missingDocs") and tab != "chung-tu":
        missing_boxes = "".join(_missing_box_html(s, m) for m in s["missingDocs"])
        missing_html = f"""
<div class="lg-card" style="border:2px solid #fecaca;background:#fff7ed;margin-top:12px">
  <p style="font-size:15px;font-weight:800;color:#991b1b;display:flex;align-items:center;gap:6px;margin:0 0 8px">{icons.circle_alert(18, "#991b1b")} Đang thiếu {len(s['missingDocs'])} thông tin — bấm để bổ sung ngay:</p>
  <div class="lg-cols-2">
    {missing_boxes}
  </div>
</div>
"""
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


def _shipment_tabs_html(s_id, active):
    parts = []
    for t in SHIPMENT_TABS:
        cls = "lg-tab active" if t["id"] == active else "lg-tab"
        parts.append(f'<a class="{cls}" href="?p=/lo-hang-detail&id={s_id}&tab={t["id"]}" target="_self" style="text-decoration:none">{t["label"]}</a>')
    return "".join(parts)


def _missing_box_html(s, m):
    if "tờ khai" in m or "VN" in m:
        target_tab = "nhap"
    elif "Biển số" in m or "giờ lấy" in m or "Packing" in m:
        target_tab = "lay-hang"
    else:
        target_tab = "tai-chinh"
    to = f"/lo-hang-detail?id={s['id']}&tab={target_tab}"
    return f"""
<div class="lg-missing" style="margin-bottom:8px">
  <span class="body">
    <h5>Thiếu {m}</h5>
  </span>
  <a class="btn" href="?p={to}" target="_self">{icons.pen(16, "#fff")} Bổ sung ngay</a>
</div>
"""


def _render_shipment_tab_layhang(s):
    pickup = s.get("pickup", {})
    cargo = s.get("cargo", {})
    export = s.get("exportInfo", {})
    docs = s.get("docs", [])

    factory_html = f"""
<div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:14px">
  <p style="font-size:15px;font-weight:700;margin:0">{pickup.get("factory", "—")}</p>
  <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">{pickup.get("address", "—")}</p>
  <p style="font-size:14px;margin:6px 0 0;display:flex;align-items:center;gap:6px">{icons.phone(15, "#94a3b8")} {pickup.get("contact", "—")} · {pickup.get("phone", "—")}</p>
</div>
"""

    missing_pickup_err = "Thiếu giờ lấy — nhà máy cần báo trước 24h" if not pickup.get("pickupTime") else None
    missing_xe_html = (f'<div class="lg-missing" style="margin-bottom:8px"><span class="body"><h5>Thiếu biển số + tài xế xe TQ</h5><p>Chưa đặt được xe — bổ sung để nhà máy cho hàng lên xe</p></span><a class="btn" href="?p=/lo-hang-detail&id={s["id"]}&tab=lay-hang" target="_self">Nhập xe ngay</a></div>') if not (pickup.get("plate") and pickup.get("driver")) else ''

    left = f"""
<div class="lg-card" style="display:flex;flex-direction:column;gap:16px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;display:flex;align-items:center;gap:8px;margin:0">{icons.map_pin(19, "#1e5aa8")} Nhà máy & lịch lấy hàng</h3>
  {factory_html}
  {_field("Thời gian lấy hàng", required=not pickup.get("pickupTime"), value=pickup.get("pickupTime", ""), placeholder="VD: 10/09/2026 09:00", error=missing_pickup_err, key="fld_pickup_time")}
  {_field("Loại / kích thước xe", value=pickup.get("truckType", ""), key="fld_truck_type")}
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;display:flex;align-items:center;gap:8px;margin:0">{icons.truck(19, "#1e5aa8")} Xe Trung Quốc</h3>
  {missing_xe_html}
  {_field("Biển số xe", required=not pickup.get("plate"), value=pickup.get("plate", ""), placeholder="VD: 粤A·88T36", key="fld_plate")}
  {_field("Tài xế", required=not pickup.get("driver"), value=pickup.get("driver", ""), placeholder="Tên tài xế", key="fld_driver")}
  {_field("SĐT tài xế", value=pickup.get("driverPhone", ""), placeholder="+86…", key="fld_driver_phone")}
  <div class="lg-cols-2">
    {_field("Ngày dự kiến", value=pickup.get("eta", ""), key="fld_eta")}
    {_field("Ngày thực tế", value=pickup.get("ata", ""), placeholder="—", key="fld_ata")}
  </div>
</div>
"""

    cargo_items = [
        ("Số kiện", str(cargo.get("packs", ""))),
        ("Trọng lượng", cargo.get("weight", "")),
        ("CBM", str(cargo.get("cbm", ""))),
        ("Kích thước", cargo.get("dims", "")),
        ("Loại hàng", cargo.get("type", "")),
    ]
    cargo_cells = "".join(
        f'<div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:12px"><p style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#94a3b8;margin:0">{k}</p><p style="font-size:15px;font-weight:700;color:#0f2a4a;margin:2px 0 0">{v}</p></div>'
        for k, v in cargo_items
    )
    cargo_html = '<div class="lg-cols-3">' + cargo_cells + '</div>'
    note_html = (f'<p style="margin-top:10px;font-size:13.5px;background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:12px">📌 Ghi chú: {cargo.get("note", "")}</p>') if cargo.get("note") else ""

    export_state = export.get("state", "—")
    export_tone = "green" if "Đã" in export_state else "amber"
    checklist = "".join(_doc_row(s, d) for d in docs)

    right = f"""
<div style="display:flex;flex-direction:column;gap:16px">
  <div class="lg-card">
    <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;display:flex;align-items:center;gap:8px;margin:0 0 12px">{icons.package(19, "#1e5aa8")} Hàng hóa</h3>
    {cargo_html}
    {note_html}
  </div>
  <div class="lg-card">
    <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Xuất khẩu — {export.get("border", "")}</h3>
    <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">Đơn vị khai</span><span style="font-weight:600">{export.get("declarant", "")}</span></div>
    <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">Ngày dự kiến / thực tế</span><span style="font-weight:600">{export.get("eta", "")} / {export.get("ata", "chưa có")}</span></div>
    <div style="display:flex;justify-content:space-between;padding:8px 0"><span style="font-size:13.5px;color:#64748b">Trạng thái</span><span class="lg-badge {export_tone} sm">{export_state}</span></div>
  </div>
  <div class="lg-card">
    <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 4px">Checklist chứng từ xuất khẩu</h3>
    <p style="font-size:13px;color:#64748b;margin:0 0 12px">Hiện trạng → thiếu gì → bấm để bổ sung. Không có cảnh báo cụt.</p>
    <div style="display:flex;flex-direction:column;gap:8px">{checklist}</div>
  </div>
</div>
"""

    st.markdown(f'<div class="lg-2col" style="margin-top:16px">{left}{right}</div>', unsafe_allow_html=True)


def _doc_row(s, d):
    if d.get("ok"):
        return f"""
<div style="display:flex;align-items:center;gap:12px;border:2px solid #bbf7d0;background:#f0fdf4;border-radius:12px;padding:12px">
  <span style="width:32px;height:32px;border-radius:999px;background:#10b981;color:#fff;display:grid;place-items:center;font-weight:800">✓</span>
  <div style="flex:1"><p style="font-size:14.5px;font-weight:700;margin:0">{d["name"]} — <span style="color:#047857">✅ Đủ</span></p><p style="font-size:13px;color:#475569;margin:2px 0 0">{d.get("note", "")}</p></div>
</div>
"""
    return f"""
<div style="display:flex;align-items:center;gap:12px;border:2px solid #fcd34d;background:#fffbeb;border-radius:12px;padding:12px">
  <span style="width:32px;height:32px;border-radius:999px;background:#f59e0b;color:#fff;display:grid;place-items:center;font-weight:800">!</span>
  <div style="flex:1"><p style="font-size:14.5px;font-weight:700;margin:0">{d["name"]} — <span style="color:#b45309">Thiếu</span></p><p style="font-size:13px;color:#475569;margin:2px 0 0">{d.get("note", "")}</p></div>
  <a class="lg-btn" style="background:#f59e0b;color:#fff;min-height:44px;padding:8px 14px" href="?p=/lo-hang-detail&id={s['id']}&tab=chung-tu" target="_self">Bổ sung</a>
</div>
"""


def _render_shipment_tab_nhap(s):
    info = s.get("importInfo", {})

    if not info.get("declarationNo"):
        missing_left = f'<div class="lg-missing" style="margin-bottom:12px"><span class="body"><h5>Thiếu số tờ khai nhập khẩu</h5><p>Hàng đang chờ ở bãi VN — có số TK mới nộp thuế & phân luồng được</p></span><a class="btn" href="?p=/lo-hang-detail&id={s["id"]}&tab=nhap" target="_self">Nhập số TK</a></div>'
    else:
        missing_left = ""

    success_banner = (f'<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:12px;font-size:13.5px;color:#1e3a8a">✅ Đã có số TK <b>{info.get("declarationNo", "")}</b>. Tiếp theo: nộp thuế rồi bấm "Thông quan" khi có kết quả phân luồng.</div>') if info.get("declarationNo") else ""

    left = f"""
<div class="lg-card" style="display:flex;flex-direction:column;gap:16px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0">Tờ khai & thuế nhập khẩu — {info.get("borderVN", "")}</h3>
  {missing_left}
  <div class="lg-cols-2">
    {_field("Số tờ khai", required=not info.get("declarationNo"), value=info.get("declarationNo", ""), placeholder="12 số tờ khai…", error="Nhập 12 số tờ khai — VD: 105588421330" if not info.get("declarationNo") else None, key="fld_tk")}
    {_field("Ngày đăng ký", value=info.get("regDate", ""), placeholder="VD: 09/09/2026", key="fld_regdate")}
    {_field("Thuế nhập khẩu (VND)", value=str(info.get("tax", "") or ""), placeholder="VD: 48200000", key="fld_tax")}
    {_field("VAT hàng nhập (VND)", value=str(info.get("vat", "") or ""), placeholder="VD: 96400000", key="fld_vat")}
    {_field("Phân luồng / kiểm hóa", value=info.get("inspection", ""), key="fld_insp")}
    {_field("Giấy phép chuyên ngành", value=info.get("license", ""), key="fld_license")}
  </div>
  {success_banner}
</div>
"""

    if not info.get("delivered") and (not info.get("driverVN") or not info.get("plateVN")):
        missing_right = f'<div class="lg-missing" style="margin-bottom:12px"><span class="body"><h5>Thiếu xe VN + tài xế</h5><p>Chưa đặt xe — đặt trước giờ giao ít nhất 4 tiếng</p></span><a class="btn" href="?p=/lo-hang-detail&id={s["id"]}&tab=nhap" target="_self">Đặt xe ngay</a></div>'
    else:
        missing_right = ""

    if info.get("delivered"):
        delivered_block = f"""
<div style="background:#ecfdf5;border:2px solid #bbf7d0;border-radius:12px;padding:16px;text-align:center">
  <p style="font-size:17px;font-weight:800;color:#065f46;margin:0">✅ ĐÃ GIAO HÀNG XONG</p>
  <p style="font-size:13.5px;color:#047857;margin:2px 0 0">{info.get("actualDelivery", "")} · Sang tab Chứng từ để xuất PXK →</p>
  <a class="lg-btn success" style="margin-top:10px" href="?p=/lo-hang-detail&id={s['id']}&tab=chung-tu" target="_self">SANG XUẤT PHIẾU XUẤT KHO →</a>
</div>
"""
    else:
        delivered_block = ""

    actual_html = (f'<p style="font-size:14px;color:#047857;font-weight:700;margin:4px 0 0">✅ Đã giao: {info.get("actualDelivery", "")}</p>') if info.get("actualDelivery") else ""

    right = f"""
<div class="lg-card" style="display:flex;flex-direction:column;gap:16px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;display:flex;align-items:center;gap:8px;margin:0">{icons.truck(19, "#1e5aa8")} Xe Việt Nam & giao hàng</h3>
  {missing_right}
  <div class="lg-cols-2">
    {_field("Loại xe VN", value=info.get("truckVN", ""), key="fld_truckvn")}
    {_field("Biển số VN", value=info.get("plateVN", ""), placeholder="VD: 29H-481.36", key="fld_platevn")}
    {_field("Tài xế VN", value=info.get("driverVN", ""), placeholder="Tên tài xế", key="fld_drivervn")}
    {_field("Lịch giao", value=info.get("schedule", ""), key="fld_schedule")}
  </div>
  <div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:14px">
    <p style="font-size:12.5px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#94a3b8;margin:0">Địa chỉ giao</p>
    <p style="font-size:15px;font-weight:700;margin:2px 0 0">{info.get("deliveryAddr", "")}</p>
    <p style="font-size:14px;color:#475569;margin:4px 0 0">Người nhận: <b>{info.get("receiver", "")}</b> · {info.get("receiverPhone", "")}</p>
    {actual_html}
  </div>
  {delivered_block}
</div>
"""

    st.markdown(f'<div class="lg-2col" style="margin-top:16px">{left}{right}</div>', unsafe_allow_html=True)

    if not info.get("delivered"):
        if st.button("✅ XÁC NHẬN ĐÃ GIAO HÀNG", key=f"btn_confirm_del_{s['id']}", type="primary", use_container_width=True):
            info["delivered"] = True
            info["actualDelivery"] = "09/09/2026 14:00"
            s["status"] = "Đã giao"
            s["statusTone"] = "green"
            s["timeline"].append({
                "time": "09/09 14:00",
                "title": "Đã giao hàng xong",
                "desc": f"Đã giao đến {info.get('deliveryAddr', 'kho khách')} · Người nhận ký biên bản",
                "tone": "green",
            })
            store.push_toast(f"Đã xác nhận giao hàng cho lô {s['id']}", "Cập nhật thành công vào dòng thời gian", "green")
            st.rerun()


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
        f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">{c["label"]}</span><span style="font-weight:700;font-size:16px">{fmt_m(c["amount"], c.get("ccy", "VND"))} <span style="font-size:12px;font-weight:700;color:#7c3aed">{c.get("ccy", "VND")}</span></span></div>'
        for c in quote
    )
    actual_rows = "".join(
        f'<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">{c["label"]}</span><span style="font-weight:700;font-size:16px">{fmt_m(c["amount"], c.get("ccy", "VND"))} <span style="font-size:12px;font-weight:700;color:#047857">{c.get("ccy", "VND")}</span></span></div>'
        for c in actual
    )

    quote_block = f"""
<div class="lg-card" style="border:2px dashed #c4b5fd;background:#faf5ff">
  <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;color:#5b21b6;background:#ede9fe;display:inline-block;padding:2px 8px;border-radius:6px">Báo giá / Dự kiến — chưa phải số thực thu/chi</span>
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:8px 0 12px">Chi phí dự kiến theo báo giá</h3>
  {quote_rows or '<p style="font-size:14px;color:#64748b">Chưa gắn báo giá. <a class="lg-link" href="?p=/kinh-doanh-bao-gia" target="_self">Mở báo giá →</a></p>'}
  <p style="font-size:12.5px;color:#94a3b8;margin:8px 0 0">Mỗi đồng tiền ghi rõ VND / USD / CNY — không gộp chung.</p>
</div>
"""

    actual_block = f"""
<div class="lg-card" style="border:2px solid #bbf7d0;background:#f0fdf4">
  <span style="font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;color:#047857;background:#d1fae5;display:inline-block;padding:2px 8px;border-radius:6px">Thực tế — đã phát sinh, có chứng từ</span>
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:8px 0 12px">Chi phí thực tế</h3>
  {actual_rows or '<p style="font-size:14px;color:#64748b">Chưa phát sinh chi phí thực tế.</p>'}
</div>
"""

    st.markdown(f'<div class="lg-cols-2" style="margin-top:16px">{quote_block}{actual_block}</div>', unsafe_allow_html=True)

    recv_m = recv / 1e6
    received_m = received / 1e6
    rec_due_m = (recv - received) / 1e6
    payable_m = payable / 1e6
    paid_m = paid / 1e6
    pay_due_m = (payable - paid) / 1e6

    receivable_block = f"""
<div class="lg-card">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;display:flex;align-items:center;gap:8px;margin:0 0 8px">{icons.wallet(19, "#059669")} Phải thu khách hàng (VND)</h3>
  <div class="lg-cols-3" style="text-align:center">
    <div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:12px"><p style="font-size:12px;color:#64748b;font-weight:600;margin:0">Phải thu</p><p style="font-size:17px;font-weight:800;margin:4px 0 0">{recv_m:.1f} tr</p></div>
    <div style="background:#ecfdf5;border:1px solid #bbf7d0;border-radius:12px;padding:12px"><p style="font-size:12px;color:#047857;font-weight:600;margin:0">Đã thu</p><p style="font-size:17px;font-weight:800;color:#047857;margin:4px 0 0">{received_m:.1f} tr</p></div>
    <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:12px"><p style="font-size:12px;color:#dc2626;font-weight:600;margin:0">Còn phải thu</p><p style="font-size:17px;font-weight:800;color:#b91c1c;margin:4px 0 0">{rec_due_m:.1f} tr</p></div>
  </div>
  <a class="lg-btn success full" style="margin-top:12px" href="?action=pay_dialog&sid={s['id']}" target="_self">＋ GHI NHẬN THANH TOÁN</a>
</div>
"""

    payable_block = f"""
<div class="lg-card">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 8px">Phải trả đối tác (VND)</h3>
  <div class="lg-cols-3" style="text-align:center">
    <div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:12px"><p style="font-size:12px;color:#64748b;font-weight:600;margin:0">Phải trả</p><p style="font-size:17px;font-weight:800;margin:4px 0 0">{payable_m:.1f} tr</p></div>
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:12px"><p style="font-size:12px;color:#1e40af;font-weight:600;margin:0">Đã trả</p><p style="font-size:17px;font-weight:800;color:#1e40af;margin:4px 0 0">{paid_m:.1f} tr</p></div>
    <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:12px"><p style="font-size:12px;color:#b45309;font-weight:600;margin:0">Còn phải trả</p><p style="font-size:17px;font-weight:800;color:#b45309;margin:4px 0 0">{pay_due_m:.1f} tr</p></div>
  </div>
  <a class="lg-btn ghost full" style="margin-top:12px" href="?p=/tai-chinh/doi-soat" target="_self">MỞ ĐỐI SOÁT</a>
</div>
"""

    st.markdown(f'<div class="lg-cols-2" style="margin-top:16px">{receivable_block}{payable_block}</div>', unsafe_allow_html=True)

    pay_rows = ""
    for p in payments:
        note_p = (" · " + p["note"]) if p.get("note") else ""
        pay_rows += f"""
<div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px;border:1px solid #e4e9f1;border-radius:12px;padding:12px">
  <span style="font-size:12.5px;font-weight:700;color:#94a3b8;min-width:92px">{p.get("date", "")}</span>
  <span style="flex:1;min-width:160px"><span style="display:block;font-weight:700;font-size:14.5px">{p.get("kind", "")}</span><span style="display:block;font-size:12.5px;color:#64748b">{p.get("by", "")}{note_p}</span></span>
  <span style="font-weight:800;font-size:15.5px">{fmt_m(p.get("amount", 0), p.get("ccy", "VND"))} <span style="font-size:11.5px;color:#94a3b8">{p.get("ccy", "VND")}</span></span>
  <a href="?action=pay_dialog&sid={s['id']}" target="_self" style="height:40px;padding:0 12px;border:1px solid #e4e9f1;border-radius:10px;background:#fff;font-size:13px;font-weight:700;color:#1e5aa8;text-decoration:none;display:inline-flex;align-items:center">Điều chỉnh</a>
</div>
"""

    history_html = f"""
<div class="lg-card" style="margin-top:16px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Lịch sử thu / chi — sửa bằng điều chỉnh, không xóa</h3>
  <div style="display:flex;flex-direction:column;gap:8px">{pay_rows or '<p style="font-size:14px;color:#64748b">Chưa ghi nhận khoản nào.</p>'}</div>
</div>
"""
    st.markdown(history_html, unsafe_allow_html=True)


def _render_shipment_tab_chungtu(s):
    s_id = s["id"]
    linked = store.find_contract(s.get("contract", ""))
    info = s.get("importInfo", {})
    pxk = s.get("pxk", {})

    if not info.get("delivered"):
        missing = f'<div class="lg-missing" style="margin:0 0 12px"><span class="body"><h5>Thiếu xác nhận đã giao hàng</h5><p>Phải giao xong mới được xuất PXK</p></span><a class="btn" href="?p=/lo-hang-detail&id={s_id}&tab=nhap" target="_self">Sang xác nhận giao</a></div>'
    else:
        missing = ""

    if linked:
        contract_html = f"""
<div class="lg-card" style="border:2px solid #e4e9f1">
  <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px">
    <span style="font-size:17px;font-weight:800;color:#0f2a4a">{linked["id"]}</span>
    <span class="lg-badge {linked.get('statusTone', 'gray')} sm">{linked.get('status', '')}</span>
  </div>
  <p style="font-size:14px;color:#475569;margin:6px 0 0">{linked.get('companyLegal', '')} · Giá trị {design.fmt_vnd(linked.get('value', 0))}</p>
  <div class="lg-cols-2" style="margin-top:12px">
    <a class="lg-btn ghost" href="?p=/hop-dong-detail&id={linked['id']}" target="_self">{icons.eye(16, "#0f2a4a")} MỞ HỢP ĐỒNG</a>
    <a class="lg-btn primary" href="?p=/hop-dong-detail&id={linked['id']}&tab=hang-hoa" target="_self">{icons.download(16, "#fff")} TẢI HỢP ĐỒNG</a>
  </div>
</div>
"""
    else:
        contract_html = '<p style="font-size:14px;color:#64748b">Lô chưa gắn hợp đồng. <a class="lg-link" href="?p=/hop-dong" target="_self">Chọn hợp đồng →</a></p>'

    docs_html = ""
    for d in s.get("docs", []):
        if d.get("ok"):
            docs_html += f"""
<div style="display:flex;align-items:center;gap:10px;border:1px solid #e4e9f1;border-radius:12px;padding:10px">
  <span style="width:28px;height:28px;border-radius:999px;background:#10b981;color:#fff;display:grid;place-items:center;font-weight:800;font-size:13px">✓</span>
  <span style="flex:1;font-weight:600;font-size:14px">{d["name"]}</span>
  <span class="lg-badge green sm">{icons.download(14, "#047857")} Có sẵn</span>
</div>
"""
        else:
            docs_html += f"""
<div style="display:flex;align-items:center;gap:10px;border:1px solid #e4e9f1;border-radius:12px;padding:10px">
  <span style="width:28px;height:28px;border-radius:999px;background:#f59e0b;color:#fff;display:grid;place-items:center;font-weight:800;font-size:13px">!</span>
  <span style="flex:1;font-weight:600;font-size:14px">{d["name"]}</span>
  <a class="lg-btn sm" style="background:#f59e0b;color:#fff" href="?p=/lo-hang-detail&id={s_id}&tab=lay-hang" target="_self">＋ Bổ sung</a>
</div>
"""

    left = f"""
<div class="lg-card">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;display:flex;align-items:center;gap:8px;margin:0 0 12px">{icons.file_text(19, "#1e5aa8")} Hợp đồng liên kết</h3>
  {contract_html}
  <div style="margin-top:16px">
    <h4 style="font-size:14.5px;font-weight:700;margin:0 0 8px">Chứng từ lô hàng — bấm để tải / bổ sung</h4>
    <div style="display:flex;flex-direction:column;gap:8px">{docs_html}</div>
  </div>
</div>
"""

    delivered_label = ("✅ Rồi — " + info.get("actualDelivery", "")) if info.get("delivered") else "❌ Chưa"
    delivered_color = "#047857" if info.get("delivered") else "#dc2626"
    src_default = pxk.get("source") or s.get("contract", "")

    if pxk.get("done"):
        pxk_action_html = f"""
<div style="margin-top:12px;background:#ecfdf5;border:2px solid #bbf7d0;border-radius:12px;padding:16px;text-align:center">
  <p style="font-weight:800;color:#065f46;margin:0">✅ ĐÃ XUẤT {pxk.get("number", "")}</p>
  <p style="font-size:13px;color:#047857;margin:4px 0 0">Ngày xuất: {pxk.get("date", "09/09/2026")} · Người nhận: {pxk.get("receiver", "")}</p>
</div>
"""
    else:
        pxk_action_html = ""

    right = f"""
<div class="lg-card" style="border:2px solid #0f2a4a">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 4px">Phiếu xuất kho (PXK) — theo từng lô</h3>
  <p style="font-size:13px;color:#64748b;margin:0 0 12px">PXK gắn với lô đã giao, nguồn từ {src_default}. Mỗi lô 1 PXK riêng.</p>
  {missing}
  <div class="lg-cols-2">
    {_field("Số PXK", value=pxk.get("number", ""), placeholder="Tự sinh khi xuất", key="fld_pxk_no")}
    {_field("Ngày PXK", value=pxk.get("date", "") or "09/09/2026", key="fld_pxk_date")}
    {_field("Địa điểm nhận", value=pxk.get("place", "") or info.get("deliveryAddr", ""), key="fld_pxk_place")}
    {_field("Người nhận", value=pxk.get("receiver", "") or info.get("receiver", ""), key="fld_pxk_receiver")}
    {_field("Chức vụ người nhận", value=pxk.get("role", "") or "Thủ kho", key="fld_pxk_role")}
    {_field("Nguồn (HDMB/PL)", value=pxk.get("source", "") or s.get("contract", ""), key="fld_pxk_source")}
  </div>
  <div style="margin-top:12px;background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:12px;font-size:13.5px">
    <p style="margin:0">Đã giao hàng xong: <b style="color:{delivered_color}">{delivered_label}</b></p>
    <p style="margin:4px 0 0">Ngày giao: <b>{info.get("actualDelivery") or info.get("schedule") or "—"}</b></p>
  </div>
  {pxk_action_html}
</div>
"""

    st.markdown(f'<div class="lg-2col" style="margin-top:16px">{left}{right}</div>', unsafe_allow_html=True)

    if not pxk.get("done") and info.get("delivered"):
        if st.button("🖨 XUẤT PHIẾU XUẤT KHO", key=f"btn_export_pxk_{s_id}", type="primary", use_container_width=True):
            pxk["done"] = True
            pxk["number"] = f"PXK-2026-{s_id.replace('LO-', '')}"
            pxk["date"] = "09/09/2026"
            pxk["receiver"] = info.get("receiver", "Phạm Minh Đức")
            pxk["place"] = info.get("deliveryAddr", "Kho khách hàng")
            s["timeline"].append({
                "time": "09/09 14:15",
                "title": f"Đã xuất {pxk['number']}",
                "desc": f"Xuất kho cho {info.get('receiver', 'khách hàng')} tại {pxk['place']}",
                "tone": "green",
            })
            store.push_toast(f"Đã xuất {pxk['number']}", "Phiếu xuất kho đã được lưu vào hồ sơ chứng từ", "green")
            st.rerun()


def _render_shipment_tab_history(s):
    timeline = s.get("timeline", [])
    rows = ""
    for t in timeline:
        tone = t.get("tone", "blue")
        dot_color = {"green": "#10b981", "amber": "#f59e0b", "red": "#dc2626", "blue": "#2563eb"}.get(tone, "#2563eb")
        desc = (f'<p style="font-size:13.5px;color:#475569;margin:2px 0 0">{t.get("desc", "")}</p>') if t.get("desc") else ""
        rows += f"""
<div style="position:relative;padding:0 0 16px 24px">
  <span style="position:absolute;left:-4px;top:4px;width:18px;height:18px;border-radius:999px;background:{dot_color};border:3px solid #fff;box-shadow:0 0 0 1px #cbd5e1"></span>
  <p style="font-size:12.5px;font-weight:700;color:#94a3b8;margin:0">{t.get("time", "")}</p>
  <p style="font-size:15px;font-weight:700;color:#0f2a4a;margin:2px 0 0">{t.get("title", "")}</p>
  {desc}
</div>
"""

    history_html = f"""
<div class="lg-card" style="margin-top:16px;max-width:800px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 16px">Dòng thời gian — {s["id"]}</h3>
  <div style="position:relative;padding-left:14px;border-left:2px solid #cbd5e1">{rows or '<p style="font-size:14px;color:#64748b">Chưa có sự kiện nào.</p>'}</div>
</div>
"""
    st.markdown(history_html, unsafe_allow_html=True)


def _field(label, required=False, value="", placeholder="", error=None, key=None):
    star = '<span style="color:#dc2626">*</span>' if required else ""
    error_html = ('<p class="lg-field-error">⚠ ' + error + '</p>') if error else ""
    missing_cls = " missing" if (required and not value) else ""
    return f"""
<div class="lg-field">
  <label class="lg-field-label">{label} {star}</label>
  <input class="lg-input{missing_cls}" placeholder="{placeholder}" value="{value}" />
  {error_html}
</div>
"""


def render_customers():
    customers = list(store.get_customers().values())
    q = st.text_input("", placeholder="Tìm tên công ty, MST, liên hệ…", key="cust_q", label_visibility="collapsed")
    filtered = [c for c in customers if not q or q.lower() in (c["name"] + c["mst"] + c.get("contact", "")).lower()]

    header_html = f"""
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{icons.users(20, "#fff")}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Khách Hàng</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Hiện trạng công nợ → hành động: tạo báo giá, tạo lô, xem hợp đồng</p>
      </div>
    </div>
  </div>
</div>
"""
    st.markdown(header_html, unsafe_allow_html=True)

    if filtered:
        rows = []
        for c in filtered:
            if c.get("debt"):
                debt_html = f'<span style="font-weight:800;color:#b91c1c">{design.fmt_vnd(c["debt"])}</span>'
            else:
                debt_html = '<span style="font-weight:700;color:#047857">Hết nợ ✓</span>'
            action_html = '<div style="display:flex;gap:6px;flex-wrap:wrap"><a class="lg-btn primary sm" href="?p=/kinh-doanh-bao-gia" target="_self">＋ Báo giá</a><a class="lg-btn ghost sm" href="?p=/tao-lo-moi" target="_self">＋ Lô</a><a class="lg-btn ghost sm" href="?p=/hop-dong" target="_self">Hợp đồng</a></div>'
            rows.append([
                f'<b>{c["name"]}</b>',
                f'<span style="font-weight:600">{c["mst"]}</span><br><span style="font-size:13px;color:#64748b">{c.get("contact", "")}</span>',
                c.get("sale", ""),
                f'<b style="text-align:center;display:block">{c.get("lots", 0)}</b>',
                debt_html,
                f'<span style="font-size:13px;color:#64748b">{c.get("updated", "")}</span>',
                action_html,
            ])
        _render_table(["Khách hàng", "MST · Liên hệ", "Sale", "Số lô", "Công nợ", "Cập nhật", "Hành động"], rows, min_width="960px")


def render_quotes():
    quotes = store.get_quotes()
    top_html = f"""
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{icons.calculator(20, "#fff")}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Kinh Doanh & Báo Giá</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Lập dự toán → gửi khách → khách chốt → tạo thỏa thuận. Mọi số đều ghi rõ BÁO GIÁ / DỰ KIẾN.</p>
      </div>
    </div>
    <a class="lg-btn primary" href="?action=open_quick_add" target="_self">＋ Tạo báo giá</a>
  </div>
  <div class="lg-cols-4">
"""
    st.markdown(top_html, unsafe_allow_html=True)

    stTone = {"ACCEPTED": ("ĐÃ CHỐT", "green"), "SENT": ("ĐÃ GỬI", "blue"), "REJECTED": ("TỪ CHỐI", "red"), "DRAFT": ("NHÁP", "gray")}
    cards = ""
    for q in quotes:
        lbl, tone = stTone.get(q["status"], (q["status"], "gray"))
        price_html = (f"{q['price'] / 1e6:.1f}tr") if q.get("price") else "—"
        cost_html = (f"{q['cost'] / 1e6:.1f}tr") if q.get("cost") else "—"
        if q["status"] == "DRAFT":
            action_html = f'<a class="lg-btn primary sm full" href="?p=/kinh-doanh-bao-gia" target="_self">GỬI KHÁCH</a>'
        elif q["status"] == "SENT":
            action_html = f'<a class="lg-btn success sm full" href="?p=/thoa-thuan-ban-giao" target="_self">KHÁCH ĐÃ CHỐT</a>'
        elif q["status"] == "ACCEPTED":
            action_html = '<a class="lg-btn success sm full" href="?p=/thoa-thuan-ban-giao" target="_self">Lập thỏa thuận</a>'
        else:
            action_html = ""
        cards += f"""
<div style="border:2px solid #e4e9f1;border-radius:16px;padding:16px">
  <div style="display:flex;align-items:center;gap:6px"><span style="font-size:15px;font-weight:800;color:#0f2a4a">{q["id"]}</span><span class="lg-badge {tone} sm">{lbl}</span></div>
  <p style="font-size:14px;font-weight:600;margin:4px 0 0">{q["customer"]}</p>
  <p style="font-size:12.5px;color:#64748b;margin:2px 0 0">{q["route"]} · {q.get("goods", "")}</p>
  <div class="lg-cols-3" style="text-align:center;font-size:12px;margin-top:10px">
    <div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:8px;padding:6px"><p style="color:#64748b;margin:0">Chi phí</p><b>{cost_html}</b></div>
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:6px"><p style="color:#64748b;margin:0">Giá bán</p><b>{price_html}</b></div>
    <div style="background:#ecfdf5;border:1px solid #bbf7d0;border-radius:8px;padding:6px"><p style="color:#64748b;margin:0">Margin</p><b style="color:#047857">{q.get("margin", "—")}</b></div>
  </div>
  <div class="lg-cols-2" style="margin-top:10px">{action_html}<a class="lg-btn ghost sm" href="?p=/kinh-doanh-bao-gia" target="_self">Chi tiết</a></div>
</div>
"""

    st.markdown(cards, unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_agreements():
    ags = store.get_agreements()
    steps = ["1 · Báo giá", "2 · Khách chốt", "3 · Thỏa thuận", "4 · Bàn giao Support"]
    steps_html = '<div style="border-radius:16px;background:#fff;border:1px solid #e4e9f1;padding:16px;display:flex;align-items:center;gap:6px;overflow-x:auto">'
    for i, s in enumerate(steps):
        if i < 3:
            steps_html += f'<span style="background:#10b981;color:#fff;border-radius:12px;padding:10px 14px;font-size:13.5px;font-weight:800;white-space:nowrap">✓ {s}</span><span style="color:#cbd5e1">→</span>'
        else:
            steps_html += f'<span style="background:#f1f5f9;color:#64748b;border-radius:12px;padding:10px 14px;font-size:13.5px;font-weight:800;white-space:nowrap">{s}</span>'
    steps_html += '</div>'

    header_html = f"""
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{icons.handshake(20, "#fff")}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Thỏa Thuận & Bàn Giao</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Báo giá chốt → thỏa thuận điều khoản → bàn giao Support kèm bằng chứng</p>
      </div>
    </div>
  </div>
  {steps_html}
</div>
"""
    st.markdown(header_html, unsafe_allow_html=True)

    toneMap = {"AGREED": "green", "REVIEWING": "amber", "VOID": "red"}
    cards = ""
    for a in ags:
        tone = toneMap.get(a["status"], "blue")
        cards += f"""
<div class="lg-card" style="margin-bottom:12px">
  <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px">
    <span style="font-size:16px;font-weight:800;color:#0f2a4a">{a["id"]}</span>
    <span class="lg-badge {tone} sm">{a["status"]}</span>
    <span style="font-size:13px;color:#64748b">Báo giá {a.get("quote", "")} · {a.get("customer", "")}</span>
  </div>
  <div class="lg-cols-2" style="margin-top:10px;font-size:14px">
    <p style="margin:0"><span style="color:#64748b">Incoterm:</span> <b>{a.get("incoterm", "")}</b></p>
    <p style="margin:0"><span style="color:#64748b">Thanh toán:</span> <b>{a.get("payment", "")}</b></p>
    <p style="margin:0;grid-column:1 / -1"><span style="color:#64748b">Phạm vi:</span> {a.get("scope", "")}</p>
    <p style="margin:0;grid-column:1 / -1"><span style="color:#64748b">Bàn giao:</span> <b>{a.get("handover", "")}</b></p>
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px">
    <a class="lg-btn primary" href="?p=/hop-dong/moi" target="_self">Lập hợp đồng →</a>
  </div>
</div>
"""
    st.markdown(cards, unsafe_allow_html=True)


def render_partner_context():
    header_html = f"""
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{icons.building(20, "#fff")}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Ngữ Cảnh Đối Tác</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Đại lý & cửa khẩu — ai làm gì, liên hệ ai, số dư ra sao</p>
      </div>
    </div>
  </div>
</div>
"""
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
    <div style="margin-top:12px;background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:12px;font-size:13.5px">Số dư phải trả Bằng Tường: <b>73.800.000 ₫</b> + <b>27.700 CNY</b> — <a class="lg-link" href="?p=/tai-chinh/doi-soat" target="_self">Đối soát →</a></div>
  </div>
  <div class="lg-card">
    <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Cửa khẩu & tuyến trọng điểm</h3>
    <div style="display:flex;flex-direction:column;gap:10px">
      <div style="border:1px solid #e4e9f1;border-radius:12px;padding:12px"><p style="font-weight:700;font-size:14.5px;margin:0">Hữu Nghị (TQ↔VN)</p><p style="font-size:13px;color:#64748b;margin:2px 0 0">Cont 40HQ · 6–8 tiếng · LO-0306, 0308 đang đi</p></div>
      <div style="border:1px solid #e4e9f1;border-radius:12px;padding:12px"><p style="font-weight:700;font-size:14.5px;margin:0">Tân Thanh (TQ↔VN)</p><p style="font-size:13px;color:#64748b;margin:2px 0 0">Xe tải · 3–5 tiếng · LO-0307, 0299 đang đi</p></div>
    </div>
  </div>
</div>
"""
    st.markdown(body_html, unsafe_allow_html=True)
