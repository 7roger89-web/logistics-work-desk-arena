"""Run 2 real-file text-layer canary for issue #130.

Synthetic XLSX + born-digital PDF bytes must feed the existing Run 1 trade
cross-check core without changing the 19 frozen semantic facts.
"""

from __future__ import annotations

import ast
import hashlib
import io
import json
import unittest
import zipfile
from pathlib import Path

from openpyxl import Workbook
from pypdf import PdfWriter

from core.document_extraction import DocumentSecurityError
from core.located_text_reader import (
    TEXT_NOT_AVAILABLE_NO_OCR,
    XLSX_FORMULA_UNSUPPORTED,
    TextReaderLimits,
    read_document_text,
)
from core.trade_compliance import DocumentType
from core.trade_document_crosscheck import FactStatus, run_trade_document_crosscheck
from tests.test_log_trade_doc_canary_crosscheck import GOLDEN_STATUSES

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "trade_canary_real_files"
CORE_READER_PATH = Path(__file__).resolve().parents[1] / "core" / "located_text_reader.py"
INVOICE_XLSX = "commercial_invoice.xlsx"
PACKING_LIST_XLSX = "packing_list.xlsx"
BL_PDF = "bill_of_lading.pdf"
ORDERED_FIXTURES = (INVOICE_XLSX, PACKING_LIST_XLSX, BL_PDF)
EXPECTED_SHA256 = {
    INVOICE_XLSX: "679bd628b09a859f9dbedca1d5ee60089f78493ac9a052b6bf9c7810802dbfcb",
    PACKING_LIST_XLSX: "3a179be0f5058bfe8ea4aa9a7ceab176f23db96af6dcd23643d0afa2344691b2",
    BL_PDF: "31e75fdbb755fd3b6991999085c409ed53ffe38f268368c4c2dc8a97f3f72e98",
}


def _fixture_bytes(name: str) -> bytes:
    return (FIXTURE_DIR / name).read_bytes()


def _located_documents(mutations: dict[str, bytes] | None = None):
    docs = []
    for name in ORDERED_FIXTURES:
        payload = (mutations or {}).get(name, _fixture_bytes(name))
        docs.append(read_document_text(payload, name))
    return docs


def _artifacts(mutations: dict[str, bytes] | None = None):
    return [doc.to_document_artifact() for doc in _located_documents(mutations)]


def _run(mutations: dict[str, bytes] | None = None):
    return run_trade_document_crosscheck(_artifacts(mutations))


def _facts_by_key(result):
    return {fact.field_key: fact for fact in result.facts}


def _mutate_xlsx_inline_text(data: bytes, old: str, new: str) -> bytes:
    """Deterministically replace one inline string in a real XLSX zip."""

    source = io.BytesIO(data)
    target = io.BytesIO()
    with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            payload = zin.read(info.filename)
            if info.filename == "xl/worksheets/sheet1.xml":
                text = payload.decode("utf-8")
                if old not in text:
                    raise AssertionError(f"mutation target not found: {old!r}")
                payload = text.replace(old, new, 1).encode("utf-8")
            out_info = zipfile.ZipInfo(info.filename, info.date_time)
            out_info.compress_type = zipfile.ZIP_DEFLATED
            out_info.external_attr = info.external_attr
            zout.writestr(out_info, payload)
    return target.getvalue()


def _blank_pdf_bytes(page_count: int = 1, *, encrypted: bool = False) -> bytes:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=72, height=72)
    if encrypted:
        writer.encrypt("secret")
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def _formula_xlsx_bytes() -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "formula_boundary"
    worksheet["A1"] = "SYNTHETIC — NOT A REAL SHIPMENT"
    worksheet["A2"] = "COMMERCIAL INVOICE"
    worksheet["A3"] = "Packages: 120 CTNS"
    worksheet["A4"] = "Total"
    worksheet["B4"] = "=1+1"
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


