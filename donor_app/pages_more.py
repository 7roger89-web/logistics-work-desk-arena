"""Contracts, Contract detail, New contract pages — all .format() to avoid f-string issues."""
from __future__ import annotations

import streamlit as st

from . import design, icons, store, ui


def render_contracts():
    contracts = store.get_contracts()
    c1, c2 = st.columns([5, 1])
    with c1:
        q = st.text_input("", placeholder="Tìm số hợp đồng · đại lý · công ty · mã lô…", key="ct_q", label_visibility="collapsed")
    with c2:
        type_filter = st.selectbox("", options=["ALL", "HDMB", "HDNT"], key="ct_type", label_visibility="collapsed", format_func=lambda x: "Tất cả" if x == "ALL" else x)

    filtered = [c for c in contracts if (type_filter == "ALL" or c.get("type") == type_filter) and (not q or q.lower() in (c["id"] + c.get("company", "") + c.get("agent", "") + " ".join(l["id"] for l in c.get("linkedLots", []))).lower())]

    header_html = """
<div class="lg-card" style="background:linear-gradient(135deg,#0f2a4a,#1e5aa8);color:#fff;margin-bottom:16px;padding:24px 28px;display:flex;flex-direction:row;align-items:center;gap:16px;flex-wrap:wrap">
  <div style="flex:1">
    <h1 style="font-size:22px;font-weight:800;margin:0">Hợp Đồng — Bàn làm việc chính</h1>
    <p style="color:#bfdbfe;font-size:14.5px;margin:6px 0 0">Tạo & quản lý HDMB / HDNT / Phụ lục tại đây. <b style="color:#fff">Không tạo hợp đồng trong màn hình Lô hàng</b> — lô chỉ gắn hợp đồng có sẵn.</p>
  </div>
  <a class="lg-btn-white" data-to="/hop-dong/moi">➕ TẠO HỢP ĐỒNG MỚI</a>
</div>
"""
    st.markdown(header_html, unsafe_allow_html=True)

    n_html = '<div class="lg-card" style="margin-bottom:16px"><p style="font-size:13.5px;color:#64748b;margin:0">Tìm thấy <b style="color:#0f2a4a">{0} hợp đồng</b> · Mỗi dòng: hiện trạng → việc thiếu → nút mở.</p></div>'.format(len(filtered))
    st.markdown(n_html, unsafe_allow_html=True)

    if filtered:
        rows = []
        for c in filtered:
            type_lbl = c.get("type", "")
            value_html = ('<b>{0}</b>'.format(design.fmt_vnd(c.get("value", 0)))) if c.get("value") else '<span style="color:#b45309">Chưa tính</span>'
            valid_html = ('{0} → {1}'.format(c.get("validFrom", ""), c.get("validTo", ""))) if c.get("validFrom") else '<span style="color:#b45309;font-weight:600">⚠ Thiếu ngày</span>'
            type_bg = "#dbeafe" if type_lbl == "HDMB" else "#d1fae5"
            type_fg = "#1e40af" if type_lbl == "HDMB" else "#047857"
            type_span = '<span style="background:{0};color:{1};font-size:12.5px;font-weight:800;border-radius:6px;padding:2px 8px">{2}</span>'.format(type_bg, type_fg, type_lbl)
            rows.append([
                '<a class="lg-link" data-to="/hop-dong-detail?id={0}" style="font-weight:800">{1}</a>'.format(c["id"], c["id"]),
                type_span,
                '<b>{0}</b><br><span style="font-size:12.5px;color:#64748b">{1}</span>'.format(c.get("company", ""), c.get("agent", "")),
                value_html,
                '<span style="font-size:13px">{0}</span>'.format(valid_html),
                '<b style="text-align:center;display:block">{0}</b>'.format(c.get("lots", 0)),
                '<span class="lg-badge {0} sm">{1}</span>'.format(c.get("statusTone", "gray"), c.get("status", "")),
                '<a class="lg-btn primary sm" data-to="/hop-dong-detail?id={0}">MỞ HỢP ĐỒNG →</a>'.format(c["id"]),
            ])
        ui._install_goto_bridge()
        from .pages_core import _render_table
        _render_table(["Số hợp đồng", "Loại", "Đại lý · Công ty", "Giá trị", "Hiệu lực", "Số lô", "Trạng thái", ""], rows, min_width="1020px")
    else:
        empty_html = """
<div class="lg-card" style="text-align:center;padding:48px;border:2px dashed #cbd5e1">
  <p style="font-weight:700;font-size:16px">Chưa có hợp đồng nào cho Đại lý này.</p>
  <a class="lg-btn primary" data-to="/hop-dong/moi">＋ TẠO HỢP ĐỒNG</a>
</div>
"""
        st.markdown(empty_html, unsafe_allow_html=True)
        ui._install_goto_bridge()


CONTRACT_TABS = [
    {"id": "thong-tin", "label": "Thông tin hợp đồng"},
    {"id": "hang-hoa", "label": "Hàng hóa & Chứng từ"},
    {"id": "lo-lien-ket", "label": "Lô hàng liên kết"},
    {"id": "tai-chinh", "label": "Tài chính hợp đồng"},
    {"id": "lich-su", "label": "Lịch sử / Phụ lục"},
]


