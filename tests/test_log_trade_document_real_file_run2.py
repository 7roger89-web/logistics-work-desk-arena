"""Run 2 real-file text-layer canary for issue #130.

Synthetic XLSX + born-digital PDF bytes must feed the existing Run 1 trade
cross-check core without changing the 19 frozen semantic facts.
"""

from __future__ import annotations

import ast
import hashlib
import io
import json
import tracemalloc
import unittest
import zipfile
import zlib
from pathlib import Path
from unittest import mock

from openpyxl import Workbook
from pypdf import PdfWriter

from core.document_extraction import DocumentSecurityError
from core.located_text_reader import (
    MAX_XLSX_CELLS,
    MAX_XLSX_INFLATED_BYTES,
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


def _rewrite_xlsx_member(data: bytes, member: str, transform) -> bytes:
    """Deterministically rewrite one member of a real XLSX zip."""

    source = io.BytesIO(data)
    target = io.BytesIO()
    seen = False
    with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            payload = zin.read(info.filename)
            if info.filename == member:
                seen = True
                payload = transform(payload.decode("utf-8")).encode("utf-8")
            out_info = zipfile.ZipInfo(info.filename, info.date_time)
            out_info.compress_type = zipfile.ZIP_DEFLATED
            out_info.external_attr = info.external_attr
            zout.writestr(out_info, payload)
    if not seen:
        raise AssertionError(f"member not found: {member}")
    return target.getvalue()


def _patch_declared_uncompressed_size(data: bytes, sizes: dict[str, int]) -> bytes:
    """Rewrite declared uncompressed sizes in the ZIP *central directory* only.

    The local member data is untouched, so the resulting bytes stay tiny while
    the container still declares a huge expansion -- exactly the amplification
    case the pre-parse budget must refuse.
    """

    patched = bytearray(data)
    remaining = dict(sizes)
    index = 0
    while remaining:
        index = patched.find(b"PK\x01\x02", index)
        if index < 0:
            raise AssertionError(f"central directory entry not found: {sorted(remaining)}")
        name_length = int.from_bytes(patched[index + 28 : index + 30], "little")
        name = bytes(patched[index + 46 : index + 46 + name_length]).decode("utf-8")
        if name in remaining:
            patched[index + 24 : index + 28] = remaining.pop(name).to_bytes(4, "little")
        index += 4
    return bytes(patched)


def _pdf_with_flate_stream(inflated_bytes: int) -> bytes:
    """Build a tiny valid PDF whose single content stream inflates very large."""

    body = b"BT /F1 10 Tf 50 760 Td (SYNTHETIC \x97 NOT A REAL SHIPMENT) Tj ET\n"
    body += b" " * max(0, inflated_bytes - len(body))
    compressed = zlib.compress(body, 9)
    objects = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: b"<< /Type /Pages /Kids [5 0 R] /Count 1 >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        4: b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(compressed) + compressed + b"\nendstream",
        5: b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
           b"/Resources << /Font << /F1 3 0 R >> >> /Contents 4 0 R >>",
    }
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {}
    for number in sorted(objects):
        offsets[number] = len(out)
        out += b"%d 0 obj\n" % number + objects[number] + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n" % (max(objects) + 1) + b"0000000000 65535 f \n"
    for number in sorted(objects):
        out += b"%010d 00000 n \n" % offsets[number]
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (max(objects) + 1, xref)
    return bytes(out)


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


