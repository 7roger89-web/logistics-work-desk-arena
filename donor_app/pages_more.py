"""Contracts, Contract detail, New contract pages."""
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
  <a class="lg-btn-white" href="?p=/hop-dong/moi" target="_self">➕ TẠO HỢP ĐỒNG MỚI</a>
</div>
"""
    st.markdown(header_html, unsafe_allow_html=True)

    n_html = f'<div class="lg-card" style="margin-bottom:16px"><p style="font-size:13.5px;color:#64748b;margin:0">Tìm thấy <b style="color:#0f2a4a">{len(filtered)} hợp đồng</b> · Mỗi dòng: hiện trạng → việc thiếu → nút mở.</p></div>'
    st.markdown(n_html, unsafe_allow_html=True)

    if filtered:
        rows = []
        for c in filtered:
            type_lbl = c.get("type", "")
            value_html = f'<b>{design.fmt_vnd(c.get("value", 0))}</b>' if c.get("value") else '<span style="color:#b45309">Chưa tính</span>'
            valid_html = f'{c.get("validFrom", "")} → {c.get("validTo", "")}' if c.get("validFrom") else '<span style="color:#b45309;font-weight:600">⚠ Thiếu ngày</span>'
            type_bg = "#dbeafe" if type_lbl == "HDMB" else "#d1fae5"
            type_fg = "#1e40af" if type_lbl == "HDMB" else "#047857"
            type_span = f'<span style="background:{type_bg};color:{type_fg};font-size:12.5px;font-weight:800;border-radius:6px;padding:2px 8px">{type_lbl}</span>'
            rows.append([
                f'<a class="lg-link" href="?p=/hop-dong-detail&id={c["id"]}" target="_self" style="font-weight:800">{c["id"]}</a>',
                type_span,
                f'<b>{c.get("company", "")}</b><br><span style="font-size:12.5px;color:#64748b">{c.get("agent", "")}</span>',
                value_html,
                f'<span style="font-size:13px">{valid_html}</span>',
                f'<b style="text-align:center;display:block">{c.get("lots", 0)}</b>',
                f'<span class="lg-badge {c.get("statusTone", "gray")} sm">{c.get("status", "")}</span>',
                f'<a class="lg-btn primary sm" href="?p=/hop-dong-detail&id={c["id"]}" target="_self">MỞ HỢP ĐỒNG →</a>',
            ])
        from .pages_core import _render_table
        _render_table(["Số hợp đồng", "Loại", "Đại lý · Công ty", "Giá trị", "Hiệu lực", "Số lô", "Trạng thái", ""], rows, min_width="1020px")
    else:
        empty_html = """
<div class="lg-card" style="text-align:center;padding:48px;border:2px dashed #cbd5e1">
  <p style="font-weight:700;font-size:16px">Chưa có hợp đồng nào cho Đại lý này.</p>
  <a class="lg-btn primary" href="?p=/hop-dong/moi" target="_self">＋ TẠO HỢP ĐỒNG</a>
</div>
"""
        st.markdown(empty_html, unsafe_allow_html=True)


CONTRACT_TABS = [
    {"id": "thong-tin", "label": "Thông tin hợp đồng"},
    {"id": "hang-hoa", "label": "Hàng hóa & Chứng từ"},
    {"id": "lo-lien-ket", "label": "Lô hàng liên kết"},
    {"id": "tai-chinh", "label": "Tài chính hợp đồng"},
    {"id": "lich-su", "label": "Lịch sử / Phụ lục"},
]


def render_contract_detail():
    cid = store.get_contract_id() or st.query_params.get("id") or "HDMB-PA-2026-031"
    c = store.find_contract(cid)
    if not c:
        st.markdown(f'<div class="lg-card" style="text-align:center;padding:48px"><p style="font-size:19px;font-weight:800">Không tìm thấy {cid}</p></div>', unsafe_allow_html=True)
        return

    tab = st.session_state.get("active_contract_tab") or st.query_params.get("tab") or "hang-hoa"
    if tab not in [t["id"] for t in CONTRACT_TABS]:
        tab = "hang-hoa"

    st.markdown('<a class="lg-link" href="?p=/hop-dong" target="_self" style="display:inline-flex;align-items:center;gap:6px;margin-bottom:8px;font-size:14.5px">← Quay lại danh sách</a>', unsafe_allow_html=True)

    type_lbl = c.get("type", "")
    type_bg = "#dbeafe" if type_lbl == "HDMB" else "#d1fae5"
    type_fg = "#1e40af" if type_lbl == "HDMB" else "#047857"

    header_html = f"""
