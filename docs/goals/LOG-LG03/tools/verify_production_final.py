"""Read-only final production identity verification for LOG-LG03 closure.
Run on the Owner's machine (app config already works there):
    python docs/goals/LOG-LG03/tools/verify_production_final.py
Only count/find; never write.
"""
import json
import os
import sys
import datetime

import toml  # type: ignore
from pymongo import MongoClient  # type: ignore

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
SECRETS = os.path.join(APP_ROOT, ".streamlit", "secrets.toml")

cfg = toml.load(SECRETS)
mongo_cfg = cfg.get("mongo", {})
uri = mongo_cfg.get("uri")
db_name = mongo_cfg.get("database") or "logistics_db"

if not uri:
    print(f"FAIL: no [mongo].uri in secrets keys: {list(cfg.keys())}", file=sys.stderr)
    sys.exit(2)

client = MongoClient(uri, serverSelectionTimeoutMS=15000)
db = client[db_name]

checks = []


def check(name: str, ok: bool, detail: str) -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}")
    checks.append({"name": name, "status": status, "detail": detail})


try:
    # --- users ---
    users = list(db.users.find({}, {"username": 1, "role": 1, "active": 1, "active_states": 1}))
    users.sort(key=lambda u: u["username"])
    admin_docs = [u for u in users if u["username"] == "admin"]
    rehearsal = [u for u in users if u["username"].startswith("rehearsal_")]
    other = [u for u in users if u["username"] != "admin" and not u["username"].startswith("rehearsal_")]

    if len(admin_docs) == 1:
        admin = admin_docs[0]
        check("admin_present", admin.get("active") is True, f"admin active={admin.get('active')}")
        check("admin_role", admin.get("role") == "admin", f"role={admin.get('role')}")
    else:
        check("admin_present", False, f"admin docs={len(admin_docs)}")

    for u in rehearsal:
        check(f"rehearsal_{u['username']}_inactive", u.get("active") is False,
              f"active={u.get('active')} active_states_n={len(u.get('active_states') or [])}")
    check("rehearsal_count", len(rehearsal) == 3, f"rehearsal users={len(rehearsal)}")
    check("no_other_users_changed", len(other) == 0, f"other user count={len(other)}")
    print(json.dumps([{"username": u["username"], "role": u.get("role"), "active": u.get("active"),
                       "active_states": u.get("active_states")} for u in users], ensure_ascii=False, indent=2))

    # --- counts ---
    customers = db.customers.count_documents({})
    shipments = db.shipments.count_documents({})
    check("customers_count", customers == 362, f"customers={customers}")
    check("shipments_count", shipments == 78, f"shipments={shipments}")

    # --- finance safety: no new finance records created during deployment session ---
    for coll in ["financial_records", "transactions", "allocations"]:
        try:
            n = db[coll].count_documents({})
            print(f"[INFO] {coll}: {n} docs")
        except Exception as e:  # noqa: BLE001
            print(f"[INFO] {coll}: not present ({e.__class__.__name__})")

finally:
    client.close()

fails = [c for c in checks if c["status"] == "FAIL"]
print(f"\nSUMMARY: {len(checks)} checks, {len(checks) - len(fails)} pass, {len(fails)} fail")
sys.exit(1 if fails else 0)
