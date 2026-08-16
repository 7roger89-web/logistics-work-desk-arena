"""LOG-C12 commercial quotation workspace.

The UI uses the existing customer/service/shipment writers and keeps all quote
numbers as estimates. It never posts a finance ledger entry.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import streamlit as st

from core.config import GETFLY_SERVICES_LIST
from core.database import (
    generate_shipment_id,
    load_customers,
    load_quotes,
    save_quotes_to_cloud,
    save_shipment_atomic,
)
from core.quotations import (
    QUOTE_STATUSES,
    build_shipment_draft,
    calculate_quote,
    new_quote_document,
    prepare_quote_for_persistence,
    transition_quote,
)
from core.validators import validate_shipment
from views.sales import ui_sales_module as ui_legacy_sales_module


def _quote_store() -> dict[str, dict[str, Any]]:
    if "db_quotes" not in st.session_state:
        st.session_state.db_quotes = load_quotes()
    return st.session_state.db_quotes


def _customer_store() -> dict[str, dict[str, Any]]:
    if "db_customers" not in st.session_state:
        st.session_state.db_customers = load_customers()
    return st.session_state.db_customers


def _persist_quote(quote: dict[str, Any]) -> bool:
    actor = str(st.session_state.get("current_user", {}).get("username") or "SALE")
    try:
        stamped = prepare_quote_for_persistence(quote, actor=actor)
    except ValueError as exc:
        st.error(str(exc))
        return False
    ok = save_quotes_to_cloud({str(stamped["id"]): stamped})
    if ok:
        _quote_store()[str(stamped["id"])] = stamped
        st.session_state.quote_detail_id = str(stamped["id"])
        st.session_state.needs_refresh = True
    return ok


def _service_options() -> tuple[list[str], dict[str, dict[str, Any]]]:
    mapping = {str(item.get("code")): item for item in GETFLY_SERVICES_LIST if item.get("code")}
    return list(mapping), mapping


def _render_quote_table(quotes: dict[str, dict[str, Any]]) -> None:
    st.subheader("BÃ¡o giÃ¡ Ä‘ang theo dÃµi")
    c1, c2, c3 = st.columns(3)
    search = c1.text_input("KhÃ¡ch hÃ ng / mÃ£ bÃ¡o giÃ¡", key="quote_search")
    status = c2.selectbox("Tráº¡ng thÃ¡i", ["Táº¥t cáº£", *QUOTE_STATUSES], key="quote_status_filter")
    owner = c3.text_input("SALE phá»¥ trÃ¡ch", key="quote_owner_filter")
    rows = []
    for quote in quotes.values():
        haystack = " ".join(str(quote.get(k, "")) for k in ("quote_no", "customer_name", "factory_name"))
        if search.strip().lower() not in haystack.lower():
            continue
        if status != "Táº¥t cáº£" and quote.get("status") != status:
            continue
        if owner.strip().lower() not in str(quote.get("sales_owner", "")).lower():
            continue
        calc = quote.get("calculation", {})
        rows.append({
            "MÃ£ bÃ¡o giÃ¡": quote.get("quote_no", quote.get("id", "")),
            "KhÃ¡ch hÃ ng": quote.get("customer_name", ""),
            "Tuyáº¿n": f"{quote.get('origin', '')} â†’ {quote.get('destination', '')}",
            "Tráº¡ng thÃ¡i": quote.get("status", "DRAFT"),
            "GiÃ¡ bÃ¡o khÃ¡ch (VND)": calc.get("selling_price_total_vnd", 0),
            "Lá»£i nhuáº­n dá»± kiáº¿n (VND)": calc.get("estimated_margin_vnd", 0),
            "LiÃªn káº¿t lÃ´": quote.get("shipment_id", "ChÆ°a táº¡o"),
            "id": quote.get("id", ""),
        })
    if not rows:
        st.info("ChÆ°a cÃ³ bÃ¡o giÃ¡ phÃ¹ há»£p. HÃ£y táº¡o má»™t bÃ¡o giÃ¡ má»›i tá»« thÃ´ng tin Logistics thá»±c táº¿.")
        return
    rows.sort(key=lambda item: item["MÃ£ bÃ¡o giÃ¡"], reverse=True)
    df = pd.DataFrame(rows)
    st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)
    selected = st.selectbox("Má»Ÿ bÃ¡o giÃ¡", [row["id"] for row in rows], format_func=lambda qid: next(row["MÃ£ bÃ¡o giÃ¡"] for row in rows if row["id"] == qid), key="quote_open_id")
    if st.button("Má»Ÿ chi tiáº¿t bÃ¡o giÃ¡", type="primary", key="quote_open_button"):
        st.session_state.quote_detail_id = selected
        st.rerun()


def _render_new_quote() -> None:
    st.subheader("Tiáº¿p nháº­n nhu cáº§u bÃ¡o giÃ¡")
    customers = _customer_store()
    customer_ids = list(customers)
    if not customer_ids:
        st.warning("ChÆ°a cÃ³ khÃ¡ch hÃ ng trong Customer 360. HÃ£y táº¡o khÃ¡ch hÃ ng trÆ°á»›c khi bÃ¡o giÃ¡.")
        return
    c1, c2, c3 = st.columns(3)
    customer_id = c1.selectbox("KhÃ¡ch hÃ ng *", customer_ids, format_func=lambda cid: f"{customers[cid].get('name', cid)} ({cid})", key="new_quote_customer")
    sales_owner = c2.text_input("SALE phá»¥ trÃ¡ch *", value="ThÃ nh", key="new_quote_owner")
    incoterm = c3.selectbox("Incoterm *", ["EXW", "FOB", "CIF", "DDP", "KhÃ¡c"], key="new_quote_incoterm")
    c1, c2, c3 = st.columns(3)
    origin = c1.text_input("Äiá»ƒm Ä‘i / nÆ¡i láº¥y hÃ ng *", value="Trung Quá»‘c", key="new_quote_origin")
    destination = c2.text_input("Äiá»ƒm Ä‘áº¿n *", value="Viá»‡t Nam", key="new_quote_destination")
    route = c3.text_input("BiÃªn giá»›i / tuyáº¿n", value="Há»¯u Nghá»‹", key="new_quote_route")
    c1, c2, c3 = st.columns(3)
    transport_mode = c1.selectbox("PhÆ°Æ¡ng thá»©c", ["Road", "Sea", "Air", "Multimodal"], key="new_quote_mode")
    goods_description = c2.text_input("MÃ´ táº£ hÃ ng hÃ³a *", key="new_quote_goods")
    expected_delivery_date = c3.date_input("NgÃ y khÃ¡ch cáº§n giao", value=date.today(), key="new_quote_delivery")

    st.markdown("#### NhÃ  mÃ¡y / lÃ´ hÃ ng")
    lot_count = st.number_input("Sá»‘ nhÃ  mÃ¡y/lÃ´", min_value=1, max_value=10, value=1, step=1, key="new_quote_lot_count")
    factory_lots: list[dict[str, Any]] = []
    for index in range(int(lot_count)):
        with st.expander(f"LÃ´ {index + 1}", expanded=True):
            a, b, c = st.columns(3)
            factory_name = a.text_input("NhÃ  mÃ¡y / nhÃ  cung cáº¥p", key=f"quote_lot_{index}_name")
            factory_contact = b.text_input("NgÆ°á»i liÃªn há»‡", key=f"quote_lot_{index}_contact")
            factory_phone = c.text_input("Äiá»‡n thoáº¡i", key=f"quote_lot_{index}_phone")
            a, b, c, d = st.columns(4)
            ready_date = a.date_input("NgÃ y sáºµn hÃ ng", value=date.today(), key=f"quote_lot_{index}_ready")
            packages = b.number_input("Sá»‘ kiá»‡n", min_value=0.0, value=0.0, key=f"quote_lot_{index}_packages")
            cbm = c.number_input("CBM", min_value=0.0, value=0.0, format="%.3f", key=f"quote_lot_{index}_cbm")
            gross_weight = d.number_input("Gross weight (kg)", min_value=0.0, value=0.0, key=f"quote_lot_{index}_weight")
            pickup_address = st.text_input("Äá»‹a chá»‰ láº¥y hÃ ng", key=f"quote_lot_{index}_pickup")
            factory_lots.append({"lot_no": index + 1, "factory_name": factory_name, "factory_contact": factory_contact, "factory_phone": factory_phone, "ready_date": str(ready_date), "packages": packages, "cbm": cbm, "gross_weight_kg": gross_weight, "pickup_address": pickup_address})

    st.markdown("#### Dá»‹ch vá»¥ vÃ  phÆ°Æ¡ng Ã¡n giÃ¡")
    service_codes, service_map = _service_options()
    line_count = st.number_input("Sá»‘ dÃ²ng dá»‹ch vá»¥", min_value=1, max_value=20, value=3, step=1, key="new_quote_line_count")
    service_lines: list[dict[str, Any]] = []
    for index in range(int(line_count)):
        a, b, c, d, e, f = st.columns([2.4, 1, 1.2, 1.2, 1.2, 1])
        code = a.selectbox("Dá»‹ch vá»¥", service_codes, format_func=lambda code: f"{code} Â· {service_map[code].get('name', code)}", key=f"quote_line_{index}_code")
        currency = b.selectbox("Tiá»n tá»‡", ["VND", "USD", "CNY"], key=f"quote_line_{index}_currency")
        qty = c.number_input("SL / basis", min_value=0.0, value=1.0, key=f"quote_line_{index}_qty")
        cost_unit = d.number_input("Chi phÃ­ dá»± kiáº¿n", min_value=0.0, value=0.0, key=f"quote_line_{index}_cost")
        sell_unit = e.number_input("GiÃ¡ bÃ¡o khÃ¡ch", min_value=0.0, value=0.0, key=f"quote_line_{index}_sell")
        tax_pct = f.number_input("Thuáº¿ %", min_value=0.0, max_value=100.0, value=0.0, key=f"quote_line_{index}_tax")
        service_lines.append({"code": code, "service_name": service_map[code].get("name", code), "unit": service_map[code].get("unit", "Láº§n"), "qty": qty, "currency": currency, "cost_unit": cost_unit, "sell_unit": sell_unit, "tax_pct": tax_pct, "cost_source": "Nháº­p bá»Ÿi SALE/Support; cáº§n Ä‘á»‘i chiáº¿u agent náº¿u lÃ  phÃ­ Trung Quá»‘c."})

    st.markdown("#### Tá»· giÃ¡ dÃ¹ng Ä‘á»ƒ bÃ¡o giÃ¡")
    a, b, c = st.columns(3)
    usd_rate = a.number_input("USD â†’ VND", min_value=0.0, value=25500.0, step=100.0, key="new_quote_usd_rate")
    cny_rate = b.number_input("CNY â†’ VND", min_value=0.0, value=3500.0, step=10.0, key="new_quote_cny_rate")
    fx_source = c.text_input("Nguá»“n / ghi chÃº tá»· giÃ¡", value="Tá»· giÃ¡ nháº­p khi bÃ¡o giÃ¡; xÃ¡c nháº­n láº¡i trÆ°á»›c khi gá»­i khÃ¡ch.", key="new_quote_fx_source")

    st.markdown("#### á»¦y thÃ¡c nháº­p kháº©u vÃ  chi phÃ­ chuyá»ƒn tiá»n (Æ°á»›c tÃ­nh)")
    a, b, c, d = st.columns(4)
    entrusted_active = a.checkbox("CÃ³ phÃ­ á»§y thÃ¡c", key="new_quote_entrusted_active")
    goods_value = b.number_input("GiÃ¡ trá»‹ hÃ ng", min_value=0.0, value=0.0, key="new_quote_goods_value")
    goods_currency = c.selectbox("Tiá»n tá»‡ giÃ¡ trá»‹ hÃ ng", ["USD", "CNY", "VND"], key="new_quote_goods_currency")
    entrusted_rate = d.number_input("Tá»· lá»‡ phÃ­ á»§y thÃ¡c %", min_value=0.0, max_value=100.0, value=0.0, key="new_quote_entrusted_rate")
    review_requested = st.checkbox("Sale/manager yÃªu cáº§u review thÆ°Æ¡ng máº¡i", key="new_quote_review_requested")
    review_reason = st.text_input("LÃ½ do review (náº¿u cÃ³)", key="new_quote_review_reason") if review_requested else ""
    if entrusted_active:
        st.caption("Tá»· lá»‡ do Sale nháº­p theo chÃ­nh sÃ¡ch/duyá»‡t thÆ°Æ¡ng máº¡i. Review chá»‰ phÃ¡t sinh khi tá»· lá»‡ ngoÃ i khoáº£ng reference 2â€“3%, cÃ³ cá» review explicit, hoáº·c má»™t policy high-value Ä‘Æ°á»£c cáº¥u hÃ¬nh; hiá»‡n khÃ´ng cáº¥u hÃ¬nh ngÆ°á»¡ng high-value.")
    a, b, c, d, e = st.columns(5)
    remittance_amount = a.number_input("Sá»‘ tiá»n chuyá»ƒn USD", min_value=0.0, value=0.0, key="new_quote_remit_amount")
    bank_pct = b.number_input("PhÃ­ ngÃ¢n hÃ ng %", min_value=0.0, value=0.2, key="new_quote_bank_pct")
    swift = c.number_input("SWIFT USD", min_value=0.0, value=5.0, key="new_quote_swift")
    receiving = d.number_input("Receiving USD", min_value=0.0, value=0.0, key="new_quote_receiving")
    agent_fee = e.number_input("Agent conversion USD", min_value=0.0, value=0.0, key="new_quote_agent_fee")
    rmb_fee = st.number_input("RMB conversion fee CNY", min_value=0.0, value=0.0, key="new_quote_rmb_fee")
    include_remittance = st.checkbox("TÃ­nh chi phÃ­ chuyá»ƒn tiá»n vÃ o chi phÃ­ dá»± kiáº¿n", key="new_quote_include_remittance")

    if st.button("TÃ­nh phÆ°Æ¡ng Ã¡n vÃ  lÆ°u bÃ¡o giÃ¡ nhÃ¡p", type="primary", key="new_quote_save"):
        if not sales_owner.strip() or not origin.strip() or not destination.strip() or not goods_description.strip():
            st.error("Vui lÃ²ng nháº­p Ä‘á»§ SALE, Ä‘iá»ƒm Ä‘i, Ä‘iá»ƒm Ä‘áº¿n vÃ  mÃ´ táº£ hÃ ng hÃ³a.")
            return
        if not any(float(line["cost_unit"]) or float(line["sell_unit"]) for line in service_lines):
            st.error("Cáº§n cÃ³ Ã­t nháº¥t má»™t dÃ²ng dá»‹ch vá»¥ cÃ³ chi phÃ­ hoáº·c giÃ¡ bÃ¡o khÃ¡ch.")
            return
        payload = {
            "customer_id": customer_id, "customer_name": customers[customer_id].get("name", customer_id), "sales_owner": sales_owner.strip(), "origin": origin.strip(), "destination": destination.strip(), "route": route.strip(), "incoterm": incoterm, "transport_mode": transport_mode, "goods_description": goods_description.strip(), "expected_delivery_date": str(expected_delivery_date), "factory_lots": factory_lots, "service_lines": service_lines,
            "fx_snapshot": {"rates_to_vnd": {"USD": usd_rate, "CNY": cny_rate, "VND": 1}, "source": fx_source},
            "entrusted_import": {"active": entrusted_active, "goods_value": goods_value, "goods_currency": goods_currency, "rate_pct": entrusted_rate, "review_requested": review_requested, "review_reason": review_reason, "high_value_review_policy": {"status": "POLICY_NOT_CONFIGURED"}, "source": "Nháº­p theo chÃ­nh sÃ¡ch/duyá»‡t thÆ°Æ¡ng máº¡i; khÃ´ng pháº£i bÃºt toÃ¡n tÃ i chÃ­nh."},
            "remittance_estimate": {"remitted_amount_usd": remittance_amount, "bank_fee_pct": bank_pct, "swift_fee_usd": swift, "receiving_bank_fee_usd": receiving, "agent_conversion_fee_usd": agent_fee, "rmb_conversion_fee_cny": rmb_fee}, "include_remittance_in_cost": include_remittance,
            "assumptions": ["ÄÃ¢y lÃ  estimate/quotation, chÆ°a pháº£i nghÄ©a vá»¥ thanh toÃ¡n.", "GiÃ¡ agent/Ä‘á»‘i tÃ¡c pháº£i Ä‘Æ°á»£c Ä‘á»‘i chiáº¿u vá»›i nguá»“n bÃ¡o giÃ¡ thá»±c táº¿.", "KhÃ´ng tá»± Ä‘á»™ng hÃ³a khai bÃ¡o háº£i quan sai lá»‡ch."],
        }
        try:
            quote = new_quote_document(payload)
        except ValueError as exc:
            st.error(str(exc)); return
        if _persist_quote(quote):
            st.success(f"ÄÃ£ lÆ°u {quote['quote_no']} á»Ÿ tráº¡ng thÃ¡i DRAFT. Má»Ÿ tab Chi tiáº¿t Ä‘á»ƒ kiá»ƒm tra VÃ¬ sao ra giÃ¡ nÃ y?.")
            st.rerun()
        st.error(st.session_state.get("last_db_error") or "KhÃ´ng lÆ°u Ä‘Æ°á»£c bÃ¡o giÃ¡ vÃ o database.")


def _render_quote_detail() -> None:
    quotes = _quote_store(); quote_id = st.session_state.get("quote_detail_id")
    if not quote_id or quote_id not in quotes:
        st.info("Chá»n má»™t bÃ¡o giÃ¡ tá»« danh sÃ¡ch Ä‘á»ƒ xem chi tiáº¿t.")
        return
    quote = quotes[quote_id]
    calc = quote.get("calculation", {})
    st.subheader(f"{quote.get('quote_no', quote_id)} Â· {quote.get('customer_name', '')}")
    st.caption(f"Tráº¡ng thÃ¡i: {quote.get('status')} Â· PhiÃªn báº£n: {quote.get('version', 1)} Â· ÄÃ¢y lÃ  estimate, chÆ°a ghi Finance Ledger.")
    a, b, c, d = st.columns(4)
    a.metric("GiÃ¡ bÃ¡o khÃ¡ch", f"{calc.get('selling_price_total_vnd', 0):,.0f} VND")
    b.metric("Chi phÃ­ dá»± kiáº¿n", f"{calc.get('estimated_cost_vnd', 0):,.0f} VND")
    c.metric("Lá»£i nhuáº­n dá»± kiáº¿n", f"{calc.get('estimated_margin_vnd', 0):,.0f} VND")
    d.metric("BiÃªn lá»£i nhuáº­n", f"{calc.get('estimated_margin_pct', 0):,.1f}%")
    with st.expander("VÃ¬ sao ra giÃ¡ nÃ y?", expanded=True):
        st.write("Tá»•ng bÃ¡o giÃ¡ Ä‘Æ°á»£c quy Ä‘á»•i vá» VND theo snapshot tá»· giÃ¡ cá»§a quotation; tá»· giÃ¡ nÃ y khÃ´ng thay tháº¿ tá»· giÃ¡ giao dá»‹ch thá»±c táº¿.")
        st.dataframe(pd.DataFrame(quote.get("service_lines", [])), use_container_width=True, hide_index=True)
        st.json({"calculation": calc, "fees": quote.get("fees", {}), "fx_snapshot": quote.get("fx_snapshot", {}), "assumptions": quote.get("assumptions", [])})
    with st.expander("NhÃ  mÃ¡y / lÃ´ vÃ  thÃ´ng tin Logistics", expanded=True):
        st.dataframe(pd.DataFrame(quote.get("factory_lots", [])), use_container_width=True, hide_index=True)
        st.write({"origin": quote.get("origin"), "destination": quote.get("destination"), "incoterm": quote.get("incoterm"), "route": quote.get("route"), "goods": quote.get("goods_description")})
    if quote.get("fees", {}).get("entrusted_import", {}).get("commercial_review_required"):
        st.warning("PhÃ­ á»§y thÃ¡c Ä‘ang cáº§n review thÆ°Æ¡ng máº¡i do giÃ¡ trá»‹ cao hoáº·c tá»· lá»‡ ngoÃ i khoáº£ng thÃ´ng thÆ°á»ng.")

    current = quote.get("status", "DRAFT")
    actions: list[tuple[str, str]] = []
    if current == "DRAFT": actions.append(("Chuyá»ƒn sang chá» review", "READY_FOR_REVIEW"))
    if current == "READY_FOR_REVIEW": actions.extend([("ÄÃ£ gá»­i khÃ¡ch", "SENT"), ("KhÃ¡ch chá»‘t", "ACCEPTED")])
    if current == "SENT": actions.append(("KhÃ¡ch chá»‘t", "ACCEPTED"))
    if current == "ACCEPTED": actions.append(("Sáºµn sÃ ng táº¡o lÃ´", "READY_TO_CREATE_SHIPMENT"))
    if actions:
        cols = st.columns(len(actions))
        for col, (label, target) in zip(cols, actions):
            if col.button(label, key=f"quote_transition_{target}"):
                try:
                    updated = transition_quote(quote, target, actor=str(st.session_state.get("current_user", {}).get("username", "SALE")))
                except ValueError as exc:
                    st.error(str(exc)); continue
                if _persist_quote(updated): st.rerun()
    if current == "READY_TO_CREATE_SHIPMENT":
        _render_create_shipment(quote)
    st.markdown("#### Lá»‹ch sá»­ tráº¡ng thÃ¡i")
    st.dataframe(pd.DataFrame(quote.get("status_history", [])), use_container_width=True, hide_index=True)


def _render_create_shipment(quote: dict[str, Any]) -> None:
    st.markdown("#### Chuyá»ƒn bÃ¡o giÃ¡ Ä‘Ã£ cháº¥p nháº­n sang shipment draft")
    if quote.get("shipment_id"):
        st.success(f"ÄÃ£ liÃªn káº¿t shipment {quote['shipment_id']}. Retry sáº½ khÃ´ng táº¡o thÃªm lÃ´.")
        return
    st.info("HÃ nh Ä‘á»™ng nÃ y chá»‰ táº¡o shipment draft, giá»¯ quote reference vÃ  khÃ´ng ghi sá»• tÃ i chÃ­nh.")
    if not st.button("Táº¡o / prefill shipment draft", type="primary", key="quote_create_shipment"):
        return
    shipments = st.session_state.get("db_shipments", {})
    existing = next((item for item in shipments.values() if item.get("quote_id") == quote.get("id") or item.get("quote_reference") == quote.get("quote_no")), None)
    if existing:
        quote["shipment_id"] = existing.get("id") or existing.get("shipment_id")
        _persist_quote(quote); st.rerun()
    shipment_id = generate_shipment_id("SHP")
    draft = build_shipment_draft(quote, shipment_id)
    validation = validate_shipment(draft)
    if not validation.is_valid:
        st.error(validation.message); return
    if save_shipment_atomic(draft):
        st.session_state.setdefault("db_shipments", {})[shipment_id] = draft
        quote["shipment_id"] = shipment_id; quote["shipment_created_at"] = str(date.today())
        if _persist_quote(quote):
            st.success(f"ÄÃ£ táº¡o shipment draft {shipment_id}; quote reference Ä‘Æ°á»£c giá»¯ láº¡i.")
            st.rerun()
    st.error(st.session_state.get("last_db_error") or "KhÃ´ng táº¡o Ä‘Æ°á»£c shipment draft.")


def ui_sales_module() -> None:
    st.title("Sales & BÃ¡o giÃ¡ Logistics")
    st.caption("KhÃ¡ch há»i giÃ¡ â†’ thu tháº­p thÃ´ng tin â†’ tÃ­nh phÆ°Æ¡ng Ã¡n â†’ bÃ¡o giÃ¡ â†’ khÃ¡ch chá»‘t â†’ táº¡o lÃ´. GiÃ¡ hiá»ƒn thá»‹ lÃ  estimate, khÃ´ng pháº£i Finance Ledger.")
    quotes = _quote_store()
    tabs = st.tabs(["Danh sÃ¡ch bÃ¡o giÃ¡", "BÃ¡o giÃ¡ má»›i", "Chi tiáº¿t", "BÃ¡o giÃ¡ khung cÅ©"])
    with tabs[0]: _render_quote_table(quotes)
    with tabs[1]: _render_new_quote()
    with tabs[2]: _render_quote_detail()
    with tabs[3]:
        st.caption("Giá»¯ nguyÃªn mÃ n hÃ¬nh bÃ¡o giÃ¡ khung hiá»‡n há»¯u Ä‘á»ƒ khÃ´ng máº¥t dá»¯ liá»‡u lá»‹ch sá»­.")
        ui_legacy_sales_module()
