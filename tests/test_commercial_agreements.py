"""LOG-C13 tests: commercial agreement domain, persistence contract, and
commercial review-queue signals.

Guarantees under test:
1. An agreement is a quote-inherited snapshot: identity, line items, FX rates,
   factory lots, entrusted-import terms and assumptions carry over verbatim.
2. Agreement persistence writes ONLY the `agreements` collection via the
   generic document upsert; the financial ledger (financial_transactions,
   contract_transactions, proxy_payments, obligations, allocations) is never
   mutated.
3. Handoff readiness is a pure read-only evaluation: MISSING_REQUIRED_DATA,
   NEEDS_COMMERCIAL_REVIEW, and READY_FOR_OPERATIONS are decided from explicit
   evidence and document states, never guessed.
4. AGREED agreements cannot silently go back to DRAFT; transitions produce a
   new version with a status_history entry.
5. Commercial review-queue signals surface blocked handoffs as read-only items
   with `agreement`/`quote` navigation targets.
"""

from __future__ import annotations

import copy
import re
import unittest
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch

from pymongo.errors import DuplicateKeyError, PyMongoError

from core.commercial_agreements import (
    Allowed_TRANSITIONS as ALLOWED_TRANSITIONS,
    AGREEMENT_STATUSES,
    HANDOFF_COMMERCIAL_REVIEW,
    HANDOFF_MISSING_REQUIRED_DATA,
    HANDOFF_READY,
    agreements_for_quote,
    agreements_for_shipment,
    build_agreement_from_quote,
    commercial_handoff_view,
    handoff_readiness,
    normalize_required_documents,
    prepare_agreement_for_persistence,
    transition_agreement,
)
from core.database import save_agreements_to_cloud


def _q(**overrides):
    base = {
        "id": "Q-C13-0001",
        "quote_no": "Q-20260817-C1301",
        "customer_id": "CUST-C13-1",
        "customer_name": "Fixture customer C13",
        "status": "ACCEPTED",
        "version": 2,
        "origin": "Trung Quốc",
        "destination": "Việt Nam",
        "route": "Hữu Nghị",
        "incoterm": "EXW",
        "transport_mode": "Road",
        "goods_description": "Máy móc fixture",
        "expected_delivery_date": "2026-09-15",
        "service_lines": [
            {
                "line_no": 1,
                "code": "EXW1",
                "service_name": "Vận chuyển EXW",
                "unit": "Lô",
                "qty": 2,
                "currency": "VND",
                "cost_unit": 1_000_000,
                "sell_unit": 1_500_000,
                "tax_pct": 8,
            },
            {
                "line_no": 2,
                "code": "UTT",
                "service_name": "Ủy thác nhập khẩu",
                "unit": "% giá trị",
                "qty": 1,
                "currency": "USD",
                "cost_unit": 0,
                "sell_unit": 100,
                "tax_pct": 8,
            },
        ],
        "factory_lots": [
            {
                "lot_no": 1,
                "factory_name": "Fixture Factory Alpha",
                "factory_contact": "Mr. Fix",
                "factory_phone": "+8612345",
                "ready_date": "2026-08-30",
                "pickup_address": "Dongguan fixture",
            },
            {
                "lot_no": 2,
                "factory_name": "Fixture Factory Beta",
                "factory_contact": "Ms. Beta",
                "factory_phone": "+8677777",
                "ready_date": "2026-09-01",
                "pickup_address": "Shenzhen fixture",
            },
        ],
        "fx_snapshot": {"rates_to_vnd": {"USD": 25500, "CNY": 3500}},
        "entrusted_import": {
            "active": True,
            "goods_value": 80000,
            "goods_currency": "USD",
            "rate_pct": 2.5,
        },
        "fees": {"entrusted_import": {"formula": "fixtures formula"}},
        "calculation": {"selling_price_total_vnd": 3_120_000, "estimated_margin_vnd": 500_000},
        "assumptions": ["Fixture assumption A", "Fixture assumption B"],
    }
    base.update(overrides)
    return base


