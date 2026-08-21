#!/usr/bin/env python3
"""LG08 — Đọc ngược sau xoay mật khẩu: chứng minh mật khẩu cũ bị từ chối."""
import sys

sys.path.insert(0, ".")
from core.config import validate_mongo_identity
from core.database import load_users
from core.users import authenticate

validate_mongo_identity()
users = load_users()
# Mật khẩu cũ của sami/fiona đã bị lộ trong tài liệu và ĐÃ XÓA khỏi repo.
# Test đọc ngược sử dụng env vars để không đưa literal vào source:
# LOGISTICS_SAMI_OLD / LOGISTICS_SAMI_NEW / LOGISTICS_FIONA_OLD / LOGISTICS_FIONA_NEW / LOGISTICS_OWNER_PW
import os

checks = [
    ("sami", os.environ.get("LOGISTICS_SAMI_OLD", "").strip(), False),      # cũ — FAIL
    ("sami", os.environ.get("LOGISTICS_SAMI_NEW", "").strip(), True),       # mới — PASS
    ("fiona", os.environ.get("LOGISTICS_FIONA_OLD", "").strip(), False),   # cũ — FAIL
    ("fiona", os.environ.get("LOGISTICS_FIONA_NEW", "").strip(), True),    # mới — PASS
    ("admin", os.environ.get("LOGISTICS_OWNER_PW", "").strip(), True),     # Owner-kept — PASS
    ("7roger", os.environ.get("LOGISTICS_OWNER_PW", "").strip(), True),    # Owner-kept — PASS
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
