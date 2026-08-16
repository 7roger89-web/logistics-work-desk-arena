"""Kiểm tra cấu hình mà không in giá trị bí mật.

Chạy từ thư mục gốc dự án:
    python scripts/check_config.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import (
    GEMINI_API_KEYS,
    GEMINI_MODEL,
    MONGO_DB_NAME,
    MONGO_URI,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
    get_loaded_secrets_path,
)


def _yes(value: object) -> str:
    return "Có" if bool(value) else "Không"


def run() -> int:
    secrets_path = get_loaded_secrets_path()
    print("LOGISTICS PRO - CONFIG CHECK")
    print(f"Secrets file: {secrets_path or 'Không tìm thấy'}")
    print(f"MongoDB URI configured: {_yes(MONGO_URI)}")
    print(f"MongoDB database: {MONGO_DB_NAME}")
    print(f"Telegram configured: {_yes(TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)}")
    print(f"Gemini key count: {len(GEMINI_API_KEYS)}")
    print(f"Gemini model: {GEMINI_MODEL}")

    if not MONGO_URI:
        print("ERROR: Chưa có [mongo].uri hoặc MONGO_URI trong secrets.toml.")
        return 2

    try:
        from core.database import get_db, get_last_db_error
    except ModuleNotFoundError as exc:
        print(f"ERROR: Thiếu thư viện {exc.name}. Chạy: python -m pip install -r requirements.txt")
        return 5

    db = get_db()
    if db is None:
        print(f"ERROR: {get_last_db_error() or 'Không thể kết nối MongoDB.'}")
        return 3

    try:
        db.command("ping")
    except Exception as exc:
        print(f"ERROR: MongoDB ping thất bại: {type(exc).__name__}: {exc}")
        return 4

    print("MongoDB connection: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
