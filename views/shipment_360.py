"""Read-only Shipment 360 financial summary + operational workspace renderer.

LOG-LG04 cải thiện không gian làm việc: việc tiếp theo nổi bật (card), 3 thẻ
"việc chính" (Xuất khẩu / Nhập khẩu & Giao hàng / Chi phí) dẫn thẳng đến khối
nhập, các khối tham khảo thu gọn, khối kỹ thuật ẩn khi chưa có dữ liệu.
Phần tài chính giữ nguyên ngữ nghĩa đọc (UNKNOWN != zero).
"""

from __future__ import annotations

from typing import Any, Mapping

import streamlit as st
from views.lg_core import nav_to_page  # noqa: E402

from core.next_action_card import render_next_action_card
from core.shipment_360 import UNKNOWN
from views.entity_context import open_entity_context


def _workspace_value(value: Any) -> str:
    if value is None or value == "":
        return "UNKNOWN"
    return str(value)


def _free_time_status(view: Mapping[str, Any]) -> tuple[str, str]:
    """Trả về (mức độ next_action, chi tiết) khi free time sắp hết.

    Dùng dữ liệu days_remaining có sẵn trong workspace view; ngưỡng 3 ngày
    được coi là "cần xử lý sớm", dưới 0 là "nghiêm trọng" (đã quá hạn).
    """

    try:
        remaining = float(view.get("free_time_remaining", UNKNOWN))
    except (TypeError, ValueError):
        return "", ""
    expiry = _workspace_value(view.get("free_time_expiry"))
    if remaining < 0:
        return (
            "critical",
            f"Đã quá hạn free time (hết hạn {expiry}) — container có nguy cơ bị tính phí lưu ngay. "
            f"Còn lại {remaining:,.0f} ngày theo dữ liệu hiện tại.",
        )
    if 0 <= remaining <= 3:
        return (
            "warning",
            f"Free time chỉ còn {remaining:,.0f} ngày (hết hạn {expiry}). "
            f"Hàng cần thông quan + lấy khỏi cảng kịp hạn để tránh phí lưu cont.",
        )
    return "", ""


def _render_workspace_signal(label: str, value: Any, detail: Any, column: Any) -> None:
    column.caption(label.upper())
    column.markdown(f"**{_workspace_value(value)}**")
    if detail not in (None, ""):
        column.caption(_workspace_value(detail))


