"""Headless bootstrap: tao tai khoan admin dau tien khong qua UI.

Dung duong code cua bootstrap UI (core.users.build_user_document +
core.database.save_user) voi database production trong secrets.toml.

Su dung:
    LOGISTICS_BOOTSTRAP_USERNAME=admin
    LOGISTICS_BOOTSTRAP_DISPLAY="Owner"
    LOGISTICS_BOOTSTRAP_EMAIL=owner@example.com
    LOGISTICS_BOOTSTRAP_PASSWORD=********
    LOGISTICS_PRO_SECRETS_FILE=/duong/dan/.streamlit/secrets.toml \
    python3 docs/goals/LOG-LG02/tools/headless_bootstrap.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))


def main() -> int:
    username = os.environ.get("LOGISTICS_BOOTSTRAP_USERNAME", "").strip().lower()
    display_name = os.environ.get("LOGISTICS_BOOTSTRAP_DISPLAY", "").strip()
    email = os.environ.get("LOGISTICS_BOOTSTRAP_EMAIL", "").strip().lower()
    password = os.environ.get("LOGISTICS_BOOTSTRAP_PASSWORD", "")

    if not (username and display_name and password):
        print("THIEU bien moi truong BOOTSTRAP (username/display/password).")
        return 2

    if len(password) < 8:
        print("Mat khau toi thieu 8 ky tu.")
        return 3

    from core.users import build_user_document, UserError
    from core.database import save_user, load_users

    if load_users():
        print("DA CO TAI KHOAN. Bootstrap chi chay khi users rong. BO QUA.")
        return 0

    try:
        document = build_user_document(
            username=username,
            password=password,
            display_name=display_name,
            role="admin",
            created_by="bootstrap-headless",
            email=email or None,
        )
    except UserError as exc:
        print(f"LOI build_user_document: {exc}")
        return 4

    if not save_user(document):
        print("KHONG LUU DUOC tai khoan (kiem tra ket noi production).")
        return 5

    after = len(load_users())
    print(f"OK: tao tai khoan '{username}' thanh cong. users count = {after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
