"""Focused validation for the bounded LOG-DOC01 extraction seam."""

from __future__ import annotations

import unittest

from core.document_extraction import (
    DOCLING_ADAPTER_IMPLEMENTED,
    DOCLING_RUNTIME_PROVEN,
    PADDLEOCR_ADAPTER_IMPLEMENTED,
    PADDLEOCR_RUNTIME_PROVEN,
    DocumentArtifact,
    DocumentSecurityError,
    ExtractionStatus,
    adapter_runtime_status,
    build_trade_evidence_plan,
    extract_document,
    to_product_identity,
    to_trade_document_evidence,
)
from core.trade_compliance import DocumentType


class LogDoc01ExtractionTests(unittest.TestCase):
    def test_complete_datasheet_maps_to_canonical_trade_evidence(self) -> None:
        result = extract_document(
            DocumentArtifact(
                filename="cartonpro-datasheet.txt",
                document_type="DATASHEET",
                content=(
                    "Category: machine\n"
                    "Product Name: CartonPro 2000\n"
                    "Manufacturer: Example Machinery\n"
                    "Model: CP-2000\n"
                    "Function: carton packing\n"
                    "Intended Use: industrial packaging\n"
                    "Power: 5 kW\n"
                    "Capacity: 120 cartons/hour\n"
                ),
                source_url="https://supplier.example/datasheet",
                page_count=2,
            )
        )
        self.assertEqual(result.status, ExtractionStatus.PASS)
        self.assertEqual(result.extraction.document_type, DocumentType.TECHNICAL_DATASHEET)
        document = to_trade_document_evidence(result)
        self.assertTrue(document.present)
        self.assertTrue(document.valid)
        self.assertTrue(document.relevant)
        self.assertTrue(document.sufficient)
        identity = to_product_identity(result)
        self.assertEqual(identity.product_name, "CartonPro 2000")
        self.assertEqual(identity.identity_status, "NORMALIZED_UNVERIFIED")

    def test_missing_product_fields_are_unknown_not_guessed(self) -> None:
        result = extract_document(
            DocumentArtifact(
                filename="partial-product.txt",
                document_type="DATASHEET",
                content="Category: chemical\nProduct Name: Cleaning liquid\n",
            )
        )
        identity = to_product_identity(result)
        self.assertIn("composition", identity.missing_fields)
        self.assertIn("chemical_identifiers", identity.missing_fields)
        self.assertIn("intended_use", identity.missing_fields)
        self.assertNotIn("composition", result.fields)
        plan = build_trade_evidence_plan(result)
        self.assertIn(DocumentType.SDS_MSDS, {request.document_type for request in plan.requests})

    def test_complete_sds_preserves_chemical_and_transport_evidence(self) -> None:
        result = extract_document(
            DocumentArtifact(
                filename="cleaning-sds.txt",
                document_type="SDS",
                content=(
                    "Category: chemical\n"
                    "Product Name: Solvent A\n"
                    "Composition: solvent blend\n"
                    "CAS Number: 123-45-6\n"
                    "Intended Use: industrial cleaning\n"
                    "UN Number: UN1993\n"
                    "Transport Hazard Class: 3\n"
                    "Packing Group: II\n"
                    "Proper Shipping Name: Flammable liquid\n"
                ),
            )
        )
        self.assertEqual(result.status, ExtractionStatus.PASS)
        self.assertEqual(result.extraction.document_type, DocumentType.SDS_MSDS)
        document = to_trade_document_evidence(result)
        self.assertTrue(document.sufficient)
        self.assertEqual(result.fields["transport_hazard_class"], "3")
        self.assertEqual(result.fields["un_number"], "UN1993")
        self.assertNotIn("NON_HAZARDOUS", " ".join(result.extraction.warnings))

    def test_missing_sds_transport_data_requires_review_and_never_non_hazardous(self) -> None:
        result = extract_document(
            DocumentArtifact(
                filename="incomplete-sds.txt",
                document_type="SDS",
                content=(
                    "Category: chemical\n"
                    "Product Name: Solvent A\n"
                    "Composition: solvent blend\n"
                    "CAS Number: 123-45-6\n"
                    "Intended Use: industrial cleaning\n"
                ),
            )
        )
        self.assertEqual(result.status, ExtractionStatus.REVIEW_REQUIRED)
        document = to_trade_document_evidence(result)
        self.assertFalse(document.sufficient)
        self.assertIn("MISSING_TRANSPORT_HAZARD_CLASS", result.review_reasons)
        self.assertIn("MISSING_UN_NUMBER", result.review_reasons)
        self.assertIn("UNKNOWN", " ".join(result.extraction.warnings))
        self.assertNotIn("NON_HAZARDOUS", " ".join(result.extraction.warnings))

    def test_iso_13485_is_extracted_but_not_import_approval(self) -> None:
        result = extract_document(
            DocumentArtifact(
                filename="iso-certificate.txt",
                document_type="CERTIFICATE",
                content=(
                    "Category: medical_device\n"
                    "Product Name: Diagnostic device\n"
                    "Manufacturer: Example Medical\n"
                    "Model: DM-1\n"
                    "Certificate Standard: ISO 13485\n"
                    "Certificate Number: ISO-123\n"
                    "Certificate Scope: Design and manufacture\n"
                ),
            )
        )
        self.assertEqual(result.status, ExtractionStatus.PASS)
        self.assertEqual(result.extraction.document_type, DocumentType.ISO_13485)
        document = to_trade_document_evidence(result)
        self.assertTrue(document.present)
        self.assertFalse(document.sufficient)
        self.assertIn("does not establish", document.interpretation or "")
        self.assertNotIn("import", result.fields)
        self.assertNotIn("approval", result.fields)

    def test_conflicting_values_are_preserved_and_require_review(self) -> None:
        result = extract_document(
            DocumentArtifact(
                filename="conflict.txt",
                document_type="DATASHEET",
                content="Product Name: Pump A\nProduct Name: Pump B\nFunction: pumping\n",
            )
        )
        self.assertEqual(result.status, ExtractionStatus.REVIEW_REQUIRED)
        self.assertEqual(result.extraction.conflicts["product_name"], ("Pump A", "Pump B"))
        document = to_trade_document_evidence(result)
        self.assertFalse(document.sufficient)
        self.assertIn("CONFLICTING_FIELDS_PRESERVED", result.review_reasons)

    def test_provenance_retains_raw_source_page_and_method(self) -> None:
        result = extract_document(
            DocumentArtifact(
                filename="source.txt",
                document_type="CATALOGUE",
                content="Product Name: Machine A\nFunction: cutting\n",
                source_url="https://supplier.example/source",
                page_count=3,
            )
        )
        payload = result.to_dict()
        self.assertIn("Product Name: Machine A", payload["extraction"]["raw_text"])
        self.assertEqual(payload["extraction"]["provenance"]["source"], "https://supplier.example/source")
        self.assertEqual(payload["extraction"]["provenance"]["method"], "deterministic_key_value")
        self.assertTrue(payload["artifact"]["content_sha256"])
        self.assertIn("product_name", payload["extraction"]["source_pages"])

    def test_security_boundaries_reject_traversal_scripts_size_and_pages(self) -> None:
        with self.assertRaises(DocumentSecurityError):
            DocumentArtifact(filename="../secret.txt", content="x")
        with self.assertRaises(DocumentSecurityError):
            DocumentArtifact(filename="macro.xlsm", content="x")
        with self.assertRaises(DocumentSecurityError):
            DocumentArtifact(filename="payload.txt", content=b"<script>alert(1)</script>")
        with self.assertRaises(DocumentSecurityError):
            DocumentArtifact(filename="large.txt", content="x", page_count=201)
        with self.assertRaises(DocumentSecurityError):
            DocumentArtifact(filename="large.txt", content="x" * (10 * 1024 * 1024 + 1))

    def test_unknown_document_type_fails_closed(self) -> None:
        result = extract_document(DocumentArtifact(filename="unknown.bin", content="unstructured text"))
        self.assertEqual(result.extraction.document_type, DocumentType.UNKNOWN_DOCUMENT)
        self.assertEqual(result.status, ExtractionStatus.REVIEW_REQUIRED)
        self.assertFalse(to_trade_document_evidence(result).sufficient)

    def test_optional_adapter_seam_does_not_prove_runtime(self) -> None:
        result = extract_document(
            DocumentArtifact(filename="adapter.txt", content="ignored"),
            adapter=lambda _: {"product_name": "Adapter Product", "category": "machine"},
        )
        self.assertEqual(result.extraction.method, "<lambda>")
        self.assertEqual(result.fields["product_name"], "Adapter Product")
        self.assertEqual(
            adapter_runtime_status(),
            {
                "docling_adapter_implemented": True,
                "docling_runtime_proven": False,
                "paddleocr_adapter_implemented": True,
                "paddleocr_runtime_proven": False,
            },
        )
        self.assertTrue(DOCLING_ADAPTER_IMPLEMENTED and PADDLEOCR_ADAPTER_IMPLEMENTED)
        self.assertFalse(DOCLING_RUNTIME_PROVEN or PADDLEOCR_RUNTIME_PROVEN)

    def test_document_type_scope_is_bounded(self) -> None:
        self.assertEqual(
            {
                DocumentType.PRODUCT_CATALOGUE,
                DocumentType.TECHNICAL_DATASHEET,
                DocumentType.PRODUCT_LABEL_OR_NAMEPLATE,
                DocumentType.SDS_MSDS,
                DocumentType.CERTIFICATE,
                DocumentType.UNKNOWN_DOCUMENT,
            },
            {
                DocumentType.PRODUCT_CATALOGUE,
                DocumentType.TECHNICAL_DATASHEET,
                DocumentType.PRODUCT_LABEL_OR_NAMEPLATE,
                DocumentType.SDS_MSDS,
                DocumentType.CERTIFICATE,
                DocumentType.UNKNOWN_DOCUMENT,
            },
        )


if __name__ == "__main__":
    unittest.main()
