"""Canonical contract workspace.

Contracts own the commercial relationship. Shipments, bank transfers, proxy
payments, and entrustment-wallet rows are linked to a contract here while the
legacy collections remain readable during migration.
"""
from __future__ import annotations

import copy
from datetime import date, datetime
from uuid import uuid4

import pandas as pd
import streamlit as st
from views.lg_core import nav_to_page  # noqa: E402

from core.config import STATUS_MAP_INV
from core.database import (
    load_contract_transactions,
    load_contracts,
    load_data,
    load_entrustments,
    load_proxy_payments,
    save_contract_proxy_payment_atomic,
    save_contract_to_cloud,
    save_contract_transaction,
    save_proxy_payment,
    save_shipment_atomic,
)
from core.auth import can_edit_contract
from views.docgen import _authority_form
from core.logic import calculate_from_shipment
from core.utils import safe_float


def normalize_contract_no(c_no: object) -> str:
    return "".join(str(c_no or "").upper().split()).replace("-", "").strip()


def _contract_id(item: dict) -> str:
    return str(item.get("id") or item.get("contract_no") or "").strip().upper()


def _shipment_contract_ids(shipment: dict) -> set[str]:
    """Read canonical and legacy relationship fields without dropping either."""
    if not isinstance(shipment, dict):
        return set()
    ids: set[str] = set()
    direct = shipment.get("contract_id")
    if direct:
        ids.add(normalize_contract_no(direct))
    for value in shipment.get("contract_ids", []) if isinstance(shipment.get("contract_ids"), list) else []:
        if value:
            ids.add(normalize_contract_no(value))
    data = shipment.get("data") if isinstance(shipment.get("data"), dict) else {}
    entrust = data.get("entrustment", {}) if isinstance(data.get("entrustment"), dict) else {}
    if isinstance(entrust, dict) and entrust.get("active") and entrust.get("contract_no"):
        ids.add(normalize_contract_no(entrust.get("contract_no")))
    if shipment.get("contract_no"):
        ids.add(normalize_contract_no(shipment.get("contract_no")))
    return {value for value in ids if value}


def _shipment_matches_contract(shipment: dict, contract_id: str) -> bool:
    return normalize_contract_no(contract_id) in _shipment_contract_ids(shipment)


def _wallet_summary(wallet: dict) -> tuple[float, float, float]:
    deposits = sum(safe_float(row.get("Số tiền (VND)", 0)) for row in wallet.get("deposits", []) if isinstance(row, dict))
    paid = sum(
        safe_float(row.get("Số Tiền Ngoại Tệ", row.get("Số Tệ (CNY)", 0)))
        * safe_float(row.get("Tỷ giá Báo Khách", 0))
        for row in wallet.get("payments", []) if isinstance(row, dict)
    )
    return deposits, paid, deposits - paid