class AgreementDomainTests(unittest.TestCase):
    def test_identity_format_is_valid(self):
        agr = build_agreement_from_quote(_q(), actor="S")
        self.assertTrue(re.match(r"^AGR-\d{8}-[0-9A-F]{8}$", agr["agreement_id"]), agr["agreement_id"])
        self.assertTrue(re.match(r"^AG-\d{8}-[0-9A-F]{8}$", agr["agreement_no"]), agr["agreement_no"])

    def test_agreement_inherits_quote_snapshot_verbatim(self):
        agr = build_agreement_from_quote(_q(), actor="F-ACTOR")
        self.assertEqual(agr["quote_id"], "Q-C13-0001")
        self.assertEqual(agr["quote_reference"], "Q-20260817-C1301")
        self.assertEqual(agr["quote_version"], 2)
        self.assertEqual(agr["customer_id"], "CUST-C13-1")
        self.assertEqual(len(agr["commercial_snapshot"]["service_lines"]), 2)
        self.assertEqual(agr["commercial_snapshot"]["fx_summary"]["rates_to_vnd"], {"USD": 25500, "CNY": 3500})
        self.assertEqual(len(agr["factory_lots"]), 2)
        self.assertEqual(agr["entrusted_import_terms"]["rate_pct"], 2.5)
        self.assertEqual(agr["assumptions"], ["Fixture assumption A", "Fixture assumption B"])
        self.assertEqual(agr["status"], "DRAFT")
        self.assertFalse(agr["ledger_posted"])

    def test_missing_core_data_blocks_handoff(self):
        agr = build_agreement_from_quote(_q(), actor="F")
        for field in ("quote_id", "customer_id"):
            broken = copy.deepcopy(agr)
            broken[field] = ""
            self.assertEqual(handoff_readiness(broken)["state"], HANDOFF_MISSING_REQUIRED_DATA, field)

    def test_empty_service_lines_block_handoff_but_empty_factory_lots_do_not(self):
        agr = build_agreement_from_quote(_q(), actor="F")
        broken = copy.deepcopy(agr)
        broken["commercial_snapshot"]["service_lines"] = []
        self.assertEqual(handoff_readiness(broken)["state"], HANDOFF_MISSING_REQUIRED_DATA)
        no_lots = copy.deepcopy(agr)
        no_lots["factory_lots"] = []
        readiness = handoff_readiness(no_lots)
        self.assertEqual(readiness["state"], HANDOFF_COMMERCIAL_REVIEW)
        self.assertTrue(any("nhà máy" in reason for reason in readiness["reasons"]))

    def test_not_agreed_or_no_evidence_blocks_handoff(self):
        agr = build_agreement_from_quote(_q(), actor="F")
        agr = transition_agreement(agr, "REVIEWING", actor="F")
        readiness = handoff_readiness(agr)
        self.assertEqual(readiness["state"], HANDOFF_COMMERCIAL_REVIEW)
        self.assertTrue(any("đồng ý" in reason for reason in readiness["reasons"]))
        agr["evidence"]["accepted_quotation"] = True
        self.assertEqual(handoff_readiness(agr)["state"], HANDOFF_COMMERCIAL_REVIEW)
        self.assertTrue(any("đồng ý" in reason for reason in handoff_readiness(agr)["reasons"]))
        agr = transition_agreement(agr, "AGREED", actor="F")
        self.assertEqual(handoff_readiness(agr)["state"], HANDOFF_READY)

    def test_missing_document_states_block_handoff(self):
        agr = build_agreement_from_quote(_q(), actor="F")
        agr = transition_agreement(agr, "REVIEWING", actor="F")
        agr = transition_agreement(agr, "AGREED", actor="F")
        agr["evidence"]["accepted_quotation"] = True
        self.assertEqual(handoff_readiness(agr)["state"], HANDOFF_READY)
        agr["required_documents"] = normalize_required_documents([
            {"name": "Commercial Invoice", "evidence_state": "missing"},
        ])
        self.assertEqual(handoff_readiness(agr)["state"], HANDOFF_COMMERCIAL_REVIEW)
        agr["required_documents"][0]["evidence_state"] = "WAITING"
        self.assertEqual(handoff_readiness(agr)["state"], HANDOFF_COMMERCIAL_REVIEW)
        agr["required_documents"][0]["evidence_state"] = "AVAILABLE"
        self.assertEqual(handoff_readiness(agr)["state"], HANDOFF_READY)

    def test_unresolved_issues_block_handoff(self):
        agr = build_agreement_from_quote(_q(), actor="F")
        agr = transition_agreement(agr, "REVIEWING", actor="F")
        agr = transition_agreement(agr, "AGREED", actor="F")
        agr["evidence"]["accepted_quotation"] = True
        agr["unresolved_issues"] = ["Khách chưa chốt kho giao nhận cuối"]
        self.assertEqual(handoff_readiness(agr)["state"], HANDOFF_COMMERCIAL_REVIEW)

    def test_void_agreement_excluded_from_review_queue_signals(self):
        agr = build_agreement_from_quote(_q(), actor="F")
        agr = transition_agreement(agr, "REVIEWING", actor="F")
        agr = transition_agreement(agr, "AGREED", actor="F")
        agr["evidence"]["accepted_quotation"] = True
        agr["required_documents"] = [{"name": "Inv", "evidence_state": "MISSING"}]
        agr = transition_agreement(agr, "REVISED", actor="F")
        agr = transition_agreement(agr, "VOID", actor="F")
        from core.review_queue import build_review_queue_items
        items = build_review_queue_items(
            {"SHP-C13-1": {}},
            agreements={agr["agreement_id"]: agr},
            quotes={"Q-C13-0001": _q()},
        )
        agreement_signals = [item for item in items if item.get("target", {}).get("kind") == "agreement"]
        self.assertEqual(agreement_signals, [])

    def test_handoff_view_has_sixteen_questions_and_explicit_unknowns(self):
        agr = build_agreement_from_quote(_q(), actor="F")
        agr = transition_agreement(agr, "REVIEWING", actor="F")
        agr = transition_agreement(agr, "AGREED", actor="F")
        agr["evidence"]["accepted_quotation"] = True
        view = commercial_handoff_view(None, agr, _q(), {})
        self.assertEqual(len(view["questions"]), 16)
        self.assertEqual(view["readiness"]["state"], HANDOFF_READY)
        self.assertEqual(len(view["factory_lots"]), 2)

    def test_transition_matrix(self):
        allowed = {
            ("DRAFT", "REVIEWING"), ("DRAFT", "VOID"), ("DRAFT", "DRAFT"),
            ("REVIEWING", "DRAFT"), ("REVIEWING", "AGREED"), ("REVIEWING", "REVIEWING"), ("REVIEWING", "REVISED"), ("REVIEWING", "VOID"),
            ("AGREED", "REVISED"), ("AGREED", "AGREED"),
            ("REVISED", "DRAFT"), ("REVISED", "REVIEWING"), ("REVISED", "REVISED"), ("REVISED", "VOID"),
            ("VOID", "VOID"),
        }
        for source in AGREEMENT_STATUSES:
            for target in AGREEMENT_STATUSES:
                try:
                    transition_agreement({"status": source, "version": 1, "agreement_id": "X"}, target, actor="F")
                except ValueError:
                    self.assertNotIn((source, target), allowed, f"{source}->{target} allowed unexpectedly")
                else:
                    self.assertIn((source, target), allowed, f"{source}->{target} blocked unexpectedly")

    def test_transition_bumps_version_and_records_history(self):
        agr = build_agreement_from_quote(_q(), actor="F")
        agr = transition_agreement(agr, "REVIEWING", actor="F")
        self.assertEqual(agr["version"], 2)
        targets = [entry["to"] for entry in agr["status_history"]]
        self.assertEqual(targets, ["DRAFT", "REVIEWING"])
        agr = transition_agreement(agr, "AGREED", actor="F")
        self.assertEqual(agr["version"], 3)
        with self.assertRaises(ValueError):
            transition_agreement(agr, "DRAFT", actor="F")
        with self.assertRaises(ValueError):
            transition_agreement(agr, "REVIEWING", actor="F")

    def test_agreed_cannot_be_overwritten_silently(self):
        agr = build_agreement_from_quote(_q(), actor="F")
        agr = transition_agreement(agr, "REVIEWING", actor="F")
        agr = transition_agreement(agr, "AGREED", actor="F")
        with self.assertRaises(ValueError):
            transition_agreement(agr, "DRAFT", actor="F")
        with self.assertRaises(ValueError):
            transition_agreement(agr, "REVIEWING", actor="F")