class Run2RealFileGoldenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.documents = _located_documents()
        self.result = run_trade_document_crosscheck([doc.to_document_artifact() for doc in self.documents])
        self.facts = _facts_by_key(self.result)

    def test_r2_p1_consumes_real_xlsx_and_pdf_bytes(self) -> None:
        self.assertEqual(_fixture_bytes(INVOICE_XLSX)[:2], b"PK")
        self.assertEqual(_fixture_bytes(PACKING_LIST_XLSX)[:2], b"PK")
        self.assertEqual(_fixture_bytes(BL_PDF)[:5], b"%PDF-")
        by_name = {doc.source_filename: doc for doc in self.documents}
        self.assertEqual(by_name[INVOICE_XLSX].file_type.value, "xlsx")
        self.assertEqual(by_name[PACKING_LIST_XLSX].file_type.value, "xlsx")
        self.assertEqual(by_name[BL_PDF].file_type.value, "pdf")
        for name, doc in by_name.items():
            self.assertEqual(doc.source_sha256, hashlib.sha256(_fixture_bytes(name)).hexdigest())
            self.assertEqual(doc.source_sha256, EXPECTED_SHA256[name])

    def test_r2_p2_location_provenance_preserves_sheet_cell_and_page(self) -> None:
        gross_weight = {observation.document_label: observation for observation in self.facts["gross_weight"].observations}
        self.assertEqual(gross_weight[INVOICE_XLSX].source_provenance["file_type"], "xlsx")
        self.assertEqual(gross_weight[INVOICE_XLSX].source_provenance["sheet_name"], "commercial_invoice")
        self.assertEqual(gross_weight[INVOICE_XLSX].source_provenance["cell_coordinate"], "A10")
        self.assertEqual(
            gross_weight[INVOICE_XLSX].source_provenance["reader_method"],
            "openpyxl.load_workbook(data_only=False)",
        )
        self.assertTrue(gross_weight[INVOICE_XLSX].source_provenance["reader_version"])
        self.assertEqual(gross_weight[INVOICE_XLSX].source_provenance["state"], "OK")
        self.assertEqual(
            gross_weight[PACKING_LIST_XLSX].source_provenance["cell_coordinate"],
            "A6",
        )
        container = {observation.document_label: observation for observation in self.facts["container"].observations}
        self.assertEqual(container[BL_PDF].source_provenance["file_type"], "pdf")
        self.assertEqual(container[BL_PDF].source_provenance["page_number"], 2)
        self.assertEqual(container[BL_PDF].source_provenance["reader_method"], "pypdf.PdfReader.page.extract_text")
        self.assertTrue(container[BL_PDF].source_provenance["reader_version"])

    def test_r2_p5_same_nineteen_semantics_as_run1(self) -> None:
        self.assertEqual(len(self.facts), 19)
        self.assertEqual({key: fact.status for key, fact in self.facts.items()}, GOLDEN_STATUSES)
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
        types = {document.document_label: document.document_type for document in self.result.documents}
        self.assertEqual(
            types,
            {
                INVOICE_XLSX: DocumentType.INVOICE,
                PACKING_LIST_XLSX: DocumentType.PACKING_LIST,
                BL_PDF: DocumentType.BILL_OF_LADING,
            },
        )

    def test_r2_p6_raw_file_hash_propagates_to_crosscheck_documents_and_observations(self) -> None:
        expected = {name: hashlib.sha256(_fixture_bytes(name)).hexdigest() for name in ORDERED_FIXTURES}
        self.assertEqual({doc.document_label: doc.content_sha256 for doc in self.result.documents}, expected)
        for fact in self.result.facts:
            for observation in fact.observations:
                self.assertEqual(observation.content_sha256, expected[observation.document_label])

    def test_existing_core_still_has_no_silent_conflict_resolution_or_fabrication(self) -> None:
        package_count = self.facts["package_count"]
        self.assertEqual(package_count.status, FactStatus.CONFLICT)
        self.assertEqual(package_count.operator_decision, "NONE")
        self.assertEqual(package_count.observed_values, ("120 CARTON", "120 CARTON", "118 CARTON"))
        text_by_name = {doc.source_filename: doc.text for doc in self.documents}
        for fact in self.result.facts:
            if fact.status in (FactStatus.MISSING, FactStatus.UNKNOWN):
                for value in fact.observed_values:
                    self.assertNotIn(value, (None, "", 0))
            for observation in fact.observations:
                if observation.raw_value is None:
                    self.assertIsNone(observation.normalized_value)
                    self.assertIsNone(observation.normalized_key)
                else:
                    self.assertIn(observation.raw_value, text_by_name[observation.document_label])

    def test_real_file_runs_are_deterministic(self) -> None:
        first = json.dumps(_run().to_dict(), sort_keys=True)
        second = json.dumps(_run().to_dict(), sort_keys=True)
        self.assertEqual(first, second)
        self.assertEqual(hashlib.sha256(first.encode()).hexdigest(), hashlib.sha256(second.encode()).hexdigest())


