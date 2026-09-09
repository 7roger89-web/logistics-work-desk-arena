"""Donor-exact UI entry point — clone of Logi-good design.

This module owns the Streamlit bootstrap. The old views (under ``views/``)
remain the source of truth for business logic; this file only changes how
those capabilities are presented.
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

# Hide the Streamlit chrome early
st.set_page_config(page_title="LOGISTICS · TRƯỜNG THÀNH", layout="wide", page_icon="⚓", initial_sidebar_state="collapsed")

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
    # initialise session state
    store._ensure_store()
    shell.init_session_state()

    # Install the post-message bridge so embedded components can dispatch
    # navigation/role/etc. actions to the parent Streamlit app.
    shell.install_bridge()

    # Process any pending actions from the bridge
    shell.process_actions()

    # Render the global shell (CSS + header + sidebar + mobile nav + drawers)
    shell.render_shell()

    # Determine which page to render
    route = shell.get_route()
    page = store.get_active_page()
    # The default main content area is rendered by the page modules below.
    # We open a flex container that the sidebar sits inside.
    st.markdown('<div class="lg-shell">', unsafe_allow_html=True)

    # Render page
    _dispatch(page, route)

    st.markdown("</div>", unsafe_allow_html=True)


def _dispatch(page: str, route: str):
    """Render the active page. The sidebar is already on the left inside
    ``lg-shell`` (rendered by the shell)."""
    # Render the page main content
    if page == "home":
        _pages_home.render()
    elif page == "tasks":
        render_tasks()
    elif page == "shipments":
        render_shipments()
    elif page == "shipment_detail" or route == "/lo-hang-detail":
        render_shipment_detail()
    elif page == "new_shipment" or route == "/tao-lo-moi":
        render_new_shipment()
    elif page == "tracking" or route == "/theo-doi":
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
    elif page == "new_contract" or route == "/hop-dong/moi":
        render_new_contract()
    elif page == "contract_detail" or route == "/hop-dong-detail":
        render_contract_detail()
    elif page == "collect" or route == "/tai-chinh/thu-tien":
        render_collect()
    elif page == "reconcile" or route == "/tai-chinh/doi-soat":
        render_reconcile()
    elif page == "partner_debt" or route == "/tai-chinh/cong-no-doi-tac":
        render_partner_debt()
    elif page == "ceo":
        render_ceo()
    elif page == "hs_lookup" or route == "/tra-cuu-thue":
        render_hs_lookup()
    elif page == "handbook" or route == "/so-tay":
        render_handbook()
    elif page == "translate" or route == "/dich-thuat":
        render_translate()
    elif page == "users" or route == "/nguoi-dung":
        render_users()
    else:
        _pages_home.render()


if __name__ == "__main__":
    main()
