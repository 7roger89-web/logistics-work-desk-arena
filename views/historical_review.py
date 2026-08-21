"""Bounded LOG-C06 Historical Review desk.

This view is a staging/review surface only.  It may read the historical workbook
and write staging metadata or review audit records, but it never calls a canonical
financial writer and never publishes an opening balance.
"""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Mapping
from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from core.database import get_db
from core.historical_opening import BUCKET_LABELS, build_cutover_draft
from core.historical_review_analysis import build_review_analysis
from core.historical_staging import (
    SALE_OWNER,
    UNKNOWN_CURRENCY,
    search_staging_items,
    source_evidence,
    stage_workbook,
    summarize_staging,
)
from core.historical_staging_store import (
    REVIEW_ACTIONS_COLLECTION,
    STAGING_COLLECTION,
    ReviewActionConflict,
    ReviewValidationError,
    StagingStoreError,
    apply_review_action,
    ensure_staging_indexes,
    load_staging_items,
    persist_staging_batch,
)


_SESSION_BATCH_KEY = "log_c06_historical_batch"
_SESSION_STAGING_KEY = "log_c06_session_staging_documents"
_SESSION_ACTIONS_KEY = "log_c06_session_review_actions"
_SESSION_DB_ERROR_KEY = "log_c06_staging_db_error"
_MAX_RESULT_CARDS = 8
_MAX_TABLE_ROWS = 100


class _SessionCollection:
    """Small database-like adapter backed only by Streamlit session state."""

    def __init__(self, state: Any, key: str):
        self._state = state
        self._key = key
        if not isinstance(state.get(key), list):
            state[key] = []

    @property
    def documents(self) -> list[dict[str, Any]]:
        return self._state[self._key]

    @staticmethod
    def _matches(document: Mapping[str, Any], query: Mapping[str, Any]) -> bool:
        return all(document.get(key) == value for key, value in query.items())

    def create_index(self, *args: Any, **kwargs: Any) -> None:
        return None

    def find_one(self, query: Mapping[str, Any]) -> dict[str, Any] | None:
        for document in self.documents:
            if self._matches(document, query):
                return copy.deepcopy(document)
        return None

    def find(self, query: Mapping[str, Any]) -> list[dict[str, Any]]:
        return [copy.deepcopy(document) for document in self.documents if self._matches(document, query)]

    def insert_one(self, document: Mapping[str, Any]) -> None:
        self.documents.append(copy.deepcopy(dict(document)))

    def replace_one(
        self,
        query: Mapping[str, Any],
        document: Mapping[str, Any],
        *,
        upsert: bool,
    ) -> Any:
        for index, current in enumerate(self.documents):
            if self._matches(current, query):
                self.documents[index] = copy.deepcopy(dict(document))
                return type("Result", (), {"matched_count": 1})()
        if upsert:
            self.insert_one(document)
        return type("Result", (), {"matched_count": 0})()


class _SessionDatabase:
    def __init__(self, state: Any):
        self._collections = {
            STAGING_COLLECTION: _SessionCollection(state, _SESSION_STAGING_KEY),
            REVIEW_ACTIONS_COLLECTION: _SessionCollection(state, _SESSION_ACTIONS_KEY),
        }

    def __getitem__(self, name: str) -> _SessionCollection:
        if name not in self._collections:
            raise KeyError(name)
        return self._collections[name]


def _session_state() -> Any:
    state = getattr(st, "session_state", None)
    if state is not None and hasattr(state, "get") and hasattr(state, "__setitem__"):
        return state
    return {}


def _state_get(key: str, default: Any = None) -> Any:
    try:
        return _session_state().get(key, default)
    except Exception:
        return default


def _state_set(key: str, value: Any) -> None:
    try:
        _session_state()[key] = value
    except Exception:
        return None


def _rerun() -> None:
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()


def _actor() -> str:
    user = _state_get("current_user", {})
    if isinstance(user, Mapping):
        return str(user.get("username") or user.get("display_name") or "local-owner")
    return "local-owner"


def _money(value: Any, currency: str = "") -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return "—"
    decimals = 0 if currency == "VND" else 2
    return f"{number:,.{decimals}f} {currency}".strip()


