"""Authenticated, disposable browser fixture over the existing T6 launcher.

Never a production entrypoint. Requires AUTH_REQUIRED=true and a private JSON
credential file (a generated, private password key). Real login,
RBAC, shipment writers, version checks and audit remain in the existing app.
The database is the project's isolated, process-local Mongomock transaction
adapter, NOT a production MongoDB durability test. See the flow evidence README.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

assert os.environ.get("AUTH_REQUIRED", "").lower() == "true", "Real login is required"
assert not os.environ.get("MONGODB_URI") and not os.environ.get("MONGO_URI"), "Isolated fixture only"
credentials_path = Path(os.environ["LOGI199_TEST_CREDENTIALS_FILE"])
readback_path = Path(os.environ["LOGI199_TEST_READBACK_FILE"])

from views import logi_sandbox
from core import config, database
from core.users import build_user_document
import mongomock

assert not os.environ.get("LOGISTICS_PRO_SECRETS_FILE"), "No production secrets"
assert not (ROOT / ".streamlit/secrets.toml").exists(), "No production secrets file"
assert config.AUTH_REQUIRED is True
assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
assert isinstance(logi_sandbox._state["client"], mongomock.MongoClient)
assert not logi_sandbox._real_uri_configured()
db = database.get_db()
credentials = json.loads(credentials_path.read_text(encoding="utf-8"))
# Fixture provisioning into the disposable DB, not login/session injection.
# The fallback staging actor has no canonical user, so unchanged require_login
# rejects it and renders the real form until the operator actually logs in.
for role in ("sale", "support"):
    username = f"flow199.{role}"
    if not db.users.find_one({"username": username}):
        db.users.insert_one(build_user_document(
            username, credentials["password"], f"Flow 199 {role.title()} (test)", role,
            created_by="isolated-flow199-fixture"))
if not db.shipments.find_one({"id": "FLOW199-FCL"}):
    from tests.test_visual_shipment_workspace import document

    shipment = document(scope=["ORIGIN_PICKUP", "EXPORT_HANDLING", "EXPORT_CUSTOMS",
                               "ORIGIN_TERMINAL_OR_BORDER", "MAIN_CARRIAGE"])
    shipment["id"] = "FLOW199-FCL"
    shipment.pop("version", None)
    shipment["data"]["1.2"]["sea_export"] = {"on_board_at": "2026-10-04"}
    shipment["data"]["1.2"]["transport_legs"][1].update(
        etd="2026-10-02", eta="2026-10-18", atd="2026-10-07")
    assert database.save_shipment_atomic(shipment, actor="isolated-flow199-fixture")
runpy.run_path(str(ROOT / "scripts/logi199_t6_staging_app.py"), run_name="__main__")

# Test-side independent DB readback after each app rerun; never user/password
# records or tokens. This is not a browser endpoint and not a product writer.
snapshot = {"isolation": "MONGOMOCK_PROCESS_LOCAL", "authRequired": config.AUTH_REQUIRED,
            "shipments": {}}
for sid in ("FLOW199-FCL", "T6-FCL", "LO-0306"):
    row = db.shipments.find_one({"id": sid}, {"_id": 0}) or {}
    audits = list(db.audit_logs.find({"entity_type": "shipment", "entity_id": sid}, {"_id": 0}))
    snapshot["shipments"][sid] = {
        "id": row.get("id"), "version": row.get("version"), "customerId": row.get("customer_id"),
        "sea_export": row.get("data", {}).get("1.2", {}).get("sea_export", {}),
        "updated_by": row.get("updated_by"), "updated_by_role": row.get("updated_by_role"),
        "audit_count": len(audits),
        "audit": [{"action": event.get("action"), "actor": event.get("actor"), "actor_role": event.get("actor_role"),
                   "before_version": (event.get("before") or {}).get("version"),
                   "after_version": (event.get("after") or {}).get("version"),
                   "before_on_board_at": (event.get("before") or {}).get("data", {}).get("1.2", {}).get("sea_export", {}).get("on_board_at"),
                   "after_on_board_at": (event.get("after") or {}).get("data", {}).get("1.2", {}).get("sea_export", {}).get("on_board_at")}
                  for event in audits],
    }
readback_path.parent.mkdir(parents=True, exist_ok=True)
readback_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