class Run2BoundEnforcementTests(unittest.TestCase):
    """Prove the amplification bounds act *before* the expensive operation."""

    def test_pdf_stream_bound_blocks_expansion_before_the_stream_is_materialised(self) -> None:
        inflated_bytes = 64 * 1024 * 1024
        payload = _pdf_with_flate_stream(inflated_bytes)
        self.assertLess(len(payload), 200_000, "amplification payload must stay tiny")

        tracemalloc.start()
        try:
            with self.assertRaises(DocumentSecurityError) as raised:
                read_document_text(payload, "amplified.pdf")
            peak = tracemalloc.get_traced_memory()[1]
        finally:
            tracemalloc.stop()

        self.assertIn("bounded limit", str(raised.exception))
        self.assertLess(
            peak,
            inflated_bytes // 8,
            f"the {inflated_bytes // 1024 // 1024} MiB expansion was materialised (peak={peak})",
        )

    def test_pdf_stream_bound_still_reads_a_stream_inside_the_bound(self) -> None:
        payload = _pdf_with_flate_stream(1024)
        document = read_document_text(payload, "small.pdf")
        self.assertEqual(document.unsupported_state, None)
        self.assertEqual(document.pages, (1,))
        self.assertIn("SYNTHETIC", document.text)

    def test_xlsx_declared_expansion_is_refused_before_openpyxl_runs(self) -> None:
        original = _fixture_bytes(INVOICE_XLSX)
        amplified = _patch_declared_uncompressed_size(
            original, {"xl/worksheets/sheet1.xml": 200 * 1024 * 1024}
        )
        self.assertLess(len(amplified), 10_000, "amplification payload must stay tiny")
        self.assertGreater(200 * 1024 * 1024, MAX_XLSX_INFLATED_BYTES)

        with mock.patch("openpyxl.load_workbook", side_effect=AssertionError("openpyxl must not run")) as loader:
            with self.assertRaises(DocumentSecurityError) as raised:
                read_document_text(amplified, INVOICE_XLSX)
        loader.assert_not_called()
        self.assertIn("bounded limit", str(raised.exception))

        # the same workbook with its real declared sizes still reads
        self.assertTrue(read_document_text(original, INVOICE_XLSX).fragments)

    def test_xlsx_total_declared_expansion_is_refused(self) -> None:
        original = _fixture_bytes(INVOICE_XLSX)
        per_member = MAX_XLSX_INFLATED_BYTES // 2 + 1
        amplified = _patch_declared_uncompressed_size(
            original,
            {"xl/styles.xml": per_member, "xl/worksheets/sheet1.xml": per_member},
        )
        self.assertTrue(all(size < MAX_XLSX_INFLATED_BYTES for size in (per_member, per_member)),
                        "each member alone must stay inside the budget")
        with self.assertRaises(DocumentSecurityError) as raised:
            read_document_text(amplified, INVOICE_XLSX)
        self.assertIn("bounded limit", str(raised.exception))

    def test_xlsx_text_bound_rejects_an_over_long_workbook(self) -> None:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "long_text"
        row_count = 4000
        for row in range(1, row_count + 1):
            worksheet.cell(row=row, column=1, value="SYNTHETIC — NOT A REAL SHIPMENT " + "x" * 200)
        output = io.BytesIO()
        workbook.save(output)
        payload = output.getvalue()

        text_budget = 1000
        with self.assertRaises(DocumentSecurityError) as raised:
            read_document_text(payload, "long_text.xlsx", limits=TextReaderLimits(max_text_chars=text_budget))
        self.assertIn("xlsx text exceeds", str(raised.exception))
        # the workbook is far below the cell bound, so the text bound is what
        # rejected it
        self.assertLess(row_count, MAX_XLSX_CELLS)

    def test_r2_p2_provenance_follows_the_actual_workbook_not_a_hardcoded_expectation(self) -> None:
        def relocate(xml: str) -> str:
            source_row = (
                '<row r="10"><c r="A10" t="inlineStr"><is><t>Gross weight: 12,500 KGS</t></is></c></row>'
            )
            replacement_row = (
                '<row r="10"><c r="A10" t="inlineStr"><is><t>Net weight: 11,800 KGS</t></is></c></row>'
            )
            moved_row = (
                '<row r="15"><c r="A15" t="inlineStr"><is><t>Gross weight: 12,500 KGS</t></is></c></row>'
            )
            self.assertIn(source_row, xml)
            xml = xml.replace(source_row, replacement_row, 1)
            return xml.replace("</sheetData>", moved_row + "</sheetData>", 1)

        relocated_bytes = _rewrite_xlsx_member(
            _fixture_bytes(INVOICE_XLSX), "xl/worksheets/sheet1.xml", relocate
        )
        self.assertNotEqual(relocated_bytes, _fixture_bytes(INVOICE_XLSX))

        result = _run({INVOICE_XLSX: relocated_bytes})
        fact = _facts_by_key(result)["gross_weight"]
        observation = {
            item.document_label: item for item in fact.observations
        }[INVOICE_XLSX]

        # A10 is the frozen expectation used by the golden provenance test; the
        # parser must report the cell the value is actually in.
        self.assertEqual(observation.source_provenance["cell_coordinate"], "A15")
        self.assertEqual(observation.source_provenance["sheet_name"], "commercial_invoice")
        self.assertEqual(fact.status, FactStatus.SAME)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
