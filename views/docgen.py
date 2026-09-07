"""📄 CHỨNG TỪ — Shipment Document Pack Generator (LOG-DOCGEN-01 V1).

Rendered inside the existing shipment workspace.  It is beginner-first and
kept compact: per-card progressive-disclosure inputs, a Vietnamese status /
missing-information card per document type, preflight, generate / download /
issue, and history.

Each legal document owns its OWN identity (HDNT / PL / HDMB / PXK number and
date).  Unknown business facts stay unknown: dates are not forced to today and
a blank quantity/price is not silently turned into 0.  VAT is locked at 8%
(read-only).  PXK must reference an explicitly selected source (HDMB or PL).

Debit USD is shown as deferred.  The writer/service layer enforces RBAC; this
view only renders (but shows the bounded issue action for operations_write).
"""

from __future__ import annotations

import math
from datetime import date
from decimal import Decimal
from typing import Any

import pandas as pd
import streamlit as st

from core.auth import (
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
    link_contract_to_shipment,
)
from core.docgen import generator as gen
from core.docgen.rules import (
    BLOCKED,
    DEBIT_USD,
    GENERATED,
    HDMB,
    HDNT,
    ISSUED,
    MISSING_INFO,
    NOT_APPLICABLE,
    OWNER_RULE_REQUIRED,
    PL,
    PXK,
    READY,
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
    if value is None:
        return "—"
    total = Decimal(str(value or 0))
    return f"{total:,.0f}".replace(",", ".")


def _readiness_card(label: str, doc_type: str, card: dict[str, Any]) -> None:
    state = card.get("state", OWNER_RULE_REQUIRED)
    icon = _STATE_ICON.get(state, "🔴")
    reason = card.get("reason", "")
    missing = card.get("missing") or []
    st.markdown(f"{icon} **{label}** — {_STATE_LABEL.get(state, state)}")
    st.caption(reason)
    if missing:
        st.caption("• " + " · ".join(str(m) for m in missing))
    if doc_type == DEBIT_USD:
        st.caption("Debit USD — Chưa triển khai")


def _cell_number(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str) and not value.strip():
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:  # noqa: BLE001
        return None


def _goods_dataframe(raw: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for i, item in enumerate(raw or [], start=1):
        rows.append(
            {
                "STT": int(i),
                "Mô tả hàng hóa": str(item.get("description") or ""),
                "Đơn vị tính": str(item.get("unit") or ""),
                "Số lượng": item.get("quantity") if item.get("quantity") is not None else None,
                "Đơn giá (chưa VAT)": item.get("unit_price_vnd_excl_vat") if item.get("unit_price_vnd_excl_vat") is not None else None,
                "VAT%": 8,
            }
        )
    return pd.DataFrame(rows, columns=_GOODS_COLUMNS)


def _from_dataframe(df: pd.DataFrame) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        if not str(row.get("Mô tả hàng hóa") or "").strip():
            continue
        quantity = _cell_number(row.get("Số lượng"))
        unit_price = _cell_number(row.get("Đơn giá (chưa VAT)"))
        lines.append(
            {
                "description": str(row.get("Mô tả hàng hóa") or "").strip(),
                "unit": str(row.get("Đơn vị tính") or "").strip(),
                "quantity": quantity,
                "unit_price_vnd_excl_vat": unit_price,
                "vat_rate": Decimal("0.08"),
            }
        )
    return lines


def _pxk_source_candidates(sid: str) -> list[dict[str, Any]]:
    """Build explicit PXK source candidates (HDMB / PL) for this shipment."""
    docs = load_docgen_documents(sid)
    candidates: list[dict[str, Any]] = []
    for _id, doc in docs.items():
        if str(doc.get("document_type") or "").upper() not in (HDMB, PL):
            continue
        snapshot = doc.get("source_snapshot") or {}
        goods_lines = snapshot.get("goods_lines") or []
        candidates.append(
            {
                "source_document_type": str(doc.get("document_type") or "").upper(),
                "source_contract_id": str(doc.get("document_id") or "").strip(),
                "source_revision": doc.get("generation_revision") or doc.get("revision") or 1,
                "source_line_count": len(goods_lines),
                "source_goods_line": list(goods_lines)[0] if goods_lines else {},
                "label": f"{_DOC_LABEL.get(str(doc.get('document_type') or '').upper(), doc.get('document_type'))} {doc.get('document_id')} — {len(goods_lines)} dòng",
            }
        )
    return candidates


def _identity_expanders(sid: str) -> dict[str, Any]:
    """Progressive-disclosure per-document identity inputs.

    Each legal document keeps its own number/date.  We never reuse one number
    across document types and never fall back to DOCGEN-{sid} as a legal number.
    Absent dates stay absent (never silently defaulted to today).
    """
    def _val(base: str) -> Any:
        return st.session_state.get(f"{base}_{sid}")

    identity: dict[str, Any] = {
        "hdnt_no": None,
        "hdnt_date": None,
        "valid_from": None,
        "valid_to": None,
        "pl_no": None,
        "pl_date": None,
        "hdmb_no": None,
        "hdmb_date": None,
        "pxk_no": None,
        "pxk_date": None,
        "currency": "VND",
        "id": None,
    }

    with st.expander("📜 Hợp đồng nguyên tắc (HDNT)", expanded=bool(_val("docgen_hdntno"))):
        identity["hdnt_no"] = st.text_input("Số HDNT", key=f"docgen_hdntno_{sid}")
        identity["hdnt_date"] = st.date_input("Ngày ký HDNT", value=None, key=f"docgen_hdntdate_{sid}")
        c1, c2 = st.columns(2)
        identity["valid_from"] = c1.date_input("Hiệu lực từ", value=None, key=f"docgen_validfrom_{sid}")
        identity["valid_to"] = c2.date_input("Hiệu lực đến", value=None, key=f"docgen_validto_{sid}")

    with st.expander("📄 Phụ lục Hợp đồng (PL)", expanded=bool(_val("docgen_plno"))):
        identity["pl_no"] = st.text_input("Số PL", key=f"docgen_plno_{sid}")
        identity["pl_date"] = st.date_input("Ngày PL", value=None, key=f"docgen_pl_date_{sid}")
        st.caption("HDNT cha được chọn ở phần tái sử dụng / liên kết bên dưới.")

    with st.expander("🛒 Hợp đồng mua bán (HDMB)", expanded=bool(_val("docgen_hdmbno"))):
        identity["hdmb_no"] = st.text_input("Số HDMB", key=f"docgen_hdmbno_{sid}")
        identity["hdmb_date"] = st.date_input("Ngày HDMB", value=None, key=f"docgen_hdmb_date_{sid}")

    with st.expander("📦 Phiếu xuất kho (PXK)", expanded=bool(_val("docgen_pxkno"))):
        identity["pxk_no"] = st.text_input("Số PXK", key=f"docgen_pxkno_{sid}")
        identity["pxk_date"] = st.date_input("Ngày PXK", value=None, key=f"docgen_pxk_date_{sid}")

    return identity


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

    # ---- purchase goods editor (source of truth for money) ----
    st.markdown("### 🧾 Hàng hóa mua (nguồn sự thật)")
    st.caption("Đây là dòng hàng hóa mua đã được xác nhận. Không suy ra từ báo giá/dịch vụ/hàng nhà máy. Đơn giá/số lượng trống = CHƯA BIẾT (không tự coi là 0).")
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
            "VAT%": st.column_config.NumberColumn(min_value=8, max_value=8, step=1, disabled=True, help="Thuế GTGT 8% (V1 cố định)"),
        },
    )
    goods_lines = _from_dataframe(edited)
    st.session_state[goods_key] = goods_lines

    # ---- delivery facts for PXK (kept absent until explicitly entered) ----
    st.markdown("### 🚚 Giao hàng (cho PXK)")
    dc1, dc2 = st.columns(2)
    delivery_completed = dc1.checkbox("Đã giao hàng xong (DELIVERY_COMPLETED = TRUE)", value=False, key=f"docgen_deliv_{sid}")
    delivery_date = dc2.date_input("Ngày giao thực tế", value=None, key=f"docgen_delivdate_{sid}")
    dl1, dl2 = st.columns(2)
    delivery_location = dl1.text_input("Địa điểm nhận hàng thực tế", key=f"docgen_delivloc_{sid}")
    receiver_name = dl2.text_input("Người nhận hàng", key=f"docgen_recv_{sid}")
    z1, z2 = st.columns(2)
    receiver_title = z1.text_input("Chức vụ người nhận", key=f"docgen_recvtitle_{sid}")
    delivery = {
        "delivery_completed": delivery_completed,
        "delivery_date": str(delivery_date) if delivery_date else "",
        "delivery_location": delivery_location,
        "receiver_name": receiver_name,
        "receiver_title": receiver_title,
    }

    # ---- per-document identity (progressive disclosure) ----
    st.markdown("### 🔐 Định danh pháp lý từng chứng từ")
    identity = _identity_expanders(sid)

    # ---- HDNT reuse / linkage ----
    contracts = load_contracts()
    hdnt_candidates = {k: c for k, c in contracts.items() if str(c.get("kind") or c.get("type") or "").upper() == HDNT}
    reuse = {}
    if agent:
        reuse = gen.reuse_decision_for_agent(contracts, agent=agent, company=company)
    parent_hdnt = None
    st.markdown("#### 🔗 HDNT cha / tái sử dụng")
    if reuse.get("valid_count", 0) >= 1:
        if reuse.get("needs_selection"):
            valid_labels = {str(c.get("id") or c.get("hdnt_no") or c.get("contract_no")): c for c in reuse.get("valid_hdnt", [])}
            chosen = st.selectbox("Chọn HDNT hợp lệ để tái sử dụng", [""] + list(valid_labels.keys()), format_func=lambda k: k or "-- Chọn HDNT --", key=f"docgen_parent_{sid}")
            parent_hdnt = valid_labels.get(chosen) if chosen else None
            st.caption("Có nhiều HDNT hợp lệ — cần chọn một HDNT để tái sử dụng (không tự chọn mới nhất).")
        else:
            parent_hdnt = reuse.get("reuse_target")
            st.caption(f"Tái sử dụng HDNT hiện có: {parent_hdnt.get('hdnt_no') or parent_hdnt.get('contract_no') or parent_hdnt.get('id')} — không tạo HDNT mới.")
    else:
        hdnt_keys = list(hdnt_candidates.keys())
        parent_label = st.selectbox("HDNT cha cho PL", [""] + hdnt_keys, format_func=lambda k: str(k) if not k else str(hdnt_candidates[k].get("contract_no") or k), key=f"docgen_parent_{sid}") if hdnt_keys else None
        parent_hdnt = hdnt_candidates.get(parent_label) if parent_label else None
        st.caption("Chưa có HDNT hợp lệ — có thể tạo HDNT mới khi xuất.")

    # ---- PXK explicit source ----
    pxk_candidates = _pxk_source_candidates(sid)
    pxk_source = None
    st.markdown("#### 📦 Nguồn PXK (HDMB/PL đã chọn)")
    if pxk_candidates:
        chosen_label = st.selectbox("Chọn chứng từ nguồn cho PXK", [""] + [c["label"] for c in pxk_candidates], key=f"docgen_pxksrc_{sid}")
        if chosen_label:
            pxk_source = next(c for c in pxk_candidates if c["label"] == chosen_label)
    else:
        st.caption("Chưa có HDMB/PL đã xuất cho lô này. Xuất HDMB hoặc PL trước, sau đó chọn làm nguồn PXK.")

    st.divider()

    # ---- compute totals & readiness ----
    contract_view = dict(identity)
    pack = gen.build_document_pack(
        shipment_id=sid,
        goods_lines=goods_lines,
        delivery_completed=delivery_completed,
        agent=agent,
        company=company,
        parent_contract=parent_hdnt,
        contract=contract_view,
        pxk_source=pxk_source,
        delivery=delivery,
        contracts=contracts,
    )
    totals = pack["totals"]
    st.markdown(f"**Tổng giá trị sau thuế:** {_money(totals.get('total_after_vat'))} VND  ·  Ngưỡng HDMB: {_money(VND_THRESHOLD)} VND")
    st.caption(f"Tiền hàng: {_money(totals.get('subtotal'))} VND · Thuế GTGT 8% (V1 cố định)" if totals.get("subtotal") is not None and totals.get("subtotal") != 0 else "Tiền hàng: — · Thuế GTGT 8% (V1 cố định)")

    cards = {c["document_type"]: c for c in pack["cards"]}
    states = {c["document_type"]: c["state"] for c in pack["cards"]}

    col1, col2, col3 = st.columns(3)
    with col1:
        _readiness_card("HDNT", HDNT, cards.get(HDNT, {}))
        _readiness_card("PL", PL, cards.get(PL, {}))
        _readiness_card("HDMB", HDMB, cards.get(HDMB, {}))
    with col2:
        _readiness_card("PXK", PXK, cards.get(PXK, {}))
        _readiness_card("Debit USD", DEBIT_USD, cards.get(DEBIT_USD, {}))
    with col3:
        st.markdown("**Tổng quát**")
        st.caption("Tổng < 50.000.000 VND → HDNT + PL.")
        st.caption("Tổng >= 50.000.000 VND → HDMB.")
        st.caption("PXK chỉ khi đã giao hàng xong, có đủ thông tin nhận hàng và có đúng nguồn 1 dòng hàng.")
        if not DOCGEN_TEMPLATE_DIR:
            st.warning("Chưa cấu hình thư mục template chứng từ (DOCGEN_TEMPLATE_DIR).")
            st.caption("TEMPLATE_ASSET_STORAGE_OWNER_GATE")

    st.divider()

    xlsx_path, docx_path = _template_paths()
    g1, g2 = st.columns([1, 1])
    want_generate = False
    with g1:
        if st.button("🟢 Xuất chứng từ đang sẵn sàng", use_container_width=True, disabled=not can_generate_documents()):
            want_generate = True
    with g2:
        st.caption("Quyền xuất: sales_write. Quyền phát hành: operations_write.")

    if want_generate:
        _do_generate(sid, agent, company, goods_lines, contract_view, parent_hdnt, delivery, pxk_source, xlsx_path, docx_path, states, reuse)

    # ---- history + issue ----
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
            issue_permitted = can_issue_documents()
            for d in docs.values():
                status = str(d.get("status") or "").upper()
                doc_id = str(d.get("document_id") or "")
                rev = d.get("generation_revision") or d.get("revision") or 1
                label = f"{d.get('output_file_name') or d.get('document_type')} — {d.get('document_type')} R{rev} ({status})"
                if status == ISSUED:
                    st.caption(f"🔒 {label} — đã phát hành, không sửa được")
                elif status == GENERATED:
                    st.caption(f"📝 {label}")
                    if issue_permitted:
                        if st.button(f"✅ Phát hành {doc_id} R{rev}", key=f"issue_{doc_id}_{rev}"):
                            from core.docgen.generator import DocumentGenerationError

                            try:
                                gen.issue_document(doc_id, revision=rev)
                                st.success("Đã phát hành (ISSUED).")
                                st.rerun()
                            except DocumentGenerationError as exc:
                                st.warning(exc.readiness.reason)
                    else:
                        st.caption("(Chỉ Admin/Support được phát hành.)")
                else:
                    st.caption(label)


