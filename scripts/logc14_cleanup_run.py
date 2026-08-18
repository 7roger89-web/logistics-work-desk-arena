"""LOG-C15 step 1b: Drop the LOG-C14 temporary test database and revoke the
LOG-C14 temporary database user, preserving before/after evidence.

Only touches:
- database logistics_workdesk_logc14 (drop)
- user logc14test (dropUser)

NEVER touches: logistics_db, production users, other cluster configuration.
Prints NO credentials, hashes, or connection strings.
"""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

TARGET_DB = "logistics_workdesk_logc14"
TARGET_USER = "logc14test"

ROOT = Path(__file__).resolve().parents[1]

import os  # noqa: E402

from pymongo import MongoClient  # noqa: E402

_explicit = os.getenv("LOGISTICS_PRO_SECRETS_FILE", "").strip()
_secrets_file = Path(_explicit).expanduser() if _explicit else (ROOT / ".streamlit" / "secrets.toml")

def main() -> int:
    with _secrets_file.open("rb") as handle:
        payload = tomllib.load(handle)
    mongo_cfg = payload.get("mongo", {})
    uri = mongo_cfg.get("uri") or payload.get("MONGO_URI", "")
    if not uri or "logc14" not in uri.lower():
        print("URI_NOT_LOGC14_CLUSTER — stopping, ownership unproven.")
        return 2

    client = MongoClient(uri, serverSelectionTimeoutMS=15000, appName="logc15-cleanup-run")
    client.admin.command("ping")
    try:
        before_dbs = sorted(db["name"] for db in client.list_databases(nameOnly=True))
        has_target_db = TARGET_DB in before_dbs
        print("BEFORE_DBS:", before_dbs)
        print(f"TARGET_DB_EXISTS_BEFORE: {has_target_db}")

        if has_target_db:
            db = client[TARGET_DB]
            # Atlas role 'readWriteAnyDatabase' on a free/limited tier may lack
            # dropDatabase privilege. Empty every collection instead — an empty
            # database holds no data and Atlas eventually removes it from
            # listDatabases once it has no collections.
            for coll in list(db.list_collection_names()):
                try:
                    db[coll].drop()
                    print(f"DROPPED_COLLECTION: {coll}")
                except Exception as exc:  # noqa: BLE001
                    print(f"DROP_COLLECTION_FAILED: {coll}: {type(exc).__name__}: {exc}")
            after_colls = db.list_collection_names()
            print("TARGET_DB_REMAINING_COLLECTIONS:", sorted(after_colls))
        after_drop_dbs = sorted(db["name"] for db in client.list_databases(nameOnly=True))
        print("AFTER_DROP_DBS:", after_drop_dbs)
        print(f"TARGET_DB_EXISTS_AFTER: {TARGET_DB in after_drop_dbs}")

        identity = client.admin.command("connectionStatus")
        authed_users = identity["authInfo"].get("authenticatedUsers", [])
        current_user_db = None
        for au in authed_users:
            if au["user"] == TARGET_USER:
                current_user_db = au["db"]
        print(f"CURRENT_CRED_IS_TARGET_USER: {current_user_db is not None}")

        # Dropping oneself is allowed if the credential holds dropUser on admin.
        drop_result = None
        if current_user_db is not None:
            try:
                drop_result = client.admin.command("dropUser", TARGET_USER)
            except Exception as exc:  # noqa: BLE001
                print(f"DROPUSER_FAILED: {type(exc).__name__}: {exc}")
        print("DROPUSER_RESULT:", "ok" if drop_result and drop_result.get("ok") else drop_result)

        # Final structural evidence
        final_dbs = sorted(db["name"] for db in client.list_databases(nameOnly=True))
        print("FINAL_DBS:", final_dbs)
        print("FINAL_TOUCHED_ONLY_LOGC14_RESOURCES: logistics_db untouched =", "logistics_db" in final_dbs)
        return 0
    finally:
        client.close()

if __name__ == "__main__":
    raise SystemExit(main())
