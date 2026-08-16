from __future__ import annotations

import os
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from unittest.mock import patch
from uuid import uuid4

from pymongo.errors import DuplicateKeyError, PyMongoError

from core.config import MONGO_DB_NAME, MONGO_URI
from core.database import (
    ensure_indexes,
    init_connection,
    save_contract_proxy_payment_atomic,
    save_direct_payment_correction,
    save_direct_shipment_payment,
    save_shipment_atomic,
    save_entrustment_book,
)
from core.logic import calculate_from_shipment
from core.payment_logic import apply_lump_sum_payment


class _Result:
    matched_count = 1
    modified_count = 1
    upserted_id = None


class _FixtureCollection:
    def __init__(self, fail: bool = False):
        self.docs: dict[str, dict] = {}
        self.fail = fail

    def find_one(self, query, projection=None, **kwargs):
        return deepcopy(self.docs.get(query.get("id")))

    def update_one(self, query, update, upsert=False, **kwargs):
        if self.fail:
            raise PyMongoError("fixture second save failure")
        key = query["id"]
        payload = deepcopy(update.get("$set", {}))
        payload.setdefault("id", key)
        self.docs[key] = payload
        return _Result()

    def insert_one(self, document, **kwargs):
        key = document.get("event_id") or document.get("id") or str(uuid4())
        self.docs[key] = deepcopy(document)
        return _Result()


class _FixtureTransaction:
    def __init__(self, db):
        self.db = db
        self.before: dict[str, dict] | None = None

    def __enter__(self):
        self.before = self.db.snapshot()
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None and self.before is not None:
            self.db.restore(self.before)
        return False


class _FixtureSession:
    def __init__(self, db):
        self.db = db

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def start_transaction(self):
        return _FixtureTransaction(self.db)


class _FixtureClient:
    def __init__(self, db):
        self.db = db

    def start_session(self):
        return _FixtureSession(self.db)


class _FixtureDatabase:
    def __init__(self, fail_contract_write: bool = False, transactions: bool = True):
        self.proxy_payments = _FixtureCollection()
        self.contract_transactions = _FixtureCollection(fail=fail_contract_write)
        self.audit_logs = _FixtureCollection()
        self.client = _FixtureClient(self) if transactions else object()

    def __getitem__(self, name):
        return getattr(self, name)

    def snapshot(self):
        return {
            name: deepcopy(getattr(self, name).docs)
            for name in ("proxy_payments", "contract_transactions", "audit_logs")
        }

    def restore(self, snapshot):
        for name, docs in snapshot.items():
            getattr(self, name).docs = docs


_MISSING = object()


def _memory_value(document, path):
    value = document
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return _MISSING
        value = value[part]
    return value


def _memory_matches(document, query):
    if not query:
        return True
    if "$or" in query and not any(_memory_matches(document, branch) for branch in query["$or"]):
        return False
    for key, expected in query.items():
        if key == "$or":
            continue
        actual = _memory_value(document, key)
        if isinstance(expected, dict) and any(str(op).startswith("$") for op in expected):
            if "$ne" in expected and actual is not _MISSING and actual == expected["$ne"]:
                return False
            if "$exists" in expected and (actual is not _MISSING) != bool(expected["$exists"]):
                return False
            continue
        if actual is _MISSING or actual != expected:
            return False
    return True


class _MemoryResult:
    def __init__(self, matched_count=1, modified_count=1):
        self.matched_count = matched_count
        self.modified_count = modified_count
        self.upserted_id = None