def render_contract_detail():
    cid = store.get_shipment_id() or st.query_params.get("id") or "HDMB-PA-2026-031"
    c = store.find_contract(cid)
    if not c:
        st.markdown('<div class="lg-card" style="text-align:center;padding:48px"><p style="font-size:19px;font-weight:800">Không tìm thấy {0}</p></div>'.format(cid), unsafe_allow_html=True)
        return

    tab = st.query_params.get("tab", "hang-hoa")
    if tab not in [t["id"] for t in CONTRACT_TABS]:
        tab = "hang-hoa"

    st.markdown('<a class="lg-link" data-to="/hop-dong" style="display:inline-flex;align-items:center;gap:6px;margin-bottom:8px;font-size:14.5px">← Quay lại danh sách</a>', unsafe_allow_html=True)

    type_lbl = c.get("type", "")
    type_bg = "#dbeafe" if type_lbl == "HDMB" else "#d1fae5"
    type_fg = "#1e40af" if type_lbl == "HDMB" else "#047857"

    header_html = """
<div class="lg-card" style="padding:0;overflow:hidden">
  <div style="height:6px;background:linear-gradient(90deg,#10b981,#1e5aa8,#0f2a4a)"></div>
  <div style="padding:20px 24px">
    <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px">
      <h1 style="font-size:24px;font-weight:800;color:#0f2a4a;margin:0">{cid}</h1>
      <span style="background:{tbg};color:{tfg};font-size:12.5px;font-weight:800;border-radius:6px;padding:4px 8px">{type_lbl}</span>
      <span class="lg-badge {st_tone}">{status}</span>
    </div>
    <p style="font-size:14.5px;color:#475569;margin:6px 0 0">{company} · Đại lý {agent} · {lots} lô liên kết</p>
    <div class="lg-tabs">
      {tabs}
    </div>
  </div>
</div>
""".format(
        cid=c["id"],
        tbg=type_bg,
        tfg=type_fg,
        type_lbl=type_lbl,
        st_tone=c.get("statusTone", "gray"),
        status=c.get("status", ""),
        company=c.get("company", ""),
        agent=c.get("agent", ""),
        lots=c.get("lots", 0),
        tabs=_contract_tabs_html(tab),
    )
    st.markdown(header_html, unsafe_allow_html=True)

    if tab == "thong-tin":
        _render_ctab_info(c)
    elif tab == "hang-hoa":
        _render_ctab_goods(c)
    elif tab == "lo-lien-ket":
        _render_ctab_linked(c)
    elif tab == "tai-chinh":
        _render_ctab_finance(c)
    elif tab == "lich-su":
        _render_ctab_history(c)
    ui._install_goto_bridge()


def _contract_tabs_html(active):
    parts = []
    for t in CONTRACT_TABS:
        cls = "lg-tab active" if t["id"] == active else "lg-tab"
        parts.append('<button class="{0}" data-tab="{1}">{2}</button>'.format(cls, t["id"], t["label"]))
    return "".join(parts)


def _render_ctab_info(c):
    buyer_missing = c.get("missingBuyerInfo", [])
    company = c.get("company", "")
    agent = c.get("agent", "")

    rep_html = ('<b>{0}</b>'.format(c.get("companyRep", ""))) if c.get("companyRep") else '<span style="color:#b45309;font-weight:700">⚠ Thiếu người đại diện</span>'
    role_html = ('<b>{0}</b>'.format(c.get("companyRole", ""))) if c.get("companyRole") else '<span style="color:#b45309;font-weight:700">⚠ Thiếu chức vụ</span>'

    extra_block = ""
    if buyer_missing:
        extra_block = """
<div style="margin-top:12px;background:#fffbeb;border:2px dashed #fbbf24;border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:10px">
  <p style="font-weight:700;color:#92400e;font-size:14.5px;margin:0">✏️ BỔ SUNG THÔNG TIN — thiếu người đại diện & chức vụ</p>
  <div class="lg-cols-2">
    <div class="lg-field"><label class="lg-field-label">Người đại diện bên mua <span style="color:#dc2626">*</span></label><input class="lg-input missing" placeholder="VD: Phạm Minh Đức" /></div>
    <div class="lg-field"><label class="lg-field-label">Chức vụ <span style="color:#dc2626">*</span></label><input class="lg-input missing" placeholder="VD: Giám đốc" /></div>
  </div>
  <button class="lg-btn primary full">💾 LƯU THÔNG TIN BÊN MUA</button>
</div>
"""

    left = """
<div class="lg-card">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Bên mua — {0}</h3>
  <div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:14px;font-size:14.5px;display:flex;flex-direction:column;gap:6px">
    <p style="margin:0"><span style="color:#64748b">Tên pháp lý:</span> <b>{1}</b></p>
    <p style="margin:0"><span style="color:#64748b">Địa chỉ:</span> {2}</p>
    <p style="margin:0"><span style="color:#64748b">MST:</span> <b>{3}</b></p>
    <p style="margin:0"><span style="color:#64748b">Người đại diện:</span> {4}</p>
    <p style="margin:0"><span style="color:#64748b">Chức vụ:</span> {5}</p>
  </div>
  {6}
</div>
""".format(company, c.get("companyLegal", ""), c.get("companyAddr", ""), c.get("companyTax", ""), rep_html, role_html, extra_block)

    right = """
<div class="lg-card">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Bên bán / Đại lý — {0}</h3>
  <div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:14px;font-size:14.5px;display:flex;flex-direction:column;gap:6px">
    <p style="margin:0"><span style="color:#64748b">Tên pháp lý:</span> <b>{1}</b></p>
    <p style="margin:0"><span style="color:#64748b">Địa chỉ:</span> {2}</p>
    <p style="margin:0"><span style="color:#64748b">MST / mã pháp lý:</span> <b>{3}</b></p>
    <p style="margin:0"><span style="color:#64748b">Người đại diện:</span> <b>{4}</b> · {5}</p>
    <p style="margin:0"><span style="color:#64748b">Chủ tài khoản:</span> {6}</p>
    <p style="margin:0"><span style="color:#64748b">Số TK:</span> <b>{7}</b> · {8}</p>
  </div>
  <div style="margin-top:12px;background:#ecfdf5;border:1px solid #bbf7d0;border-radius:12px;padding:12px;font-size:13.5px;color:#064e3b">✅ Thông tin đại lý đầy đủ — không cần bổ sung.</div>
</div>
""".format(agent, c.get("agentLegal", ""), c.get("agentAddr", ""), c.get("agentTax", ""), c.get("agentRep", ""), c.get("agentRole", ""), c.get("bankOwner", ""), c.get("bankNo", ""), c.get("bankName", ""))

    st.markdown('<div class="lg-2col" style="margin-top:16px">{0}{1}</div>'.format(left, right), unsafe_allow_html=True)


