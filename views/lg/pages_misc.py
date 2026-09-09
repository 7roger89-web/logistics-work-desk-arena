"""Donor-structured surfaces for Kinh doanh / Tài chính / Công cụ / Quản trị."""
from __future__ import annotations

import streamlit as st

from . import svc, widgets as w
from .helpers import actor, set_page, to_text, UNKNOWN
from .shell import render_mobile_drawer, render_header
from .widgets import fmt_money


# ------------------------------------------------------------------ CUSTOMERS
def customers_page():
    render_header("Khách Hàng", "Danh sách khách hàng & người liên hệ")
    render_mobile_drawer()
    rows = svc.customers()
    if st.button("＋ Thêm khách hàng", key="cus_new", type="primary"):
        st.info("Biểu mẫu thêm khách hàng nằm ở phân hệ Khách Hàng (thực thi nghiệp vụ).")
    if not rows:
        st.markdown('<div class="lg-card" style="color:#64748b">Chưa có khách hàng trong dữ liệu.</div>',
                    unsafe_allow_html=True)
        return
    head = "<tr><th>Khách hàng</th><th>MST</th><th>Người liên hệ</th><th>Điện thoại</th><th>Sale</th></tr>"
    body = []
    for r in rows.values():
        body.append(
            f'<tr><td><b style="color:#0f2a4a">{w._esc(r.get("name") or r.get("company") or r.get("id"))}</b>'
            f'<div class="lg-muted" style="font-size:12px">{w._esc(r.get("id"))}</div></td>'
            f'<td>{w._esc(r.get("mst",""))}</td>'
            f'<td>{w._esc(r.get("contact") or r.get("contact_person"))}</td>'
            f'<td>{w._esc(r.get("phone"))}</td>'
            f'<td>{w._esc(r.get("sale_owner") or r.get("sales_owner"))}</td></tr>')
    st.markdown(f'<div class="lg-tablewrap"><table class="lg-tbl"><thead>{head}</thead>'
                f'<tbody>{"".join(body)}</tbody></table></div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ CONTRACTS
def contracts_page():
    render_header("Hợp Đồng", "HDMB · Phụ lục · theo dõi nghĩa vụ hợp đồng")
    render_mobile_drawer()
    if st.button("＋ Hợp đồng mới", key="ctr_new", type="primary"):
        set_page("new_contract")
    rows = svc.contracts()
    if not rows:
        st.markdown('<div class="lg-card" style="color:#64748b">Chưa có hợp đồng trong dữ liệu.</div>',
                    unsafe_allow_html=True)
        return
    head = "<tr><th>Số hợp đồng</th><th>Khách hàng</th><th>Loại</th><th>Trạng thái</th><th>Giá trị</th></tr>"
    body = []
    for r in rows.values():
        tone = "green" if (r.get("status") or "").lower() in ("active", "hoạt động") else "amber"
        body.append(
            f'<tr><td><b style="color:#0f2a4a">{w._esc(r.get("contract_no") or r.get("id"))}</b></td>'
            f'<td>{w._esc(r.get("customer") or r.get("customer_name"))}</td>'
            f'<td>{w._esc(r.get("type",""))}</td>'
            f'<td>{w.badge_html(r.get("status") or UNKNOWN, tone)}</td>'
            f'<td>{fmt_money(r.get("value_vnd"))}</td></tr>')
    st.markdown(f'<div class="lg-tablewrap"><table class="lg-tbl"><thead>{head}</thead>'
                f'<tbody>{"".join(body)}</tbody></table></div>', unsafe_allow_html=True)
    sel = st.selectbox("Chọn hợp đồng", options=[r.get("id") for r in rows.values()], key="ctr_sel")
    if st.button("Mở chi tiết hợp đồng →", key="ctr_open", type="primary") and sel:
        st.session_state["lg_contract"] = sel
        set_page("contract_detail")
        st.rerun()


def contract_detail_page():
    cid = st.session_state.get("lg_contract")
    rows = svc.contracts()
    doc = rows.get(cid) if cid else None
    render_header(f"Hợp Đồng · {to_text(cid)}", "Chi tiết hợp đồng & liên kết lô")
    render_mobile_drawer()
    if not doc:
        st.markdown("### Không tìm thấy hợp đồng")
        if st.button("← Về danh sách hợp đồng"):
            set_page("contracts")
        return
    c = st.columns(4)
    c[0].markdown(f'<div style="font-size:13px;color:#64748b">Khách hàng</div><b>{w._esc(doc.get("customer"))}</b>',
                  unsafe_allow_html=True)
    c[1].markdown(f'<div style="font-size:13px;color:#64748b">Loại</div><b>{w._esc(doc.get("type",""))}</b>',
                  unsafe_allow_html=True)
    c[2].markdown(f'<div style="font-size:13px;color:#64748b">Trạng thái</div>{w.badge_html(doc.get("status") or UNKNOWN)}',
                  unsafe_allow_html=True)
    c[3].markdown(f'<div style="font-size:13px;color:#64748b">Giá trị</div><b>{fmt_money(doc.get("value_vnd"))}</b>',
                  unsafe_allow_html=True)
    sids = doc.get("shipment_ids") or doc.get("shipments") or []
    st.markdown("#### Lô hàng liên kết")
    if not sids:
        st.markdown('<div class="lg-card" style="color:#64748b">Chưa liên kết lô hàng nào với hợp đồng này.</div>',
                    unsafe_allow_html=True)
    else:
        for s in sids:
            st.markdown(f'<div class="lg-state"><div class="sl">{w._esc(s)}</div></div>', unsafe_allow_html=True)


def new_contract_page():
    render_header("Hợp Đồng Mới", "Tạo hợp đồng vận chuyển")
    render_mobile_drawer()
    if st.button("＋ Hợp đồng mới", key="nc_top", type="primary"):
        pass
    st.markdown(
        '<div class="lg-card" style="font-size:14px;color:#475569">Biểu mẫu tạo hợp đồng mới — '
        'phân hệ Hợp Đồng tiếp nhận tại màn hình chuyên biệt (khớp nghiệp vụ HDMB/PL).</div>',
        unsafe_allow_html=True)


# ------------------------------------------------------------------ FINANCE
def receive_page():
    render_header("Thu Tiền-Công Nợ", "Thu tiền khách hàng & theo dõi công nợ phải thu")
    render_mobile_drawer()
    st.markdown(w.section_title("💰", "Thu tiền & công nợ phải thu",
                                "Tập trung các khoản phải thu theo khách hàng"), unsafe_allow_html=True)
    _finance_guard()


def reconcile_page():
    render_header("Đối Soát Tài Chính", "Đối soát thu chi, công nợ từng lô / đối tác")
    render_mobile_drawer()
    st.markdown(w.section_title("🧮", "Đối soát tài chính",
                                "Rà soát trạng thái tài chính của các lô đang mở"), unsafe_allow_html=True)
    _finance_guard()


def partner_debt_page():
    render_header("Công Nợ Đối Tác", "Công nợ với đối tác / nhà cung cấp dịch vụ")
    render_mobile_drawer()
    st.markdown(w.section_title("🏢", "Công nợ đối tác", "Vị thế tài chính theo từng đối tác"),
                unsafe_allow_html=True)
    _finance_guard()


def ceo_page():
    render_header("Báo Cáo CEO", "Tổng hợp vận hành & tài chính cấp điều hành")
    render_mobile_drawer()
    st.markdown(w.section_title("📊", "Báo cáo điều hành (CEO)",
                                "Tổng quan toàn công ty theo thời gian"), unsafe_allow_html=True)
    _finance_guard()


def _finance_guard():
    rows = svc.dashboard_rows()
    summary = svc.build_summary()
    c = st.columns(4)
    c[0].markdown(w.kpi("📦", "Tổng lô", str(summary.get("total", 0))), unsafe_allow_html=True)
    c[1].markdown(w.kpi("🔔", "Cần chú ý", str(summary.get("attention", 0))), unsafe_allow_html=True)
    c[2].markdown(w.kpi("✅", "Hoàn tất", str(summary.get("done", 0))), unsafe_allow_html=True)
    c[3].markdown(w.kpi("🟡", "Đang mở", str(summary.get("open", 0))), unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<div class="lg-card" style="font-size:14px;color:#475569">Phân hệ <b>Tài chính</b> được vận hành '
        'tại màn hình chuyên biệt (thu tiền, đối soát, công nợ đối tác, báo cáo CEO). '
        'Dưới đây là tóm tắt trạng thái tài chính các lô.</div>', unsafe_allow_html=True)
    _finance_table(rows)


def _finance_table(rows):
    if not rows:
        return
    head = "<tr><th>Lô hàng</th><th>Khách hàng</th><th>Trạng thái tài chính</th></tr>"
    body = []
    for r in rows:
        fi_tone = {"ok": "green", "open": "amber", "review": "blue", "unknown": "gray"}.get(
            r.get("financial_flag") or "unknown", "gray")
        body.append(f'<tr><td><b>{w._esc(r.get("shipment_id"))}</b></td>'
                    f'<td>{w._esc(r.get("customer"))}</td>'
                    f'<td>{w.badge_html(r.get("financial_label") or UNKNOWN, fi_tone)}</td></tr>')
    st.markdown(f'<div class="lg-tablewrap"><table class="lg-tbl"><thead>{head}</thead>'
                f'<tbody>{"".join(body)}</tbody></table></div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ KINH DOANH misc
def context_page():
    render_header("Ngữ Cảnh", "Ngữ cảnh khách hàng & dự án")
    render_mobile_drawer()
    st.markdown(w.section_title("🧭", "Ngữ cảnh", "Bối cảnh làm việc với khách hàng / đối tác"),
                unsafe_allow_html=True)
    _empty_card("Ngữ cảnh")


def quote_page():
    render_header("Kinh Doanh-Báo Giá", "Báo giá vận chuyển cho khách hàng")
    render_mobile_drawer()
    st.markdown(w.section_title("💱", "Báo giá", "Các báo giá & trạng thái theo dõi"), unsafe_allow_html=True)
    rows = svc.quotes()
    if not rows:
        _empty_card("Báo giá")
        return
    head = "<tr><th>Mã báo giá</th><th>Khách hàng</th><th>Giá trị</th><th>Hạn hiệu lực</th></tr>"
    body = []
    for r in list(rows.values())[:30]:
        body.append(f'<tr><td><b>{w._esc(r.get("id") or r.get("quote_id"))}</b></td>'
                    f'<td>{w._esc(r.get("customer"))}</td>'
                    f'<td>{fmt_money(r.get("total"))}</td>'
                    f'<td>{w._esc(r.get("valid_until",""))}</td></tr>')
    st.markdown(f'<div class="lg-tablewrap"><table class="lg-tbl"><thead>{head}</thead>'
                f'<tbody>{"".join(body)}</tbody></table></div>', unsafe_allow_html=True)


def agreement_page():
    render_header("Thỏa Thuận", "Thỏa thuận hợp tác & khung giá")
    render_mobile_drawer()
    st.markdown(w.section_title("🤝", "Thỏa thuận", "Thỏa thuận với khách hàng / đối tác"), unsafe_allow_html=True)
    rows = svc.agreements()
    if not rows:
        _empty_card("Thỏa thuận")
        return
    for r in list(rows.values())[:20]:
        st.markdown(
            f'<div class="lg-state"><div class="sl">{w._esc(r.get("id"))} · '
            f'{w._esc(r.get("name") or r.get("title") or r.get("counterparty"))}</div>'
            f'<div class="sv">{w.badge_html(r.get("status") or UNKNOWN)}</div></div>',
            unsafe_allow_html=True)


# ------------------------------------------------------------------ TOOLS
def tariff_page():
    render_header("Tra Cứu Thuế-HS", "Tra cứu mã HS & thuế xuất nhập khẩu")
    render_mobile_drawer()
    st.markdown(w.section_title("🧾", "Tra cứu thuế - mã HS", "Tìm mã HS theo mô tả hàng hóa"),
                unsafe_allow_html=True)
    st.text_input("Mô tả hàng hóa / mã HS", key="tariff_q")
    st.info("Cơ sở dữ liệu thuế biểu được quản lý và tra cứu tại phân hệ Tra Cứu Thuế-HS.")


def notebook_page():
    render_header("Sổ Tay", "Kiến thức & sổ tay nghiệp vụ")
    render_mobile_drawer()
    st.markdown(w.section_title("📒", "Sổ tay", "Kiến thức, checklist, tài liệu nội bộ"), unsafe_allow_html=True)
    st.info("Sổ tay & kiến thức nghiệp vụ được quản lý tại phân hệ Sổ Tay.")


def translate_page():
    render_header("Dịch Thuật", "Hỗ trợ dịch thuật tài liệu")
    render_mobile_drawer()
    st.markdown(w.section_title("🌐", "Dịch thuật", "Dịch tài liệu thương mại"), unsafe_allow_html=True)
    st.text_area("Văn bản cần dịch", key="tr_input", height=150)
    st.button("Dịch", key="tr_go", type="primary")


# ------------------------------------------------------------------ ADMIN
def admin_page():
    render_header("Người Dùng", "Quản trị người dùng & phân quyền")
    render_mobile_drawer()
    st.markdown(w.section_title("👥", "Người dùng & vai trò",
                                "ADMIN / SUPPORT / SALE — phân quyền theo mô hình RBAC"),
                unsafe_allow_html=True)
    rows = svc.users()
    head = "<tr><th>Tài khoản</th><th>Tên hiển thị</th><th>Vai trò</th><th>Trạng thái</th></tr>"
    body = []
    for r in rows.values():
        tone = "green" if (r.get("active") is not False) else "gray"
        body.append(f'<tr><td><b style="color:#0f2a4a">{w._esc(r.get("username"))}</b></td>'
                    f'<td>{w._esc(r.get("display_name"))}</td>'
                    f'<td>{w.badge_html((r.get("role") or "").upper(), "violet")}</td>'
                    f'<td>{w.badge_html("HOẠT ĐỘNG" if tone=="green" else "KHÓA", tone)}</td></tr>')
    st.markdown(f'<div class="lg-tablewrap"><table class="lg-tbl"><thead>{head}</thead>'
                f'<tbody>{"".join(body)}</tbody></table></div>', unsafe_allow_html=True)
    st.caption(f'Đang đăng nhập: {actor()["username"]} ({actor()["role"].upper()})')


def _empty_card(label):
    st.markdown(
        f'<div class="lg-card" style="color:#64748b;font-size:14px">Chưa có dữ liệu {label.lower()} '
        f'được đồng bộ trong lần này. Khi có MongoDB thật, màn hình hiển thị dữ liệu '
        f'{label.lower()} trực tiếp từ nghiệp vụ.</div>', unsafe_allow_html=True)
