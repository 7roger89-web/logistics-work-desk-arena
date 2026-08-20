"""Quản lý cache session-state tập trung."""
from __future__ import annotations

import streamlit as st

from core.database import ensure_indexes, load_agreements, load_contracts, load_customers, load_data, load_rate_cards


def initialize_state() -> None:
    defaults = {
        "view_mode": "dashboard",
        "db_shipments": {},
        "db_customers": {},
        "db_contracts": {},
        "db_agreements": {},
        "db_rate_cards": {},
        "data_loaded": False,
        "needs_refresh": False,
        "dirty_resources": set(),
        "last_db_error": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def refresh_core_data(force: bool = False) -> None:
    if not force and st.session_state.get("data_loaded") and not st.session_state.get("needs_refresh"):
        return
    ensure_indexes()
    st.session_state.db_shipments = load_data()
    st.session_state.db_customers = load_customers()
    st.session_state.db_contracts = load_contracts()
    # UX-STAB P1: Lazy-load agreements and rate_cards — only used by specific views
    # (entity_context, review_queue, sales) which have their own fallback loading.
    # This reduces login/cold-start latency by ~2s.
    if 'db_agreements' not in st.session_state or not st.session_state.db_agreements:
        st.session_state.db_agreements = load_agreements()
    if 'db_rate_cards' not in st.session_state or not st.session_state.db_rate_cards:
        st.session_state.db_rate_cards = load_rate_cards()
    st.session_state.pop("db_reporting_shipments", None)
    st.session_state.pop("db_archive", None)
    st.session_state.pop("db_entrustments", None)
    st.session_state.pop("kb_data", None)
    st.session_state.data_loaded = True
    st.session_state.needs_refresh = False
    st.session_state.dirty_resources = set()
