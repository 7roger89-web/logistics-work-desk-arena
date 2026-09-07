"""📄 CHỨNG TỪ — Shipment Document Pack Generator (LOG-DOCGEN-01 V1).

Rendered inside the existing shipment workspace.  It is beginner-first and
kept compact: each card shows only the Vietnamese status, why applicable / not
applicable, the selected source, missing information, preflight, generate /
download, and history.

Debit USD is shown as deferred.  The writer/service layer enforces RBAC; this
view only renders.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import pandas as pd
import streamlit as st

from core.auth import (
    current_user,
    can_generate_documents,
    can_issue_documents,
    current_actor_context,
)
from core.config import DOCGEN_TEMPLATE_DIR
from core.database import (
    load_authority_agents,
    load_authority_companies,
    load_contracts,
    load_docgen_documents,
    save_authority_agent,
    save_authority_company,
    save_docgen_document,
    save_contract_to_cloud,
)
from core.docgen import generator as gen
from core.docgen.rules import (
    DEBIT_USD,
    HDMB,
    HDNT,
    ISSUED,
    MISSING_INFO,
    NOT_APPLICABLE,
    OWNER_RULE_REQUIRED,
    PL,
    PXK,
    READY,
    BLOCKED,
    VND_THRESHOLD,
)

_STATE_ICON = {
    READY: "🟢",
    MISSING_INFO: "🟠",
    NOT_APPLICABLE: "⚪",
    OWNER_RULE_REQUIRED: "🔴",
    BLOCKED: "🚫",
    "DEFERRED": "⏸️",
}
_STATE_LABEL = {
    READY: "Sẵn sàng",
    MISSING_INFO: "Thiếu thông tin",
    NOT_APPLICABLE: "Không áp dụng",
    OWNER_RULE_REQUIRED: "Cần quyết định",
    BLOCKED: "Bị chặn",
    "DEFERRED": "Chưa triển khai",
}
_DOC_LABEL = {
    HDNT: "Hợp đồng nguyên tắc",
    PL: "Phụ lục Hợp đồng",
    HDMB: "Hợp đồng mua bán",
    PXK: "Phiếu xuất kho",
    DEBIT_USD: "Debit USD",
}

_TEMPLATE_FILES = {HDNT: "HDNT-TT-agent.docx", PL: "truong-thanh-agent.xlsx", HDMB: "truong-thanh-agent.xlsx", PXK: "truong-thanh-agent.xlsx"}

_GOODS_COLUMNS = ["STT", "Mô tả hàng hóa", "Đơn vị tính", "Số lượng", "Đơn giá (chưa VAT)", "VAT%"]


def _template_paths() -> tuple[str | None, str | None]:
    if DOCGEN_TEMPLATE_DIR is None:
        return None, None
    return (
        str(DOCGEN_TEMPLATE_DIR / _TEMPLATE_FILES[PL]),
        str(DOCGEN_TEMPLATE_DIR / _TEMPLATE_FILES[HDNT]),
    )


def _money(value: Any) -> str:
    total = Decimal(str(value or 0))
    return f"{total:,.0f}".replace(",", ".")


def _readiness_card(label: str, doc_type: str, view: str, card: dict[str, Any]) -> None:
    state = card.get("state", OWNER_RULE_REQUIRED)
    icon = _STATE_ICON.get(state, "🔴")
    reason = card.get("reason", "")
    missing = card.get("missing") or []
    st.markdown(
        f"{icon} **{label}** — {_STATE_LABEL.get(state, state)}"
    )
    st.caption(reason)
    if missing:
        st.caption("• " + " · ".join(str(m) for m in missing))
    if doc_type == DEBIT_USD:
        st.caption("Debit USD — Chưa triển khai")


def _goods_dataframe(raw: list[dict[str, Any]]) -> pd.DataFrame:
    rows = [
        {
            "STT": int(i),
            "Mô tả hàng hóa": str(item.get("description") or ""),
            "Đơn vị tính": str(item.get("unit") or ""),
            "Số lượng": item.get("quantity") or 0,
            "Đơn giá (chưa VAT)": item.get("unit_price_vnd_excl_vat") or 0,
            "VAT%": 8,
        }
        for i, item in enumerate(raw or [], start=1)
    ]
    return pd.DataFrame(rows, columns=_GOODS_COLUMNS)


def _from_dataframe(df: pd.DataFrame) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        if not str(row.get("Mô tả hàng hóa") or "").strip():
            continue
        lines.append(
            {
                "description": str(row.get("Mô tả hàng hóa") or "").strip(),
                "unit": str(row.get("Đơn vị tính") or "").strip(),
                "quantity": row.get("Số lượng") or 0,
                "unit_price_vnd_excl_vat": row.get("Đơn giá (chưa VAT)") or 0,
                "vat_rate": Decimal("0.08"),
            }
        )
    return lines


def ui_document_pack(sid: str, ship: dict[str, Any]) -> None:
    st.markdown("## 📄 CHỨNG TỪ")
    st.caption("Hệ thống tự điền dữ liệu đã biết, chỉ ra thông tin còn thiếu, người dùng bổ sung/xác nhận rồi xuất chứng từ.")

    # ---- authority master ----
    companies = load_authority_companies()
    agents = load_authority_agents()
    company_keys = list(companies.keys())
    agent_keys = list(agents.keys())

    c1, c2 = st.columns(2)
    selected_company_id = c1.selectbox("Công ty (Bên mua / Trường Thành)", company_keys, format_func=lambda k: companies.get(k, {}).get("legal_name", k)) if company_keys else None
    selected_agent_id = c2.selectbox("Đại lý (Bên bán)", agent_keys, format_func=lambda k: agents.get(k, {}).get("legal_name", k)) if agent_keys else None

    if not company_keys:
        st.info("Chưa có hồ sơ pháp lý Công ty. Tạo hồ sơ tối thiểu bên dưới.")
        _authority_form("company")
    if not agent_keys:
        st.info("Chưa có hồ sơ pháp lý Đại lý. Tạo hồ sơ tối thiểu bên dưới.")
        _authority_form("agent")
    st.divider()

    company = companies.get(selected_company_id) if selected_company_id else None
    agent = agents.get(selected_agent_id) if selected_agent_id else None

    # ---- purchase goods editor ----
    st.markdown("### 🧾 Hàng hóa mua (nguồn sự thật)")
    st.caption("Đây là dòng hàng hóa mua đã được xác nhận. Không suy ra từ báo giá/dịch vụ/hàng nhà máy.")
    goods_key = f"docgen_goods_{sid}"
    raw = st.session_state.get(goods_key) or []
    edited = st.data_editor(
        _goods_dataframe(raw),
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key=f"docgen_goods_editor_{sid}",
        column_config={
            "Số lượng": st.column_config.NumberColumn(min_value=0, step=1),
            "Đơn giá (chưa VAT)": st.column_config.NumberColumn(min_value=0, step=1000),
            "VAT%": st.column_config.NumberColumn(min_value=0, max_value=8, step=1),
        },
    )
    goods_lines = _from_dataframe(edited)
    st.session_state[goods_key] = goods_lines

    # ---- delivery info for PXK ----
    st.markdown("### 🚚 Giao hàng (cho PXK)")
    dc1, dc2 = st.columns(2)
    delivery_completed = dc1.checkbox("Đã giao hàng xong (DELIVERY_COMPLETED = TRUE)", value=False, key=f"docgen_deliv_{sid}")
    delivery_date = dc2.date_input("Ngày giao thực tế", value=date.today(), key=f"docgen_delivdate_{sid}")
    dl1, dl2 = st.columns(2)
    delivery_location = dl1.text_input("Địa điểm nhận hàng thực tế", key=f"docgen_delivloc_{sid}")
    receiver_name = dl2.text_input("Người nhận hàng", key=f"docgen_recv_{sid}")
    z1, z2 = st.columns(2)
    receiver_title = z1.text_input("Chức vụ người nhận", key=f"docgen_recvtitle_{sid}")
    delivery = {
        "delivery_completed": delivery_completed,
        "delivery_date": str(delivery_date),
        "delivery_location": delivery_location,
        "receiver_name": receiver_name,
        "receiver_title": receiver_title,
    }

    # ---- contract inputs ----
    st.markdown("### 📜 Hợp đồng")
    nc1, nc2 = st.columns(2)
    contract_no = nc1.text_input("Số hợp đồng / chứng từ", key=f"docgen_contractno_{sid}")
    contract_date = nc2.date_input("Ngày", value=date.today(), key=f"docgen_contractdate_{sid}")

    v1, v2 = st.columns(2)
    valid_from = v1.date_input("Hiệu lực từ", value=date.today(), key=f"docgen_validfrom_{sid}")
    valid_to = v2.date_input("Hiệu lực đến", value=date.today(), key=f"docgen_validto_{sid}")

    contracts = load_contracts()
    hdnt_contracts = {k: c for k, c in contracts.items() if str(c.get("kind") or "").upper() == HDNT or str(c.get("contract_no") or "").upper().startswith("HDNT")}
    hdnt_keys = list(hdnt_contracts.keys())
    parent_no = st.selectbox("HDNT cha cho PL", [""] + hdnt_keys, format_func=lambda k: k or "-- Chọn HDNT cha --", key=f"docgen_parent_{sid}") if hdnt_keys else st.text_input("Số HDNT cha", key=f"docgen_parent_{sid}")
    parent_contract = hdnt_contracts.get(parent_no) if parent_no else None

    st.divider()

    # ---- compute totals & readiness ----
    pack = gen.build_document_pack(
        shipment_id=sid,
        goods_lines=goods_lines,
        delivery_completed=delivery_completed,
        agent=agent,
        company=company,
        parent_contract=parent_contract,
        contract={"currency": "VND", "contract_no": contract_no, "contract_date": str(contract_date)},
    )
    totals = pack["totals"]
    st.markdown(f"**Tổng giá trị sau thuế:** {_money(totals['total_after_vat'])} VND  ·  Ngưỡng HDMB: {_money(VND_THRESHOLD)} VND")
    st.caption(f"Tiền hàng: {_money(totals['subtotal'])} VND · Thuế GTGT 8%: {_money(totals['vat_amount'])} VND")

    # ---- cards ----
    cards = {c["document_type"]: c for c in pack["cards"]}
    states = {c["document_type"]: c["state"] for c in pack["cards"]}

    col1, col2, col3 = st.columns(3)
    with col1:
        _readiness_card("HDNT", HDNT, "card", cards.get(HDNT, {}))
        _readiness_card("PL", PL, "card", cards.get(PL, {}))
        _readiness_card("HDMB", HDMB, "card", cards.get(HDMB, {}))
    with col2:
        _readiness_card("PXK", PXK, "card", cards.get(PXK, {}))
        _readiness_card("Debit USD", DEBIT_USD, "card", cards.get(DEBIT_USD, {}))
    with col3:
        st.markdown("**Tổng quát**")
        st.caption("Nếu tổng < 50.000.000 VND → HDNT + PL.")
        st.caption("Nếu tổng >= 50.000.000 VND → HDMB.")
        st.caption("PXK chỉ khi đã giao hàng xong và có đúng 1 dòng hàng từ nguồn.")
        if not DOCGEN_TEMPLATE_DIR:
            st.warning("Chưa cấu hình thư mục template chứng từ (DOCGEN_TEMPLATE_DIR).")
            st.caption("TEMPLATE_ASSET_STORAGE_OWNER_GATE")

    st.divider()

    # ---- generate / download / history ----
    xlsx_path, docx_path = _template_paths()
    contract_doc = {
        "id": contract_no.strip().upper() if contract_no and contract_no.strip() else f"DOCGEN-{sid}",
        "contract_no": contract_no,
        "contract_date": str(contract_date),
        "date": str(contract_date),
        "currency": "VND",
        "kind": None,
        "agent_id": agent.get("agent_id") if agent else None,
        "company_id": company.get("company_id") if company else None,
        "parent_contract_id": parent_contract.get("id") if parent_contract else None,
        "goods_lines": goods_lines,
        "valid_from": str(valid_from),
        "valid_to": str(valid_to),
        "client": company.get("legal_name") if company else "",
    }

    g1, g2 = st.columns([1, 1])
    want_generate = False
    with g1:
        if st.button("🟢 Xuất chứng từ đang sẵn sàng", use_container_width=True, disabled=not can_generate_documents()):
            want_generate = True
    with g2:
        st.caption("Quyền xuất: sales_write. Quyền phát hành: operations_write.")

    if want_generate:
        _do_generate(sid, agent, company, goods_lines, contract_doc, parent_contract, delivery, xlsx_path, docx_path, states)

    # history
    docs = load_docgen_documents(sid)
    if docs:
        with st.expander(f"🕒 Lịch sử chứng từ ({len(docs)})", expanded=False):
            rows = [
                {
                    "document_id": d.get("document_id"),
                    "Loại": d.get("document_type"),
                    "Revision": d.get("generation_revision"),
                    "Trạng thái": d.get("status"),
                    "File": d.get("output_file_name"),
                    "Generated": d.get("generated_at"),
                }
                for d in docs.values()
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            for d in docs.values():
                fname = d.get("output_file_name")
                if d.get("output_file_name"):
                    st.caption(f"{fname} — {d.get('document_type')} R{d.get('generation_revision')} ({d.get('status')})")


def _do_generate(
    sid: str,
    agent: dict[str, Any] | None,
    company: dict[str, Any] | None,
    goods_lines: list[dict[str, Any]],
    contract_doc: dict[str, Any],
    parent_contract: dict[str, Any] | None,
    delivery: dict[str, Any],
    xlsx_path: str | None,
    docx_path: str | None,
    states: dict[str, str],
) -> None:
    if not agent or not company:
        st.error("Cần chọn Đại lý và Công ty để xuất chứng từ.")
        return
    if not DOCGEN_TEMPLATE_DIR:
        st.error("Chưa cấu hình thư mục template chứng từ (DOCGEN_TEMPLATE_DIR).")
        return

    actor = current_actor_context()
    contract_doc["goods_lines"] = goods_lines
    for line in goods_lines:
        line["confirmed_by"] = actor["username"]
        line["confirmed_at"] = str(date.today())

    # Pick the document type(s) that are READY.
    to_generate = [dt for dt, state in states.items() if state == READY and dt in (HDNT, PL, HDMB, PXK)]
    if not to_generate:
        st.warning("Không có chứng từ nào đang ở trạng thái Sẵn sàng để xuất.")
        return

    template_by_doc = {HDNT: docx_path, PL: xlsx_path, HDMB: xlsx_path, PXK: xlsx_path}
    existing = load_docgen_documents(sid)

    produced = 0
    for doc_type in to_generate:
        try:
            result = gen.generate_document(
                doc_type,
                shipment_id=sid,
                agent=agent,
                company=company,
                goods_lines=goods_lines,
                contract=contract_doc,
                parent_contract=parent_contract if doc_type == PL else None,
                delivery=delivery,
                template_path_xlsx=template_by_doc.get(doc_type),
                template_path_docx=template_by_doc.get(doc_type),
                existing_documents=existing,
            )
        except gen.DocumentGenerationError as exc:
            st.warning(f"{_DOC_LABEL.get(doc_type, doc_type)}: {exc.readiness.reason}")
            continue

        # Persist contract + metadata.
        contract_doc["kind"] = doc_type
        if doc_type in (PL, HDMB, HDNT):
            save_contract_to_cloud(dict(contract_doc))
        metadata = result["metadata"]
        metadata["generated_by"] = actor["username"]
        if not save_docgen_document(metadata):
            st.error(f"Không lưu metadata {result['document_id']}.")
            continue

        produced += 1
        st.success(f"Đã xuất {_DOC_LABEL.get(doc_type, doc_type)} — {result['output_file_name']} (R{result['revision']})")
        st.download_button(
            f"⬇ Tải {result['output_file_name']}",
            data=result["bytes"],
            file_name=result["output_file_name"],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if doc_type != HDNT else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"dl_{doc_type}_{result['document_id']}_{result['revision']}",
        )

    if not produced:
        st.error("Không có chứng từ nào được xuất.")
    else:
        st.rerun()


def _authority_form(kind: str) -> None:
    with st.expander(f"➕ Thêm hồ sơ { 'Đại lý' if kind == 'agent' else 'Công ty' }", expanded=False):
        if kind == "company":
            key = st.text_input("Mã Công ty", key="doc_company_id")
            name = st.text_input("Tên pháp lý", key="doc_company_name")
            addr = st.text_input("Địa chỉ pháp lý", key="doc_company_addr")
            code = st.text_input("Mã số thuế", key="doc_company_code")
            rep = st.text_input("Người đại diện", key="doc_company_rep")
            title = st.text_input("Chức vụ", key="doc_company_title")
            if st.button("Lưu Công ty", key="doc_company_save"):
                ok = save_authority_company({
                    "company_id": key.strip().upper(),
                    "legal_name": name,
                    "legal_address": addr,
                    "tax_or_legal_code": code,
                    "legal_representative": rep,
                    "representative_title": title,
                })
                st.success("Đã lưu.") if ok else st.error("Không lưu được.")
        else:
            key = st.text_input("Mã Đại lý", key="doc_agent_id")
            name = st.text_input("Tên pháp lý", key="doc_agent_name")
            addr = st.text_input("Địa chỉ pháp lý", key="doc_agent_addr")
            code = st.text_input("Mã số thuế / pháp lý", key="doc_agent_code")
            rep = st.text_input("Người đại diện", key="doc_agent_rep")
            title = st.text_input("Chức vụ", key="doc_agent_title")
            bank_holder = st.text_input("Chủ tài khoản", key="doc_agent_bank_holder")
            bank_no = st.text_input("Số tài khoản", key="doc_agent_bank_no")
            bank_name = st.text_input("Ngân hàng", key="doc_agent_bank_name")
            if st.button("Lưu Đại lý", key="doc_agent_save"):
                ok = save_authority_agent({
                    "agent_id": key.strip().upper(),
                    "legal_name": name,
                    "legal_address": addr,
                    "legal_code_type": "MST",
                    "legal_code": code,
                    "legal_representative": rep,
                    "representative_title": title,
                    "bank_account_holder": bank_holder,
                    "bank_account_number": bank_no,
                    "bank_name": bank_name,
                })
                st.success("Đã lưu.") if ok else st.error("Không lưu được.")