<div class="lg-card" style="padding:0;overflow:hidden">
  <div style="height:6px;background:linear-gradient(90deg,#10b981,#1e5aa8,#0f2a4a)"></div>
  <div style="padding:20px 24px">
    <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px">
      <h1 style="font-size:24px;font-weight:800;color:#0f2a4a;margin:0">{c["id"]}</h1>
      <span style="background:{type_bg};color:{type_fg};font-size:12.5px;font-weight:800;border-radius:6px;padding:4px 8px">{type_lbl}</span>
      <span class="lg-badge {c.get('statusTone', 'gray')}">{c.get('status', '')}</span>
    </div>
    <p style="font-size:14.5px;color:#475569;margin:6px 0 0">{c.get('company', '')} · Đại lý {c.get('agent', '')} · {c.get('lots', 0)} lô liên kết</p>
    <div class="lg-tabs">
      {_contract_tabs_html(c['id'], tab)}
    </div>
  </div>
</div>
"""
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


def _contract_tabs_html(c_id, active):
    parts = []
    for t in CONTRACT_TABS:
        cls = "lg-tab active" if t["id"] == active else "lg-tab"
        parts.append(f'<a class="{cls}" href="?p=/hop-dong-detail&id={c_id}&tab={t["id"]}" target="_self" style="text-decoration:none">{t["label"]}</a>')
    return "".join(parts)


def _render_ctab_info(c):
    buyer_missing = c.get("missingBuyerInfo", [])
    company = c.get("company", "")
    agent = c.get("agent", "")

    rep_html = f'<b>{c.get("companyRep", "")}</b>' if c.get("companyRep") else '<span style="color:#b45309;font-weight:700">⚠ Thiếu người đại diện</span>'
    role_html = f'<b>{c.get("companyRole", "")}</b>' if c.get("companyRole") else '<span style="color:#b45309;font-weight:700">⚠ Thiếu chức vụ</span>'

    extra_block = ""
    if buyer_missing:
        extra_block = """
<div style="margin-top:12px;background:#fffbeb;border:2px dashed #fbbf24;border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:10px">
  <p style="font-weight:700;color:#92400e;font-size:14.5px;margin:0">✏️ BỔ SUNG THÔNG TIN — thiếu người đại diện & chức vụ</p>
  <div class="lg-cols-2">
    <div class="lg-field"><label class="lg-field-label">Người đại diện bên mua <span style="color:#dc2626">*</span></label><input class="lg-input missing" placeholder="VD: Phạm Minh Đức" /></div>
    <div class="lg-field"><label class="lg-field-label">Chức vụ <span style="color:#dc2626">*</span></label><input class="lg-input missing" placeholder="VD: Giám đốc" /></div>
  </div>
</div>
"""

    left = f"""
<div class="lg-card">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Bên mua — {company}</h3>
  <div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:14px;font-size:14.5px;display:flex;flex-direction:column;gap:6px">
    <p style="margin:0"><span style="color:#64748b">Tên pháp lý:</span> <b>{c.get("companyLegal", "")}</b></p>
    <p style="margin:0"><span style="color:#64748b">Địa chỉ:</span> {c.get("companyAddr", "")}</p>
    <p style="margin:0"><span style="color:#64748b">MST:</span> <b>{c.get("companyTax", "")}</b></p>
    <p style="margin:0"><span style="color:#64748b">Người đại diện:</span> {rep_html}</p>
    <p style="margin:0"><span style="color:#64748b">Chức vụ:</span> {role_html}</p>
  </div>
  {extra_block}
</div>
"""

    right = f"""
<div class="lg-card">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Bên bán / Đại lý — {agent}</h3>
  <div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:14px;font-size:14.5px;display:flex;flex-direction:column;gap:6px">
    <p style="margin:0"><span style="color:#64748b">Tên pháp lý:</span> <b>{c.get("agentLegal", "")}</b></p>
    <p style="margin:0"><span style="color:#64748b">Địa chỉ:</span> {c.get("agentAddr", "")}</p>
    <p style="margin:0"><span style="color:#64748b">MST / mã pháp lý:</span> <b>{c.get("agentTax", "")}</b></p>
    <p style="margin:0"><span style="color:#64748b">Người đại diện:</span> <b>{c.get("agentRep", "")}</b> · {c.get("agentRole", "")}</p>
    <p style="margin:0"><span style="color:#64748b">Chủ tài khoản:</span> {c.get("bankOwner", "")}</p>
    <p style="margin:0"><span style="color:#64748b">Số TK:</span> <b>{c.get("bankNo", "")}</b> · {c.get("bankName", "")}</p>
  </div>
  <div style="margin-top:12px;background:#ecfdf5;border:1px solid #bbf7d0;border-radius:12px;padding:12px;font-size:13.5px;color:#064e3b">✅ Thông tin đại lý đầy đủ — không cần bổ sung.</div>
