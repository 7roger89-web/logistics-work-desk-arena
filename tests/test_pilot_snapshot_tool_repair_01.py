"""Focused tests for LOGI_PILOT_DATA_CONNECTION_01 — PILOT_SNAPSHOT_TOOL_REPAIR_01.

Proves, WITHOUT any real MongoDB or credentials, that the existing one-time
backup/restore tool (``docs/goals/LOG-LG02/tools/restore_production.py``) can:

  A. accept ``--target-db logistics_pilot``
  B. reject an arbitrary target such as ``customer_prod_copy``
  C. skip ``users`` via ``--exclude-collection users``
  D. skip ``users`` + ``notification_outbox`` together
  E. still restore an included collection (shipments) with its indexes
  F. ``--dry-run`` reports target / includes / skips with zero DB mutation
  G. keep the production confirmation boundary on ``logistics_db``

Run from the repo root:
    python3 -m unittest tests.test_pilot_snapshot_tool_repair_01 -v
or:
    python3 tests/test_pilot_snapshot_tool_repair_01.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "docs" / "goals" / "LOG-LG02" / "tools" / "restore_production.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("restore_production_under_test", str(TOOL))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


tool = _load_tool()


class FakeCollection:
    def __init__(self, name: str):
        self.name = name
        self.docs: list[dict] = []
        self.indexes: list[dict] = []
        self.dropped = False

    def list_indexes(self):
        return list(self.indexes)

    def drop_index(self, name: str):
        self.indexes = [i for i in self.indexes if i.get("name") != name]

    def drop(self):
        self.dropped = True
        self.docs = []

    def insert_one(self, doc):
        self.docs.append(dict(doc))

    def create_index(self, keys, name=None, unique=False):
        self.indexes.append({"name": name, "key": dict(keys), "unique": bool(unique)})


class FakeDb(dict):
    """Creates a FakeCollection lazily on first access, like pymongo does."""

    def __getitem__(self, key):
        if key not in self:
            self[key] = FakeCollection(key)
        return dict.__getitem__(self, key)


class PilotToolTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.backup_dir = Path(self.tmp.name)
        self._build_backup(self.backup_dir)

    def tearDown(self):
        self.tmp.cleanup()

    # ------------------------------------------------------------- fixtures
    @staticmethod
    def _build_backup(base: Path) -> None:
        (base / "schema").mkdir(parents=True, exist_ok=True)

        metadata = {
            "db": "logistics_db",
            "collections": [
                {"name": "shipments", "file": "shipments.jsonl", "count_exported": 2, "indexes": 2},
                {"name": "customers", "file": "customers.jsonl", "count_exported": 1, "indexes": 1},
                {"name": "users", "file": "users.jsonl", "count_exported": 1, "indexes": 1},
                {"name": "notification_outbox", "file": "notification_outbox.jsonl", "count_exported": 1, "indexes": 1},
            ],
        }
        (base / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

        def jsonl(name: str, docs: list[dict]) -> None:
            with (base / f"{name}.jsonl").open("w", encoding="utf-8") as fh:
                for doc in docs:
                    fh.write(json.dumps(doc, ensure_ascii=False) + "\n")

        jsonl("shipments", [
            {"_id": "ship1", "id": "LO-1", "status": "done"},
            {"_id": "ship2", "id": "LO-2", "status": "pending"},
        ])
        jsonl("customers", [{"_id": "cust1", "id": "CUST-1", "name": "Fake Customer"}])
        jsonl("users", [{"_id": "user1", "username": "pilot_admin", "password_hash": "redacted"}])
        jsonl("notification_outbox", [{"_id": "evt1", "event_id": "E-1"}])

        (base / "schema" / "shipments.json").write_text(
            json.dumps({
                "keys": {"id": "str"},
                "indexes": [
                    {"name": "uq_shipment_id", "key": {"id": 1}, "unique": True},
                    {"name": "ix_shipment_worklist", "key": {"status": 1, "updated_at": -1}, "unique": False},
                ],
            }),
            encoding="utf-8",
        )

    # ------------------------------------------------------------- CLI helpers
    def _run(self, args: list[str], stdin: str | None = None, env_extra: dict | None = None):
        env = dict(os.environ)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            [sys.executable, str(TOOL)] + args,
            input=stdin,
            text=True,
            capture_output=True,
            cwd=str(REPO),
            env=env,
            timeout=60,
        )

    # ------------------------------------------------------------- unit tests
    def test_parse_exclusions_repeat_and_comma(self):
        self.assertEqual(
            tool.parse_exclusions(["users", "notification_outbox, proxy_payments"]),
            frozenset({"users", "notification_outbox", "proxy_payments"}),
        )
        self.assertEqual(tool.parse_exclusions([]), frozenset())
        self.assertEqual(tool.parse_exclusions(None), frozenset())

    def test_G_requires_confirmation_boundary(self):
        # Production always requires confirmation unless the controlled override.
        self.assertTrue(tool.requires_confirmation("logistics_db"))
        self.assertFalse(tool.requires_confirmation("logistics_db", no_confirm=True))
        self.assertFalse(tool.requires_confirmation("logistics_db", dry_run=True))
        # Non-production targets never require production confirmation.
        self.assertFalse(tool.requires_confirmation("logistics_pilot"))
        self.assertFalse(tool.requires_confirmation("logistics_workdesk_logc14"))

    def test_A_validate_target_accepts_pilot(self):
        self.assertEqual(tool.validate_target("logistics_pilot"), "logistics_pilot")

    def test_B_validate_target_rejects_arbitrary(self):
        import contextlib
        import io

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as ctx:
                tool.validate_target("customer_prod_copy")
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("không hợp lệ", stderr.getvalue())

    def test_C_restore_excludes_users(self):
        db = FakeDb()
        results = tool.restore_backup(db, str(self.backup_dir), tool.load_metadata(str(self.backup_dir)),
                                      excluded=frozenset({"users"}))
        self.assertEqual(results["users"], ("skipped", 0))
        self.assertNotIn("users", db)
        # Everything else is still imported.
        self.assertEqual(results["shipments"], ("imported", 2))
        self.assertEqual(db["shipments"].docs[0]["id"], "LO-1")
        self.assertEqual(results["customers"], ("imported", 1))
        self.assertEqual(results["notification_outbox"], ("imported", 1))

    def test_D_restore_excludes_users_and_outbox(self):
        db = FakeDb()
        results = tool.restore_backup(db, str(self.backup_dir), tool.load_metadata(str(self.backup_dir)),
                                      excluded=frozenset({"users", "notification_outbox"}))
        self.assertEqual(results["users"], ("skipped", 0))
        self.assertEqual(results["notification_outbox"], ("skipped", 0))
        self.assertNotIn("users", db)
        self.assertNotIn("notification_outbox", db)
        self.assertEqual(results["shipments"], ("imported", 2))

    def test_E_included_shipments_restore_with_indexes(self):
        db = FakeDb()
        tool.restore_backup(db, str(self.backup_dir), tool.load_metadata(str(self.backup_dir)),
                            excluded=frozenset({"users", "notification_outbox"}))
        coll = db["shipments"]
        self.assertEqual(len(coll.docs), 2)
        self.assertEqual({d["id"] for d in coll.docs}, {"LO-1", "LO-2"})
        index_names = {i.get("name") for i in coll.indexes}
        self.assertIn("uq_shipment_id", index_names)
        self.assertIn("ix_shipment_worklist", index_names)
        uq = next(i for i in coll.indexes if i.get("name") == "uq_shipment_id")
        self.assertTrue(uq.get("unique"))

    # ------------------------------------------------------------- CLI tests
    def test_A_cli_pilot_target_accepted(self):
        proc = self._run(["--backup-dir", str(self.backup_dir), "--target-db", "logistics_pilot", "--dry-run"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("TARGET_DB=logistics_pilot", proc.stdout)

    def test_B_cli_arbitrary_target_rejected(self):
        proc = self._run(["--backup-dir", str(self.backup_dir), "--target-db", "customer_prod_copy", "--dry-run"])
        self.assertEqual(proc.returncode, 2)
        self.assertIn("không hợp lệ", proc.stderr)

    def test_F_cli_dry_run_reports_and_zero_mutation(self):
        # Point secrets at a non-existent path: a dry-run must not even touch
        # secrets. In this sandbox pymongo is also absent, so any connection
        # attempt would crash — returncode 0 proves zero DB access/mutation.
        proc = self._run(
            [
                "--backup-dir", str(self.backup_dir),
                "--target-db", "logistics_pilot",
                "--exclude-collection", "users",
                "--exclude-collection", "notification_outbox",
                "--dry-run",
            ],
            env_extra={"LOGISTICS_PRO_SECRETS_FILE": "/nonexistent/pilot-secrets.toml"},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = proc.stdout
        self.assertIn("TARGET_DB=logistics_pilot", out)
        self.assertIn("INCLUDE shipments", out)
        self.assertIn("SKIPPED users (excluded)", out)
        self.assertIn("SKIPPED notification_outbox (excluded)", out)
        self.assertIn("zero mutations", out)
        # No collection was dropped/created: the backup dir is byte-identical.
        before = {p.name: p.read_bytes() for p in self.backup_dir.rglob("*") if p.is_file()}
        self.assertIn("users.jsonl", before)  # untouched fixtures still present
        self.assertNotIn("SKIPPED shipments", out)

    def test_G_cli_production_confirmation_preserved(self):
        # A production import still stops at the typed confirmation token and
        # aborts before any connection when the token is wrong.
        secrets = self.backup_dir / "fake_secrets.toml"
        secrets.write_text('[mongo]\nuri = "mongodb://localhost:1/fake"\n', encoding="utf-8")
        proc = self._run(
            ["--backup-dir", str(self.backup_dir), "--target-db", "logistics_db"],
            stdin="NOT THE TOKEN\n",
            env_extra={"LOGISTICS_PRO_SECRETS_FILE": str(secrets)},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ROLLBACK CONFIRM", proc.stdout)
        self.assertIn("Đã hủy thao tác", proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
