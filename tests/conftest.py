"""Suite-wide isolation for shared, PROCESS-GLOBAL runtime state.

Two pieces of state survive between tests that do not own them:

* the Phase-B staging transport — ONE in-process ``mongomock`` handle created by
  ``views.logi_sandbox`` — and
* ``streamlit.session_state``, which the tests share with the app.

Without isolation a test that seeds an operator, writes a shipment or logs a
session in silently changes the meaning of every later test: the same file
passed alone and failed inside ``python -m pytest tests -q`` (Issue #247 —
``test_unknown_role_falls_back_to_viewer`` saw a leaked SUPPORT session, and the
first-admin bootstrap tests saw a leaked user store, so
``require_login()`` rendered the login form instead of the bootstrap form).

The fix is isolation, not relaxation: each test starts from an EMPTY staging
database and an EMPTY session, and the fixtures that need data still seed it
themselves.  No test is skipped, deselected or re-ordered.
"""

from __future__ import annotations

import pytest


def _clear_session() -> None:
    """Drop every session key; harmless outside a Streamlit script run."""
    import streamlit as st

    try:
        st.session_state.clear()
    except Exception:  # noqa: BLE001 - bare mode may refuse; nothing to clear
        pass


@pytest.fixture(autouse=True)
def isolate_shared_runtime_state():
    from views import logi_sandbox

    logi_sandbox.reset_backend()
    _clear_session()
    yield
    _clear_session()
    logi_sandbox.reset_backend()