</div>
"""

    st.markdown(f'<div class="lg-2col" style="margin-top:16px">{left}{right}</div>', unsafe_allow_html=True)


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
    banner = f"""
<div style="margin-top:12px;background:{bg};border:2px solid {border};border-radius:16px;padding:16px;display:flex;flex-direction:row;align-items:center;gap:12px;flex-wrap:wrap">
  <div style="flex:1">
    <p style="font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;opacity:.7;margin:0">Tổng sau VAT: {design.fmt_vnd(total)}</p>
    <p style="font-size:21px;font-weight:800;color:#0f2a4a;margin:2px 0 0">{route_text}</p>
    <p style="font-size:13.5px;color:#475569;margin:4px 0 0">Ngưỡng: dưới 50.000.000 ₫ → HDNT + PL · Từ 50.000.000 ₫ trở lên → HDMB.</p>
  </div>
  <span style="background:{badge_bg};color:#fff;border-radius:999px;padding:8px 16px;font-weight:800;font-size:14.5px;display:inline-flex;align-items:center;gap:6px">{badge_icon} {readiness_label}</span>
</div>
"""

    goods_rows = ""
    for i, g in enumerate(goods):
        bad = not g["desc"].strip() or not g["qty"] or not g["price"]
        row_class = ' style="background:#fef2f2"' if bad else ""
        desc_invalid = " invalid" if not g["desc"].strip() else ""
        qty_invalid = " invalid" if not g["qty"] else ""
        price_invalid = " invalid" if not g["price"] else ""
        price_value = f'{g["price"]:,.0f}'.replace(",", ".") if g["price"] else ""
        line_total = design.fmt_vnd(round(g["qty"] * g["price"] * 1.08))
        sel = lambda unit: ' selected' if g["unit"] == unit else ''
        unit_options = f'<option{sel("Cái")}>Cái</option><option{sel("Máy")}>Máy</option><option{sel("Bộ")}>Bộ</option><option{sel("Lô")}>Lô</option><option{sel("Hệ thống")}>Hệ thống</option><option{sel("Kiện")}>Kiện</option><option{sel("Kg")}>Kg</option>'
        goods_rows += f"""
<tr{row_class}>
  <td style="font-weight:800;text-align:center">{i + 1}</td>
  <td><input class="lg-input{desc_invalid}" value="{g['desc']}" /></td>
  <td><select class="lg-input">{unit_options}</select></td>
  <td><input type="number" class="lg-input{qty_invalid}" value="{g['qty']}" /></td>
  <td><input type="text" class="lg-input{price_invalid}" value="{price_value}" /></td>
  <td style="text-align:center;font-weight:700;color:#64748b">8%</td>
  <td style="font-weight:800;color:#0f2a4a;white-space:nowrap">{line_total}</td>
  <td><span style="color:#dc2626;cursor:pointer">{icons.trash(17, "#dc2626")}</span></td>
</tr>
"""

    goods_card = f"""
<div class="lg-card" style="margin-top:16px">
  <div class="lg-section-title">
    <h2 style="font-size:17px;font-weight:800;color:#0f2a4a;margin:0">Hàng hóa — nhập từng dòng, máy tự tính tiền</h2>
    <span style="font-size:13px;color:#64748b">STT · VAT 8% · Thành tiền: tự động, không cần nhập</span>
  </div>
  <div style="overflow-x:auto">
    <table class="lg-tbl" style="min-width:860px">
      <thead><tr><th style="width:52px">STT</th><th>Mô tả hàng hóa *</th><th style="width:110px">Đơn vị</th><th style="width:110px">Số lượng *</th><th style="width:170px">Đơn giá chưa VAT *</th><th style="width:80px">VAT</th><th style="width:160px">Thành tiền</th><th style="width:70px"></th></tr></thead>
      <tbody>{goods_rows}</tbody>
    </table>
  </div>
  <div class="lg-cols-3" style="margin-top:12px;background:#0f2a4a;color:#fff;padding:16px;border-radius:16px;text-align:center">
    <div><p style="font-size:12px;color:#bfdbfe;font-weight:600;margin:0">Tiền hàng</p><p style="font-size:18px;font-weight:800;margin:2px 0 0">{design.fmt_vnd(pre_total)}</p></div>
    <div><p style="font-size:12px;color:#bfdbfe;font-weight:600;margin:0">VAT 8%</p><p style="font-size:18px;font-weight:800;margin:2px 0 0">{design.fmt_vnd(vat)}</p></div>
    <div style="background:rgba(255,255,255,.1);border-radius:12px;padding:8px 0"><p style="font-size:12px;color:#fde68a;font-weight:700;margin:0">TỔNG SAU VAT</p><p style="font-size:21px;font-weight:800;color:#fde68a;margin:2px 0 0">{design.fmt_vnd(total)}</p></div>
  </div>
