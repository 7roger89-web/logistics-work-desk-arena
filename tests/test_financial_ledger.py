from __future__ import annotations

import os
import threading
import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from pymongo.errors import DuplicateKeyError, PyMongoError

from core.config import MONGO_DB_NAME, MONGO_URI
from core.database import ensure_indexes, init_connection
from core.financial_ledger import (
    CONFIRMED,
    ALLOCATIONS,
    RESTRICTED,
    REVIEW_REQUIRED,
    UNKNOWN,
    allocate_transaction,
    build_partner_financial_position,
    derive_obligation_position,
    derive_transaction_position,
    link_financial_record_to_shipment,
    party_key,
    project_partner_financial_position,
    reverse_allocation,
    save_obligation,
    save_transaction,
)


class _MemoryResult:
    def __init__(self, matched_count: int = 1, modified_count: int = 1):
        self.matched_count = matched_count
        self.modified_count = modified_count
        self.upserted_id = None


_MISSING = object()


def _value(document, path):
    current = document
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return _MISSING
        current = current[part]
    return current


def _matches(document, query):
    if not query:
        return True
    if "$or" in query and not any(_matches(document, branch) for branch in query["$or"]):
        return False
    for key, expected in query.items():
        if key == "$or":
            continue
        actual = _value(document, key)
        if isinstance(expected, dict) and any(str(op).startswith("$") for op in expected):
            if "$ne" in expected and actual is not _MISSING and actual == expected["$ne"]:
                return False
            if "$nin" in expected and actual is not _MISSING and actual in expected["$nin"]:
                return False
            if "$in" in expected and (actual is _MISSING or actual not in expected["$in"]):
                return False
            if "$exists" in expected and (actual is not _MISSING) != bool(expected["$exists"]):
                return False
            continue
        if actual is _MISSING or actual != expected:
            return False
    return True


class _MemoryCollection:
    def __init__(self, name: str):
        self.name = name
        self.docs: dict[str, dict] = {}
        self.fail_on_insert_calls: set[int] = set()
        self.fail_on_update_calls: set[int] = set()
        self.insert_calls = 0
        self.update_calls = 0

    def _key(self, document):
        return str(
            document.get("request_id")
            or document.get("correction_request_id")
            or document.get("event_id")
            or document.get("id")
            or uuid4()
        )

    def find_one(self, query, projection=None, **kwargs):
        for document in self.docs.values():
            if _matches(document, query):
                result = deepcopy(document)
                if projection and projection.get("_id") == 0:
                    result.pop("_id", None)
                return result
        return None

    def find(self, query=None, projection=None, **kwargs):
        rows = []
        for document in self.docs.values():
            if _matches(document, query or {}):
                result = deepcopy(document)
                if projection and projection.get("_id") == 0:
                    result.pop("_id", None)
                rows.append(result)
        return rows

    def insert_one(self, document, **kwargs):
        self.insert_calls += 1
        if self.insert_calls in self.fail_on_insert_calls:
            raise PyMongoError(f"fixture forced insert failure in {self.name}")
        key = self._key(document)
        if key in self.docs:
            raise DuplicateKeyError(f"fixture duplicate key in {self.name}: {key}")
        self.docs[key] = deepcopy(document)
        return _MemoryResult()

    def update_one(self, query, update, upsert=False, **kwargs):
        self.update_calls += 1
        if self.update_calls in self.fail_on_update_calls:
            raise PyMongoError(f"fixture forced update failure in {self.name}")
        key = next((key for key, value in self.docs.items() if _matches(value, query)), None)
        if key is None:
            if not upsert:
                return _MemoryResult(matched_count=0, modified_count=0)
            document = {name: value for name, value in query.items() if not name.startswith("$") and not isinstance(value, dict)}
            key = self._key(document)
            self.docs[key] = document
        document = deepcopy(self.docs[key])
        for field, value in update.get("$set", {}).items():
            document[field] = deepcopy(value)
        for field, value in update.get("$inc", {}).items():
            document[field] = document.get(field, 0) + value
        self.docs[key] = document
        return _MemoryResult()

    def create_index(self, *args, **kwargs):
        return kwargs.get("name", "fixture-index")

    def count_documents(self, query):
        return sum(1 for document in self.docs.values() if _matches(document, query))


