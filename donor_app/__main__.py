"""Donor-exact UI entry point — clone of Logi-good design.

This module owns the Streamlit bootstrap.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

# Ensure repo root is importable
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Page config
st.set_page_config(
    page_title="LOGISTICS · TRƯỜNG THÀNH",
    layout="wide",
    page_icon="⚓",
    initial_sidebar_state="collapsed",
)

from donor_app import design, shell, store
from donor_app import home_page as _pages_home
from donor_app.pages_core import (
    render_tasks, render_shipments, render_shipment_detail,
    render_customers, render_quotes, render_agreements, render_partner_context,
)
from donor_app.pages_more import (
    render_contracts, render_contract_detail, render_new_contract, render_new_shipment,
)
from donor_app.pages_finance import (
    render_collect, render_reconcile, render_partner_debt,
    render_ceo, render_hs_lookup, render_handbook, render_translate,
    render_tracking, render_users,
)


def main():
    # 1. Initialise sandbox store and session state
    store._ensure_store()
    shell.init_session_state()

    # 2. Process query parameter actions and routes
    shell.process_actions()

    # 3. Render CSS, header, search dropdown, drawers, toasts
    shell.render_header_and_overlays()

    # 4. Two-column desktop layout (Sidebar + Main Content)
    active_page = store.get_active_page()
    route = shell.get_route()

    col_side, col_main = st.columns([264, 1100], gap="small")
    with col_side:
        shell.render_sidebar_content(active_page)

    with col_main:
        st.markdown('<div class="lg-main-content">', unsafe_allow_html=True)
        _dispatch(active_page, route)
        st.markdown('</div>', unsafe_allow_html=True)

    # 5. Mobile bottom navigation (visible on mobile < 700px)
    shell.render_mobile_nav(active_page)


def _dispatch(page: str, route: str):
    """Render the active page inside lg-main-content."""
    if page == "home":
        _pages_home.render()
    elif page == "tasks":
        render_tasks()
    elif page == "shipments":
        render_shipments()
    elif page == "shipment_detail":
        render_shipment_detail()
    elif page == "new_shipment":
        render_new_shipment()
    elif page == "tracking":
        render_tracking()
    elif page == "customers":
        render_customers()
    elif page == "partner_context":
        render_partner_context()
    elif page == "quotes":
        render_quotes()
    elif page == "agreements":
        render_agreements()
    elif page == "contracts":
        render_contracts()
    elif page == "new_contract":
        render_new_contract()
    elif page == "contract_detail":
        render_contract_detail()
    elif page == "collect":
        render_collect()
    elif page == "reconcile":
        render_reconcile()
    elif page == "partner_debt":
        render_partner_debt()
    elif page == "ceo":
        render_ceo()
    elif page == "hs_lookup":
        render_hs_lookup()
    elif page == "handbook":
        render_handbook()
    elif page == "translate":
        render_translate()
    elif page == "users":
        render_users()
    else:
        _pages_home.render()


if __name__ == "__main__":
    main()
