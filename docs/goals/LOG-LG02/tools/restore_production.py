"""Pre-approved one-time snapshot importer (LOG-LG02), extended for the pilot.

DANGER: this script MUTATES the target database. It is for RESTORE/ROLLBACK and
one-time pilot snapshot use only, after explicit Owner decision.

Usage (from the repo root):

    python docs/goals/LOG-LG02/tools/restore_production.py \
        --backup-dir <PROD_BACKUP_DIR> \
        --target-db logistics_pilot \
        --exclude-collection users \
        --exclude-collection notification_outbox \
        --dry-run

Then, only after Owner Gate, the same command without ``--dry-run``.

Behaviour:

* By default imports into ``logistics_db`` (production authority), which always
  requires the typed confirmation token (or ``--no-confirm`` under controlled
  automation). Production confirmation is NOT weakened.
* ``--target-db`` now also accepts ``logistics_pilot`` (the STAGING pilot
  snapshot target) alongside the historical non-production rehearsal databases.
  Any other target is rejected before any connection.
* ``--exclude-collection`` is repeatable (and comma-separated). Excluded
  collections are never dropped, never created/restored, are reported as
  ``SKIPPED``, and are excluded from ``--dry-run`` output too.
* ``--dry-run`` prints the plan (target, included collections, skipped
  exclusions) and performs zero database connection and zero mutation, so it
  requires no secrets.
* New controlled exports marked ``mongodb_extended_json_canonical_v1`` are
  decoded through PyMongo's BSON Extended JSON codec so ObjectId/datetime and
  other BSON values keep their types. Older plain-JSON backups remain readable.

Credentials come from the same ``.streamlit/secrets.toml`` used by the app.
Only the existing JSONL + metadata.json + schema/ + pymongo restore path is
reused; no new backup format or dependency is introduced.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Iterable, Mapping

try:
    import tomllib  # Python 3.11+
except ImportError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
STREAMLIT_SECRETS = os.path.join(APP_ROOT, ".streamlit", "secrets.toml")

PROD_DB = "logistics_db"
NON_PROD_DBS = [
    "logistics_workdesk_LG01_E2E",
    "logistics_workdesk_logc14",
    "logistics_pilot",
]
ALLOWED_TARGET_DBS = [PROD_DB] + NON_PROD_DBS

CONFIRMATION_TOKEN = "ROLLBACK CONFIRM"
EXTENDED_JSON_SERIALIZATION = "mongodb_extended_json_canonical_v1"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(2)


def requires_confirmation(target: str, no_confirm: bool = False, dry_run: bool = False) -> bool:
    """Production write boundary."""
    return target == PROD_DB and not no_confirm and not dry_run


def confirm() -> None:
    try:
        raw = input(
            f"Xác nhận import vào database? Gõ chính xác '{CONFIRMATION_TOKEN}': "
        ).strip()
    except EOFError:
        raw = ""
    if raw != CONFIRMATION_TOKEN:
        print("Đã hủy thao tác (không gõ đúng token xác nhận).", file=sys.stderr)
        sys.exit(0)


def parse_exclusions(exclude_args: Iterable[str] | None) -> frozenset[str]:
    """Normalize repeatable / comma-separated ``--exclude-collection`` values."""
    excluded: set[str] = set()
    for item in exclude_args or []:
        for part in str(item).split(","):
            name = part.strip()
            if name:
                excluded.add(name)
    return frozenset(excluded)


def validate_target(target: str | None) -> str:
    target = (target or PROD_DB).strip()
    if target not in ALLOWED_TARGET_DBS:
        fail(
            f"Target db {target!r} không hợp lệ (chỉ cho phép {PROD_DB} hoặc "
            f"các database non-production {NON_PROD_DBS})."
        )
    return target


def load_metadata(backup_dir: str) -> dict[str, Any]:
    meta_path = os.path.join(backup_dir, "metadata.json")
    if not os.path.exists(meta_path):
        fail(
            f"Không tìm thấy {meta_path}. Chỉ định --backup-dir trỏ tới thư mục "
            "chứa metadata.json."
        )
    with open(meta_path, encoding="utf-8") as fh:
        return json.load(fh)


def plan_collections(meta: Mapping[str, Any], excluded: frozenset[str]) -> list[tuple[dict[str, Any], bool]]:
    """Return (collection_meta, is_excluded) for every collection in the manifest."""
    return [
        (coll_meta, str(coll_meta.get("name", "")) in excluded)
        for coll_meta in meta.get("collections", [])
        if isinstance(coll_meta, Mapping)
    ]


def _clear_non_id_indexes(coll: Any) -> None:
    """Best-effort removal of non-``_id`` indexes."""
    try:
        for idx in coll.list_indexes():
            name = idx.get("name") if isinstance(idx, dict) else getattr(idx, "name", None)
            if name and name != "_id_":
                try:
                    coll.drop_index(name)
                except Exception:
                    pass
    except Exception:
        pass


def _decode_jsonl_document(line: str, serialization: str) -> dict[str, Any]:
    """Decode one backup line, preserving BSON types for new Extended JSON backups."""
    if serialization == EXTENDED_JSON_SERIALIZATION:
        try:
            from bson import json_util
        except ImportError as exc:
            raise RuntimeError(
                "Backup dùng MongoDB Extended JSON nhưng môi trường thiếu bson/pymongo."
            ) from exc
        decoded = json_util.loads(line)
    else:
        decoded = json.loads(line)
    if not isinstance(decoded, dict):
        raise ValueError("Backup JSONL phải chứa một document object trên mỗi dòng.")
    return decoded


def _restore_collection(
    coll: Any,
    backup_dir: str,
    coll_meta: Mapping[str, Any],
    serialization: str = "",
) -> int:
    """Drop + reinsert one collection from its JSONL file, then recreate indexes."""
    src = os.path.join(backup_dir, str(coll_meta.get("file", "")))
    imported = 0
    if os.path.exists(src):
        _clear_non_id_indexes(coll)
        coll.drop()
        with open(src, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                coll.insert_one(_decode_jsonl_document(line, serialization))
                imported += 1
        schema_path = os.path.join(backup_dir, "schema", f"{coll_meta.get('name')}.json")
        if os.path.exists(schema_path):
            with open(schema_path, encoding="utf-8") as fh:
                idx_spec = json.load(fh).get("indexes", [])
            for idx in idx_spec:
                name = idx.get("name")
                key = idx.get("key")
                if name and name != "_id_" and isinstance(key, dict):
                    coll.create_index(list(key.items()), name=name, unique=bool(idx.get("unique", False)))
    return imported


def restore_backup(
    db: Any,
    backup_dir: str,
    meta: Mapping[str, Any],
    excluded: frozenset[str] = frozenset(),
) -> dict[str, tuple[str, int]]:
    """Import every manifest collection into ``db`` except those in ``excluded``."""
    results: dict[str, tuple[str, int]] = {}
    serialization = str(meta.get("serialization") or "")
    for coll_meta, skipped in plan_collections(meta, excluded):
        name = str(coll_meta.get("name", ""))
        if skipped:
            results[name] = ("skipped", 0)
            continue
        imported = _restore_collection(
            db[name],
            backup_dir,
            coll_meta,
            serialization=serialization,
        )
        results[name] = ("imported", imported)
    return results


def _secrets_path() -> str:
    explicit = os.getenv("LOGISTICS_PRO_SECRETS_FILE", "").strip()
    if explicit:
        return os.path.expanduser(explicit)
    return STREAMLIT_SECRETS


def _load_uri() -> str:
    path = _secrets_path()
    if not os.path.exists(path):
        fail(f"Không tìm thấy {path}. Chạy script này tại repo gốc của ứng dụng.")
    try:
        with open(path, "rb") as fh:
            secrets = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        fail(f"Không đọc được secrets: {exc}")

    mongo = secrets.get("mongodb") or secrets.get("mongo") or {}
    uri = (mongo.get("uri") or os.environ.get("MONGO_URI", "")).strip()
    if not uri:
        fail("Không có [mongo].uri / MONGO_URI trong secrets.")
    return uri


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup-dir", required=True,
                        help="Đường dẫn tới thư mục backup (chứa metadata.json)")
    parser.add_argument("--target-db", default=None,
                        help="DB đích (mặc định logistics_db). Chấp nhận logistics_pilot và các database rehearsal non-production.")
    parser.add_argument("--exclude-collection", action="append", default=None,
                        help="Collection cần BỎ QUA khi restore (lặp lại được, hoặc phân cách bằng dấu phẩy). VD: --exclude-collection users --exclude-collection notification_outbox")
    parser.add_argument("--no-confirm", action="store_true",
                        help="Bỏ qua xác nhận (chỉ dùng tự động hóa có kiểm soát)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Chỉ in kế hoạch (target/includes/skips), KHÔNG kết nối DB, KHÔNG import")
    args = parser.parse_args(argv)

    target = validate_target(args.target_db)
    excluded = parse_exclusions(args.exclude_collection)
    meta = load_metadata(args.backup_dir)
    plan = plan_collections(meta, excluded)

    if args.dry_run:
        print("DRY-RUN: no database connection, no mutation.")
        print(f"TARGET_DB={target}")
        print("SERIALIZATION=" + str(meta.get("serialization") or "legacy_plain_json"))
        excluded_list = sorted(excluded)
        print("EXCLUDED_COLLECTIONS=" + (",".join(excluded_list) if excluded_list else "(none)"))
        for coll_meta, skipped in plan:
            name = str(coll_meta.get("name", ""))
            if skipped:
                print(f"SKIPPED {name} (excluded)")
            else:
                print(f"INCLUDE {name}: {coll_meta.get('count_exported', '?')} docs")
        print("OK: dry-run complete (zero mutations).")
        return 0

    uri = _load_uri()

    if requires_confirmation(target, args.no_confirm, args.dry_run):
        confirm()

    try:
        from pymongo import MongoClient
        from pymongo.errors import PyMongoError
    except ImportError:
        fail("Thiếu pymongo. Chạy: pip install pymongo")

    client = None
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        db = client[target]
        client.admin.command("ping")
    except PyMongoError as exc:
        fail(f"Không kết nối được MongoDB: {exc}")

    print(f"IMPORT TARGET_DB={target}")
    print("SERIALIZATION=" + str(meta.get("serialization") or "legacy_plain_json"))
    for name in sorted(excluded):
        print(f"SKIPPED {name} (excluded)")

    results = restore_backup(db, args.backup_dir, meta, excluded)
    for coll_meta, skipped in plan:
        name = str(coll_meta.get("name", ""))
        if skipped:
            continue
        status, count = results.get(name, ("unknown", 0))
        expected = coll_meta.get("count_exported", "?")
        print(f"IMPORTED {name}: {count} docs, expected {expected}")

    if client is not None:
        client.close()
    print("OK: restore hoàn tất.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