def _render_ctab_goods(c):
    goods = c.get("goods", [])
    pre_total = sum(g["qty"] * g["price"] for g in goods)
    vat = round(pre_total * 0.08)
    total = pre_total + vat

    if c.get("type") == "HDNT" or c.get("hdntNo"):
        route = "HDNT+PL"
        route_text = "→ Lập HỢP ĐỒNG NGUYÊN TẮC (HDNT) + PHỤ LỤC (PL)"
        readiness_ok = bool(c.get("hdntNo") and c.get("hdntDate") and c.get("plNo"))
        readiness_label = "Sẵn sàng xuất" if readiness_ok else "Thiếu thông tin HDNT/PL"
    elif total < 50_000_000:
        route = "HDNT+PL"
        route_text = "→ Lập HỢP ĐỒNG NGUYÊN TẮC (HDNT) + PHỤ LỤC (PL)"
        readiness_ok = bool(c.get("hdntNo") and c.get("hdntDate") and c.get("plNo"))
        readiness_label = "Sẵn sàng xuất" if readiness_ok else "Thiếu thông tin HDNT/PL"
    else:
        route = "HDMB"
        route_text = "→ Lập HỢP ĐỒNG MUA BÁN (HDMB)"
        readiness_ok = bool(c.get("hdmbDate"))
        readiness_label = "Sẵn sàng xuất" if readiness_ok else "Thiếu Ngày HDMB"

    bg = "#eff6ff" if route == "HDMB" else "#ecfdf5"
    border = "#bfdbfe" if route == "HDMB" else "#bbf7d0"
    badge_bg = "#10b981" if readiness_ok else "#f59e0b"
    badge_icon = "✓" if readiness_ok else "!"
    banner = """
<div style="margin-top:12px;background:{bg};border:2px solid {border};border-radius:16px;padding:16px;display:flex;flex-direction:row;align-items:center;gap:12px;flex-wrap:wrap">
  <div style="flex:1">
    <p style="font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;opacity:.7;margin:0">Tổng sau VAT: {total_vnd}</p>
    <p style="font-size:21px;font-weight:800;color:#0f2a4a;margin:2px 0 0">{route_text}</p>
    <p style="font-size:13.5px;color:#475569;margin:4px 0 0">Ngưỡng: dưới 50.000.000 ₫ → HDNT + PL · Từ 50.000.000 ₫ trở lên → HDMB.</p>
  </div>
  <span style="background:{bbg};color:#fff;border-radius:999px;padding:8px 16px;font-weight:800;font-size:14.5px;display:inline-flex;align-items:center;gap:6px">{bicon} {blbl}</span>
</div>
""".format(bg=bg, border=border, total_vnd=design.fmt_vnd(total), route_text=route_text, bbg=badge_bg, bicon=badge_icon, blbl=readiness_label)

    goods_rows = ""
    for i, g in enumerate(goods):
        bad = not g["desc"].strip() or not g["qty"] or not g["price"]
        row_class = ' style="background:#fef2f2"' if bad else ""
        desc_invalid = " invalid" if not g["desc"].strip() else ""
        qty_invalid = " invalid" if not g["qty"] else ""
        price_invalid = " invalid" if not g["price"] else ""
        price_value = ('"{0:,.0f}".format(g["price"])').replace(",", ".") if g["price"] else 'placeholder="0"'
        line_total = design.fmt_vnd(round(g["qty"] * g["price"] * 1.08))
        sel = lambda unit: ' selected' if g["unit"] == unit else ''
        unit_options = '<option{0}>Cái</option><option{1}>Máy</option><option{2}>Bộ</option><option{3}>Lô</option><option{4}>Hệ thống</option><option{5}>Kiện</option><option{6}>Kg</option>'.format(sel("Cái"), sel("Máy"), sel("Bộ"), sel("Lô"), sel("Hệ thống"), sel("Kiện"), sel("Kg"))
        trash_icon = icons.trash(17, "#dc2626")
        goods_rows += """
<tr{rc}>
  <td style="font-weight:800;text-align:center">{i}</td>
  <td><input class="lg-input{di}" value="{desc}" /></td>
  <td><select class="lg-input">{uo}</select></td>
  <td><input type="number" class="lg-input{qi}" value="{qty}" /></td>
  <td><input type="number" class="lg-input{pi}" value="{pv}" /></td>
  <td style="text-align:center;font-weight:700;color:#64748b">8%</td>
  <td style="font-weight:800;color:#0f2a4a;white-space:nowrap">{lt}</td>
  <td><button class="lg-btn ghost sm" style="color:#dc2626">{ti}</button></td>
</tr>
""".format(rc=row_class, i=i + 1, di=desc_invalid, desc=g["desc"], uo=unit_options, qi=qty_invalid, qty=g["qty"], pi=price_invalid, pv=price_value, lt=line_total, ti=trash_icon)

    goods_card = """
<div class="lg-card" style="margin-top:16px">
  <div class="lg-section-title">
    <h2 style="font-size:17px;font-weight:800;color:#0f2a4a;margin:0">Hàng hóa — nhập từng dòng, máy tự tính tiền</h2>
    <span style="font-size:13px;color:#64748b">STT · VAT 8% · Thành tiền: tự động, không cần nhập</span>
  </div>
  <div style="overflow-x:auto">
    <table class="lg-tbl" style="min-width:860px">
      <thead><tr><th style="width:52px">STT</th><th>Mô tả hàng hóa *</th><th style="width:110px">Đơn vị</th><th style="width:110px">Số lượng *</th><th style="width:170px">Đơn giá chưa VAT *</th><th style="width:80px">VAT</th><th style="width:160px">Thành tiền</th><th style="width:70px"></th></tr></thead>
      <tbody>{gr}</tbody>
    </table>
  </div>
  <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap">
    <button class="lg-btn ghost" style="flex:1;border-style:dashed;border-color:#1e5aa8;color:#1e5aa8">{0} THÊM DÒNG HÀNG HÓA</button>
    <button class="lg-btn primary" style="flex:1">💾 LƯU HÀNG HÓA</button>
  </div>
  <div class="lg-cols-3" style="margin-top:12px;background:#0f2a4a;color:#fff;padding:16px;border-radius:16px;text-align:center">
    <div><p style="font-size:12px;color:#bfdbfe;font-weight:600;margin:0">Tiền hàng</p><p style="font-size:18px;font-weight:800;margin:2px 0 0">{1}</p></div>
    <div><p style="font-size:12px;color:#bfdbfe;font-weight:600;margin:0">VAT 8%</p><p style="font-size:18px;font-weight:800;margin:2px 0 0">{2}</p></div>
    <div style="background:rgba(255,255,255,.1);border-radius:12px;padding:8px 0"><p style="font-size:12px;color:#fde68a;font-weight:700;margin:0">TỔNG SAU VAT</p><p style="font-size:21px;font-weight:800;color:#fde68a;margin:2px 0 0">{3}</p></div>
  </div>
</div>
""".format(icons.plus(19, "#1e5aa8"), design.fmt_vnd(pre_total), design.fmt_vnd(vat), design.fmt_vnd(total), gr=goods_rows)

    st.markdown(goods_card, unsafe_allow_html=True)
    st.markdown("""
<div class="lg-card" style="border:2px solid #0f2a4a;margin-top:16px">
  <h3 style="font-size:17px;font-weight:800;color:#0f2a4a;margin:0">✅ PHƯƠNG ÁN CHỨNG TỪ <span style="font-size:13px;font-weight:500;color:#64748b">(tự chọn theo tổng sau VAT — đúng 50 tr thuộc HDMB)</span></h3>
  {0}
  {1}
  <button class="lg-btn success full" style="margin-top:16px;font-size:16.5px;min-height:56px">🖨 XUẤT CHỨNG TỪ SẴN SÀNG</button>
</div>
""".format(banner, _render_route_form(c, route)), unsafe_allow_html=True)