def _source_batch() -> dict[str, Any]:
    cached = _state_get(_SESSION_BATCH_KEY)
    if isinstance(cached, Mapping) and isinstance(cached.get("items"), list):
        return copy.deepcopy(dict(cached))
    batch = stage_workbook()
    _state_set(_SESSION_BATCH_KEY, batch)
    return copy.deepcopy(batch)


def _load_items() -> tuple[list[dict[str, Any]], Any, str, str | None]:
    """Return items, staging store, source mode, and a safe DB error message."""

    state = _session_state()
    try:
        batch = _source_batch()
    except FileNotFoundError:
        raise
    source_hash = str(batch.get("source_file_hash") or "") or None
    db_error: str | None = None
    try:
        db = get_db()
        if db is not None:
            ensure_staging_indexes(db)
            items = load_staging_items(db, source_file_hash=source_hash)
            if not items:
                persist_staging_batch(db, batch)
                items = load_staging_items(db, source_file_hash=source_hash)
            return items, db, "staging DB", None
        db_error = "Staging DB chưa khả dụng; đang hiển thị session-only."
    except Exception:
        db_error = "Staging DB không khả dụng; đang hiển thị session-only và không ghi canonical."
        _state_set(_SESSION_DB_ERROR_KEY, db_error)

    session_db = _SessionDatabase(state)
    ensure_staging_indexes(session_db)
    items = load_staging_items(session_db, source_file_hash=source_hash)
    if not items:
        persist_staging_batch(session_db, batch)
        items = load_staging_items(session_db, source_file_hash=source_hash)
    return items, session_db, "session-only", db_error


def _summary_table(items: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        proposal = item.get("proposal") if isinstance(item.get("proposal"), Mapping) else {}
        rows.append(
            {
                "Nguồn": item.get("source_reference") or "",
                "Sheet": item.get("sheet") or "",
                "Dòng": item.get("source_row") or "",
                "Amount": _money(proposal.get("amount", item.get("raw_amount")), proposal.get("currency", "")),
                "SALE raw": item.get("raw_sale") or "—",
                "Event": proposal.get("event_type") or "unknown",
                "Currency": proposal.get("currency") or UNKNOWN_CURRENCY,
                "Trạng thái": item.get("review_status") or "RAW",
                "Anomaly": ", ".join(item.get("anomaly_flags") or []) or "—",
            }
        )
    return rows


def _render_summary(items: list[dict[str, Any]], source_mode: str, source_hash: str | None) -> dict[str, Any]:
    summary = summarize_staging(items)
    st.subheader("Tổng quan staging")
    columns = st.columns(5)
    metrics = [
        ("Đã xác nhận", summary.get("confirmed", 0)),
        ("Đề xuất tin cậy", summary.get("high_confidence", 0)),
        ("Cần review", summary.get("needs_review", 0)),
        ("SALE khác", summary.get("other_sale", 0)),
        ("Có anomaly", summary.get("anomalies", 0)),
    ]
    for column, (label, value) in zip(columns, metrics):
        column.metric(label, value)
    st.caption(
        f"Nguồn: {source_mode} · {summary.get('total_items', 0)} dòng staging · "
        f"SHA-256: {source_hash or 'chưa có'}"
    )
    if source_mode == "session-only":
        st.warning("Session-only: review action chỉ tồn tại trong phiên hiện tại; chưa có staging DB durable.")
    st.info(
        "Raw workbook là bằng chứng bất biến. Chỉ dòng CONFIRMED, đúng currency và không phải checkpoint "
        "mới được xét vào draft opening; không có tổng gộp CNY/USD/VND."
    )
    return summary


def _filtered_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    query = st.text_input(
        "Tìm dòng lịch sử",
        placeholder="Ví dụ: 62464, 1687, 1572 hoặc 25025",
        key="log_c06_search",
    ).strip()
    status_options = ["Tất cả", "PROPOSED", "CONFIRMED", "REVIEW_REQUIRED", "NOT_APPLICABLE", "REJECTED"]
    status = st.selectbox("Lọc trạng thái", status_options, key="log_c06_status_filter")
    results = search_staging_items(items, query)
    if status != "Tất cả":
        results = [item for item in results if item.get("review_status") == status]
    return results


def _request_id(item: Mapping[str, Any], action: str, reason: str, correction: Mapping[str, Any] | None) -> str:
    payload = {
        "source_item_id": item.get("source_item_id"),
        "action": action,
        "review_version": item.get("review_version", 0),
        "reason": reason,
        "correction": correction or {},
    }
    return "c06-" + hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:24]


