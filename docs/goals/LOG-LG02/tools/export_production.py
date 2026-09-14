"""Pre-release production backup exporter for LOG-LG02.

Run on the Owner's machine where a Streamlit secrets file already contains the
application connection string (same config the Streamlit app uses). By default
this is .streamlit/secrets.toml; set LOGISTICS_PRO_SECRETS_FILE to use another
existing local secrets path without copying credentials into this repo.

Usage (from the repo root):
    python docs/goals/LOG-LG02/tools/export_production.py

Output (docs/goals/LOG-LG02/backups/<timestamp>/):
    metadata.json          backup manifest (db, collections, counts, timestamps, digests)
    <collection>.jsonl     one document per line, MongoDB Canonical Extended JSON
    schema/<collection>.json   first document sample shape + index spec

This script is READ-ONLY against the database: it only runs countDocuments,
list_indexes, and find(). It exports logistics_db only (production authority).

NOT committed to Git via backup dir (backups/ is gitignored). Credentials never
leave the Owner's machine.
"""
import json
import os
import sys
from datetime import datetime, timezone

try:
    import tomllib  # Python 3.11+
except ImportError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
STREAMLIT_SECRETS = os.path.join(APP_ROOT, ".streamlit", "secrets.toml")
BACKUP_ROOT = os.path.join(APP_ROOT, "docs", "goals", "LOG-LG02", "backups")
PROD_DB = "logistics_db"
EXPECTED_ALLOWED = ["logistics_workdesk_logc14", "logistics_workdesk_LG01_E2E", "logistics_db"]
SERIALIZATION = "mongodb_extended_json_canonical_v1"


def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(2)


def _secrets_path() -> str:
    explicit = os.getenv("LOGISTICS_PRO_SECRETS_FILE", "").strip()
    if explicit:
        return os.path.expanduser(explicit)
    return STREAMLIT_SECRETS


def main() -> None:
    secrets_path = _secrets_path()
    if not os.path.exists(secrets_path):
        fail(
            f"Không tìm thấy {secrets_path}. Đặt LOGISTICS_PRO_SECRETS_FILE tới "
            "secrets hiện có hoặc chạy trong repo có .streamlit/secrets.toml."
        )

    try:
        with open(secrets_path, "rb") as fh:
            secrets = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        fail(f"Không đọc được secrets: {exc}")

    mongo = secrets.get("mongodb") or secrets.get("mongo") or {}
    uri = (mongo.get("uri") or os.environ.get("MONGO_URI", "")).strip()
    db_name = (
        mongo.get("database")
        or os.environ.get("MONGO_DB_NAME", "")
    ).strip()

    if not uri:
        fail("Không có [mongo].uri / MONGO_URI trong secrets.")

    if db_name != PROD_DB:
        print(
            f"WARN: secrets đang trỏ tới db_name={db_name!r}, nhưng backup authority là "
            f"{PROD_DB!r}. Script sẽ kết nối URI và xuất database {PROD_DB} "
            f"(URI không chứa tên db hoặc sẽ được ghi đè bằng {PROD_DB}).",
            file=sys.stderr,
        )

    try:
        from bson import json_util
        from pymongo import MongoClient
        from pymongo.errors import PyMongoError
    except ImportError:
        fail("Thiếu pymongo/bson. Chạy: pip install -r requirements.txt")

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        db = client[PROD_DB]
        if PROD_DB not in EXPECTED_ALLOWED:
            fail(f"{PROD_DB} không nằm trong MONGO_ALLOWED_DB_NAMES của ứng dụng.")
        client.admin.command("ping")
    except PyMongoError as exc:
        fail(f"Không kết nối được MongoDB: {exc}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = os.path.join(BACKUP_ROOT, f"prod_backup_{stamp}")
    schema_dir = os.path.join(out_dir, "schema")
    os.makedirs(schema_dir, exist_ok=True)

    collections = sorted(db.list_collection_names())
    manifest = {
        "goal": "LOG-LG02",
        "purpose": "pre-release production backup (R2)",
        "cluster": "cluster0.qvjh5ji.mongodb.net (Atlas free tier, no Atlas-managed backup)",
        "db": PROD_DB,
        "serialization": SERIALIZATION,
        "export_timestamp_utc": stamp,
        "script": "docs/goals/LOG-LG02/tools/export_production.py",
        "collections": [],
        "total_documents": 0,
    }

    for cname in collections:
        coll = db[cname]
        count = coll.count_documents({})
        jsonl_path = os.path.join(out_dir, f"{cname}.jsonl")
        written = 0
        first_doc_shape = None
        with open(jsonl_path, "w", encoding="utf-8") as fh:
            for doc in coll.find():
                if first_doc_shape is None:
                    first_doc_shape = {k: type(v).__name__ for k, v in doc.items()}
                fh.write(
                    json_util.dumps(
                        doc,
                        json_options=json_util.CANONICAL_JSON_OPTIONS,
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                written += 1
        indexes = [
            {"name": idx["name"], "key": idx["key"], "unique": idx.get("unique", False)}
            for idx in coll.list_indexes()
        ]
        if first_doc_shape:
            with open(os.path.join(schema_dir, f"{cname}.json"), "w", encoding="utf-8") as fh:
                json.dump({"keys": first_doc_shape, "indexes": indexes}, fh,
                          ensure_ascii=False, indent=2)
        manifest["collections"].append({
            "name": cname,
            "count_exported": written,
            "count_documents": count,
            "indexes": len(indexes),
            "file": f"{cname}.jsonl",
            "ok": written == count,
        })
        manifest["total_documents"] += written

    manifest_path = os.path.join(out_dir, "metadata.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    print(f"OK: export hoàn tất -> {out_dir}")
    print(f"    serialization: {SERIALIZATION}")
    print(f"    collections: {len(collections)}, total documents: {manifest['total_documents']}")
    for c in manifest["collections"]:
        flag = "OK" if c["ok"] else "MISMATCH"
        print(f"    {flag} {c['name']}: {c['count_exported']}/{c['count_documents']} docs")

    client.close()


if __name__ == "__main__":
    main()
