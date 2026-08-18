"""Pre-approved rollback importer for LOG-LG02.

DANGER: this script MUTATES the target database. It is for RESTORE/ROLLBACK use
only, after explicit Owner decision during an incident.

Usage (from the repo root):
    python docs/goals/LOG-LG02/tools/restore_production.py --backup-dir <path>

By default imports into logistics_db (production authority). Use
--target-db <name> for a restore rehearsal on an isolated DB (e.g.
logistics_workdesk_LG01_E2E) to verify the procedure without touching
production.

Credentials come from the same .streamlit/secrets.toml used by the app.
"""
import argparse
import json
import os
import sys

import toml

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
STREAMLIT_SECRETS = os.path.join(APP_ROOT, ".streamlit", "secrets.toml")

PROD_DB = "logistics_db"
REHEARSAL_DBS = ["logistics_workdesk_LG01_E2E", "logistics_workdesk_logc14"]


def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(2)


def confirm():
    raw = input("Xác nhận import vào database? Gõ chính xác 'ROLLBACK CONFIRM': ").strip()
    if raw != "ROLLBACK CONFIRM":
        print("Đã hủy thao tác (không gõ đúng token xác nhận).", file=sys.stderr)
        sys.exit(0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup-dir", required=True, help="Đường dẫn tới thư mục backup (chứa metadata.json)")
    parser.add_argument("--target-db", default=None, help="DB đích (mặc định logistics_db)")
    parser.add_argument("--no-confirm", action="store_true", help="Bỏ qua xác nhận (chỉ dùng tự động hóa có kiểm soát)")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ kiểm tra tính hợp lệ của backup và thủ tục, KHÔNG import")
    args = parser.parse_args()

    meta_path = os.path.join(args.backup_dir, "metadata.json")
    if not os.path.exists(meta_path):
        fail(f"Không tìm thấy {meta_path}. Chỉ định --backup-dir trỏ tới thư mục chứa metadata.json.")

    secrets = toml.load(STREAMLIT_SECRETS)
    mongo = secrets.get("mongodb") or secrets.get("mongo") or {}
    uri = (mongo.get("uri") or os.environ.get("MONGO_URI", "")).strip()
    if not uri:
        fail("Không có [mongo].uri / MONGO_URI trong secrets.")

    target = (args.target_db or PROD_DB).strip()
    if target not in REHEARSAL_DBS + [PROD_DB]:
        fail(f"Target db {target!r} không hợp lệ (chỉ cho phép {PROD_DB} hoặc các TEST db {REHEARSAL_DBS}).")

    if target == PROD_DB and not args.no_confirm and not args.dry_run:
        confirm()

    from pymongo import MongoClient
    from pymongo.errors import PyMongoError

    client = None
    db = None
    if not args.dry_run:
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=10000)
            db = client[target]
            client.admin.command("ping")
        except PyMongoError as exc:
            fail(f"Không kết nối được MongoDB: {exc}")

    with open(meta_path, encoding="utf-8") as fh:
        meta = json.load(fh)

    print(f"OK: {"DRY-RUN: thủ tục import vào db=" if args.dry_run else "import vào db="}{target}")
    for coll_meta in meta["collections"]:
        src = os.path.join(args.backup_dir, coll_meta["file"])
        if args.dry_run:
            print(f"    [dry-run] {coll_meta['name']}: {coll_meta['count_exported']} docs sẽ được import")
            continue
        coll = db[coll_meta["name"]]
        if not coll_meta.get("indexes"):
            continue
        for idx in coll.list_indexes():
            if idx["name"] != "_id_":
                try:
                    coll.drop_index(idx["name"])
                except PyMongoError:
                    pass
        imported = 0
        if os.path.exists(src):
            coll.drop()
            with open(src, encoding="utf-8") as fh:
                for line in fh:
                    doc = json.loads(line)
                    coll.insert_one(doc)
                    imported += 1
            # Restore index structure
            with open(os.path.join(args.backup_dir, "schema", f"{coll_meta['name']}.json"), encoding="utf-8") as fh:
                idx_spec = json.load(fh)["indexes"]
            for idx in idx_spec:
                if idx["name"] != "_id_":
                    coll.create_index(list(idx["key"].items()), name=idx["name"],
                                      unique=idx.get("unique", False))
        print(f"    {coll_meta['name']}: imported {imported} docs, expected {coll_meta['count_exported']}")
    if client is not None:
        client.close()
    print("OK: restore hoàn tất.")


if __name__ == "__main__":
    main()
