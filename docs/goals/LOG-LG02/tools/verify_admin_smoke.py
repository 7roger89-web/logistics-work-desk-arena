"""Smoke xac minh tai khoan admin da tao trong production (read-only)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from core.database import load_users
from core.users import verify_password

users = load_users()
assert isinstance(users, dict) and users, "users rong"
u = next(iter(users.values()))
print("users:", len(users), "| username:", u.get("username"),
      "| role:", u.get("role"), "| created_by:", u.get("created_by"))

wrong = verify_password(u, "XyZ-1234-wrong-pwd")
assert wrong is False, "wrong password phai fail"
print("wrong-password verify =", wrong, "(OK phai la False)")
print("SMOKE_ADMIN_OK")
