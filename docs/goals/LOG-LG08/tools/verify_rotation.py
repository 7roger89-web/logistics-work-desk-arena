#!/usr/bin/env python3
"""LG08 — Đọc ngược sau xoay mật khẩu: chứng minh mật khẩu cũ bị từ chối."""
import sys

sys.path.insert(0, ".")
from core.config import validate_mongo_identity
from core.database import load_users
from core.users import authenticate

validate_mongo_identity()
users = load_users()
checks = [
    ("sami", "Sami2026!", False),      # mật khẩu cũ — phải FAIL
    ("sami", "Sami2026New!", True),    # mật khẩu mới — phải PASS
    ("fiona", "Fiona2026!", False),    # cũ — FAIL
    ("fiona", "Fiona2026New!", True),  # mới — PASS
    ("admin", "7roger899", True),      # không đổi — PASS
    ("7roger", "7roger899", True),     # không đổi — PASS
]
all_ok = True
for uname, pw, expect in checks:
    doc = None
    for u in users.values():
        if str(u.get("username")).lower() == uname.lower():
            doc = u
            break
    result = authenticate(doc, pw) is not None if doc else False
    status = "OK" if result == expect else "FAIL"
    if status == "FAIL":
        all_ok = False
    print(f"{uname} ({pw}): got={result} expect={expect} -> {status}")
print("ALL_PASS" if all_ok else "SOME_FAIL")
