"""LOGI-GOOD EXACT — pages of the shell.

VẬN HÀNH pages (home/tasks/shipments/new/tracking) and thin wrappers that
present the other real modules (khách hàng, hợp đồng, tài chính, …) inside the
Logi-good shell.  All numbers/rows come from the real read model
(core.shipment_dashboard / core.readiness / session caches) — this module never
invents values and never writes to the database.
"""
from __future__ import annotations

import datetime
from typing import Any, Mapping

import streamlit as st

from core.auth import current_user, has_permission
from views.lg_core import (
    MUTED,
    NAVY_900,
    UNKNOWN_LABEL,
    a,
    badge,
    date_label,
    esc,
    fmt_vnd,
    link_url,
    money_number,
    pill,
    section_title,
    stat_cell,
    text,
    today_vn,
    tone_for_status,
)

# ---------------------------------------------------------------------------
# Real data helpers
# ---------------------------------------------------------------------------
def _db() -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]]:
    ships = st.session_state.get("db_shipments", {}) or {}
    customers = st.session_state.get("db_customers", {}) or {}
    contracts = st.session_state.get("db_contracts", {}) or {}
    return ships, customers, contracts


def _dashboard_rows(ships: Mapping[str, Any]) -> list[dict[str, Any]]:
    from core.shipment_dashboard import build_shipment_dashboard_view  # noqa: PLC0415

    today = datetime.date.today()
    rows: list[dict[str, Any]] = []
    for ship in ships.values():
        if not isinstance(ship, Mapping):
            continue
        try:
            rows.append(build_shipment_dashboard_view(ship, today=today))
        except Exception:  # noqa: BLE001  (defensive; one bad doc must not kill page)
            continue
    return rows


def _readiness_map(ships: Mapping[str, Any]) -> dict[str, Any]:
    """Readiness per active shipment id -> (results, next_action)."""
    from core.readiness import get_all_readiness, derive_next_action  # noqa: PLC0415
    from core.shipment_dashboard import build_shipment_summary  # noqa: PLC0415

    out: dict[str, Any] = {}
    for sid, ship in ships.items():
        if not isinstance(ship, Mapping):
            continue
        status = str(ship.get("status") or "").strip().casefold()
        if status in ("done", "cancel"):
            continue
        try:
            summary = build_shipment_summary(ship)
            results = get_all_readiness(ship, summary)
            out[str(sid)] = (results, derive_next_action(ship, results))
        except Exception:  # noqa: BLE001
            continue
    return out


def _user_greeting() -> str:
    user = current_user() or {}
    return text(user.get("display_name") or user.get("username"), "bạn")


def _support_name(ship: Mapping[str, Any]) -> str:
    from views.lg_core import first_value  # noqa: PLC0415

    return text(
        first_value(ship, ("support_owner", "support", "ops_owner", "customer_support")),
        "Chưa phân công",
    )


def _money_known(value: Any) -> bool:
    num = money_number(value)
    return num is not None


