"""Read-only Shipment 360 financial summary renderer."""

from __future__ import annotations

from typing import Any, Mapping

import streamlit as st

from core.shipment_360 import UNKNOWN
from views.entity_context import open_entity_context


def _workspace_value(value: Any) -> str:
    if value is None or value == "":
        return "UNKNOWN"
    return str(value)


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
    st.markdown("<div class='shipment360-kicker'>SHIPMENT 360 · OPERATIONAL WORKSPACE</div>", unsafe_allow_html=True)
    st.markdown(f"<h1 class='shipment360-title'>{shipment_id} · {customer}</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='shipment360-route'>{route_label} · {_workspace_value(route.get('mode'))} · "
        f"Incoterm {_workspace_value(route.get('incoterm'))}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='shipment360-note'>Đọc nhanh để xử lý lô · dữ liệu thiếu được hiển thị là UNKNOWN · "
        "các trường chỉnh sửa và writer hiện có nằm bên dưới khu vực tổng quan.</div>",
        unsafe_allow_html=True,
    )

    action = view.get("next_action") or {}
    action_severity = action.get("severity")
    action_text = f"**{_workspace_value(action.get('label'))}** — {_workspace_value(action.get('detail'))}"
    if action_severity == "critical":
        st.error(f"NEXT ACTION · {action_text}")
    elif action_severity == "warning":
        st.warning(f"NEXT ACTION · {action_text}")
    elif action_severity == "normal":
        st.success(f"NEXT ACTION · {action_text}")
    else:
        st.info(f"NEXT ACTION · {action_text}")
    st.caption(f"Nguồn bước tiếp theo: {_workspace_value(action.get('source'))}")

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
    with st.expander(f"⚠️ Cảnh báo và việc cần theo dõi ({len(alerts)})", expanded=bool(alerts)):
        if not alerts:
            st.caption("Không có cảnh báo deterministic từ read model hiện tại.")
        for item in alerts:
            st.markdown(
                f"**{_workspace_value(item.get('label'))}** — {_workspace_value(item.get('detail'))}  "
                f"\nNguồn: {_workspace_value(item.get('source'))}",
            )

    with st.expander("👥 Khách hàng · nhà máy · pickup · delivery", expanded=True):
        context = view.get("context") or {}
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Khách hàng**  \n{customer}")
            st.markdown(f"**Customer ID**  \n{_workspace_value(view.get('customer_id'))}")
            st.markdown(f"**Nhà cung cấp**  \n{_workspace_value(context.get('supplier'))}")
            st.markdown(f"**Agent/partner**  \n{_workspace_value(context.get('agent'))}")
        with c2:
            st.markdown(f"**Pickup contact**  \n{_workspace_value(context.get('pickup_contact'))}")
            st.markdown(f"**Pickup address**  \n{_workspace_value(context.get('pickup_address'))}")
            st.markdown(f"**Delivery address**  \n{_workspace_value(context.get('delivery_address'))}")
            st.markdown(f"**Receiver**  \n{_workspace_value(context.get('receiver'))}")
        st.caption(
            f"Booking: {_workspace_value(route.get('booking'))} · Carrier: {_workspace_value(route.get('carrier'))} · "
            f"Vessel: {_workspace_value(route.get('vessel'))} · Cont: {_workspace_value(route.get('container'))}"
        )
        link_columns = st.columns(3)
        customer_key = _workspace_value(view.get("customer_id"))
        if customer not in (UNKNOWN, "") and link_columns[0].button("Open Customer 360", key=f"shipment_customer_context_{shipment_id}", use_container_width=True):
            open_entity_context("customer", customer_key if customer_key != UNKNOWN else customer, return_shipment_id=shipment_id)
        factory_names = sorted({
            _workspace_value(row.get("factory"))
            for row in view.get("factory_lots", [])
            if isinstance(row, Mapping) and _workspace_value(row.get("factory")) != UNKNOWN
        })
        if factory_names and link_columns[1].button("Open Factory / Supplier 360", key=f"shipment_factory_context_{shipment_id}", use_container_width=True):
            open_entity_context("factory", factory_names[0], return_shipment_id=shipment_id)
        partner_name = _workspace_value(context.get("agent"))
        if partner_name != UNKNOWN and link_columns[2].button("Open Partner / Agent 360", key=f"shipment_partner_context_{shipment_id}", use_container_width=True):
            open_entity_context("partner", partner_name, return_shipment_id=shipment_id)

    lots = [row for row in view.get("factory_lots", []) if isinstance(row, Mapping)]
    lots_status = _workspace_value(view.get("factory_lots_status"))
    with st.expander(f"🏭 Factory lots ({len(lots) if lots else lots_status})", expanded=bool(lots)):
        if lots:
            # Keep mixed known/UNKNOWN quantities Arrow-compatible without
            # coercing missing values into a numeric guess.
            lots_display = [
                {key: _workspace_value(value) for key, value in row.items()}
                for row in lots
            ]
            st.dataframe(lots_display, hide_index=True, use_container_width=True)
        else:
            st.caption("UNKNOWN — shipment chưa có collection factories/factory_lots/factory_items chuẩn.")

    documents = [row for row in view.get("documents", []) if isinstance(row, Mapping)]
    with st.expander(f"📄 Chứng từ ({_workspace_value(view.get('documents_status'))})", expanded=view.get("documents_status") != "KNOWN"):
        st.caption("Trạng thái dưới đây phản ánh trường/evidence hiện có; không tự kết luận đủ chứng từ bắt buộc.")
        if documents:
            st.dataframe(documents, hide_index=True, use_container_width=True)
        else:
            st.caption("UNKNOWN — chưa có dữ liệu chứng từ để hiển thị.")

    timeline = _timeline_rows(view, audit_rows)
    with st.expander(f"🕒 Lịch sử / audit ({len(timeline)})", expanded=False):
        if timeline:
            st.dataframe(timeline, hide_index=True, use_container_width=True)
        else:
            st.caption("UNKNOWN — chưa có mốc thời gian hoặc audit log đủ tin cậy.")

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
        st.session_state.active_page = "Thỏa Thuận & Bàn Giao"
        st.rerun()


