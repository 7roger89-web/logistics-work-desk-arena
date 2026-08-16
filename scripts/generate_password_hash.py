"""Sinh password hash để dán vào .streamlit/secrets.toml."""
from __future__ import annotations

import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.auth import hash_password

if __name__ == "__main__":
    password = getpass.getpass("Mật khẩu: ")
    confirm = getpass.getpass("Nhập lại: ")
    if password != confirm:
        raise SystemExit("Mật khẩu không khớp.")
    print(hash_password(password))
