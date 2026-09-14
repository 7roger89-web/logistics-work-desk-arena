"""One-time safe copy: logistics_db (production) -> logistics_pilot.

LOGI_ATLAS_PILOT_COPY_01 — the smallest possible live DB-to-DB snapshot copy.
It reuses the credential conventions of export_production.py (same secrets file
resolution, same MONGO_URI fallback). It is NOT an ETL: documents are copied
AS-IS through pymongo, so BSON values (ObjectId, datetime, nested documents,
arrays, numbers, null, booleans) keep their types. No normalization, no
schema changes, no derived values. UNKNOWN stays UNKNOWN.

Usage (from the repo root):

    python docs/goals/LOG-LG02/tools/copy_production_to_pilot.py            # DRY RUN / PRECHECK (default)
    python docs/goals/LOG-LG02/tools/copy_production_to_pilot.py --execute  # actual copy

Safety contract (fail closed):

* SOURCE (logistics_db) is touched ONLY with read-only operations:
  list_collection_names, count_documents, find, list_indexes.
* DESTINATION (logistics_pilot) is inspected BEFORE any write. If it already
  contains ANY document in ANY collection the tool STOPS with
  PILOT_NOT_EMPTY (collection names + counts) — no overwrite, no merge,
  no clean, no drop.
* Default mode is DRY RUN / PRECHECK: it connects, inventories the source
  and prechecks the pilot, and performs ZERO writes. Actual writes require
  the explicit ``--execute`` flag.
* ``users`` and ``notification_outbox`` are NEVER copied and must not exist
  in the pilot afterwards (verified after the copy).
* For each included source collection the non-automatic indexes are
  recreated in the pilot (keys + unique + name). Mongo's automatic ``_id_``
  index is never recreated manually.
* After the copy, every included collection is verified: SOURCE_COUNT ==
  PILOT_COUNT, plus a representative-document BSON spot check on
  ``_id`` / ``created_at`` / ``updated_at`` (where present).
* On any error or verification mismatch the tool exits 2 (FAIL).

Credentials: MONGO_URI environment variable and/or the existing secrets file
used by the app (``.streamlit/secrets.toml``, or
``LOGISTICS_PRO_SECRETS_FILE`` for another existing local path). The URI is
never printed. Never commit credentials.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Iterable

try:
    import tomllib  # Python 3.11+
except ImportError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
STREAMLIT_SECRETS = os.path.join(APP_ROOT, ".streamlit", "secrets.toml")

SOURCE_DB = "logistics_db"
DESTINATION_DB = "logistics_pilot"
EXCLUDED_COLLECTIONS = frozenset({"users", "notification_outbox"})
NAMED_CHECK_COLLECTIONS = [
    "customers",
    "shipments",
    "contracts",
    "audit_logs",
    "legacy_historical_staging",
    "legacy_historical_review_actions",
    "proxy_payments",
    "tasks",
]
BSON_SPOT_FIELDS = ("_id", "created_at", "updated_at")
# The only operations this tool may ever run against the SOURCE database.
READ_ONLY_SOURCE_OPS = frozenset(
    {"list_collection_names", "count_documents", "find", "list_indexes"}
)

_MISSING = object()


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(2)


def _secrets_path() -> str:
    explicit = os.getenv("LOGISTICS_PRO_SECRETS_FILE", "").strip()
    if explicit:
        return os.path.expanduser(explicit)
    return STREAMLIT_SECRETS


def _load_uri() -> str:
    """Same credential resolution as export_production.py. Never prints the URI."""
    path = _secrets_path()
    uri = ""
    if os.path.exists(path):
        try:
            with open(path, "rb") as fh:
                secrets = tomllib.load(fh)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            fail(f"Không đọc được secrets: {exc}")
        mongo = secrets.get("mongodb") or secrets.get("mongo") or {}
        uri = str(mongo.get("uri") or "").strip()
    uri = uri or os.environ.get("MONGO_URI", "").strip()
    if not uri:
        fail(
            "Không có [mongo].uri trong secrets / MONGO_URI. Đặt biến môi trường "
            "MONGO_URI hoặc LOGISTICS_PRO_SECRETS_FILE trỏ tới secrets hiện có."
        )
    return uri


def _index_key_pairs(key: Any) -> list[tuple[str, int]]:
    """Normalize list_indexes() key shape (pymongo: list of pairs; mongomock: dict)."""
    if isinstance(key, dict):
        return list(key.items())
    return list(key)


def pilot_precheck(pilot_db: Any) -> tuple[str, list[tuple[str, int]]]:
    """Inspect the pilot before any write.

    Returns (status, occupants) where status is one of:
      "ABSENT"    — the pilot database has no collections at all;
      "EMPTY"     — collections exist but every one holds 0 documents;
      "NOT_EMPTY" — occupants lists (collection_name, doc_count) for every
                    collection that already contains documents.
    Read-only.
    """
    names = sorted(pilot_db.list_collection_names())
    occupants: list[tuple[str, int]] = []
    for name in names:
        count = pilot_db[name].count_documents({})
        if count > 0:
            occupants.append((name, count))
    if occupants:
        return "NOT_EMPTY", occupants
    return ("EMPTY" if names else "ABSENT"), []


def source_inventory(src_db: Any) -> list[dict[str, Any]]:
    """Read-only inventory: every source collection with doc count + index specs."""
    inventory: list[dict[str, Any]] = []
    for name in sorted(src_db.list_collection_names()):
        coll = src_db[name]
        inventory.append(
            {
                "name": name,
                "count": coll.count_documents({}),
                "indexes": [
                    {
                        "name": idx.get("name"),
                        "key": idx.get("key"),
                        "unique": bool(idx.get("unique", False)),
                    }
                    for idx in coll.list_indexes()
                ],
            }
        )
    return inventory


def copy_collection(src_coll: Any, dst_coll: Any) -> int:
    """Copy one collection AS-IS (no transformation) and return the doc count."""
    docs = list(src_coll.find())
    if docs:
        dst_coll.insert_many(docs)
    return len(docs)


def copy_indexes(src_coll: Any, dst_coll: Any) -> list[str]:
    """Recreate the source collection's non-automatic indexes in the destination.

    Preserves keys, the unique property and the index name. Mongo's automatic
    ``_id_`` index is never recreated manually.
    """
    copied: list[str] = []
    for idx in src_coll.list_indexes():
        name = idx.get("name")
        if not name or name == "_id_":
            continue
        dst_coll.create_index(
            _index_key_pairs(idx.get("key") or {}),
            name=name,
            unique=bool(idx.get("unique", False)),
        )
        copied.append(name)
    return copied


def verify_collection_counts(
    src_db: Any, dst_db: Any, names: Iterable[str]
) -> list[tuple[str, int, int, bool]]:
    """SOURCE_COUNT == PILOT_COUNT for every included collection (read-only)."""
    rows: list[tuple[str, int, int, bool]] = []
    for name in names:
        source_count = src_db[name].count_documents({})
        pilot_count = dst_db[name].count_documents({})
        rows.append((name, source_count, pilot_count, source_count == pilot_count))
    return rows


def bson_spot_check(
    src_db: Any, dst_db: Any, names: Iterable[str]
) -> list[tuple[str, str, Any, bool]]:
    """Representative-document BSON fidelity check (read-only).

    For each non-empty included collection, the first source document is
    re-read from the pilot by ``_id`` and the values of ``_id`` /
    ``created_at`` / ``updated_at`` (where present) must be equal AND of the
    same type. Returns (collection, field, source_value, matched).
    """
    results: list[tuple[str, str, Any, bool]] = []
    for name in names:
        src_coll = src_db[name]
        src_doc = next(iter(src_coll.find().limit(1)), None)
        if src_doc is None:
            continue
        dst_doc = dst_db[name].find_one({"_id": src_doc["_id"]})
        if dst_doc is None:
            results.append((name, "_doc", src_doc.get("_id"), False))
            continue
        for field in BSON_SPOT_FIELDS:
            if field not in src_doc:
                continue
            src_value = src_doc[field]
            dst_value = dst_doc.get(field, _MISSING)
            matched = (
                dst_value is not _MISSING
                and dst_value == src_value
                and type(dst_value) is type(src_value)
            )
            results.append((name, field, src_value, matched))
    return results


def _report_pilot_not_empty(occupants: list[tuple[str, int]]) -> None:
    print("PILOT_NOT_EMPTY")
    for name, count in occupants:
        print(f"PILOT_NOT_EMPTY {name}: {count} docs")
    fail(
        f"{DESTINATION_DB} đã chứa document — KHÔNG ghi đè, KHÔNG merge, "
        "KHÔNG clean, KHÔNG drop. Hủy thao tác."
    )


def run(client: Any, execute: bool = False) -> int:
    """Run the copy (or the dry-run precheck) against an already-connected client."""
    src_db = client[SOURCE_DB]
    pilot_db = client[DESTINATION_DB]

    print(f"MODE={'EXECUTE' if execute else 'DRY_RUN'}")
    print(f"SOURCE_DB={SOURCE_DB}")
    print(f"DESTINATION_DB={DESTINATION_DB}")

    status, occupants = pilot_precheck(pilot_db)
    if status == "NOT_EMPTY":
        _report_pilot_not_empty(occupants)
    print(f"PILOT_PRECHECK={'ABSENT' if status == 'ABSENT' else 'EMPTY'}")

    inventory = source_inventory(src_db)
    included = [c for c in inventory if c["name"] not in EXCLUDED_COLLECTIONS]
    if not inventory:
        print("WARN: source database có 0 collection — kiểm tra lại connection.")
    print(
        f"SOURCE_COLLECTION_COUNT={len(inventory)} "
        f"(included={len(included)}, excluded={len(inventory) - len(included)})"
    )
    for c in inventory:
        label = "EXCLUDED" if c["name"] in EXCLUDED_COLLECTIONS else "INCLUDE"
        print(f"{label} {c['name']}: {c['count']} docs, {len(c['indexes'])} indexes")
    for name in NAMED_CHECK_COLLECTIONS:
        match = next((c for c in inventory if c["name"] == name), None)
        if match is not None:
            print(f"NAMED {name}: FOUND {match['count']} docs")
        else:
            print(f"NAMED {name}: ABSENT")

    if not execute:
        print("OK: dry-run complete (zero mutations).")
        return 0

    # ---- write phase: writes go to DESTINATION_DB only ----
    try:
        # Re-inspect immediately before the first write (fail closed).
        status, occupants = pilot_precheck(pilot_db)
        if status == "NOT_EMPTY":
            _report_pilot_not_empty(occupants)

        for c in included:
            copied = copy_collection(src_db[c["name"]], pilot_db[c["name"]])
            print(f"COPIED {c['name']}: {copied} docs")
        for c in included:
            for index_name in copy_indexes(src_db[c["name"]], pilot_db[c["name"]]):
                print(f"INDEX {c['name']}: {index_name} recreated")

        included_names = [c["name"] for c in included]
        rows = verify_collection_counts(src_db, pilot_db, included_names)
        for name, source_count, pilot_count, ok in rows:
            print(
                f"VERIFY {name}: source={source_count} pilot={pilot_count} "
                f"{'OK' if ok else 'COUNT_MISMATCH'}"
            )

        pilot_names = set(pilot_db.list_collection_names())
        for name in sorted(EXCLUDED_COLLECTIONS):
            present = name in pilot_names
            print(f"VERIFY {name} in pilot={'YES' if present else 'NO'}")

        spot = bson_spot_check(src_db, pilot_db, included_names)
        for name, field, src_value, matched in spot:
            print(
                f"BSON {name}.{field}: {'MATCH' if matched else 'MISMATCH'} "
                f"(type={type(src_value).__name__})"
            )

        bad_counts = [r for r in rows if not r[3]]
        bad_spot = [r for r in spot if not r[3]]
        leaked = sorted(n for n in EXCLUDED_COLLECTIONS if n in pilot_names)
        if bad_counts or bad_spot or leaked:
            fail(
                f"Verification failed: counts={bad_counts}, bson={bad_spot}, "
                f"excluded_leaked={leaked}. SOURCE_MUTATIONS=0 (source untouched)."
            )

        print(f"PILOT_COLLECTION_COUNT={len(pilot_db.list_collection_names())}")
        print("SOURCE_MUTATIONS=0")
        print("OK: pilot copy complete.")
    except Exception as exc:  # fail closed: stop on any unexpected error
        fail(f"Copy thất bại (fail-closed, không viết tiếp): {exc}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "One-time safe copy logistics_db -> logistics_pilot. "
            "Default: DRY RUN / PRECHECK (zero writes); --execute performs the copy."
        )
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Thực hiện copy thật vào logistics_pilot (mặc định chỉ DRY RUN / PRECHECK).",
    )
    args = parser.parse_args(argv)

    uri = _load_uri()

    try:
        from pymongo import MongoClient
        from pymongo.errors import PyMongoError
    except ImportError:
        fail("Thiếu pymongo/bson. Chạy: pip install -r requirements.txt")

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        client.admin.command("ping")
    except PyMongoError as exc:
        fail(f"Không kết nối được MongoDB: {exc}")

    try:
        return run(client, execute=args.execute)
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