def _render_route_form(c, route):
    if route == "HDNT+PL":
        if c.get("reusableHdnt"):
            reusable = """
<div style="background:#ecfdf5;border:1px solid #bbf7d0;border-radius:12px;padding:12px;margin-bottom:12px">
  <p style="font-weight:700;font-size:14px;color:#064e3b;margin:0">✔ CÓ THỂ TÁI SỬ DỤNG HDNT {0} (còn hiệu lực tới {1})</p>
  <div class="lg-cols-2" style="margin-top:8px">
    <button class="lg-btn success">Tái sử dụng</button>
    <button class="lg-btn ghost">Lập HDNT mới</button>
  </div>
</div>
""".format(c.get("hdntNo", ""), c.get("hdntTo", ""))
        else:
            reusable = ""

        hdnt_block = """
<div class="lg-card" style="margin-top:12px">
  <h4 style="font-weight:800;font-size:15px;margin:0 0 12px">Hợp đồng nguyên tắc (HDNT)</h4>
  {0}
  <div class="lg-cols-2">
    <div class="lg-field"><label class="lg-field-label">Số HDNT <span style="color:#dc2626">*</span></label><input class="lg-input" value="{1}" placeholder="VD: HDNT-PA-2026-119" /></div>
    <div class="lg-field"><label class="lg-field-label">Ngày ký <span style="color:#dc2626">*</span></label><input class="lg-input" value="{2}" placeholder="VD: 09/09/2026" /></div>
    <div class="lg-field"><label class="lg-field-label">Hiệu lực từ</label><input class="lg-input" value="{3}" /></div>
    <div class="lg-field"><label class="lg-field-label">Hiệu lực đến</label><input class="lg-input" value="{4}" /></div>
  </div>
</div>
""".format(reusable, c.get("hdntNo", ""), c.get("hdntDate", ""), c.get("hdntFrom", ""), c.get("hdntTo", ""))

        pl_block = """
<div class="lg-card" style="margin-top:12px">
  <h4 style="font-weight:800;font-size:15px;margin:0 0 12px">Phụ lục (PL) — HDNT cha: {0}</h4>
  <div class="lg-cols-2">
    <div class="lg-field"><label class="lg-field-label">Số PL <span style="color:#dc2626">*</span></label><input class="lg-input" value="{1}" placeholder="VD: PL-118-B" /></div>
    <div class="lg-field"><label class="lg-field-label">Ngày PL <span style="color:#dc2626">*</span></label><input class="lg-input" value="{2}" placeholder="VD: 09/09/2026" /></div>
  </div>
</div>
""".format(c.get("hdntNo", ""), c.get("plNo", ""), c.get("plDate", ""))

        return '<div class="lg-cols-2" style="margin-top:12px">{0}{1}</div>'.format(hdnt_block, pl_block)

    missing_class = " missing" if not c.get("hdmbDate") else ""
    return """
<div class="lg-card" style="margin-top:12px">
  <h4 style="font-weight:800;font-size:15px;margin:0 0 12px">Hợp đồng mua bán (HDMB)</h4>
  <div class="lg-cols-2">
    <div class="lg-field"><label class="lg-field-label">Số HDMB <span style="color:#dc2626">*</span></label><input class="lg-input" value="{0}" /></div>
    <div class="lg-field"><label class="lg-field-label">Ngày HDMB <span style="color:#dc2626">*</span></label><input class="lg-input{1}" value="{2}" placeholder="VD: 09/09/2026" /></div>
  </div>
</div>
""".format(c.get("hdmbNo", ""), missing_class, c.get("hdmbDate", ""))


