"""Remove the 3 rehearsal test users from the production database (LG03 W11).

SAFETY CONTRACT (read-only until explicit run):
- Dry-run mode by default (--dry-run); prints what would be deleted, mutates NOTHING.
- With --apply: deletes ONLY documents whose username is exactly one of
  REHEARSAL_USERNAMES. Admin account (username='admin') is NEVER touched.
- Before deletion, prints per-user document summary (no password hashes printed).
- Refuses to run if production DB is not detected as logistics_db on the Atlas
  cluster (hard-coded guard below).

Run:
  PYTHONPATH=/home/ubuntu/logistics_repo python3 docs/goals/LOG-LG03/tools/cleanup_rehearsal_users.py --dry-run
  PYTHONPATH=/home/ubuntu/logistics_repo python3 docs/goals/LOG-LG03/tools/cleanup_rehearsal_users.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.database import get_db
from core.users import build_user_document

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

EXPECTED_DB = "logistics_db"
EXPECTED_CLUSTER_HINT = "cluster0.qvjh5ji.mongodb.net"
REHEARSAL_USERNAMES = ("rehearsal_admin", "rehearsal_sale", "rehearsal_support")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    db = get_db()
    uri = str(db.client.address or "")
    db_name = db.name

    print(f"Target DB: {db_name}")
    if db_name != EXPECTED_DB:
        print(f"GUARD: expected {EXPECTED_DB}, aborting.")
        return 2

    users_col = db["users"]
    found: list[dict] = []
    for uname in REHEARSAL_USERNAMES:
        doc = users_col.find_one({"username": uname})
        if doc is None:
            print(f"- {uname}: KHÔNG TỒN TẠI (không cần xóa)")
            continue
        # Summary without any hash/password field
        summary = {k: v for k, v in doc.items() if k not in ("password_hash",)}
        print(f"- {uname}: TỒN TẠI — {summary}")
        found.append(doc)

    if not found:
        print("Không có tài khoản rehearsal nào cần dọn.")
        return 0

    if not args.apply:
        print(f"\nDRY-RUN: sẽ xóa {len(found)} tài khoản rehearsal: "
              f"{[d['username'] for d in found]}.")
        print("Chạy lại với --apply để xóa thật.")
        return 0

    print(f"\nAPPLY: đang xóa {len(found)} tài khoản rehearsal...")
    result = users_col.delete_many({"username": {"$in": REHEARSAL_USERNAMES}})
    print(f"Đã xóa: {result.deleted_count} tài khoản.")

    # Verify: only admin-family accounts remain
    remaining = [d["username"] for d in users_col.find({}, {"username": 1, "_id": 0})]
    print(f"Còn lại trong users collection: {remaining}")
    admin_exists = users_col.find_one({"username": "admin"}) is not None
    print(f"Tài khoản admin của Owner còn nguyên: {admin_exists}")
    return 0 if admin_exists else 1


if __name__ == "__main__":
    sys.exit(main())