class _MemoryCollection:
    def __init__(self, name):
        self.name = name
        self.docs = {}
        self.fail_on_update_calls = set()
        self.fail_on_insert_calls = set()
        self.update_calls = 0
        self.insert_calls = 0

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
            if _memory_matches(document, query):
                return deepcopy(document)
        return None

    def _apply_update(self, document, update):
        for key, value in update.get("$set", {}).items():
            document[key] = deepcopy(value)
        for key, value in update.get("$inc", {}).items():
            document[key] = document.get(key, 0) + value

    def update_one(self, query, update, upsert=False, **kwargs):
        self.update_calls += 1
        if self.update_calls in self.fail_on_update_calls:
            raise PyMongoError(f"fixture forced update failure in {self.name}")
        key = next((key for key, value in self.docs.items() if _memory_matches(value, query)), None)
        if key is None:
            if not upsert:
                return _MemoryResult(matched_count=0, modified_count=0)
            document = {name: value for name, value in query.items() if not name.startswith("$") and not isinstance(value, dict)}
            self._apply_update(document, update)
            document.update(deepcopy(update.get("$setOnInsert", {})))
            key = self._key(document)
            self.docs[key] = document
            return _MemoryResult(matched_count=0, modified_count=1)
        document = deepcopy(self.docs[key])
        self._apply_update(document, update)
        self.docs[key] = document
        return _MemoryResult()

    def insert_one(self, document, **kwargs):
        self.insert_calls += 1
        if self.insert_calls in self.fail_on_insert_calls:
            raise PyMongoError(f"fixture forced insert failure in {self.name}")
        key = self._key(document)
        if key in self.docs:
            raise DuplicateKeyError(f"fixture duplicate key in {self.name}: {key}")
        self.docs[key] = deepcopy(document)
        return _MemoryResult()

    def create_index(self, *args, **kwargs):
        return kwargs.get("name", "fixture-index")

    def count_documents(self, query):
        return sum(1 for document in self.docs.values() if _memory_matches(document, query))


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
    COLLECTION_NAMES = (
        "shipments",
        "financial_action_requests",
        "financial_corrections",
        "entrustments",
        "audit_logs",
        "notification_outbox",
    )

    def __init__(self):
        self.lock = threading.RLock()
        self.client = _MemoryClient(self)
        for name in self.COLLECTION_NAMES:
            setattr(self, name, _MemoryCollection(name))

    def __getitem__(self, name):
        return getattr(self, name)

    def snapshot(self):
        return {name: deepcopy(getattr(self, name).docs) for name in self.COLLECTION_NAMES}

    def restore(self, snapshot):
        for name, docs in snapshot.items():
            getattr(self, name).docs = docs


def _shipment_fixture(shipment_id="SHP-FIXTURE-B1"):
    return {
        "id": shipment_id,
        "customer_id": "CUSTOMER-FIXTURE-B1",
        "customer": "Fixture customer B1",
        "status": "pending",
        "is_deleted": False,
        "is_archived": False,
        "version": 0,
        "data": {
            "0.0": {"created_at": "2026-08-01", "st": "pending"},
            "1.2": {},
            "2.6": {},
            "2.7": {},
            "3.4": {
                "details": [{"qty": 1, "price": 100_000, "cost": 50_000, "vat_line": 0}],
                "commission": {},
                "payments": [],
            },
        },
    }


class ContractProxyAtomicityFixtureTests(unittest.TestCase):
    PAYMENT = {
        "id": "PX-FIXTURE-ATOMIC",
        "contract_id": "CT-FIXTURE-ATOMIC",
        "amount_vnd": 30_000_000,
    }
    TRANSACTION = {
        "id": "PX-FIXTURE-ATOMIC",
        "contract_id": "CT-FIXTURE-ATOMIC",
        "transaction_type": "proxy_payment",
    }

    def test_second_write_failure_rolls_back_both_documents_and_audits(self):
        fixture_db = _FixtureDatabase(fail_contract_write=True)
        with patch("core.database.get_db", return_value=fixture_db), patch("core.database.LOGGER.exception"):
            result = save_contract_proxy_payment_atomic(self.PAYMENT, self.TRANSACTION)

        self.assertFalse(result)
        self.assertEqual(fixture_db.proxy_payments.docs, {})
        self.assertEqual(fixture_db.contract_transactions.docs, {})
        self.assertEqual(fixture_db.audit_logs.docs, {})

    def test_success_writes_pair_and_two_audit_rows(self):
        fixture_db = _FixtureDatabase()
        with patch("core.database.get_db", return_value=fixture_db):
            result = save_contract_proxy_payment_atomic(self.PAYMENT, self.TRANSACTION)

        self.assertTrue(result)
        self.assertIn("PX-FIXTURE-ATOMIC", fixture_db.proxy_payments.docs)
        self.assertIn("PX-FIXTURE-ATOMIC", fixture_db.contract_transactions.docs)
        self.assertEqual(len(fixture_db.audit_logs.docs), 2)

    def test_unsupported_transaction_topology_fails_closed_before_write(self):
        fixture_db = _FixtureDatabase(transactions=False)
        with patch("core.database.get_db", return_value=fixture_db):
            result = save_contract_proxy_payment_atomic(self.PAYMENT, self.TRANSACTION)

        self.assertFalse(result)
        self.assertEqual(fixture_db.proxy_payments.docs, {})
        self.assertEqual(fixture_db.contract_transactions.docs, {})