def _render_ctab_linked(c):
    lots = c.get("linkedLots", [])
    rows = ""
    for l in lots:
        rows += """
<tr>
  <td><b><a class="lg-link" data-to="/lo-hang-detail?id={id}">{id}</a></b></td>
  <td>{cust}</td>
  <td>{status}</td>
  <td>{delivery}</td>
  <td>{pxk}</td>
  <td><div style="display:flex;gap:6px"><a class="lg-btn primary sm" data-to="/lo-hang-detail?id={id}">MỞ LÔ</a><a class="lg-btn ghost sm" data-to="/lo-hang-detail?id={id}&tab=chung-tu">LÀM PXK</a></div></td>
</tr>
""".format(id=l["id"], cust=l["customer"], status=l["status"], delivery=l["delivery"], pxk=l["pxk"])

    body = """
<div class="lg-card" style="margin-top:16px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 4px">Lô hàng liên kết — {n} lô</h3>
  <p style="font-size:13.5px;color:#64748b;margin:0 0 12px">PXK làm theo từng lô (không gộp). Bấm MỞ LÔ để xử lý, LÀM PXK để xuất phiếu.</p>
  <div style="overflow-x:auto">
    <table class="lg-tbl" style="min-width:760px">
      <thead><tr><th>Mã lô</th><th>Khách hàng</th><th>Trạng thái</th><th>Ngày giao</th><th>PXK</th><th>Hành động</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>
""".format(n=len(lots), rows=rows or '<tr><td colspan="6" style="text-align:center;color:#64748b;padding:24px">Chưa có lô liên kết.</td></tr>')
    st.markdown(body, unsafe_allow_html=True)
    ui._install_goto_bridge()


