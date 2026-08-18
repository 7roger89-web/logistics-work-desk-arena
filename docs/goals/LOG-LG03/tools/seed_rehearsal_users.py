#!/usr/bin/env python3
"""LG03: Seeding tai khoan test (sale/support/admin) vao rehearsal DB.
DUNG CHAY tren production — chi dung cho DB rehearsal local (logistics_workdesk_LG01_E2E).

Su dung:
    PYTHONPATH=/home/ubuntu/logistics_repo python3 docs/goals/LOG-LG03/tools/seed_rehearsal_users.py
"""
from __future__ import annotations

import sys
from pymongo import MongoClient

from core.users import build_user_document

REHEARSAL_URI = "mongodb://localhost:27017/"
REHEARSAL_DB = "logistics_workdesk_LG01_E2E"
_PRODUCTION_DB_NAMES = frozenset({"logistics_db"})

ROLE_MAP = {
    "admin": {"display_name": "Nguoi quan tri", "email": "admin@rehearsal.local"},
    "sale": {"display_name": "Nhan vien Sales", "email": "sale@rehearsal.local"},
    "support": {"display_name": "Nhan vien Ho tro", "email": "support@rehearsal.local"},
}

PASSWORD = "Rehearsal2026!"


def main() -> None:
    client = MongoClient(REHEARSAL_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")  # verify local connection early
    db = client[REHEARSAL_DB]

    assert REHEARSAL_DB not in _PRODUCTION_DB_NAMES, "NEVER seed a production DB name"
    collections = db.list_collection_names()
    users_col = db.users if "users" in collections else db.create_collection("users")
    before = users_col.count_documents({})

    created = 0
    for role, meta in ROLE_MAP.items():
        username = f"rehearsal_{role}"
        if users_col.find_one({"username": username}):
            print(f"SKIP: {username} da ton tai")
            continue
        doc = build_user_document(
            username=username,
            display_name=meta["display_name"],
            email=meta["email"],
            role=role,
            password=PASSWORD,
        )
        users_col.insert_one(doc)
        created += 1
        print(f"OK: {username} ({role}) da tao")

    after = users_col.count_documents({})
    print(f"users: {before} -> {after}")
    if after != before + created:
        print(f"FAIL: count mismatch (expected {before + created}, got {after})")
        sys.exit(1)
    print("CHECKPOINT_SEED_USERS: PASS")


if __name__ == "__main__":
    main()