class AgreementPersistenceTests(unittest.TestCase):
    class _MemoryCollection:
        def __init__(self, name):
            self.name = name
            self.docs = {}
            self.upsert_calls = 0
            self.fail_on_update_calls = set()

        def find_one(self, query, projection=None, **kwargs):
            del projection
            for document in self.docs.values():
                if document.get("agreement_id") == query.get("agreement_id") and document.get("version") == query.get("version"):
                    return dict(document)
            return None

        def update_one(self, query, update, **kwargs):
            self.upsert_calls += 1
            if self.upsert_calls in self.fail_on_update_calls:
                raise PyMongoError("fixture upsert failure")
            for document in self.docs.values():
                if all(document.get(k) == v for k, v in query.items() if not k.startswith("$")):
                    document.update(update.get("$set", {}))
                    document.update(update.get("$setOnInsert", {}))
                    return self
            if kwargs.get("upsert"):
                document = {name: value for name, value in query.items() if not name.startswith("$") and not isinstance(value, dict)}
                document.update(update.get("$set", {}))
                document.update(update.get("$setOnInsert", {}))
                key = f"{document.get('agreement_id') or document.get('id')}:v{document.get('version')}"
                self.docs[key] = document
            return self

        def insert_one(self, document, **kwargs):
            key = str(document.get("event_id") or len(self.docs))
            self.docs[key] = dict(document)
            return self

        def create_index(self, *args, **kwargs):
            return kwargs.get("name", "fixture")

    class _MemoryDatabase:
        def __init__(self):
            self.agreements = AgreementPersistenceTests._MemoryCollection("agreements")
            self.audit_logs = AgreementPersistenceTests._MemoryCollection("audit_logs")

        def __getitem__(self, name):
            return getattr(self, name)

    def setUp(self):
        self.auth_patch = patch(
            "core.auth.st",
            SimpleNamespace(
                session_state={
                    "current_user": {
                        "user_id": "sale-fixture-01",
                        "username": "sale.fixture",
                        "display_name": "Sale Fixture",
                        "role": "sale",
                    }
                }
            ),
        )
        self.auth_patch.start()
        self.addCleanup(self.auth_patch.stop)
        self.db = self._MemoryDatabase()

    def test_persistence_writes_only_agreements_collection(self):
        agr = build_agreement_from_quote(_q(), actor="F")
        stamped = prepare_agreement_for_persistence(agr, actor="F")
        stamped["id"] = stamped["agreement_id"]
        with patch("core.database.get_db", return_value=self.db):
            result = save_agreements_to_cloud({"key": stamped})
        self.assertTrue(result)
        self.assertEqual(self.db.agreements.upsert_calls, 1)
        self.assertIn(stamped["agreement_id"], {document["agreement_id"] for document in self.db.agreements.docs.values()})
        self.assertFalse(stamped["ledger_posted"])
        self.assertEqual(stamped["provenance"]["source"], "LOG-C13 commercial agreement workspace")

    def test_same_version_is_idempotent_via_upsert(self):
        """Same agreement identity upserts on `id`; identical version overwrites
        itself harmlessly, while a newer revision replaces the older doc."""
        agr = build_agreement_from_quote(_q(), actor="F")
        first = prepare_agreement_for_persistence(agr, actor="F")
        revision_doc = copy.deepcopy(agr)
        revision_doc["evidence"]["accepted_quotation"] = True
        revision_doc = transition_agreement(revision_doc, "REVIEWING", actor="F")
        second = prepare_agreement_for_persistence(revision_doc, actor="F")
        with patch("core.database.get_db", return_value=self.db):
            self.assertTrue(save_agreements_to_cloud({"key": first}))
            self.assertTrue(save_agreements_to_cloud({"key": first}))
            self.assertTrue(save_agreements_to_cloud({"key": second}))
        self.assertEqual(self.db.agreements.upsert_calls, 3)
        self.assertEqual(len(self.db.agreements.docs), 1)
        stored = next(iter(self.db.agreements.docs.values()))
        self.assertEqual(stored["version"], 2)
        self.assertEqual(stored["status"], "REVIEWING")
        self.assertEqual(stored["evidence"]["accepted_quotation"], True)

    def test_save_returns_false_on_transient_failure(self):
        agr = build_agreement_from_quote(_q(), actor="F")
        self.db.agreements.fail_on_update_calls = {1}
        stamped = prepare_agreement_for_persistence(agr, actor="F")
        with patch("core.database.get_db", return_value=self.db):
            result = save_agreements_to_cloud({"key": stamped})
        self.assertFalse(result)
        self.assertEqual(self.db.agreements.docs, {})

    def test_financial_ledger_collections_untouched(self):
        agr = build_agreement_from_quote(_q(), actor="F")
        stamped = prepare_agreement_for_persistence(agr, actor="F")
        stamped["id"] = stamped["agreement_id"]
        with patch("core.database.get_db", return_value=self.db):
            save_agreements_to_cloud({"key": stamped})
        for name in ("financial_transactions", "contract_transactions", "proxy_payments", "financial_action_requests"):
            with self.subTest(collection=name):
                self.assertFalse(hasattr(self.db, name) and getattr(self.db, name).docs)


