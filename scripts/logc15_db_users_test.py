"""Kiểm thử Mongo users store trên Atlas với database test riêng.

- Dùng chính credentials cấu hình của app (.streamlit/secrets.toml trên máy
  Owner, KHÔNG in ra ngoài).
- Chạy qua subprocess với MONGO_DB_NAME=logistics_workdesk_logc15 để toàn bộ
  core.database dùng DB test riêng, không chạm production.
- Chạy: create/read/update/soft-delete/hard-delete + index uniqueness + audit logs.
- Cuối cùng xóa toàn bộ collection trong database test — evidence in stdout.
"""
from __future__ import annotations

import subprocess
import sys


def main() -> int:
    test_db = "logistics_workdesk_logc15"
    env = {"MONGO_DB_NAME": test_db}
    result = subprocess.run(
        [sys.executable, "scripts/logc15_db_users_test_runner.py"],
        cwd=".",
        env={**__import__("os").environ, **env},
        timeout=600,
    )
    # Dù test có thất bại, vẫn dọn database test (an toàn vì chỉ chứa fixture).
    try:
        import core.database
        client = core.database.init_connection()
        if client is not None:
            db = client[test_db]
            dropped = []
            for cname in db.list_collection_names():
                db[cname].drop()
                dropped.append(cname)
            print(f"\nDọn database test {test_db}: đã xóa {len(dropped)} collection ({', '.join(dropped) or 'không có'})")
    except Exception as exc:  # noqa: BLE001
        print(f"\nDọn database test {test_db}: không xóa được — {type(exc).__name__}: {str(exc)[:150]}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
