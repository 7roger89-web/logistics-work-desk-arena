"""Thỏa thuận thương mại & bàn giao vận hành (LOG-C13).

Trang này giữ cho Báo giá / Thỏa thuận / Shipment / Finance Ledger tách biệt:
- Thỏa thuận chỉ ghi nhận điều khoản thương mại (điều khoản thanh toán, trách
  nhiệm, chứng từ, ủy thác nhập khẩu) và KHÔNG tạo payment, transaction,
  allocation hay event Finance Ledger nào.
- Bằng chứng (evidence) được đánh dấu thủ công AVAILABLE/MISSING/WAITING/UNKNOWN;
  không suy "đã ký" từ tên file hay ghi chú.
- Thỏa thuận đã đồng ý (AGREED) không bị ghi đè ngầm: sửa điều khoản tạo một
  bản revision mới (REVISED → DRAFT giữ bản đã đồng ý).
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from core.commercial_agreements import (
    AGREEMENT_STATUSES,
    DEFAULT_PAYMENT_TERM_CHOICES,
    DEFAULT_REQUIRED_DOCUMENTS,
    EVIDENCE_STATES,
    HANDOFF_COMMERCIAL_REVIEW,
    HANDOFF_MISSING_REQUIRED_DATA,
    HANDOFF_READY,
    build_agreement_from_quote,
    commercial_handoff_view,
    handoff_readiness,
    prepare_agreement_for_persistence,
    transition_agreement,
)
from core.auth import has_write_permission
from core.database import load_agreements, save_agreements_to_cloud


def _agreement_store() -> dict[str, dict[str, Any]]:
    if "db_agreements" not in st.session_state:
        st.session_state.db_agreements = load_agreements()
    return st.session_state.db_agreements


def _quote_store() -> dict[str, dict[str, Any]]:
    if "db_quotes" not in st.session_state:
        st.session_state.db_quotes = {}
    return st.session_state.db_quotes


def _customer_store() -> dict[str, dict[str, Any]]:
    if "db_customers" not in st.session_state:
        st.session_state.db_customers = {}
    return st.session_state.db_customers


def _shipment_store() -> dict[str, dict[str, Any]]:
    if "db_shipments" not in st.session_state:
        st.session_state.db_shipments = {}
    return st.session_state.db_shipments


def _actor() -> str:
    return str(st.session_state.get("current_user", {}).get("username") or "SALE")


def _persist_agreement(agreement: dict[str, Any]) -> bool:
    actor = _actor()
    try:
        stamped = prepare_agreement_for_persistence(agreement, actor=actor)
    except ValueError as exc:
        st.error(str(exc))
        return False
    ok = save_agreements_to_cloud({str(stamped["agreement_id"]): stamped})
    if ok:
        _agreement_store()[str(stamped["agreement_id"])] = stamped
        st.session_state.agreement_detail_id = str(stamped["agreement_id"])
        st.session_state.needs_refresh = True
    return ok


def _acceptance_eligible_quotes(quotes: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        quote_id: quote for quote_id, quote in quotes.items()
        if quote.get("status") in ("ACCEPTED", "READY_TO_CREATE_SHIPMENT") and not quote.get("is_deleted")
    }


def _readiness_badge_color(readiness_state: str) -> str:
    if readiness_state == HANDOFF_READY:
        return "var(--ops-green)"
    if readiness_state == HANDOFF_MISSING_REQUIRED_DATA:
        return "var(--ops-red)"
    return "var(--ops-amber)"


def _evidence_badge(state: str) -> str:
    if state == "AVAILABLE":
        return "AVAILABLE ✓"
    if state == "MISSING":
        return "MISSING ✗"
    if state == "WAITING":
        return "WAITING ⏳"
    return "UNKNOWN ?"


def _link_shipments(agreement: dict[str, Any], shipments: dict[str, dict[str, Any]]) -> list[str]:
    """Link agreements to shipments without creating a duplicate shipment.

    If the quote already created a shipment, the same shipment is reused.
    Otherwise the user may choose any existing shipment; no new shipment is
    created from this page.
    """
    linked: list[str] = []
    quote_id = str(agreement.get("quote_id") or "")
    quote_no = str(agreement.get("quote_reference") or "")
    already_linked = set(str(item) for item in agreement.get("shipment_ids") or [])
    candidates = [
        (shipment_id, shipment) for shipment_id, shipment in shipments.items()
        if shipment.get("quote_id") == quote_id or shipment.get("quote_reference") == quote_no
    ]
    if not candidates and quote_id:
        candidates = [
            (shipment_id, shipment) for shipment_id, shipment in shipments.items()
            if str(shipment.get("customer_id")) == str(agreement.get("customer_id"))
            and not shipment.get("is_deleted")
        ]
    for shipment_id, _shipment in candidates:
        if shipment_id not in already_linked:
            linked.append(shipment_id)
    return linked


def _render_agreement_table(agreements: dict[str, dict[str, Any]]) -> None:
    st.subheader("Thỏa thuận thương mại đang theo dõi")
    c1, c2 = st.columns(2)
    search = c1.text_input("Khách hàng / mã thỏa thuận", key="agr_search")
    status = c2.selectbox("Trạng thái", ["Tất cả", *AGREEMENT_STATUSES], key="agr_status_filter")
    rows = []
    for agreement in agreements.values():
        haystack = " ".join(str(agreement.get(k, "")) for k in ("agreement_no", "customer_name", "quote_reference"))
        if search.strip().lower() not in haystack.lower():
            continue
        if status != "Tất cả" and agreement.get("status") != status:
            continue
        readiness = handoff_readiness(agreement)
        rows.append({
            "Mã thỏa thuận": agreement.get("agreement_no", agreement.get("agreement_id", "")),
            "Khách hàng": agreement.get("customer_name", ""),
            "Báo giá đã chốt": agreement.get("quote_reference", ""),
            "Trạng thái": agreement.get("status", "DRAFT"),
            "Incoterm": (agreement.get("commercial_snapshot") or {}).get("incoterm", ""),
            "Bàn giao": readiness["label"],
            "Shipment": ", ".join(str(item) for item in agreement.get("shipment_ids") or []) or "Chưa liên kết",
            "id": agreement.get("agreement_id", ""),
        })
    if not rows:
        st.info("Chưa có thỏa thuận thương mại. Hãy tạo một thỏa thuận từ báo giá đã chốt.")
        return
    rows.sort(key=lambda item: item["Mã thỏa thuận"], reverse=True)
    df = pd.DataFrame(rows)
    st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)
    selected = st.selectbox(
        "Mở thỏa thuận",
        [row["id"] for row in rows],
        format_func=lambda aid: next(row["Mã thỏa thuận"] for row in rows if row["id"] == aid),
        key="agr_open_id",
    )
    if st.button("Mở chi tiết thỏa thuận", type="primary", key="agr_open_button"):
        st.session_state.agreement_detail_id = selected
        st.session_state.active_page = "Thỏa Thuận & Bàn Giao"
        st.rerun()


def _render_new_agreement() -> None:
    st.subheader("Tạo thỏa thuận từ báo giá đã chốt")
    quotes = _quote_store()
    eligible = _acceptance_eligible_quotes(quotes)
    if not eligible:
        st.warning("Chưa có báo giá ở trạng thái ACCEPTED hoặc Sẵn sàng tạo lô. Hãy chốt một báo giá trong Sales & Báo Giá trước.")
        return
    quote_id = st.selectbox(
        "Báo giá đã chốt *",
        sorted(eligible.keys()),
        format_func=lambda qid: f"{eligible[qid].get('quote_no', qid)} · {eligible[qid].get('customer_name', '')} · {eligible[qid].get('status')}",
        key="agr_from_quote_id",
    )
    quote = eligible[quote_id]
    calc = quote.get("calculation", {})
    snapshot = build_agreement_from_quote(quote, actor=_actor())
    with st.expander("Xem snapshot thương mại sẽ được đóng băng", expanded=False):
        st.caption("Các trường sau được giữ nguyên từ báo giá đã chốt; phiên bản báo giá được ghi lại để tránh thay đổi ngầm.")
        st.json({
            "quote_id": snapshot.get("quote_id"),
            "quote_reference": snapshot.get("quote_reference"),
            "quote_version": snapshot.get("quote_version"),
            "customer": snapshot.get("customer_name"),
            "incoterm": snapshot["commercial_snapshot"]["incoterm"],
            "factory_lots": snapshot.get("factory_lots"),
            "services": snapshot["commercial_snapshot"]["service_lines"],
        })
    st.caption("Nhấn nút dưới đây sẽ tạo thỏa thuận DRAFT giữ nguyên toàn bộ điều khoản như trong báo giá đã chốt, "
               "để tránh điều khoản bị thay đổi ngầm. Sau khi khách đồng ý, Sale đánh dấu AGREED.")
    if st.button(
        "Tạo thỏa thuận từ báo giá này",
        type="primary",
        key="agr_create_from_quote",
        disabled=not has_write_permission("commercial_write"),
    ):
        if not has_write_permission("commercial_write"):
            st.error("Bạn không có quyền tạo thỏa thuận. Liên hệ người quản trị.")
            st.stop()
        if _persist_agreement(snapshot):
            st.success(f"Đã tạo thỏa thuận {snapshot['agreement_no']} (DRAFT) từ báo giá {quote.get('quote_no')}.")
            st.rerun()
        st.error(st.session_state.get("last_db_error") or "Không lưu được thỏa thuận.")


def _render_agreement_detail() -> None:
    agreements = _agreement_store()
    agreement_id = st.session_state.get("agreement_detail_id")
    if not agreement_id or agreement_id not in agreements:
        st.info("Chọn một thỏa thuận từ danh sách để xem chi tiết.")
        return
    agreement = agreements[agreement_id]
    snapshot = agreement.get("commercial_snapshot") or {}
    readiness = handoff_readiness(agreement)
    st.subheader(f"{agreement.get('agreement_no', agreement_id)} · {agreement.get('customer_name', '')}")
    st.caption(
        f"Trạng thái: {agreement.get('status')} · Phiên bản: {agreement.get('version', 1)} · "
        f"Báo giá: {agreement.get('quote_reference', '')} v{agreement.get('quote_version', '?')} · "
        f"Thỏa thuận thương mại, KHÔNG ghi Finance Ledger."
    )
    readiness_color = _readiness_badge_color(readiness["state"])
    st.markdown(
        f"<div style='background:var(--ops-surface);border:1px solid var(--ops-line);border-radius:8px;"
        f"border-left:6px solid {readiness_color};padding:10px 14px'>"
        f"<b>Bàn giao vận hành:</b> <span style='color:{readiness_color};font-weight:800'>{readiness['label']}</span>"
        + (f"<br>{' · '.join(readiness['reasons'])}" if readiness["reasons"] else "")
        + "</div>",
        unsafe_allow_html=True,
    )

    tabs = st.tabs([
        "Phạm vi & Incoterm", "Điều khoản thanh toán",
        "Trách nhiệm", "Chứng từ & bằng chứng",
        "Sửa điều khoản", "Bàn giao vận hành",
    ])
    with tabs[0]:
        st.write({
            "Tuyến": f"{snapshot.get('origin', '')} → {snapshot.get('destination', '')}",
            "Biên giới/tuyến": snapshot.get("route"),
            "Incoterm": snapshot.get("incoterm"),
            "Phương thức": snapshot.get("transport_mode"),
            "Hàng hóa": snapshot.get("goods_description"),
            "Khách cần giao ngày": snapshot.get("expected_delivery_date"),
        })
        st.markdown("#### Nhà máy / lô hàng")
        st.dataframe(pd.DataFrame(agreement.get("factory_lots") or []), use_container_width=True, hide_index=True)
        st.markdown("#### Phạm vi dịch vụ đã bán")
        st.dataframe(pd.DataFrame(snapshot.get("service_lines") or []), use_container_width=True, hide_index=True)
        entrusted = agreement.get("entrusted_import_terms") or {}
        if entrusted.get("active"):
            st.warning("Phí ủy thác nhập khẩu nằm trong phạm vi thỏa thuận.")
            st.json(entrusted)
        else:
            st.info("Không có phí ủy thác nhập khẩu trong thỏa thuận này.")

    with tabs[1]:
        payment = dict(agreement.get("payment_terms") or {})
        st.caption("Điều khoản thanh toán thương mại được ghi nhận ở đây. Việc thanh toán thực tế chỉ phát sinh qua luồng Finance đã tồn tại (không tự động từ trang này).")
        st.multiselect(
            "Điều khoản thanh toán",
            DEFAULT_PAYMENT_TERM_CHOICES,
            default=list(payment.get("selected") or []),
            key="agr_payment_terms",
        )
        credit_days = st.number_input("Credit term (ngày, nếu có)", min_value=0, max_value=365, value=int(payment.get("credit_term_days") or 0), step=1, key="agr_credit_days")
        due_trigger = st.text_input("Điểm kích hoạt hạn thanh toán", value=str(payment.get("due_date_trigger") or "Thanh toán trước khi giao hàng trừ khi có credit term"), key="agr_due_trigger")
        payment_notes = st.text_input("Ghi chú điều khoản thanh toán", value=str(payment.get("notes") or ""), key="agr_payment_notes")
        agreement["payment_terms"] = {
            "selected": st.session_state.agr_payment_terms,
            "credit_term_days": int(credit_days) or None,
            "due_date_trigger": due_trigger.strip(),
            "notes": payment_notes.strip(),
        }

    with tabs[2]:
        responsibilities = dict(agreement.get("responsibilities") or {})
        st.markdown("#### Trường Thành thực hiện")
        tt_text = "\n".join(f"- {item}" for item in responsibilities.get("truong_thanh") or [])
        edited_tt = st.text_area("Phạm vi Trường Thành", value=tt_text, height=120, key="agr_tt_scope")
        st.markdown("#### Khách cần cung cấp")
        cp_text = "\n".join(f"- {item}" for item in responsibilities.get("customer_provides") or [])
        edited_cp = st.text_area("Phạm vi khách hàng", value=cp_text, height=120, key="agr_customer_scope")
        agreement["responsibilities"] = {
            "truong_thanh": [line[2:].strip() for line in edited_tt.split("\n") if line.strip().startswith("- ")],
            "customer_provides": [line[2:].strip() for line in edited_cp.split("\n") if line.strip().startswith("- ")],
        }
        st.markdown("#### Vấn đề chưa xử lý (thương mại)")
        issues_text = "\n".join(f"- {item}" for item in agreement.get("unresolved_issues") or [])
        edited_issues = st.text_area("Chưa giải quyết (mỗi dòng một issue)", value=issues_text, height=80, key="agr_unresolved")
        agreement["unresolved_issues"] = [line[2:].strip() for line in edited_issues.split("\n") if line.strip().startswith("- ")]

    with tabs[3]:
        evidence = dict(agreement.get("evidence") or {})
        st.caption("Bằng chứng được đánh dấu thủ công: AVAILABLE / MISSING / WAITING / UNKNOWN. Không suy 'đã ký' từ tên file hay ghi chú.")
        col_flags = st.columns(4)
        for col, flag, label in zip(col_flags, ("accepted_quotation", "signed_contract", "customer_confirmation", "entrusted_documentation"), (
            "Báo giá được khách chấp nhận",
            "Hợp đồng đã ký / đồng ý điều khoản",
            "Khách xác nhận bằng văn bản",
            "Chứng từ ủy thác nhập khẩu",
        )):
            value = bool(evidence.get(flag))
            evidence[flag] = col.checkbox(label, value=value, key=f"agr_ev_{flag}")
        evidence["notes"] = st.text_input("Ghi chú bằng chứng", value=str(evidence.get("notes") or ""), key="agr_ev_notes")
        agreement["evidence"] = evidence

        st.markdown("#### Chứng từ cần thiết")
        documents = deepcopy(agreement.get("required_documents") or [{"name": name, "evidence_state": "UNKNOWN", "note": ""} for name in DEFAULT_REQUIRED_DOCUMENTS])
        document_edits: list[dict[str, Any]] = []
        for index, document in enumerate(documents):
            a, b, c = st.columns([3, 1.6, 3])
            name = a.text_input("Tên chứng từ", value=document.get("name", ""), key=f"agr_doc_{index}_name")
            state = b.selectbox("Bằng chứng", EVIDENCE_STATES, index=EVIDENCE_STATES.index(str(document.get("evidence_state") or "UNKNOWN").upper()), key=f"agr_doc_{index}_state")
            note = c.text_input("Ghi chú", value=document.get("note", ""), key=f"agr_doc_{index}_note")
            document_edits.append({"name": name.strip(), "evidence_state": state, "note": note.strip()})
        agreement["required_documents"] = document_edits

    with tabs[4]:
        current = agreement.get("status", "DRAFT")
        st.markdown("#### Chuyển trạng thái thỏa thuận")
        st.caption("Thỏa thuận AGREED không bị ghi đè: sửa điều khoản tạo bản revision mới, giữ nguyên bản đã đồng ý.")
        action_cols: list[tuple[str, str]] = []
        if current == "DRAFT":
            action_cols.append(("Gửi Sale xem trước khi gửi khách", "REVIEWING"))
        if current == "REVIEWING":
            action_cols.extend([("Khách đồng ý (AGREED)", "AGREED"), ("Quay lại nháp", "DRAFT")])
        if current in ("DRAFT", "REVIEWING", "AGREED"):
            action_cols.append(("Sửa điều khoản (tạo revision)", "REVISED"))
        if current in ("DRAFT", "REVIEWING"):
            action_cols.append(("Hủy thỏa thuận", "VOID"))
        if action_cols:
            cols = st.columns(len(action_cols))
            for col, (label, target) in zip(cols, action_cols):
                if col.button(label, key=f"agr_transition_{target}"):
                    if target == "AGREED":
                        if not evidence.get("accepted_quotation") and not evidence.get("customer_confirmation") and not evidence.get("signed_contract"):
                            st.warning("Nên đánh dấu ít nhất một bằng chứng chấp nhận (báo giá được chấp nhận / khách xác nhận / hợp đồng ký) trước khi AGREED.")
                    if target == "REVISED":
                        if _render_revision_dialog(agreement):
                            st.rerun()
                        continue
                    try:
                        updated = transition_agreement(agreement, target, actor=_actor())
                    except ValueError as exc:
                        st.error(str(exc))
                        continue
                    if _persist_agreement(updated):
                        st.rerun()
        else:
            st.info("Thỏa thuận đã được đồng ý; muốn sửa điều khoản hãy dùng 'Sửa điều khoản' ở trên.")

        st.markdown("#### Liên kết với lô vận chuyển (Shipment)")
        shipments = _shipment_store()
        candidate_ids = [shipment_id for shipment_id in _link_shipments(agreement, shipments) if shipment_id in shipments]
        if candidate_ids:
            st.caption(f"{len(candidate_ids)} shipment phù hợp được phát hiện. Link vào các lô này KHÔNG tạo shipment mới.")
        with st.form("agr_link_shipments"):
            linked = st.multiselect(
                "Shipment đã liên kết / để link",
                [str(item) for item in agreement.get("shipment_ids") or []] + candidate_ids,
                default=[str(item) for item in agreement.get("shipment_ids") or []],
                key="agr_linked_shipments",
            )
            if st.form_submit_button(
                "Cập nhật liên kết lô",
                type="primary",
                disabled=not has_write_permission("commercial_write"),
            ):
                if not has_write_permission("commercial_write"):
                    st.error("Bạn không có quyền cập nhật liên kết lô. Liên hệ người quản trị.")
                    st.stop()
                agreement["shipment_ids"] = list(dict.fromkeys(str(item) for item in linked if item in shipments))
                if _persist_agreement(agreement):
                    st.success("Đã cập nhật liên kết lô vận chuyển.")
                    st.rerun()

        st.markdown("#### Lịch sử trạng thái")
        st.dataframe(pd.DataFrame(agreement.get("status_history") or []), use_container_width=True, hide_index=True)

    with tabs[5]:
        customers = _customer_store()
        shipment = None
        shipments = _shipment_store()
        for shipment_id in agreement.get("shipment_ids") or []:
            if shipment_id in shipments:
                shipment = shipments[shipment_id]
                break
        quote = _quote_store().get(agreement.get("quote_id"))
        view = commercial_handoff_view(shipment, agreement, quote, customers)
        _render_handoff_view(view, agreement)


def _render_revision_dialog(agreement: dict[str, Any]) -> bool:
    """Start a bounded revision: keep the AGREED document, open a DRAFT revision.

    Returns True when the revision was persisted.
    """
    with st.form("agr_revision"):
        st.caption("Tạo bản nháp sửa đổi. Bản thỏa thuận đã đồng ý được giữ nguyên làm lịch sử.")
        note = st.text_input("Lý do sửa điều khoản", key="agr_revision_reason")
        if st.form_submit_button(
            "Tạo bản sửa đổi (revision draft)",
            type="primary",
            disabled=not has_write_permission("commercial_write"),
        ):
            if not has_write_permission("commercial_write"):
                st.error("Bạn không có quyền sửa điều khoản thỏa thuận. Liên hệ người quản trị.")
                st.stop()
            if not note.strip():
                st.error("Cần ghi rõ lý do sửa điều khoản.")
                return False
            revision = deepcopy(dict(agreement))
            revision["revision_of"] = str(agreement.get("agreement_id"))
            revision["revision_reason"] = note.strip()
            try:
                revised = transition_agreement(agreement, "REVISED", actor=_actor())
            except ValueError as exc:
                st.error(str(exc))
                return False
            if not (_persist_agreement(revised) and _persist_agreement(revision)):
                return False
            st.session_state.agreement_detail_id = str(revision["agreement_id"])
            st.success(f"Đã tạo revision DRAFT {revision.get('agreement_no')}; bản AGREED {agreement.get('agreement_no')} được giữ nguyên.")
            return True
    return False


def _render_handoff_view(view: dict[str, Any], agreement: dict[str, Any]) -> None:
    readiness = view.get("readiness") or {}
    readiness_color = _readiness_badge_color(readiness.get("state", HANDOFF_COMMERCIAL_REVIEW))
    st.markdown(
        f"<div style='background:var(--ops-surface);border:1px solid var(--ops-line);border-radius:8px;"
        f"border-left:6px solid {readiness_color};padding:10px 14px'>"
        f"<b>Sẵn sàng bàn giao vận hành:</b> <span style='color:{readiness_color};font-weight:800'>{readiness.get('label')}</span>"
        + (f"<br>{' · '.join(readiness.get('reasons') or [])}" if readiness.get("reasons") else "")
        + "</div>",
        unsafe_allow_html=True,
    )
    st.subheader("Kiểm tra đủ thông tin cho Support")
    st.caption("Đây là danh mục thông tin Support cần có để vận hành lô hàng (nhà máy, lịch trình, chứng từ, "
               "điều khoản...). Đủ hết các mục thì Support mới có thể làm việc suôn sẻ.")
    df = pd.DataFrame(view.get("questions") or [])
    st.dataframe(df, use_container_width=True, hide_index=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Nhà máy / lô")
        st.dataframe(pd.DataFrame(view.get("factory_lots") or []), use_container_width=True, hide_index=True)
        st.markdown("#### Phạm vi dịch vụ đã bán")
        st.dataframe(pd.DataFrame(view.get("services_sold") or []), use_container_width=True, hide_index=True)
    with c2:
        st.markdown("#### Điều khoản thanh toán (thương mại)")
        payment = view.get("payment_terms") or {}
        st.write({
            "Đã chọn": payment.get("selected") or "Chưa chọn điều khoản",
            "Credit term": f"{payment.get('credit_term_days')} ngày" if payment.get("credit_term_days") else "Không có",
            "Hạn thanh toán": payment.get("due_date_trigger") or "UNKNOWN",
            "Ghi chú": payment.get("notes") or "UNKNOWN",
        })
        st.caption("Điều khoản thanh toán ở đây là cam kết thương mại; KHÔNG phải payment thực tế. Thanh toán thực tế chỉ qua luồng Finance.")
        st.markdown("#### Bằng chứng chấp nhận")
        ev = view.get("evidence") or {}
        st.write({
            "Báo giá được chấp nhận": "CÓ" if ev.get("accepted_quotation") else "Chưa đánh dấu",
            "Hợp đồng ký / đồng ý": "CÓ" if ev.get("signed_contract") else "Chưa đánh dấu",
            "Khách xác nhận": "CÓ" if ev.get("customer_confirmation") else "Chưa đánh dấu",
            "Chứng từ ủy thác": "CÓ" if ev.get("entrusted_documentation") else "Chưa đánh dấu",
            "Ghi chú": ev.get("notes") or "UNKNOWN",
        })
        st.markdown("#### Chứng từ cần thiết")
        st.dataframe(pd.DataFrame(view.get("required_documents") or []), use_container_width=True, hide_index=True)
        if view.get("unresolved_issues"):
            st.warning("Unresolved issue: " + " · ".join(view["unresolved_issues"]))
        if view.get("assumptions"):
            with st.expander("Commercial assumptions cần theo dõi"):
                st.write(view["assumptions"])


def ui_agreements_module() -> None:
    st.title("Thỏa Thuận & Bàn Giao")
    st.caption("Trang này KHÔNG tạo payment, transaction hay event Finance Ledger nào.")
    # LOG-LG04: hành trình 4 bước giải thích bằng tiếng Việt thường (Ý 10)
    st.markdown(
        "<style>"
        ".lg04-journey {{ border: 2px solid #D0D7DE; border-radius: 10px; padding: .6rem .8rem; "
        "margin: .3rem 0 1rem; background: #F6F8FA; }}"
        ".lg04-step {{ display: inline-block; background: #0B6E99; color: #FFFFFF; border-radius: 14px; "
        "padding: .15rem .6rem; font-weight: 800; font-size: .8rem; margin-right: .4rem; }}"
        "</style>"
        "<div class='lg04-journey'>"
        "<div><span class='lg04-step'>1</span><b>Báo giá</b> — Sale lập phương án giá (menu Kinh Doanh &amp; Báo Giá)</div>"
        "<div><span class='lg04-step'>2</span><b>Khách chốt</b> — khách đồng ý báo giá, Sale đánh dấu ACCEPTED</div>"
        "<div><span class='lg04-step'>3</span><b>Thỏa thuận</b> — chốt lại điều khoản thương mại theo báo giá đã chốt</div>"
        "<div><span class='lg04-step'>4</span><b>Bàn giao cho Support</b> — kiểm tra đủ thông tin Support cần để vận hành lô hàng (liên hệ nhà máy, xe, chứng từ, điều khoản...)</div>"
        "<div style='color:#475467;font-size:.82rem;margin-top:.3rem'>Sau bàn giao, Support mở lô hàng và làm việc theo 3 mục: Lấy hàng &amp; Xuất khẩu / Nhập khẩu &amp; Giao hàng / Chi phí &amp; Công nợ.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    agreements = _agreement_store()
    tabs = st.tabs(["Danh sách thỏa thuận", "Tạo từ báo giá khách đã chốt", "Chi tiết &amp; Bàn giao"])
    with tabs[0]:
        _render_agreement_table(agreements)
    with tabs[1]:
        _render_new_agreement()
    with tabs[2]:
        _render_agreement_detail()