class _MemoryTransaction:
    def __init__(self, db):
        self.db = db
        self.before = None

    def __enter__(self):
        self.db.lock.acquire()
        self.before = self.db.snapshot()
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None and self.before is not None:
            self.db.restore(self.before)
        self.db.lock.release()
        return False


class _MemorySession:
    def __init__(self, db):
        self.db = db

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def start_transaction(self):
        return _MemoryTransaction(self.db)


class _MemoryClient:
    def __init__(self, db):
        self.db = db

    def start_session(self):
        return _MemorySession(self.db)


class _MemoryDatabase:
    def __init__(self):
        self.lock = threading.RLock()
        self.client = _MemoryClient(self)
        self.collections: dict[str, _MemoryCollection] = {}

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = _MemoryCollection(name)
        return self.collections[name]

    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return self[name]

    def snapshot(self):
        return {name: deepcopy(collection.docs) for name, collection in self.collections.items()}

    def restore(self, snapshot):
        for name, docs in snapshot.items():
            self[name].docs = docs
        for name in list(self.collections):
            if name not in snapshot:
                self.collections[name].docs = {}


TT = {"party_type": "partner", "party_id": "TT", "name": "Trường Thành"}
ABO = {"party_type": "partner", "party_id": "ABO", "name": "A Bò"}
FACTORY = {"party_type": "factory", "party_id": "FACTORY-CN", "name": "Factory CN"}
CUSTOMER = {"party_type": "customer", "party_id": "BC", "name": "BC"}

SUPPORT_FIXTURE_USER = {
    "user_id": "support-ledger-fixture-01",
    "username": "support.ledger.fixture",
    "display_name": "Support Ledger Fixture",
    "role": "support",
}


def _support_auth_patch():
    return patch(
        "core.auth.st",
        new=SimpleNamespace(session_state={"current_user": SUPPORT_FIXTURE_USER}),
    )


def _obligation(obligation_id, amount, currency="VND", shipment_ids=None, purpose="partner payable", owner="Thành", from_party=TT, to_party=ABO):
    return {
        "id": obligation_id,
        "from_party": from_party,
        "to_party": to_party,
        "amount": amount,
        "currency": currency,
        "purpose": purpose,
        "shipment_ids": shipment_ids or [],
        "internal_sale_owner": owner,
        "evidence_refs": [{"kind": "fixture", "reference": obligation_id}],
    }


def _transaction(transaction_id, amount, currency="VND", *, kind="held_money", shipment_ids=None, owner="Thành", source=TT, holder=ABO, beneficial=TT, allowed_to=None, classification=CONFIRMED, restriction=None):
    allowed_use = {"allowed_to_party_keys": allowed_to or [party_key(holder)]}
    return {
        "id": transaction_id,
        "source_party": source,
        "holder_party": holder,
        "beneficial_owner": beneficial,
        "amount": amount,
        "currency": currency,
        "transaction_kind": kind,
        "shipment_ids": shipment_ids or [],
        "internal_sale_owner": owner,
        "allowed_use": allowed_use,
        "classification_status": classification,
        "restriction": restriction or {"status": "NONE"},
        "evidence_refs": [{"kind": "fixture", "reference": transaction_id}],
    }


