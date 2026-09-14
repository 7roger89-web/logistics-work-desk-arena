"""Focused no-dependency checks for pilot snapshot BSON fidelity."""
from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RESTORE = REPO / "docs" / "goals" / "LOG-LG02" / "tools" / "restore_production.py"
EXPORT = REPO / "docs" / "goals" / "LOG-LG02" / "tools" / "export_production.py"


def _load_restore():
    spec = importlib.util.spec_from_file_location("restore_snapshot_fidelity", str(RESTORE))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


restore = _load_restore()


class SnapshotBsonFidelityTests(unittest.TestCase):
    def test_extended_json_uses_bson_json_util_loader(self):
        calls: list[str] = []

        class FakeJsonUtil:
            @staticmethod
            def loads(line: str):
                calls.append(line)
                return {"decoded": True, "kind": "bson"}

        fake_bson = types.ModuleType("bson")
        fake_bson.json_util = FakeJsonUtil
        previous = sys.modules.get("bson")
        sys.modules["bson"] = fake_bson
        try:
            result = restore._decode_jsonl_document(
                '{"created_at":{"$date":{"$numberLong":"0"}}}',
                restore.EXTENDED_JSON_SERIALIZATION,
            )
        finally:
            if previous is None:
                sys.modules.pop("bson", None)
            else:
                sys.modules["bson"] = previous

        self.assertEqual(result, {"decoded": True, "kind": "bson"})
        self.assertEqual(len(calls), 1)

    def test_legacy_plain_json_backup_remains_readable(self):
        self.assertEqual(
            restore._decode_jsonl_document('{"id":"LO-1","version":2}', ""),
            {"id": "LO-1", "version": 2},
        )

    def test_exporter_declares_canonical_extended_json_and_no_string_fallback(self):
        source = EXPORT.read_text(encoding="utf-8")
        self.assertIn("mongodb_extended_json_canonical_v1", source)
        self.assertIn("json_util.CANONICAL_JSON_OPTIONS", source)
        self.assertIn('"serialization": SERIALIZATION', source)
        self.assertNotIn("default=str", source)
        self.assertNotIn('doc["_id"] = str', source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
