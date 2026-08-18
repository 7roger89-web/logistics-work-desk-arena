"""Debug: why does _visible_routes hide Tạo Lô Mới for role=sale in AppTest?"""
from __future__ import annotations

import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from streamlit.testing.v1 import AppTest  # noqa: E402

APP_PATH = Path(__file__).resolve().parents[4] / "app.py"

app = AppTest.from_file(str(APP_PATH), default_timeout=120)
app.session_state.active_page = "Tổng Quan Công Việc"
app.session_state.current_user = {
    "username": "qa_sale",
    "role": "sale",
    "display_name": "QA sale",
    "user_id": "qa_sale",
    "email": "",
}
with ExitStack() as stack:
    stack.enter_context(patch("views.web_app.refresh_core_data", return_value=None))
    stack.enter_context(patch("views.dashboard.cached_load_data", return_value={}))
    stack.enter_context(patch("views.dashboard.load_tasks", return_value=[]))
    stack.enter_context(patch("views.shipment.load_proxy_payments", return_value={}))
    stack.enter_context(patch("views.shipment.load_entrustments", return_value={}))
    stack.enter_context(patch("views.shipment.load_audit_logs", return_value=[]))
    app.run()

print("exception:", app.exception)
print("session current_user after run:", app.session_state["current_user"] if "current_user" in app.session_state else None)
print("session active_page after run:", app.session_state["active_page"] if "active_page" in app.session_state else None)
texts = []
for items in (app.button,):
    for item in items:
        label = getattr(item, "label", None)
        if isinstance(label, str):
            texts.append(label)
print("\nALL SIDEBAR+BODY BUTTONS:")
for t in texts:
    print("-", t)