def _apply_action(
    store: Any,
    item: Mapping[str, Any],
    action: str,
    *,
    reason: str,
    correction: Mapping[str, Any] | None = None,
) -> None:
    if not reason.strip():
        st.warning("Nhập lý do review trước khi ghi metadata staging.")
        return
    try:
        result = apply_review_action(
            store,
            str(item.get("source_item_id")),
            action,
            actor=_actor(),
            reason=reason,
            request_id=_request_id(item, action, reason, correction),
            correction=correction,
            expected_review_version=int(item.get("review_version") or 0),
        )
        if result.get("status") == "IDEMPOTENT":
            st.info("Review action này đã được áp dụng trước đó; không tạo bản ghi lặp.")
        else:
            st.success(f"Đã cập nhật staging: {result.get('after_status') or 'đã ghi'}.")
        _rerun()
    except (ReviewActionConflict, ReviewValidationError, StagingStoreError) as error:
        st.error(f"Không ghi được review action: {error}")


def _render_review_controls(store: Any, item: Mapping[str, Any]) -> None:
    status = str(item.get("review_status") or "RAW")
    if item.get("raw_amount") is None or status in {"NOT_APPLICABLE", "REJECTED"}:
        return
    proposal = item.get("proposal") if isinstance(item.get("proposal"), Mapping) else {}
    st.markdown("**Review action — chỉ ghi staging metadata/audit**")
    reason = st.text_input(
        "Lý do / căn cứ owner",
        key=f"log_c06_reason_{item.get('source_item_id')}",
    ).strip()
    owner_options = ["Giữ đề xuất", SALE_OWNER, "Không phải Thành"]
    owner_choice = st.selectbox(
        "SALE sau review",
        owner_options,
        key=f"log_c06_owner_{item.get('source_item_id')}",
    )
    bucket_options = ["Giữ đề xuất"] + list(BUCKET_LABELS)
    bucket_choice = st.selectbox(
        "Bucket sau review",
        bucket_options,
        key=f"log_c06_bucket_{item.get('source_item_id')}",
    )
    columns = st.columns(4)
    with columns[0]:
        if st.button("Xác nhận", key=f"log_c06_confirm_{item.get('source_item_id')}"):
            _apply_action(store, item, "confirm", reason=reason)
    with columns[1]:
        if st.button("Sửa & xác nhận", key=f"log_c06_correct_{item.get('source_item_id')}"):
            correction: dict[str, Any] = {}
            if owner_choice == SALE_OWNER:
                correction["internal_sale_owner"] = SALE_OWNER
            elif owner_choice == "Không phải Thành":
                correction["internal_sale_owner"] = None
            if bucket_choice != "Giữ đề xuất":
                correction["candidate_bucket"] = bucket_choice
            _apply_action(store, item, "correct", reason=reason, correction=correction)
    with columns[2]:
        if st.button("Không phải SALE Thành", key=f"log_c06_not_thanh_{item.get('source_item_id')}"):
            _apply_action(store, item, "not_thanh", reason=reason)
    with columns[3]:
        if st.button("Đánh dấu chưa rõ", key=f"log_c06_unknown_{item.get('source_item_id')}"):
            _apply_action(store, item, "unknown", reason=reason)


def _render_evidence_and_card(store: Any, item: Mapping[str, Any], *, expanded: bool) -> None:
    proposal = item.get("proposal") if isinstance(item.get("proposal"), Mapping) else {}
    reference = item.get("source_reference") or f"{item.get('sheet')}!row {item.get('source_row')}"
    currency = str(proposal.get("currency") or UNKNOWN_CURRENCY)
    amount = proposal.get("amount", item.get("raw_amount"))
    with st.expander(
        f"{reference} · {_money(amount, currency)} · {item.get('review_status') or 'RAW'}",
        expanded=expanded,
    ):
        st.caption(
            f"Sheet {item.get('sheet')} · dòng {item.get('source_row')} · cells {item.get('source_cell_range')} · "
            f"source_id {item.get('source_item_id')}"
        )
        st.write(f"SALE raw: {item.get('raw_sale') or 'trống'} · Event: {proposal.get('event_type') or 'unknown'}")
        st.write(f"Review reason: {item.get('review_reason') or '—'}")
        st.markdown("**Raw evidence (không bị sửa)**")
        st.json(source_evidence(item))
        st.markdown("**Proposal tách riêng**")
        st.json(proposal)
        if item.get("anomaly_flags"):
            st.warning("Anomaly: " + ", ".join(item["anomaly_flags"]))
        _render_review_controls(store, item)