class DirectFinancialWriteFixtureTests(unittest.TestCase):
    def setUp(self):
        self.db = _MemoryDatabase()
        self.db.shipments.insert_one(_shipment_fixture())

    def _payment(self, request_id, payment_id, amount=40_000):
        return {
            "id": payment_id,
            "request_id": request_id,
            "date": "2026-08-14",
            "note": "fixture direct payment",
            "amount": amount,
        }

    def test_same_request_is_idempotent_but_legitimate_equal_payment_is_accepted(self):
        with patch("core.database.get_db", return_value=self.db):
            first = save_direct_shipment_payment(
                "SHP-FIXTURE-B1",
                self._payment("REQ-A", "PAY-A"),
                actor="fixture",
            )
            retry = save_direct_shipment_payment(
                "SHP-FIXTURE-B1",
                self._payment("REQ-A", "PAY-A-RETRY"),
                actor="fixture",
            )
            legitimate = save_direct_shipment_payment(
                "SHP-FIXTURE-B1",
                self._payment("REQ-B", "PAY-B"),
                actor="fixture",
            )
            mismatch = save_direct_shipment_payment(
                "SHP-FIXTURE-B1",
                self._payment("REQ-A", "PAY-A-MISMATCH", amount=45_000),
                actor="fixture",
            )

        self.assertTrue(first[0], first[2])
        self.assertTrue(retry[0], retry[2])
        self.assertTrue(legitimate[0], legitimate[2])
        self.assertFalse(mismatch[0])
        self.assertEqual(first[1]["payment_id"], retry[1]["payment_id"])
        saved = self.db.shipments.find_one({"id": "SHP-FIXTURE-B1"})
        payments = saved["data"]["3.4"]["payments"]
        self.assertEqual(len(payments), 2)
        self.assertEqual(calculate_from_shipment(saved)["paid"], 80_000)
        self.assertEqual(calculate_from_shipment(saved)["debt"], 20_000)
        self.assertEqual(self.db.financial_action_requests.count_documents({}), 2)

    def test_failure_after_shipment_update_rolls_back_and_retry_is_safe(self):
        self.db.financial_action_requests.fail_on_insert_calls = {1}
        with patch("core.database.get_db", return_value=self.db):
            failed = save_direct_shipment_payment(
                "SHP-FIXTURE-B1",
                self._payment("REQ-FAIL", "PAY-FAIL"),
                actor="fixture",
            )
        self.assertFalse(failed[0])
        self.assertEqual(self.db.shipments.find_one({"id": "SHP-FIXTURE-B1"})["data"]["3.4"]["payments"], [])
        self.assertEqual(self.db.financial_action_requests.docs, {})
        self.assertEqual(self.db.audit_logs.docs, {})
        self.assertEqual(self.db.notification_outbox.docs, {})

        self.db.financial_action_requests.fail_on_insert_calls = set()
        with patch("core.database.get_db", return_value=self.db):
            retried = save_direct_shipment_payment(
                "SHP-FIXTURE-B1",
                self._payment("REQ-FAIL", "PAY-FAIL-RETRY"),
                actor="fixture",
            )
            duplicate_retry = save_direct_shipment_payment(
                "SHP-FIXTURE-B1",
                self._payment("REQ-FAIL", "PAY-FAIL-DUPLICATE"),
                actor="fixture",
            )

        self.assertTrue(retried[0], retried[2])
        self.assertTrue(duplicate_retry[0], duplicate_retry[2])
        saved = self.db.shipments.find_one({"id": "SHP-FIXTURE-B1"})
        self.assertEqual(len(saved["data"]["3.4"]["payments"]), 1)
        self.assertEqual(calculate_from_shipment(saved)["paid"], 40_000)

    def test_direct_write_fails_closed_without_transaction_support(self):
        self.db.client = object()
        with patch("core.database.get_db", return_value=self.db):
            result = save_direct_shipment_payment(
                "SHP-FIXTURE-B1",
                self._payment("REQ-NO-TX", "PAY-NO-TX"),
                actor="fixture",
            )
        self.assertFalse(result[0])
        self.assertEqual(self.db.shipments.find_one({"id": "SHP-FIXTURE-B1"})["data"]["3.4"]["payments"], [])
        self.assertEqual(self.db.financial_action_requests.docs, {})

    def test_correction_preserves_original_and_recomputes_derived_balance(self):
        with patch("core.database.get_db", return_value=self.db):
            created = save_direct_shipment_payment(
                "SHP-FIXTURE-B1",
                self._payment("REQ-CORR-PAY", "PAY-CORR"),
                actor="fixture",
            )
            correction = save_direct_payment_correction(
                "SHP-FIXTURE-B1",
                created[1]["payment_id"],
                "REQ-CORR-1",
                "Nhập nhầm khoản thu fixture",
                evidence={"kind": "fixture-proof"},
                actor="fixture",
            )
            retry = save_direct_payment_correction(
                "SHP-FIXTURE-B1",
                created[1]["payment_id"],
                "REQ-CORR-1",
                "Nhập nhầm khoản thu fixture",
                evidence={"kind": "fixture-proof"},
                actor="fixture",
            )

        self.assertTrue(created[0], created[2])
        self.assertTrue(correction[0], correction[2])
        self.assertTrue(retry[0], retry[2])
        self.assertEqual(correction[1], retry[1])
        saved = self.db.shipments.find_one({"id": "SHP-FIXTURE-B1"})
        payment = saved["data"]["3.4"]["payments"][0]
        self.assertEqual(payment["id"], "PAY-CORR")
        self.assertEqual(payment["status"], "reversed")
        self.assertTrue(payment["is_reversed"])
        self.assertEqual(calculate_from_shipment(saved)["paid"], 0)
        self.assertEqual(calculate_from_shipment(saved)["debt"], 100_000)
        correction_doc = self.db.financial_corrections.find_one({"correction_request_id": "REQ-CORR-1"})
        self.assertEqual(correction_doc["original_id"], "PAY-CORR")
        self.assertEqual(correction_doc["reason"], "Nhập nhầm khoản thu fixture")
        self.assertEqual(self.db.financial_corrections.count_documents({}), 1)


