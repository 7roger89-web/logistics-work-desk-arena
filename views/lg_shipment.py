"""LOGI-GOOD EXACT — Lô Hàng detail (one shipment workspace).

Header (real read model) + the *real* shipment workspace
(``views.shipment.ui_shipment_detail_tabs``) so every operational field stays
editable through the real current-model writers.  Tab pills mirror the
Logi-good design; each pill deep-links to the corresponding real workspace tab.
"""
from __future__ import annotations

import datetime
from typing import Any, Mapping

import streamlit as st

from views.lg_core import (
    UNKNOWN_LABEL,
    a,
    badge,
    esc,
    link_url,
    pill,
    section_title,
    text,
    tone_for_status,
)

_PILLS: tuple[tuple[str, str, str], ...] = (
    ("lay-hang", "Lấy hàng & Xuất khẩu", "Lấy hàng"),
    ("nhap", "Nhập khẩu & Giao hàng", "Nhập & Giao"),
    ("tai-chinh", "Tài chính / Công nợ", "Tài chính"),
    ("chung-tu", "Chứng từ & PXK", "Chứng từ"),
    ("lich-su", "Lịch sử", "Lịch sử"),
)

_SECTION_MAP: dict[str, Any] = {
    "lay-hang": "export",
    "nhap": "import",
    "tai-chinh": "finance",
    "chung-tu": "documents",
    "lich-su": None,
}


def _shipment(sid: str) -> Mapping[str, Any] | None:
    ships = st.session_state.get("db_shipments", {}) or {}
    ship = ships.get(sid)
    return ship if isinstance(ship, Mapping) else None


def _row(sid: str, ship: Mapping[str, Any]) -> dict[str, Any]:
    from core.shipment_dashboard import build_shipment_dashboard_view  # noqa: PLC0415

    try:
        return build_shipment_dashboard_view(ship, today=datetime.date.today())
    except Exception:  # noqa: BLE001
        return {}


def _readiness(ship: Mapping[str, Any]):
    from core.readiness import get_all_readiness, derive_next_action  # noqa: PLC0415
    from core.shipment_dashboard import build_shipment_summary  # noqa: PLC0415

    try:
        summary = build_shipment_summary(ship)
        results = get_all_readiness(ship, summary)
        return results, derive_next_action(ship, results)
    except Exception:  # noqa: BLE001
        return [], None


def _customer_mst(customer_id: str, customer: str) -> str:
    customers = st.session_state.get("db_customers", {}) or {}
    doc = customers.get(customer_id) or {}
    if not doc:
        doc = next((c for c in customers.values() if str(c.get("name", "")) == str(customer)), {})
    return text(doc.get("tax_code") or doc.get("mst"), UNKNOWN_LABEL)


def _contract_link(ship: Mapping[str, Any], sid: str) -> str:
    data = ship.get("data") or {}
    ent = data.get("entrustment") or {}
    contract = str(ship.get("contract_id") or ent.get("contract_no") or "").strip()
    if contract:
        return (f"<a href='{link_url('contracts')}' style='color:#1e5aa8;font-weight:800;text-decoration:none;'>"
                f"{esc(contract.upper())}</a>")
    return "<span style='color:#94a3b8;'>Chưa liên kết</span>"