class FinancialLedgerMemoryFixtureTests(unittest.TestCase):
    def setUp(self):
        self.db = _MemoryDatabase()
        self.auth_patch = _support_auth_patch()
        self.auth_patch.start()
        self.patch_db = patch("core.database.get_db", return_value=self.db)
        self.patch_db.start()

    def tearDown(self):
        self.patch_db.stop()
        self.auth_patch.stop()

    def test_obligation_transaction_are_shipment_optional_and_request_retry_is_idempotent(self):
        obligation = _obligation("OBL-NO-SHIPMENT", 80_000_000, shipment_ids=[])
        first = save_obligation(obligation, "REQ-OBL-1", actor="fixture")
        retry = save_obligation({**obligation, "id": "OBL-RETRY-ID"}, "REQ-OBL-1", actor="fixture")
        transaction = save_transaction(_transaction("TX-NO-SHIPMENT", 30_000_000), "REQ-TX-1", actor="fixture")

        self.assertTrue(first[0], first[2])
        self.assertTrue(retry[0], retry[2])
        self.assertTrue(transaction[0], transaction[2])
        self.assertEqual(first[1]["id"], retry[1]["id"])
        saved_obligation = self.db.financial_obligations.find_one({"id": "OBL-NO-SHIPMENT"})
        saved_transaction = self.db.financial_transactions.find_one({"id": "TX-NO-SHIPMENT"})
        self.assertEqual(saved_obligation["shipment_ids"], [])
        self.assertIsNone(saved_obligation["shipment_id"])
        self.assertEqual(saved_transaction["shipment_ids"], [])
        self.assertIsNone(saved_transaction["shipment_id"])
        self.assertEqual(saved_obligation["created_by_user_id"], SUPPORT_FIXTURE_USER["user_id"])
        self.assertEqual(saved_transaction["created_by_role"], "support")
        self.assertNotIn("outstanding", saved_obligation)
        self.assertNotIn("unallocated", saved_transaction)

    def test_abo_held_money_can_later_allocate_to_shipment_obligation(self):
        transaction = save_transaction(_transaction("TX-ABO-HELD", 30_000_000), "REQ-ABO-HELD", actor="fixture")
        obligation = save_obligation(_obligation("OBL-L-001", 80_000_000, shipment_ids=["L-001"]), "REQ-L-001", actor="fixture")
        allocated = allocate_transaction(transaction[1]["id"], obligation[1]["id"], 30_000_000, "REQ-ABO-ALLOC", actor="fixture")

        self.assertTrue(allocated[0], allocated[2])
        tx = self.db.financial_transactions.find_one({"id": "TX-ABO-HELD"})
        obl = self.db.financial_obligations.find_one({"id": "OBL-L-001"})
        allocations = self.db.financial_allocations.find({})
        tx_position = derive_transaction_position(tx, allocations)
        obl_position = derive_obligation_position(obl, allocations)
        self.assertEqual(tx_position["allocated"], 30_000_000)
        self.assertEqual(tx_position["unallocated"], 0)
        self.assertEqual(obl_position["outstanding"], 50_000_000)
        projection = build_partner_financial_position(ABO, db=self.db)
        self.assertEqual(projection["totals_by_currency"]["VND"]["payable_to_partner"], 50_000_000)
        self.assertEqual(projection["totals_by_currency"]["VND"]["held_credit"], 0)
        self.assertTrue(projection["derived"])
        self.assertTrue(projection["read_only"])

    def test_one_transaction_can_allocate_to_many_obligations_and_keep_unallocated_remainder(self):
        transaction = save_transaction(_transaction("TX-MULTI", 300_000_000), "REQ-TX-MULTI", actor="fixture")
        obligations = [
            save_obligation(_obligation("OBL-SHIP-A", 200_000_000, shipment_ids=["SHIP-A"], purpose="goods"), "REQ-OBL-A", actor="fixture"),
            save_obligation(_obligation("OBL-FREIGHT-A", 50_000_000, shipment_ids=["SHIP-A"], purpose="freight"), "REQ-OBL-FREIGHT", actor="fixture"),
            save_obligation(_obligation("OBL-TAX-A", 30_000_000, shipment_ids=["SHIP-A"], purpose="tax"), "REQ-OBL-TAX", actor="fixture"),
        ]
        for index, obligation in enumerate(obligations, start=1):
            self.assertTrue(
                allocate_transaction(transaction[1]["id"], obligation[1]["id"], (200_000_000, 50_000_000, 30_000_000)[index - 1], f"REQ-MULTI-{index}", actor="fixture")[0]
            )
        tx = self.db.financial_transactions.find_one({"id": "TX-MULTI"})
        position = derive_transaction_position(tx, self.db.financial_allocations.find({}))
        self.assertEqual(position["amount"], 300_000_000)
        self.assertEqual(position["allocated"], 280_000_000)
        self.assertEqual(position["unallocated"], 20_000_000)
        self.assertEqual(self.db.financial_transactions.count_documents({"id": "TX-MULTI"}), 1)
        self.assertEqual(self.db.financial_allocations.count_documents({"transaction_id": "TX-MULTI"}), 3)

    def test_multiple_payments_settle_one_obligation(self):
        obligation = save_obligation(
            _obligation("OBL-CNY-100K", 100_000, currency="CNY", from_party=CUSTOMER, to_party=FACTORY, purpose="factory payment"),
            "REQ-CNY-OBL",
            actor="fixture",
        )
        for index, amount in enumerate((30_000, 50_000, 20_000), start=1):
            transaction = save_transaction(
                _transaction(
                    f"TX-CNY-{index}",
                    amount,
                    currency="CNY",
                    source=CUSTOMER,
                    holder=FACTORY,
                    beneficial=CUSTOMER,
                    allowed_to=[party_key(FACTORY)],
                ),
                f"REQ-CNY-TX-{index}",
                actor="fixture",
            )
            self.assertTrue(transaction[0], transaction[2])
            allocation = allocate_transaction(transaction[1]["id"], obligation[1]["id"], amount, f"REQ-CNY-ALLOC-{index}", actor="fixture")
            self.assertTrue(allocation[0], allocation[2])
        saved_obligation = self.db.financial_obligations.find_one({"id": "OBL-CNY-100K"})
        position = derive_obligation_position(saved_obligation, self.db.financial_allocations.find({}))
        self.assertEqual(position["allocated"], 100_000)
        self.assertEqual(position["outstanding"], 0)

    def test_received_on_behalf_payment_only_and_later_link_do_not_duplicate_history(self):
        received = save_transaction(
            _transaction(
                "TX-RECEIVED-ON-BEHALF",
                62_464,
                currency="CNY",
                kind="received_on_behalf",
                source=TT,
                holder=ABO,
                beneficial=FACTORY,
                allowed_to=[party_key(FACTORY)],
            ),
            "REQ-RECEIVED",
            actor="fixture",
        )
        payment_only = save_transaction(
            _transaction(
                "TX-PAYMENT-ONLY",
                1_687,
                currency="CNY",
                kind="payment_only",
                source=CUSTOMER,
                holder=ABO,
                beneficial=CUSTOMER,
                allowed_to=[party_key(FACTORY)],
            ),
            "REQ-PAYMENT-ONLY",
            actor="fixture",
        )
        link = link_financial_record_to_shipment("transaction", payment_only[1]["id"], "L-002", "REQ-LINK-1", actor="fixture")
        link_retry = link_financial_record_to_shipment("transaction", payment_only[1]["id"], "L-002", "REQ-LINK-1", actor="fixture")

        self.assertTrue(received[0], received[2])
        self.assertTrue(payment_only[0], payment_only[2])
        self.assertTrue(link[0], link[2])
        self.assertTrue(link_retry[0], link_retry[2])
        self.assertEqual(self.db.financial_transactions.count_documents({}), 2)
        saved = self.db.financial_transactions.find_one({"id": "TX-PAYMENT-ONLY"})
        self.assertEqual(saved["shipment_ids"], ["L-002"])
        self.assertEqual(saved["source_party"]["party_id"], "BC")
        self.assertEqual(saved["holder_party"]["party_id"], "ABO")
        self.assertEqual(saved["beneficial_owner"]["party_id"], "BC")
        self.assertEqual(self.db.financial_action_requests.count_documents({"request_id": "REQ-LINK-1"}), 1)

        obligation = save_obligation(
            _obligation("OBL-RECEIVED", 62_464, currency="CNY", shipment_ids=["L-003"], from_party=TT, to_party=FACTORY, purpose="factory payment"),
            "REQ-RECEIVED-OBL",
            actor="fixture",
        )
        allocation = allocate_transaction(received[1]["id"], obligation[1]["id"], 62_464, "REQ-RECEIVED-ALLOC", actor="fixture")
        self.assertTrue(allocation[0], allocation[2])
        self.assertEqual(self.db.financial_transactions.count_documents({"id": "TX-RECEIVED-ON-BEHALF"}), 1)

    def test_projection_keeps_received_history_after_full_allocation_and_exposes_owner_coverage(self):
        received = save_transaction(
            _transaction(
                "TX-RECEIVED-FULL",
                62_464,
                currency="CNY",
                kind="received_on_behalf",
                source=FACTORY,
                holder=ABO,
                beneficial=TT,
                allowed_to=[party_key(FACTORY)],
            ),
            "REQ-RECEIVED-FULL",
            actor="fixture",
        )
        obligation = save_obligation(
            _obligation(
                "OBL-RECEIVED-FULL",
                62_464,
                currency="CNY",
                shipment_ids=["L-003"],
                from_party=TT,
                to_party=FACTORY,
                purpose="factory payment",
            ),
            "REQ-RECEIVED-FULL-OBL",
            actor="fixture",
        )
        allocation = allocate_transaction(
            received[1]["id"],
            obligation[1]["id"],
            62_464,
            "REQ-RECEIVED-FULL-ALLOC",
            actor="fixture",
        )
        self.assertTrue(allocation[0], allocation[2])
        projection = build_partner_financial_position(ABO, internal_sale_owner="Thành", db=self.db)
        received_row = next(
            row for row in projection["buckets"]["received_on_behalf"] if row["transaction_id"] == "TX-RECEIVED-FULL"
        )
        self.assertEqual(received_row["received_amount"], 62_464)
        self.assertEqual(received_row["remaining_unallocated"], 0)
        self.assertEqual(received_row["allocation_history"][0]["id"], allocation[1]["id"])
        self.assertGreaterEqual(projection["owner_coverage"]["matching_owner_count"], 1)

    def test_projection_exposes_paid_on_behalf_without_treating_it_as_held_credit(self):
        paid = save_transaction(
            _transaction(
                "TX-PAID-ON-BEHALF",
                134_973,
                currency="CNY",
                kind="paid_on_behalf",
                source=ABO,
                holder=FACTORY,
                beneficial=TT,
                allowed_to=[party_key(FACTORY)],
            ),
            "REQ-PAID-ON-BEHALF",
            actor="fixture",
        )
        self.assertTrue(paid[0], paid[2])
        projection = build_partner_financial_position(ABO, internal_sale_owner="Thành", db=self.db)
        paid_row = next(
            row for row in projection["buckets"]["paid_on_behalf"] if row["transaction_id"] == "TX-PAID-ON-BEHALF"
        )
        self.assertEqual(paid_row["spent_amount"], 134_973)
        self.assertEqual(projection["totals_by_currency"]["CNY"]["paid_on_behalf"], 134_973)
        self.assertEqual(projection["totals_by_currency"]["CNY"]["held_credit"], 0)

    def test_restricted_unknown_and_incompatible_currency_are_blocked(self):
        restricted = save_transaction(
            _transaction("TX-RESTRICTED", 10_000, restriction={"status": RESTRICTED}),
            "REQ-RESTRICTED",
            actor="fixture",
        )
        unknown = save_transaction(
            _transaction("TX-UNKNOWN", 11_000, classification=UNKNOWN),
            "REQ-UNKNOWN",
            actor="fixture",
        )
        cny = save_transaction(_transaction("TX-CNY", 12_000, currency="CNY"), "REQ-CNY", actor="fixture")
        vnd_obligation = save_obligation(_obligation("OBL-VND", 12_000, currency="VND"), "REQ-VND-OBL", actor="fixture")
        restricted_obligation = save_obligation(_obligation("OBL-RESTRICTED", 10_000), "REQ-RESTRICTED-OBL", actor="fixture")
        unknown_obligation = save_obligation(_obligation("OBL-UNKNOWN", 11_000), "REQ-UNKNOWN-OBL", actor="fixture")

        self.assertFalse(allocate_transaction(restricted[1]["id"], restricted_obligation[1]["id"], 10_000, "REQ-RESTRICTED-ALLOC", actor="fixture")[0])
        self.assertFalse(allocate_transaction(unknown[1]["id"], unknown_obligation[1]["id"], 11_000, "REQ-UNKNOWN-ALLOC", actor="fixture")[0])
        self.assertFalse(allocate_transaction(cny[1]["id"], vnd_obligation[1]["id"], 12_000, "REQ-CURRENCY-ALLOC", actor="fixture")[0])
        self.assertEqual(self.db.financial_allocations.count_documents({}), 0)

        projection = build_partner_financial_position(ABO, db=self.db)
        self.assertGreaterEqual(len(projection["buckets"]["restricted"]), 1)
        self.assertGreaterEqual(len(projection["buckets"]["unknown"]), 1)
        self.assertEqual(projection["totals_by_currency"]["CNY"]["held_credit"], 12_000)
        self.assertEqual(projection["totals_by_currency"]["VND"]["payable_to_partner"], 33_000)
        self.assertNotIn("net_position", projection)

    def test_allocation_reversal_preserves_original_and_restores_derived_positions(self):
        transaction = save_transaction(_transaction("TX-REVERSAL", 30_000_000), "REQ-REV-TX", actor="fixture")
        obligation = save_obligation(_obligation("OBL-REVERSAL", 80_000_000, shipment_ids=["L-004"]), "REQ-REV-OBL", actor="fixture")
        allocation = allocate_transaction(transaction[1]["id"], obligation[1]["id"], 30_000_000, "REQ-REV-ALLOC", actor="fixture")
        reversed_once = reverse_allocation(allocation[1]["id"], "REQ-REV-CORR", "fixture correction", {"kind": "fixture-proof"}, actor="fixture")
        reversed_retry = reverse_allocation(allocation[1]["id"], "REQ-REV-CORR", "fixture correction", {"kind": "fixture-proof"}, actor="fixture")

        self.assertTrue(reversed_once[0], reversed_once[2])
        self.assertTrue(reversed_retry[0], reversed_retry[2])
        self.assertEqual(reversed_once[1], reversed_retry[1])
        saved_allocation = self.db.financial_allocations.find_one({"id": allocation[1]["id"]})
        self.assertEqual(saved_allocation["status"], "reversed")
        self.assertTrue(saved_allocation["is_reversed"])
        self.assertEqual(self.db.financial_corrections.count_documents({"correction_request_id": "REQ-REV-CORR"}), 1)
        tx_position = derive_transaction_position(self.db.financial_transactions.find_one({"id": "TX-REVERSAL"}), self.db.financial_allocations.find({}))
        obl_position = derive_obligation_position(self.db.financial_obligations.find_one({"id": "OBL-REVERSAL"}), self.db.financial_allocations.find({}))
        self.assertEqual(tx_position["unallocated"], 30_000_000)
        self.assertEqual(obl_position["outstanding"], 80_000_000)

    def test_overallocated_history_is_visible_review_not_silently_settled(self):
        transaction = save_transaction(_transaction("TX-OVER", 100_000), "REQ-OVER-TX", actor="fixture")
        obligation = save_obligation(_obligation("OBL-OVER", 100_000), "REQ-OVER-OBL", actor="fixture")
        self.db.financial_allocations.insert_one(
            {
                "id": "ALC-OVER",
                "transaction_id": transaction[1]["id"],
                "obligation_id": obligation[1]["id"],
                "amount": 120_000,
                "currency": "VND",
                "status": "active",
            }
        )

        tx_position = derive_transaction_position(
            self.db.financial_transactions.find_one({"id": transaction[1]["id"]}),
            self.db.financial_allocations.find({}),
        )
        obl_position = derive_obligation_position(
            self.db.financial_obligations.find_one({"id": obligation[1]["id"]}),
            self.db.financial_allocations.find({}),
        )
        projection = build_partner_financial_position(ABO, db=self.db)

        self.assertEqual(tx_position["status"], REVIEW_REQUIRED)
        self.assertTrue(tx_position["overallocated"])
        self.assertEqual(obl_position["status"], REVIEW_REQUIRED)
        self.assertTrue(obl_position["overallocated"])
        self.assertGreaterEqual(len(projection["buckets"]["unknown"]), 2)
        self.assertEqual(projection["status"], REVIEW_REQUIRED)

    def test_failure_rolls_back_canonical_record_and_request_registry(self):
        self.db.financial_action_requests.fail_on_insert_calls = {1}
        result = save_transaction(_transaction("TX-ROLLBACK", 10_000), "REQ-ROLLBACK", actor="fixture")
        self.assertFalse(result[0])
        self.assertIsNone(self.db.financial_transactions.find_one({"id": "TX-ROLLBACK"}))
        self.assertEqual(self.db.financial_action_requests.count_documents({}), 0)
        self.assertEqual(self.db.audit_logs.count_documents({}), 0)
        self.assertEqual(self.db.notification_outbox.count_documents({}), 0)

    def test_no_transaction_support_fails_closed(self):
        self.db.client = object()
        result = save_obligation(_obligation("OBL-NO-TX", 10_000), "REQ-NO-TX", actor="fixture")
        self.assertFalse(result[0])
        self.assertEqual(self.db.financial_obligations.count_documents({}), 0)

    def test_sale_thanh_is_only_a_projection_dimension(self):
        obligation_thanh = _obligation("OBL-THANH", 20_000_000, owner="Thành")
        obligation_other = _obligation("OBL-OTHER-OWNER", 40_000_000, owner="Khác")
        transaction_thanh = _transaction("TX-THANH", 5_000_000, owner="Thành")
        transaction_other = _transaction("TX-OTHER-OWNER", 7_000_000, owner="Khác")
        for document, request_id in (
            (obligation_thanh, "REQ-DIM-OBL-1"),
            (obligation_other, "REQ-DIM-OBL-2"),
        ):
            self.assertTrue(save_obligation(document, request_id, actor="fixture")[0])
        for document, request_id in (
            (transaction_thanh, "REQ-DIM-TX-1"),
            (transaction_other, "REQ-DIM-TX-2"),
        ):
            self.assertTrue(save_transaction(document, request_id, actor="fixture")[0])
        allocation = allocate_transaction("TX-THANH", "OBL-THANH", 2_000_000, "REQ-DIM-ALLOC", actor="fixture")
        self.assertTrue(allocation[0], allocation[2])
        projection = build_partner_financial_position(ABO, internal_sale_owner="Thành", db=self.db)
        self.assertEqual(projection["internal_sale_owner"], "Thành")
        self.assertEqual({row["obligation_id"] for row in projection["buckets"]["payable_to_partner"]}, {"OBL-THANH"})
        self.assertEqual({row["transaction_id"] for row in projection["buckets"]["held_credit"]}, {"TX-THANH"})
        self.assertEqual({row["allocation_id"] for row in projection["recent_allocations"]}, {allocation[1]["id"]})
        saved = self.db.financial_obligations.find_one({"id": "OBL-THANH"})
        self.assertEqual(saved["to_party"]["party_id"], "ABO")
        self.assertNotEqual(saved["to_party"].get("party_id"), "Thành")


