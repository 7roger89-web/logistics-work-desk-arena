"""S2 TEST-only observer around the unchanged app.py.

Run with Streamlit, AUTH_REQUIRED=true, no MONGO_URI, S2_EVIDENCE_DIR and
S2_TEST_PASSWORD. This is not an alternate app or writer: it seeds TEST users
through core.users, exercises one canonical RBAC denial, then calls app.py's
real main(). Observation wraps only the existing model builder and payment
writer. Every DB assertion below reads the SAME database handle in this OS
process. A configurable first-call delay makes pending UI observable; it never
changes the writer's arguments or result.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import runpy
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = Path(os.environ["S2_EVIDENCE_DIR"]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
PASSWORD = os.environ["S2_TEST_PASSWORD"]
assert len(PASSWORD) >= 8
assert not os.environ.get("MONGO_URI"), "S2 refuses a real Mongo URI"
assert os.environ.get("AUTH_REQUIRED", "").lower() == "true"

import streamlit as st
st.secrets = {}
from core import auth, config, database
from core.users import build_user_document
from views import logi_sandbox, logi_view_model as vm

assert config.AUTH_REQUIRED is True
# After the first script run the existing sandbox has installed its explicit
# placeholder. Accept only that exact local value on reruns, never a real URI.
assert config.MONGO_URI in ("", logi_sandbox.STAGING_URI_PLACEHOLDER)
assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
DB = database.get_db()
assert DB.name == "logistics_staging"
assert type(DB.client).__module__.startswith("mongomock")
assert config.ENV_IDENTITY == "PREVIEW"
LOT = "LO-0306"

if not hasattr(vm, "_s2_observed_build"):
    for username, role in (("qa.s2.support", "support"), ("qa.s2.sale", "sale")):
        if DB.users.find_one({"username": username}) is None:
            DB.users.insert_one(build_user_document(
                username, PASSWORD, f"S2 TEST {role}", role, created_by="s2.fixture",
            ))


    def store_rows():
        ship = DB.shipments.find_one({"id": LOT}, {"_id": 0}) or {}
        payments = list(((ship.get("data") or {}).get("3.4") or {}).get("payments") or [])
        requests = list(DB.financial_action_requests.find({"shipment_id": LOT}, {"_id": 0}))
        audits = list(DB.audit_logs.find(
            {"entity_type": "shipment", "entity_id": LOT, "action": "direct_payment_created"},
            {"_id": 0},
        ))
        events = list(DB.notification_outbox.find(
            {"event_type": "shipment.payment_recorded", "payload.shipment_id": LOT}, {"_id": 0},
        ))
        return {
            "pid": os.getpid(), "database": DB.name, "client_object_id": id(DB.client),
            "database_object_id": id(DB), "transport": logi_sandbox.transport_name(),
            "shipment_id": LOT, "currency": ship.get("currency"),
            "version": ship.get("version"), "payments": payments,
            "payment_count": len(payments), "requests": requests,
            "request_count": len(requests), "audits": audits, "audit_count": len(audits),
            "events": events, "event_count": len(events),
        }


    def write_json(name, value):
        payload = json.dumps(value, ensure_ascii=False, default=str, indent=2) + "\n"
        temp = OUT / (name + ".tmp")
        temp.write_text(payload, encoding="utf-8")
        temp.replace(OUT / name)


    # Canonical backend denial on the SAME store, not a mocked authorization result.
    st.session_state["current_user"] = {
        "username": "qa.s2.sale", "user_id": "qa.s2.sale", "role": "sale",
    }
    assert auth.can_operate_business("finance_write") is False
    before_denial = store_rows()
    denied = database.save_direct_shipment_payment(LOT, {
        "amount": 137000, "request_id": "S2-UNAUTHORIZED-CONTROL", "note": "Thu tiền khách",
    }, actor="qa.s2.sale")
    after_denial = store_rows()
    assert denied[0] is False and "không có quyền" in denied[2].lower(), denied
    assert before_denial == after_denial, "unauthorized call changed persisted state"
    write_json("rbac-negative.json", {
        "result": False, "error": denied[2], "actor": "qa.s2.sale",
        "finance_write": False, "before": before_denial, "after": after_denial,
        "state_unchanged": True, "same_process_and_store": True,
    })
    st.session_state.pop("current_user", None)
    write_json("pre-state.json", store_rows())

    ORIGINAL_BUILD = vm.build_view_model
    ORIGINAL_WRITER = database.save_direct_shipment_payment
    CALLS = []
    DELAYED = set()
    write_json("writer-calls.json", CALLS)


    def observed_writer(shipment_id, payment_document, actor=None):
        request_id = str(payment_document.get("request_id") or "")
        call = {
            "index": len(CALLS) + 1, "shipment_id": shipment_id,
            "request_id": request_id, "amount": str(payment_document.get("amount")),
            "actor": actor, "started_ns": time.time_ns(),
            "before": store_rows(),
        }
        CALLS.append(call)
        write_json("writer-calls.json", CALLS)
        # Delay only the first browser payment intent, leaving all business logic
        # and the return value untouched. The browser must still be pending here.
        if request_id.startswith("PAY-") and request_id not in DELAYED:
            DELAYED.add(request_id)
            time.sleep(float(os.environ.get("S2_WRITER_DELAY_SECONDS", "4")))
        result = ORIGINAL_WRITER(shipment_id, payment_document, actor=actor)
        call.update({"finished_ns": time.time_ns(), "ok": result[0],
                     "message": result[2], "after": store_rows()})
        write_json("writer-calls.json", CALLS)
        return result


    def observed_build():
        model = ORIGINAL_BUILD()
        user = auth.current_user()
        raw = store_rows()
        fresh = next((row for row in model.get("shipments", []) if row.get("id") == LOT), {})
        snapshot = {
            "observed_ns": time.time_ns(), "raw": raw,
            "actor": {k: user.get(k) for k in ("username", "user_id", "role")},
            "finance_write": auth.can_operate_business("finance_write"),
            "fresh_payment_projection": (fresh.get("finance") or {}).get("payments", []),
            "lastWrites": model.get("lastWrites", []),
            "writer_call_count": len(CALLS),
        }
        write_json("latest-readback.json", snapshot)
        # Append bounded receipts, never credentials or the full user/customer DB.
        with (OUT / "readback-history.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(snapshot, ensure_ascii=False, default=str) + "\n")
        return model


    vm.build_view_model = observed_build
    database.save_direct_shipment_payment = observed_writer
    vm._s2_observed_build = observed_build
    vm._s2_payment_writer = observed_writer
    print(json.dumps({"S2_STARTUP": store_rows(), "auth_required": True,
                      "app": "app.py", "fixture_lot": LOT}), flush=True)

# Execute the actual repository launcher, hence the actual views.web_app.main.
runpy.run_path(str(ROOT / "app.py"), run_name="__main__")