def _timeline_rows(view: Mapping[str, Any], audit_rows: list[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    rows = [dict(row) for row in view.get("timeline", []) if isinstance(row, Mapping)]
    for row in audit_rows or []:
        rows.append(
            {
                "event": row.get("action") or "Audit event",
                "date": str(row.get("created_at") or "UNKNOWN"),
                "source": f"audit · {row.get('actor') or 'UNKNOWN'}",
                "status": "KNOWN",
            }
        )
    return rows


def _primary_status_snippet(view: Mapping[str, Any], section: str) -> str:
    """Tóm tắt trạng thái ngắn cho mỗi thẻ việc chính, chỉ đọc field có sẵn."""

    route = view.get("route") or {}
    if section == "export":
        booking = _workspace_value(route.get("booking"))
        mode = _workspace_value(route.get("mode"))
        return f"{mode} · Booking {booking}"
    if section == "import":
        arrival = _workspace_value(view.get("arrival_date"))
        free = _workspace_value(view.get("free_time_remaining"))
        return f"ETA {arrival} · Free time còn {free} ngày"
    return ""


def render_primary_work_cards(view: Mapping[str, Any]) -> None:
    """3 thẻ việc chính của Support — dẫn thẳng đến khối nhập liên quan."""

    cards = [
        {
            "title": "🚛 Lấy hàng & Xuất khẩu",
            "section": "export",
            "description": "Booking, vận đơn, lịch tàu, lấy hàng từ nhà máy.",
            "anchor": "lg04_tab_export",
            "label": "Mở Xuất khẩu",
        },
        {
            "title": "🛃 Nhập khẩu & Giao hàng",
            "section": "import",
            "description": "Tờ khai, thông quan, thuế, giao hàng tận nơi.",
            "anchor": "lg04_tab_import",
            "label": "Mở Nhập khẩu & Giao hàng",
        },
        {
            "title": "💰 Chi phí & Công nợ",
            "section": "finance",
            "description": "Nhập chi phí, giá bán, thu tiền, đối soát công nợ.",
            "anchor": "lg04_tab_finance",
            "label": "Mở Chi phí",
        },
    ]

    st.markdown(
        """
        <style>
        .lg04-work-card { border: 2px solid #D0D7DE; border-radius: 12px;
            background: #FFFFFF; padding: .75rem .9rem; margin: 0 .15rem .6rem; }
        .lg04-work-card .card-title { color: #102A43; font-size: 1.02rem;
            font-weight: 900; }
        .lg04-work-card .card-desc { color: #475467; font-size: .82rem; }
        .lg04-work-card .card-status { color: #667085; font-size: .78rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    shipment_id = _workspace_value(view.get("shipment_id"))
    cols = st.columns(3)
    for card, column in zip(cards, cols):
        with column:
            st.markdown(f"<div class='lg04-work-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-title'>{card['title']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-desc'>{card['description']}</div>", unsafe_allow_html=True)
            snippet = _primary_status_snippet(view, card["section"])
            if snippet:
                st.markdown(f"<div class='card-status'>{snippet}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            if column.button(card["label"], key=f"lg04_work_jump_{card['anchor']}", use_container_width=True):
                st.session_state.active_shipment_section = card["section"]
                st.markdown(
                    f"""
                    <script>
                    const target = document.getElementById('{card['anchor']}');
                    if (target) {{ target.scrollIntoView({{behavior: 'smooth', block: 'start'}}); }}
                    </script>
                    """,
                    unsafe_allow_html=True,
                )


def _render_primary_work_areas(view: Mapping[str, Any], shipment_id: str) -> None:
    """LOG-LG04 R2: 3 khối việc chính hiển thị trực tiếp ở đầu workspace.

    Mỗi khối có: tiêu đề + tóm tắt trạng thái + trường thiếu (nếu có) + nút "Cập nhật".
    Nút "Cập nhật" không phải thẻ nhảy — nó là hành động trực tiếp trong khối việc.
    Khi bấm, app chuyển sang trang chi tiết với tab đúng đã mở sẵn.
    """

    st.markdown(
        """
        <style>
        .lg04-work-area { border: 1px solid #D0D7DE; border-radius: 10px;
            background: #FFFFFF; padding: .8rem .9rem; margin-bottom: .8rem; }
        .lg04-work-area .area-header { display: flex; align-items: baseline; gap: .5rem; flex-wrap: wrap; }
        .lg04-work-area .area-title { color: #102A43; font-size: 1.05rem; font-weight: 800; }
        .lg04-work-area .area-status { color: #18794E; font-size: .82rem; font-weight: 600; }
        .lg04-work-area .area-missing { color: #9A6700; font-size: .8rem; margin-top: .3rem; }
        .lg04-work-area .area-summary { color: #475467; font-size: .82rem; margin-top: .2rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    areas = [
        {
            "title": "🚛 Lấy hàng & Xuất khẩu",
            "section": "export",
            "summary": _area_summary_export(view),
            "missing": _area_missing_export(view),
        },
        {
            "title": "🛃 Nhập khẩu & Giao hàng",
            "section": "import",
            "summary": _area_summary_import(view),
            "missing": _area_missing_import(view),
        },
        {
            "title": "💰 Chi phí & Công nợ",
            "section": "finance",
            "summary": _area_summary_finance(view),
            "missing": _area_missing_finance(view),
        },
    ]

    for area in areas:
        with st.container():
            st.markdown(
                f"""
                <div class='lg04-work-area'>
                    <div class='area-header'>
                        <span class='area-title'>{area['title']}</span>
                    </div>
                    <div class='area-summary'>{area['summary']}</div>
                    {f"<div class='area-missing'>{area['missing']}</div>" if area['missing'] else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )
            c_left, c_right = st.columns([5, 1])
            c_left.caption("Bấm \"Cập nhật\" để mở phần nhập liệu tương ứng")
            if c_right.button("Cập nhật", key=f"lg04_r2_update_{area['section']}_{shipment_id}", use_container_width=True):
                st.session_state.active_shipment_section = area["section"]
                st.rerun()


def _area_summary_export(view: Mapping[str, Any]) -> str:
    route = view.get("route") or {}
    mode = _workspace_value(route.get("mode"))
    booking = _workspace_value(route.get("booking"))
    mbl = _workspace_value(route.get("mbl"))
    etd = _workspace_value(route.get("etd"))
    pol = _workspace_value(route.get("pol"))
    pod = _workspace_value(route.get("pod"))
    status = _workspace_value(view.get("operational_status_label"))
    return f"Mode: {mode} · Booking: {booking} · MBL: {mbl} · ETD: {etd} · {pol} → {pod} · Trạng thái: {status}"


def _area_missing_export(view: Mapping[str, Any]) -> str:
    route = view.get("route") or {}
    missing = []
    if not route.get("booking"):
        missing.append("Booking No")
    if not route.get("mbl"):
        missing.append("MBL")
    if not route.get("etd"):
        missing.append("ETD")
    if missing:
        return f"⚠️ Thiếu: {', '.join(missing)}"
    return ""


def _area_summary_import(view: Mapping[str, Any]) -> str:
    arrival = _workspace_value(view.get("arrival_date"))
    free_time = _workspace_value(view.get("free_time_remaining"))
    tk_no = _workspace_value(view.get("tk_no"))
    delivery = _workspace_value(view.get("delivery_status"))
    return f"ETA: {arrival} · Free time: {free_time} ngày · TK HQ: {tk_no} · Giao hàng: {delivery}"


def _area_missing_import(view: Mapping[str, Any]) -> str:
    missing = []
    if not view.get("arrival_date"):
        missing.append("ETA")
    if not view.get("free_time") and view.get("free_time_remaining") in (None, "", UNKNOWN):
        missing.append("Free time")
    if not view.get("tk_no"):
        missing.append("Số TK HQ")
    if missing:
        return f"⚠️ Thiếu: {', '.join(missing)}"
    return ""


def _area_summary_finance(view: Mapping[str, Any]) -> str:
    recv = view.get("receivable") or {}
    pay = view.get("payable") or {}
    receivable = _workspace_value(recv.get("total"))
    outstanding_recv = _workspace_value(recv.get("outstanding"))
    payable = _workspace_value(pay.get("total"))
    outstanding_pay = _workspace_value(pay.get("outstanding"))
    fin_status = _workspace_value(view.get("financial_status"))
    return f"Phải thu: {receivable} (còn {outstanding_recv}) · Phải trả: {payable} (còn {outstanding_pay}) · Trạng thái: {fin_status}"


def _area_missing_finance(view: Mapping[str, Any]) -> str:
    missing = []
    route = view.get("route") or {}
    details = (view.get("financial_details") or []) if isinstance(view.get("financial_details"), list) else []
    if not details:
        missing.append("Chi phí / giá bán")
    if missing:
        return f"⚠️ Thiếu: {', '.join(missing)}"
    return ""


def render_shipment_workspace(
    view: Mapping[str, Any],
    *,
    audit_rows: list[Mapping[str, Any]] | None = None,
    navigation_shipment_id: str | None = None,
) -> None:
    """Render the operational Shipment 360 workspace without any writer."""

    st.markdown(
        """
        <style>
        .shipment360-kicker { color: #0B6E99; font-size: .68rem; font-weight: 800; letter-spacing: .14em; margin-top: .1rem; }
        .shipment360-title { color: #102A43; font-size: 1.65rem; line-height: 1.15; margin: .15rem 0 .25rem; }
        .shipment360-route { color: #667085; font-size: .86rem; }
        .shipment360-note { color: #475467; font-size: .8rem; border-left: 3px solid #0B6E99; background: #F0F7FA; padding: .55rem .75rem; margin: .65rem 0 .9rem; }
        .shipment360-signal { border-top: 1px solid #D9E2EC; padding-top: .55rem; min-height: 4.5rem; }
        @media (max-width: 900px) { .shipment360-title { font-size: 1.35rem; } .shipment360-signal { min-height: 3.8rem; } }
        @media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition-duration: .01ms !important; animation-duration: .01ms !important; } }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Legacy documents can expose an old id inside the payload while
    # Dashboard opens the current mapping key. Keep display facts source-bound
    # but use the explicit key for context navigation when supplied.
    shipment_id = _workspace_value(navigation_shipment_id or view.get("shipment_id"))
    customer = _workspace_value(view.get("customer"))
    route = view.get("route") or {}
    route_label = f"{_workspace_value(route.get('pol'))} → {_workspace_value(route.get('pod'))}"
    st.markdown("<div class='shipment360-kicker'>LÔ HÀNG · KHÔNG GIAN LÀM VIỆC</div>", unsafe_allow_html=True)
    st.markdown(f"<h1 class='shipment360-title'>{shipment_id} · {customer}</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='shipment360-route'>{route_label} · {_workspace_value(route.get('mode'))} · "
        f"Incoterm {_workspace_value(route.get('incoterm'))}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='shipment360-note'>Phần trên là tóm tắt để đọc nhanh · Việc cần làm hiện ngay dưới đây · "
        "Các khối nhập liệu nằm ở 3 mục bên dưới.</div>",
        unsafe_allow_html=True,
    )

    # ---- LOG-LG04 R2: Việc tiếp theo nổi bật ----
    action = dict(view.get("next_action") or {})
    free_severity, free_detail = _free_time_status(view)
    if free_severity and action.get("severity") not in ("critical", "warning"):
        action = {
            "code": "FREE_TIME_EXPIRING",
            "severity": free_severity,
            "label": "Free time sắp hết — cần đẩy nhanh thông quan & giao hàng",
            "detail": free_detail,
            "who": "Support vận hành",
            "source": "Free time còn lại so với hạn miễn phí (tài chính lô hàng)",
        }
    render_next_action_card(action, anchor="lg04_tab_export")

    # ---- LOG-LG04 R2: 3 khối việc chính — hiển thị trực tiếp, không phải thẻ nhảy ----
    _render_primary_work_areas(view, shipment_id)

    s1, s2, s3, s4, s5 = st.columns(5)
    for column in (s1, s2, s3, s4, s5):
        column.markdown("<div class='shipment360-signal'>", unsafe_allow_html=True)
    _render_workspace_signal("Vận hành", view.get("operational_status_label"), "giai đoạn hiện tại", s1)
    _render_workspace_signal("Tài chính", view.get("financial_status"), view.get("financial_label"), s2)
    _render_workspace_signal("Chủ sở hữu", view.get("owner"), "người phụ trách", s3)
    _render_workspace_signal("Hạn khách", view.get("required_date"), f"kế hoạch {_workspace_value(view.get('planned_date'))}", s4)
    free_time = view.get("free_time_remaining")
    free_detail = f"hết hạn {_workspace_value(view.get('free_time_expiry'))}"
    _render_workspace_signal("Free time", free_time if free_time != UNKNOWN else UNKNOWN, free_detail, s5)

    alerts = [item for item in view.get("alerts", []) if isinstance(item, Mapping)]
    if alerts:
        with st.expander(f"⚠️ Việc cần theo dõi khác ({len(alerts)})", expanded=False):
            for item in alerts:
                st.markdown(
                    f"**{_workspace_value(item.get('label'))}** — {_workspace_value(item.get('detail'))}  "
                    f"\nNguồn: {_workspace_value(item.get('source'))}",
                )
    else:
        st.caption("Không có cảnh báo nào khác ngoài việc tiếp theo ở trên.")

    # ---- LOG-LG04: khối đối tác thu gọn + giải thích (Ý 4, Ý 8) ----
    with st.expander("🏭 Khách hàng · Nhà máy · Đại lý", expanded=False):
        st.caption(
            "Thông tin liên hệ của các bên trong lô hàng, dùng khi lấy hàng, xử lý chứng từ và giao hàng."
        )
        context = view.get("context") or {}
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Khách hàng**  \n{customer}")
            st.markdown(f"**Nhà cung cấp / nhà máy**  \n{_workspace_value(context.get('supplier'))}")
            st.markdown(f"**Đại lý / đối tác**  \n{_workspace_value(context.get('agent'))}")
        with c2:
            st.markdown(f"**Liên hệ lấy hàng**  \n{_workspace_value(context.get('pickup_contact'))}")
            st.markdown(f"**Địa chỉ lấy hàng**  \n{_workspace_value(context.get('pickup_address'))}")
            st.markdown(f"**Địa chỉ giao hàng**  \n{_workspace_value(context.get('delivery_address'))}")
            st.markdown(f"**Người nhận hàng**  \n{_workspace_value(context.get('receiver'))}")
        st.caption(
            "Booking: {_workspace_value(route.get('booking'))} · Carrier: {_workspace_value(route.get('carrier'))} · "
            f"Tàu: {_workspace_value(route.get('vessel'))} · Cont: {_workspace_value(route.get('container'))}"
        )
        customer_key = _workspace_value(view.get("customer_id"))
        if customer not in (UNKNOWN, "") and st.button(
            "Mở hồ sơ Khách hàng 360",
            key=f"shipment_customer_context_{shipment_id}",
            use_container_width=True,
        ):
            open_entity_context("customer", customer_key if customer_key != UNKNOWN else customer, return_shipment_id=shipment_id)
        if st.button("Xem chi tiết các bên (360)", key=f"shipment_partner_detail_{shipment_id}", use_container_width=True):
            st.session_state.setdefault("_context_expanded", True)
        factory_names = sorted({
            _workspace_value(row.get("factory"))
            for row in view.get("factory_lots", [])
            if isinstance(row, Mapping) and _workspace_value(row.get("factory")) != UNKNOWN
        })
        partner_name = _workspace_value(context.get("agent"))
        if factory_names and st.button(
            "Mở hồ sơ Nhà máy/NCC 360",
            key=f"shipment_factory_context_{shipment_id}",
            use_container_width=True,
        ):
            open_entity_context("factory", factory_names[0], return_shipment_id=shipment_id)
        if partner_name != UNKNOWN and st.button(
            "Mở hồ sơ Đại lý 360",
            key=f"shipment_partner_context_{shipment_id}",
            use_container_width=True,
        ):
            open_entity_context("partner", partner_name, return_shipment_id=shipment_id)

    # ---- LOG-LG04: hàng từ nhà máy — ẩn khi chưa có dữ liệu (Ý 6) ----
    lots = [row for row in view.get("factory_lots", []) if isinstance(row, Mapping)]
    if lots:
        with st.expander(f"🏭 Hàng từ nhà máy ({len(lots)})", expanded=False):
            st.caption("Thông tin hàng hóa lấy từ từng nhà máy để lên kế hoạch lấy hàng.")
            lots_display = [
                {key: _workspace_value(value) for key, value in row.items()}
                for row in lots
            ]
            st.dataframe(lots_display, hide_index=True, use_container_width=True)

    # ---- LOG-LG04 R2: chứng từ dạng tín hiệu ngắn + "Xem chứng từ" ----
    documents = [row for row in view.get("documents", []) if isinstance(row, Mapping)]
    documents_status = _workspace_value(view.get("documents_status"))
    missing_docs = [
        row.get("document", "Chứng từ")
        for row in documents
        if isinstance(row, Mapping) and (row.get("status") in ("CHƯA CÓ DỮ LIỆU", UNKNOWN, None) or not row.get("status"))
    ]
    if missing_docs:
        with st.expander(f"❌ Thiếu {len(missing_docs)} chứng từ: {', '.join(missing_docs)} — Xem chứng từ", expanded=False):
            st.caption("Các chứng từ cần bổ sung để lô hàng tiến hành đúng hạn.")
            for row in documents:
                status = row.get("status") or "UNKNOWN"
                status_tag = "✅ Có" if status == "CÓ DỮ LIỆU" else ("❓ Chưa có" if status in ("CHƯA CÓ DỮ LIỆU", UNKNOWN) else status)
                st.markdown(
                    f"**{row.get('document', 'Chứng từ')}** — {status_tag}"
                    + (f" · {row.get('step', '')}" if row.get("step") else ""),
                )
    elif documents:
        st.success(f"✅ Đủ {len(documents)} chứng từ")
        with st.expander("Xem chi tiết chứng từ", expanded=False):
            st.dataframe(documents, hide_index=True, use_container_width=True)
    else:
        st.caption(f"Chứng từ ({documents_status}): chưa có dữ liệu chứng từ trong lô.")

    timeline = _timeline_rows(view, audit_rows)
    with st.expander(f"🕒 Lịch sử / audit ({len(timeline)})", expanded=False):
        if timeline:
            st.dataframe(timeline, hide_index=True, use_container_width=True)
        else:
            st.caption("Chưa có mốc thời gian hoặc audit log đủ tin cậy.")

    st.divider()
    st.caption("Chi tiết chỉnh sửa, chứng từ nhập liệu và finance controls hiện có được giữ nguyên bên dưới.")


def _format_metric(metric: Mapping[str, Any]) -> str:
    if metric.get("status") == "UNKNOWN" or metric.get("value") is None:
        return "UNKNOWN"
    value = metric.get("value")
    try:
        formatted = f"{float(value):,.0f}"
    except (TypeError, ValueError):
        formatted = str(value)
    currency = metric.get("currency") or ""
    return f"{formatted} {currency}".strip()


def _metric(view: Mapping[str, Any], key: str, label: str, column: Any) -> None:
    value = view.get(key) or {}
    column.metric(label, _format_metric(value))
    if value.get("status") == "UNKNOWN":
        column.caption(str(value.get("reason") or "Chưa có nguồn dữ liệu"))


def _payable_metric(view: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    payable = view.get("payable") or {}
    return payable.get(key) or {"status": "UNKNOWN", "reason": "Chưa có nguồn công nợ phải trả tổng thể"}


def _relation_rows(view: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relation in view.get("relationships", []):
        if not isinstance(relation, Mapping):
            continue
        rows.append(
            {
                "Loại": relation.get("label"),
                "ID": relation.get("id"),
                "Liên kết": relation.get("link_kind"),
                "Bên nhận/ghi chú": relation.get("beneficiary") or relation.get("linked_type") or relation.get("note") or "",
                "Tiền gốc": relation.get("original_amount") or relation.get("amount_vnd"),
                "Tiền tệ": relation.get("original_currency") or "",
                "Tỷ giá đã lưu": relation.get("exchange_rate"),
                "Nguồn": relation.get("source"),
            }
        )
    return rows


def _payment_rows(view: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for payment in view.get("payments", []):
        rows.append(
            {
                "Ngày": payment.get("date"),
                "Số tiền": payment.get("amount"),
                "Tiền tệ": payment.get("currency"),
                "Ghi chú": payment.get("note"),
                "Phân bổ": payment.get("allocation_status"),
                "Nguồn": payment.get("source"),
            }
        )
    return rows


def _offer_agreement_link(commercial: Mapping[str, Any]) -> None:
    """Offer navigation to the linked commercial agreement without mutating data."""

    agreement_id = commercial.get("agreement_id") or ""
    if not agreement_id:
        return
    if st.button(
        f"Mở Thỏa Thuận & Bàn Giao · {_workspace_value(commercial.get('agreement_reference'))}",
        key=f"shp360_open_agreement_{agreement_id}",
        use_container_width=True,
    ):
        import streamlit as st
        st.session_state.agreement_detail_id = str(agreement_id)
        nav_to_page("Thỏa Thuận & Bàn Giao")
        st.rerun()


def render_shipment_360_summary(view: Mapping[str, Any]) -> None:
    """Render the read model without any input or persistence control."""

    st.markdown("### 💰 Tóm tắt tài chính lô hàng")
    st.caption(
        f"Lô: **{view.get('shipment_id') or 'UNKNOWN'}** · "
        f"Khách hàng: **{view.get('customer') or 'UNKNOWN'}** · "
        "Chỉ đọc — số liệu có nguồn hoặc được đánh dấu UNKNOWN"
    )
    commercial = view.get("commercial") or {}
    if commercial.get("agreement_id"):
        _offer_agreement_link(commercial)

    receivable = view.get("receivable") or {}
    r1, r2, r3 = st.columns(3)
    _metric({"receivable": receivable.get("total")}, "receivable", "TỔNG PHẢI THU", r1)
    _metric({"receivable": receivable.get("collected")}, "receivable", "ĐÃ THU", r2)
    _metric({"receivable": receivable.get("outstanding")}, "receivable", "CÒN PHẢI THU", r3)

    payable = view.get("payable") or {}
    p1, p2, p3 = st.columns(3)
    _metric({"payable": payable.get("total")}, "payable", "TỔNG PHẢI TRẢ (NGUỒN ĐẠI LÝ)", p1)
    _metric({"payable": payable.get("settled") or payable.get("paid")}, "payable", "ĐÃ TRẢ / CẤN TRỪ", p2)
    _metric({"payable": payable.get("outstanding")}, "payable", "CÒN PHẢI TRẢ", p3)
    if not payable.get("known"):
        st.caption("Tổng phải trả toàn bộ shipment: UNKNOWN — hiện chỉ có thể đọc nguồn agency nếu trường này tồn tại.")

    d1, d2, d3, d4 = st.columns(4)
    _metric({"known_cost": view.get("known_cost")}, "known_cost", "CHI PHÍ ĐÃ BIẾT", d1)
    _metric({"unallocated": view.get("unallocated")}, "unallocated", "CHƯA PHÂN BỔ", d2)
    _metric({"unreconciled": view.get("unreconciled")}, "unreconciled", "CHƯA ĐỐI SOÁT", d3)
    _metric({"tax": view.get("tax")}, "tax", "THUẾ CÓ DỮ LIỆU", d4)

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("VẬN HÀNH", str(view.get("operational_status") or "UNKNOWN"))
    s2.metric("TÀI CHÍNH", str(view.get("financial_status") or "UNKNOWN"))
    s3.metric("ĐÓNG TÀI CHÍNH", str(view.get("closure_status") or "UNKNOWN"))
    expected = view.get("expected_profit") or {}
    s4.metric("LỢI NHUẬN DỰ KIẾN", _format_metric(expected))

    with st.expander("Chi tiết dòng tiền và quan hệ công nợ", expanded=False):
        for payment in _payment_rows(view):
            st.markdown(
                f"**{payment.get('Ngày')}** · {payment.get('Số tiền')} {payment.get('Tiền tệ')} — "
                f"{payment.get('Ghi chú') or 'Không ghi chú'} ({payment.get('Phân bổ') or 'Chưa phân bổ'})",
            )
        for row in _relation_rows(view):
            st.markdown(
                f"**{row['Loại']}** · {row['Bên nhận/ghi chú']} — gốc {row['Tiền gốc']} {row['Tiền tệ']} "
                f"({row['Nguồn']})",
            )
    st.caption("Số liệu trên đây chỉ dùng để đọc nhanh. Nhập chi phí / thu tiền ở mục bên dưới.")