class AgreementReviewQueueSignalTests(unittest.TestCase):
    def test_accepted_quote_without_agreement_raises_attention_signal(self):
        from core.review_queue import build_review_queue_items, CATEGORY_COMMERCIAL
        items = build_review_queue_items(
            {"SHP-C13-Q1": {}},
            agreements={},
            quotes={"Q-C13-0001": _q()},
        )
        commercial = [item for item in items if item.get("category") == CATEGORY_COMMERCIAL]
        self.assertEqual(len(commercial), 1)
        self.assertIn("COMMERCIAL_QUOTE_UNCOVERED", commercial[0]["item_id"])
        self.assertEqual(commercial[0]["target"]["kind"], "quote")

    def test_linked_agreement_suppresses_quote_signal(self):
        from core.review_queue import build_review_queue_items
        agr = build_agreement_from_quote(_q(), actor="F")
        items = build_review_queue_items(
            {"SHP-C13-Q1": {}},
            agreements={agr["agreement_id"]: agr},
            quotes={"Q-C13-0001": _q()},
        )
        commercial = [item for item in items if item.get("code") == "COMMERCIAL_QUOTE_UNCOVERED"]
        self.assertEqual(commercial, [])

    def test_not_ready_agreement_raises_blocking_signal_with_target(self):
        from core.review_queue import build_review_queue_items
        agr = build_agreement_from_quote(_q(), actor="F")
        agr = transition_agreement(agr, "REVIEWING", actor="F")
        agr["shipment_ids"] = ["SHP-C13-A1"]
        items = build_review_queue_items(
            {"SHP-C13-A1": {}},
            agreements={agr["agreement_id"]: agr},
            quotes={"Q-C13-0001": _q()},
        )
        blocked = [item for item in items if item.get("target", {}).get("kind") == "agreement"]
        self.assertEqual(len(blocked), 1)
        self.assertIn(blocked[0]["status"], ("WAITING", "NEEDS ATTENTION"))
        self.assertIn("Thỏa thuận thương mại", blocked[0]["title"])

    def test_ready_agreement_absent_from_queue(self):
        from core.review_queue import build_review_queue_items
        agr = build_agreement_from_quote(_q(), actor="F")
        agr = transition_agreement(agr, "REVIEWING", actor="F")
        agr = transition_agreement(agr, "AGREED", actor="F")
        agr["evidence"]["accepted_quotation"] = True
        agr["required_documents"] = [{"name": "Inv", "evidence_state": "AVAILABLE"}]
        items = build_review_queue_items(
            {"SHP-C13-A1": {}},
            agreements={agr["agreement_id"]: agr},
            quotes={"Q-C13-0001": _q()},
        )
        blocked = [item for item in items if item.get("target", {}).get("kind") == "agreement"]
        self.assertEqual(blocked, [])

    def test_linking_helpers_resolve(self):
        agr = build_agreement_from_quote(_q(), actor="F")
        agr["shipment_ids"] = ["SHP-C13-9"]
        self.assertEqual(agreements_for_shipment("SHP-C13-9", {agr["agreement_id"]: agr}), [agr])
        self.assertEqual(agreements_for_quote("Q-C13-0001", {agr["agreement_id"]: agr}), [agr])
        self.assertEqual(agreements_for_quote("Q-MISSING", {}), [])