def _review_amounts_label(amounts_by_currency: Mapping[str, Any]) -> str:
    parts = [
        _money(amount, currency)
        for currency, amount in sorted(amounts_by_currency.items())
    ]
    return " · ".join(parts) or "Chưa có số tiền đã chuẩn hóa"


def _render_owner_review_analysis(analysis: Mapping[str, Any]) -> None:
    """Render business-facing derived evidence without changing staging state."""

    st.subheader("Business review map")
    st.info(
        "Đây là bản phân tích staging để Owner quyết định. "
        "READY_FOR_OWNER_CONFIRMATION không phải CONFIRMED, không ghi sổ cái và không làm thay đổi draft live."
    )
    owner_states = analysis.get("owner_review_state_counts") or {}
    metric_columns = st.columns(4)
    for column, (label, value) in zip(
        metric_columns,
        (
            ("Sẵn sàng Owner xác nhận", owner_states.get("READY_FOR_OWNER_CONFIRMATION", 0)),
            ("Cần review", owner_states.get("REVIEW_REQUIRED", 0)),
            ("UNKNOWN", owner_states.get("UNKNOWN", 0)),
            ("Nhóm business", analysis.get("cluster_count", 0)),
        ),
    ):
        column.metric(label, value)
    st.caption(
        f"{analysis.get('review_required_count', 0)} dòng REVIEW_REQUIRED đã được gom đúng một nhóm; "
        f"phân tích phiên bản {analysis.get('analysis_version', 'unknown')}."
    )

    golden_items = analysis.get("golden_items") or []
    with st.expander("6 golden items — ý nghĩa tiền và quyết định Owner", expanded=True):
        if not golden_items:
            st.info("Chưa có đủ source rows để dựng golden items trong phiên hiện tại.")
        for item in golden_items:
            business = item.get("business") if isinstance(item.get("business"), Mapping) else {}
            amount = _money(item.get("amount"), str(item.get("currency") or ""))
            st.markdown(f"### {business.get('title') or item.get('source_reference')} · {amount}")
            st.caption(
                f"Source: {item.get('source_reference')} · row {item.get('source_row')} · "
                f"trạng thái hiện tại: {item.get('current_review_status')} · "
                f"đề xuất review: {item.get('owner_review_state')}"
            )
            st.write(f"Tiền từ: {business.get('money_from') or 'Chưa xác định'}")
            st.write(f"Đang ở đâu: {business.get('money_location') or 'Chưa xác định'}")
            st.write(f"Ý nghĩa business: {business.get('business_meaning') or 'Chưa xác định'}")
            st.write(f"Shipment / khách hàng: {business.get('shipment_or_customer') or 'Chưa xác định'}")
            st.write(f"Mức chắc chắn: {business.get('certainty') or 'Chưa xác định'}")
            st.write(f"Khuyến nghị: {business.get('recommendation') or 'Giữ review'}")
            st.info(f"Owner cần quyết định: {business.get('owner_question') or 'Cần bổ sung source evidence.'}")
            st.markdown("---")

    clusters = analysis.get("clusters") or []
    with st.expander("185 mục review — nhóm theo quyết định business", expanded=True):
        cluster_rows = [
            {
                "Nhóm": cluster.get("label") or cluster.get("cluster_key"),
                "Số dòng": cluster.get("count", 0),
                "Số tiền theo currency": _review_amounts_label(cluster.get("amounts_by_currency") or {}),
                "Sẵn sàng Owner": cluster.get("ready_count", 0),
                "UNKNOWN": cluster.get("unknown_count", 0),
                "Một quyết định cho nhóm": "Có" if cluster.get("one_owner_rule") else "Không",
                "Câu hỏi chính": cluster.get("owner_question") or "Cần review từng dòng",
            }
            for cluster in clusters
        ]
        if cluster_rows:
            st.dataframe(pd.DataFrame(cluster_rows), hide_index=True, use_container_width=True)
            for cluster in clusters:
                st.markdown(
                    f"**{cluster.get('label') or cluster.get('cluster_key')}** — "
                    f"{cluster.get('rule_resolution') or 'Giữ review theo source evidence.'}"
                )
        else:
            st.info("Chưa có nhóm REVIEW_REQUIRED trong phiên hiện tại.")

    decision_pack = analysis.get("owner_decision_pack")
    decisions = decision_pack.get("decisions") if isinstance(decision_pack, Mapping) else []
    with st.expander("Owner Decision Pack — chỉ các quyết định cần Owner", expanded=True):
        if not decisions:
            st.info("Chưa có golden decision nào để Owner xác nhận.")
        for decision in decisions:
            evidence = decision.get("evidence") if isinstance(decision.get("evidence"), Mapping) else {}
            st.markdown(f"#### {decision.get('decision_id')} · {decision.get('title')}")
            st.caption(
                f"Evidence: {evidence.get('source_reference')} · "
                f"{_money(evidence.get('amount'), str(evidence.get('currency') or ''))} · "
                f"staging status: {evidence.get('current_review_status')}"
            )
            st.write(f"Khuyến nghị: {decision.get('recommended') or 'Giữ review'}")
            st.write(f"Nếu Owner xác nhận: {decision.get('financial_effect_if_confirmed') or 'Chưa có effect.'}")
            st.warning(f"Cần trả lời: {decision.get('owner_question') or 'Cần bổ sung evidence.'}")
        if isinstance(decision_pack, Mapping):
            st.caption(f"Cutover lock: {decision_pack.get('cutover_lock') or 'DRAFT / NOT_APPROVED / NOT_LIVE'}")

    checkpoint = analysis.get("checkpoint_reconstruction")
    if isinstance(checkpoint, Mapping):
        with st.expander("Checkpoint 134,973 CNY — arithmetic và chống double count", expanded=True):
            st.markdown("### 134,973 CNY — component candidate")
            st.write(checkpoint.get("reason") or "Chưa có kết luận số học.")
            component_rows = [
                {
                    "Row": component.get("source_row"),
                    "Source": component.get("source_reference"),
                    "Amount": _money(component.get("amount"), str(component.get("currency") or "")),
                }
                for component in checkpoint.get("candidate_components") or []
            ]
            if component_rows:
                st.dataframe(pd.DataFrame(component_rows), hide_index=True, use_container_width=True)
            st.caption(
                f"Tổng component: {_money(checkpoint.get('candidate_component_amount'), 'CNY')} · "
                f"Chênh lệch: {_money(checkpoint.get('difference'), 'CNY')} · "
                f"Nghiệm exact: {checkpoint.get('exact_solution_count', 0)}"
            )
            excluded_rows = [row.get("source_row") for row in checkpoint.get("context_exclusion_rows") or []]
            st.warning(
                "Row 129 là summary nên không vào component/opening. "
                f"Các money leg tách riêng bị loại khỏi candidate set: {', '.join(str(row) for row in excluded_rows) or 'không có'}."
            )