def _contract_transaction_rows(contract_id: str, item: dict, proxy_db: dict, entrust_db: dict) -> list[dict]:
    """Return canonical rows plus read-only projections of legacy records."""
    rows: list[dict] = []
    seen: set[str] = set()
    for tx_id, tx in load_contract_transactions(contract_id).items():
        row = dict(tx)
        row.setdefault("id", tx_id)
        row.setdefault("source", "contract_transactions")
        rows.append(row)
        seen.add(str(row["id"]))

    details = item.get("details", {}) if isinstance(item.get("details"), dict) else {}
    for index, tx in enumerate(details.get("transactions", []) if isinstance(details.get("transactions"), list) else []):
        legacy_id = str(tx.get("id") or f"LEGACY-BANK-{contract_id}-{index}")
        if legacy_id in seen:
            continue
        rows.append({
            "id": legacy_id,
            "transaction_type": "bank_transfer",
            "date": tx.get("date"),
            "amount": safe_float(tx.get("amount", 0)),
            "currency": tx.get("currency", item.get("currency", "USD")),
            "note": tx.get("note", ""),
            "status": "legacy",
            "source": "contract.details.transactions",
        })
        seen.add(legacy_id)

    normalized_id = normalize_contract_no(contract_id)
    for payment_id, payment in proxy_db.items():
        if not isinstance(payment, dict):
            continue
        linked = payment.get("contract_id") or payment.get("linked_id")
        linked_type = payment.get("linked_type")
        if normalize_contract_no(linked) != normalized_id or (linked_type and linked_type not in {"Hợp Đồng", "contract"} and not payment.get("contract_id")):
            continue
        legacy_id = str(payment.get("id") or payment_id)
        if legacy_id in seen:
            continue
        rows.append({
            "id": legacy_id,
            "transaction_type": "proxy_payment",
            "date": payment.get("date"),
            "amount_vnd": safe_float(payment.get("amount_vnd", 0)),
            "amount_fc_needed": safe_float(payment.get("amount_fc_needed", 0)),
            "amount_fc_paid": safe_float(payment.get("amount_fc_paid", 0)),
            "amount_fc_remain": safe_float(payment.get("amount_fc_remain", 0)),
            "currency": payment.get("currency", ""),
            "beneficiary": payment.get("beneficiary", ""),
            "note": payment.get("note", ""),
            "status": payment.get("status", "legacy"),
            "source": "proxy_payments",
        })
        seen.add(legacy_id)

    for wallet_id, wallet in entrust_db.items():
        if not isinstance(wallet, dict):
            continue
        linked = wallet.get("contract_id") or wallet.get("linked_id")
        linked_type = wallet.get("linked_type")
        if normalize_contract_no(linked) != normalized_id or (linked_type and linked_type != "Hợp Đồng" and not wallet.get("contract_id")):
            continue
        deposited, paid, balance = _wallet_summary(wallet)
        legacy_id = f"{wallet_id}"
        if legacy_id in seen:
            continue
        rows.append({
            "id": legacy_id,
            "transaction_type": "entrustment_wallet",
            "date": wallet.get("updated_at"),
            "wallet_code": wallet_id,
            "amount_vnd": deposited,
            "amount_paid_vnd": paid,
            "balance_vnd": balance,
            "status": "legacy",
            "source": "entrustments",
        })
        seen.add(legacy_id)
    return rows


def _tx_dataframe(rows: list[dict]) -> pd.DataFrame:
    display = []
    labels = {
        "bank_transfer": "Thanh toán ngân hàng",
        "proxy_payment": "Thanh toán hộ",
        "entrustment_wallet": "Ví ký quỹ",
    }
    for row in rows:
        display.append({
            "Loại": labels.get(row.get("transaction_type"), row.get("transaction_type", "Khác")),
            "Ngày": row.get("date", ""),
            "Mã GD / Ví": row.get("id", ""),
            "Ngoại tệ": row.get("currency", ""),
            "Số tiền": safe_float(row.get("amount", row.get("amount_fc_paid", 0))),
            "VNĐ nhận / nạp": safe_float(row.get("amount_vnd", 0)),
            "Còn lại": safe_float(row.get("amount_fc_remain", row.get("balance_vnd", 0))),
            "Trạng thái": row.get("status", ""),
            "Nguồn": row.get("source", ""),
        })
    return pd.DataFrame(display)


def _save_contract_and_refresh(item: dict, contracts_db: dict) -> bool:
    contract_id = _contract_id(item)
    contracts_db[contract_id] = item
    ok = save_contract_to_cloud(item)
    if ok:
        st.session_state.db_contracts = contracts_db
    return ok