class CommercialSnapshotImmutabilityTests(unittest.TestCase):
    def test_mutating_agreement_does_not_mutate_source_quote(self):
        quote = _q()
        original_lines = copy.deepcopy(quote["service_lines"])
        agr = build_agreement_from_quote(quote, actor="F")
        agr["commercial_snapshot"]["service_lines"][0]["sell_unit"] = 999
        self.assertEqual(quote["service_lines"][0]["sell_unit"], 1_500_000)
        self.assertEqual(quote["service_lines"], original_lines)

    def test_persistence_stamps_are_stable_in_concurrent_requests(self):
        stamped = []
        errors = []

        def persist(actor):
            try:
                agr = build_agreement_from_quote(_q(), actor=actor)
                stamped.append(prepare_agreement_for_persistence(agr, actor=actor))
            except Exception as exc:  # pragma: no cover - record-only
                errors.append(exc)

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(persist, (f"A{i}" for i in range(8))))
        self.assertEqual(errors, [])
        self.assertEqual(len(stamped), 8)
        ids = [s["agreement_id"] for s in stamped]
        self.assertEqual(len(set(ids)), 8)
        write_ids = {s["write_request_id"] for s in stamped}
        self.assertEqual(len(write_ids), 8)


if __name__ == "__main__":
    unittest.main()