def _render_owner_reconciliation(reconciliation: Mapping[str, Any] | None) -> None:
    """Show the Owner-confirmed lineage and source-level checkpoint reconciliation."""

    if not isinstance(reconciliation, Mapping):
        return
    st.subheader("Owner-confirmed reconciliation")
    paid = reconciliation.get("paid_on_behalf_group")
    received = reconciliation.get("received_on_behalf_group")
    checkpoint = reconciliation.get("checkpoint_134973")
    columns = st.columns(4)
    metrics = (
        ("Paid/chuyển hộ", (paid or {}).get("component_amount", 0), "CNY"),
        ("Checkpoint 134,973", (checkpoint or {}).get("component_amount", 0), "CNY"),
        ("Received source group", (received or {}).get("component_amount", 0), "CNY"),
        ("Expected received", (received or {}).get("expected_amount", 0), "CNY"),
    )
    for column, (label, amount, currency) in zip(columns, metrics):
        column.metric(label, _money(amount, currency))
    if isinstance(paid, Mapping):
        st.caption(
            f"159,998 CNY = 134,973 checkpoint components + 25,025 B&G Green; "
            f"trạng thái {paid.get('status')} và derived total không phải event mới."
        )
    if isinstance(received, Mapping):
        difference = float(received.get("difference") or 0)
        message = (
            f"Nhóm received C102/C109/C115/C190/C197/C198: "
            f"{_money(received.get('component_amount'), 'CNY')} so với kỳ vọng "
            f"{_money(received.get('expected_amount'), 'CNY')}; chênh lệch "
            f"{_money(difference, 'CNY')}."
        )
        if difference:
            st.warning(message)
        else:
            st.success(message)
        source_reconciliation = received.get("source_reconciliation")
        if isinstance(source_reconciliation, Mapping):
            st.caption(
                f"Six-source status: {source_reconciliation.get('status')} · "
                f"row delta sum: {_money(source_reconciliation.get('delta_sum'), 'CNY')} · "
                "C190/C197/C198 are oracle labels mapped to physical rows C192/C199/C200."
            )
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Oracle": row.get("source_oracle"),
                            "Source cell": row.get("source_cell"),
                            "Verified": _money(row.get("verified_amount"), "CNY"),
                            "Staging row": row.get("staging_source_row"),
                            "Staged raw": _money(row.get("staged_raw_amount"), "CNY"),
                            "Normalized": _money(row.get("normalized_amount"), "CNY"),
                            "Confirmed": _money(row.get("confirmed_amount"), "CNY"),
                            "Included": _money(row.get("included_amount"), "CNY"),
                            "Delta": _money(row.get("delta"), "CNY"),
                            "Classification": row.get("classification"),
                            "Exclusion": row.get("exclusion_reason"),
                        }
                        for row in source_reconciliation.get("rows") or []
                    ]
                ),
                hide_index=True,
                use_container_width=True,
            )
    snapshot = reconciliation.get("snapshot_credit_lineage")
    if isinstance(snapshot, Mapping):
        st.info(
            "24,576 CNY được giữ làm source component nhưng đã embedded trong checkpoint "
            "99,824.43; hệ thống không trừ lại lần thứ hai."
        )
    with st.expander("Lineage và double-count protection", expanded=False):
        st.json(
            {
                "snapshot_credit_lineage": snapshot,
                "checkpoint_134973": checkpoint,
                "paid_on_behalf_group": paid,
                "received_on_behalf_group": received,
                "historical_position_checkpoint": reconciliation.get("historical_position_checkpoint"),
                "opening_lineage": reconciliation.get("opening_lineage"),
            }
        )