def _do_generate(
    sid: str,
    agent: dict[str, Any] | None,
    company: dict[str, Any] | None,
    goods_lines: list[dict[str, Any]],
    contract_view: dict[str, Any],
    parent_hdnt: dict[str, Any] | None,
    delivery: dict[str, Any],
    pxk_source: dict[str, Any] | None,
    xlsx_path: str | None,
    docx_path: str | None,
    states: dict[str, str],
    reuse: dict[str, Any],
) -> None:
    if not agent or not company:
        st.error("Cần chọn Đại lý và Công ty để xuất chứng từ.")
        return
    if not DOCGEN_TEMPLATE_DIR:
        st.error("Chưa cấu hình thư mục template chứng từ (DOCGEN_TEMPLATE_DIR).")
        return

    actor = current_actor_context()
    for line in goods_lines:
        line["confirmed_by"] = actor["username"]
        line["confirmed_at"] = _today_iso() if line.get("confirmed_at") is None else line["confirmed_at"]

    to_generate = [dt for dt, state in states.items() if state == READY and dt in (HDNT, PL, HDMB, PXK)]
    # HDNT reuse: if a valid HDNT exists we do NOT auto-generate a new one.
    if HDNT in to_generate and reuse.get("valid_count", 0) >= 1:
        if reuse.get("needs_selection"):
            st.warning("Có nhiều HDNT hợp lệ — cần chọn một HDNT để tái sử dụng, không tạo HDNT mới.")
            to_generate.remove(HDNT)
        else:
            st.info(f"Tái sử dụng HDNT {reuse['reuse_target'].get('hdnt_no') or reuse['reuse_target'].get('contract_no') or reuse['reuse_target'].get('id')} — không tạo HDNT mới.")
            to_generate.remove(HDNT)

    if not to_generate:
        st.warning("Không có chứng từ nào đang ở trạng thái Sẵn sàng để xuất.")
        return

    template_by_doc = {HDNT: docx_path, PL: xlsx_path, HDMB: xlsx_path, PXK: xlsx_path}
    existing = load_docgen_documents(sid)

    produced = 0
    for doc_type in to_generate:
        doc_contract = dict(contract_view)
        # Each document gets its own legal identity field; we never reuse one number.
        doc_contract["id"] = (doc_contract.get(f"{doc_type.lower()}_no") or "").strip().upper()
        if not doc_contract["id"]:
            st.warning(f"{_DOC_LABEL[doc_type]}: thiếu số chứng từ.")
            continue
        try:
            result = gen.generate_document(
                doc_type,
                shipment_id=sid,
                agent=agent,
                company=company,
                goods_lines=goods_lines,
                contract=doc_contract,
                parent_contract=parent_hdnt if doc_type == PL else (parent_hdnt if doc_type == HDNT else None),
                delivery=delivery if doc_type == PXK else delivery,
                template_path_xlsx=template_by_doc.get(doc_type),
                template_path_docx=template_by_doc.get(doc_type),
                existing_documents=existing,
                pxk_source=pxk_source if doc_type == PXK else None,
            )
        except gen.DocumentGenerationError as exc:
            st.warning(f"{_DOC_LABEL.get(doc_type, doc_type)}: {exc.readiness.reason}")
            continue
        except PermissionError as exc:
            st.error("Bạn không có quyền xuất chứng từ (sales_write).")
            continue

        # Persist contract + additive shipment linkage.
        doc_contract["kind"] = doc_type
        doc_contract["contract_no"] = result["metadata"].get("document_no") or doc_contract.get(f"{doc_type.lower()}_no")
        doc_contract["agent_id"] = agent.get("agent_id")
        doc_contract["company_id"] = company.get("company_id")
        if doc_type in (PL, HDMB, HDNT):
            save_contract_to_cloud(dict(doc_contract))
            link_contract_to_shipment(str(doc_contract["id"]), sid)
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


def _today_iso() -> str:
    return date.today().isoformat()


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