class EntrustmentBatchFixtureTests(unittest.TestCase):
    def _documents(self, count=3):
        return {
            f"ENT-{index}": {
                "linked_type": "fixture",
                "linked_id": f"SHP-{index}",
                "payments": [],
            }
            for index in range(1, count + 1)
        }

    def test_second_and_middle_failure_are_all_or_nothing(self):
        for count, fail_call in ((2, 2), (3, 2)):
            with self.subTest(count=count):
                db = _MemoryDatabase()
                db.entrustments.fail_on_update_calls = {fail_call}
                with patch("core.database.get_db", return_value=db):
                    result = save_entrustment_book(
                        self._documents(count),
                        request_id=f"ENT-FAIL-{count}",
                        actor="fixture",
                    )
                self.assertFalse(result)
                self.assertEqual(db.entrustments.docs, {})
                self.assertEqual(db.financial_action_requests.docs, {})
                self.assertEqual(db.audit_logs.docs, {})

    def test_failed_batch_retry_and_successful_duplicate_are_safe(self):
        db = _MemoryDatabase()
        db.entrustments.fail_on_update_calls = {2}
        documents = self._documents(3)
        with patch("core.database.get_db", return_value=db):
            failed = save_entrustment_book(documents, request_id="ENT-RETRY", actor="fixture")
        self.assertFalse(failed)
        self.assertEqual(db.entrustments.docs, {})

        db.entrustments.fail_on_update_calls = set()
        with patch("core.database.get_db", return_value=db):
            retried = save_entrustment_book(documents, request_id="ENT-RETRY", actor="fixture")
            duplicate = save_entrustment_book(documents, request_id="ENT-RETRY", actor="fixture")

        self.assertTrue(retried)
        self.assertTrue(duplicate)
        self.assertEqual(len(db.entrustments.docs), 3)
        self.assertEqual(db.financial_action_requests.count_documents({}), 1)
        self.assertEqual(len(db.audit_logs.docs), 3)

    def test_batch_fails_closed_without_transaction_support(self):
        db = _MemoryDatabase()
        db.client = object()
        with patch("core.database.get_db", return_value=db):
            result = save_entrustment_book(
                self._documents(2),
                request_id="ENT-NO-TX",
                actor="fixture",
            )
        self.assertFalse(result)
        self.assertEqual(db.entrustments.docs, {})
        self.assertEqual(db.financial_action_requests.docs, {})


