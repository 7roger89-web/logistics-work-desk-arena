"""Read-only Customer / Factory / Partner context workspace."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import streamlit as st

from core.entity_context import build_entity_context, list_context_entities
from core.shipment_360 import UNKNOWN


_REQUEST_KEY = "entity_context_request"


def open_entity_context(
    entity_type: str,
    entity_key: str,
    *,
    return_shipment_id: str | None = None,
    return_page: str | None = None,
) -> None:
    """Set a read-only context navigation request and rerun the current app."""

    st.session_state[_REQUEST_KEY] = {
        "entity_type": str(entity_type),
        "entity_key": str(entity_key),
        "return_shipment_id": str(return_shipment_id or ""),
        "return_page": str(return_page or ""),
    }
    st.session_state.active_page = "Entity Context"
    st.rerun()


def _value(value: Any) -> str:
    if value in (None, ""):
        return UNKNOWN
    return str(value)


def _request() -> dict[str, str]:
    request = st.session_state.get(_REQUEST_KEY) or {}
    return {
        "entity_type": str(request.get("entity_type") or ""),
        "entity_key": str(request.get("entity_key") or ""),
        "return_shipment_id": str(request.get("return_shipment_id") or ""),
        "return_page": str(request.get("return_page") or ""),
    }


def _go_dashboard() -> None:
    request = _request()
    st.session_state.active_page = request.get("return_page") or "Dashboard"
    if st.session_state.active_page == "Review Queue":
        st.session_state.review_queue_return = False
    st.session_state.pop(_REQUEST_KEY, None)
    st.rerun()


def _open_shipment(shipment_id: str) -> None:
    requested_id = str(shipment_id or "")
    shipments = st.session_state.get("db_shipments") or {}
    resolved_id = requested_id
    if isinstance(shipments, dict) and requested_id not in shipments:
        resolved_id = next(
            (str(key) for key in shipments if str(key).strip() == requested_id.strip()),
            requested_id,
        )
    st.session_state.active_page = "Dashboard"
    st.session_state.active_shipment_id = resolved_id
    st.session_state.dashboard_active_shipment_id = resolved_id
    if _request().get("return_page") == "Review Queue":
        st.session_state.review_queue_return = True
    st.session_state.pop(_REQUEST_KEY, None)
    st.rerun()


def _render_master(view: Mapping[str, Any]) -> None:
    identity = view.get("identity") or {}
    master = view.get("master") or {}
    fields = master.get("fields") or {}
    st.markdown("### Master identity / contact")
    st.caption(
        f"Nguồn master: {_value(master.get('source'))} · trạng thái: {_value(master.get('status'))}. "
        "Các dòng shipment/lot bên dưới không ghi đè master."
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Entity", _value(identity.get("name")))
    c2.metric("ID", _value(identity.get("id")))
    c3.metric("Contact", _value(fields.get("contact")))
    c4.metric("Phone", _value(fields.get("phone")))
    with st.expander("Master details", expanded=False):
        st.dataframe(
            [{"Field": label, "Value": _value(value), "Source": _value(master.get("source"))} for label, value in fields.items()],
            hide_index=True,
            use_container_width=True,
        )


def _render_shipment_rows(rows: list[Mapping[str, Any]], key_prefix: str) -> None:
    if not rows:
        st.caption("UNKNOWN — chưa có shipment liên quan trong dữ liệu hiện tại.")
        return
    st.dataframe(
        [
            {
                "Shipment": _value(row.get("shipment_id")),
                "Status": _value(row.get("status")),
                "Required date": _value(row.get("required_date")),
                "Planned date": _value(row.get("planned_date")),
                "Attention": _value(row.get("attention")),
            }
            for row in rows
        ],
        hide_index=True,
        use_container_width=True,
    )
    for index, row in enumerate(rows):
        shipment_id = _value(row.get("shipment_id"))
        button_col, note_col = st.columns([1.1, 4.9])
        if button_col.button(
            f"Open Shipment 360 · {shipment_id}",
            key=f"{key_prefix}_open_{index}_{shipment_id}",
            use_container_width=True,
        ):
            _open_shipment(shipment_id)
        note_col.caption(
            f"{_value(row.get('attention_detail'))} · source: {_value(row.get('source'))}"
        )


def _render_customer(view: Mapping[str, Any]) -> None:
    requirements = view.get("requirements") or []
    st.markdown("### Requirements / delivery expectation")
    st.dataframe(
        [{"Requirement": _value(row.get("label")), "Value": _value(row.get("value"))} for row in requirements],
        hide_index=True,
        use_container_width=True,
    )
    gaps = view.get("gaps") or []
    with st.expander(f"Missing / unknown data ({len(gaps)})", expanded=bool(gaps)):
        for gap in gaps:
            st.markdown(f"- {_value(gap)}")
    with st.expander(f"Active shipments ({len(view.get('active_shipments') or [])})", expanded=True):
        _render_shipment_rows(list(view.get("active_shipments") or []), "customer_active")
    with st.expander(f"Shipments needing attention ({len(view.get('attention_shipments') or [])})", expanded=bool(view.get("attention_shipments"))):
        _render_shipment_rows(list(view.get("attention_shipments") or []), "customer_attention")
    with st.expander(f"Historical shipment context ({len(view.get('history_shipments') or [])})", expanded=False):
        _render_shipment_rows(list(view.get("history_shipments") or []), "customer_history")
    with st.expander(f"Báo giá đã chốt ({len(view.get('active_quotations') or [])})", expanded=bool(view.get("active_quotations"))):
        _render_customer_quotation_rows(list(view.get("active_quotations") or []), "customer_quote")
    with st.expander(f"Thỏa thuận thương mại ({len(view.get('active_agreements') or [])})", expanded=bool(view.get("active_agreements"))):
        _render_customer_agreement_rows(list(view.get("active_agreements") or []), "customer_agr")


def _render_customer_quotation_rows(rows: list[Mapping[str, Any]], key_prefix: str) -> None:
    if not rows:
        st.caption("UNKNOWN — chưa có báo giá liên quan trong dữ liệu hiện tại.")
        return
    st.dataframe(
        [
            {
                "Mã báo giá": _value(row.get("quote_reference")),
                "Phiên bản": _value(row.get("version")),
                "Trạng thái": _value(row.get("status_code")),
                "Tuyến": _value(row.get("route")),
                "Giá báo khách (VND)": row.get("price_snapshot_vnd"),
                "Lô liên kết": _value(row.get("shipment_id")),
            }
            for row in rows
        ],
        hide_index=True,
        use_container_width=True,
    )
    for index, row in enumerate(rows):
        button_col, note_col = st.columns([1.4, 4.6])
        if button_col.button(
            f"Mở Sales & Báo Giá · {_value(row.get('quote_reference'))}",
            key=f"{key_prefix}_open_{index}_{row.get('quote_id')}",
            use_container_width=True,
        ):
            st.session_state.quote_detail_id = str(row.get("quote_id"))
            st.session_state.active_page = "Sales & Báo Giá"
            st.rerun()
        note_col.caption(f"source: {_value(row.get('source'))}")


def _render_customer_agreement_rows(rows: list[Mapping[str, Any]], key_prefix: str) -> None:
    if not rows:
        st.caption("UNKNOWN — chưa có thỏa thuận thương mại liên quan trong dữ liệu hiện tại.")
        return
    st.dataframe(
        [
            {
                "Mã thỏa thuận": _value(row.get("agreement_reference")),
                "Phiên bản": _value(row.get("version")),
                "Trạng thái": _value(row.get("status_code")),
                "Báo giá": _value(row.get("quote_reference")),
                "Incoterm": _value(row.get("incoterm")),
                "Dịch vụ đã bán": _value(row.get("services_sold")),
                "Khách cần giao": _value(row.get("required_date")),
                "Bàn giao": _value(row.get("handoff_readiness")),
                "Shipment": _value(row.get("shipments")),
            }
            for row in rows
        ],
        hide_index=True,
        use_container_width=True,
    )
    for index, row in enumerate(rows):
        button_col, note_col = st.columns([1.4, 4.6])
        if button_col.button(
            f"Mở Thỏa Thuận & Bàn Giao · {_value(row.get('agreement_reference'))}",
            key=f"{key_prefix}_open_{index}_{row.get('agreement_id')}",
            use_container_width=True,
        ):
            st.session_state.agreement_detail_id = str(row.get("agreement_id"))
            st.session_state.active_page = "Thỏa Thuận & Bàn Giao"
            st.rerun()
        note_col.caption(f"source: {_value(row.get('source'))}")


def _render_factory(view: Mapping[str, Any]) -> None:
    st.markdown("### Factory / supplier lot context")
    st.caption(f"Next coordination need: {_value(view.get('next_coordination'))}")
    lots = list(view.get("lots") or [])
    if lots:
        st.dataframe(
            [
                {
                    "Shipment": _value(row.get("shipment_id")),
                    "Lot": _value(row.get("lot")),
                    "Product": _value(row.get("product")),
                    "Qty": _value(row.get("quantity")),
                    "Weight": _value(row.get("weight")),
                    "CBM": _value(row.get("cbm")),
                    "Ready date": _value(row.get("ready_date")),
                    "Readiness": _value(row.get("readiness")),
                    "Pickup contact": _value(row.get("pickup_contact")),
                    "Completeness": _value(row.get("completeness")),
                }
                for row in lots
            ],
            hide_index=True,
            use_container_width=True,
        )
        st.caption("Các cột quantity/weight/CBM/ready là shipment/lot-specific; UNKNOWN không được suy đoán.")
    else:
        st.info("UNKNOWN — chưa có factory lot record chuẩn để hiển thị.")
    with st.expander(f"Related shipments ({len(view.get('shipments') or [])})", expanded=True):
        _render_shipment_rows(list(view.get("shipments") or []), "factory_shipments")
    with st.expander("Missing / unknown data", expanded=True):
        for gap in view.get("gaps") or [UNKNOWN]:
            st.markdown(f"- {_value(gap)}")


def _render_partner(view: Mapping[str, Any]) -> None:
    roles = ", ".join(_value(role) for role in view.get("roles") or [UNKNOWN])
    st.markdown(f"### Roles by shipment · {roles}")
    st.caption("Partner/Agent context là workspace tổng quát. Finance bên dưới chỉ là projection canonical theo từng shipment.")
    rows = list(view.get("shipments") or [])
    if rows:
        st.dataframe(
            [
                {
                    "Shipment": _value(row.get("shipment_id")),
                    "Role": _value(row.get("role")),
                    "Operational context": _value(row.get("operational_context")),
                    "Route": _value(row.get("route")),
                    "Status": _value(row.get("status")),
                    "Attention": _value(row.get("attention")),
                }
                for row in rows
            ],
            hide_index=True,
            use_container_width=True,
        )
        _render_shipment_rows(rows, "partner_shipments")
    else:
        st.info("UNKNOWN — chưa có shipment liên quan đến partner/agent này.")
    with st.expander(f"Evidence / documents ({len(view.get('documents') or [])})", expanded=True):
        documents = view.get("documents") or []
        if documents:
            st.dataframe(
                [
                    {
                        "Shipment": _value(row.get("shipment_id")),
                        "Document": _value(row.get("document")),
                        "Status": _value(row.get("status")),
                        "Source": _value(row.get("source")),
                    }
                    for row in documents
                ],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption("UNKNOWN — chưa có document evidence liên quan.")
    with st.expander("Canonical financial projection", expanded=False):
        st.caption(_value(view.get("financial_note")))
        finance = view.get("financial_projection") or []
        if finance:
            st.dataframe(
                [
                    {"Shipment": _value(row.get("shipment_id")), "Status": _value(row.get("status")), "Label": _value(row.get("label")), "Source": _value(row.get("source"))}
                    for row in finance
                ],
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption("UNKNOWN — không có projection canonical theo shipment.")
    with st.expander("Missing / unknown data", expanded=True):
        for gap in view.get("gaps") or [UNKNOWN]:
            st.markdown(f"- {_value(gap)}")


def _selector(entity_type: str, options: list[dict[str, str]]) -> None:
    typed = [option for option in options if option.get("entity_type") == entity_type]
    label = {"customer": "Customer", "factory": "Factory / Supplier", "partner": "Partner / Agent"}[entity_type]
    st.markdown(f"#### {label}")
    if not typed:
        st.caption("UNKNOWN — chưa có entity option từ dữ liệu hiện tại.")
        return
    selected = st.selectbox(
        f"Chọn {label}",
        typed,
        format_func=lambda option: f"{option['label']} · {option['entity_key']}",
        key=f"entity_selector_{entity_type}",
    )
    if st.button(f"Open {label} context", key=f"entity_open_{entity_type}", type="primary"):
        open_entity_context(entity_type, selected["entity_key"])


def ui_entity_context() -> None:
    """Render the generic read-only entity workspace."""

    st.markdown(
        """
        <style>
        .entity-context-kicker { color: #0B6E99; font-size: .68rem; font-weight: 800; letter-spacing: .14em; }
        .entity-context-note { color: #475467; font-size: .82rem; border-left: 3px solid #0B6E99; background: #F0F7FA; padding: .55rem .75rem; margin: .65rem 0 .9rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    shipments = st.session_state.get("db_shipments", {})
    customers = st.session_state.get("db_customers", {})
    options = list_context_entities(customers, shipments)
    request = _request()

    st.markdown("<div class='entity-context-kicker'>ENTITY CONTEXT · READ-ONLY WORKSPACE</div>", unsafe_allow_html=True)
    st.title("Customer / Factory / Partner 360")
    st.markdown(
        "<div class='entity-context-note'>Master identity stays separate from shipment/lot facts. "
        "Missing data remains UNKNOWN. Navigation here does not save or change business data.</div>",
        unsafe_allow_html=True,
    )

    if not request["entity_type"] or not request["entity_key"]:
        st.info("Chọn một entity để xem context quanh các shipment liên quan.")
        c1, c2, c3 = st.tabs(["Customer 360", "Factory / Supplier 360", "Partner / Agent 360"])
        with c1:
            _selector("customer", options)
        with c2:
            _selector("factory", options)
        with c3:
            _selector("partner", options)
        return

    entity_label = {"customer": "Customer 360", "factory": "Factory / Supplier 360", "partner": "Partner / Agent 360"}.get(request["entity_type"], "Entity Context")
    st.subheader(f"{entity_label} · {_value(request['entity_key'])}")
    back_col, nav_col = st.columns([1.4, 4.6])
    if request["return_shipment_id"]:
        if back_col.button("← Back to Shipment 360", key="entity_back_shipment", use_container_width=True):
            _open_shipment(request["return_shipment_id"])
    else:
        back_label = "← Back to Review Queue" if request.get("return_page") == "Review Queue" else "← Back to Dashboard"
        if back_col.button(back_label, key="entity_back_dashboard", use_container_width=True):
            _go_dashboard()
    nav_col.caption("Read-only context · source-bound fields · no entity CRUD")

    quotes = st.session_state.get("db_quotes") or {}
    agreements = st.session_state.get("db_agreements") or {}
    try:
        view = build_entity_context(
            request["entity_type"],
            request["entity_key"],
            customers=customers,
            shipments=shipments,
            quotes=quotes,
            agreements=agreements,
        )
    except ValueError:
        st.error("Entity type không được hỗ trợ.")
        return
    _render_master(view)
    if request["entity_type"] == "customer":
        _render_customer(view)
    elif request["entity_type"] == "factory":
        _render_factory(view)
    else:
        _render_partner(view)


__all__ = ["open_entity_context", "ui_entity_context"]
