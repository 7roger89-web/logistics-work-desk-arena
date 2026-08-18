"""Documents & Review Queue read-only workspace for LOG-C10."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import streamlit as st

from core.review_queue import (
    CATEGORY_COMMERCIAL,
    CATEGORY_FINANCIAL,
    CATEGORIES,
    STATUSES,
    STATUS_ATTENTION,
    STATUS_CRITICAL,
    STATUS_REVIEW,
    STATUS_WAITING,
    build_review_queue_items,
    filter_review_queue_items,
    label_vi,
    summarize_review_queue,
)
from core.shipment_360 import UNKNOWN
from views.entity_context import open_entity_context


def _value(value: Any) -> str:
    if value in (None, ""):
        return UNKNOWN
    return str(value)


def _resolve_shipment_id(requested: str) -> str:
    shipments = st.session_state.get("db_shipments") or {}
    if not isinstance(shipments, Mapping):
        return requested
    if requested in shipments:
        return requested
    normalized = requested.strip().casefold()
    for key, shipment in shipments.items():
        if str(key).strip().casefold() == normalized:
            return str(key)
        if isinstance(shipment, Mapping) and any(
            str(shipment.get(alias) or "").strip().casefold() == normalized
            for alias in ("id", "shipment_id")
        ):
            return str(key)
    return requested


def _open_shipment(item: Mapping[str, Any]) -> None:
    target = item.get("target") or {}
    requested = _value(target.get("shipment_id") or item.get("shipment_id"))
    resolved = _resolve_shipment_id(requested)
    st.session_state.active_page = "Tổng Quan Công Việc"
    st.session_state.active_shipment_id = resolved
    st.session_state.dashboard_active_shipment_id = resolved
    st.session_state.review_queue_return = True
    st.rerun()


def _entity_target(item: Mapping[str, Any]) -> tuple[str, str] | None:
    target = item.get("target") or {}
    if target.get("kind") == "entity":
        key = _value(target.get("key"))
        return "customer", key
    for entity_type, key in (("customer", item.get("customer")), ("factory", item.get("factory")), ("partner", item.get("partner"))):
        if _value(key) != UNKNOWN:
            return entity_type, _value(key)
    return None


def _open_entity(item: Mapping[str, Any]) -> None:
    target = _entity_target(item)
    if target is None:
        st.info("Entity context UNKNOWN — chưa có mapping source-bound để mở.")
        return
    entity_type, entity_key = target
    open_entity_context(entity_type, entity_key, return_page="Việc Cần Xử Lý")


def _open_finance_review(item: Mapping[str, Any]) -> None:
    shipment_id = _value(item.get("shipment_id"), "")
    st.session_state.active_page = "Đối Soát Tài Chính"
    st.session_state.finance_review_scope = "shipment" if shipment_id else "Tất cả"
    st.session_state.finance_review_target = shipment_id
    st.session_state.finance_review_return = False
    st.rerun()
def _status_label(item: Mapping[str, Any]) -> str:
    status = _value(item.get("status"))
    return f"{status} · {_value(item.get('title'))} · {_value(item.get('shipment_id'))}"


def _table_rows(items: list[Mapping[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in items:
        context = f"{_value(item.get('customer'))} · Sale {_value(item.get('owner'))}"
        entity_bits = []
        if _value(item.get("factory")) != UNKNOWN:
            entity_bits.append(f"Xưởng: {_value(item.get('factory'))}")
        if _value(item.get("partner")) != UNKNOWN:
            entity_bits.append(f"Đối tác: {_value(item.get('partner'))}")
        if entity_bits:
            context += " · " + " · ".join(entity_bits)
        rows.append(
            {
                "Mức": label_vi(_value(item.get("status"))),
                "Nhóm": label_vi(_value(item.get("category"))),
                "Việc cần xử lý": _value(item.get("title")),
                "Shipment": _value(item.get("shipment_id")),
                "Bối cảnh": context,
                "Việc tiếp theo": _value(item.get("next_action")),
                "Evidence / nguồn": _value(item.get("evidence")),
            }
        )
    return rows


def ui_review_queue() -> None:
    """Render the actionable review queue without adding a writer."""

    st.markdown(
        """
        <style>
        .review-kicker { color: #0B6E99; font-size: .68rem; font-weight: 800; letter-spacing: .14em; }
        .review-title { color: #102A43; font-size: 1.65rem; line-height: 1.15; margin: .15rem 0 .25rem; }
        .review-note { color: #475467; font-size: .82rem; border-left: 3px solid #0B6E99; background: #F0F7FA; padding: .6rem .8rem; margin: .65rem 0 1rem; }
        .review-readonly { color: #667085; font-size: .76rem; }
        .review-action { border-left: 3px solid #D97706; background: #FFFBEB; padding: .55rem .75rem; color: #7C4A03; }
        @media (max-width: 900px) { .review-title { font-size: 1.35rem; } }
        @media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition-duration: .01ms !important; animation-duration: .01ms !important; } }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div class='review-kicker'>VIỆC CẦN XỬ LÝ · CHỨNG TỪ + BẤT THƯỜNG</div>", unsafe_allow_html=True)
    st.markdown("<h1 class='review-title'>Chứng Từ & Việc Cần Xử Lý</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div class='review-note'><strong>Đây là work queue, không phải danh sách cảnh báo.</strong> "
        "Mỗi dòng có lý do, next action, nguồn/evidence và nơi mở để xử lý. UNKNOWN vẫn là UNKNOWN; queue không tự kết luận document completeness.</div>",
        unsafe_allow_html=True,
    )
    st.caption("Read-only projection · không có nút Resolve · không thay đổi ledger, payment, allocation, FX hay historical data.")

    shipments = st.session_state.get("db_shipments") or {}
    if not shipments:
        st.info("Chưa có shipment data để xây review queue.")
        return

    quotes = st.session_state.get("db_quotes") or {}
    agreements = st.session_state.get("db_agreements") or {}
    items = build_review_queue_items(shipments, agreements=agreements, quotes=quotes)
    summary = summarize_review_queue(items)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Cần xử lý", summary["total"])
    m2.metric("Nghiêm trọng", summary["critical"])
    m3.metric("Cần chú ý", summary["attention"])
    m4.metric("Đang chờ", summary["waiting"])
    m5.metric("Số lô hàng", summary["shipments"])

    categories = ["Tất cả"] + [label_vi(c) for c in CATEGORIES]
    _cat_by_vi = {label_vi(c): c for c in CATEGORIES}
    statuses = ["Tất cả"] + [label_vi(c) for c in STATUSES]
    _st_by_vi = {label_vi(c): c for c in STATUSES}
    shipment_options = ["Tất cả"] + sorted({_value(item.get("shipment_id")) for item in items})
    customer_options = ["Tất cả"] + sorted({_value(item.get("customer")) for item in items})
    factory_options = ["Tất cả"] + sorted({_value(item.get("factory")) for item in items if _value(item.get("factory")) != UNKNOWN})
    partner_options = ["Tất cả"] + sorted({_value(item.get("partner")) for item in items if _value(item.get("partner")) != UNKNOWN})

    # Keep the work table in the first viewport; filters stay one click away
    # in a popover instead of becoming the primary page content.
    with st.popover("🔎 Tìm kiếm & lọc", use_container_width=True):
        search = st.text_input("Tìm theo shipment, customer, reason, việc tiếp theo, source", key="review_queue_search")
        f1, f2, f3 = st.columns(3)
        category = f1.selectbox("Nhóm", categories, key="review_queue_category")
        status = f2.selectbox("Trạng thái", statuses, key="review_queue_status")
        severity = f3.selectbox("Mức độ", ["Tất cả", label_vi(STATUS_CRITICAL), label_vi(STATUS_ATTENTION), label_vi(STATUS_WAITING), label_vi(STATUS_REVIEW)], key="review_queue_severity")
        f4, f5, f6, f7 = st.columns(4)
        shipment_id = f4.selectbox("Lô hàng", shipment_options, key="review_queue_shipment")
        customer = f5.selectbox("Khách hàng", customer_options, key="review_queue_customer")
        factory = f6.selectbox("Xưởng", factory_options, key="review_queue_factory")
        partner = f7.selectbox("Đối tác", partner_options, key="review_queue_partner")

    filter_category = _cat_by_vi.get(category, category)
    filter_status = _st_by_vi.get(status, status)
    filter_severity = {label_vi(STATUS_CRITICAL): STATUS_CRITICAL, label_vi(STATUS_ATTENTION): STATUS_ATTENTION,
                       label_vi(STATUS_WAITING): STATUS_WAITING, label_vi(STATUS_REVIEW): STATUS_REVIEW}.get(severity, severity)
    filtered = filter_review_queue_items(
        items,
        search=search,
        category=filter_category,
        status=filter_status,
        severity=filter_severity,
        shipment_id=shipment_id,
        customer=customer,
        factory=factory,
        partner=partner,
    )
    st.markdown(
        f"**{len(filtered)} / {len(items)} mục** · bộ lọc không làm thay đổi dữ liệu nguồn · "
        "mở một dòng để xem reason và đi đúng workspace."
    )
    if not filtered:
        if any((search, category != "Tất cả", status != "Tất cả", severity != "Tất cả", shipment_id != "Tất cả", customer != "Tất cả", factory != "Tất cả", partner != "Tất cả")):
            st.info("Không có mục phù hợp với bộ lọc. Đây không có nghĩa là toàn hệ thống đã hoàn tất.")
        else:
            st.success("Không có mục cần xử lý từ các source hiện tại.")
        return

    st.dataframe(_table_rows(filtered), hide_index=True, use_container_width=True, height=min(620, 110 + len(filtered) * 42))
    item_ids = [_value(item.get("item_id")) for item in filtered]
    selected_id = st.session_state.get("review_selected_item")
    if selected_id not in item_ids:
        selected_id = item_ids[0]
        st.session_state.review_selected_item = selected_id
    selected_id = st.selectbox(
        "Chọn mục để xem chi tiết / mở workspace",
        item_ids,
        index=item_ids.index(selected_id),
        format_func=lambda value: _status_label(next(item for item in filtered if item.get("item_id") == value)),
        key="review_selected_item",
    )
    selected = next(item for item in filtered if item.get("item_id") == selected_id)
    st.markdown(
        f"<div class='review-action'><strong>{_value(selected.get('status'))} · {_value(selected.get('title'))}</strong><br>"
        f"Lý do: {_value(selected.get('reason'))}<br>"
        f"Việc tiếp theo: {_value(selected.get('next_action'))}<br>"
        f"Nguồn: {_value(selected.get('source'))} · Evidence: {_value(selected.get('evidence'))}</div>",
        unsafe_allow_html=True,
    )
    b1, b2, b3 = st.columns([1.35, 1.35, 3.3])
    if b1.button("Mở Hồ Sơ Lô 360°", type="primary", use_container_width=True, key="review_open_shipment"):
        _open_shipment(selected)
    if b2.button("Mở Ngữ Cảnh Đối Tác", use_container_width=True, key="review_open_entity"):
        _open_entity(selected)
    if selected.get("category") == CATEGORY_FINANCIAL:
        if b3.button("Mở Đối Soát Tài Chính", use_container_width=True, key="review_open_finance"):
            _open_finance_review(selected)
    elif selected.get("category") == CATEGORY_COMMERCIAL:
        if b3.button("Mở Thỏa Thuận & Bàn Giao", use_container_width=True, key="review_open_commercial"):
            _open_commercial(selected)
    else:
        b3.caption("Điều hướng workspace chỉ đọc; không có nút Resolve và không thay đổi dữ liệu tài chính.")


def _open_commercial(item: Mapping[str, Any]) -> None:
    """Navigate to the commercial agreement/quote targeted by a COMMERCIAL review item."""

    target = item.get("target") or {}
    kind = target.get("kind")
    key = _value(target.get("key"))
    if kind == "agreement":
        st.session_state.agreement_detail_id = key
        st.session_state.active_page = "Thỏa Thuận & Bàn Giao"
        st.rerun()
    if kind == "quote":
        st.session_state.quote_detail_id = key
        st.session_state.active_page = "Kinh Doanh & Báo Giá"
        st.rerun()
    st.session_state.active_page = "Thỏa Thuận & Bàn Giao"
    st.rerun()

__all__ = ["ui_review_queue"]