def _render_ctab_finance(c):
    pre_total = sum(g["qty"] * g["price"] for g in c.get("goods", []))
    vat = round(pre_total * 0.08)
    total = pre_total + vat
    received = sum(s["finance"].get("received", 0) for s in store.get_shipments() if s.get("contract") == c["id"])
    remain = max(0, total - received)

    body = """
<div class="lg-card" style="margin-top:16px;max-width:860px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Tài chính hợp đồng {cid}</h3>
  <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">Giá trị hợp đồng (sau VAT)</span><span style="font-weight:800;font-size:19px;color:#0f2a4a">{total_vnd}</span></div>
  <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">Đã thu (cộng các lô)</span><span style="font-weight:600">{rec_vnd}</span></div>
  <div style="display:flex;justify-content:space-between;padding:8px 0"><span style="font-size:13.5px;color:#64748b">Còn phải thu</span><span style="font-weight:700;color:#b91c1c">{rem_vnd}</span></div>
  <a class="lg-btn success" style="margin-top:12px" data-to="/tai-chinh/thu-tien">{arr} MỞ THU TIỀN & CÔNG NỢ</a>
</div>
""".format(cid=c["id"], total_vnd=design.fmt_vnd(total), rec_vnd=design.fmt_vnd(received), rem_vnd=design.fmt_vnd(remain), arr=icons.arrow_right(16, "#fff"))
    st.markdown(body, unsafe_allow_html=True)
    ui._install_goto_bridge()


def _render_ctab_history(c):
    history = c.get("history", [])
    if not history:
        empty = """
<div class="lg-card" style="margin-top:16px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Lịch sử phát hành & phụ lục</h3>
  <div style="border:2px dashed #cbd5e1;border-radius:12px;padding:24px;text-align:center;color:#64748b;font-size:14px">Chưa phát hành chứng từ nào. Sang tab <b>Hàng hóa & Chứng từ</b> để xuất bản đầu tiên.</div>
</div>
"""
        st.markdown(empty, unsafe_allow_html=True)
        return
    rows = ""
    for h in history:
        rows += """
<tr>
  <td style="font-weight:700">{type}</td>
  <td style="font-weight:600">{no}</td>
  <td>{date}</td>
  <td>{rev}</td>
  <td><span style="background:#d1fae5;color:#065f46;border-radius:999px;padding:4px 10px;font-size:12.5px;font-weight:800">● {status}</span></td>
  <td>{by} · {created}</td>
  <td><div style="display:flex;gap:6px"><button class="lg-btn ghost sm">{eye} Xem</button><button class="lg-btn ghost sm">{down} Tải lại</button></div></td>
</tr>
""".format(type=h.get("type", ""), no=h.get("no", ""), date=h.get("date", ""), rev=h.get("rev", ""), status=h.get("status", ""), by=h.get("by", ""), created=h.get("created", ""), eye=icons.eye(14, "#0f2a4a"), down=icons.download(14, "#0f2a4a"))

    body = """
<div class="lg-card" style="margin-top:16px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Lịch sử phát hành & phụ lục</h3>
  <div style="overflow-x:auto">
    <table class="lg-tbl" style="min-width:820px">
      <thead><tr><th>Loại</th><th>Số</th><th>Ngày</th><th>Revision</th><th>Trạng thái</th><th>Người tạo</th><th></th></tr></thead>
      <tbody>{0}</tbody>
    </table>
  </div>
</div>
""".format(rows)
    st.markdown(body, unsafe_allow_html=True)


