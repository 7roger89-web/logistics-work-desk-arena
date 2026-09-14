"""Focused tests for LOGI_ATLAS_PILOT_COPY_01 — copy_production_to_pilot.py.

Prove, WITHOUT any real MongoDB or credentials, that the one-time
production -> pilot copy tool (``docs/goals/LOG-LG02/tools/
copy_production_to_pilot.py``):

  1. default (dry-run) performs NO destination writes
  2. never mutates the source (only read-only ops reach logistics_db)
  3. refuses a non-pristine pilot with PILOT_NOT_PRISTINE (no
     overwrite/merge/clean/drop)
  4. never copies the excluded collections (users, notification_outbox)
  5. documents retain representative BSON types (ObjectId, datetime, ...)
  6. included collection counts match source == pilot
  7. relevant (incl. unique) indexes are reproduced; automatic ``_id_`` is
     never recreated manually
  8. --execute is required for writes (CLI default is dry-run; without a
     credential the tool fails closed before any connection)
  9. source authority fail-closed: the source must contain customers +
     shipments; an empty or unrelated source exits 2 with zero pilot writes
     in BOTH dry-run and --execute (SOURCE_AUTHORITY_CHECK=PASS/FAIL)
 10. the pilot must be COMPLETELY pristine before --execute: zero collection
     names — even an existing EMPTY collection (e.g. empty users) is refused
     before anything is written (PILOT_NOT_PRISTINE)
 11. indexes are independently re-verified after the copy (name + ordered
     keys + unique; automatic ``_id_`` ignored); any mismatch exits 2

Transport for behavioural tests is the existing mongomock convention (see
views/logi_sandbox.py); source read-only discipline is additionally pinned
with call-recording fakes. Production is never used.

Run from the repo root:
    python3 -m unittest tests.test_logi_atlas_pilot_copy_01 -v
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "docs" / "goals" / "LOG-LG02" / "tools" / "copy_production_to_pilot.py"

SOURCE_DB = "logistics_db"
PILOT_DB = "logistics_pilot"


def _load_tool():
    spec = importlib.util.spec_from_file_location("copy_production_to_pilot_under_test", str(TOOL))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


tool = _load_tool()


# ---------------------------------------------------------------------------
# Call-recording fakes (source read-only discipline)
# ---------------------------------------------------------------------------

class FakeCursor:
    def __init__(self, docs: list):
        self._docs = list(docs)

    def limit(self, n):
        if n is not None:
            self._docs = self._docs[:n]
        return self

    def __iter__(self):
        return iter(self._docs)


class FakeCollection:
    """Records EVERY method call; write methods still work so accidental
    writes are observable and fail the assertions."""

    def __init__(self, name: str, docs: list | None = None, indexes: list | None = None):
        self.name = name
        self.docs = [dict(d) for d in (docs or [])]
        self.indexes = list(indexes) if indexes is not None else [{"name": "_id_", "key": [("_id", 1)]}]
        self.calls: list[str] = []

    # read-only ops (allowed against the source)
    def count_documents(self, _query):
        self.calls.append("count_documents")
        return len(self.docs)

    def find(self, _query=None):
        self.calls.append("find")
        return FakeCursor(self.docs)

    def find_one(self, _query):
        self.calls.append("find_one")
        return dict(self.docs[0]) if self.docs else None

    def list_indexes(self):
        self.calls.append("list_indexes")
        return [dict(i) for i in self.indexes]

    # write ops (must never be called on the SOURCE; they work for the pilot)
    def insert_one(self, doc):
        self.calls.append("insert_one")
        self.docs.append(dict(doc))

    def insert_many(self, docs):
        self.calls.append("insert_many")
        self.docs.extend(dict(d) for d in docs)

    def create_index(self, keys, name=None, unique=False):
        self.calls.append("create_index")
        self.indexes.append({"name": name, "key": list(keys), "unique": bool(unique)})

    def update_one(self, *a, **k):
        self.calls.append("update_one")

    def update_many(self, *a, **k):
        self.calls.append("update_many")

    def replace_one(self, *a, **k):
        self.calls.append("replace_one")

    def delete_one(self, *a, **k):
        self.calls.append("delete_one")

    def delete_many(self, *a, **k):
        self.calls.append("delete_many")

    def drop(self):
        self.calls.append("drop")
        self.docs = []

    def drop_index(self, *a, **k):
        self.calls.append("drop_index")

    def rename(self, *a, **k):
        self.calls.append("rename")


class FakeDb(dict):
    """Auto-creates a FakeCollection on first access, like pymongo."""

    def __init__(self):
        super().__init__()
        self.calls: list[str] = []

    def __getitem__(self, key):
        if key not in self:
            self[key] = FakeCollection(key)
        return super().__getitem__(key)

    def list_collection_names(self):
        self.calls.append("list_collection_names")
        return sorted(self.keys())


class FakeClient:
    def __init__(self):
        self._dbs: dict[str, FakeDb] = {}

    def __getitem__(self, db_name: str) -> FakeDb:
        if db_name not in self._dbs:
            self._dbs[db_name] = FakeDb()
        return self._dbs[db_name]


def _captured(fn, *args, **kwargs):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fn(*args, **kwargs)
    return code, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# mongomock fixtures (existing test transport for behavioural tests)
# ---------------------------------------------------------------------------

def _mongomock_client() -> "object":
    import mongomock
    return mongomock.MongoClient()


def _seed_source(client, now=None) -> dict:
    """Seed a representative production source. Returns the reference docs."""
    from bson import ObjectId

    now = now or datetime(2026, 9, 14, 8, 30, 0, 123456, tzinfo=timezone.utc)
    src = client[SOURCE_DB]

    ship1 = {
        "_id": ObjectId(),
        "id": "LO-0001",
        "status": "in_transit",
        "created_at": now,
        "updated_at": now,
        "data": {"3.4": {"details": [{"sku": "A1", "qty": 2, "price_in": 1250000.5}]}},
        "tags": ["pilot", "cn"],
        "version": 3,
        "paid": False,
        "note": None,
    }
    ship2 = {
        "_id": ObjectId(),
        "id": "LO-0002",
        "status": "done",
        "created_at": now,
        "updated_at": now,
    }
    ship3 = {"_id": ObjectId(), "id": "LO-0003", "status": "pending"}
    src["shipments"].insert_many([ship1, ship2, ship3])
    src["shipments"].create_index([("id", 1)], name="uq_shipment_id", unique=True)
    src["shipments"].create_index(
        [("status", 1), ("updated_at", -1)], name="ix_shipment_worklist"
    )

    src["customers"].insert_many(
        [
            {"_id": ObjectId(), "id": "CUST-1", "name": "Khách A", "created_at": now},
            {"_id": ObjectId(), "id": "CUST-2", "name": "Khách B"},
        ]
    )
    src["customers"].create_index([("id", 1)], name="uq_customer_id", unique=True)

    src["tasks"].insert_one({"_id": ObjectId(), "title": "review pilot", "created_at": now})
    # An existing but EMPTY source collection: must be copied as 0 docs and
    # verified 0 == 0. (mongomock registers a collection once it has an index.)
    src["legacy_historical_staging"].create_index(
        [("created_at", 1)], name="ix_created_at"
    )
    src["users"].insert_many(
        [
            {"_id": ObjectId(), "username": "u1"},
            {"_id": ObjectId(), "username": "u2"},
        ]
    )
    src["notification_outbox"].insert_one({"_id": ObjectId(), "event_id": "E-1"})
    return {"ship1": ship1}


# ---------------------------------------------------------------------------
# 1-2: dry-run no writes + source never mutated
# ---------------------------------------------------------------------------

class DryRunAndSourceReadOnlyTests(unittest.TestCase):
    def test_1_dry_run_performs_no_destination_writes(self):
        client = _mongomock_client()
        _seed_source(client)
        code, out, _err = _captured(tool.run, client, execute=False)
        self.assertEqual(code, 0)
        pilot = client[PILOT_DB]
        self.assertEqual(pilot.list_collection_names(), [], "dry-run must not create any pilot collection")
        self.assertIn("MODE=DRY_RUN", out)
        self.assertIn("SOURCE_DB=logistics_db", out)
        self.assertIn("DESTINATION_DB=logistics_pilot", out)
        self.assertIn("SOURCE_AUTHORITY_CHECK=PASS", out)
        self.assertIn("PILOT_PRECHECK=ABSENT", out)
        self.assertIn("SOURCE_COLLECTION_COUNT=6 (included=4, excluded=2)", out)
        self.assertIn("INCLUDE shipments: 3 docs, 3 indexes", out)
        self.assertIn("INCLUDE legacy_historical_staging: 0 docs, 2 indexes", out)
        self.assertIn("EXCLUDED users: 2 docs, 1 indexes", out)
        self.assertIn("EXCLUDED notification_outbox: 1 docs, 1 indexes", out)
        self.assertIn("NAMED shipments: FOUND 3 docs", out)
        self.assertIn("NAMED legacy_historical_staging: FOUND 0 docs", out)
        self.assertIn("NAMED contracts: ABSENT", out)
        self.assertIn("OK: dry-run complete (zero mutations).", out)
        self.assertNotIn("COPIED", out)

    def test_2_source_is_never_mutated(self):
        client = FakeClient()
        src = client[SOURCE_DB]
        src["shipments"] = FakeCollection(
            "shipments",
            docs=[{"_id": "s1", "id": "LO-1"}, {"_id": "s2", "id": "LO-2"}],
            indexes=[
                {"name": "_id_", "key": [("_id", 1)]},
                {"name": "uq_shipment_id", "key": [("id", 1)], "unique": True},
            ],
        )
        src["users"] = FakeCollection("users", docs=[{"_id": "u1"}])
        src["tasks"] = FakeCollection("tasks", docs=[{"_id": "t1"}])
        # customers: part of the minimum source authority
        src["customers"] = FakeCollection("customers", docs=[{"_id": "c1"}])
        before = {name: [dict(d) for d in coll.docs] for name, coll in src.items()}

        for execute in (False, True):
            _captured(tool.run, client, execute=execute)

        # Every source collection: ONLY read-only operations were called.
        for name, coll in src.items():
            self.assertTrue(
                set(coll.calls) <= tool.READ_ONLY_SOURCE_OPS,
                f"source collection {name!r} received non-read-only calls: {sorted(set(coll.calls))}",
            )
        self.assertEqual(set(src.calls), {"list_collection_names"})
        after = {name: [dict(d) for d in coll.docs] for name, coll in src.items()}
        self.assertEqual(before, after, "source documents changed")


# ---------------------------------------------------------------------------
# 3: non-pristine pilot is refused (B1: non-empty, B2: empty collection,
#    B3: empty users before any write, B4: pristine accepted)
# ---------------------------------------------------------------------------

def _run_failing(tc, client, execute):
    """Run the tool expecting a fail-closed SystemExit(2); return (out, err)."""
    err = io.StringIO()
    with contextlib.redirect_stdout(io.StringIO()) as out_buf, \
            contextlib.redirect_stderr(err):
        with tc.assertRaises(SystemExit) as ctx:
            tool.run(client, execute=execute)
    tc.assertEqual(ctx.exception.code, 2)
    return out_buf.getvalue(), err.getvalue()


class PilotPristineRefusalTests(unittest.TestCase):
    def test_b1_non_empty_pilot_refused_without_overwrite(self):
        client = _mongomock_client()
        _seed_source(client)
        existing = {"_id": "keep-me", "title": "prior pilot data"}
        client[PILOT_DB]["tasks"].insert_one(existing)

        out, err = _run_failing(self, client, execute=True)
        self.assertIn("PILOT_NOT_PRISTINE", out)
        self.assertIn("PILOT_NOT_PRISTINE tasks: 1 docs", out)
        self.assertIn("FAIL", err)
        self.assertIn(PILOT_DB, err)

        pilot = client[PILOT_DB]
        # No overwrite, no merge, no clean, no drop: prior data intact,
        # nothing else was created.
        self.assertEqual(pilot["tasks"].count_documents({}), 1)
        self.assertEqual(pilot["tasks"].find_one({"_id": "keep-me"})["title"], "prior pilot data")
        self.assertEqual(pilot.list_collection_names(), ["tasks"])

    def test_b2_empty_pilot_collection_refused(self):
        client = _mongomock_client()
        _seed_source(client)
        # A pilot collection that EXISTS but is EMPTY (materialized by an index).
        client[PILOT_DB]["tasks"].create_index([("title", 1)], name="ix_title")

        out, _err = _run_failing(self, client, execute=True)
        self.assertIn("PILOT_NOT_PRISTINE", out)
        self.assertIn("PILOT_NOT_PRISTINE tasks: 0 docs", out)

        pilot = client[PILOT_DB]
        # Refused BEFORE any write, and the existing collection was neither
        # dropped nor cleaned.
        self.assertEqual(pilot.list_collection_names(), ["tasks"])
        self.assertEqual(pilot["tasks"].count_documents({}), 0)
        self.assertIn("ix_title", [i["name"] for i in pilot["tasks"].list_indexes()])

    def test_b3_empty_users_refused_before_any_write(self):
        client = _mongomock_client()
        _seed_source(client)
        # An empty EXISTING users collection in the pilot.
        client[PILOT_DB]["users"].create_index([("username", 1)], name="ix_username")

        out, _err = _run_failing(self, client, execute=True)
        self.assertIn("PILOT_NOT_PRISTINE users: 0 docs", out)

        pilot = client[PILOT_DB]
        # Nothing else was written: no shipments/customers materialized.
        self.assertEqual(pilot.list_collection_names(), ["users"])

    def test_b4_pristine_pilot_accepted(self):
        client = _mongomock_client()
        _seed_source(client)
        code, out, _err = _captured(tool.run, client, execute=True)
        self.assertEqual(code, 0)
        self.assertIn("SOURCE_AUTHORITY_CHECK=PASS", out)
        self.assertIn("PILOT_PRECHECK=ABSENT", out)
        self.assertIn("OK: pilot copy complete.", out)


# ---------------------------------------------------------------------------
# 4-7: execute path on mongomock
# ---------------------------------------------------------------------------

class ExecuteCopyTests(unittest.TestCase):
    def setUp(self):
        self.client = _mongomock_client()
        self.refs = _seed_source(self.client)
        self.code, self.out, self.err = _captured(tool.run, self.client, execute=True)

    def test_4_excluded_collections_are_not_copied(self):
        self.assertEqual(self.code, 0)
        pilot_names = set(self.client[PILOT_DB].list_collection_names())
        self.assertNotIn("users", pilot_names)
        self.assertNotIn("notification_outbox", pilot_names)
        # The empty source collection exists in the pilot too (its index is
        # recreated, materializing it) and verifies 0 == 0.
        self.assertEqual(
            pilot_names,
            {"shipments", "customers", "tasks", "legacy_historical_staging"},
        )
        self.assertIn("VERIFY users in pilot=NO", self.out)
        self.assertIn("VERIFY notification_outbox in pilot=NO", self.out)

    def test_5_documents_retain_representative_bson_types(self):
        self.assertEqual(self.code, 0)
        from bson import ObjectId

        ship1 = self.refs["ship1"]
        back = self.client[PILOT_DB]["shipments"].find_one({"_id": ship1["_id"]})
        self.assertIsNotNone(back, "representative document missing in pilot")
        # The fidelity contract is pilot-read == source-read for the same doc
        # (both sides decoded by the same codec; MongoDB stores datetimes at
        # millisecond precision — the tool itself performs no transformation).
        back_src = self.client[SOURCE_DB]["shipments"].find_one({"_id": ship1["_id"]})
        for field in ("_id", "created_at", "updated_at", "data", "tags", "version", "paid", "note"):
            self.assertEqual(
                back[field], back_src[field], f"pilot value differs from source for {field}"
            )
            self.assertIs(type(back[field]), type(back_src[field]))
        # BSON types preserved (checked against the original Python values too).
        self.assertIsInstance(back["_id"], ObjectId)
        self.assertEqual(back["_id"], ship1["_id"])
        self.assertIsInstance(back["created_at"], datetime)
        self.assertIsInstance(back["updated_at"], datetime)
        # nested document / arrays / numbers / booleans / null
        self.assertEqual(back["data"], ship1["data"])
        self.assertIsInstance(back["data"]["3.4"]["details"][0]["qty"], int)
        self.assertIsInstance(back["data"]["3.4"]["details"][0]["price_in"], float)
        self.assertEqual(back["tags"], ["pilot", "cn"])
        self.assertIsInstance(back["version"], int)
        self.assertIs(back["paid"], False)
        self.assertIsNone(back["note"])
        self.assertIn("BSON shipments._id: MATCH (type=ObjectId)", self.out)
        self.assertIn("BSON shipments.created_at: MATCH (type=datetime)", self.out)
        self.assertIn("BSON shipments.updated_at: MATCH (type=datetime)", self.out)

    def test_6_included_collection_counts_match(self):
        self.assertEqual(self.code, 0)
        src, pilot = self.client[SOURCE_DB], self.client[PILOT_DB]
        for name in ("shipments", "customers", "tasks", "legacy_historical_staging"):
            self.assertEqual(
                pilot[name].count_documents({}),
                src[name].count_documents({}),
                f"count mismatch for {name}",
            )
            self.assertIn(f"VERIFY {name}: source=", self.out)
            self.assertIn("OK", self.out)
        self.assertNotIn("COUNT_MISMATCH", self.out)
        self.assertIn("SOURCE_MUTATIONS=0", self.out)
        # 4 collections materialized (empty one via its index), all 0==0 or n==n.
        self.assertIn("VERIFY legacy_historical_staging: source=0 pilot=0 OK", self.out)
        self.assertIn("PILOT_COLLECTION_COUNT=4", self.out)
        self.assertIn("OK: pilot copy complete.", self.out)
        # A3 (execute path) + C1 (matching indexes verify OK for every
        # included collection).
        self.assertIn("SOURCE_AUTHORITY_CHECK=PASS", self.out)
        for name in ("shipments", "customers", "tasks", "legacy_historical_staging"):
            self.assertIn(f"INDEX_VERIFY {name}: OK", self.out)

    def test_7_relevant_indexes_reproduced_and_id_index_not_manual(self):
        self.assertEqual(self.code, 0)
        src_coll = self.client[SOURCE_DB]["shipments"]
        pilot_coll = self.client[PILOT_DB]["shipments"]

        # Direct unit pin: copy_indexes never recreates the automatic _id_ index.
        copied = tool.copy_indexes(src_coll, pilot_coll)
        self.assertNotIn("_id_", copied)

        by_name = {i["name"]: i for i in pilot_coll.list_indexes()}
        self.assertIn("_id_", by_name)
        self.assertEqual(len([i for i in pilot_coll.list_indexes() if i["name"] == "_id_"]), 1)
        # unique index: keys + unique preserved
        self.assertIn("uq_shipment_id", by_name)
        self.assertEqual(dict(by_name["uq_shipment_id"]["key"]), {"id": 1})
        self.assertTrue(by_name["uq_shipment_id"].get("unique"))
        # non-unique compound index: keys + order preserved
        self.assertIn("ix_shipment_worklist", by_name)
        self.assertEqual(
            dict(by_name["ix_shipment_worklist"]["key"]),
            {"status": 1, "updated_at": -1},
        )
        self.assertFalse(by_name["ix_shipment_worklist"].get("unique", False))
        # customers unique index survived too
        cust_by_name = {i["name"]: i for i in self.client[PILOT_DB]["customers"].list_indexes()}
        self.assertTrue(cust_by_name["uq_customer_id"].get("unique"))
        self.assertIn("INDEX shipments: uq_shipment_id recreated", self.out)


# ---------------------------------------------------------------------------
# 9: source authority fail-closed (A1 zero source, A2 unrelated source,
#    A3 valid source passes)
# ---------------------------------------------------------------------------

class SourceAuthorityTests(unittest.TestCase):
    def test_a1_zero_source_fails_closed_with_zero_writes(self):
        client = _mongomock_client()
        # The source database exists but contains 0 collections.
        for execute in (False, True):
            out, err = _run_failing(self, client, execute=execute)
            self.assertIn("SOURCE_AUTHORITY_CHECK=FAIL", out)
            self.assertIn("0 collections", err)
        pilot = client[PILOT_DB]
        self.assertEqual(
            pilot.list_collection_names(), [],
            "an invalid source must not create any pilot collection",
        )

    def test_a2_unrelated_source_fails_closed_with_zero_writes(self):
        client = _mongomock_client()
        src = client[SOURCE_DB]
        src["orders"].insert_one({"_id": "o1", "total": 10})
        src["widgets"].insert_many([{"_id": "w1"}, {"_id": "w2"}])

        out, err = _run_failing(self, client, execute=True)
        self.assertIn("SOURCE_AUTHORITY_CHECK=FAIL", out)
        self.assertIn("missing required collection(s): customers, shipments", err)
        self.assertEqual(
            client[PILOT_DB].list_collection_names(), [],
            "an unrelated source must not produce any pilot write",
        )

    def test_a3_valid_source_with_customers_and_shipments_passes(self):
        client = _mongomock_client()
        _seed_source(client)
        code, out, _err = _captured(tool.run, client, execute=True)
        self.assertEqual(code, 0)
        self.assertIn("SOURCE_AUTHORITY_CHECK=PASS", out)
        self.assertIn("OK: pilot copy complete.", out)


# ---------------------------------------------------------------------------
# 11: post-copy index verification (C1 matching, C2 mismatch, C3 _id_ ignored)
# ---------------------------------------------------------------------------

class IndexVerificationTests(unittest.TestCase):
    def test_c2_deliberate_index_mismatch_fails_closed(self):
        client = _mongomock_client()
        _seed_source(client)
        # Sabotage: indexes are NOT recreated, so the independent
        # post-copy comparison must catch it.
        original = tool.copy_indexes
        tool.copy_indexes = lambda src_coll, dst_coll: []
        try:
            out, _err = _run_failing(self, client, execute=True)
        finally:
            tool.copy_indexes = original
        self.assertIn("INDEX_VERIFY shipments: MISMATCH", out)
        self.assertIn("uq_shipment_id: missing-in-pilot", out)
        self.assertNotIn("OK: pilot copy complete", out)

    def test_c3_id_index_ignored_in_verification(self):
        src_db = FakeDb()
        dst_db = FakeDb()
        src_db["shipments"] = FakeCollection(
            "shipments",
            docs=[{"_id": "s1"}],
            indexes=[
                {"name": "_id_", "key": [("_id", 1)]},
                {"name": "uq_shipment_id", "key": [("id", 1)], "unique": True},
            ],
        )
        # Deliberately different automatic _id_ spec on the pilot side:
        # it must be ignored by the comparison.
        dst_db["shipments"] = FakeCollection(
            "shipments",
            docs=[{"_id": "s1"}],
            indexes=[
                {"name": "_id_", "key": [("tenant_id", 1)]},
                {"name": "uq_shipment_id", "key": [("id", 1)], "unique": True},
            ],
        )
        rows = tool.verify_indexes(src_db, dst_db, ["shipments"])
        self.assertEqual(rows, [("shipments", True, "")])

    def test_c3b_key_order_and_uniqueness_are_compared(self):
        src_db = FakeDb()
        dst_db = FakeDb()
        src_db["shipments"] = FakeCollection(
            "shipments",
            docs=[{"_id": "s1"}],
            indexes=[
                {"name": "ix", "key": [("status", 1), ("updated_at", -1)], "unique": False},
            ],
        )
        # Same fields but reversed order / different unique => mismatch.
        dst_db["shipments"] = FakeCollection(
            "shipments",
            docs=[{"_id": "s1"}],
            indexes=[
                {"name": "ix", "key": [("updated_at", -1), ("status", 1)], "unique": True},
            ],
        )
        rows = tool.verify_indexes(src_db, dst_db, ["shipments"])
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0][1])
        self.assertIn("ix: spec differs", rows[0][2])


# ---------------------------------------------------------------------------
# 8: --execute is required for writes (CLI level)
# ---------------------------------------------------------------------------

class ExecuteFlagRequiredTests(unittest.TestCase):
    def _run_cli(self, args, env_extra=None):
        env = {k: v for k, v in os.environ.items() if k not in ("MONGO_URI", "LOGISTICS_PRO_SECRETS_FILE")}
        env["LOGISTICS_PRO_SECRETS_FILE"] = "/nonexistent/arena-no-secrets.toml"
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            [sys.executable, str(TOOL)] + args,
            capture_output=True, text=True, cwd=str(REPO), env=env, timeout=60,
        )

    def test_8_cli_help_documents_dry_run_default(self):
        proc = self._run_cli(["--help"])
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--execute", proc.stdout)
        self.assertIn("DRY RUN", proc.stdout)
        self.assertIn("PRECHECK", proc.stdout)

    def test_8_cli_default_and_execute_fail_closed_without_credential(self):
        # No MONGO_URI, no secrets file => the tool must fail BEFORE any
        # connection; neither the default (dry-run) nor --execute can write.
        for args in ([], ["--execute"]):
            proc = self._run_cli(args)
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertIn("FAIL", proc.stderr)
            self.assertNotIn("COPIED", proc.stdout)
            self.assertNotIn("OK: pilot copy complete", proc.stdout)

    def test_8_default_mode_is_not_execute(self):
        # The --execute flag must opt-in (store_true, default False) and
        # run()'s default keyword must be the dry-run path.
        text = TOOL.read_text(encoding="utf-8")
        self.assertIn('action="store_true"', text)
        self.assertIn("def run(client: Any, execute: bool = False) -> int:", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
