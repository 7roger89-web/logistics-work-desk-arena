"""LOG-C15 step 1: Ownership evidence for LOG-C14 test resources.

Checks Atlas cluster reachable with current secrets.toml credentials:
- whether database 'logistics_workdesk_logc14' exists and its collections,
- whether DB user 'logc14test' exists for this cluster.

Does NOT print credentials, password hashes or connection strings with
userinfo. Only structural evidence.
"""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

TARGET_DB = "logistics_workdesk_logc14"
TARGET_USER = "logc14test"

ROOT = Path(__file__).resolve().parents[1]

# Secrets resolution mirrors core/config.py ordering:
# env var > secrets.toml (project root .streamlit)
import os  # noqa: E402

from pymongo import MongoClient  # noqa: E402

_explicit = os.getenv("LOGISTICS_PRO_SECRETS_FILE", "").strip()
_secrets_file = Path(_explicit).expanduser() if _explicit else (ROOT / ".streamlit" / "secrets.toml")

def main() -> int:
    with _secrets_file.open("rb") as handle:
        payload = tomllib.load(handle)
    mongo_cfg = payload.get("mongo", {})
    uri = mongo_cfg.get("uri") or payload.get("MONGO_URI", "")
    if not uri:
        print("NO_MONGO_URI_CONFIGURED")
        return 2

    if "logc14" not in uri.lower():
        print("URI_NOT_LOGC14_CLUSTER — cannot prove ownership; stopping.")
        return 2

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=15000, appName="logc15-cleanup-check")
        client.admin.command("ping")
    except Exception as exc:  # noqa: BLE001
        print(f"CONNECTION_FAILED: {type(exc).__name__}")
        return 2

    try:
        dbs = [db["name"] for db in client.list_databases(nameOnly=True)]
        has_target_db = TARGET_DB in dbs
        print(f"Databases on cluster: {sorted(dbs)}")
        print(f"TARGET_DB_EXISTS ({TARGET_DB}): {has_target_db}")

        colls: list[str] = []
        if has_target_db:
            db = client[TARGET_DB]
            colls = sorted(db.list_collection_names())
        print(f"TARGET_DB_COLLECTIONS: {colls}")

        users: list[str] = []
        try:
            admin_db_users = client.admin.command("usersInfo", 1)
            users = [u["user"] for u in admin_db_users.get("users", [])]
        except Exception as exc:  # noqa: BLE001
            print(f"USERSINFO_FAILED: {type(exc).__name__} (current credential may lack admin privilege)")
        print(f"Cluster users: {users}")
        print(f"TARGET_USER_EXISTS ({TARGET_USER}): {TARGET_USER in users}")

        # Cross-check: the current credential's own user identity
        identity = client.admin.command("connectionStatus")
        authed = identity.get("authInfo", {})
        print("CURRENT_CRED_USER:", authed.get("authenticatedUsers"))
        print("CURRENT_CRED_ROLES:", authed.get("authenticatedUserRoles"))
        return 0
    finally:
        client.close()

if __name__ == "__main__":
    raise SystemExit(main())
