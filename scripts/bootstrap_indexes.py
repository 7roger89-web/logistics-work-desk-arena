"""Tạo toàn bộ index cần thiết trên MongoDB."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import ensure_indexes, get_last_db_error

if __name__ == "__main__":
    if not ensure_indexes():
        raise SystemExit(get_last_db_error() or "Không thể tạo index. Kiểm tra kết nối MongoDB.")
    print("Đã tạo/kiểm tra index thành công.")
