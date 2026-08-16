"""Bounded read-only partner financial projection renderer."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd
import streamlit as st

from core.financial_ledger import build_partner_financial_position


def _party_label(value: Any) -> str:
    if isinstance(value, Mapping):
        return str(value.get("name") or value.get("party_id") or "UNKNOWN")
    return str(value or "UNKNOWN")


def _money(value: Any, currency: str) -> str:
    try:
        return f"{float(value):,.0f} {currency}".strip()
    except (TypeError, ValueError):
        return f"UNKNOWN {currency}".strip()


def _table_rows(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        result.append(
            {
                "ID": row.get("obligation_id") or row.get("transaction_id") or row.get("allocation_id"),
                "Shipment": ", ".join(str(item) for item in row.get("shipment_ids") or []) or "Chưa gắn shipment",
                "Từ": _party_label(row.get("from_party") or row.get("source_party")),
                "Đến/đang giữ": _party_label(row.get("to_party") or row.get("holder_party")),
                "Chủ sở hữu tiền": _party_label(row.get("beneficial_owner")),
                "Mục đích": row.get("purpose") or row.get("transaction_kind") or "",
                "Đã phân bổ": _money(row.get("allocated"), row.get("currency") or ""),
                "Còn lại": _money(row.get("outstanding", row.get("unallocated")), row.get("currency") or ""),
                "Trạng thái": row.get("review_reason") or row.get("classification_status") or "CONFIRMED",
                "Công thức": row.get("formula") or "",
            }
        )
    return result


def render_partner_financial_position() -> None:
    """Render the canonical partner projection without any mutation control."""

    st.markdown("### A Bò — Sale Thành · Đối soát tài chính đọc-only")
    st.caption(
        "Projection chỉ đọc từ canonical ledger. Không chỉnh số dư trực tiếp; "
        "UNKNOWN/RESTRICTED không được cộng vào vị trí đã xác nhận."
    )

    c1, c2, c3 = st.columns(3)
    party_id = c1.text_input("Mã đối tác", value="ABO", key="ledger_partner_id")
    party_name = c2.text_input("Tên hiển thị", value="A Bò", key="ledger_partner_name")
    sale_owner = c3.text_input("Sale nội bộ", value="Thành", key="ledger_internal_sale_owner")
    party = {"party_type": "partner", "party_id": party_id.strip(), "name": party_name.strip()}
    if not party["party_id"]:
        st.warning("Cần mã đối tác để đọc projection.")
        return

    position = build_partner_financial_position(party, internal_sale_owner=sale_owner.strip() or None)
    if position.get("error"):
        st.info(f"Chưa đọc được canonical ledger: {position['error']}")
        return

    totals = position.get("totals_by_currency") or {}
    if not totals and not (position.get("buckets") or {}).get("unknown") and not (position.get("buckets") or {}).get("restricted"):
        st.info("Chưa có canonical ledger record phù hợp với đối tác/sale đang chọn.")
        return

    if position.get("status") != "CONFIRMED":
        st.warning(
            f"Vị trí cần review: {position.get('unknown_count', 0)} khoản UNKNOWN/REVIEW_REQUIRED, "
            f"{position.get('restricted_count', 0)} khoản RESTRICTED."
        )

    for currency, values in sorted(totals.items()):
        st.markdown(f"#### Tiền tệ: {currency}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("TT phải trả A Bò", _money(values.get("payable_to_partner"), currency))
        m2.metric("A Bò đang giữ/credit", _money(values.get("held_credit"), currency))
        m3.metric("Chưa phân bổ", _money(values.get("unallocated"), currency))
        m4.metric("Net sau allocation hợp lệ", _money(values.get("net_after_valid_allocations"), currency))

    buckets = position.get("buckets") or {}
    with st.expander("Chi tiết các bucket", expanded=True):
        for key, label in (
            ("payable_to_partner", "TT phải trả A Bò"),
            ("held_credit", "A Bò đang giữ/credit"),
            ("received_on_behalf", "Nhận hộ"),
            ("unallocated", "Chưa phân bổ"),
            ("restricted", "RESTRICTED"),
            ("unknown", "UNKNOWN / REVIEW_REQUIRED"),
        ):
            rows = buckets.get(key) or []
            st.markdown(f"**{label}** · {len(rows)} dòng")
            if rows:
                st.dataframe(pd.DataFrame(_table_rows(rows)), hide_index=True, use_container_width=True)
            else:
                st.caption("Không có dòng.")

    with st.expander("Vì sao ra số này?", expanded=False):
        explanations = position.get("explanations") or []
        if explanations:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Bucket": item.get("label") or item.get("bucket"),
                            "Số tiền": _money(item.get("value"), item.get("currency") or ""),
                            "Công thức": item.get("formula") or "",
                            "Nguồn record": ", ".join(str(value) for value in item.get("source_record_ids") or []),
                            "Loại trừ confirmed": "Có" if item.get("excluded_from_confirmed") else "Không",
                        }
                        for item in explanations
                    ]
                ),
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption("Chưa có dòng giải thích từ canonical ledger.")

    recent = position.get("recent_allocations") or []
    with st.expander("Allocation gần đây", expanded=False):
        if recent:
            st.dataframe(pd.DataFrame(recent), hide_index=True, use_container_width=True)
        else:
            st.caption("Chưa có allocation.")


__all__ = ["render_partner_financial_position"]