def render_new_contract():
    if "nc_step" not in st.session_state:
        st.session_state["nc_step"] = 1
    if "nc_company" not in st.session_state:
        st.session_state["nc_company"] = ""
    if "nc_mst" not in st.session_state:
        st.session_state["nc_mst"] = ""
    if "nc_addr" not in st.session_state:
        st.session_state["nc_addr"] = ""
    if "nc_agent" not in st.session_state:
        st.session_state["nc_agent"] = "Phú An Logistics Việt Nam"
    if "nc_created" not in st.session_state:
        st.session_state["nc_created"] = None

    header = """
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{0}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Tạo Hợp Đồng Mới</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">3 bước: Bên mua → Hàng hóa → Xuất chứng từ. Mỗi bước đều báo rõ còn thiếu gì.</p>
      </div>
    </div>
  </div>
  {1}
</div>
""".format(icons.file_text(20, "#fff"), _stepper(st.session_state["nc_step"], st.session_state["nc_created"]))
    st.markdown(header, unsafe_allow_html=True)

    if st.session_state["nc_step"] == 1 and not st.session_state["nc_created"]:
        sel_pa = "selected" if st.session_state["nc_agent"] == "Phú An Logistics Việt Nam" else ""
        company_missing_cls = " missing" if not st.session_state["nc_company"] else ""
        mst_missing_cls = " missing" if not st.session_state["nc_mst"] else ""
        company_err = '<p class="lg-field-error">⚠ Nhập tên công ty — không để trống</p>' if not st.session_state["nc_company"] else ""
        mst_err = '<p class="lg-field-error">⚠ Nhập MST để tra cứu & in hợp đồng</p>' if not st.session_state["nc_mst"] else ""
        warn = ('<div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;padding:12px;font-size:13.5px;color:#9a3412">⚠ Thiếu tên công ty — nhập tên thì nút "Tiếp tục" mới đi tiếp được.</div>') if not st.session_state["nc_company"] else ""

        step1 = """
<div class="lg-card" style="display:flex;flex-direction:column;gap:14px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0">Bước 1 — Chọn đại lý & bên mua</h3>
  <div class="lg-field"><label class="lg-field-label">Đại lý (bên bán)</label>
    <select class="lg-input">
      <option {sel_pa}>Phú Anh Logistics Việt Nam</option>
      <option>Trường Thành — CN Lạng Sơn</option>
    </select>
  </div>
  <div class="lg-cols-2">
    <div class="lg-field"><label class="lg-field-label">Công ty bên mua <span style="color:#dc2626">*</span></label>
      <input class="lg-input{co_cls}" placeholder="VD: Công ty TNHH Thiết Bị Minh Đức" value="{co_val}" oninput="this.setAttribute('value', this.value)" />
      {co_err}
    </div>
    <div class="lg-field"><label class="lg-field-label">Mã số thuế <span style="color:#dc2626">*</span></label>
      <input class="lg-input{mst_cls}" placeholder="VD: 0201884452" value="{mst_val}" />
      {mst_err}
    </div>
  </div>
  <div class="lg-field"><label class="lg-field-label">Địa chỉ bên mua</label>
    <input class="lg-input" placeholder="VD: KCN Tràng Duệ, Hải Phòng" value="{addr_val}" />
  </div>
  {warn}
</div>
""".format(sel_pa=sel_pa, co_cls=company_missing_cls, co_val=st.session_state["nc_company"], co_err=company_err, mst_cls=mst_missing_cls, mst_val=st.session_state["nc_mst"], mst_err=mst_err, addr_val=st.session_state["nc_addr"], warn=warn)
        st.markdown(step1, unsafe_allow_html=True)

        c1, c2 = st.columns([1, 1])
        with c2:
            if st.button("TIẾP TỤC → NHẬP HÀNG HÓA", type="primary", use_container_width=True):
                if st.session_state["nc_company"] and st.session_state["nc_mst"]:
                    st.session_state["nc_step"] = 2
                    st.rerun()
                else:
                    store.push_toast("Thiếu thông tin bắt buộc", "Vui lòng nhập tên công ty + MST.", "red")

    if st.session_state["nc_step"] == 2 and not st.session_state["nc_created"]:
        addr_block = ('<p style="margin:0">Địa chỉ: {0}</p>'.format(st.session_state["nc_addr"])) if st.session_state["nc_addr"] else ""
        step2 = """
<div class="lg-card" style="display:flex;flex-direction:column;gap:14px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0">Bước 2 — Xác nhận & tạo nháp</h3>
  <div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:16px;font-size:14.5px;display:flex;flex-direction:column;gap:6px">
    <p style="margin:0">Đại lý: <b>{agent}</b></p>
    <p style="margin:0">Bên mua: <b>{company}</b> · MST {mst}</p>
    {addr}
  </div>
  <p style="font-size:13.5px;color:#64748b;margin:0">Bấm "Tạo nháp" để sinh số HDMB-033, sau đó nhập từng dòng hàng hóa ở màn hình chi tiết (máy tự tính VAT 8% & gợi ý HDMB/HDNT).</p>
  <div class="lg-cols-2">
    <button class="lg-btn ghost full" onclick="document.querySelector('button[data-action=&quot;nc_back&quot;]')?.click()">← Sửa bên mua</button>
    <button class="lg-btn primary full" onclick="document.querySelector('button[data-action=&quot;nc_create&quot;]')?.click()">➕ TẠO NHÁP HỢP ĐỒNG</button>
  </div>
</div>
""".format(agent=st.session_state["nc_agent"], company=st.session_state["nc_company"], mst=st.session_state["nc_mst"], addr=addr_block)
        st.markdown(step2, unsafe_allow_html=True)

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("← Sửa bên mua", type="secondary", use_container_width=True, key="nc_back"):
                st.session_state["nc_step"] = 1
                st.rerun()
        with c2:
            if st.button("➕ TẠO NHÁP HỢP ĐỒNG", type="primary", use_container_width=True, key="nc_create"):
                st.session_state["nc_created"] = "HDMB-PA-2026-033"
                store.push_toast("Đã tạo HDMB-PA-2026-033", "Hợp đồng nháp đã lưu — sang bước nhập hàng hóa để xuất chứng từ.", "green")
                st.rerun()

    if st.session_state["nc_created"]:
        done = """
<div class="lg-card" style="border:2px solid #bbf7d0;text-align:center;padding:32px">
  <div style="width:56px;height:56px;border-radius:999px;background:#10b981;color:#fff;display:grid;place-items:center;margin:0 auto">{ck}</div>
  <h3 style="font-size:19px;font-weight:800;color:#0f2a4a;margin:12px 0 4px">✅ ĐÃ TẠO NHÁP {cid}</h3>
  <p style="font-size:14.5px;color:#475569;margin:0">Bên mua: <b>{co}</b> · Tiếp theo: nhập hàng hóa → máy gợi ý phương án chứng từ → xuất file.</p>
  <div class="lg-cols-2" style="margin-top:16px;max-width:520px;margin-left:auto;margin-right:auto">
    <a class="lg-btn primary full" data-to="/hop-dong-detail?id=HDMB-PA-2026-032">{pen} NHẬP HÀNG HÓA NGAY</a>
    <a class="lg-btn ghost full" data-to="/hop-dong">{ft} Về danh sách</a>
  </div>
</div>
""".format(ck=icons.circle_check(28, "#fff"), cid=st.session_state["nc_created"], co=st.session_state["nc_company"], pen=icons.pen(17, "#fff"), ft=icons.file_text(17, "#0f2a4a"))
        st.markdown(done, unsafe_allow_html=True)
        ui._install_goto_bridge()


