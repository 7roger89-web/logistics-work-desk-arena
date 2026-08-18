# FILE: views/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
from uuid import uuid4
import calendar 
import re

# --- IMPORT CHUẨN TỪ CORE SYSTEM ---
from core.config import STATUS_MAP_INV
from core.utils import get_shipment_business_date, parse_date, log_error, escape_html, safe_float
from core.logic import calculate_from_shipment, apply_financial_snapshot
from core.auth import has_permission
from core.database import load_data, load_archived_data, save_shipment_atomic, delete_shipment
from core.shipment_dashboard import (
    CRITICAL,
    FINANCIAL_OPEN,
    FINANCIAL_REVIEW,
    FINANCIAL_UNKNOWN,
    build_dashboard_summary,
    build_shipment_dashboard_view,
    filter_dashboard_views,
    sort_dashboard_views,
)
from views.shipment import ui_shipment_detail_tabs 

from core.getfly_reader import process_getfly_excel, get_kpi_summary
from core.database import load_quick_note, save_quick_note, load_tasks, add_task, toggle_task
from core.excel_utils import generate_getfly_excel, generate_commission_excel

def cached_load_data():
    return load_data()

def clean_client_name(name):
    if not name or name == "Unknown": return "Khách Lẻ"
    name = str(name).upper().strip()
    keywords = ["CÔNG TY TNHH MTV", "CÔNG TY TNHH", "CÔNG TY CỔ PHẦN", "CÔNG TY CP", "CTY TNHH", "CTY CP", "DOANH NGHIỆP TƯ NHÂN", "DNTN", "CHI NHÁNH", "THƯƠNG MẠI", "DỊCH VỤ", "XUẤT NHẬP KHẨU", "GROUP", "JSC", "CO.,LTD", "CÔNG TY"]
    for key in keywords: name = name.replace(key, "")
    return re.sub(' +', ' ', name).strip(" -.,").title()

# ==========================================
# DIALOG CÔNG CỤ NHANH
# ==========================================
@st.dialog("📝 SỔ TAY NHÁP (TEAM STICKY NOTE)")
def quick_note_dialog():
    st.caption("Dùng để dán tạm số Cont, SĐT tài xế... Đồng bộ cho cả team.")
    current_note, updated_at = load_quick_note()
    if updated_at:
        st.markdown(f"<div style='text-align:right; font-size:12px; color:gray; font-style:italic;'>🕒 Cập nhật: {updated_at}</div>", unsafe_allow_html=True)
    note_text = st.text_area("Nội dung ghi chú:", value=current_note, height=300, label_visibility="collapsed")
    if st.button("💾 LƯU SỔ TAY", type="primary", use_container_width=True):
        save_quick_note(note_text)
        st.success("✅ Đã lưu sổ tay!")
        st.rerun()

@st.dialog("🎯 GIAO VIỆC MỚI")
def quick_assign_task_dialog():
    TEAM_MEMBERS = ["Tất cả (Team)", "Thành", "Mến", "Linh"]
    t_content = st.text_area("📝 Nội dung công việc", placeholder="Ví dụ: Lấy lệnh DO...")
    c1, c2 = st.columns(2)
    t_assignee = c1.selectbox("👤 Giao cho ai?", TEAM_MEMBERS)
    t_deadline = c2.date_input("📅 Deadline (Hạn chót)", value=date.today())
    
    if st.button("🚀 XÁC NHẬN GIAO VIỆC", type="primary", use_container_width=True):
        if t_content.strip():
            add_task(t_content.strip(), t_assignee, t_deadline.strftime("%d/%m/%Y"))
            st.success(f"🎉 Đã giao việc cho {t_assignee}!")
            st.rerun()
        else: st.error("⚠️ Vui lòng nhập nội dung!")

# ==========================================
# HELPER HIỂN THỊ STATUS
# ==========================================
def get_rank_info_full(client_full_name):
    db_cust = st.session_state.get('db_customers', {})
    found_cust = None
    for c in db_cust.values():
        if c.get('name') == client_full_name:
            found_cust = c; break
    if not found_cust: return ("👤", "") 
    rank = found_cust.get('rank', 'Đồng')
    icon_map = {"Kim Cương": "💎", "Vàng": "🥇", "Bạc": "🥈", "Đồng": "👤"}
    return (icon_map.get(rank, "👤"), "")

def render_status_pill(label, color_code, is_active):
    opacity = "1" if is_active else "0.3"
    fw = "700" if is_active else "400"
    bg_map = {"#2E7D32": "#E8F5E9", "#1565C0": "#E3F2FD", "#7B1FA2": "#F3E5F5", "#C62828": "#FFEBEE", "#F57C00": "#FFF3E0", "#757575": "#EEEEEE"}
    bg = bg_map.get(color_code, "#F5F5F5") if is_active else "#F5F5F5"
    border = f"1px solid {color_code}40" if is_active else "1px solid #ddd"
    return f"<span style='display:inline-block; padding:2px 6px; border-radius:4px; font-size:10px; color:{color_code}; background-color:{bg}; opacity:{opacity}; font-weight:{fw}; border:{border}; margin-right:3px;'>{label}</span>"

