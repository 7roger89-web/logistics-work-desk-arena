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
* SOURCE AUTHORITY: before ANY destination write (and also in dry-run) the
  source must be a plausible logistics source: the collections ``customers``
  and ``shipments`` must exist (presence only — counts are not pinned). An
  empty or unrelated database fails closed: SOURCE_AUTHORITY_CHECK=FAIL,
  exit 2, zero destination writes.
* DESTINATION (logistics_pilot) is inspected BEFORE any write (and re-checked
  immediately before the first write). The only allowed pre-write state is a
  COMPLETELY PRISTINE pilot: zero collection names. If ANY collection exists
  — even an empty one — the tool STOPS with PILOT_NOT_PRISTINE (collection
  names + counts): no overwrite, no merge, no clean, no drop.
* Default mode is DRY RUN / PRECHECK: it connects, runs the fail-closed
  prechecks and inventories the source, and performs ZERO writes. Actual
  writes require the explicit ``--execute`` flag.
* ``users`` and ``notification_outbox`` are NEVER copied and must not exist
  in the pilot afterwards (verified after the copy).
* For each included source collection the non-automatic indexes are
  recreated in the pilot (keys + unique + name), then independently verified
  after the copy (INDEX_VERIFY <collection>: OK, exit 2 on mismatch). Mongo's
  automatic ``_id_`` index is never recreated manually and is ignored in the
  comparison.
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
# Minimum source authority: a valid logistics source must contain these
# collections (presence only — document counts may legitimately change).
REQUIRED_SOURCE_COLLECTIONS = frozenset({"customers", "shipments"})
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


def check_source_authority(src_db: Any) -> tuple[bool, str]:
    """Fail-closed minimum source authority (read-only).

    The source must be a plausible logistics source: it may not be empty and
    must contain every collection in REQUIRED_SOURCE_COLLECTIONS. Presence
    only — no document counts are hardcoded (counts may legitimately change).
    Returns (ok, reason).
    """
    names = set(src_db.list_collection_names())
    if not names:
        return False, "source database contains 0 collections"
    missing = sorted(REQUIRED_SOURCE_COLLECTIONS - names)
    if missing:
        return False, "source missing required collection(s): " + ", ".join(missing)
    return True, "required collections present: " + ", ".join(sorted(REQUIRED_SOURCE_COLLECTIONS))


def check_pilot_pristine(pilot_db: Any) -> tuple[bool, list[tuple[str, int]]]:
    """The only allowed pre-write destination state: ZERO collection names.

    Returns (pristine, evidence) where evidence lists (collection_name,
    doc_count) for every existing collection — including empty ones.
    Read-only.
    """
    names = sorted(pilot_db.list_collection_names())
    evidence = [(name, pilot_db[name].count_documents({})) for name in names]
    return len(names) == 0, evidence


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


def _index_spec_map(coll: Any) -> dict[str, tuple]:
    """Non-automatic index name -> (ordered key pairs, unique) for one collection."""
    specs: dict[str, tuple] = {}
    for idx in coll.list_indexes():
        name = idx.get("name")
        if not name or name == "_id_":
            continue
        specs[name] = (
            tuple(tuple(pair) for pair in _index_key_pairs(idx.get("key") or {})),
            bool(idx.get("unique", False)),
        )
    return specs


def verify_indexes(
    src_db: Any, dst_db: Any, names: Iterable[str]
) -> list[tuple[str, bool, str]]:
    """Independent post-copy index comparison for every included collection.

    Compares index name, ordered key specification and the unique boolean,
    ignoring Mongo's automatic ``_id_`` index on both sides. Returns
    (collection, matched, detail) rows.
    """
    results: list[tuple[str, bool, str]] = []
    for name in names:
        src_specs = _index_spec_map(src_db[name])
        dst_specs = _index_spec_map(dst_db[name])
        if src_specs == dst_specs:
            results.append((name, True, ""))
            continue
        detail: list[str] = []
        for index_name in sorted(set(src_specs) | set(dst_specs)):
            src_spec, dst_spec = src_specs.get(index_name), dst_specs.get(index_name)
            if dst_spec is None:
                detail.append(f"{index_name}: missing-in-pilot")
            elif src_spec is None:
                detail.append(f"{index_name}: extra-in-pilot")
            else:
                detail.append(f"{index_name}: spec differs")
        results.append((name, False, "; ".join(detail)))
    return results


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


def _fail_source_authority(reason: str) -> None:
    print("SOURCE_AUTHORITY_CHECK=FAIL")
    fail(
        f"SOURCE_AUTHORITY_CHECK=FAIL: {reason}. "
        "Source không phải logistics source hợp lệ — KHÔNG ghi gì vào destination."
    )


def _fail_pilot_not_pristine(evidence: list[tuple[str, int]]) -> None:
    print("PILOT_NOT_PRISTINE")
    for name, count in evidence:
        print(f"PILOT_NOT_PRISTINE {name}: {count} docs")
    fail(
        f"{DESTINATION_DB} không pristine (trạng thái duy nhất được phép trước write: "
        "0 collection) — KHÔNG drop, KHÔNG clean, KHÔNG ghi đè, KHÔNG merge. "
        "Hủy thao tác."
    )


def run(client: Any, execute: bool = False) -> int:
    """Run the copy (or the dry-run precheck) against an already-connected client."""
    src_db = client[SOURCE_DB]
    pilot_db = client[DESTINATION_DB]

    print(f"MODE={'EXECUTE' if execute else 'DRY_RUN'}")
    print(f"SOURCE_DB={SOURCE_DB}")
    print(f"DESTINATION_DB={DESTINATION_DB}")

    # Fail-closed prechecks (applied in dry-run AND execute).
    ok, reason = check_source_authority(src_db)
    if not ok:
        _fail_source_authority(reason)
    print("SOURCE_AUTHORITY_CHECK=PASS")

    ok, evidence = check_pilot_pristine(pilot_db)
    if not ok:
        _fail_pilot_not_pristine(evidence)
    print("PILOT_PRECHECK=ABSENT")

    inventory = source_inventory(src_db)
    included = [c for c in inventory if c["name"] not in EXCLUDED_COLLECTIONS]
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
        # Re-establish the preconditions immediately before the first write
        # (fail closed).
        ok, evidence = check_pilot_pristine(pilot_db)
        if not ok:
            _fail_pilot_not_pristine(evidence)
        ok, reason = check_source_authority(src_db)
        if not ok:
            _fail_source_authority(reason)

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

        idx_rows = verify_indexes(src_db, pilot_db, included_names)
        for name, matched, detail in idx_rows:
            print(
                f"INDEX_VERIFY {name}: {'OK' if matched else 'MISMATCH'}"
                + (f" ({detail})" if detail else "")
            )

        spot = bson_spot_check(src_db, pilot_db, included_names)
        for name, field, src_value, matched in spot:
            print(
                f"BSON {name}.{field}: {'MATCH' if matched else 'MISMATCH'} "
                f"(type={type(src_value).__name__})"
            )

        bad_counts = [r for r in rows if not r[3]]
        bad_indexes = [r for r in idx_rows if not r[1]]
        bad_spot = [r for r in spot if not r[3]]
        leaked = sorted(n for n in EXCLUDED_COLLECTIONS if n in pilot_names)
        if bad_counts or bad_indexes or bad_spot or leaked:
            fail(
                f"Verification failed: counts={bad_counts}, indexes={bad_indexes}, "
                f"bson={bad_spot}, excluded_leaked={leaked}. "
                "SOURCE_MUTATIONS=0 (source untouched)."
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
