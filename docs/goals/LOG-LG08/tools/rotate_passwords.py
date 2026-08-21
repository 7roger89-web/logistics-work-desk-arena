#!/usr/bin/env python3
"""LG08 — Xoay mật khẩu sau khi lộ plaintext trong tài liệu (2026-08-21).

Xoay mật khẩu cho sami và fiona (tài khoản bị ghi plaintext trong
final_report.md đã commit). admin và 7roger do chính Owner giữ nên không đổi.

Cách dùng: đặt LOGISTICS_SAMI_NEW và LOGISTICS_FIONA_NEW trước khi chạy.
"""
from __future__ import annotations

import os

from core.auth import hash_password
from core.config import validate_mongo_identity
from core.database import load_users, save_user


def rotate(username: str) -> str:
    key = f"LOGISTICS_{username.upper()}_NEW"
    new_pw = os.environ.get(key, "").strip()
    if not new_pw:
        raise SystemExit(f"Thiếu biến môi trường {key}")
    if len(new_pw) < 8:
        raise SystemExit(f"Mật khẩu mới cho {username} phải >= 8 ký tự")
    users = load_users()
    doc = None
    for u in users.values():
        if str(u.get("username")).lower() == username.lower():
            doc = dict(u)
            break
    if doc is None:
        raise SystemExit(f"Không tìm thấy user {username}")
    doc["password_hash"] = hash_password(new_pw)
    doc["updated_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    doc["updated_by"] = "lg08_rotate"
    ok = save_user(doc)
    return "OK" if ok else "FAIL"


if __name__ == "__main__":
    validate_mongo_identity()
    print("sami :", rotate("sami"))
    print("fiona:", rotate("fiona"))
