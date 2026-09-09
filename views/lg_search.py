"""LOGI-GOOD EXACT — Tìm kiếm toàn cục (mã lô · khách hàng · hợp đồng)."""
from __future__ import annotations

import streamlit as st

from views.lg_core import esc, link_url


def search_page(close_href: str | None = None) -> None:
    if not close_href:
        # Overlay close fallback: preserve lg/sid/tab, drop only ov.
        qp = st.query_params
        parts = [f"{key}={esc(str(qp.get(key)))}" for key in ("lg", "sid", "tab")
                 if key in qp and str(qp.get(key) or "").strip()]
        close_href = ("?" + "&".join(parts)) if parts else "?lg=home"
    st.markdown(
        "<div style='max-width:760px;margin:0 auto;'><div class='lg-card'>"
        "<div style='padding:20px 22px;'>"
        "<p style='margin:0 0 4px;font-size:22px;font-weight:800;color:#0f2a4a;'>Tìm kiếm</p>"
        "<p style='margin:0 0 12px;color:#64748b;font-size:14px;'>Tìm mã lô · khách hàng · hợp đồng · người phụ trách</p>"
        "<input id='lg-search-input' placeholder='Gõ ít nhất 2 ký tự…' style='width:100%;border:2px solid #e2e8f0;"
        "border-radius:12px;padding:12px 14px;font-size:15px;outline:none;' oninput=\"const v=this.value.trim();"
        "document.querySelectorAll('.lg-sr').forEach(e=>e.style.display='none'); if(v.length>=2){"
        "document.querySelectorAll('.lg-sr').forEach(e=>{if((e.dataset.s||'').toLowerCase().includes(v.toLowerCase()))"
        "e.style.display=''});} this.value;\" />",
        unsafe_allow_html=True,
    )
    ships = st.session_state.get("db_shipments", {}) or {}
    customers = st.session_state.get("db_customers", {}) or {}
    contracts = st.session_state.get("db_contracts", {}) or {}

    st.markdown("<p style='margin:14px 0 8px;font-size:12px;font-weight:800;letter-spacing:.08em;color:#94a3b8;'>"
                "LÔ HÀNG</p>", unsafe_allow_html=True)
    if ships:
        items = []
        for sid, ship in ships.items():
            if not isinstance(ship, dict):
                continue
            label = f"{sid} · {ship.get('customer') or ship.get('client') or ''}"
            items.append(
                f"<a class='lg-sr lg-rowlink' data-s='{esc(label.lower())} {esc(sid.lower())}' "
                f"href='{link_url('shipment', sid=sid)}'>"
                f"<span style='width:40px;height:40px;border-radius:12px;background:#eff6ff;display:grid;"
                f"place-items:center;font-size:18px;'>📦</span>"
                f"<span style='flex:1;min-width:0;'><b style='color:#0f2a4a;font-size:14.5px;'>{esc(label)}</b>"
                f"<span style='display:block;font-size:12.5px;color:#64748b;'>Lô hàng — {esc(ship.get('status') or '')}</span></span>"
                f"<span style='color:#cbd5e1;'>→</span></a>"
            )
        if items:
            st.markdown(f"<div style='display:grid;gap:8px;'>{''.join(items)}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#94a3b8;font-size:13.5px;'>Chưa có dữ liệu lô hàng.</p>", unsafe_allow_html=True)

    st.markdown("<p style='margin:16px 0 8px;font-size:12px;font-weight:800;letter-spacing:.08em;color:#94a3b8;'>"
                "KHÁCH HÀNG</p>", unsafe_allow_html=True)
    c_items = []
    for cid, doc in customers.items():
        if not isinstance(doc, dict):
            continue
        name = doc.get("name") or cid
        c_items.append(
            f"<a class='lg-sr lg-rowlink' data-s='{esc(str(name).lower())}' href='{link_url('customers')}'>"
            f"<span style='width:40px;height:40px;border-radius:12px;background:#fffbeb;display:grid;"
            f"place-items:center;font-size:18px;'>👥</span>"
            f"<span style='flex:1;min-width:0;'><b style='color:#0f2a4a;font-size:14.5px;'>{esc(name)}</b>"
            f"<span style='display:block;font-size:12.5px;color:#64748b;'>MST {esc(doc.get('tax_code') or '—')}</span></span>"
            f"<span style='color:#cbd5e1;'>→</span></a>"
        )
    if c_items:
        st.markdown(f"<div style='display:grid;gap:8px;'>{''.join(c_items)}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#94a3b8;font-size:13.5px;'>Chưa có dữ liệu khách hàng.</p>", unsafe_allow_html=True)

    st.markdown("<p style='margin:16px 0 8px;font-size:12px;font-weight:800;letter-spacing:.08em;color:#94a3b8;'>"
                "HỢP ĐỒNG</p>", unsafe_allow_html=True)
    k_items = []
    for cid, doc in contracts.items():
        if not isinstance(doc, dict):
            continue
        name = doc.get("id") or cid
        company = doc.get("company") or doc.get("customer") or ""
        k_items.append(
            f"<a class='lg-sr lg-rowlink' data-s='{esc(f'{name} {company}'.lower())}' href='{link_url('contracts')}'>"
            f"<span style='width:40px;height:40px;border-radius:12px;background:#ecfdf5;display:grid;"
            f"place-items:center;font-size:18px;'>📜</span>"
            f"<span style='flex:1;min-width:0;'><b style='color:#0f2a4a;font-size:14.5px;'>{esc(name)}</b>"
            f"<span style='display:block;font-size:12.5px;color:#64748b;'>{esc(company)}</span></span>"
            f"<span style='color:#cbd5e1;'>→</span></a>"
        )
    if k_items:
        st.markdown(f"<div style='display:grid;gap:8px;'>{''.join(k_items)}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#94a3b8;font-size:13.5px;'>Chưa có dữ liệu hợp đồng.</p>", unsafe_allow_html=True)
    st.markdown(
        "<p style='margin-top:14px;font-size:12.5px;color:#94a3b8;'>Kết quả hiện tại dừng ở danh sách có sẵn — "
        "hệ thống chỉ tìm trên dữ liệu thật của bạn.</p>"
        f"<a href='{close_href}' style='display:inline-flex;margin-top:6px;font-weight:800;color:#1e5aa8;'>"
        "← Đóng tìm kiếm</a>"
        "</div></div></div>",
        unsafe_allow_html=True,
    )
