"""LOGISTICS PRO — Logi-good donor view entry (V4).

Run:  streamlit run views/lg_app.py
"""
from __future__ import annotations

import os
import sys

# Make repo root importable regardless of launch directory (core, views, lg).
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
_VIEWS = os.path.dirname(os.path.abspath(__file__))
if _VIEWS not in sys.path:
    sys.path.insert(0, _VIEWS)

import streamlit as st

from core.auth import require_login

from lg.pages import (
    home_page, tasks_page, shipments_page, new_shipment_page,
    shipment_detail_page,
)
from lg import svc
from lg.shell import render_sidebar, render_bottom_nav

from lg.pages_misc import (
    customers_page, contracts_page, contract_detail_page, new_contract_page,
    receive_page, reconcile_page, partner_debt_page, ceo_page,
    context_page, quote_page, agreement_page,
    tariff_page, notebook_page, translate_page, admin_page,
)


def _tracking_page():
    from lg.pages import _set_page, _status_tone
    from lg.helpers import to_text, set_page
    from lg import widgets as w

    rows = svc.dashboard_rows()
    st.markdown(
        '<div style="display:flex;justify-content:space-between;align-items:center;padding:4px 0 8px">'
        '<div><div style="font-size:18px;font-weight:800;color:#0f2a4a">🛰 Theo Dõi Vận Chuyển</div>'
        '<div style="font-size:12.5px;color:#64748b">Trạng thái từng chặng của các lô đang vận chuyển</div></div></div>',
        unsafe_allow_html=True,
    )
    if not rows:
        st.markdown('<div class="lg-card" style="color:#64748b">Không có lô đang vận chuyển.</div>',
                    unsafe_allow_html=True)
        return
    steps = ["Lấy hàng", "Vận chuyển", "Thông quan", "Giao hàng"]
    for r in rows:
        tone = _status_tone(r.get("operational_status"))
        cur = {"wait": 0, "pending": 2, "done": 3}.get(r.get("operational_status"), 1)
        chips = []
        for i, s in enumerate(steps):
            cls = "stp-done" if i < cur else ("stp-cur" if i == cur else "stp-todo")
            chips.append(f'<div class="step"><div class="n {cls}">{i+1}</div>'
                         f'<div class="l">{s}</div></div>')
        if st.button(f'📦 {r.get("shipment_id")} · {r.get("customer")} →',
                     key=f'tr_{r.get("shipment_id")}', use_container_width=True, type="secondary"):
            st.session_state["lg_shipment"] = r.get("shipment_id")
            set_page("shipment_detail")
            st.rerun()
        st.markdown(
            f'<div class="lg-card" style="margin:4px 0 10px">'
            f'<div style="display:flex;justify-content:space-between;margin-bottom:8px;flex-wrap:wrap">'
            f'<b style="color:#0f2a4a">{w._esc(r.get("shipment_id"))}</b>'
            f'<span>{w.badge_html(r.get("operational_status_label"), tone)}</span></div>'
            f'<div class="lg-progress">{"".join(chips)}'
            f'<div style="flex:1"></div></div></div>',
            unsafe_allow_html=True,
        )


PAGES = {
    "home": home_page,
    "tasks": tasks_page,
    "shipments": shipments_page,
    "shipment_detail": shipment_detail_page,
    "new_shipment": new_shipment_page,
    "tracking": _tracking_page,
    "customers": customers_page,
    "context": context_page,
    "quote": quote_page,
    "agreement": agreement_page,
    "contracts": contracts_page,
    "contract_detail": contract_detail_page,
    "new_contract": new_contract_page,
    "receive": receive_page,
    "reconcile": reconcile_page,
    "partner_debt": partner_debt_page,
    "ceo": ceo_page,
    "tariff": tariff_page,
    "notebook": notebook_page,
    "translate": translate_page,
    "admin": admin_page,
}


def main() -> None:
    st.set_page_config(page_title="LOGISTICS PRO", layout="wide",
                       initial_sidebar_state="expanded")
    identity = require_login()
    if identity is None:
        st.stop()

    svc.ensure_ready()

    page = st.session_state.get("lg_page", "home")
    if page not in PAGES:
        page = "home"

    render_sidebar()
    PAGES[page]()
    render_bottom_nav()


if __name__ == "__main__":
    main()