class MongoFinancialLedgerFixtureTests(unittest.TestCase):
    """Opt-in disposable Mongo proof; never points at the application DB."""

    @classmethod
    def setUpClass(cls):
        if os.environ.get("LOG_C02_RUN_MONGO_FIXTURES") != "1":
            raise unittest.SkipTest("set LOG_C02_RUN_MONGO_FIXTURES=1 for isolated Mongo proof")
        if not MONGO_URI:
            raise unittest.SkipTest("Mongo URI is not configured")
        cls.client = init_connection()
        if cls.client is None:
            raise unittest.SkipTest("Mongo is not reachable")
        cls.db_name = f"l02b2_{uuid4().hex[:16]}"
        if cls.db_name == MONGO_DB_NAME or cls.db_name in cls.client.list_database_names():
            raise RuntimeError("fixture database name was not isolated")
        cls.db = cls.client[cls.db_name]
        with patch("core.database.get_db", return_value=cls.db):
            if not ensure_indexes():
                raise RuntimeError("fixture indexes could not be created")
        cls.created_fixture = False

    @classmethod
    def tearDownClass(cls):
        if not hasattr(cls, "client"):
            return
        try:
            if getattr(cls, "created_fixture", False) and cls.db_name != MONGO_DB_NAME:
                if cls.db_name in cls.client.list_database_names():
                    cls.client.drop_database(cls.db_name)
        finally:
            cls.client.close()

    def setUp(self):
        type(self).created_fixture = True
        self.auth_patch = _support_auth_patch()
        self.auth_patch.start()

    def tearDown(self):
        self.auth_patch.stop()

    def _fresh_db(self):
        from pymongo import MongoClient

        fresh_client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            retryWrites=True,
            tz_aware=True,
        )
        return fresh_client, fresh_client[type(self).db_name]

    def test_golden_case_persists_and_reads_back_from_fresh_client(self):
        with patch("core.database.get_db", return_value=type(self).db):
            transaction = save_transaction(_transaction("TX-MONGO-ABO", 30_000_000), "REQ-MONGO-TX", actor="fixture")
            obligation = save_obligation(_obligation("OBL-MONGO-L001", 80_000_000, shipment_ids=["L-001"]), "REQ-MONGO-OBL", actor="fixture")
            allocation = allocate_transaction(transaction[1]["id"], obligation[1]["id"], 30_000_000, "REQ-MONGO-ALLOC", actor="fixture")
        self.assertTrue(transaction[0], transaction[2])
        self.assertTrue(obligation[0], obligation[2])
        self.assertTrue(allocation[0], allocation[2])

        fresh_client, fresh_db = self._fresh_db()
        try:
            saved_transaction = fresh_db.financial_transactions.find_one({"id": "TX-MONGO-ABO"})
            saved_obligation = fresh_db.financial_obligations.find_one({"id": "OBL-MONGO-L001"})
            saved_allocation = fresh_db.financial_allocations.find_one({"id": allocation[1]["id"]})
            self.assertIsNotNone(saved_transaction)
            self.assertIsNotNone(saved_obligation)
            self.assertIsNotNone(saved_allocation)
            self.assertEqual(saved_transaction["shipment_ids"], [])
            self.assertEqual(saved_obligation["shipment_ids"], ["L-001"])
            self.assertEqual(derive_transaction_position(saved_transaction, [saved_allocation])["unallocated"], 0)
            self.assertEqual(derive_obligation_position(saved_obligation, [saved_allocation])["outstanding"], 50_000_000)
            position = build_partner_financial_position(ABO, db=fresh_db)
            self.assertEqual(position["totals_by_currency"]["VND"]["payable_to_partner"], 50_000_000)
            self.assertEqual(fresh_db.financial_action_requests.count_documents({"request_id": "REQ-MONGO-ALLOC"}), 1)
        finally:
            fresh_client.close()


if __name__ == "__main__":
    unittest.main()
