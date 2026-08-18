#!/usr/bin/env python3
"""LG03: Seeding tai khoan test (sale/support/admin) vao rehearsal DB.

DUNG CHAY tren production — chi dung cho DB rehearsal local.
Dung core.users.build_user_document + core.database.save_user (duong giong bootstrap UI).
Su dung:
    python3 docs/goals/LOG-LG03/tools/seed_rehearsal_users.py
"""
from __future__ import annotations

from pymongo import MongoClient

from core.users import build_user_document
from core.database import save_user

ROLE_MAP = {
    "admin": {"display_name": "Nguoi quan tri", "email": "admin@rehearsal.local"},
    "sale": {"display_name": "Nhan vien Sales", "email": "sale@rehearsal.local"},
    "support": {"display_name": "Nhan vien Ho tro", "email": "support@rehearsal.local"},
}

BASELINE: dict[str, int] = {}


def current_counts() -> dict[str, int]:
    client = MongoClient("mongodb://localhost:27017/")
    db = client.logistics_workdesk_LG01_E2E
    return {"users": db.users.count_documents({}) if "users" in db.list_collection_names() else 0}


def main() -> None:
    counts = current_counts()
    for role, meta in ROLE_MAP.items():
        username = f"rehearsal_{role}"
        doc = build_user_document(
            username=username,
            display_name=meta["display_name"],
            email=meta["email"],
            role=role,
            password="Rehearsal2026!",
        )
        save_user(doc)
        print(f"OK: {username} ({role}) da tao")
    after = current_counts()
    expected = counts["users"] + 3
    assert after["users"] == expected, f"FAIL: users={after['users']} expected {expected}"
    print(f"CHECKPOINT_SEED_USERS: PASS (users={after['users']})")


if __name__ == "__main__":
    main()