def shipment_page(sid: str = "", tab: str = "") -> None:
    sid = str(sid or "").strip()
    ships = st.session_state.get("db_shipments", {}) or {}
    if not sid or sid not in ships:
        # try legacy active id resolution
        legacy = st.session_state.get("dashboard_active_shipment_id") or st.session_state.get("active_shipment_id")
        if legacy and str(legacy) in ships:
            sid = str(legacy)
        else:
            st.markdown(
                "<div class='lg-empty'><p style='font-weight:800;font-size:17px;color:#334155;'>"
                f"Không tìm thấy lô {esc(sid)}</p>"
                "<p style='font-size:14px;color:#64748b;'>Mã lô có thể sai hoặc chưa được đồng bộ.</p></div>",
                unsafe_allow_html=True,
            )
            st.button("← Về danh sách lô", on_click=_back_to_list)
            st.stop()
    ship = ships[sid]
    st.session_state.dashboard_active_shipment_id = sid
    st.session_state.active_shipment_id = sid

    # Legacy reviewers return to their own desks, not the list.
    back_label = ""
    if st.session_state.get("review_queue_return"):
        back_label = "Việc Cần Xử Lý"
    elif st.session_state.get("finance_review_return"):
        back_label = "Đối Soát Tài Chính"
    if back_label:
        if st.button(f"← Về {back_label}", key=f"lg_back_{sid}", type="secondary"):
            st.session_state.review_queue_return = False
            st.session_state.finance_review_return = False
            st.session_state.active_shipment_id = None
            st.session_state.dashboard_active_shipment_id = None
            st.session_state.active_page = back_label
            st.query_params.clear()
            st.rerun()
    else:
        st.markdown(
            f"<a href='{link_url('shipments')}' style='display:inline-flex;align-items:center;gap:6px;"
            f"font-size:14.5px;font-weight:700;color:#64748b;text-decoration:none;margin-bottom:10px;'>"
            f"← Quay lại danh sách lô</a>",
            unsafe_allow_html=True,
        )

    row = _row(sid, ship)
    results, action = _readiness(ship)
    status_raw = ship.get("status") or ((ship.get("data") or {}).get("0.0") or {}).get("st") or "wait"
    tone = tone_for_status(status_raw)
    from core.config import STATUS_LABELS  # noqa: PLC0415

    status_label = STATUS_LABELS.get(str(status_raw).lower()) or str(status_raw)
    missing_n = sum(1 for res in results if not res.ready)
    customer = text(ship.get("customer") or ship.get("client"), UNKNOWN_LABEL)
    mst = _customer_mst(str(ship.get("customer_id") or ""), customer)
    updated = str(row.get("last_update_label") or "")
    owner = text(row.get("owner") or ship.get("internal_sale_owner"), "Chưa phân công")
    support = _support(ship)
    route = text(row.get("route") or _route(ship), UNKNOWN_LABEL)

    # severity for banner
    sev = getattr(action, "severity", "") if action else ""
    tone_banner = "green" if sev == "ok" else "red" if sev == "critical" else "amber"
    banner_title = action.label if action else "Tất cả thông tin đã sẵn sàng"
    banner_desc = action.recommended_action if action else "Lô hàng đã đủ thông tin để xử lý các bước tiếp theo."
    missing_html = (f"<span style='display:inline-flex;align-items:center;gap:6px;font-size:13px;font-weight:800;"
                    f"background:#fef2f2;color:#b91c1c;border:1px solid #fecaca;border-radius:999px;padding:5px 12px;'>"
                    f"⚠ Thiếu {missing_n} thông tin</span>") if missing_n else ""

    header = (
        f"<div class='lg-card' style='overflow:hidden;'>"
        f"<div style='height:6px;background:linear-gradient(90deg,#0f2a4a,#1e5aa8,#10b981);'></div>"
        f"<div style='padding:18px 20px;'>"
        f"<div style='display:flex;flex-wrap:wrap;align-items:center;gap:8px;'>"
        f"<h1 style='margin:0;font-size:24px;font-weight:800;color:#0f2a4a;'>{esc(sid)}</h1>"
        f"{badge(tone, esc(status_label))}{missing_html}"
        f"<span style='margin-left:auto;font-size:12.5px;color:#94a3b8;'>🕒 Cập nhật {esc(updated or '—')}</span>"
        f"</div>"
        f"<p style='margin:6px 0 0;font-weight:600;font-size:15.5px;color:#1e293b;'>{esc(customer)}"
        f"<span style='color:#94a3b8;font-weight:400;'> · MST {esc(mst)}</span></p>"
        f"<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:2px 18px;margin-top:10px;'>"
        f"{_state_row('Tuyến', esc(route))}"
        f"{_state_row('Cửa khẩu / điểm giao', esc(_border_point(ship)))}"
        f"{_state_row('Hợp đồng', _contract_link(ship, sid))}"
        f"{_state_row('Sale · Support', f'<b>{esc(owner)}</b> · {esc(support)}')}"
        f"</div></div>"
        f"<div style='padding:0 20px 16px;'>"
        f"<div class='lg-banner {tone_banner}' style='margin:0;'>"
        f"<span class='ic' style='background:{'#059669' if tone_banner=='green' else '#dc2626' if tone_banner=='red' else '#d97706'};'>"
        f"{'✓' if tone_banner=='green' else '!'}</span>"
        f"<span class='txt'><small>Việc tiếp theo</small><b>{esc(banner_title)}</b>"
        f"<span>{esc(banner_desc)}</span></span>"
        f"<span style='font-size:12px;color:#64748b;'>Từ read model readiness thật</span></div></div>"
        f"<div style='padding:12px 20px 16px;border-top:1px solid #eef2f7;display:flex;gap:8px;overflow-x:auto;'>"
    )
    pills_html = []
    for pid, label, short in _PILLS:
        active = (tab or "") == pid
        pills_html.append(
            f"<a href='{link_url('shipment', sid=sid, tab=pid)}' style='text-decoration:none;'>"
            f"{pill(active, label)}</a>"
        )
    st.markdown(header + "".join(pills_html) + "</div></div>", unsafe_allow_html=True)
    st.write("")

    # Map donor pill to real workspace default tab.
    section = _SECTION_MAP.get(tab or "", None)
    if section is not None:
        st.session_state.active_shipment_section = section

    from core.auth import can_operate_business  # noqa: PLC0415

    can_edit = can_operate_business("shipment_edit")
    if can_edit:
        from views.shipment import ui_shipment_detail_tabs  # noqa: PLC0415

        ui_shipment_detail_tabs(sid, ship)
    else:
        st.info("Tài khoản hiện tại chỉ có quyền xem lô hàng này.")
        from core.shipment_workspace import build_shipment_workspace_view  # noqa: PLC0415
        from views.shipment_360 import render_shipment_workspace  # noqa: PLC0415

        view = build_shipment_workspace_view(ship, today=datetime.date.today())
        render_shipment_workspace(view, audit_rows=None, navigation_shipment_id=sid)

    if (tab or "") == "lich-su":
        _render_audit(sid)