</div>
"""

    st.markdown(goods_card, unsafe_allow_html=True)
    st.markdown(f"""
<div class="lg-card" style="border:2px solid #0f2a4a;margin-top:16px">
  <h3 style="font-size:17px;font-weight:800;color:#0f2a4a;margin:0">✅ PHƯƠNG ÁN CHỨNG TỪ <span style="font-size:13px;font-weight:500;color:#64748b">(tự chọn theo tổng sau VAT — đúng 50 tr thuộc HDMB)</span></h3>
  {banner}
  {_render_route_form(c, route)}
</div>
""", unsafe_allow_html=True)


def _render_route_form(c, route):
    if route == "HDNT+PL":
        reusable = ""
        if c.get("reusableHdnt"):
            reusable = f"""
<div style="background:#ecfdf5;border:1px solid #bbf7d0;border-radius:12px;padding:12px;margin-bottom:12px">
  <p style="font-weight:700;font-size:14px;color:#064e3b;margin:0">✔ CÓ THỂ TÁI SỬ DỤNG HDNT {c.get('hdntNo', '')} (còn hiệu lực tới {c.get('hdntTo', '')})</p>
</div>
"""

        hdnt_block = f"""
<div class="lg-card" style="margin-top:12px">
  <h4 style="font-weight:800;font-size:15px;margin:0 0 12px">Hợp đồng nguyên tắc (HDNT)</h4>
  {reusable}
  <div class="lg-cols-2">
    <div class="lg-field"><label class="lg-field-label">Số HDNT <span style="color:#dc2626">*</span></label><input class="lg-input" value="{c.get('hdntNo', '')}" placeholder="VD: HDNT-PA-2026-119" /></div>
    <div class="lg-field"><label class="lg-field-label">Ngày ký <span style="color:#dc2626">*</span></label><input class="lg-input" value="{c.get('hdntDate', '')}" placeholder="VD: 09/09/2026" /></div>
    <div class="lg-field"><label class="lg-field-label">Hiệu lực từ</label><input class="lg-input" value="{c.get('hdntFrom', '')}" /></div>
    <div class="lg-field"><label class="lg-field-label">Hiệu lực đến</label><input class="lg-input" value="{c.get('hdntTo', '')}" /></div>
  </div>
</div>
"""

        pl_block = f"""
<div class="lg-card" style="margin-top:12px">
  <h4 style="font-weight:800;font-size:15px;margin:0 0 12px">Phụ lục (PL) — HDNT cha: {c.get('hdntNo', '')}</h4>
  <div class="lg-cols-2">
    <div class="lg-field"><label class="lg-field-label">Số PL <span style="color:#dc2626">*</span></label><input class="lg-input" value="{c.get('plNo', '')}" placeholder="VD: PL-118-B" /></div>
    <div class="lg-field"><label class="lg-field-label">Ngày PL <span style="color:#dc2626">*</span></label><input class="lg-input" value="{c.get('plDate', '')}" placeholder="VD: 09/09/2026" /></div>
  </div>
</div>
"""
        return f'<div class="lg-cols-2" style="margin-top:12px">{hdnt_block}{pl_block}</div>'

    missing_class = " missing" if not c.get("hdmbDate") else ""
    return f"""
<div class="lg-card" style="margin-top:12px">
  <h4 style="font-weight:800;font-size:15px;margin:0 0 12px">Hợp đồng mua bán (HDMB)</h4>
  <div class="lg-cols-2">
    <div class="lg-field"><label class="lg-field-label">Số HDMB <span style="color:#dc2626">*</span></label><input class="lg-input" value="{c.get('hdmbNo', '')}" /></div>
    <div class="lg-field"><label class="lg-field-label">Ngày HDMB <span style="color:#dc2626">*</span></label><input class="lg-input{missing_class}" value="{c.get('hdmbDate', '')}" placeholder="VD: 09/09/2026" /></div>
  </div>
</div>
"""


def _render_ctab_linked(c):
    lots = c.get("linkedLots", [])
    rows = ""
    for l in lots:
        rows += f"""