def _render_review_inbox(items: list[dict[str, Any]], store: Any) -> None:
    st.subheader("Review inbox")
    results = _filtered_items(items)
    st.caption(f"Tìm thấy {len(results)} dòng")
    if results:
        st.dataframe(
            pd.DataFrame(_summary_table(results[:_MAX_TABLE_ROWS])),
            hide_index=True,
            use_container_width=True,
        )
        query = _state_get("log_c06_search", "")
        for item in results[:_MAX_RESULT_CARDS]:
            _render_evidence_and_card(store, item, expanded=bool(query))
    else:
        st.info("Không có dòng phù hợp bộ lọc hiện tại.")


def _render_opening_draft(items: list[dict[str, Any]]) -> None:
    st.subheader("Draft opening position")
    st.caption("Đây là draft tính từ CONFIRMED staging; chưa phải số dư live và chưa ghi canonical ledger.")
    default_date = date.today()
    selected_date = st.date_input("Ngày cutover dự kiến", value=default_date, key="log_c06_cutover_date")
    if isinstance(selected_date, date):
        cutover_date = selected_date.isoformat()
    else:
        cutover_date = default_date.isoformat()
    draft = build_cutover_draft(
        items,
        proposed_cutover_date=cutover_date,
        generated_by=_actor(),
    )
    if draft["cutover_readiness"] == "READY":
        st.success("READY — draft đủ cấu trúc để owner review; chưa được approve/live.")
    else:
        st.warning("NOT_READY — còn dữ liệu cần review hoặc checkpoint chưa reconcile.")
        st.write("Lý do: " + ", ".join(draft.get("readiness_reasons") or []))
    st.caption(
        f"Draft {draft.get('draft_id')} · status {draft.get('status')} · snapshot {draft.get('snapshot_hash')} · "
        "owner confirmation required"
    )
    st.info("Không có tổng gộp CNY/USD/VND. Mỗi currency và business bucket được hiển thị riêng.")
    draft_reconciliation = draft.get("owner_reconciliation")
    if isinstance(draft_reconciliation, Mapping):
        received = draft_reconciliation.get("received_on_behalf_group")
        historical = draft_reconciliation.get("historical_position_checkpoint")
        if isinstance(received, Mapping) and isinstance(historical, Mapping):
            st.caption(
                "Checkpoint expectation: 418,060.79 + 159,998 - 416,482.2426005565 "
                "= 161,576.5473994435 CNY; draft uses only confirmed source buckets "
                "and keeps the checkpoint as DRAFT / NOT_APPROVED / NOT_LIVE."
            )
            if received.get("difference"):
                st.warning(
                    f"Received group difference: {_money(received.get('difference'), 'CNY')} "
                    "(not auto-filled)."
                )
    for currency in draft.get("position_by_currency", {}):
        data = draft["position_by_currency"][currency]
        st.markdown(f"### {currency}")
        metric_columns = st.columns(4)
        metric_values = [
            ("Payable A Bò", data["buckets"]["payable_to_a_bo"]["amount"]),
            ("Held / credit", data["buckets"]["held_credit"]["amount"]),
            ("Nhận hộ available", data["buckets"]["received_on_behalf_available"]["amount"]),
            ("Chi hộ settled", data["buckets"]["paid_on_behalf_settled"]["amount"]),
        ]
        for column, (label, amount) in zip(metric_columns, metric_values):
            column.metric(label, _money(amount, currency))
        with st.expander(f"Vì sao opening position ra số này? · {currency}", expanded=False):
            component_rows: list[dict[str, Any]] = []
            for bucket, bucket_data in data["buckets"].items():
                for component in bucket_data.get("components") or []:
                    component_rows.append(
                        {
                            "Bucket": bucket_data.get("label") or bucket,
                            "Amount": _money(component.get("signed_amount"), currency),
                            "Source": component.get("source_reference"),
                            "Sheet": component.get("sheet"),
                            "Row": component.get("source_row"),
                            "Source ID": component.get("source_item_id"),
                        }
                    )
            st.dataframe(pd.DataFrame(component_rows), hide_index=True, use_container_width=True)
            st.caption(
                f"Confirmed components: {data.get('confirmed_component_count', 0)} · "
                f"Excluded unresolved amount: {_money(data.get('excluded_unresolved_amount'), currency)}"
            )
    checkpoint_rows = draft.get("checkpoint_reconciliation") or []
    if checkpoint_rows:
        st.markdown("### Checkpoint reconciliation")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Checkpoint": row.get("checkpoint_source_item_id"),
                        "Expected": _money(row.get("expected_amount"), row.get("currency") or ""),
                        "Components": ", ".join(row.get("component_source_item_ids") or []) or "Chưa có link",
                        "Status": row.get("status"),
                        "Reason": row.get("reason"),
                    }
                    for row in checkpoint_rows
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
    with st.expander("Dòng bị loại khỏi opening draft", expanded=False):
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Source": row.get("source_reference"),
                        "Amount": _money(row.get("amount"), row.get("currency") or ""),
                        "Status": row.get("review_status"),
                        "Reason": row.get("reason"),
                    }
                    for row in (draft.get("exclusions") or [])[:_MAX_TABLE_ROWS]
                ]
            ),
            hide_index=True,
            use_container_width=True,
        )
    st.caption("Không có nút approve/live/cutover trong LOG-C06; owner phải xác nhận ở bước riêng.")


def ui_historical_review() -> None:
    """Render the staging-only Historical Review view."""

    st.title("Historical Review · SALE Thành")
    st.caption(
        "LOG-C06 · chuẩn hóa workbook lịch sử thành staging có provenance · "
        "không tạo số dư canonical và không suy SALE Thành từ text tự do."
    )
    try:
        items, store, source_mode, db_error = _load_items()
    except FileNotFoundError as error:
        st.error("Không tìm thấy workbook lịch sử; không tạo dữ liệu thay thế.")
        st.caption(str(error))
        return
    if db_error:
        st.warning(db_error)
    source_hash = items[0].get("source_file_hash") if items else None
    _render_summary(items, source_mode, source_hash)
    analysis = build_review_analysis(items)
    _render_owner_review_analysis(analysis)
    _render_owner_reconciliation(analysis.get("owner_reconciliation"))
    _render_review_inbox(items, store)
    _render_opening_draft(items)


__all__ = ["ui_historical_review"]
