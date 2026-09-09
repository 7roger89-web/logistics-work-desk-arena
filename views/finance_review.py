"""Finance Review read-only investigation workspace for LOG-C11."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd
import streamlit as st
from views.lg_core import nav_to_page  # noqa: E402

from core.finance_review import (
    ACTIONABLE_STATUSES,
    STATUS_CONFIRMED,
    STATUS_MISSING_EVIDENCE,
    STATUS_REVIEW,
    STATUS_RESTRICTED,
    STATUS_UNKNOWN,
    build_finance_review_from_db,
)
from core.shipment_360 import UNKNOWN
from views.entity_context import open_entity_context


def _value(value: Any, default: str = UNKNOWN) -> str:
    if value in (None, ""):
        return default
    return str(value)


def _money(value: Any, currency: Any) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0.0
    return f"{number:,.2f} {_value(currency, UNKNOWN)}"


def _shipment_id(item: Mapping[str, Any]) -> str:
    values = item.get("shipment_ids") or []
    if isinstance(values, str):
        return values
    return _value(values[0]) if values else UNKNOWN


def _table_rows(items: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "Trạng thái": _value(item.get("status")),
            "Bucket": _value(item.get("bucket")),
            "Record": _value(item.get("record_id")),
            "Payer": _value(item.get("payer")),
            "Payee": _value(item.get("payee")),
            "Holder": _value(item.get("holder")),
            "Beneficial owner": _value(item.get("beneficial_owner")),
            "Currency": _value(item.get("currency")),
            "Amount": _money(item.get("amount"), item.get("currency")),
            "Allocated": _money(item.get("allocated"), item.get("currency")),
            "Outstanding / remainder": _money(item.get("outstanding"), item.get("currency")),
            "Due": _value(item.get("due_date")),
            "Shipment": _shipment_id(item),
        }
        for item in items
    ]


def _open_shipment(item: Mapping[str, Any]) -> None:
    shipment_id = _shipment_id(item)
    if shipment_id == UNKNOWN:
        st.info("Shipment mapping UNKNOWN — không tự suy diễn destination.")
        return
    shipments = st.session_state.get("db_shipments") or {}
    resolved = shipment_id
    if isinstance(shipments, Mapping) and shipment_id not in shipments:
        resolved = next(
            (str(key) for key, shipment in shipments.items()
             if str(key).casefold() == shipment_id.casefold()
             or (isinstance(shipment, Mapping) and str(shipment.get("shipment_id") or shipment.get("id") or "").casefold() == shipment_id.casefold())),
            shipment_id,
        )
    nav_to_page("Tổng Quan Công Việc")
    st.session_state.active_shipment_id = resolved
    st.session_state.dashboard_active_shipment_id = resolved
    st.session_state.finance_review_return = True
    st.rerun()


def _open_entity(item: Mapping[str, Any]) -> None:
    entity_type = _value(item.get("party_type"), "").casefold()
    entity_key = _value(item.get("party_id"), "")
    if entity_key == UNKNOWN:
        entity_key = _value(item.get("party"), "")
    if entity_type not in {"customer", "partner", "factory"} or not entity_key:
        st.info("Entity mapping UNKNOWN — chưa có source-bound context để mở.")
        return
    open_entity_context(entity_type, entity_key, return_page="Đối Soát Tài Chính")


def _back_to_queue() -> None:
    nav_to_page("Việc Cần Xử Lý")
    st.session_state.finance_review_return = False
    st.session_state.review_queue_return = False
    st.rerun()


def _summary_rows(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for currency, values in (summary.get("totals_by_currency") or {}).items():
        rows.append({
            "Currency": currency,
            "Confirmed obligation outstanding": _money(values.get("confirmed_outstanding"), currency),
            "Confirmed unallocated remainder": _money(values.get("confirmed_unallocated"), currency),
            "Excluded UNKNOWN/restricted/review/evidence": _money(values.get("excluded_amount"), currency),
            "Formula": "confirmed excludes uncertain/restricted/review states",
        })
    return rows


def _render_partner_position(snapshot: Mapping[str, Any]) -> None:
    position = snapshot.get("partner_position") or {}
    totals = position.get("totals_by_currency") or {}
    if not totals:
        return
    st.markdown("#### Partner position — canonical read model")
    rows = []
    for currency, values in sorted(totals.items()):
        rows.append({
            "Currency": currency,
            "TT phải trả partner": _money(values.get("payable_to_partner"), currency),
            "Partner đang giữ credit": _money(values.get("held_credit"), currency),
            "Partner nhận hộ": _money(values.get("received_on_behalf"), currency),
            "Partner chi hộ": _money(values.get("paid_on_behalf"), currency),
            "Unallocated": _money(values.get("unallocated"), currency),
            "Net secondary": _money(values.get("net_after_valid_allocations"), currency),
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    if position.get("status") != STATUS_CONFIRMED:
        st.warning(
            f"Partner position cần review: {position.get('unknown_count', 0)} UNKNOWN/REVIEW, "
            f"{position.get('restricted_count', 0)} restricted."
        )


def ui_finance_review() -> None:
    st.markdown("<div class='review-kicker'>FINANCIAL CONTROL · READ-ONLY INVESTIGATION</div>", unsafe_allow_html=True)
    st.title("Đối Soát Tài Chính")
    st.caption(
        "Ai phải trả ai, bao nhiêu, tiền tệ gì, đã allocation thế nào và vì sao ra số này. "
        "Canonical ledger là source of truth; không có nút sửa số dư, Resolve hay auto-allocation."
    )

    if st.session_state.get("finance_review_return"):
        if st.button("← Quay lại Finance Review", key="finance_review_return_button"):
            st.session_state.finance_review_return = False
            st.rerun()

    st.session_state.setdefault("finance_review_scope", "Tất cả")
    st.session_state.setdefault("finance_review_target", "")
    st.session_state.setdefault("finance_review_sale_owner", "")
    st.session_state.setdefault("finance_review_currency", "")
    st.session_state.setdefault("finance_review_search", "")
    f1, f2, f3, f4 = st.columns([1.2, 1.6, 1.6, 1.4])
    scope = f1.selectbox("Scope", ["Tất cả", "partner", "customer", "shipment"], key="finance_review_scope")
    target = f2.text_input("Partner / Customer / Shipment", key="finance_review_target", placeholder="ID hoặc tên canonical")
    sale_owner = f3.text_input("SALE owner (optional)", key="finance_review_sale_owner", placeholder="Chỉ lọc canonical field")
    currency = f4.text_input("Currency", key="finance_review_currency", placeholder="USD / CNY / VND")
    search = st.text_input("Tìm record, payer/payee, holder, reason, reference", key="finance_review_search")

    party_type = None if scope in {"Tất cả", "shipment"} else scope
    party_id = None if scope in {"Tất cả", "shipment"} or not target.strip() else target.strip()
    shipment_id = target.strip() if scope == "shipment" and target.strip() else None
    snapshot = build_finance_review_from_db(
        party_type=party_type,
        party_id=party_id,
        shipment_id=shipment_id,
        internal_sale_owner=sale_owner.strip() or None,
        currency=currency.strip() or None,
        search=search.strip(),
    )

    if snapshot.get("error"):
        st.warning(f"Finance Review chưa đọc được canonical source: {snapshot['error']}")
        st.info("Không có dữ liệu thay thế hoặc số dư suy diễn nào được hiển thị.")
        return

    items = list(snapshot.get("items") or [])
    summary = snapshot.get("summary") or {}
    st.dataframe(
        pd.DataFrame(_summary_rows(summary) or [{"Currency": UNKNOWN, "Formula": "Chưa có canonical finance record phù hợp"}]),
        hide_index=True,
        use_container_width=True,
    )
    counts = summary.get("counts") or {}
    st.caption(
        f"{len(items)} financial records · {sum(counts.get(status, 0) for status in ACTIONABLE_STATUSES)} actionable/review signals · "
        "UNKNOWN/restricted/evidence không được âm thầm cộng vào confirmed totals."
    )
    st.info('Tổng thương mại trên bảng này là số ước tính theo công thức, không phải số tiền thực tế đã thanh toán. Đối chiếu với sổ sách kế toán trước khi quyết định.')
    _render_partner_position(snapshot)

    if not items:
        st.info("Không có canonical financial record phù hợp. Điều này không đồng nghĩa hệ thống đã complete.")
        return

    st.markdown("#### Investigation queue")
    st.dataframe(_table_rows(items), hide_index=True, use_container_width=True, height=min(660, 120 + len(items) * 42))
    item_ids = [_value(item.get("item_id")) for item in items]
    selected_id = st.selectbox("Chọn financial item để xem lineage", item_ids, key="finance_review_selected_item")
    selected = next(item for item in items if item.get("item_id") == selected_id)
    st.markdown(
        f"**{_value(selected.get('status'))} · {_value(selected.get('record_type'))} · {_value(selected.get('record_id'))}**  \n"
        f"Reason: {_value(selected.get('reason'))}  \n"
        f"Next action: {_value(selected.get('next_action'))}"
    )
    st.code(_value(selected.get("formula")), language="text")
    evidence = selected.get("evidence") or []
    with st.expander("Evidence / source / correction lineage", expanded=True):
        st.write({
            "source": selected.get("source"),
            "source_record_ids": selected.get("source_record_ids"),
            "evidence": evidence,
            "raw_record": selected.get("raw_record"),
        })

    b1, b2, b3 = st.columns([1.35, 1.35, 2.5])
    if b1.button("Mở Shipment 360", type="primary", use_container_width=True, key="finance_open_shipment"):
        _open_shipment(selected)
    if b2.button("Mở Customer / Partner", use_container_width=True, key="finance_open_entity"):
        _open_entity(selected)
    if b3.button("← Về Review Queue", use_container_width=True, key="finance_back_queue"):
        _back_to_queue()
    st.caption("Finance Review chỉ đọc projection và evidence; không có mutation path trong workspace này.")


__all__ = ["ui_finance_review"]