<tr>
  <td><b><a class="lg-link" href="?p=/lo-hang-detail&id={l['id']}" target="_self">{l['id']}</a></b></td>
  <td>{l['customer']}</td>
  <td>{l['status']}</td>
  <td>{l['delivery']}</td>
  <td>{l['pxk']}</td>
  <td><div style="display:flex;gap:6px"><a class="lg-btn primary sm" href="?p=/lo-hang-detail&id={l['id']}" target="_self">MỞ LÔ</a><a class="lg-btn ghost sm" href="?p=/lo-hang-detail&id={l['id']}&tab=chung-tu" target="_self">LÀM PXK</a></div></td>
</tr>
"""

    body = f"""
<div class="lg-card" style="margin-top:16px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 4px">Lô hàng liên kết — {len(lots)} lô</h3>
  <p style="font-size:13.5px;color:#64748b;margin:0 0 12px">PXK làm theo từng lô (không gộp). Bấm MỞ LÔ để xử lý, LÀM PXK để xuất phiếu.</p>
  <div style="overflow-x:auto">
    <table class="lg-tbl" style="min-width:760px">
      <thead><tr><th>Mã lô</th><th>Khách hàng</th><th>Trạng thái</th><th>Ngày giao</th><th>PXK</th><th>Hành động</th></tr></thead>
      <tbody>{rows or '<tr><td colspan="6" style="text-align:center;color:#64748b;padding:24px">Chưa có lô liên kết.</td></tr>'}</tbody>
    </table>
  </div>
</div>
"""
    st.markdown(body, unsafe_allow_html=True)


def _render_ctab_finance(c):
    pre_total = sum(g["qty"] * g["price"] for g in c.get("goods", []))
    vat = round(pre_total * 0.08)
    total = pre_total + vat
    received = sum(s["finance"].get("received", 0) for s in store.get_shipments() if s.get("contract") == c["id"])
    remain = max(0, total - received)

    body = f"""
<div class="lg-card" style="margin-top:16px;max-width:860px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Tài chính hợp đồng {c['id']}</h3>
  <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">Giá trị hợp đồng (sau VAT)</span><span style="font-weight:800;font-size:19px;color:#0f2a4a">{design.fmt_vnd(total)}</span></div>
  <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9"><span style="font-size:13.5px;color:#64748b">Đã thu (cộng các lô)</span><span style="font-weight:600">{design.fmt_vnd(received)}</span></div>
  <div style="display:flex;justify-content:space-between;padding:8px 0"><span style="font-size:13.5px;color:#64748b">Còn phải thu</span><span style="font-weight:700;color:#b91c1c">{design.fmt_vnd(remain)}</span></div>
  <a class="lg-btn success" style="margin-top:12px" href="?p=/tai-chinh/thu-tien" target="_self">{icons.arrow_right(16, "#fff")} MỞ THU TIỀN & CÔNG NỢ</a>
</div>
"""
    st.markdown(body, unsafe_allow_html=True)


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
        rows += f"""
<tr>
  <td style="font-weight:700">{h.get('type', '')}</td>
  <td style="font-weight:600">{h.get('no', '')}</td>
  <td>{h.get('date', '')}</td>
  <td>{h.get('rev', '')}</td>
  <td><span style="background:#d1fae5;color:#065f46;border-radius:999px;padding:4px 10px;font-size:12.5px;font-weight:800">● {h.get('status', '')}</span></td>
  <td>{h.get('by', '')} · {h.get('created', '')}</td>
  <td><span class="lg-badge green sm">{icons.download(14, "#047857")} Có sẵn</span></td>
</tr>
"""

    body = f"""
<div class="lg-card" style="margin-top:16px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Lịch sử phát hành & phụ lục</h3>
  <div style="overflow-x:auto">
    <table class="lg-tbl" style="min-width:820px">
      <thead><tr><th>Loại</th><th>Số</th><th>Ngày</th><th>Revision</th><th>Trạng thái</th><th>Người tạo</th><th></th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>
"""
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
        st.session_state["nc_agent"] = "Phú Anh Logistics Việt Nam"
    if "nc_created" not in st.session_state:
        st.session_state["nc_created"] = None

    header = f"""
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{icons.file_text(20, "#fff")}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Tạo Hợp Đồng Mới</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">3 bước: Bên mua → Hàng hóa → Xuất chứng từ. Mỗi bước đều báo rõ còn thiếu gì.</p>
      </div>
    </div>
  </div>
  {_stepper(st.session_state["nc_step"], st.session_state["nc_created"])}