def _state_row(label: str, value_html: str) -> str:
    return (
        f"<div style='padding:7px 0;border-bottom:1px solid #f1f5f9;'>"
        f"<p style='margin:0;font-size:12.5px;color:#64748b;font-weight:600;'>{esc(label)}</p>"
        f"<p style='margin:2px 0 0;font-size:14px;font-weight:700;color:#1e293b;word-break:break-word;'>{value_html}</p>"
        f"</div>"
    )


def _support(ship: Mapping[str, Any]) -> str:
    from views.lg_core import first_value  # noqa: PLC0415

    return text(first_value(ship, ("support_owner", "support", "ops_owner")), "—")


def _route(ship: Mapping[str, Any]) -> str:
    data = ship.get("data") or {}
    sec = data.get("1.2") or {}
    route = sec.get("route") or ""
    if route:
        return str(route)
    pol = text(sec.get("pol"), "")
    pod = text(sec.get("pod"), "")
    if pol or pod:
        return f"{pol} → {pod}"
    return UNKNOWN_LABEL


def _border_point(ship: Mapping[str, Any]) -> str:
    data = ship.get("data") or {}
    sec27 = data.get("2.7") or {}
    addr = text(sec27.get("addr"), "")
    return addr if addr else str((data.get("1.2") or {}).get("pod") or "—")


def _back_to_list() -> None:
    st.session_state.active_shipment_id = None
    st.session_state.dashboard_active_shipment_id = None
    st.query_params.clear()
    st.session_state.active_page = "Lô Hàng"


def _render_audit(sid: str) -> None:
    st.markdown(section_title("🕒", "Lịch sử thay đổi", "Audit log thật của lô hàng"), unsafe_allow_html=True)
    try:
        from core.database import load_audit_logs  # noqa: PLC0415
        import pandas as pd  # noqa: PLC0415

        audit_rows = load_audit_logs("shipment", sid, limit=30)
    except Exception:  # noqa: BLE001
        audit_rows = []
    if audit_rows:
        df = pd.DataFrame(
            [
                {"Thời gian": str(r.get("created_at", "")), "Người thực hiện": r.get("actor", ""),
                 "Hành động": r.get("action", "")}
                for r in audit_rows
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("Chưa có audit log cho lô này.")
