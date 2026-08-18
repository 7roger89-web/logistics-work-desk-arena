"""Read-only A Bò / SALE Thành reconciliation desk.

The view is deliberately a thin Streamlit consumer of the canonical partner
projection and the pure helpers in ``core.reconciliation``.  It contains no
financial write control, no manual balance, and no owner inference.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Any
from uuid import uuid4

import pandas as pd
import streamlit as st

from core.database import get_db
from core.debit_draft import (
    DEBIT_STATUS_READY_FOR_REVIEW,
    REPORT_STATUS_READY_FOR_REVIEW,
    build_debit_draft,
    build_manager_report,
)
from core.debit_snapshot import (
    DebitSnapshotConflictError,
    get_debit_draft_snapshot,
    list_debit_draft_snapshots,
    save_debit_draft_snapshot,
)
from core.financial_ledger import build_partner_financial_position
from core.reconciliation import (
    BUCKET_LABELS,
    REVIEW_CATEGORY_LABELS,
    build_all_currency_explanations,
    build_money_location_trace,
    build_period_reconciliation,
    build_review_inbox,
    compare_reported_position,
    search_partner_position,
)
from core.utils import to_decimal
from views.historical_review import ui_historical_review


PARTNER = {"party_type": "partner", "party_id": "ABO", "name": "A Bò"}
SALE_OWNER = "Thành"
_VIEW_STATE_KEY = "log_c05_partner_view"
_SNAPSHOT_REQUEST_KEY = "log_c05_snapshot_request_id"


def _session_state() -> Any | None:
    state = getattr(st, "session_state", None)
    if callable(getattr(state, "get", None)) and hasattr(state, "__setitem__"):
        return state
    return None


def _state_get(key: str, default: Any = None) -> Any:
    state = _session_state()
    if state is None:
        return default
    try:
        return state.get(key, default)
    except Exception:
        return default


def _state_set(key: str, value: Any) -> None:
    state = _session_state()
    if state is None:
        return
    try:
        state[key] = value
    except Exception:
        return


def _rerun() -> None:
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()


def _set_partner_view(view: str) -> None:
    _state_set(_VIEW_STATE_KEY, view)
    _rerun()


def _mode_navigation() -> str:
    mode = str(_state_get(_VIEW_STATE_KEY, "desk") or "desk")
    if mode != "desk":
        if st.button("← Quay lại bàn đối soát", key="log_c05_back_to_desk"):
            _set_partner_view("desk")
        return mode
    st.markdown("### Tác vụ LOG-C05")
    st.caption("Mở báo cáo quản lý hoặc Debit Draft được tính từ cùng projection canonical; không nhập tay tổng debit.")
    if st.button("Rà soát lịch sử", key="log_c06_open_historical_review"):
        _set_partner_view("historical_review")
    if st.button("Báo cáo Sếp", key="log_c05_open_report"):
        _set_partner_view("report")
    if st.button("Debit Draft", key="log_c05_open_debit"):
        _set_partner_view("debit")
    return mode


def _debit_line_table(
    lines: list[Mapping[str, Any]],
    currency: str,
    *,
    excluded: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in lines:
        rows.append(
            {
                "Record": line.get("record_id") or "",
                "Bucket": line.get("label") or BUCKET_LABELS.get(line.get("bucket"), line.get("bucket")),
                "Số tiền": _money(line.get("amount"), currency),
                "Shipment": ", ".join(str(value) for value in line.get("shipment_ids") or []) or "Chưa gắn shipment",
                "Allocation": ", ".join(str(value) for value in line.get("allocation_ids") or []),
                "Nguồn": ", ".join(str(value) for value in line.get("source_record_ids") or []),
                "Lý do loại": (line.get("reason") or line.get("category") or "") if excluded else "",
            }
        )
    return rows


def _show_snapshot_references(snapshot: Mapping[str, Any]) -> None:
    st.caption(
        f"Snapshot {snapshot.get('snapshot_id')} · V{snapshot.get('version')} · "
        f"{snapshot.get('status')} · hash {snapshot.get('content_hash')}"
    )
    st.json(
        {
            "ledger_record_ids": snapshot.get("ledger_record_ids") or [],
            "obligation_ids": snapshot.get("obligation_ids") or [],
            "transaction_ids": snapshot.get("transaction_ids") or [],
            "allocation_ids": snapshot.get("allocation_ids") or [],
            "correction_ids": snapshot.get("correction_ids") or [],
            "financial_effect_write_count": snapshot.get("financial_effect_write_count", 0),
        }
    )


def _render_manager_report(position: Mapping[str, Any]) -> None:
    report = build_manager_report(
        position,
        report_date=date.today(),
        status=REPORT_STATUS_READY_FOR_REVIEW,
    )
    st.title("BÁO CÁO CÔNG NỢ A BÒ — SALE THÀNH")
    period = report.get("period") or {}
    st.caption(
        f"Kỳ: {period.get('start') or 'Tất cả'} → {period.get('end') or 'Tất cả'} · "
        f"Ngày tạo: {report.get('report_date') or 'Chưa rõ'} · SALE {report.get('sale_owner') or SALE_OWNER} · "
        f"Đối tác: {_party_label(report.get('party'))} · {report.get('status')}"
    )
    summaries = report.get("summary_by_currency") or {}
    if not summaries:
        st.info("Chưa có dữ liệu canonical đủ điều kiện để lập báo cáo cho A Bò / SALE Thành.")
        return
    for currency, values in sorted(summaries.items()):
        st.markdown(f"## {currency}")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("TT phải trả A Bò", _money(values.get("payable_to_partner"), currency))
        m2.metric("A Bò đang giữ / credit", _money(values.get("held_credit"), currency))
        m3.metric("A Bò đã nhận hộ", _money(values.get("received_on_behalf"), currency))
        m4.metric("A Bò đã chi hộ", _money(values.get("paid_on_behalf"), currency))
        m5.metric("Debit eligible", _money(values.get("debit_eligible_amount"), currency))
        preview_values = (report.get("debit_preview") or {}).get("by_currency", {}).get(currency) or {}
        st.caption(
            f"Confirmed position: {_money(values.get('confirmed_position'), currency)} · "
            f"Review cần xử lý: {_money(values.get('review_required_amount'), currency)} · "
            f"Dòng debit đủ điều kiện: {len(preview_values.get('included_items') or [])}"
        )
        explanation = (report.get("explanations") or {}).get(currency) or {}
        with st.expander(f"DIỄN GIẢI SỐ LIỆU · {currency}", expanded=False):
            st.write(explanation.get("formula") or f"0 {currency}")
            included = explanation.get("included_lines") or []
            excluded = explanation.get("excluded_lines") or []
            if included:
                st.markdown("**Dòng đã dùng để tính confirmed/debit**")
                st.dataframe(
                    pd.DataFrame(_debit_line_table(included, currency)),
                    hide_index=True,
                    use_container_width=True,
                )
            if excluded:
                st.markdown("**Dòng hiển thị để review nhưng không cộng vào debit**")
                st.dataframe(
                    pd.DataFrame(_debit_line_table(excluded, currency, excluded=True)),
                    hide_index=True,
                    use_container_width=True,
                )
            st.caption(
                "Công thức và source IDs được sinh lại theo projection; partner-reported difference không tự động cộng vào debit."
            )
    shipments = report.get("important_shipments") or []
    st.markdown("### Shipment quan trọng")
    if shipments:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Shipment": row.get("shipment_id"),
                        "Tiền tệ": row.get("currency"),
                        "Ảnh hưởng": _money(row.get("impact_amount"), row.get("currency") or ""),
                        "Số dòng": row.get("line_count"),
                        "Nguồn": ", ".join(str(value) for value in row.get("source_record_ids") or []),
                    }
                    for row in shipments
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.caption("Chưa có shipment linkage trong các dòng hiện tại.")
    differences = [row for row in report.get("partner_difference") or [] if row.get("has_difference")]
    if differences:
        st.markdown("### Chênh lệch A Bò báo lại — không tự cộng vào Debit")
        st.warning(
            "Các chênh lệch này chỉ là đầu mối đối soát; cần xác minh với A Bò trước khi thay đổi dữ liệu canonical."
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Tiền tệ": row.get("currency"),
                        "Canonical confirmed": _money(row.get("system_confirmed"), row.get("currency") or ""),
                        "A Bò báo": _money(row.get("partner_reported"), row.get("currency") or ""),
                        "Chênh lệch": _money(row.get("difference"), row.get("currency") or ""),
                        "Xử lý": row.get("action"),
                    }
                    for row in differences
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
    st.caption("Báo cáo này là read-only; READY_FOR_REVIEW không đồng nghĩa đã được phê duyệt hay đã thanh toán.")


def _render_debit_draft(position: Mapping[str, Any]) -> None:
    draft = build_debit_draft(position, status="DRAFT")
    st.title("DEBIT DRAFT — A BÒ / SALE THÀNH")
    st.caption("DRAFT · Tính riêng từng loại tiền · Không có nút thanh toán · Không nhập tay tổng debit")
    by_currency = draft.get("by_currency") or {}
    if not by_currency:
        st.info("Chưa có dữ liệu canonical đủ điều kiện để lập Debit Draft cho A Bò / SALE Thành.")
        return
    eligible = False
    for currency, values in sorted(by_currency.items()):
        ready_amount = float(to_decimal(values.get("debit_ready_amount", 0)))
        eligible = eligible or ready_amount > 0
        st.markdown(f"## Debit Draft · {currency}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Payable subtotal", _money(values.get("payable_subtotal"), currency))
        m2.metric("Credit / settlement", _money(values.get("credit_subtotal"), currency))
        m3.metric("Đã settled / allocated", _money(values.get("settled_amount"), currency))
        m4.metric("Debit ready", _money(ready_amount, currency))
        with st.expander(f"Vì sao debit ra số này? · {currency}", expanded=True):
            st.write(values.get("formula") or f"0 {currency}")
            st.caption("Số tiền lấy từ payable, credit và allocation history; dòng review không được tự động đưa vào.")
        included = values.get("included_items") or []
        excluded = values.get("excluded_items") or []
        st.markdown("### Dòng được cộng vào Debit")
        if included:
            st.dataframe(
                pd.DataFrame(_debit_line_table(included, currency)),
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption("Chưa có dòng confirmed đủ điều kiện.")
        st.markdown("### Dòng bị loại khỏi Debit")
        if excluded:
            st.dataframe(
                pd.DataFrame(_debit_line_table(excluded, currency, excluded=True)),
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption("Không có dòng bị loại trong currency này.")
        st.caption(
            f"References: ledger={len((values.get('references') or {}).get('ledger_record_ids') or [])}, "
            f"obligation={len((values.get('references') or {}).get('obligation_ids') or [])}, "
            f"transaction={len((values.get('references') or {}).get('transaction_ids') or [])}, "
            f"allocation={len((values.get('references') or {}).get('allocation_ids') or [])}"
        )

    db = get_db() if eligible else None
    if not eligible:
        st.info("Chưa có số debit đủ điều kiện để lưu READY_FOR_REVIEW; các dòng review vẫn chỉ là review.")
    elif db is None:
        st.warning("MongoDB metadata chưa sẵn sàng; nút snapshot bị khóa. Không ghi số thay thế vào canonical ledger.")
    request_id = str(_state_get(_SNAPSHOT_REQUEST_KEY, "") or "")
    if not request_id:
        request_id = f"LOG-C05-{uuid4().hex}"
        _state_set(_SNAPSHOT_REQUEST_KEY, request_id)
    if st.button(
        "Lưu READY_FOR_REVIEW snapshot",
        disabled=db is None or not eligible,
        key="log_c05_save_snapshot",
    ):
        try:
            ready_draft = build_debit_draft(position, status=DEBIT_STATUS_READY_FOR_REVIEW)
            ready_report = build_manager_report(position, status=REPORT_STATUS_READY_FOR_REVIEW)
            current_user = _state_get("current_user", {})
            prepared_by = str(current_user.get("username") or "system") if isinstance(current_user, Mapping) else "system"
            result = save_debit_draft_snapshot(
                db,
                ready_draft,
                manager_report=ready_report,
                request_id=request_id,
                prepared_by=prepared_by,
            )
            st.success(f"Snapshot {result['snapshot'].get('snapshot_id')} đã sẵn sàng để review ({result['message']}).")
            _show_snapshot_references(result["snapshot"])
        except DebitSnapshotConflictError as exc:
            st.error(str(exc))
        except (TypeError, ValueError, RuntimeError) as exc:
            st.error(f"Không lưu được snapshot metadata: {exc}")

    if db is None:
        return
    period = draft.get("period") or {}
    try:
        snapshots = list_debit_draft_snapshots(
            db,
            party_key=str(draft.get("party_key") or ""),
            sale_owner=str(draft.get("internal_sale_owner") or SALE_OWNER),
            period=period,
        )
    except (TypeError, ValueError, RuntimeError) as exc:
        st.warning(f"Chưa đọc được lịch sử snapshot: {exc}")
        return
    st.markdown("### Snapshot đã lưu / mở lại")
    if not snapshots:
        st.caption("Chưa có snapshot metadata cho kỳ và owner này.")
        return
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Version": row.get("version"),
                    "Status": row.get("status"),
                    "Snapshot ID": row.get("snapshot_id"),
                    "Hash": row.get("content_hash"),
                    "Tạo bởi": row.get("prepared_by"),
                }
                for row in snapshots
            ]
        ),
        hide_index=True,
        use_container_width=True,
    )
    labels = [f"V{row.get('version')} · {row.get('snapshot_id')}" for row in snapshots]
    selected_label = st.selectbox(
        "Chọn snapshot để mở lại / tạo phiên bản mới",
        labels,
        key="log_c05_snapshot_select",
    )
    selected = snapshots[labels.index(selected_label)] if selected_label in labels else snapshots[0]
    c1, c2 = st.columns(2)
    if c1.button("Mở lại snapshot", key="log_c05_reopen_snapshot"):
        reopened = get_debit_draft_snapshot(db, snapshot_id=selected.get("snapshot_id"))
        if reopened:
            _show_snapshot_references(reopened)
            st.info(f"Đang đọc lại nội dung đã lưu của V{reopened.get('version')}; hash không phụ thuộc thời điểm mở lại.")
        else:
            st.warning("Không tìm thấy snapshot đã chọn.")
    if c2.button("Tạo phiên bản mới", key="log_c05_regenerate_snapshot"):
        try:
            next_version = int(selected.get("version") or 0) + 1
            result = save_debit_draft_snapshot(
                db,
                build_debit_draft(position, status=DEBIT_STATUS_READY_FOR_REVIEW),
                manager_report=build_manager_report(position, status=REPORT_STATUS_READY_FOR_REVIEW),
                request_id=f"{selected.get('snapshot_id')}-v{next_version}",
                version=next_version,
                supersedes_snapshot_id=selected.get("snapshot_id"),
                prepared_by="system",
            )
            st.success(f"Đã tạo V{result['snapshot'].get('version')} và giữ lại phiên bản trước.")
        except (DebitSnapshotConflictError, TypeError, ValueError, RuntimeError) as exc:
            st.error(f"Không tạo được phiên bản mới: {exc}")


def _money(value: Any, currency: str) -> str:
    try:
        return f"{float(to_decimal(value)):,.0f} {currency}".strip()
    except (TypeError, ValueError, ArithmeticError):
        return f"Chưa rõ {currency}".strip()


def _party_label(value: Any) -> str:
    if isinstance(value, Mapping):
        return str(value.get("name") or value.get("party_id") or "Chưa rõ")
    return str(value or "Chưa rõ")


def _row_id(row: Mapping[str, Any]) -> str:
    return str(
        row.get("record_id")
        or row.get("obligation_id")
        or row.get("transaction_id")
        or row.get("allocation_id")
        or ""
    )


def _row_amount(row: Mapping[str, Any], bucket: str | None = None) -> float:
    if bucket == "payable_to_partner":
        return float(to_decimal(row.get("outstanding", 0)))
    if bucket == "received_on_behalf":
        return float(to_decimal(row.get("received_amount", row.get("amount", 0))))
    if bucket == "paid_on_behalf":
        return float(to_decimal(row.get("spent_amount", row.get("amount", 0))))
    return float(to_decimal(row.get("unallocated", row.get("outstanding", row.get("amount", 0)))))


def _row_table(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        bucket = str(row.get("bucket") or "")
        currency = str(row.get("currency") or "UNKNOWN")
        result.append(
            {
                "Mã dòng": _row_id(row),
                "Shipment": ", ".join(str(item) for item in row.get("shipment_ids") or [])
                or "Chưa gắn shipment",
                "Từ": _party_label(row.get("from_party") or row.get("source_party")),
                "Đến / đang giữ": _party_label(row.get("to_party") or row.get("holder_party")),
                "Chủ sở hữu hưởng lợi": _party_label(row.get("beneficial_owner")),
                "Số tiền": _money(_row_amount(row, bucket), currency),
                "Còn chưa phân bổ": _money(
                    row.get("remaining_unallocated", row.get("unallocated", row.get("outstanding", 0))),
                    currency,
                ),
                "Trạng thái": row.get("allocation_status")
                or row.get("review_reason")
                or row.get("classification_status")
                or "Đã xác minh",
                "Ghi chú / mục đích": row.get("note") or row.get("purpose") or row.get("transaction_kind") or "",
            }
        )
    return result


def _show_table(rows: list[Mapping[str, Any]], *, empty_text: str = "Không có dòng.") -> None:
    if rows:
        st.dataframe(pd.DataFrame(_row_table(rows)), hide_index=True, use_container_width=True)
    else:
        st.caption(empty_text)


def _show_owner_coverage(position: Mapping[str, Any]) -> None:
    coverage = position.get("owner_coverage") or {}
    related = int(coverage.get("related_record_count") or 0)
    missing = int(coverage.get("missing_owner_count") or 0)
    matched = int(coverage.get("matching_owner_count") or 0)
    if not related:
        st.info(
            "Chưa có dòng canonical nào được gắn SALE Thành. Màn hình không suy đoán "
            "từ ghi chú, địa chỉ hay tên khách hàng."
        )
        return
    if not matched:
        st.warning(
            "Có dữ liệu liên quan nhưng chưa có dòng nào có `internal_sale_owner = Thành`. "
            "Kết quả đang để trống theo đúng dữ liệu chuẩn hóa."
        )
    elif missing:
        st.warning(
            f"SALE Thành đã khớp {matched}/{related} dòng chuẩn hóa; còn {missing} dòng "
            "thiếu owner nên chưa được tự động đưa vào."
        )
    else:
        st.caption(f"Bộ lọc canonical: `internal_sale_owner = Thành` · {matched} dòng khớp.")


def _show_position(position: Mapping[str, Any]) -> None:
    totals = position.get("totals_by_currency") or {}
    buckets = position.get("buckets") or {}
    inbox = build_review_inbox(position)
    currencies = sorted(
        set(str(value).upper() for value in totals)
        | {
            str(row.get("currency") or "UNKNOWN").upper()
            for rows in buckets.values()
            for row in rows or []
            if isinstance(row, Mapping)
        }
    )

    if not totals and not inbox:
        st.info("Chưa có canonical ledger record phù hợp với A Bò / SALE Thành.")
        return

    explanations = build_all_currency_explanations(position)
    for currency in currencies:
        values = totals.get(currency) or {}
        review_rows = [row for row in inbox if str(row.get("currency") or "").upper() == currency]
        st.markdown(f"### {currency}")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("TT phải trả A Bò", _money(values.get("payable_to_partner", 0), currency))
        m2.metric("A Bò đang giữ / credit", _money(values.get("held_credit", 0), currency))
        m3.metric("A Bò đã nhận hộ", _money(values.get("received_on_behalf", 0), currency))
        m4.metric("A Bò đã chi hộ", _money(values.get("paid_on_behalf", 0), currency))
        m5.metric("Cần Thành xử lý", f"{len(review_rows)} dòng")
        st.caption(
            f"Vị trí confirmed của nhóm {currency}: "
            f"{_money(values.get('net_after_valid_allocations', 0), currency)} "
            "= TT phải trả − A Bò đang giữ / credit."
        )

        with st.expander(f"Vì sao ra số này? · {currency}", expanded=False):
            explanation = explanations.get(currency) or {}
            st.write(explanation.get("formula") or f"0 {currency}")
            included = explanation.get("lines") or []
            if included:
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Dấu": item.get("sign"),
                                "Bucket": item.get("label") or BUCKET_LABELS.get(item.get("bucket"), item.get("bucket")),
                                "Số tiền": _money(item.get("amount"), currency),
                                "Nguồn record / allocation": ", ".join(
                                    str(value) for value in item.get("source_record_ids") or []
                                ),
                            }
                            for item in included
                        ]
                    ),
                    hide_index=True,
                    use_container_width=True,
                )
            excluded = explanation.get("excluded_lines") or []
            if excluded:
                st.markdown("**Hiển thị để xử lý, nhưng chưa cộng vào confirmed**")
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Bucket": item.get("label") or BUCKET_LABELS.get(item.get("bucket"), item.get("bucket")),
                                "Số tiền": _money(item.get("amount"), currency),
                                "Lý do": item.get("review_reason") or "Cần đối soát",
                                "Nguồn": ", ".join(str(value) for value in item.get("source_record_ids") or []),
                            }
                            for item in excluded
                        ]
                    ),
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.caption("Không có dòng UNKNOWN / bị giới hạn trong nhóm này.")

        with st.expander(f"Các dòng tiền và nghĩa vụ · {currency}", expanded=False):
            for bucket in (
                "payable_to_partner",
                "held_credit",
                "received_on_behalf",
                "paid_on_behalf",
                "unallocated",
            ):
                rows = [row for row in buckets.get(bucket) or [] if str(row.get("currency") or "").upper() == currency]
                st.markdown(f"**{BUCKET_LABELS[bucket]}** · {len(rows)} dòng")
                _show_table(rows)

        if review_rows:
            with st.expander(f"CẦN THÀNH XỬ LÝ · {currency} · {len(review_rows)} dòng", expanded=True):
                review_table = []
                for row in review_rows:
                    category = row.get("review_category") or "unknown"
                    review_table.append(
                        {
                            **(_row_table([row])[0]),
                            "Nhóm xử lý": REVIEW_CATEGORY_LABELS.get(category, category),
                            "Confirmed": "Không",
                        }
                    )
                st.dataframe(pd.DataFrame(review_table), hide_index=True, use_container_width=True)


def _show_search_and_trace(position: Mapping[str, Any]) -> None:
    st.markdown("### Tra cứu nhanh trong phạm vi A Bò / SALE Thành")
    term = st.text_input(
        "Mã shipment, số tiền, source/reference hoặc transaction ID",
        placeholder="Ví dụ: 62464 hoặc TX-RECEIVED-62464",
        key="log_c04_partner_search",
    ).strip()
    if not term:
        st.caption("Chỉ tìm trong projection của A Bò / SALE Thành; không phải global search.")
        return
    results = search_partner_position(position, term)
    if not results:
        st.info(f"Không thấy dòng nào chứa “{term}” trong projection hiện tại.")
        return
    st.caption(f"Tìm thấy {len(results)} dòng. Chọn một dòng để xem tiền đang ở đâu.")
    st.dataframe(pd.DataFrame(_row_table(results)), hide_index=True, use_container_width=True)
    by_id = {_row_id(row): row for row in results if _row_id(row)}
    if not by_id:
        return
    selected_id = st.selectbox("Dòng cần lần theo", list(by_id), key="log_c04_trace_record")
    trace = build_money_location_trace(by_id[selected_id])
    st.markdown("**Nguồn → người đang giữ → chủ sở hữu hưởng lợi → phân bổ → phần còn lại**")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Từ": step.get("from"),
                    "Đến": step.get("to"),
                    "Diễn giải": step.get("label"),
                    "Allocation": step.get("allocation_id") or "",
                }
                for step in trace.get("steps") or []
            ]
        ),
        hide_index=True,
        use_container_width=True,
    )
    with st.expander("Nguồn và chứng từ của dòng này", expanded=False):
        st.json(
            {
                "record_id": trace.get("record_id"),
                "source_record_ids": trace.get("source_record_ids"),
                "evidence_refs": trace.get("evidence_refs"),
                "source_refs": trace.get("source_refs"),
                "provenance": trace.get("provenance"),
                "remaining": trace.get("remaining"),
            }
        )


def _show_period_draft(position: Mapping[str, Any]) -> None:
    st.markdown("### Bản nháp đối soát theo kỳ")
    st.caption(
        "Đây là bản nháp quản lý để tìm chênh lệch. Không đóng kỳ, không khóa sổ, "
        "không ghi đè canonical ledger."
    )
    today = date.today()
    default_start = today.replace(day=1)
    c1, c2 = st.columns(2)
    start = c1.date_input("Từ ngày", value=default_start, key="log_c04_period_start")
    end = c2.date_input("Đến ngày", value=today, key="log_c04_period_end")
    if start > end:
        st.warning("Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.")
        return
    try:
        draft = build_period_reconciliation(position, start, end)
    except (TypeError, ValueError) as exc:
        st.warning(f"Chưa lập được bản nháp kỳ này: {exc}")
        return
    st.caption(f"{draft['start']} → {draft['end']} · draft={draft['draft']} · close_or_lock={draft['close_or_lock']}")
    rows = []
    for currency, values in sorted((draft.get("by_currency") or {}).items()):
        rows.append(
            {
                "Tiền tệ": currency,
                "Vị trí đầu kỳ": _money(values.get("opening_prior_position"), currency),
                "Nghĩa vụ mới": _money(values.get("new_obligations"), currency),
                "Khoản chi hộ": _money(values.get("payments"), currency),
                "Nhận hộ": _money(values.get("received_on_behalf"), currency),
                "Phân bổ / cấn": _money(values.get("allocations_netting"), currency),
                "Confirmed canonical": _money(values.get("current_confirmed_position"), currency),
                "Chênh lệch cần xem": _money(values.get("draft_difference"), currency),
                "Trạng thái": "Cần đối soát" if values.get("review_required") else "Đã cân",
            }
        )
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        for currency, values in sorted((draft.get("by_currency") or {}).items()):
            with st.expander(f"Công thức bản nháp · {currency}", expanded=False):
                st.write(values.get("formula"))
    else:
        st.info("Chưa có dòng canonical trong khoảng thời gian này.")


def _show_reported_difference(position: Mapping[str, Any]) -> None:
    st.markdown("### Nếu A Bò báo một số khác")
    st.caption("Nhập số để so sánh tạm thời; hệ thống chỉ nêu chênh lệch và nhóm cần tìm, không tự sửa số.")
    currencies = sorted(
        set((position.get("totals_by_currency") or {}).keys())
        | {
            str(row.get("currency") or "UNKNOWN").upper()
            for rows in (position.get("buckets") or {}).values()
            for row in rows or []
            if isinstance(row, Mapping)
        }
    )
    reported: dict[str, float] = {}
    for currency in currencies:
        raw = st.text_input(
            f"A Bò báo lại ({currency})",
            value="",
            placeholder="Để trống nếu chưa có số đối tác báo",
            key=f"log_c04_reported_{currency}",
        ).strip()
        if not raw:
            continue
        try:
            reported[currency] = float(to_decimal(raw.replace(",", "")))
        except (TypeError, ValueError, ArithmeticError):
            st.warning(f"Số A Bò báo lại cho {currency} chưa đọc được.")
    if not reported:
        return
    comparison = compare_reported_position(position, reported)
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Tiền tệ": item["currency"],
                    "Canonical confirmed": _money(item["system_confirmed"], item["currency"]),
                    "A Bò báo": _money(item["partner_reported"], item["currency"]),
                    "Chênh lệch": _money(item["difference"], item["currency"]),
                    "Nhóm cần tìm": ", ".join(
                        REVIEW_CATEGORY_LABELS.get(value, value)
                        for value in item.get("candidate_unmatched_categories") or []
                    )
                    or "Không có chênh lệch",
                }
                for item in comparison.get("comparisons") or []
            ]
        ),
        hide_index=True,
        use_container_width=True,
    )


def ui_partner_reconciliation_desk() -> None:
    """Render the A Bò / SALE Thành management projection."""

    st.title("Công nợ A Bò")
    st.caption(
        "SALE Thành · bàn đối soát chỉ đọc · dữ liệu lấy từ canonical ledger · "
        "không có sổ Thành riêng"
    )
    st.info(
        "Nguyên tắc đọc số: TT phải trả A Bò và tiền A Bò đang giữ/credit là hai bucket khác nhau. "
        "Tiền nhận hộ, chi hộ, chưa phân bổ, chưa xác minh và bị giới hạn không bị gộp lẫn."
    )

    mode = _mode_navigation()
    if mode == "historical_review":
        ui_historical_review()
        return

    with st.spinner("Đang đọc vị trí canonical của A Bò..."):
        position = build_partner_financial_position(PARTNER, internal_sale_owner=SALE_OWNER)
    if position.get("error"):
        st.warning("Chưa đọc được canonical ledger; màn hình không tự tạo số thay thế.")
        st.caption(str(position["error"]))
        if mode == "report":
            _render_manager_report(position)
        elif mode == "debit":
            _render_debit_draft(position)
        return

    if mode == "report":
        _render_manager_report(position)
        return
    if mode == "debit":
        _render_debit_draft(position)
        return

    _show_owner_coverage(position)
    _show_position(position)
    if position.get("read_only"):
        st.caption("Projection này là read-only; không có thao tác ghi nhận, phân bổ hay chốt kỳ trên màn hình.")
    _show_search_and_trace(position)
    _show_period_draft(position)
    _show_reported_difference(position)


__all__ = ["ui_partner_reconciliation_desk"]