</div>
"""
    st.markdown(header, unsafe_allow_html=True)

    if st.session_state["nc_step"] == 1 and not st.session_state["nc_created"]:
        with st.form("form_new_contract_step1"):
            st.markdown('<h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0 0 12px">Bước 1 — Chọn đại lý & bên mua</h3>', unsafe_allow_html=True)
            agent = st.selectbox("Đại lý (bên bán)", ["Phú Anh Logistics Việt Nam", "Trường Thành — CN Lạng Sơn"], index=0)
            c1, c2 = st.columns(2)
            with c1:
                co = st.text_input("Công ty bên mua *", value=st.session_state["nc_company"], placeholder="VD: Công ty TNHH Thiết Bị Minh Đức")
            with c2:
                mst = st.text_input("Mã số thuế *", value=st.session_state["nc_mst"], placeholder="VD: 0201884452")
            addr = st.text_input("Địa chỉ bên mua", value=st.session_state["nc_addr"], placeholder="VD: KCN Tràng Duệ, Hải Phòng")

            submit = st.form_submit_button("TIẾP TỤC → NHẬP HÀNG HÓA", type="primary", use_container_width=True)
            if submit:
                if co.strip() and mst.strip():
                    st.session_state["nc_agent"] = agent
                    st.session_state["nc_company"] = co.strip()
                    st.session_state["nc_mst"] = mst.strip()
                    st.session_state["nc_addr"] = addr.strip()
                    st.session_state["nc_step"] = 2
                    st.rerun()
                else:
                    store.push_toast("Thiếu thông tin bắt buộc", "Vui lòng nhập tên công ty và MST bên mua.", "red")
                    st.rerun()

    elif st.session_state["nc_step"] == 2 and not st.session_state["nc_created"]:
        step2 = f"""
<div class="lg-card" style="display:flex;flex-direction:column;gap:14px">
  <h3 style="font-size:16.5px;font-weight:800;color:#0f2a4a;margin:0">Bước 2 — Xác nhận & tạo nháp</h3>
  <div style="background:#f8fafc;border:1px solid #e4e9f1;border-radius:12px;padding:16px;font-size:14.5px;display:flex;flex-direction:column;gap:6px">
    <p style="margin:0">Đại lý: <b>{st.session_state["nc_agent"]}</b></p>
    <p style="margin:0">Bên mua: <b>{st.session_state["nc_company"]}</b> · MST {st.session_state["nc_mst"]}</p>
    {f'<p style="margin:0">Địa chỉ: {st.session_state["nc_addr"]}</p>' if st.session_state["nc_addr"] else ''}
  </div>
  <p style="font-size:13.5px;color:#64748b;margin:0">Bấm "Tạo nháp" để sinh số HDMB-033, sau đó nhập từng dòng hàng hóa ở màn hình chi tiết (máy tự tính VAT 8% & gợi ý HDMB/HDNT).</p>
</div>
"""
        st.markdown(step2, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Sửa bên mua", type="secondary", use_container_width=True, key="nc_back"):
                st.session_state["nc_step"] = 1
                st.rerun()
        with c2:
            if st.button("➕ TẠO NHÁP HỢP ĐỒNG", type="primary", use_container_width=True, key="nc_create"):
                new_cid = "HDMB-PA-2026-033"
                new_ct = {
                    "id": new_cid,
                    "type": "HDMB",
                    "company": st.session_state["nc_company"],
                    "companyLegal": st.session_state["nc_company"].upper(),
                    "companyAddr": st.session_state["nc_addr"],
                    "companyTax": st.session_state["nc_mst"],
                    "companyRep": "Nguyễn Văn Đại",
                    "companyRole": "Giám đốc",
                    "agent": st.session_state["nc_agent"],
                    "agentLegal": "CÔNG TY TNHH PHÚ ANH LOGISTICS VIỆT NAM",
                    "agentAddr": "Số 88 Trần Thái Tông, Cầu Giấy, Hà Nội",
                    "agentTax": "0108123456",
                    "agentRep": "Nguyễn Phú Anh",
                    "agentRole": "Giám đốc",
                    "bankOwner": "CÔNG TY TNHH PHÚ ANH LOGISTICS VIỆT NAM",
                    "bankNo": "0451000412345",
                    "bankName": "Vietcombank Thanh Xuân",
                    "value": 0,
                    "validFrom": "09/09/2026",
                    "validTo": "31/12/2026",
                    "lots": 0,
                    "status": "Còn hiệu lực",
                    "statusTone": "green",
                    "missingBuyerInfo": [],
                    "goods": [
                        {"desc": "Máy công nghiệp model PA-2026", "unit": "Máy", "qty": 1, "price": 450_000_000},
                    ],
                    "hdmbNo": new_cid,
                    "hdmbDate": "09/09/2026",
                    "history": [
                        {"type": "HDMB", "no": new_cid, "date": "09/09/2026", "rev": "V1", "status": "ĐÃ PHÁT HÀNH", "by": "Thu Hằng", "created": "09/09/2026"},
                    ],
                    "linkedLots": [],
                }
                store.get_contracts().insert(0, new_ct)
                st.session_state["nc_created"] = new_cid
                store.set_contract_id(new_cid)
                store.push_toast(f"Đã tạo {new_cid}", "Hợp đồng nháp đã lưu — sang bước nhập hàng hóa để xuất chứng từ.", "green")
                st.rerun()

    if st.session_state["nc_created"]:
        cid = st.session_state["nc_created"]
        done = f"""