class Run2AdversarialTests(unittest.TestCase):
    def test_blank_pdf_returns_text_not_available_no_ocr(self) -> None:
        document = read_document_text(_blank_pdf_bytes(), "blank.pdf")
        self.assertEqual(document.unsupported_state, TEXT_NOT_AVAILABLE_NO_OCR)
        self.assertEqual(document.fragments, ())
        self.assertIn(TEXT_NOT_AVAILABLE_NO_OCR, document.warnings)

    def test_corrupt_oversized_page_limit_encrypted_and_stream_limit_fail_closed(self) -> None:
        with self.assertRaises(DocumentSecurityError):
            read_document_text(b"%PDF-1.4\nnot a complete pdf", "corrupt.pdf")
        with self.assertRaises(DocumentSecurityError):
            read_document_text(b"x" * 11, "oversized.pdf", limits=TextReaderLimits(max_file_bytes=10))
        with self.assertRaises(DocumentSecurityError):
            read_document_text(_blank_pdf_bytes(page_count=2), "too_many_pages.pdf", limits=TextReaderLimits(max_pdf_pages=1))
        with self.assertRaises(DocumentSecurityError):
            read_document_text(_blank_pdf_bytes(encrypted=True), "encrypted.pdf")
        with self.assertRaises(DocumentSecurityError):
            read_document_text(_fixture_bytes(BL_PDF), BL_PDF, limits=TextReaderLimits(max_pdf_content_stream_bytes=10))

    def test_xlsx_macro_and_formula_boundary_is_explicit(self) -> None:
        with self.assertRaises(DocumentSecurityError):
            read_document_text(_fixture_bytes(INVOICE_XLSX), "macro.xlsm")
        document = read_document_text(_formula_xlsx_bytes(), "formula_boundary.xlsx")
        self.assertEqual(document.unsupported_state, "UNSUPPORTED_FORMULA_VALUES_PRESENT")
        self.assertIn(f"{XLSX_FORMULA_UNSUPPORTED}:formula_boundary!B4", document.warnings)
        self.assertIn("=1+1", document.text)
        self.assertNotIn(" 2", document.text)

    def test_mutated_xlsx_source_fact_produces_deterministic_conflict(self) -> None:
        mutated_invoice = _mutate_xlsx_inline_text(_fixture_bytes(INVOICE_XLSX), "12,500 KGS", "12,501 KGS")
        result = _run({INVOICE_XLSX: mutated_invoice})
        fact = _facts_by_key(result)["gross_weight"]
        self.assertEqual(fact.status, FactStatus.CONFLICT)
        self.assertEqual(fact.observed_values, ("12501", "12500", "12500"))
        again = _run({INVOICE_XLSX: mutated_invoice})
        self.assertEqual(result.to_dict(), again.to_dict())

    def test_reader_import_surface_has_no_provider_network_db_ui_or_ocr_stack(self) -> None:
        tree = ast.parse(CORE_READER_PATH.read_text(encoding="utf-8"))
        imported_roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(name.name.split(".")[0] for name in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported_roots.add(node.module.split(".")[0])
        forbidden_imports = {
            "google",
            "google_genai",
            "pymongo",
            "requests",
            "socket",
            "streamlit",
            "subprocess",
            "urllib",
            "docling",
            "paddleocr",
            "pytesseract",
        }
        self.assertEqual(imported_roots & forbidden_imports, set())
        source = CORE_READER_PATH.read_text(encoding="utf-8").lower()
        for forbidden in ("gemini", "aidock", "tesseract", "paddleocr"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
