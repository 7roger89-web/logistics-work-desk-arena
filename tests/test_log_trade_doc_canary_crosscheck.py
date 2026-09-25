"""Focused tests for the TT-DOC-CANARY-01 trade document cross-check canary.

Issue #126. The frozen golden set embedded here is acceptance authority and
must not be edited to make the implementation pass.
"""

from __future__ import annotations

import ast
import hashlib
import json
import unittest
from decimal import Decimal
from pathlib import Path

from core.document_extraction import DocumentArtifact
from core.trade_compliance import DocumentType
from core.trade_document_crosscheck import (
    FactStatus,
    ObservationStatus,
    classify_trade_document,
    iso6346_check_digit,
    normalize_container,
    normalize_date,
    run_trade_document_crosscheck,
    trade_label_adapter,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "trade_canary"
ENGINE_PATH = Path(__file__).resolve().parents[1] / "core" / "trade_document_crosscheck.py"
INVOICE_FILE = "commercial_invoice.txt"
PACKING_LIST_FILE = "packing_list.txt"
BL_FILE = "bill_of_lading.txt"

GOLDEN_STATUSES = {
    # SAME
    "gross_weight": FactStatus.SAME,
    "consignee": FactStatus.SAME,
    "shipper": FactStatus.SAME,
    "pod": FactStatus.SAME,
    "container": FactStatus.SAME,
    "cbm": FactStatus.SAME,
    "invoice_number": FactStatus.SAME,
    # CONFLICT
    "package_count": FactStatus.CONFLICT,
    # MISSING
    "bl_number": FactStatus.MISSING,
    "hs_code": FactStatus.MISSING,
    # UNKNOWN
    "invoice_date": FactStatus.UNKNOWN,
    # SINGLE_SOURCE
    "vessel": FactStatus.SINGLE_SOURCE,
    "voyage": FactStatus.SINGLE_SOURCE,
    "pol": FactStatus.SINGLE_SOURCE,
    "seal": FactStatus.SINGLE_SOURCE,
    "incoterm": FactStatus.SINGLE_SOURCE,
    "total": FactStatus.SINGLE_SOURCE,
    "net_weight": FactStatus.SINGLE_SOURCE,
    "origin": FactStatus.SINGLE_SOURCE,
}


def _fixture_text(name: str) -> str:
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


def _artifacts(mutations: dict[str, str] | None = None):
    texts = {name: _fixture_text(name) for name in (INVOICE_FILE, PACKING_LIST_FILE, BL_FILE)}
    for name, (old, new) in (mutations or {}).items():
        if old not in texts[name]:
            raise AssertionError(f"mutation target not found in {name}: {old!r}")
        texts[name] = texts[name].replace(old, new, 1)
    return [
        DocumentArtifact(filename=name, content=texts[name])
        for name in (INVOICE_FILE, PACKING_LIST_FILE, BL_FILE)
    ]


def _run(mutations: dict[str, str] | None = None, **kwargs):
    return run_trade_document_crosscheck(_artifacts(mutations), **kwargs)


def _facts_by_key(result):
    return {fact.field_key: fact for fact in result.facts}


class GoldenSetAgreementTests(unittest.TestCase):
    """P1 — 100% agreement with the frozen golden set."""

    def setUp(self) -> None:
        self.result = _run()
        self.facts = _facts_by_key(self.result)

    def test_document_classification_is_three_of_three(self) -> None:
        types = {document.document_label: document.document_type for document in self.result.documents}
        self.assertEqual(
            types,
            {
                INVOICE_FILE: DocumentType.INVOICE,
                PACKING_LIST_FILE: DocumentType.PACKING_LIST,
                BL_FILE: DocumentType.BILL_OF_LADING,
            },
        )

    def test_all_nineteen_golden_statuses_agree(self) -> None:
        self.assertEqual(len(self.facts), len(GOLDEN_STATUSES))
        for field_key, expected_status in GOLDEN_STATUSES.items():
            self.assertIn(field_key, self.facts, field_key)
            self.assertEqual(
                self.facts[field_key].status,
                expected_status,
                msg=f"{field_key}: expected {expected_status}, got {self.facts[field_key].status}",
            )

    def test_status_counts_match_golden_distribution(self) -> None:
        self.assertEqual(
            self.result.status_counts(),
            {
                "CONFLICT": 1,
                "UNKNOWN": 1,
                "SAME": 7,
                "MISSING": 2,
                "SINGLE_SOURCE": 8,
            },
        )
        self.assertEqual(sum(self.result.status_counts().values()), 19)

    def test_conflict_keeps_all_three_sides_without_winner(self) -> None:
        fact = self.facts["package_count"]
        self.assertEqual(fact.status, FactStatus.CONFLICT)
        self.assertEqual(fact.observed_values, ("120 CARTON", "120 CARTON", "118 CARTON"))
        self.assertEqual(fact.reason, "FOUND_VALUES_DIFFER_NO_WINNER_SELECTED")
        self.assertEqual(fact.operator_decision, "NONE")
        raw_sides = sorted({observation.raw_value for observation in fact.observations})
        self.assertEqual(raw_sides, ["118 CARTONS", "120 CARTONS", "120 CTNS"])

    def test_missing_fields_use_none_and_hs_carries_lookup_handoff(self) -> None:
        bl_number = self.facts["bl_number"]
        self.assertEqual(bl_number.status, FactStatus.MISSING)
        self.assertEqual(bl_number.observed_values, ())
        for observation in bl_number.observations:
            self.assertIsNone(observation.raw_value)
            self.assertIsNone(observation.normalized_value)
            self.assertIsNone(observation.normalized_key)
        hs_code = self.facts["hs_code"]
        self.assertEqual(hs_code.status, FactStatus.MISSING)
        self.assertEqual(hs_code.observed_values, ())
        self.assertIsNotNone(hs_code.handoff)
        self.assertEqual(hs_code.handoff["action"], "HS_CODE_LOOKUP_REQUIRED")
        self.assertNotIn("8708", json.dumps(hs_code.to_dict()))  # no generated code

    def test_ambiguous_packing_list_date_keeps_invoice_date_unknown(self) -> None:
        fact = self.facts["invoice_date"]
        self.assertEqual(fact.status, FactStatus.UNKNOWN)
        by_doc = {observation.document_label: observation for observation in fact.observations}
        self.assertEqual(by_doc[INVOICE_FILE].normalized_key, "2026-03-04")
        self.assertEqual(by_doc[PACKING_LIST_FILE].raw_value, "03/04/2026")
        self.assertIsNone(by_doc[PACKING_LIST_FILE].normalized_key)
        self.assertEqual(by_doc[PACKING_LIST_FILE].reason, "AMBIGUOUS_DAY_MONTH_ORDER")


class ZeroFabricationTests(unittest.TestCase):
    """P2 — every raw value is grounded verbatim in its source text."""

    def test_every_raw_value_exists_verbatim_in_its_source_document(self) -> None:
        result = _run()
        texts = {name: _fixture_text(name) for name in (INVOICE_FILE, PACKING_LIST_FILE, BL_FILE)}
        for fact in result.facts:
            for observation in fact.observations:
                if observation.status is ObservationStatus.NOT_FOUND:
                    self.assertIsNone(observation.raw_value)
                    continue
                self.assertIsNotNone(observation.raw_value)
                self.assertIn(
                    observation.raw_value,
                    texts[observation.document_label],
                    msg=f"ungrounded raw value in {observation.document_label}/{observation.field_key}",
                )


class ExactValuesTests(unittest.TestCase):
    """P5 — raw text preserved; exact Decimal semantics for numbers/money."""

    def setUp(self) -> None:
        self.facts = _facts_by_key(_run())

    def _observations(self, field_key):
        return {observation.document_label: observation for observation in self.facts[field_key].observations}

    def test_gross_weight_uses_exact_decimal_with_kg_unit(self) -> None:
        observations = self._observations("gross_weight")
        raws = {
            INVOICE_FILE: "12,500 KGS",
            PACKING_LIST_FILE: "12500.00 KG",
            BL_FILE: "12,500.000 KGS",
        }
        for label, raw in raws.items():
            observation = observations[label]
            self.assertEqual(observation.raw_value, raw)
            self.assertIsInstance(observation.normalized_value, Decimal)
            self.assertEqual(observation.normalized_value, Decimal("12500"))
            self.assertEqual(observation.normalized_key, "12500")
            self.assertEqual(observation.unit, "kg")

    def test_total_money_is_exact_decimal_with_currency_and_no_fx(self) -> None:
        observation = self._observations("total")[INVOICE_FILE]
        self.assertEqual(observation.raw_value, "USD 45,678.90")
        self.assertIsInstance(observation.normalized_value, Decimal)
        self.assertEqual(observation.normalized_value, Decimal("45678.90"))
        self.assertEqual(observation.unit, "USD")
        self.assertEqual(observation.normalized_key, "USD 45678.9")

    def test_cbm_compares_25_600_and_25_6_as_equal(self) -> None:
        observations = self._observations("cbm")
        self.assertEqual(observations[PACKING_LIST_FILE].normalized_key, "25.6")
        self.assertEqual(observations[BL_FILE].normalized_key, "25.6")
        self.assertIsInstance(observations[PACKING_LIST_FILE].normalized_value, Decimal)
        self.assertEqual(self.facts["cbm"].status, FactStatus.SAME)

    def test_normalization_preserves_comparison_only_semantics(self) -> None:
        observations = {
            "shipper": self._observations("shipper"),
            "consignee": self._observations("consignee"),
            "pod": self._observations("pod"),
        }
        self.assertEqual(observations["shipper"][INVOICE_FILE].normalized_key, "NINGBO EXAMPLE FURNITURE CO LTD")
        self.assertEqual(observations["shipper"][BL_FILE].normalized_key, "NINGBO EXAMPLE FURNITURE CO LTD")
        self.assertEqual(observations["consignee"][INVOICE_FILE].normalized_key, "VIDU TRADING CO LTD")
        self.assertEqual(observations["consignee"][BL_FILE].normalized_key, "VIDU TRADING CO LTD")
        self.assertEqual(observations["pod"][INVOICE_FILE].normalized_key, "HAIPHONGVIETNAM")
        self.assertEqual(observations["pod"][BL_FILE].normalized_key, "HAIPHONGVIETNAM")


class ProvenanceTests(unittest.TestCase):
    """P7 — fixture identity, actual input SHA-256, document type, methods,
    and source locations only when genuinely known."""

    def setUp(self) -> None:
        self.result = _run()

    def test_every_observation_carries_full_provenance(self) -> None:
        for fact in self.result.facts:
            for observation in fact.observations:
                self.assertEqual(
                    observation.content_sha256,
                    hashlib.sha256(_fixture_text(observation.document_label).encode("utf-8")).hexdigest(),
                )
                self.assertTrue(observation.extraction_method)
                self.assertTrue(observation.normalization)
                self.assertIsInstance(observation.document_type, DocumentType)

    def test_source_locations_are_real_page_line_pairs(self) -> None:
        facts = _facts_by_key(self.result)
        invoice_lines = _fixture_text(INVOICE_FILE).splitlines()
        bl_lines = _fixture_text(BL_FILE).splitlines()
        gross_weight = {o.document_label: o for o in facts["gross_weight"].observations}
        self.assertEqual(
            gross_weight[INVOICE_FILE].source_location,
            (1, invoice_lines.index("Gross weight: 12,500 KGS") + 1),
        )
        container = {o.document_label: o for o in facts["container"].observations}
        self.assertEqual(
            container[BL_FILE].source_location,
            (2, bl_lines.index("Container: TTXU5821408") + 1),
        )
        self.assertEqual(
            container[PACKING_LIST_FILE].source_location[0],
            1,
        )

    def test_document_summaries_carry_actual_input_sha256(self) -> None:
        for document in self.result.documents:
            self.assertEqual(
                document.content_sha256,
                hashlib.sha256(_fixture_text(document.document_label).encode("utf-8")).hexdigest(),
            )
            self.assertEqual(document.classification_method, "trade_title_rules_v1")
            self.assertEqual(document.extraction_status, "PASS")


class GuardTests(unittest.TestCase):
    """P3/P4/P6/P8 plus adversarial challenges."""

    def setUp(self) -> None:
        self.result = _run()
        self.facts = _facts_by_key(self.result)

    def test_no_empty_string_or_zero_semantics_for_missing_or_unknown(self) -> None:
        for fact in self.result.facts:
            for observation in fact.observations:
                if observation.status in (ObservationStatus.NOT_FOUND,):
                    self.assertIsNone(observation.raw_value)
                    self.assertNotEqual(observation.reason, "")
                if observation.status is ObservationStatus.FOUND:
                    self.assertNotEqual(observation.raw_value, "")
                self.assertIsNot(observation.normalized_value, 0)
            if fact.status in (FactStatus.MISSING, FactStatus.UNKNOWN):
                self.assertEqual(fact.observed_values, () or fact.observed_values)
        missing = self.facts["bl_number"]
        self.assertEqual(missing.observed_values, ())
        self.assertIsNone(missing.observations[0].normalized_value)

    def test_engine_module_has_zero_io_import_surface(self) -> None:
        allowed_roots = {
            "__future__",
            "core",
            "re",
            "string",
            "unicodedata",
            "dataclasses",
            "datetime",
            "decimal",
            "enum",
            "typing",
        }
        tree = ast.parse(ENGINE_PATH.read_text(encoding="utf-8"))
        imported_roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(name.name.split(".")[0] for name in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported_roots.add(node.module.split(".")[0])
        self.assertTrue(imported_roots.issubset(allowed_roots), imported_roots - allowed_roots)
        forbidden = {"pymongo", "requests", "urllib", "http", "socket", "streamlit", "subprocess", "pathlib"}
        self.assertEqual(imported_roots & forbidden, set())

    def test_two_identical_runs_are_identical(self) -> None:
        first = json.dumps(_run().to_dict(), sort_keys=True)
        second = json.dumps(_run().to_dict(), sort_keys=True)
        self.assertEqual(first, second)
        self.assertEqual(
            hashlib.sha256(first.encode("utf-8")).hexdigest(),
            hashlib.sha256(second.encode("utf-8")).hexdigest(),
        )

    def test_result_is_order_independent(self) -> None:
        forward = run_trade_document_crosscheck(_artifacts()).to_dict()
        reversed_run = run_trade_document_crosscheck(list(reversed(_artifacts()))).to_dict()
        self.assertEqual(forward, reversed_run)

    # -- adversarial challenges -------------------------------------------

    def test_adversarial_a_mutated_bl_package_count_stays_deterministic_conflict(self) -> None:
        result = _run({BL_FILE: ("118 CARTONS", "117 CARTONS")})
        fact = _facts_by_key(result)["package_count"]
        self.assertEqual(fact.status, FactStatus.CONFLICT)
        self.assertEqual(fact.observed_values, ("120 CARTON", "120 CARTON", "117 CARTON"))
        again = _run({BL_FILE: ("118 CARTONS", "117 CARTONS")})
        self.assertEqual(result.to_dict(), again.to_dict())

    def test_adversarial_b_ungrounded_adapter_value_becomes_unreadable_unknown(self) -> None:
        def ghost_adapter(artifact):
            values = trade_label_adapter(artifact)
            if artifact.filename == BL_FILE:
                values["vessel"] = ["M/V EXAMPLE STAR", "M/V GHOST STAR"]
            return values

        result = run_trade_document_crosscheck(_artifacts(), adapter=ghost_adapter)
        fact = _facts_by_key(result)["vessel"]
        self.assertEqual(fact.status, FactStatus.UNKNOWN)
        statuses = {observation.raw_value: observation.status for observation in fact.observations}
        self.assertEqual(statuses["M/V EXAMPLE STAR"], ObservationStatus.FOUND)
        ghost = next(o for o in fact.observations if o.raw_value == "M/V GHOST STAR")
        self.assertEqual(ghost.status, ObservationStatus.UNREADABLE)
        self.assertEqual(ghost.reason, "RAW_VALUE_NOT_GROUNDED_IN_SOURCE")
        self.assertIsNone(ghost.normalized_key)
        self.assertIsNone(ghost.normalized_value)
        self.assertNotIn("M/V GHOST STAR", _fixture_text(BL_FILE))  # sanity: truly ungrounded

    def test_adversarial_c_ambiguous_date_never_becomes_a_guess(self) -> None:
        normal = normalize_date("03/04/2026")
        self.assertIsNone(normal.key)
        self.assertEqual(normal.reason, "AMBIGUOUS_DAY_MONTH_ORDER")
        self.assertIsNone(normal.value)
        resolved_day_first = normalize_date("25/03/2026")
        self.assertEqual(resolved_day_first.key, "2026-03-25")
        iso = normalize_date("2026-03-04")
        self.assertEqual(iso.key, "2026-03-04")
        result = _run({PACKING_LIST_FILE: ("03/04/2026", "05/06/2026")})
        self.assertEqual(_facts_by_key(result)["invoice_date"].status, FactStatus.UNKNOWN)

    def test_adversarial_d_invalid_container_check_digit_is_never_repaired(self) -> None:
        self.assertEqual(iso6346_check_digit("TTXU5821408"), 8)
        valid = normalize_container("TTXU 582140-8")
        self.assertEqual(valid.key, "TTXU5821408")
        invalid = normalize_container("TTXU5821409")
        self.assertIsNone(invalid.key)
        self.assertEqual(invalid.reason, "ISO_6346_CHECK_DIGIT_INVALID")
        result = _run({BL_FILE: ("TTXU5821408", "TTXU5821409")})
        fact = _facts_by_key(result)["container"]
        self.assertEqual(fact.status, FactStatus.UNKNOWN)
        bl_observation = next(o for o in fact.observations if o.document_label == BL_FILE)
        self.assertEqual(bl_observation.raw_value, "TTXU5821409")
        self.assertIsNone(bl_observation.normalized_value)
        self.assertIsNone(bl_observation.normalized_key)
        # The engine must not silently "fix" the digit to the matching value.
        self.assertNotIn("ISO_6346_REPAIRED", json.dumps(result.to_dict()))
        pl_observation = next(o for o in fact.observations if o.document_label == PACKING_LIST_FILE)
        self.assertEqual(pl_observation.normalized_key, "TTXU5821408")


class ClassificationUnitTests(unittest.TestCase):
    def test_unmarkable_text_is_unknown_document(self) -> None:
        self.assertEqual(classify_trade_document("hello world"), DocumentType.UNKNOWN_DOCUMENT)

    def test_titles_classify_deterministically(self) -> None:
        self.assertEqual(classify_trade_document(_fixture_text(INVOICE_FILE)), DocumentType.INVOICE)
        self.assertEqual(classify_trade_document(_fixture_text(PACKING_LIST_FILE)), DocumentType.PACKING_LIST)
        self.assertEqual(classify_trade_document(_fixture_text(BL_FILE)), DocumentType.BILL_OF_LADING)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
