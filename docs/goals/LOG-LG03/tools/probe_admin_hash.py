"""Read-only probe: test candidate passwords against production admin hash.

Does NOT modify any data. Prints only PASS/FAIL results, never prints any hash.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from pymongo import MongoClient  # noqa: E402

import streamlit as st  # noqa: E402
from streamlit.runtime.scriptrunner import get_script_run_ctx  # noqa: E402

import core.auth as auth  # noqa: E402

CANDIDATES = [
    "1123456",
    "7roger89",
    "Qazqaz12",
]


def main() -> int:
    import tomllib

    secrets_path = Path(__file__).resolve().parents[4] / ".streamlit" / "secrets.toml"
    secrets = tomllib.load(secrets_path.open("rb"))
    client = MongoClient(secrets["mongo"]["uri"], serverSelectionTimeoutMS=15000)
    db = client[secrets["mongo"]["database"]]
    users = list(db.users.find({"username": "admin"}, {"password_hash": 1}))
    if not users:
        print("NO_ADMIN_USER_FOUND")
        return 1
    stored = users[0]["password_hash"]
    print(f"candidates tested: {len(CANDIDATES)}")
    for candidate in CANDIDATES:
        ok = auth.verify_password(candidate, stored)
        print(f"candidate={candidate!r} -> {'MATCH' if ok else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