def _stepper(step: int, created):
    parts = ""
    states = [(0, "1 · Bên mua"), (1, "2 · Hàng hóa"), (2, "3 · Xuất")]
    for i, (idx, lbl) in enumerate(states):
        if created and i < 3:
            cls = "background:#10b981;color:#fff"
        elif i + 1 == step:
            cls = "background:#0f2a4a;color:#fff"
        else:
            cls = "background:#fff;border:1px solid #e4e9f1;color:#94a3b8"
        check = "✓ " if (created and i < 3) else ""
        parts += '<div style="flex:1"><span style="display:block;text-align:center;border-radius:12px;padding:10px 0;font-size:13.5px;font-weight:800;{0}">{1}{2}</span></div>'.format(cls, check, lbl)
        if i < 2:
            parts += '<span style="color:#cbd5e1;display:flex;align-items:center">→</span>'
    return '<div style="display:flex;align-items:center;gap:6px">{0}</div>'.format(parts)


def render_new_shipment():
    if "ns_done" not in st.session_state:
        st.session_state["ns_done"] = False

    header = """
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{0}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Tạo Lô Mới</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Tạo từ báo giá đã chốt — thông tin tự điền, chỉ bổ sung phần thiếu</p>
      </div>
    </div>
  </div>
</div>
""".format(icons.plus_circle(20, "#fff"))
    st.markdown(header, unsafe_allow_html=True)

    success_block = ""
    if st.session_state["ns_done"]:
        success_block = """
<div style="background:#ecfdf5;border:2px solid #bbf7d0;border-radius:12px;padding:16px;text-align:center">
  <p style="font-weight:800;color:#065f46;font-size:16px;margin:0">✅ ĐÃ TẠO LO-0309 (NHÁP)</p>
  <p style="font-size:13.5px;color:#047857;margin:4px 0 0">Tiếp theo: chốt xe TQ + giờ lấy hàng.</p>
  <div class="lg-cols-2" style="margin-top:12px">
    <a class="lg-btn success full" data-to="/lo-hang-detail?id=LO-0308&tab=lay-hang">MỞ TAB LẤY HÀNG MẪU →</a>
    <a class="lg-btn ghost full" data-to="/lo-hang">Về danh sách lô</a>
  </div>
</div>
"""
    else:
        success_block = '<button class="lg-btn primary full" onclick="document.querySelector(\'button[data-action=&quot;ns_create&quot;]\')?.click()">➕ TẠO LÔ HÀNG</button>'

    form_html = """
<div class="lg-card" style="display:flex;flex-direction:column;gap:14px;max-width:860px">
  <div class="lg-field">
    <label class="lg-field-label">Tạo từ báo giá đã chốt</label>
    <select class="lg-input">
      <option>BG-2026-214 (Minh Đức — ĐÃ CHỐT)</option>
      <option>BG-2026-212 (An Phát — ĐÃ CHỐT)</option>
      <option>Nhập tay (không từ báo giá)</option>
    </select>
    <span class="lg-field-hint">Chọn báo giá ACCEPTED — khách, tuyến, hàng tự điền</span>
  </div>
  <div class="lg-cols-2">
    <div class="lg-field"><label class="lg-field-label">Khách hàng <span style="color:#dc2626">*</span></label><input class="lg-input" value="Công ty TNHH Thiết Bị Minh Đức" /></div>
    <div class="lg-field"><label class="lg-field-label">Tuyến <span style="color:#dc2626">*</span></label>
      <select class="lg-input">
        <option>Quảng Đông → Hữu Nghị → Hải Phòng</option>
        <option>Quảng Đông → Hữu Nghị → Hà Nội</option>
        <option>Quảng Tây → Tân Thanh → Bắc Ninh</option>
      </select>
    </div>
    <div class="lg-field"><label class="lg-field-label">Cửa khẩu TQ</label>
      <select class="lg-input">
        <option>Hữu Nghị (TQ)</option>
        <option>Tân Thanh (TQ)</option>
      </select>
    </div>
    <div class="lg-field"><label class="lg-field-label">Ngày dự kiến lấy hàng <span style="color:#dc2626">*</span></label><input class="lg-input missing" placeholder="VD: 12/09/2026 09:00" /></div>
  </div>
  <div class="lg-field"><label class="lg-field-label">Hàng hóa</label><input class="lg-input" placeholder="VD: Máy CNC — 2 máy — 18.500 kg" /></div>
  {0}
  {1}
</div>
""".format("" if st.session_state["ns_done"] else '<button class="lg-btn primary full" onclick="document.querySelector(\'button[data-action=&quot;ns_create&quot;]\')?.click()">➕ TẠO LÔ HÀNG</button>', success_block)

    st.markdown(form_html, unsafe_allow_html=True)

    if not st.session_state["ns_done"]:
        if st.button("➕ TẠO LÔ HÀNG", type="primary", use_container_width=True, key="ns_create"):
            st.session_state["ns_done"] = True
            store.push_toast("Đã tạo lô LO-0309 (nháp)", "Tiếp theo: chốt xe TQ & giờ lấy ở tab Lấy hàng.", "green")
            st.rerun()
    ui._install_goto_bridge()