def render_status_visual(ship_data):
    d = ship_data.get('data', {})
    has_docs = bool(d.get('1.2', {}).get('booking_no') or d.get('1.2', {}).get('mbl'))
    is_cleared = d.get('2.4', {}).get('customs_status', False)
    is_delivered = d.get('2.7', {}).get('is_delivered', False)
    summary = calculate_from_shipment(ship_data)
    rev = safe_float(summary.get('receivable', 0))
    debt = safe_float(summary.get('debt', 0))
    
    html_parts = []
    html_parts.append(render_status_pill("DOCS", "#2E7D32", has_docs))
    html_parts.append(render_status_pill("HQ", "#1565C0", is_cleared))
    html_parts.append(render_status_pill("GIAO", "#7B1FA2", is_delivered))
    
    if rev == 0: html_parts.append(render_status_pill("WAIT", "#757575", False))
    elif debt <= 1000: html_parts.append(render_status_pill("PAID", "#2E7D32", True))
    else: html_parts.append(render_status_pill(f"NỢ: {debt/1e6:.1f}M", "#C62828", True))
    return "".join(html_parts)


def _desk_badge(label, background, foreground="#172033"):
    return (
        f"<span style='display:inline-block; padding:3px 7px; border-radius:999px; "
        f"background:{background}; color:{foreground}; font-size:11px; font-weight:700; "
        f"border:1px solid {foreground}35; margin:1px 3px 1px 0;'>{escape_html(label)}</span>"
    )


def _desk_attention_filter(rows, selection):
    if selection in {"Tất cả", "__all__"}:
        return rows
    code_map = {
        "Quá free time": "FREE_TIME_OVERDUE",
        "Sắp hết free time": "FREE_TIME_SOON",
        "Sắp/quá hạn khách": "CUSTOMER_DEADLINE",
        "Thiếu thông tin": "MISSING_",
        "Nhà máy chưa đủ dữ liệu": "FACTORY_INFO_MISSING",
        "Tài chính cần theo dõi": "FINANCE_",
    }
    prefix = code_map.get(selection)
    if not prefix:
        return rows
    return [
        row for row in rows
        if any(str(alert.get("code", "")).startswith(prefix) for alert in row.get("alerts", []))
    ]


def _desk_money_label(metric, currency="VND"):
    """Format a financial read-model metric without turning UNKNOWN into zero."""

    if not isinstance(metric, dict):
        return "UNKNOWN"
    value = metric.get("value")
    status = str(metric.get("status") or "").upper()
    if value is None or status == "UNKNOWN":
        return "UNKNOWN"
    try:
        return f"{float(value):,.0f} {metric.get('currency') or currency}"
    except (TypeError, ValueError):
        return "UNKNOWN"


def _desk_source_context(row, data, route):
    """Return compact context facts that are already present in the shipment."""

    context = []
    customer = str(row.get("customer") or "Chưa có khách hàng")
    context.append(f"Khách: {customer}")
    owner = str(row.get("owner") or "Chưa phân công")
    context.append(f"Sale: {owner}")

    factory_count = row.get("factory_count")
    missing_factory_count = row.get("missing_factory_count") or 0
    if factory_count is None:
        context.append("Nhà máy: UNKNOWN")
    else:
        factory_label = f"{factory_count} nhà máy/lô con"
        if missing_factory_count:
            factory_label += f" · thiếu {missing_factory_count}"
        context.append(factory_label)

    doc_keys = (
        ("Booking", "booking_no"),
        ("MBL", "mbl"),
        ("HBL", "hbl"),
        ("Invoice", "invoice_no"),
    )
    known_docs = [label for label, key in doc_keys if route.get(key)]
    context.append("Chứng từ: " + (", ".join(known_docs) if known_docs else "chưa có trường chuẩn"))

    finance = data.get("3.4", {}) if isinstance(data, dict) else {}
    agency = finance.get("agency") if isinstance(finance, dict) else None
    context.append("Đại lý: có nguồn agency" if isinstance(agency, dict) else "Đại lý: chưa có nguồn chuẩn")
    return context


def _render_financial_explanation(row):
    """Expose the read-only financial projection and why it has its status."""

    projection = row.get("financial_projection") or {}
    if not isinstance(projection, dict):
        st.warning("Không có financial projection hợp lệ; không suy đoán số tiền.")
        return

    currency = str(projection.get("currency") or "VND")
    st.markdown(
        f"**Ý nghĩa hiện tại:** {escape_html(row.get('financial_status') or 'UNKNOWN')}  "
        f"· trạng thái UI: `{escape_html(row.get('financial_label') or 'UNKNOWN')}`",
        unsafe_allow_html=True,
    )
    m1, m2, m3 = st.columns(3)
    m1.metric("Phải thu còn lại", _desk_money_label((projection.get("receivable") or {}).get("outstanding"), currency))
    m2.metric("Phải trả theo agency", _desk_money_label((projection.get("payable") or {}).get("outstanding"), currency))
    m3.metric("Lợi nhuận dự kiến", _desk_money_label(projection.get("expected_profit"), currency))

    sources = projection.get("sources") or []
    if sources:
        st.caption("Nguồn và điều kiện tính")
        for source in sources:
            if not isinstance(source, dict):
                continue
            label = escape_html(source.get("label") or "Metric")
            status = escape_html(source.get("status") or "UNKNOWN")
            source_name = escape_html(source.get("source") or "Chưa có source")
            reason = escape_html(source.get("reason") or "")
            suffix = f" · {reason}" if reason else ""
            st.markdown(f"- **{label}** · `{status}` · {source_name}{suffix}", unsafe_allow_html=True)
    st.caption(
        "Chỉ đọc · không thay đổi ledger, payment, historical data hay canonical financial truth. "
        f"Nguồn projection: {escape_html(row.get('source') or 'chưa có')}."
    )


