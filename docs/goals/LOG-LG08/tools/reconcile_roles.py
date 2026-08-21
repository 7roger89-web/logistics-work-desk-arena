#!/usr/bin/env python3
"""LG08 — Đối chiếu vai trò người dùng theo chính sách Owner phê duyệt 2026-08-21.

Chính sách được phê duyệt (Owner xác nhận "CHẤP NHẬN"):
admin = admin, 7roger = sale, sami = support, fiona = support.
"""
from __future__ import annotations

import datetime

from core.config import validate_mongo_identity
from core.database import get_db, load_users, update_user
from core.users import normalize_role

POLICY = {"admin": "admin", "7roger": "sale", "sami": "support", "fiona": "support"}
ACTOR = "lg08_owner_2026-08-21"


def reconcile() -> None:
    db = get_db()
    before = {u.get("username"): u.get("role") for u in load_users().values()}
    for uname, target in POLICY.items():
        target = normalize_role(target)
        if before.get(uname) == target:
            print(f"{uname}: role {target} — đã khớp, không đổi")
            continue
        now = datetime.datetime.now(datetime.UTC).isoformat()
        ok = update_user(
            uname,
            payload={"role": target, "role_updated_at": now, "role_updated_by": ACTOR},
            actor=ACTOR,
        )
        print(f"{uname}: {before.get(uname)} -> {target} — {'OK' if ok else 'FAIL'}")
    after = {u.get("username"): u.get("role") for u in load_users().values()}
    for uname, target in POLICY.items():
        status = "MATCH" if after.get(uname) == normalize_role(target) else "MISMATCH"
        print(f"read-back {uname}: {after.get(uname)} — {status}")


if __name__ == "__main__":
    validate_mongo_identity()
    reconcile()