# ---------------------------------------------------------------------------
# TỔNG QUAN CÔNG VIỆC
# ---------------------------------------------------------------------------
def home_page() -> None:
    # The dashboard never owns a shipment focus: clear any stale workspace id so
    # later internal reruns cannot be mistaken for a legacy workspace jump.
    st.session_state.active_shipment_id = None
    st.session_state.dashboard_active_shipment_id = None
    ships, _customers, _contracts = _db()
    rows = _dashboard_rows(ships)

    active_rows = [r for r in rows if not r.get("is_complete")]
    done_rows = [r for r in rows if r.get("is_complete")]
    critical_rows = [r for r in rows if (r.get("top_alert") or {}).get("severity") == "critical"]
    active = len(active_rows)
    n_pending = sum(1 for r in active_rows if r.get("operational_status") == "pending")
    n_wait = sum(1 for r in active_rows if r.get("operational_status") == "wait")
    n_done_today = sum(
        1 for r in done_rows if r.get("last_update") and r["last_update"] == datetime.date.today()
    )
    over_free = [
        r for r in active_rows
        if any(al.get("code") in ("FREE_TIME_OVERDUE", "CUSTOMER_DEADLINE_OVERDUE", "CUSTOMER_DEADLINE_RISK")
               for al in r.get("alerts", []) if isinstance(al, Mapping))
    ]
    # real money aggregation (KNOWN only — UNKNOWN stays UNKNOWN)
    receivable = [r for r in rows if r.get("financial_projection")]
    total_due: float | None = None
    total_pay: float | None = None
    due_known = pay_known = False
    for row in rows:
        fp = row.get("financial_projection") or {}
        recv = fp.get("receivable") or {}
        out_metric = recv.get("outstanding") or {}
        if out_metric.get("status") == "KNOWN" and _money_known(out_metric.get("value")):
            due_known = True
            value = money_number(out_metric.get("value"))
            if value is not None and value > 0:
                total_due = (total_due or 0.0) + value
        pay = fp.get("payable") or {}
        pay_out = pay.get("outstanding") or {}
        if pay_out.get("status") == "KNOWN" and _money_known(pay_out.get("value")):
            pay_known = True
            value = money_number(pay_out.get("value"))
            if value is not None and value > 0:
                total_pay = (total_pay or 0.0) + value
    due_label = "—" if not due_known else (fmt_vnd(total_due) if total_due else "0 ₫")
    pay_label = "—" if not pay_known else (fmt_vnd(total_pay) if total_pay else "0 ₫")

    now = today_vn()
    user = _user_greeting()
    st.markdown(
        f"<div class='lg-hero'><span style='position:absolute;right:-60px;top:-60px;width:240px;height:240px;"
        f"border-radius:50%;background:rgba(255,255,255,.08);'></span>"
        f"<span style='position:absolute;right:40px;bottom:-40px;width:140px;height:140px;border-radius:50%;"
        f"background:rgba(255,255,255,.05);'></span>"
        f"<p class='kicker'>{esc(now)} · Ca sáng</p>"
        f"<h1>Hôm nay tôi cần làm gì?</h1>"
        f"<p>Xin chào <b style='color:#fff'>{esc(user)}</b> — theo dõi sát các lô đang chạy, "
        f"xử lý việc thiếu thông tin và chốt công nợ đúng hạn.</p>"
        f"<div class='actions'>"
        f"<a class='btn-white' href='{link_url('tasks')}'>XỬ LÝ NGAY →</a>"
        f"<a class='btn-ghost' href='{link_url('shipments')}'>Mở danh sách lô</a>"
        f"</div></div>",
        unsafe_allow_html=True,
    )
    st.write("")

    # Red banner for the most critical overdue item (real readiness/alert)
    if critical_rows:
        top = critical_rows[0]
        alert = top.get("top_alert") or {}
        sid = str(top.get("shipment_id") or "")
        st.markdown(
            f"<div class='lg-banner red'><span class='ic' style='background:#dc2626;'>!</span>"
            f"<span class='txt'><small>Cảnh báo đỏ</small>"
            f"<b>{esc(alert.get('label') or 'Việc quá hạn')} · {esc(sid)}</b>"
            f"<span>{esc(alert.get('detail') or '')} — Khách: {esc(top.get('customer') or UNKNOWN_LABEL)}</span></span>"
            f"<a class='lg-btn' style='min-height:44px;' href='{link_url('shipment', sid=sid, tab='lay-hang')}'>"
            f"XỬ LÝ NGAY</a></div>",
            unsafe_allow_html=True,
        )
        st.write("")

    # ---- VIỆC TIẾP THEO (real readiness buckets) ----
    readiness = _readiness_map(ships)
    bucket = {
        "pickup": 0, "export": 0, "customs": 0, "delivery": 0, "finance": 0,
    }
    docs_missing = 0
    for sid, (results, _action) in readiness.items():
        ship = ships.get(sid) or {}
        status = str(ship.get("status") or "").casefold()
        if status in ("done", "cancel"):
            continue
        stage_flags: dict[str, bool] = {}
        for res in results:
            key = str(res.stage).lower()
            if key == "pickup":
                stage_flags["pickup"] = not res.ready
            elif key == "xuất khẩu":
                stage_flags["export"] = not res.ready and not stage_flags.get("pickup")
            elif key == "hải quan":
                stage_flags["customs"] = not res.ready
            elif key == "giao hàng":
                stage_flags["delivery"] = not res.ready
        missing = [res for res in results if not res.ready]
        first_missing = missing[0].stage.lower() if missing else ""
        key = {"pickup": "pickup", "xuất khẩu": "export", "hải quan": "customs", "giao hàng": "delivery"}.get(first_missing)
        if key:
            bucket[key] += 1
        if not stage_flags.get("pickup") and not stage_flags.get("export") and not stage_flags.get("customs") \
                and not stage_flags.get("delivery"):
            pass
        pending_docs = sum(
            1 for res in results
            if getattr(res, "missing_items", None)
            and any("chứng từ" in (str(m).lower()) or "tờ khai" in str(m).lower() or "pxk" in str(m).lower()
                    for m in res.missing_items)
        )
        docs_missing += 1 if pending_docs else 0
    n_finance = sum(1 for r in rows if (r.get("financial_flag") in ("open", "review", "unknown")))
    cards = [
        ("Truck / Lấy hàng cần bổ sung", "Lô đang chờ thông tin nhà máy, lịch lấy hàng", "🚛",
         "lay-hang", bucket.get("pickup", 0) + bucket.get("export", 0), "slate"),
        ("Lô cần thông quan", "Thiếu tờ khai / ETA / giấy nộp thuế", "🛃", "nhap", bucket.get("customs", 0), "amber"),
        ("Lô cần giao hàng", "Chờ chốt xe VN / xác nhận đã giao", "📦", "nhap", bucket.get("delivery", 0), "blue"),
        ("Hồ sơ thiếu chứng từ", "CO, PL, hóa đơn, biên lai chưa đủ", "🧾", "tasks", docs_missing, "red"),
    ]
    cards_html = []
    for label, desc, icon, _tab, count, color in cards:
        bar = {"slate": "#64748b", "amber": "#f59e0b", "blue": "#2563eb", "red": "#dc2626"}[color]
        bg = {"slate": "#475569", "amber": "#d97706", "blue": "#1d4ed8", "red": "#dc2626"}[color]
        ttl = label if count == 0 else f"{label} ({count})"
        cards_html.append(
            f"<div class='lg-actioncard'><div class='bar' style='background:{bar}'></div><div class='inner'>"
            f"<span class='ttl'><span style='width:36px;height:36px;border-radius:10px;color:#fff;display:grid;"
            f"place-items:center;font-size:17px;background:{bg};'>{icon}</span>{esc(ttl)}</span>"
            f"<span class='desc'>{esc(desc)}</span>"
            f"<span class='cta'>{'Không có việc đang chờ' if count == 0 else 'Mở danh sách xử lý'} →</span></div></div>"
        )
    st.markdown(section_title("🧭", "Việc cần xử lý", "Số việc thật đang mở cho các lô chưa hoàn thành"), unsafe_allow_html=True)
    st.markdown(
        f"<div class='lg-grid' style='grid-template-columns:1fr;'><div class='lg-grid-5' style='display:grid;"
        f"gap:12px;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));'>{''.join(cards_html)}</div></div>",
        unsafe_allow_html=True,
    )
    st.write("")

    # ---- KPIs ----
    kpis = [
        ("Lô đang chạy", str(active), "wait + pending", "navy"),
        ("Chờ xử lý (wait)", str(n_wait), "Lô mới chưa xử lý", ""),
        ("Đang thông quan / giao hàng", str(n_pending), "pending", ""),
        ("Quá hạn free time / hạn khách", str(len(over_free)), "Cần xử lý ngay", "red" if over_free else ""),
        ("Đã hoàn thành", str(len(done_rows)), "Toàn thời gian", "green"),
        ("Đã giao hôm nay", str(n_done_today), f"{now}", "green" if n_done_today else ""),
    ]
    kpi_html = "".join(
        stat_cell(label, value, sub, tone=tone) for label, value, sub, tone in kpis
    )
    money_html = (
        stat_cell("Còn phải thu (đã đối soát)", due_label,
                  "Chỉ tổng KNOWN từ read model tài chính" if due_known else "Chưa đủ dữ liệu đối soát (UNKNOWN)",
                  tone="green" if due_known and total_due else "")
        + stat_cell("Còn phải trả (đã đối soát)", pay_label,
                    "Chỉ tổng KNOWN từ read model tài chính" if pay_known else "Chưa đủ dữ liệu đối soát (UNKNOWN)",
                    tone="amber" if pay_known and total_pay else "")
    )
    st.markdown(section_title("📊", "Chỉ số vận hành", "Số liệu thật của hệ thống — UNKNOWN không tính là 0"), unsafe_allow_html=True)
    st.markdown(
        f"<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;'>"
        f"{kpi_html}</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        f"<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;'>"
        f"{money_html}</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    # ---- Trạng thái các lô đang chạy + quá hạn/sắp hạn ----
    overdue_list = sorted(over_free, key=lambda r: str((r.get("top_alert") or {}).get("label", "")))
    st.markdown(section_title("🚚", "Trạng thái các lô đang chạy", "Bấm vào lô để mở workspace xử lý"), unsafe_allow_html=True)
    rows_html = []
    for row in active_rows:
        sid = str(row.get("shipment_id") or "")
        tone = tone_for_status(row.get("operational_status"))
        na = (row.get("next_action") or {}).get("label") if row.get("next_action") else ""
        rows_html.append(
            f"<a class='lg-rowlink' href='{link_url('shipment', sid=sid)}'>"
            f"{badge(tone, text(row.get('operational_status_label'), row.get('operational_status') or '?'), 'sm')}"
            f"<span style='flex:1;min-width:0;'><b style='color:#0f2a4a;'>{esc(sid)} · {esc(row.get('customer') or UNKNOWN_LABEL)}</b>"
            f"<span style='display:block;font-size:13px;color:#64748b;'>{esc(na) if na else 'Tiếp theo: mở workspace để xem việc thiếu'}</span></span>"
            f"<span style='color:#1e5aa8;font-weight:700;font-size:13.5px;'>Mở →</span></a>"
        )
    if not rows_html:
        rows_html = ["<div class='lg-empty'>Không có lô nào đang chạy.</div>"]
    st.markdown(f"<div class='lg-grid'>{''.join(rows_html)}</div>", unsafe_allow_html=True)
    st.write("")

    # Money section cards
    def money_card(tone_label: str, title: str, amount: str, note: str, href: str, cta: str) -> str:
        bgs = {"green": "#059669", "amber": "#d97706", "navy": "#0f2a4a"}
        bg = bgs.get(tone_label, "#0f2a4a")
        return (
            f"<div style='border-radius:18px;padding:16px 18px;border:2px solid "
            f"{'#a7f3d0' if tone_label=='green' else '#fcd34d' if tone_label=='amber' else '#e2e8f0'};"
            f"background:{'#ecfdf5' if tone_label=='green' else '#fffbeb' if tone_label=='amber' else '#eff6ff'};'>"
            f"<p style='margin:0;font-size:13px;font-weight:800;color:#475569;'>{esc(title)}</p>"
            f"<p style='margin:4px 0 2px;font-size:22px;font-weight:800;color:#0f2a4a;'>{esc(amount)}</p>"
            f"<p style='margin:0 0 10px;font-size:13px;color:#64748b;min-height:18px;'>{esc(note)}</p>"
            f"<a class='lg-btn' style='background:{bg};min-height:42px;font-size:13.5px;' href='{href}'>{esc(cta)}</a></div>"
        )
    st.markdown(section_title("💰", "Tiền hôm nay — hiện trạng → việc thiếu → hành động",
                              "Số liệu từ read model tài chính (Shipment 360)"), unsafe_allow_html=True)
    st.markdown(
        "<div class='lg-grid-3' style='display:grid;gap:12px;'>"
        + money_card("green", "Còn phải thu", due_label,
                     "Khoản KNOWN chưa thu" if due_known else "Dữ liệu chưa đủ — cần cập nhật chi tiết lô",
                     link_url("finance"), "GHI NHẬN THANH TOÁN")
        + money_card("amber", "Còn phải trả", pay_label,
                     "Khoản KNOWN chưa trả" if pay_known else "Dữ liệu chưa đủ — cần đối soát",
                     link_url("reconcile"), "ĐỐI SOÁT NGAY")
        + money_card("navy", "Mở sổ tài chính", "→", "Xem toàn bộ công nợ khách & đối tác",
                     link_url("finance"), "MỞ SỔ THU TIỀN")
        + "</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    if not ships:
        st.info("Chưa có dữ liệu lô hàng nào được đồng bộ. Kiểm tra kết nối database hoặc bấm **🔄 Reload Data**.")
    if critical_rows:
        st.caption("⚠️ Những lô có cảnh báo đỏ đã được liệt kê theo read model readiness thật của hệ thống.")


# ---------------------------------------------------------------------------
# LÔ HÀNG (standalone list)
# ---------------------------------------------------------------------------
def shipments_page() -> None:
    # Clear legacy deep-link so the list stays a list.
    st.session_state.active_shipment_id = None
    st.session_state.dashboard_active_shipment_id = None
    ships, _customers, _contracts = _db()

    q = st.text_input("", placeholder="Nhập mã lô (LO-…), khách hàng, hợp đồng…", key="lg_ship_q",
                      label_visibility="collapsed")
    status_filter = st.selectbox("Lọc theo trạng thái", ["ALL", "wait", "pending", "done", "cancel"],
                                 format_func=lambda s: {"ALL": "Tất cả", "wait": "Chờ xử lý",
                                                        "pending": "Đang thông quan/giao hàng",
                                                        "done": "Hoàn thành", "cancel": "Đã hủy"}[s],
                                 key="lg_ship_st", label_visibility="collapsed")
    rows = _dashboard_rows(ships)
    rows = [r for r in rows if status_filter == "ALL" or r.get("operational_status") == status_filter]
    term = (q or "").strip().lower()
    if term:
        rows = [r for r in rows
                if term in str(r.get("shipment_id") or "").lower()
                or term in str(r.get("customer") or "").lower()
                or term in str(r.get("owner") or "").lower()]
    rows.sort(key=lambda r: str(r.get("last_update") or ""), reverse=True)

    header_right = (
        f"<a href='{link_url('new')}' class='lg-btn' style='min-height:44px;font-size:14px;'>＋ Tạo lô mới</a>"
        if has_permission("shipment_create") else ""
    )
    st.markdown(section_title("📦", "Lô Hàng",
                              "Tìm theo mã lô · khách · hợp đồng · trạng thái — mỗi dòng mở thẳng workspace xử lý",
                              right=header_right), unsafe_allow_html=True)

    if rows:
        st.markdown(f"<p style='color:#64748b;font-size:13.5px;margin:0 0 8px;'>Tìm thấy "
                    f"<b style='color:#0f2a4a;'>{len(rows)} lô</b>{' cho “' + esc(q) + '”' if term else ''}</p>",
                    unsafe_allow_html=True)
        trs = []
        for row in rows:
            sid = str(row.get("shipment_id") or "")
            tone = tone_for_status(row.get("operational_status"))
            st_label = text(row.get("operational_status_label"), str(row.get("operational_status") or "?"))
            fin = str(row.get("financial_label") or "—")
            alert = row.get("top_alert") or {}
            next_text = str((row.get("next_action") or {}).get("label") or alert.get("label") or "")
            detail = f"{esc(row.get('last_update_label') or '')}"
            trs.append(
                f"<tr><td><a href='{link_url('shipment', sid=sid)}' "
                f"style='font-weight:800;color:#1e5aa8;font-size:15px;'>{esc(sid)}</a>"
                f"<span style='display:block;font-size:12px;color:#94a3b8;'>Cập nhật {detail}</span></td>"
                f"<td style='font-weight:600;max-width:200px;'>{esc(row.get('customer') or UNKNOWN_LABEL)}</td>"
                f"<td style='max-width:240px;'><span style='display:block;font-size:13px;color:#64748b;'>"
                f"{esc(route_of(row))}</span></td>"
                f"<td>{badge(tone, st_label, 'sm')}</td>"
                f"<td style='max-width:260px;font-size:13.5px;'><span style='font-weight:600;'>"
                f"{esc(next_text) if next_text else '—'}</span></td>"
                f"<td style='white-space:nowrap;font-size:13px;'>Sale: <b>{esc(row.get('owner') or '—')}</b></td>"
                f"<td><span style='font-size:12px;font-weight:800;'>{esc(fin)}</span></td>"
                f"<td><a class='lg-btn' style='min-height:40px;padding:6px 12px;font-size:13px;' "
                f"href='{link_url('shipment', sid=sid)}'>XỬ LÝ</a></td></tr>"
            )
        st.markdown(
            f"<div class='lg-card' style='overflow-x:auto;'><table class='tbl' style='width:100%;min-width:1080px;'>"
            f"<thead><tr><th>Mã lô</th><th>Khách hàng</th><th>Tuyến</th><th>Trạng thái</th><th>Việc tiếp theo</th>"
            f"<th>Sale</th><th>Tài chính</th><th>Hành động</th></tr></thead><tbody>{''.join(trs)}</tbody></table></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<div class='lg-empty'><p style='font-weight:800;font-size:16px;color:#334155;'>"
                    "Không tìm thấy lô nào</p><p style='font-size:14px;color:#64748b;'>"
                    "Thử từ khóa khác hoặc tạo lô mới.</p></div>", unsafe_allow_html=True)


def route_of(row: Mapping[str, Any]) -> str:
    from views.lg_core import UNKNOWN_LABEL  # noqa: PLC0415

    raw = row.get("route")
    if raw:
        return str(raw)
    return UNKNOWN_LABEL


# ---------------------------------------------------------------------------
# Thin wrappers of the real modules (same content, Logi-good shell chrome)
# ---------------------------------------------------------------------------
def tasks_page() -> None:
    st.markdown(section_title("🧭", "Việc Cần Xử Lý",
                              "Hiện trạng → việc thiếu → bấm XỬ LÝ NGAY để tới đúng ô cần nhập"), unsafe_allow_html=True)
    from views.review_queue import ui_review_queue  # noqa: PLC0415

    ui_review_queue()


def newlot_page() -> None:
    st.markdown(section_title("➕", "Tạo Lô Mới",
                              "Tạo lô theo quy trình thật: kiểm tra ràng buộc, snapshot tài chính và lưu atomic"),
                unsafe_allow_html=True)
    from views.shipment import ui_create_new_shipment  # noqa: PLC0415

    ui_create_new_shipment()


def tracking_page() -> None:
    st.markdown(section_title("🌐", "Theo Dõi Vận Chuyển",
                              "Vị trí & mốc thời gian từng lô — dữ liệu từ workspace lô hàng"),
                unsafe_allow_html=True)
    from views.tracking import ui_tracking_tool  # noqa: PLC0415

    ui_tracking_tool()


def customers_page() -> None:
    from views.customers import ui_customers  # noqa: PLC0415

    ui_customers()


def partner_page() -> None:
    from views.entity_context import ui_entity_context  # noqa: PLC0415

    ui_entity_context()


def quotes_page() -> None:
    from views.quotations import ui_sales_module  # noqa: PLC0415

    ui_sales_module()


def agreements_page() -> None:
    from views.agreements import ui_agreements_module  # noqa: PLC0415

    ui_agreements_module()


def contracts_page() -> None:
    from views.contracts import ui_contracts_management  # noqa: PLC0415

    ui_contracts_management()


def finance_page() -> None:
    from views.finance import ui_receivables_management  # noqa: PLC0415

    ui_receivables_management()


def reconcile_page() -> None:
    from views.finance_review import ui_finance_review  # noqa: PLC0415

    ui_finance_review()


def partnerdebt_page() -> None:
    from views.partner_reconciliation import ui_partner_reconciliation_desk  # noqa: PLC0415

    ui_partner_reconciliation_desk()


def reports_page() -> None:
    from views.reports import ui_reports_dashboard  # noqa: PLC0415

    ui_reports_dashboard()


def tariff_page() -> None:
    from views.tariff import ui_super_tariff_hub  # noqa: PLC0415

    ui_super_tariff_hub()


def handbook_page() -> None:
    from views.knowledge_base import ui_knowledge_base  # noqa: PLC0415

    ui_knowledge_base()


def translate_page() -> None:
    from views.translation import ui_translation  # noqa: PLC0415

    ui_translation()


def intake_page() -> None:
    """Nhập dữ liệu GetFly — real upload/process UI from the home module."""
    from views.dashboard import _render_excel_import_ui  # noqa: PLC0415

    _render_excel_import_ui()