<div class="lg-card" style="border:2px solid #bbf7d0;text-align:center;padding:32px">
  <div style="width:56px;height:56px;border-radius:999px;background:#10b981;color:#fff;display:grid;place-items:center;margin:0 auto">{icons.circle_check(28, "#fff")}</div>
  <h3 style="font-size:19px;font-weight:800;color:#0f2a4a;margin:12px 0 4px">✅ ĐÃ TẠO NHÁP {cid}</h3>
  <p style="font-size:14.5px;color:#475569;margin:0">Bên mua: <b>{st.session_state['nc_company']}</b> · Tiếp theo: nhập hàng hóa → máy gợi ý phương án chứng từ → xuất file.</p>
  <div class="lg-cols-2" style="margin-top:16px;max-width:520px;margin-left:auto;margin-right:auto">
    <a class="lg-btn primary full" href="?p=/hop-dong-detail&id={cid}&tab=hang-hoa" target="_self">{icons.pen(17, "#fff")} NHẬP HÀNG HÓA NGAY</a>
    <a class="lg-btn ghost full" href="?p=/hop-dong" target="_self">{icons.file_text(17, "#0f2a4a")} Về danh sách</a>
  </div>
</div>
"""
        st.markdown(done, unsafe_allow_html=True)


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
        parts += f'<div style="flex:1"><span style="display:block;text-align:center;border-radius:12px;padding:10px 0;font-size:13.5px;font-weight:800;{cls}">{check}{lbl}</span></div>'
        if i < 2:
            parts += '<span style="color:#cbd5e1;display:flex;align-items:center">→</span>'
    return f'<div style="display:flex;align-items:center;gap:6px">{parts}</div>'


def render_new_shipment():
    if "ns_done" not in st.session_state:
        st.session_state["ns_done"] = False

    header = f"""
<div class="lg-card" style="margin-bottom:16px">
  <div class="lg-section-title">
    <div style="display:flex;align-items:flex-start;gap:10px">
      <span class="lg-section-icon">{icons.plus_circle(20, "#fff")}</span>
      <div>
        <h2 style="font-size:18px;font-weight:800;color:#0f2a4a;margin:0">Tạo Lô Mới</h2>
        <p style="font-size:13.5px;color:#64748b;margin:2px 0 0">Tạo từ báo giá đã chốt — thông tin tự điền, chỉ bổ sung phần thiếu</p>
      </div>
    </div>
  </div>
</div>
"""
    st.markdown(header, unsafe_allow_html=True)

    if st.session_state["ns_done"]:
        success_block = """
<div style="background:#ecfdf5;border:2px solid #bbf7d0;border-radius:12px;padding:16px;text-align:center">
  <p style="font-weight:800;color:#065f46;font-size:16px;margin:0">✅ ĐÃ TẠO LO-0309 (NHÁP)</p>
  <p style="font-size:13.5px;color:#047857;margin:4px 0 0">Tiếp theo: chốt xe TQ + giờ lấy hàng.</p>
  <div class="lg-cols-2" style="margin-top:12px">
    <a class="lg-btn success full" href="?p=/lo-hang-detail&id=LO-0309&tab=lay-hang" target="_self">MỞ TAB LẤY HÀNG MẪU →</a>
    <a class="lg-btn ghost full" href="?p=/lo-hang" target="_self">Về danh sách lô</a>
  </div>