def _render_shipment_links(contract_id: str, shipments_db: dict) -> list[dict]:
    linked = [sid for sid, shipment in shipments_db.items() if _shipment_matches_contract(shipment, contract_id)]
    options = list(shipments_db.keys())
    selected = st.multiselect(
        "Các lô hàng dùng chung hợp đồng này",
        options,
        default=[sid for sid in linked if sid in options],
        key=f"contract_shipments_{contract_id}",
        help="Một hợp đồng có thể gắn nhiều lô hàng. Liên kết trực tiếp được lưu ở contract_id; dữ liệu entrustment cũ vẫn được đọc.",
    )
    if st.button("💾 Lưu liên kết lô hàng", key=f"save_contract_shipments_{contract_id}", type="primary", disabled=not can_edit_contract()):
        if not can_edit_contract():
            st.warning("Bạn không có quyền sửa hợp đồng.")
        failures = []
        for sid, shipment in shipments_db.items():
            should_link = sid in selected
            current = normalize_contract_no(shipment.get("contract_id", ""))
            target = normalize_contract_no(contract_id)
            if should_link and current != target:
                before = copy.deepcopy(shipment)
                shipment["contract_id"] = contract_id
                if not save_shipment_atomic(shipment, expected_version=shipment.get("version")):
                    shipments_db[sid] = before
                    failures.append(sid)
            elif not should_link and current == target:
                before = copy.deepcopy(shipment)
                shipment.pop("contract_id", None)
                if not save_shipment_atomic(shipment, expected_version=shipment.get("version")):
                    shipments_db[sid] = before
                    failures.append(sid)
        if failures:
            st.error(f"Không lưu được liên kết ở: {', '.join(failures)}")
        else:
            st.success("Đã cập nhật liên kết hợp đồng – lô hàng.")
            st.session_state.needs_refresh = True
            st.rerun()

    if linked:
        rows = []
        for sid in linked:
            shipment = shipments_db[sid]
            docs = shipment.get("data", {}).get("1.2", {})
            summary = calculate_from_shipment(shipment)
            rows.append({
                "Mã lô hàng": sid,
                "ETD": docs.get("etd", "-"),
                "MBL": docs.get("mbl", "-"),
                "Doanh thu trước VAT": safe_float(summary.get("revenue_net", 0)),
                "Lợi nhuận": safe_float(summary.get("profit", 0)),
                "Trạng thái": STATUS_MAP_INV.get(shipment.get("status", "wait"), "Chờ xử lý"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có lô hàng nào được gắn trực tiếp. Các liên kết entrustment cũ sẽ được hiển thị nếu còn tồn tại.")
    return [shipments_db[sid] for sid in linked]


def _render_contract_finance(item: dict, contracts_db: dict, proxy_db: dict, entrust_db: dict) -> None:
    contract_id = _contract_id(item)
    rows = _contract_transaction_rows(contract_id, item, proxy_db, entrust_db)
    st.caption("Đây là sổ giao dịch của hợp đồng. Thu tiền & Công nợ vẫn là sổ phân bổ công nợ theo khách hàng, không bị ghi đè bởi các dòng dưới đây.")
    if rows:
        st.dataframe(_tx_dataframe(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có dòng thanh toán nào trong hợp đồng.")

    bank_tab, proxy_tab, wallet_tab = st.tabs(["🏦 Thanh toán ngân hàng", "💸 Thanh toán hộ", "👛 Ví ký quỹ"])
    with bank_tab:
        with st.form(f"contract_bank_form_{contract_id}"):
            c1, c2, c3 = st.columns(3)
            bank_date = c1.date_input("Ngày chuyển tiền", date.today())
            bank_amount = c2.number_input("Số tiền ngoại tệ", min_value=0.0, step=100.0, format="%.2f")
            bank_currency = c3.selectbox("Loại tiền", ["USD", "EUR", "CNY", "VND"])
            bank_note = st.text_input("Số lệnh chi / ghi chú ngân hàng")
            if st.form_submit_button("➕ Ghi nhận chuyển khoản", disabled=not can_edit_contract()):
                if not can_edit_contract():
                    st.warning("Bạn không có quyền sửa hợp đồng.")
                if bank_amount <= 0:
                    st.error("Số tiền phải lớn hơn 0.")
                else:
                    tx_id = f"BANK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:5].upper()}"
                    tx = {"id": tx_id, "contract_id": contract_id, "transaction_type": "bank_transfer", "date": str(bank_date), "amount": bank_amount, "currency": bank_currency, "note": bank_note.strip(), "status": "recorded"}
                    if save_contract_transaction(tx):
                        details = item.setdefault("details", {})
                        details.setdefault("transactions", []).append({"id": tx_id, "date": str(bank_date), "amount": bank_amount, "currency": bank_currency, "note": bank_note.strip(), "type": "Chi"})
                        _save_contract_and_refresh(item, contracts_db)
                        st.success("Đã ghi nhận thanh toán ngân hàng.")
                        st.rerun()
                    else:
                        st.error("Không lưu được giao dịch hợp đồng.")

    with proxy_tab:
        with st.form(f"contract_proxy_form_{contract_id}"):
            c1, c2, c3 = st.columns(3)
            proxy_date = c1.date_input("Ngày nhận tiền", date.today())
            proxy_customer = c2.text_input("Người gửi / khách hàng")
            proxy_vnd = c3.number_input("VNĐ đã nhận", min_value=0.0, step=100000.0, format="%.0f")
            c4, c5, c6 = st.columns(3)
            proxy_rate = c4.number_input("Tỷ giá", min_value=0.0, step=1.0, format="%.0f")
            proxy_currency = c5.selectbox("Ngoại tệ", ["CNY (¥)", "USD ($)", "EUR (€)"])
            proxy_needed = c6.number_input("Ngoại tệ cần chuyển", min_value=0.0, step=100.0, format="%.2f")
            proxy_paid = st.number_input("Ngoại tệ đã chuyển", min_value=0.0, step=100.0, format="%.2f")
            proxy_beneficiary = st.text_input("Nhà máy / đại lý thụ hưởng")
            proxy_note = st.text_input("Ghi chú thanh toán hộ")
            if st.form_submit_button("➕ Ghi nhận thanh toán hộ", disabled=not can_edit_contract()):
                if not can_edit_contract():
                    st.warning("Bạn không có quyền sửa hợp đồng.")
                if not proxy_customer.strip() or proxy_vnd <= 0:
                    st.error("Cần người gửi và số VNĐ đã nhận.")
                else:
                    payment_id = f"PX-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:5].upper()}"
                    remain = proxy_needed - proxy_paid
                    payment = {"id": payment_id, "date": str(proxy_date), "customer": proxy_customer.strip(), "amount_vnd": proxy_vnd, "exchange_rate": proxy_rate, "currency": proxy_currency, "amount_fc_needed": proxy_needed, "amount_fc_paid": proxy_paid, "amount_fc_remain": remain, "beneficiary": proxy_beneficiary.strip(), "status": "✅ Đã tất toán xong" if remain <= 0 and proxy_needed > 0 else "⏳ Đang xử lý / Chờ chuyển thêm", "linked_type": "Hợp Đồng", "linked_id": contract_id, "contract_id": contract_id, "note": proxy_note.strip()}
                    tx = {"id": payment_id, "contract_id": contract_id, "transaction_type": "proxy_payment", "date": str(proxy_date), "amount_vnd": proxy_vnd, "amount_fc_needed": proxy_needed, "amount_fc_paid": proxy_paid, "amount_fc_remain": remain, "currency": proxy_currency, "beneficiary": proxy_beneficiary.strip(), "status": payment["status"], "note": proxy_note.strip(), "source_id": payment_id}
                    if save_contract_proxy_payment_atomic(payment, tx):
                        proxy_db[payment_id] = payment
                        st.session_state.db_proxy = proxy_db
                        st.success("Đã ghi nhận thanh toán hộ trong hợp đồng.")
                        st.rerun()
                    else:
                        st.error("Không lưu được giao dịch thanh toán hộ.")

    with wallet_tab:
        st.markdown("Ví ký quỹ được hiển thị chung ở đây; dữ liệu ví cũ vẫn được đọc từ kho entrustments.")
        with st.form(f"contract_wallet_form_{contract_id}"):
            c1, c2, c3 = st.columns(3)
            wallet_code = c1.text_input("Mã ví / mã đặt cọc")
            wallet_date = c2.date_input("Ngày nạp", date.today())
            wallet_amount = c3.number_input("Số tiền ký quỹ (VNĐ)", min_value=0.0, step=100000.0, format="%.0f")
            wallet_note = st.text_input("Ghi chú ví ký quỹ")
            if st.form_submit_button("➕ Ghi nhận nạp ví", disabled=not can_edit_contract()):
                if not can_edit_contract():
                    st.warning("Bạn không có quyền sửa hợp đồng.")
                if wallet_amount <= 0:
                    st.error("Số tiền ký quỹ phải lớn hơn 0.")
                else:
                    tx_id = f"WALLET-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:5].upper()}"
                    tx = {"id": tx_id, "contract_id": contract_id, "transaction_type": "entrustment_wallet", "date": str(wallet_date), "wallet_code": wallet_code.strip(), "amount_vnd": wallet_amount, "balance_vnd": wallet_amount, "status": "recorded", "note": wallet_note.strip()}
                    if save_contract_transaction(tx):
                        st.success("Đã ghi nhận nạp ví ký quỹ trong hợp đồng.")
                        st.rerun()
                    else:
                        st.error("Không lưu được dòng ví ký quỹ.")


def _authority_field_form(record: dict[str, Any] | None, kind: str, key_suffix: str) -> None:
    """✏️ Bổ sung thông tin — edits the EXISTING authority master record."""
    from core.database import save_authority_agent, save_authority_company

    is_agent = kind == "agent"
    label = "Đại lý" if is_agent else "Công ty"
    fields = (
        ("legal_name", "Tên pháp lý"),
        ("legal_address", "Địa chỉ"),
        ("legal_code" if is_agent else "tax_or_legal_code", "MST / mã pháp lý"),
        ("legal_representative", "Người đại diện"),
        ("representative_title", "Chức vụ"),
    )
    bank_fields = (
        ("bank_account_holder", "Chủ tài khoản"),
        ("bank_account_number", "Số tài khoản"),
        ("bank_name", "Ngân hàng"),
    ) if is_agent else ()

    values: dict[str, str] = {}
    with st.form(f"auth_edit_{kind}_{key_suffix}"):
        for field, text in fields:
            values[field] = st.text_input(text, value=str((record or {}).get(field) or ""), key=f"ae_{kind}_{key_suffix}_{field}")
        for field, text in bank_fields:
            values[field] = st.text_input(text, value=str((record or {}).get(field) or ""), key=f"ae_{kind}_{key_suffix}_{field}")
        if st.form_submit_button(f"💾 Lưu hồ sơ {label}", type="primary"):
            payload = dict(record or {})
            payload.update(values)
            ok = save_authority_agent(payload) if is_agent else save_authority_company(payload)
            if ok:
                st.success(f"Đã lưu hồ sơ {label} (nguồn gốc, không lưu bản sao trong hợp đồng).")
                st.rerun()
            else:
                st.error(f"Không lưu được hồ sơ {label}.")


def _render_contract_parties(contract_id: str, item: dict[str, Any], contracts_db: dict) -> None:
    """Tab 1 — BÊN MUA / BÊN BÁN read from the existing authority master."""
    from core.database import load_authority_agents, load_authority_companies

    companies = load_authority_companies()
    agents = load_authority_agents()
    company_keys = list(companies.keys())
    agent_keys = list(agents.keys())

    left, right = st.columns(2)
    with left:
        st.markdown("#### 🏢 BÊN MUA (Công ty)")
        if company_keys:
            index = company_keys.index(item["company_id"]) if item.get("company_id") in company_keys else 0
            company_id = st.selectbox(
                "Công ty", company_keys, index=index,
                format_func=lambda k: companies.get(k, {}).get("legal_name", k),
                key=f"contract_company_{contract_id}",
            )
        else:
            company_id = None
            st.info("Chưa có hồ sơ pháp lý Công ty.")
    with right:
        st.markdown("#### 🤝 BÊN BÁN (Đại lý)")
        if agent_keys:
            index = agent_keys.index(item["agent_id"]) if item.get("agent_id") in agent_keys else 0
            agent_id = st.selectbox(
                "Đại lý", agent_keys, index=index,
                format_func=lambda k: agents.get(k, {}).get("legal_name", k),
                key=f"contract_agent_{contract_id}",
            )
        else:
            agent_id = None
            st.info("Chưa có hồ sơ pháp lý Đại lý.")

    changed = False
    if company_id and item.get("company_id") != company_id:
        item["company_id"] = company_id
        changed = True
    if agent_id and item.get("agent_id") != agent_id:
        item["agent_id"] = agent_id
        changed = True
    if changed:
        _save_contract_and_refresh(item, contracts_db)

    company = companies.get(company_id) if company_id else None
    agent = agents.get(agent_id) if agent_id else None

    from views.docgen import _authority_summary_card, _missing_authority_fields

    _authority_summary_card(company, agent)

    missing = _missing_authority_fields(agent, company)
    if missing:
        st.warning("Thiếu thông tin pháp lý: " + " ".join(missing))
    if company is None and not company_keys:
        _authority_form("company", key_suffix=f"ct_{contract_id}")
    if agent is None and not agent_keys:
        _authority_form("agent", key_suffix=f"ct_{contract_id}")

    edit_col1, edit_col2 = st.columns(2)
    with edit_col1:
        with st.expander("✏️ Bổ sung thông tin BÊN MUA", expanded=False):
            if company is None:
                st.caption("Chưa chọn Công ty.")
            else:
                _authority_field_form(company, "company", f"buyer_{contract_id}")
    with edit_col2:
        with st.expander("✏️ Bổ sung thông tin BÊN BÁN", expanded=False):
            if agent is None:
                st.caption("Chưa chọn Đại lý.")
            else:
                _authority_field_form(agent, "agent", f"seller_{contract_id}")


def _contract_document_summary(contract_id: str) -> None:
    """Tab 5 — concise generated-document history for this contract."""
    from core.database import load_docgen_documents

    docs = load_docgen_documents(contract_id)
    if not docs:
        st.info("Chưa có chứng từ nào được xuất cho hợp đồng này.")
        return
    rows = [
        {
            "Loại": d.get("document_type"),
            "Số": d.get("document_id"),
            "Ngày": str(d.get("generated_at") or "")[:10],
            "Revision": d.get("generation_revision") or d.get("revision") or 1,
            "Trạng thái": d.get("status"),
            "Người tạo": d.get("generated_by") or "—",
            "File": d.get("output_file_name"),
        }
        for d in docs.values()
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _contract_card(item: dict, contracts_db: dict, linked_count: int) -> None:
    """One concise, beginner-friendly contract row."""
    contract_id = _contract_id(item)
    with st.container(border=True):
        info, action = st.columns([5, 1])
        with info:
            st.markdown(f"**{item.get('contract_no') or contract_id}** · {item.get('kind') or item.get('type') or '—'}")
            st.caption(f"Đại lý: {item.get('agent_id') or '—'} · Công ty: {item.get('company_id') or '—'}")
            st.caption(
                f"Giá trị: {safe_float(item.get('value', 0)):,.0f} {item.get('currency', 'VND')}"
                f" · Hiệu lực: {str(item.get('date') or '—')}"
                f" · Lô liên kết: {linked_count}"
                f" · Trạng thái: {item.get('status') or 'Đang xử lý'}"
            )
        with action:
            if st.button("MỞ HỢP ĐỒNG", key=f"open_contract_{contract_id}", type="primary", use_container_width=True):
                st.session_state.selected_contract_v2 = contract_id
                st.rerun()


def ui_contracts_management() -> None:
    """📜 HỢP ĐỒNG — the contract work desk (contract-centric owner workflow)."""
    st.title("📜 HỢP ĐỒNG")
    st.caption(
        "Hợp đồng là nơi làm việc chính: thông tin pháp lý hai bên, hàng hóa, "
        "chứng từ HDNT / PL / HDMB và tải file. Phiếu xuất kho (PXK) vẫn thuộc lô hàng."
    )

    if "db_contracts" not in st.session_state:
        st.session_state.db_contracts = load_contracts()
    if "db_shipments" not in st.session_state:
        st.session_state.db_shipments = load_data()
    if "db_proxy" not in st.session_state:
        st.session_state.db_proxy = load_proxy_payments()
    if "db_entrustments" not in st.session_state:
        st.session_state.db_entrustments = load_entrustments()

    contracts_db = st.session_state.db_contracts
    shipments_db = st.session_state.db_shipments
    proxy_db = st.session_state.db_proxy
    entrust_db = st.session_state.db_entrustments

    # ------------------------------------------------------------------
    # A. DANH SÁCH HỢP ĐỒNG
    # ------------------------------------------------------------------
    st.markdown("## 📋 DANH SÁCH HỢP ĐỒNG")

    if st.button("➕ TẠO HỢP ĐỒNG MỚI", type="primary", key="toggle_new_contract"):
        st.session_state.show_new_contract = not st.session_state.get("show_new_contract", False)
        st.rerun()

    if st.session_state.get("show_new_contract") or not contracts_db:
        with st.form("new_contract_form_v2"):
            c1, c2, c3 = st.columns(3)
            new_no = c1.text_input("Số hợp đồng")
            new_date = c2.date_input("Ngày ký", date.today())
            new_client = c3.text_input("Đối tác / nhà nhập khẩu")
            c4, c5, c6 = st.columns(3)
            new_value = c4.number_input("Tổng giá trị", min_value=0.0, step=1000.0, format="%.2f")
            new_currency = c5.selectbox("Loại tiền", ["VND", "USD", "EUR", "CNY"])
            new_note = c6.text_input("Điều khoản / ghi chú")
            if st.form_submit_button("🚀 Lưu hợp đồng", type="primary", disabled=not can_edit_contract()):
                if not can_edit_contract():
                    st.warning("Bạn không có quyền sửa hợp đồng.")
                else:
                    contract_id = new_no.strip().upper()
                    if not contract_id or not new_client.strip():
                        st.error("Cần số hợp đồng và đối tác.")
                    elif any(normalize_contract_no(existing) == normalize_contract_no(contract_id) for existing in contracts_db):
                        st.error("Số hợp đồng này đã tồn tại.")
                    else:
                        item = {
                            "id": contract_id, "contract_no": contract_id, "normalized_no": normalize_contract_no(contract_id),
                            "date": str(new_date), "client": new_client.strip(), "value": new_value, "currency": new_currency,
                            "note": new_note.strip(), "details": {"transactions": []}, "linked_shipment_ids": [],
                        }
                        if _save_contract_and_refresh(item, contracts_db):
                            st.session_state.selected_contract_v2 = contract_id
                            st.session_state.show_new_contract = False
                            st.success(f"Đã tạo hợp đồng {contract_id}.")
                            st.rerun()
                        else:
                            st.error("Không lưu được hợp đồng.")

    search = st.text_input("🔍 Tìm hợp đồng (số hợp đồng, đối tác, đại lý)", key="contract_search_box")
    needle = str(search or "").strip().upper()

    if not contracts_db:
        st.info("Hiện tại chưa có hợp đồng nào.")
        return

    def _matches(item: dict) -> bool:
        if not needle:
            return True
        haystack = " ".join(
            str(item.get(field) or "") for field in ("id", "contract_no", "client", "agent_id", "company_id", "note", "kind", "type")
        ).upper()
        return needle in haystack

    visible = [item for item in contracts_db.values() if _matches(item)]
    if not visible:
        st.info("Không tìm thấy hợp đồng phù hợp.")

    for item in visible:
        contract_id = _contract_id(item)
        linked_count = sum(1 for shipment in shipments_db.values() if _shipment_matches_contract(shipment, contract_id))
        _contract_card(item, contracts_db, linked_count)

    st.divider()

    # ------------------------------------------------------------------
    # B. CONTRACT DETAIL
    # ------------------------------------------------------------------
    contract_options = list(contracts_db.keys())
    default_id = st.session_state.get("selected_contract_v2")
    index = contract_options.index(default_id) if default_id in contract_options else 0
    selected_id = st.selectbox("Chọn hợp đồng để mở", contract_options, index=index, key="selected_contract_v2")
    item = contracts_db[selected_id]
    contract_id = _contract_id(item)
    st.markdown(f"## 📂 HỢP ĐỒNG {item.get('contract_no') or contract_id} · {item.get('client', '')}")

    info_tab, goods_tab, shipment_tab, finance_tab, terms_tab = st.tabs(
        ["📋 THÔNG TIN HỢP ĐỒNG", "🧾 HÀNG HÓA & CHỨNG TỪ", "🚢 LÔ HÀNG LIÊN KẾT", "💰 TÀI CHÍNH HỢP ĐỒNG", "⚙️ PHỤ LỤC / LỊCH SỬ"]
    )

    with info_tab:
        _render_contract_parties(contract_id, item, contracts_db)

    with goods_tab:
        from views.docgen import ui_contract_document_pack

        ui_contract_document_pack(contract_id, item)

    with shipment_tab:
        linked = _render_shipment_links(contract_id, shipments_db)
        for shipment in linked:
            sid = str(shipment.get("id") or shipment.get("shipment_id") or "")
            if not sid:
                continue
            with st.container(border=True):
                left, mid, right = st.columns([3, 1.4, 1.6])
                left.markdown(f"**{sid}**")
                left.caption(f"Khách hàng: {shipment.get('customer') or shipment.get('client') or '—'} · Trạng thái: {STATUS_MAP_INV.get(shipment.get('status', 'wait'), 'Chờ xử lý')}")
                if mid.button("🚢 MỞ LÔ HÀNG", key=f"contract_open_shipment_{sid}", use_container_width=True):
                    st.session_state.dashboard_active_shipment_id = sid
                    st.session_state.active_shipment_section = "export"
                    nav_to_page("Tổng Quan Công Việc")
                    st.rerun()
                if right.button("📦 LÀM PHIẾU XUẤT KHO", key=f"contract_pxk_{sid}", use_container_width=True):
                    st.session_state.dashboard_active_shipment_id = sid
                    st.session_state.active_shipment_section = "documents"
                    nav_to_page("Tổng Quan Công Việc")
                    st.rerun()

    with finance_tab:
        _render_contract_finance(item, contracts_db, proxy_db, entrust_db)

    with terms_tab:
        new_value = st.number_input("Điều chỉnh giá trị theo phụ lục", value=safe_float(item.get("value", 0)), key=f"contract_value_{contract_id}")
        new_note = st.text_area("Ghi chú / điều khoản", value=item.get("note", ""), key=f"contract_note_{contract_id}")
        if st.button("💾 Cập nhật phụ lục", key=f"save_contract_terms_{contract_id}", disabled=not can_edit_contract()):
            if not can_edit_contract():
                st.warning("Bạn không có quyền sửa hợp đồng.")
            item["value"] = new_value
            item["note"] = new_note.strip()
            if _save_contract_and_refresh(item, contracts_db):
                st.success("Đã cập nhật phụ lục hợp đồng.")
                st.rerun()
        st.divider()
        st.markdown("#### 🕒 LỊCH SỬ CHỨNG TỪ")
        _contract_document_summary(contract_id)
