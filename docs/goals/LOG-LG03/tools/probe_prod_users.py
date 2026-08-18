"""Read-only diagnostic: inspect production users collection metadata only.

Prints usernames, roles, active flags, created_by — NEVER prints any hash or
credential material. Used to verify whether rehearsal seed polluted production.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from pymongo import MongoClient  # noqa: E402

FIELD_MAP = {
    "username": "username",
    "role": "role",
    "active": "active",
    "created_by": "created_by",
    "deactivated_by": "deactivated_by",
}


def main() -> int:
    import tomllib

    secrets_path = Path(__file__).resolve().parents[4] / ".streamlit" / "secrets.toml"
    secrets = tomllib.load(secrets_path.open("rb"))
    client = MongoClient(secrets["mongo"]["uri"], serverSelectionTimeoutMS=15000)
    db = client[secrets["mongo"]["database"]]
    users = list(
        db.users.find(
            {},
            {k: 1 for k in FIELD_MAP},
        )
    )
    print(f"production users count: {len(users)}")
    for u in users:
        print(
            f"- username={u.get('username')!r} role={u.get('role')!r} "
            f"active={u.get('active')} created_by={u.get('created_by')!r} "
            f"deactivated_by={u.get('deactivated_by')!r}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
