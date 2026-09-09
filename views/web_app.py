"""Logistics Work Desk — Phase A entry.

The entire visible shell + active page is ONE Streamlit Components v2
component root running the literal Logi-good React UI. Inner data is the
Logistics view-model (sandbox seed in Phase A; real readers in Phase B).
"""

from __future__ import annotations

import streamlit as st

from views import logi_shell, logi_view_model


def main() -> None:
    st.set_page_config(
        page_title="Phú Anh Logistics · Nội bộ",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Phase A: sandbox view-model (no production DB, no credentials).
    vm = logi_view_model.build_view_model()
    logi_shell.render(vm)