class MongoPersistenceFixtureTests(unittest.TestCase):
    """Opt-in tests against a newly generated, disposable Mongo database."""

    @classmethod
    def setUpClass(cls):
        if os.environ.get("LOG_C02_RUN_MONGO_FIXTURES") != "1":
            raise unittest.SkipTest("set LOG_C02_RUN_MONGO_FIXTURES=1 for isolated Mongo proof")
        if not MONGO_URI:
            raise unittest.SkipTest("Mongo URI is not configured")

        cls.client = init_connection()
        if cls.client is None:
            raise unittest.SkipTest("Mongo is not reachable")
        # Atlas limits database names to 38 bytes; keep the safety prefix and
        # use a short random suffix so the generated target remains valid.
        cls.db_name = f"l02b0_{uuid4().hex[:16]}"
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
        self.cls = type(self)
        self.cls.created_fixture = True

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
        return fresh_client, fresh_client[self.cls.db_name]

    def test_contract_proxy_pair_persists_and_reads_back_from_fresh_client(self):
        payment_id = "PX-MONGO-FIXTURE-ATOMIC"
        payment = {
            "id": payment_id,
            "contract_id": "CT-MONGO-FIXTURE",
            "amount_vnd": 30_000_000,
            "currency": "CNY",
            "amount_fc_needed": 62_464,
            "amount_fc_paid": 0,
            "amount_fc_remain": 62_464,
        }
        transaction = {
            "id": payment_id,
            "contract_id": "CT-MONGO-FIXTURE",
            "transaction_type": "proxy_payment",
            "amount_vnd": 30_000_000,
        }

        with patch("core.database.get_db", return_value=self.cls.db):
            self.assertTrue(save_contract_proxy_payment_atomic(payment, transaction))

        fresh_client, fresh_db = self._fresh_db()
        try:
            self.assertIsNotNone(fresh_db.proxy_payments.find_one({"id": payment_id}))
            self.assertIsNotNone(fresh_db.contract_transactions.find_one({"id": payment_id}))
            self.assertEqual(fresh_db.audit_logs.count_documents({"entity_id": payment_id}), 2)
        finally:
            fresh_client.close()

    def test_lump_sum_payment_is_durable_derived_and_idempotent_after_reload(self):
        shipment_id = "SHP-MONGO-FIXTURE-PAYMENT"
        shipment = {
            "id": shipment_id,
            "customer_id": "CUSTOMER-MONGO-FIXTURE",
            "customer": "Fixture customer",
            "status": "pending",
            "is_deleted": False,
            "is_archived": False,
            "version": 0,
            "data": {
                "0.0": {"created_at": "2026-08-01", "st": "pending"},
                "1.2": {},
                "2.6": {},
                "2.7": {},
                "3.4": {
                    "details": [{"qty": 1, "price": 100_000, "cost": 0, "vat_line": 0}],
                    "commission": {},
                    "payments": [],
                },
            },
        }
        self.cls.db.shipments.insert_one(deepcopy(shipment))

        with patch("core.database.get_db", return_value=self.cls.db):
            first = apply_lump_sum_payment(
                customer_ref="CUSTOMER-MONGO-FIXTURE",
                amount=40_000,
                all_shipments={shipment_id: shipment},
                payment_date="2026-08-14",
                note="fixture payment",
                idempotency_key="fixture-payment-key-1",
                actor="fixture",
            )
            retry = apply_lump_sum_payment(
                customer_ref="CUSTOMER-MONGO-FIXTURE",
                amount=40_000,
                all_shipments={shipment_id: shipment},
                payment_date="2026-08-14",
                note="fixture payment",
                idempotency_key="fixture-payment-key-1",
                actor="fixture",
            )

        self.assertTrue(first[0], first[3])
        self.assertTrue(retry[0], retry[3])
        self.assertEqual(self.cls.db.payment_receipts.count_documents({"idempotency_key": "fixture-payment-key-1"}), 1)

        fresh_client, fresh_db = self._fresh_db()
        try:
            readback = fresh_db.shipments.find_one({"id": shipment_id})
            self.assertIsNotNone(readback)
            summary = calculate_from_shipment(readback)
            self.assertEqual(summary["paid"], 40_000)
            self.assertEqual(summary["debt"], 60_000)
            self.assertEqual(len(readback["data"]["3.4"]["payments"]), 1)
        finally:
            fresh_client.close()

    def test_single_shipment_save_is_durable_and_balance_is_derived_after_reload(self):
        shipment = {
            "id": "SHP-MONGO-FIXTURE-DIRECT",
            "customer": "Fixture direct customer",
            "status": "pending",
            "data": {
                "0.0": {"created_at": "2026-08-01", "st": "pending"},
                "1.2": {},
                "2.6": {},
                "2.7": {},
                "3.4": {
                    "details": [{"qty": 1, "price": 120_000, "cost": 50_000, "vat_line": 0}],
                    "commission": {},
                    "payments": [],
                },
            },
        }

        with patch("core.database.get_db", return_value=self.cls.db):
            self.assertTrue(save_shipment_atomic(shipment))
            created = save_direct_shipment_payment(
                shipment["id"],
                {
                    "id": "PAY-MONGO-FIXTURE-DIRECT",
                    "request_id": "REQ-MONGO-FIXTURE-DIRECT",
                    "amount": 20_000,
                    "date": "2026-08-14",
                },
                actor="fixture",
            )
        self.assertTrue(created[0], created[2])

        fresh_client, fresh_db = self._fresh_db()
        try:
            readback = fresh_db.shipments.find_one({"id": shipment["id"]})
            self.assertIsNotNone(readback)
            summary = calculate_from_shipment(readback)
            self.assertEqual(summary["paid"], 20_000)
            self.assertEqual(summary["debt"], 100_000)
        finally:
            fresh_client.close()

    def test_direct_payment_equal_legitimate_action_correction_and_fresh_readback(self):
        shipment_id = "SHP-MONGO-FIXTURE-B1-DIRECT"
        self.cls.db.shipments.insert_one(_shipment_fixture(shipment_id))
        with patch("core.database.get_db", return_value=self.cls.db):
            first = save_direct_shipment_payment(
                shipment_id,
                {"id": "PAY-MONGO-B1-A", "request_id": "REQ-MONGO-B1-A", "amount": 40_000, "date": "2026-08-14"},
                actor="fixture",
            )
            retry = save_direct_shipment_payment(
                shipment_id,
                {"id": "PAY-MONGO-B1-A-RETRY", "request_id": "REQ-MONGO-B1-A", "amount": 40_000, "date": "2026-08-14"},
                actor="fixture",
            )
            second = save_direct_shipment_payment(
                shipment_id,
                {"id": "PAY-MONGO-B1-B", "request_id": "REQ-MONGO-B1-B", "amount": 40_000, "date": "2026-08-14"},
                actor="fixture",
            )
            correction = save_direct_payment_correction(
                shipment_id,
                first[1]["payment_id"],
                "REQ-MONGO-B1-CORR",
                "fixture correction",
                evidence={"fixture": True},
                actor="fixture",
            )
            correction_retry = save_direct_payment_correction(
                shipment_id,
                first[1]["payment_id"],
                "REQ-MONGO-B1-CORR",
                "fixture correction",
                evidence={"fixture": True},
                actor="fixture",
            )

        for result in (first, retry, second, correction, correction_retry):
            self.assertTrue(result[0], result[2])
        self.assertEqual(first[1]["payment_id"], retry[1]["payment_id"])
        self.assertEqual(correction[1], correction_retry[1])

        fresh_client, fresh_db = self._fresh_db()
        try:
            readback = fresh_db.shipments.find_one({"id": shipment_id})
            self.assertIsNotNone(readback)
            self.assertEqual(len(readback["data"]["3.4"]["payments"]), 2)
            reversed_rows = [row for row in readback["data"]["3.4"]["payments"] if row.get("is_reversed")]
            self.assertEqual(len(reversed_rows), 1)
            summary = calculate_from_shipment(readback)
            self.assertEqual(summary["paid"], 40_000)
            self.assertEqual(summary["debt"], 60_000)
            self.assertEqual(fresh_db.financial_corrections.count_documents({"correction_request_id": "REQ-MONGO-B1-CORR"}), 1)
        finally:
            fresh_client.close()

    def test_direct_payment_same_identity_concurrent_submit_has_one_effect(self):
        shipment_id = "SHP-MONGO-FIXTURE-B1-CONCURRENT"
        self.cls.db.shipments.insert_one(_shipment_fixture(shipment_id))

        def submit(index):
            return save_direct_shipment_payment(
                shipment_id,
                {
                    "id": f"PAY-MONGO-B1-CONCURRENT-{index}",
                    "request_id": "REQ-MONGO-B1-CONCURRENT",
                    "amount": 30_000,
                    "date": "2026-08-14",
                },
                actor="fixture",
            )

        with patch("core.database.get_db", return_value=self.cls.db):
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(submit, (1, 2)))

        self.assertTrue(any(result[0] for result in results))
        fresh_client, fresh_db = self._fresh_db()
        try:
            readback = fresh_db.shipments.find_one({"id": shipment_id})
            self.assertIsNotNone(readback)
            self.assertEqual(len(readback["data"]["3.4"]["payments"]), 1)
            self.assertEqual(fresh_db.financial_action_requests.count_documents({"request_id": "REQ-MONGO-B1-CONCURRENT"}), 1)
        finally:
            fresh_client.close()

    def test_entrustment_batch_is_durable_idempotent_and_reads_back_from_fresh_client(self):
        documents = {
            "ENT-MONGO-B1-A": {"linked_type": "fixture", "linked_id": "SHP-MONGO-B1-A", "payments": []},
            "ENT-MONGO-B1-B": {"linked_type": "fixture", "linked_id": "SHP-MONGO-B1-B", "payments": []},
        }
        with patch("core.database.get_db", return_value=self.cls.db):
            first = save_entrustment_book(documents, request_id="ENT-REQ-MONGO-B1", actor="fixture")
            duplicate = save_entrustment_book(documents, request_id="ENT-REQ-MONGO-B1", actor="fixture")
        self.assertTrue(first)
        self.assertTrue(duplicate)

        fresh_client, fresh_db = self._fresh_db()
        try:
            self.assertIsNotNone(fresh_db.entrustments.find_one({"id": "ENT-MONGO-B1-A"}))
            self.assertIsNotNone(fresh_db.entrustments.find_one({"id": "ENT-MONGO-B1-B"}))
            self.assertEqual(fresh_db.financial_action_requests.count_documents({"request_id": "ENT-REQ-MONGO-B1"}), 1)
        finally:
            fresh_client.close()


if __name__ == "__main__":
    unittest.main()
