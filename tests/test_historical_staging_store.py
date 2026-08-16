"""Fake-database write-oracle tests for LOG-C06 staging persistence."""

from __future__ import annotations

import copy
import unittest
from pathlib import Path

from core.historical_staging_store import (
    REVIEW_ACTIONS_COLLECTION,
    STAGING_COLLECTION,
    ReviewActionConflict,
    ReviewValidationError,
    apply_review_action,
    ensure_staging_indexes,
    list_review_actions,
    load_staging_batch,
    persist_staging_batch,
)


class FakeResult:
    def __init__(self, matched_count: int = 0):
        self.matched_count = matched_count


class FakeCollection:
    def __init__(self, name: str):
        self.name = name
        self.documents: list[dict] = []
        self.indexes: list[dict] = []

    @staticmethod
    def _matches(document: dict, query: dict) -> bool:
        return all(document.get(key) == value for key, value in query.items())

    def create_index(self, keys, *, unique: bool, name: str):
        self.indexes.append({"keys": list(keys), "unique": unique, "name": name})
        return name

    def find_one(self, query: dict):
        return next((copy.deepcopy(item) for item in self.documents if self._matches(item, query)), None)

    def find(self, query: dict):
        return [copy.deepcopy(item) for item in self.documents if self._matches(item, query)]

    def insert_one(self, document: dict):
        if "_id" in document and any(item.get("_id") == document["_id"] for item in self.documents):
            raise AssertionError(f"Duplicate fake _id in {self.name}: {document['_id']}")
        self.documents.append(copy.deepcopy(document))

    def replace_one(self, query: dict, document: dict, *, upsert: bool):
        for index, item in enumerate(self.documents):
            if self._matches(item, query):
                self.documents[index] = copy.deepcopy(document)
                return FakeResult(matched_count=1)
        if upsert:
            self.insert_one(document)
            return FakeResult(matched_count=0)
        return FakeResult(matched_count=0)


class FakeDatabase(dict):
    def __init__(self):
        super().__init__()
        self[STAGING_COLLECTION] = FakeCollection(STAGING_COLLECTION)
        self[REVIEW_ACTIONS_COLLECTION] = FakeCollection(REVIEW_ACTIONS_COLLECTION)
        self.canonical_accesses: list[str] = []

    def __getitem__(self, name):
        if name not in {STAGING_COLLECTION, REVIEW_ACTIONS_COLLECTION}:
            self.canonical_accesses.append(name)
            raise AssertionError(f"Canonical collection touched: {name}")
        return super().__getitem__(name)


class FailingAuditCollection(FakeCollection):
    def insert_one(self, document: dict):
        raise RuntimeError("fixture forced audit insert failure")


class FailingAuditDatabase(FakeDatabase):
    def __init__(self):
        super().__init__()
        self[REVIEW_ACTIONS_COLLECTION] = FailingAuditCollection(REVIEW_ACTIONS_COLLECTION)


def _item(source_item_id: str, amount: float = 10.0) -> dict:
    return {
        "source_item_id": source_item_id,
        "source_file": "fixture.xls",
        "source_file_hash": "fixture-hash",
        "sheet": "Sheet2",
        "source_row": int(source_item_id.rsplit("-", 1)[-1]),
        "source_cell_range": "D1:D1",
        "source_reference": f"Sheet2!D{source_item_id.rsplit('-', 1)[-1]}",
        "raw_values": {"D1": amount},
        "raw_cell_types": {"D1": 2},
        "raw_text": f"raw {source_item_id}",
        "raw_note": f"raw {source_item_id}",
        "raw_date": "2026-01-01",
        "raw_date_serial": 46023.0,
        "inherited_date_context": None,
        "raw_sale": "thành",
        "raw_customer": "fixture party",
        "raw_reference": [],
        "raw_amount": amount,
        "raw_currency": "CNY",
        "parser_version": "fixture-v1",
        "imported_at": "2026-08-15T00:00:00+00:00",
        "review_status": "PROPOSED",
        "proposal": {
            "internal_sale_owner": "Thành",
            "currency": "CNY",
            "amount": amount,
            "event_type": "received_on_behalf",
            "candidate_bucket": "received_on_behalf",
            "anomalies": [],
        },
        "review_reason": "fixture",
        "anomaly_flags": [],
        "review_history": [],
    }


class HistoricalStagingStoreTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDatabase()
        self.batch = {
            "source_file": "fixture.xls",
            "source_file_hash": "fixture-hash",
            "parser_version": "fixture-v1",
            "items": [_item("fixture-1"), _item("fixture-2", amount=20.0)],
        }
        ensure_staging_indexes(self.db)

    def test_indexes_and_import_are_staging_only_and_retry_safe(self):
        result = persist_staging_batch(self.db, self.batch)
        self.assertEqual(result["inserted"], 2)
        self.assertEqual(result["updated"], 0)
        self.assertEqual(result["canonical_writes"], 0)
        self.assertEqual(len(self.db[STAGING_COLLECTION].documents), 2)
        self.assertEqual(len(self.db[REVIEW_ACTIONS_COLLECTION].documents), 0)
        self.assertEqual(len(self.db[STAGING_COLLECTION].indexes), 2)
        self.assertEqual(len(self.db[REVIEW_ACTIONS_COLLECTION].indexes), 2)

        retry = persist_staging_batch(self.db, self.batch)
        self.assertEqual(retry["inserted"], 0)
        self.assertEqual(retry["updated"], 2)
        loaded = load_staging_batch(self.db)
        self.assertEqual(loaded["item_count"], 2)
        self.assertEqual(loaded["source_file_hash"], "fixture-hash")
        self.assertEqual(self.db.canonical_accesses, [])

    def test_confirm_action_preserves_raw_fields_and_is_idempotent(self):
        persist_staging_batch(self.db, self.batch)
        before = self.db[STAGING_COLLECTION].find_one({"source_item_id": "fixture-1"})
        applied = apply_review_action(
            self.db,
            "fixture-1",
            "confirm",
            actor="owner-1",
            reason="Đã đối chiếu source row.",
            request_id="request-confirm-1",
            acted_at="2026-08-15T01:00:00+00:00",
            expected_review_version=0,
        )
        self.assertEqual(applied["status"], "APPLIED")
        self.assertEqual(applied["after_status"], "CONFIRMED")
        self.assertEqual(applied["item"]["review_version"], 1)
        self.assertEqual(len(applied["item"]["review_history"]), 1)
        self.assertEqual(applied["item"]["raw_text"], before["raw_text"])
        self.assertEqual(applied["item"]["raw_values"], before["raw_values"])

        retry = apply_review_action(
            self.db,
            "fixture-1",
            "confirm",
            actor="owner-1",
            reason="retry",
            request_id="request-confirm-1",
        )
        self.assertEqual(retry["status"], "IDEMPOTENT")
        self.assertEqual(retry["item"]["review_version"], 1)
        self.assertEqual(len(list_review_actions(self.db, source_item_id="fixture-1")), 1)

    def test_correct_action_changes_proposal_metadata_only(self):
        persist_staging_batch(self.db, self.batch)
        before = self.db[STAGING_COLLECTION].find_one({"source_item_id": "fixture-2"})
        result = apply_review_action(
            self.db,
            "fixture-2",
            "correct",
            actor="owner-1",
            reason="Đã xác nhận lại bên thụ hưởng.",
            request_id="request-correct-1",
            correction={"internal_sale_owner": "Thành", "candidate_bucket": "held_credit"},
        )
        self.assertEqual(result["after_status"], "CONFIRMED")
        self.assertTrue(result["item"]["proposal"]["correction_applied"])
        self.assertEqual(result["item"]["proposal"]["candidate_bucket"], "held_credit")
        self.assertEqual(result["item"]["raw_amount"], before["raw_amount"])
        self.assertEqual(result["item"]["raw_sale"], before["raw_sale"])
        self.assertEqual(len(self.db[REVIEW_ACTIONS_COLLECTION].documents), 1)

    def test_lineage_repair_returns_to_review_and_preserves_raw_evidence(self):
        persist_staging_batch(self.db, self.batch)
        before = self.db[STAGING_COLLECTION].find_one({"source_item_id": "fixture-1"})
        result = apply_review_action(
            self.db,
            "fixture-1",
            "lineage_repair",
            actor="technical-review",
            reason="Correct source amount cell lineage; no business reclassification.",
            request_id="request-lineage-repair-1",
            correction={
                "amount": 99.0,
                "amount_source_cell": "E1",
                "amount_source_kind": "numeric_cell",
                "technical_lineage_status": "corrected_parser_amount_source",
                "technical_lineage_repair_id": "fixture-repair-1",
                "technical_lineage": {"source_cell": "Sheet2!E1"},
            },
            expected_review_version=0,
        )
        self.assertEqual(result["status"], "APPLIED")
        self.assertEqual(result["after_status"], "REVIEW_REQUIRED")
        self.assertEqual(result["item"]["proposal"]["amount"], 99.0)
        self.assertEqual(result["item"]["proposal"]["technical_lineage_status"], "corrected_parser_amount_source")
        self.assertEqual(result["item"]["raw_values"], before["raw_values"])
        self.assertEqual(result["item"]["raw_amount"], before["raw_amount"])

        retry = apply_review_action(
            self.db,
            "fixture-1",
            "lineage_repair",
            actor="technical-review",
            reason="retry",
            request_id="request-lineage-repair-1",
        )
        self.assertEqual(retry["status"], "IDEMPOTENT")
        self.assertEqual(len(list_review_actions(self.db, source_item_id="fixture-1")), 1)

    def test_not_thanh_and_unknown_are_excluded_states(self):
        self.batch["items"].extend([_item("fixture-3"), _item("fixture-4")])
        persist_staging_batch(self.db, self.batch)
        not_thanh = apply_review_action(
            self.db,
            "fixture-3",
            "not_thanh",
            actor="owner-1",
            reason="SALE field belongs to another owner.",
            request_id="request-not-thanh",
        )
        unknown = apply_review_action(
            self.db,
            "fixture-4",
            "unknown",
            actor="owner-1",
            reason="Source does not establish the business meaning.",
            request_id="request-unknown",
        )
        self.assertEqual(not_thanh["after_status"], "NOT_APPLICABLE")
        self.assertEqual(unknown["after_status"], "REJECTED")
        self.assertEqual(unknown["item"]["proposal"]["restriction"], "unresolved_unknown")
        self.assertEqual(unknown["item"]["proposal"]["candidate_bucket"], None)

    def test_conflict_and_forbidden_raw_correction_fail_closed(self):
        persist_staging_batch(self.db, self.batch)
        with self.assertRaises(ReviewValidationError):
            apply_review_action(
                self.db,
                "fixture-1",
                "correct",
                actor="owner-1",
                reason="bad patch",
                request_id="request-bad-patch",
                correction={"raw_amount": 999},
            )
        apply_review_action(
            self.db,
            "fixture-1",
            "confirm",
            actor="owner-1",
            reason="first",
            request_id="request-conflict-base",
        )
        with self.assertRaises(ReviewActionConflict):
            apply_review_action(
                self.db,
                "fixture-1",
                "correct",
                actor="owner-1",
                reason="stale correction",
                request_id="request-stale",
                expected_review_version=0,
                correction={"candidate_bucket": "held_credit"},
            )
        with self.assertRaises(ReviewActionConflict):
            apply_review_action(
                self.db,
                "fixture-1",
                "not_thanh",
                actor="owner-1",
                reason="same request, different action",
                request_id="request-conflict-base",
            )

    def test_audit_insert_failure_rolls_back_staging_metadata(self):
        db = FailingAuditDatabase()
        ensure_staging_indexes(db)
        persist_staging_batch(db, self.batch)
        before = db[STAGING_COLLECTION].find_one({"source_item_id": "fixture-1"})
        with self.assertRaises(RuntimeError):
            apply_review_action(
                db,
                "fixture-1",
                "confirm",
                actor="owner-1",
                reason="audit failure fixture",
                request_id="request-audit-failure",
            )
        after = db[STAGING_COLLECTION].find_one({"source_item_id": "fixture-1"})
        self.assertEqual(after, before)
        self.assertEqual(db[REVIEW_ACTIONS_COLLECTION].documents, [])

    def test_store_has_no_canonical_provider_dependency(self):
        source = Path(__file__).resolve().parents[1] / "core" / "historical_staging_store.py"
        text = source.read_text(encoding="utf-8")
        self.assertNotIn("from core.database", text)
        self.assertNotIn("financial_ledger", text)
        self.assertNotIn("financial_obligations", text)


if __name__ == "__main__":
    unittest.main()