</div>
"""
        st.markdown(success_block, unsafe_allow_html=True)
    else:
        with st.form("form_new_shipment"):
            bg_sel = st.selectbox("Tạo từ báo giá đã chốt", ["BG-2026-214 (Minh Đức — ĐÃ CHỐT)", "BG-2026-212 (An Phát — ĐÃ CHỐT)", "Nhập tay (không từ báo giá)"])
            c1, c2 = st.columns(2)
            with c1:
                cust = st.text_input("Khách hàng *", value="Công ty TNHH Thiết Bị Minh Đức")
                route = st.selectbox("Tuyến *", ["Quảng Đông → Hữu Nghị → Hải Phòng", "Quảng Đông → Hữu Nghị → Hà Nội", "Quảng Tây → Tân Thanh → Bắc Ninh"])
            with c2:
                border = st.selectbox("Cửa khẩu TQ", ["Hữu Nghị (TQ)", "Tân Thanh (TQ)"])
                pickup_date = st.text_input("Ngày dự kiến lấy hàng *", value="12/09/2026 09:00")
            cargo = st.text_input("Hàng hóa", value="Máy dập kim loại 200 tấn — 1 máy — 18.500 kg")

            create_submit = st.form_submit_button("➕ TẠO LÔ HÀNG", type="primary", use_container_width=True)
            if create_submit:
                new_lot = {
                    "id": "LO-0309",
                    "customer": cust,
                    "customerShort": "Minh Đức",
                    "customerMST": "0200667788",
                    "customer_id": "minh_duc",
                    "contract": "HDMB-PA-2026-028",
                    "route": route,
                    "borderVN": "Hữu Nghị",
                    "sale": "Hồng Nhung",
                    "support": "Thu Hằng",
                    "status": "Chờ lấy hàng",
                    "statusTone": "amber",
                    "priority": "Khan",
                    "nextAction": "Chốt xe TQ + giờ lấy hàng trước 12:00 hôm nay",
                    "nextActionDetail": "Nhà máy cần báo trước 24h — đang chờ Bằng Tường xác nhận xe",
                    "nextLabel": "CHỐT XE NGAY",
                    "nextRoute": "/lo-hang-detail?id=LO-0309&tab=lay-hang",
                    "updated": "09/09/2026 10:00",
                    "pickup": {
                        "factory": "Nhà máy Thiết Bị Minh Đức — CN Quảng Đông",
                        "address": "Khu CNC Đông Quan, Quảng Đông",
                        "contact": "Mr. Wang",
                        "phone": "+86 137 5566 7788",
                        "truckType": "Cont 40HQ",
                        "plate": "",
                        "driver": "",
                        "driverPhone": "",
                        "eta": "12/09/2026",
                        "ata": "—",
                        "pickupTime": pickup_date,
                    },
                    "importInfo": {
                        "borderVN": "Hữu Nghị (VN)", "declarationNo": "", "regDate": "", "tax": 22_000_000, "vat": 44_000_000,
                        "inspection": "Luồng vàng", "license": "—", "truckVN": "Cont 40HQ",
                        "plateVN": "", "driverVN": "", "schedule": "14/09/2026",
                        "deliveryAddr": "KCN Tràng Duệ, Hải Phòng", "receiver": "Nguyễn Hải Yến", "receiverPhone": "0912 345 678",
                        "delivered": False, "actualDelivery": "", "clearDate": "",
                    },
                    "cargo": {
                        "type": cargo, "packs": 1, "weight": "18.500 kg", "cbm": 22,
                        "dims": "4.2 x 2.0 x 2.6 m", "note": "Yêu cầu xe cẩu chuyên dụng",
                    },
                    "exportInfo": {
                        "border": "Hữu Nghị (TQ)", "declarant": "Phú Anh — chi nhánh Bằng Tường",
                        "eta": "12/09/2026", "ata": "—", "state": "Chờ lấy hàng",
                    },
                    "docs": [
                        {"name": "Hợp đồng mua bán (HDMB)", "ok": True, "note": "HDMB-PA-2026-028"},
                        {"name": "Packing List", "ok": False, "note": "Đang chờ nhà máy cập nhật"},
                        {"name": "Invoice (Hóa đơn thương mại)", "ok": True, "note": "INV-2026-0615"},
                    ],
                    "pxk": {"number": "", "date": "", "place": "", "receiver": "", "role": "Thủ kho", "source": "HDMB-PA-2026-028", "done": False},
                    "finance": {
                        "receivable": 425_000_000, "received": 0, "payable": 58_000_000, "paid": 0,
                        "payments": [],
                        "quote": [],
                        "actual": [],
                    },
                    "timeline": [
                        {"time": "09/09 10:00", "title": "Đã tạo lô LO-0309", "desc": "Từ báo giá BG-2026-214 đã chốt", "tone": "blue"},
                    ],
                    "missingDocs": ["Biển số xe TQ", "Tài xế TQ"],
                }
                store.get_shipments().insert(0, new_lot)
                st.session_state["ns_done"] = True
                store.set_shipment_id("LO-0309")
                store.push_toast("Đã tạo lô LO-0309 (nháp)", "Tiếp theo: chốt xe TQ & giờ lấy ở tab Lấy hàng.", "green")
                st.rerun()