def render_shipment_360_summary(view: Mapping[str, Any]) -> None:
    """Render the read model without any input or persistence control."""

    st.markdown("### 💰 Shipment 360 — Hồ sơ tài chính đọc nhanh")
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
    if (view.get("actual_profit") or {}).get("status") == "UNKNOWN":
        st.caption(f"Lợi nhuận thực tế: UNKNOWN — {(view.get('actual_profit') or {}).get('reason')}")

    attention = view.get("attention") or []
    with st.expander("⚠️ Tiền cần chú ý", expanded=bool(attention)):
        if not attention:
            st.caption("Chưa có cảnh báo từ read model hiện tại.")
        else:
            for item in attention:
                severity = item.get("severity", "info")
                label = item.get("label") or "UNKNOWN"
                reason = item.get("source") or ""
                line = f"**{label}**"
                if reason:
                    line += f" — {reason}"
                if severity == "high":
                    st.warning(line)
                elif severity == "warning":
                    st.warning(line)
                else:
                    st.info(line)

    with st.expander("🧭 Money map & nguồn số liệu", expanded=True):
        st.markdown("**Quan hệ tiền hiện đọc được**")
        money_map = view.get("money_map") or []
        if money_map:
            st.dataframe(money_map, hide_index=True, use_container_width=True)
        else:
            st.caption("UNKNOWN — chưa có quan hệ tiền đủ tin cậy.")

        st.markdown("**Nguồn của từng số liệu**")
        sources = view.get("sources") or []
        if sources:
            st.dataframe(sources, hide_index=True, use_container_width=True)

    with st.expander("🔗 Hợp đồng, thanh toán hộ, nhận hộ / trả hộ", expanded=False):
        relation_rows = _relation_rows(view)
        if relation_rows:
            st.dataframe(relation_rows, hide_index=True, use_container_width=True)
        else:
            st.caption("Chưa tìm thấy liên kết trực tiếp hoặc qua hợp đồng.")

    with st.expander("💳 Các khoản khách hàng đã chuyển", expanded=False):
        payment_rows = _payment_rows(view)
        if payment_rows:
            st.dataframe(payment_rows, hide_index=True, use_container_width=True)
        else:
            st.caption("Chưa có payment row trong data.3.4.payments.")

    with st.expander("🤝 Bối cảnh thương mại (báo giá · thỏa thuận · bàn giao)", expanded=False):
        commercial = view.get("commercial") or {}
        if commercial:
            st.dataframe(
                [
                    {
                        "Báo giá": commercial.get("quote_reference", UNKNOWN),
                        "Thỏa thuận": commercial.get("agreement_reference", UNKNOWN),
                        "Trạng thái thỏa thuận": commercial.get("agreement_status", UNKNOWN),
                        "Incoterm": commercial.get("incoterm", UNKNOWN),
                        "Dịch vụ đã bán": commercial.get("services_sold", UNKNOWN),
                        "Khách cần giao": commercial.get("required_date", UNKNOWN),
                        "Bàn giao": commercial.get("handoff_readiness_label", UNKNOWN),
                    }
                ],
                hide_index=True,
                use_container_width=True,
            )
            if commercial.get("handoff_readiness_label") not in (None, "", "UNKNOWN"):
                for reason in commercial.get("handoff_reasons") or []:
                    st.info(reason)
            st.caption("Thương mại chỉ đọc từ quotes/agreements; không tạo hay sửa số liệu Finance Ledger từ đây.")
        else:
            st.caption("UNKNOWN — chưa tìm thấy báo giá/thỏa thuận liên kết với lô này.")