def _render_shipment_workdesk(all_ships, rows):
    """Render the shipment-first read-only operations queue."""

    st.markdown(
        "<div class='ops-section-kicker'>BẢNG VIỆC CHÍNH · DANH SÁCH LÔ HÀNG</div>"
        "<h2 class='ops-section-title'>Lô hàng cần xử lý</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Ưu tiên theo cảnh báo và deadline. Mỗi dòng trả lời nhanh: lô nào, đang chờ ai, bước tiếp theo là gì.")

    summary = build_dashboard_summary(rows)
    action_count = summary["critical"] + summary["warning"]
    st.markdown(
        f"""
        <div class='ops-summary-band' aria-label='Tổng quan vận hành'>
          <div><span class='ops-summary-label'>TỔNG LÔ</span><strong>{summary['total']}</strong><small>trong phạm vi hiện tại</small></div>
          <div class='ops-summary-focus'><span class='ops-summary-label'>CẦN XỬ LÝ</span><strong>{action_count}</strong><small>cảnh báo ưu tiên</small></div>
          <div><span class='ops-summary-label'>DEADLINE</span><strong>{summary['deadline_soon']}</strong><small>sắp hoặc quá hạn</small></div>
          <div><span class='ops-summary-label'>TÀI CHÍNH CẦN THEO DÕI</span><strong>{summary['financial_attention']}</strong><small>không phải số đã chốt</small></div>
          <div><span class='ops-summary-label'>THIẾU CONTEXT</span><strong>{summary['missing_info']}</strong><small>cần bổ sung dữ liệu</small></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    owners = sorted({str(row.get("owner") or "").strip() for row in rows if row.get("owner")})
    # Keep the requested owner filter discoverable without assigning it to rows.
    if "SALE Thành" not in owners:
        owners.insert(0, "SALE Thành")
    customers = sorted({str(row.get("customer") or "").strip() for row in rows if row.get("customer")})
    status_options = ["Tất cả"] + sorted({str(row.get("operational_status") or "").strip() for row in rows if row.get("operational_status")})
    financial_options = [
        ("Tất cả", None),
        ("Tài chính OK", "ok"),
        ("Đang mở", FINANCIAL_OPEN),
        ("Cần đối soát", FINANCIAL_REVIEW),
        ("UNKNOWN", FINANCIAL_UNKNOWN),
    ]

    with st.expander("🔎 Lọc & tìm trong queue", expanded=True):
        f1, f2, f3, f4, f5 = st.columns([1.4, 1.5, 1.5, 1.4, 1.6])
        owner_filter = f1.selectbox("Sale phụ trách", ["Tất cả"] + owners, key="dashboard_owner_filter")
        customer_filter = f2.selectbox("Khách hàng", ["Tất cả"] + customers, key="dashboard_customer_filter")
        attention_filter = f3.selectbox(
            "Cảnh báo",
            [
                "Tất cả",
                "Quá free time",
                "Sắp hết free time",
                "Sắp/quá hạn khách",
                "Thiếu thông tin",
                "Nhà máy chưa đủ dữ liệu",
                "Tài chính cần theo dõi",
            ],
            key="dashboard_attention_filter",
        )
        operational_filter = f4.selectbox(
            "Vận hành",
            status_options,
            format_func=lambda value: "Tất cả" if value == "Tất cả" else STATUS_MAP_INV.get(value, value),
            key="dashboard_operational_filter",
        )
        financial_filter_label = f5.selectbox(
            "Tài chính",
            [label for label, _ in financial_options],
            key="dashboard_financial_filter",
        )
        q1, q2, q3 = st.columns([1.5, 1.5, 3.0])
        only_actionable = q1.checkbox("Chỉ còn việc", value=False, key="dashboard_only_actionable")
        deadline_only = q2.checkbox("Chỉ deadline", value=False, key="dashboard_deadline_only")
        q3.caption("Search ở thanh phạm vi phía trên · financial status luôn là read-only projection.")

    filtered_rows = filter_dashboard_views(
        rows,
        owner=owner_filter,
        customer=customer_filter,
        operational_status=operational_filter,
        financial_flag=dict(financial_options).get(financial_filter_label),
        has_alert=True if only_actionable else None,
        deadline_soon=True if deadline_only else None,
        search=st.session_state.get("dashboard_search_query", ""),
    )
    filtered_rows = _desk_attention_filter(filtered_rows, attention_filter)
    filtered_rows = sort_dashboard_views(filtered_rows)
    st.markdown(
        f"<div class='ops-filter-note'><strong>{len(filtered_rows)}/{len(rows)} lô</strong> đang hiển thị · "
        "mở một dòng để đi thẳng vào Shipment 360 · các trạng thái UNKNOWN được giữ nguyên.</div>",
        unsafe_allow_html=True,
    )

    if not filtered_rows:
        st.info("📭 Không có lô hàng phù hợp với các bộ lọc hiện tại.")
        return

    for row in filtered_rows:
        row_sid = str(row.get("shipment_id") or "UNKNOWN")
        ship = all_ships.get(row_sid)
        if ship is None:
            ship = next(
                (
                    candidate
                    for candidate in all_ships.values()
                    if str(candidate.get("id") or candidate.get("shipment_id") or "") == row_sid
                ),
                None,
            )
        if not ship:
            continue
        sid = str(ship.get("id") or row_sid)
        data = ship.get("data", {})
        route = data.get("1.2", {}) if isinstance(data, dict) else {}
        if not isinstance(route, dict):
            route = {}
        top_alert = row.get("top_alert") or {}
        alert_color = {CRITICAL: ("#FDECEC", "#B42318"), "warning": ("#FFF4E5", "#9A6700"), "info": ("#EEF2FF", "#4657C8")}.get(top_alert.get("severity"), ("#F3F4F6", "#475467"))
        finance_color = {
            "ok": ("#EAF7EF", "#18794E"),
            FINANCIAL_OPEN: ("#FFF4E5", "#9A6700"),
            FINANCIAL_REVIEW: ("#EEF2FF", "#4657C8"),
            FINANCIAL_UNKNOWN: ("#FDECEC", "#B42318"),
        }.get(row.get("financial_flag"), ("#F3F4F6", "#475467"))

        context_bits = _desk_source_context(row, data, route)
        with st.container(border=True):
            st.markdown(
                f"<div class='ops-row-head'><span class='ops-row-id'>{escape_html(sid)}</span>"
                f"<span class='ops-row-customer'>{escape_html(row.get('customer') or 'Chưa có khách hàng')}</span>"
                f"<span class='ops-row-route'>{escape_html(route.get('pol') or '?')} → {escape_html(route.get('pod') or '?')}</span></div>",
                unsafe_allow_html=True,
            )
            c_main, c_ops, c_finance, c_action = st.columns([2.8, 1.5, 1.8, 1.25])
            with c_main:
                st.caption(
                    f"Sale: {row.get('owner', 'Chưa phân công')} · "
                    f"Cập nhật: {row.get('last_update_label', 'Chưa có')} · "
                    f"{escape_html(route.get('pol', '?'))} ➝ {escape_html(route.get('pod', '?'))}"
                )
                date_bits = [f"ETA: {row.get('arrival_date_label', 'Chưa có')}"]
                if row.get("required_date"):
                    date_bits.append(f"Hạn khách: {row.get('required_date_label')}")
                if row.get("promised_date"):
                    date_bits.append(f"Mốc hẹn: {row.get('promised_date_label')}")
                if row.get("planned_date"):
                    date_bits.append(f"Kế hoạch: {row.get('planned_date_label')}")
                st.caption(" · ".join(date_bits))
                st.caption(" · ".join(context_bits))
            with c_ops:
                st.markdown(_desk_badge(f"Vận hành: {row.get('operational_status_label')}", "#EEF2FF", "#4657C8"), unsafe_allow_html=True)
                if row.get("days_remaining") is not None:
                    free_label = f"Free time: {row['days_remaining']} ngày"
                    st.markdown(_desk_badge(free_label, alert_color[0], alert_color[1]), unsafe_allow_html=True)
                elif row.get("free_time_days") is None:
                    st.caption("Free time: UNKNOWN")
            with c_finance:
                st.markdown(_desk_badge(f"Tài chính: {row.get('financial_label')}", finance_color[0], finance_color[1]), unsafe_allow_html=True)
                st.caption(escape_html(row.get("financial_status")))
                with st.expander("Vì sao ra số này?", expanded=False):
                    _render_financial_explanation(row)
            with c_action:
                st.markdown("**MỞ HỒ SƠ LÔ 360°**")
                if st.button(sid, key=f"dashboard_open_360_{sid}", help="Mở Shipment 360", use_container_width=True):
                    st.session_state.active_shipment_id = sid
                    st.session_state.dashboard_active_shipment_id = sid
                    st.rerun()

            if top_alert:
                severity_icon = {CRITICAL: "🔴", "warning": "🟠", "info": "🔵"}.get(top_alert.get("severity"), "ℹ️")
                st.markdown(
                    f"<div class='ops-next-action'>{severity_icon} <strong>Việc tiếp theo:</strong> {escape_html(top_alert.get('label'))} — "
                    f"{escape_html(top_alert.get('detail'))}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("<div class='ops-next-action ops-next-action-ok'>✅ Chưa có cảnh báo cần xử lý.</div>", unsafe_allow_html=True)

def ui_dashboard():
    st.markdown("""
    <style>
        .ops-section-kicker { color: #0B6E99; font-size: 0.66rem; font-weight: 800; letter-spacing: 0.14em; margin-top: 0.25rem; }
        .ops-section-title { color: #102A43; font-size: 1.55rem; line-height: 1.15; margin: 0.18rem 0 0.35rem; }
        h1.ops-page-title { color: #102A43; font-size: 1.55rem !important; line-height: 1.15 !important; margin: 0.18rem 0 0.35rem !important; }
        .ops-summary-band { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); border: 1px solid #D9E2EC; border-radius: 8px; background: #FFFFFF; overflow: hidden; margin: 0.8rem 0 1rem; }
        .ops-summary-band > div { padding: 0.78rem 0.9rem; border-right: 1px solid #D9E2EC; }
        .ops-summary-band > div:last-child { border-right: 0; }
        .ops-summary-band strong { display: block; color: #102A43; font-size: 1.42rem; line-height: 1.1; margin-top: 0.18rem; }
        .ops-summary-band small { display: block; color: #667085; font-size: 0.69rem; margin-top: 0.22rem; }
        .ops-summary-label { color: #667085; display: block; font-size: 0.64rem; font-weight: 800; letter-spacing: 0.08em; }
        .ops-summary-focus { background: #FFF8EB; }
        .ops-summary-focus strong { color: #9A6700; }
        .ops-filter-note { color: #475467; font-size: 0.82rem; padding: 0.52rem 0.72rem; border-left: 3px solid #0B6E99; background: #F0F7FA; margin: 0.7rem 0; }
        .ops-row-head { display: flex; align-items: baseline; gap: 0.55rem; flex-wrap: wrap; padding-bottom: 0.18rem; }
        .ops-row-id { color: #102A43; font-size: 1.02rem; font-weight: 800; letter-spacing: 0.01em; }
        .ops-row-customer { color: #344054; font-size: 0.9rem; font-weight: 650; }
        .ops-row-route { color: #667085; font-size: 0.76rem; margin-left: auto; }
        .ops-next-action { border-top: 1px solid #E7EEF3; color: #475467; font-size: 0.82rem; line-height: 1.4; padding-top: 0.52rem; margin-top: 0.38rem; }
        .ops-next-action-ok { color: #18794E; }
        .ops-unknown { color: #9A6700; }
        div[data-testid="stVerticalBlock"] button { border: 1px solid #C8D4DF; font-weight: 700; color: #102A43; min-height: 2.45rem; }
        div[data-testid="stVerticalBlock"] button:hover { border-color: #0B6E99; color: #0B6E99; }
        div[data-testid="stExpander"] { border: none; box-shadow: none; }
        div[data-testid="stExpander"] details { border: 1px solid #D9E2EC; background: white; border-radius: 7px; }
        @media (max-width: 900px) {
            .ops-summary-band { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .ops-summary-band > div { border-bottom: 1px solid #D9E2EC; }
            .ops-row-route { margin-left: 0; width: 100%; }
        }
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after { transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; }
        }
    </style>
    """, unsafe_allow_html=True)

    # ==============================================================
    # HEADER & CÔNG CỤ NHANH TRÊN CÙNG
    # ==============================================================
    c1, c_btn1, c_btn2, c_tog = st.columns([2.5, 1.2, 1.2, 1.1])
    c1.markdown(
        "<div class='ops-section-kicker'>KHU VỰC QUẢN LÝ VẬN HÀNH</div>"
        "<h1 class='ops-section-title ops-page-title'>Phòng điều khiển lô hàng</h1>"
        "<div style='color:#667085;font-size:0.82rem;'>Bảng việc là mặt tiền · Tài chính là bối cảnh có nguồn</div>",
        unsafe_allow_html=True,
    )
    if c_btn1.button("➕ Giao Việc Nhanh", use_container_width=True): quick_assign_task_dialog()
    if c_btn2.button("📝 Sổ Tay Nháp", use_container_width=True): quick_note_dialog()
    view_archive = c_tog.toggle("Lưu Trữ", value=False)
    
    # ==============================================================
    # BỘ LỌC THỜI GIAN VÀ TÌM KIẾM (HIỂN THỊ CHÍNH GIỮA MÀN HÌNH)
    # ==============================================================
    with st.expander("🔎 BỘ LỌC DỮ LIỆU & THỜI GIAN", expanded=False):
        f1, f2, f3, f4 = st.columns([2, 2, 3, 2])
        
        search_query = f1.text_input("Tìm kiếm:", placeholder="Mã lô, khách, Sale, trạng thái...", key="dashboard_search_query")
        
        # Chế độ thời gian, mặc định là "Tháng này"
        time_mode = f2.selectbox(
            "Khoảng thời gian:", 
            ["Tháng này", "Tháng trước", "Năm nay", "Thời gian khác", "Tất cả"], 
            index=4,
            key="dashboard_time_mode",
        )

        today = date.today()
        start_date, end_date = None, None
        
        if time_mode == "Tháng này":
            start_date = date(today.year, today.month, 1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = date(today.year, today.month, last_day)
            f3.info(f"Đang hiển thị: **{start_date.strftime('%d/%m/%Y')}** đến **{end_date.strftime('%d/%m/%Y')}**")
            
        elif time_mode == "Tháng trước":
            first_this_month = date(today.year, today.month, 1)
            end_date = first_this_month - timedelta(days=1)
            start_date = date(end_date.year, end_date.month, 1)
            f3.info(f"Đang hiển thị: **{start_date.strftime('%d/%m/%Y')}** đến **{end_date.strftime('%d/%m/%Y')}**")
            
        elif time_mode == "Năm nay":
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)
            f3.info(f"Đang hiển thị toàn bộ năm {today.year}")
            
        elif time_mode == "Thời gian khác":
            date_range = f3.date_input(
                "Chọn khoảng ngày tùy chỉnh:",
                value=(date(today.year, today.month, 1), today),
                format="DD/MM/YYYY",
                key="dashboard_custom_date_range",
            )
            if isinstance(date_range, tuple):
                if len(date_range) == 2:
                    start_date, end_date = date_range
                elif len(date_range) == 1:
                    start_date = end_date = date_range[0]
        else:
            f3.success("Đang hiển thị TẤT CẢ các lô hàng trong lịch sử.")

        status_filter = f4.selectbox("Trạng thái:", ["Tất cả", "Active", "Done"], index=0, key="dashboard_status_filter")

    # --- BẢNG CẢNH BÁO VIỆC CẦN LÀM & LỊCH SỬ ---
    try: tasks = load_tasks()
    except: tasks = []
    
    pending_tasks = [t for t in tasks if not t.get('done', False)]
    completed_tasks = [t for t in tasks if t.get('done', False)]
    
    col_pend, col_hist = st.columns(2)
    
    with col_pend:
        with st.expander(f"📋 Bảng Việc Đang Chờ ({len(pending_tasks)})", expanded=False):
            if pending_tasks:
                for t in pending_tasks:
                    col_chk, col_txt = st.columns([0.08, 0.92])
                    is_done = col_chk.checkbox("Đánh dấu đã xong", value=False, label_visibility="collapsed", key=f"pend_chk_{t['_id']}")
                    if is_done:
                        toggle_task(t['_id'], True)
                        st.rerun()
                    
                    assignee = escape_html(t.get('assignee', '').strip())
                    badge = ""
                    if assignee:
                        if "Tất cả" in assignee or "Team" in assignee:
                            badge = f"<span style='background:#E8F5E9; color:#2E7D32; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:800; border:1px solid #A5D6A7; margin-left:10px;'>👥 TEAM</span>"
                        else:
                            badge = f"<span style='background:#FFEBEE; color:#C62828; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:900; border:1px solid #FFCDD2; margin-left:10px;'>👤 {assignee.upper()}</span>"

                    col_txt.markdown(f"<div style='font-size:14px; font-weight: 500; color: #0F2C59; padding-top:4px;'>{escape_html(t.get('content'))}{badge}</div>", unsafe_allow_html=True)
                    st.markdown("<hr style='margin: 4px 0px; opacity: 0.2;'>", unsafe_allow_html=True)
            else:
                st.caption("🎉 Tuyệt vời! Team hiện không có công việc nào tồn đọng.")

    with col_hist:
        with st.expander(f"🕒 Lịch Sử Đã Xong ({len(completed_tasks)})", expanded=False):
            if completed_tasks:
                recent_completed = sorted(completed_tasks, key=lambda x: str(x.get('_id')), reverse=True)[:20]
                for t in recent_completed:
                    col_chk, col_txt = st.columns([0.08, 0.92])
                    is_undone = col_chk.checkbox("Giữ trạng thái đã xong", value=True, label_visibility="collapsed", key=f"hist_chk_{t['_id']}")
                    if not is_undone:
                        toggle_task(t['_id'], False)
                        st.rerun()
                    
                    assignee = escape_html(t.get('assignee', '').strip())
                    badge = f"<span style='font-size:10px; opacity:0.5; margin-left:10px;'>({assignee})</span>" if assignee else ""

                    col_txt.markdown(f"<div style='font-size:14px; color: #999; text-decoration: line-through; padding-top:4px;'>{escape_html(t.get('content'))}{badge}</div>", unsafe_allow_html=True)
                    st.markdown("<hr style='margin: 4px 0px; opacity: 0.2;'>", unsafe_allow_html=True)
            else:
                st.caption("Chưa có công việc nào hoàn thành.")
    
    st.markdown("---")
    
    # ==============================================================
    # LOAD DỮ LIỆU & ÁP DỤNG BỘ LỌC
    # ==============================================================
    if 'db_shipments' not in st.session_state or not st.session_state.db_shipments:
        st.session_state.db_shipments = cached_load_data()
    if view_archive and 'db_archive' not in st.session_state:
        st.session_state.db_archive = load_archived_data()
    raw_data = st.session_state.get('db_archive', {}) if view_archive else st.session_state.get('db_shipments', {})
    
    all_ships = {}
    iterable = raw_data.values() if isinstance(raw_data, dict) else raw_data
    for item in iterable:
        sid = str(item.get('id') or f"UNKNOWN_{id(item)}")
        item['client_short'] = clean_client_name(str(item.get('customer') or "Unknown"))
        item['client_full'] = str(item.get('customer') or "Unknown")
        if 'data' not in item: item['data'] = {}
        for k in ['0.0','1.2','2.4','2.6','2.7','3.4','entrustment']: 
            if k not in item['data']: item['data'][k]={}
        item['status'] = str(item.get('status', '')).strip() or item['data']['0.0'].get('st', 'wait')
        all_ships[sid] = item
    if not view_archive:
        st.session_state.db_shipments = all_ships
    
    ships_filtered = {}
    for sid, ship in all_ships.items():
        created_dt = get_shipment_business_date(ship)
        keep = True
        
        # Áp dụng bộ lọc thời gian
        if time_mode != "Tất cả":
            if created_dt is None: 
                keep = False
            else:
                if start_date and created_dt < start_date: keep = False
                if end_date and created_dt > end_date: keep = False
        
        is_done = ship['status'] in ['done', 'Done', 'Hoàn thành']
        if status_filter == "Active" and is_done: keep = False
        if status_filter == "Done" and not is_done: keep = False
        
        if search_query:
            q = search_query.lower()
            if q not in sid.lower() and q not in str(ship.get('customer')).lower(): keep = False
        
        if keep: ships_filtered[sid] = ship

    # ==============================================================
    # MAIN TABS CỦA DASHBOARD
    # ==============================================================
    t_board, t_cust, t_gf, t_comm = st.tabs(["📋 DASHBOARD", "🏆 TOP KHÁCH", "🔗 GETFLY", "💰 HOA HỒNG"])
    
    with t_board:
        active_sid = st.session_state.get('dashboard_active_shipment_id') or st.session_state.get('active_shipment_id')
        if active_sid and str(active_sid) in all_ships:
            ship_data = all_ships[str(active_sid)]
            if str(active_sid) not in ships_filtered and time_mode != "Tất cả":
                st.info("Lô hàng đang mở không nằm trong bộ lọc hiện tại; bạn vẫn có thể xem và đóng chi tiết.")
            with st.container(border=True):
                can_edit = has_permission("shipment_edit")
                can_delete = has_permission("shipment_delete")
                c_head, c_save, c_del, c_close = st.columns([3, 1.5, 1.5, 1])
                c_head.markdown(f"#### 📂 {active_sid}")
                if c_save.button("💾 LƯU", key="btn_save_top", type="primary", use_container_width=True, disabled=not can_edit):
                    apply_financial_snapshot(ship_data)
                    if save_shipment_atomic(ship_data, expected_version=ship_data.get("version")):
                        st.session_state.needs_refresh = True
                        st.toast("Đã lưu thành công!")
                        st.rerun()
                    st.error(st.session_state.get("last_db_error") or "Không thể lưu dữ liệu.")
                
                if c_del.button("🗑️ XÓA", key="btn_del_top", type="secondary", use_container_width=True, disabled=not can_delete):
                    st.session_state.confirm_delete_sid = active_sid; st.rerun()
                
                return_to_queue = bool(st.session_state.get("review_queue_return"))
                return_to_finance = bool(st.session_state.get("finance_review_return"))
                if c_close.button("← Queue" if return_to_queue else "❌", key="btn_close_top", use_container_width=True):
                    st.session_state.active_shipment_id = None
                    st.session_state.dashboard_active_shipment_id = None
                    if return_to_finance:
                        st.session_state.active_page = "Đối Soát Tài Chính"
                        st.session_state.finance_review_return = False
                    elif return_to_queue:
                        st.session_state.active_page = "Việc Cần Xử Lý"
                        st.session_state.review_queue_return = False
                    st.rerun()

                if st.session_state.get('confirm_delete_sid') == active_sid:
                    st.warning("Lô sẽ được đưa vào thùng lưu trữ và vẫn còn trong audit log.")
                    col_y, col_n = st.columns(2)
                    if col_y.button("✅ XÁC NHẬN XÓA", key="confirm_yes"):
                        if delete_shipment(active_sid):
                            if active_sid in st.session_state.db_shipments: del st.session_state.db_shipments[active_sid]
                            st.success("Đã xóa lô hàng."); st.session_state.active_shipment_id = None; st.session_state.dashboard_active_shipment_id = None; st.session_state.confirm_delete_sid = None; st.rerun()
                    if col_n.button("Hủy bỏ", key="confirm_no"): st.session_state.confirm_delete_sid = None; st.rerun()

                st.divider()
                if can_edit:
                    ui_shipment_detail_tabs(active_sid, ship_data)
                else:
                    st.info("Tài khoản hiện tại chỉ có quyền xem.")
                    st.json(ship_data, expanded=False)
                st.divider()

        dashboard_rows = [
            build_shipment_dashboard_view(ship, today=today)
            for ship in ships_filtered.values()
        ]
        _render_shipment_workdesk(all_ships, dashboard_rows)

    with t_cust:
        if ships_filtered:
            df = pd.DataFrame(ships_filtered.values())
            summaries = [calculate_from_shipment(ship) for ship in ships_filtered.values()]
            df['profit'] = [safe_float(item.get('profit', 0)) for item in summaries]
            df['revenue'] = [safe_float(item.get('revenue_net', 0)) for item in summaries]
            grp = df.groupby('client_short')[['profit', 'revenue']].sum().reset_index().sort_values('profit', ascending=False)
            
            total_rev = grp['revenue'].sum()
            total_prof = grp['profit'].sum()

            st.markdown(f"##### 🏆 Xếp hạng Khách ({time_mode})")
            m1, m2 = st.columns(2)
            m1.metric("💰 Tổng Doanh Thu", f"{total_rev:,.0f}".replace(",", ".") + " ₫")
            m2.metric("📈 Tổng Lợi Nhuận", f"{total_prof:,.0f}".replace(",", ".") + " ₫")
            st.divider()

            st.dataframe(
                grp, 
                column_config={
                    "client_short": "Khách Hàng", 
                    "profit": st.column_config.NumberColumn("Lợi Nhuận", format="%.0f ₫"), 
                    "revenue": st.column_config.NumberColumn("Doanh Thu", format="%.0f ₫")
                }, 
                use_container_width=True, hide_index=True, height=500
            )
        else: st.info("Không có dữ liệu trong khoảng thời gian này.")

    with t_gf:
        sub_t1, sub_t2 = st.tabs(["📊 Phân tích DSDH", "📤 Xuất GetFly"])
        with sub_t1:
            uploaded_file = st.file_uploader("Upload file 'Danh sách đơn hàng' (DSDH.xlsx)", type=['xlsx'])
            if uploaded_file:
                df_gf, error_gf = process_getfly_excel(uploaded_file)
                if error_gf: 
                    st.error(error_gf)
                else:
                    rev, profit, orders = get_kpi_summary(df_gf)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Doanh Thu GF", f"{rev:,.0f}"); m2.metric("Lợi Nhuận GF", f"{profit:,.0f}"); m3.metric("Số Đơn", f"{orders}")
                    st.dataframe(df_gf, use_container_width=True)
                    
                    st.divider()
                    if st.button("🚀 Ghi Nhận Dữ Liệu Này Vào Bảng Điều Khiển", type="primary", use_container_width=True):
                        with st.spinner("Đang đồng bộ đơn hàng vào Database..."):
                            success_count = 0
                            grouped = df_gf.groupby('order_id')
                            
                            for oid, group in grouped:
                                sid = str(oid).strip()
                                if sid not in st.session_state.db_shipments:
                                    first_row = group.iloc[0]
                                    cust_name = str(first_row.get('customer_name', 'Khách Lẻ')).strip()
                                    order_date = str(first_row.get('order_date', date.today()))
                                    matched_customer_id = next((cid for cid, customer in st.session_state.get('db_customers', {}).items() if str(customer.get('name', '')).strip().lower() == cust_name.lower()), '')

                                    details = []
                                    for _, row in group.iterrows():
                                        qty = safe_float(row.get('qty', 1)) or 1
                                        unit_price = safe_float(row.get('price', 0))
                                        line_revenue = safe_float(row.get('revenue', 0))
                                        if unit_price <= 0 and line_revenue > 0:
                                            unit_price = line_revenue / qty
                                        product_code = str(row.get('product_code', 'DVK')).strip()
                                        if product_code.lower() in {'', 'nan', 'none'}:
                                            product_code = 'DVK'
                                        product_name = str(row.get('product_name', 'Dịch vụ')).strip()
                                        if product_name.lower() in {'', 'nan', 'none'}:
                                            product_name = 'Dịch vụ Logistics'
                                        product_note = str(row.get('product_note', '')).strip()
                                        if product_note.lower() in {'nan', 'none', 'null'}:
                                            product_note = ''
                                        details.append({
                                            "id": str(uuid4()),
                                            "name_full": product_name,
                                            "display_name": product_name,
                                            "code": product_code,
                                            "qty": qty,
                                            "cost": safe_float(row.get('cost', 0)),
                                            "price": unit_price,
                                            "vat_line": 0,
                                            "note": product_note,
                                        })
                                    
                                    raw_status = str(first_row.get('status', '')).strip().lower()
                                    internal_status = 'done' if any(token in raw_status for token in ['hoàn thành', 'completed', 'done']) else 'pending'
                                    new_ship = {
                                        "id": sid,
                                        "shipment_id": sid,
                                        "customer": cust_name,
                                        "client": cust_name,
                                        "customer_id": matched_customer_id,
                                        "status": internal_status,
                                        "data": {
                                            "0.0": {"created_at": order_date, "st": internal_status, "mode": "Sea", "source_status": str(first_row.get("status", ""))},
                                            "1.2": {}, "2.4": {}, "2.6": {}, "2.7": {}, "entrustment": {},
                                            "3.4": {
                                                "details": details,
                                                "payments": [],
                                                "commission": {},
                                                "out": sum([safe_float(d['price']) * safe_float(d['qty']) for d in details]),
                                                "in": sum([safe_float(d['cost']) * safe_float(d['qty']) for d in details])
                                            }
                                        }
                                    }
                                    
                                    apply_financial_snapshot(new_ship)
                                    if save_shipment_atomic(new_ship):
                                        st.session_state.db_shipments[sid] = new_ship
                                        success_count += 1
                                        
                            st.success(f"✅ Đã import thành công {success_count} lô hàng mới từ GetFly vào cơ sở dữ liệu!")
                            st.session_state.needs_refresh = True
                            st.rerun()
                    
        with sub_t2:
            st.caption("Xuất dữ liệu từ phần mềm này ra Excel để nạp vào GetFly.")
            c1, c2 = st.columns(2)
            
            ship_map_display = {}
            for s in all_ships.values():
                display_str = f"{s['id']} - {s['client_short']}"
                ship_map_display[display_str] = s['id']
            
            ship_opts = list(ship_map_display.keys())
            sel_specific_ships = st.multiselect("🎯 Chọn lô hàng cụ thể (Ưu tiên):", ship_opts, key="gf_specific_ships")
            
            cli_opts = sorted(list(set([s['client_full'] for s in all_ships.values()])))
            gf_cli = c1.multiselect("Lọc theo Khách (Nếu chưa chọn lô)", cli_opts, key="gf_c")
            gf_m = c2.checkbox("Chỉ tháng này?", value=False, key="gf_m")
            
            if st.button("📥 Tạo File Import GetFly"):
                target = []
                if sel_specific_ships:
                    selected_ids = [ship_map_display[x] for x in sel_specific_ships]
                    for sid in selected_ids:
                        if sid in all_ships: target.append((sid, all_ships[sid]))
                else:
                    now = datetime.now()
                    for sid, s in all_ships.items():
                        if gf_cli and s['client_full'] not in gf_cli: continue
                        if gf_m:
                            created = get_shipment_business_date(s)
                            if not created or created.month != now.month or created.year != now.year: continue
                        target.append((sid, s))
                
                if target:
                    target_dict = dict(target)
                    assignee_name = st.session_state.get("current_user", {}).get("display_name", "")
                    xls = generate_getfly_excel(target_dict, assignee_name=assignee_name, customers_dict=st.session_state.get("db_customers", {}))
                    if xls: st.download_button("Download Getfly_Import.xlsx", xls, "Getfly_Import.xlsx")
                else: st.warning("Không có dữ liệu phù hợp với bộ lọc.")

    with t_comm:
        st.markdown(f"##### 💰 Báo Cáo Hoa Hồng ({time_mode})")
        comm_data = []
        for sid, s in ships_filtered.items():
            comm_info = s['data']['3.4'].get('commission', {})
            val = safe_float(comm_info.get('total', 0))
            if val > 0:
                comm_data.append({"Mã Lô": sid, "Khách Hàng": s['client_short'], "Hoa Hồng": val, "Ghi Chú": comm_info.get('note', '')})
        if comm_data:
            df_comm = pd.DataFrame(comm_data)
            st.metric("Tổng Hoa Hồng", f"{df_comm['Hoa Hồng'].sum():,.0f} ₫")
            st.dataframe(df_comm, column_config={"Hoa Hồng": st.column_config.NumberColumn(format="%d ₫")}, use_container_width=True, hide_index=True)
            if st.button("📥 Tải Excel Hoa Hồng"):
                xls = generate_commission_excel([(item['Mã Lô'], ships_filtered[item['Mã Lô']]) for item in comm_data])
                if xls: st.download_button("Download Commission.xlsx", xls, "Commission.xlsx")
        else: st.info("Không có hoa hồng trong khoảng thời gian này.")
