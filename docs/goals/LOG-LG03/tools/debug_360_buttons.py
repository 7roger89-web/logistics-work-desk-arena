"""Debug: which buttons render after dashboard_open_360_S-001 click?"""
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, ".")
from streamlit.testing.v1 import AppTest

APP_PATH = Path("app.py").resolve()

def _shipments():
    return {
        "S-001": {
            "id": "S-001", "shipment_id": "S-001", "customer": "Acme", "customer_id": "CUS-1",
            "status": "pending", "customer_required_date": "2026-08-30",
            "factories": [{"factory_name": "Factory North", "lot_id": "LOT-1", "product": "Widgets",
                           "quantity": 12, "factory_ready_date": "2026-08-20",
                           "required_information_complete": True}],
            "partner": {"name": "Blue Agent", "role": "Pickup agent"},
            "data": {"0.0": {"created_at": "2026-08-01", "mode": "Sea"}, "1.2": {"pol": "Yantian", "pod": "Cat Lai"},
                     "2.4": {}, "2.6": {}, "2.7": {}, "3.4": {"details": [], "payments": []}},
        }
    }

with ExitStack() as stack:
    stack.enter_context(patch("views.web_app.require_login", return_value={"username": "fixture", "display_name": "Fixture", "role": "admin"}))
    stack.enter_context(patch("core.database.init_connection", return_value=None))
    stack.enter_context(patch("views.web_app.refresh_core_data", return_value=None))
    stack.enter_context(patch("views.dashboard.cached_load_data", return_value=_shipments()))
    stack.enter_context(patch("views.dashboard.load_tasks", return_value=[]))
    stack.enter_context(patch("views.shipment.load_proxy_payments", return_value={}))
    stack.enter_context(patch("views.shipment.load_entrustments", return_value={}))
    stack.enter_context(patch("views.shipment.load_audit_logs", return_value=[]))
    app = AppTest.from_file(str(APP_PATH), default_timeout=60)
    app.session_state.active_page = "Tổng Quan Công Việc"
    app.session_state.db_shipments = _shipments()
    app.session_state.db_customers = {"CUS-1": {"id": "CUS-1", "name": "Acme", "contact_person": "Lan"}}
    app.run()
    print("exceptions:", len(app.exception))
    open_button = next(item for item in app.button if item.key == "dashboard_open_360_S-001")
    open_button.click()
    app.run()
    print("after click exceptions:", len(app.exception))
    for e in app.exception:
        print("EXC:", e.type, e.value)
    print("buttons:", [b.key for b in app.button])
    print("subheaders:", [str(h.value)[:70] for h in app.subheader])
