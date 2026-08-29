"""Focused LOG-TRADE01 validation; intentionally not a broad application regression."""

from __future__ import annotations

import json
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from core.trade_compliance import (
    DocumentType,
    EvidenceStatus,
    HSClassificationStatus,
    MeasureCategory,
    MeasureStatus,
    PreferenceEligibility,
    RegulatoryAssessmentStatus,
    RegulatoryMeasure,
    SourceAuthority,
    SourceRecord,
    TaxCalculationStatus,
    TaxSnapshotStatus,
    TradeTaxSnapshot,
    assess_document,
    assess_regulatory,
    build_evidence_request_plan,
    build_tax_snapshot,
    calculate_import_taxes,
    generate_hs_assessment,
    load_official_source_registry,
    normalize_product_identity,
    parse_source_record,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "log_trade01"


def fixture(name: str):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def verified_tariff_source(
    *,
    status: EvidenceStatus = EvidenceStatus.VERIFIED,
    conclusion: dict | None = None,
    hs_code: str = "8422",
) -> SourceRecord:
    return SourceRecord(
        jurisdiction="VN",
        authority="Vietnam Customs",
        source_url="https://www.customs.gov.vn/tariff/8422",
        retrieved_at="2026-08-29T09:00:00+07:00",
        effective_from="2026-01-01",
        effective_to="2026-12-31",
        product_hs_scope=(hs_code,),
        conclusion=conclusion
        or {
            "destination_country": "VN",
            "origin_country": "CN",
            "hs_code": hs_code,
            "mfn_rate": "0.10",
            "preferential_rate": "0.05",
            "fta_program": "Example FTA programme",
            "preferential_eligibility": "POTENTIALLY_AVAILABLE",
            "origin_evidence_required": ["CERTIFICATE_OF_ORIGIN"],
            "vat_rate": "0.08",
        },
        confidence=Decimal("0.95"),
        evidence_status=status,
        authority_level=SourceAuthority.OFFICIAL,
        source_reference="official-tariff-record-8422",
    )


class LogTrade01Tests(unittest.TestCase):
    def test_official_source_registry_preserves_discovery_provenance(self):
        registry = load_official_source_registry()
        records = registry.for_jurisdiction("VN")
        self.assertEqual(registry.registry_id, "logistics.trade_compliance.authoritative_sources")
        self.assertFalse(registry.live_source_poc)
        self.assertEqual(len(records), 3)
        self.assertTrue(all(record.source_url.startswith("https://") for record in records))
        self.assertTrue(all(record.authority_level is SourceAuthority.OFFICIAL_DISCOVERY for record in records))
        self.assertTrue(all(record.evidence_status is EvidenceStatus.NOT_RETRIEVED for record in records))
        self.assertTrue(all(record.retrieved_at is None for record in records))

    def test_source_parse_requires_provenance_for_verified_result(self):
        with self.assertRaises(ValueError):
            parse_source_record(
                {
                    "jurisdiction": "VN",
                    "authority": "Vietnam Customs",
                    "source_url": "https://www.customs.gov.vn/tariff/8422",
                    "evidence_status": "VERIFIED",
                    "conclusion": {"hs_code": "8422"},
                }
            )
        with self.assertRaises(ValueError):
            parse_source_record(
                {
                    "jurisdiction": "VN",
                    "authority": "Discovery site",
                    "source_url": "http://example.invalid",
                }
            )

    def test_fixture_a_identity_and_candidate_hs(self):
        identity = normalize_product_identity(fixture("fixture_a_industrial_machine.json"))
        self.assertEqual(identity.category, "machine")
        self.assertEqual(identity.commercial_name, "CartonPro 2000")
        self.assertEqual(identity.field_states["function"].value, "PROVIDED")
        self.assertEqual(identity.missing_fields, ())

        hs = generate_hs_assessment(identity)
        self.assertEqual([candidate.hs_code for candidate in hs.candidates], ["8422"])
        self.assertEqual(hs.final_classification_status, HSClassificationStatus.CANDIDATE_ONLY)
        self.assertNotEqual(hs.final_classification_status.value, "FINAL_CLASSIFICATION")

    def test_fixture_d_insufficient_description_fails_closed(self):
        identity = normalize_product_identity(fixture("fixture_d_insufficient_machine.json"))
        self.assertEqual(identity.category, "machine")
        self.assertIn("function", identity.missing_fields)
        hs = generate_hs_assessment(identity)
        self.assertEqual(hs.candidates, ())
        self.assertEqual(hs.final_classification_status, HSClassificationStatus.NEEDS_MORE_PRODUCT_DATA)

        assessment = assess_regulatory(identity)
        self.assertEqual(assessment.assessment_status, RegulatoryAssessmentStatus.NEEDS_CUSTOMER_INPUT)
        self.assertEqual(assessment.hs_candidates.candidates, ())
        self.assertEqual(assessment.import_status, "UNKNOWN")

    def test_fixture_e_multiple_candidates_are_ambiguous(self):
        identity = normalize_product_identity(fixture("fixture_e_ambiguous_machine.json"))
        hs = generate_hs_assessment(identity)
        self.assertGreaterEqual(len(hs.candidates), 2)
        self.assertEqual(hs.final_classification_status, HSClassificationStatus.HUMAN_CLASSIFICATION_REQUIRED)
        self.assertTrue(hs.ambiguity)
        assessment = assess_regulatory(identity)
        self.assertEqual(assessment.assessment_status, RegulatoryAssessmentStatus.NEEDS_HS_CONFIRMATION)
        self.assertIn("technical_specifications", assessment.missing_information)

    def test_document_requests_are_conditional_for_machine(self):
        plan = build_evidence_request_plan(fixture("fixture_a_industrial_machine.json"))
        requested = {request.document_type for request in plan.requests}
        self.assertIn(DocumentType.PRODUCT_CATALOGUE, requested)
        self.assertIn(DocumentType.PRODUCT_PHOTOGRAPHS, requested)
        self.assertNotIn(DocumentType.SDS_MSDS, requested)
        self.assertNotIn(DocumentType.CAS_NUMBER, requested)

    def test_present_but_invalid_document_does_not_satisfy_request(self):
        plan = build_evidence_request_plan(
            fixture("fixture_a_industrial_machine.json"),
            supplied_documents=[
                {
                    "type": "CATALOGUE",
                    "present": True,
                    "valid": False,
                    "relevant": True,
                    "sufficient": False,
                }
            ],
        )
        self.assertIn(
            DocumentType.PRODUCT_CATALOGUE,
            {request.document_type for request in plan.requests},
        )

    def test_chemical_without_sds_or_composition_requests_evidence(self):
        product = fixture("fixture_b_chemical_without_sds.json")
        identity = normalize_product_identity(product)
        plan = build_evidence_request_plan(product)
        requested = {request.document_type for request in plan.requests}
        self.assertTrue({DocumentType.SDS_MSDS, DocumentType.COMPOSITION, DocumentType.CAS_NUMBER} <= requested)
        self.assertIn("DANGEROUS_GOODS_STATUS_UNKNOWN", " ".join(plan.warnings))
        self.assertIsNone(identity.dangerous_goods_status)
        self.assertEqual(generate_hs_assessment(identity).candidates, ())
        assessment = assess_regulatory(product)
        self.assertEqual(assessment.assessment_status, RegulatoryAssessmentStatus.NEEDS_CUSTOMER_INPUT)
        self.assertNotIn("NORMALLY_IMPORTABLE", assessment.import_status)
        self.assertIn(MeasureCategory.CHEMICAL_CONTROL, {measure.category for measure in assessment.measures})
        self.assertIn(MeasureCategory.DANGEROUS_GOODS, {measure.category for measure in assessment.measures})

    def test_iso_13485_is_not_sufficient_import_permission(self):
        product = fixture("fixture_c_possible_medical_iso.json")
        document = {
            "type": "ISO13485",
            "present": True,
            "valid": True,
            "relevant": True,
            "sufficient": True,
        }
        assessed = assess_document(document, product)
        self.assertTrue(assessed.present)
        self.assertTrue(assessed.valid)
        self.assertTrue(assessed.relevant)
        self.assertFalse(assessed.sufficient)
        self.assertIn("does not establish", assessed.interpretation)
        assessment = assess_regulatory(product, documents=[document])
        self.assertEqual(assessment.assessment_status, RegulatoryAssessmentStatus.REGULATORY_REVIEW_REQUIRED)
        self.assertEqual(assessment.import_status, "UNKNOWN")
        self.assertIn("ISO_13485_PRESENT", " ".join(assessment.warnings))
        self.assertIn(
            MeasureCategory.MEDICAL_DEVICE_CONTROL,
            {measure.category for measure in assessment.measures},
        )
        self.assertIn(
            MeasureCategory.CONFORMITY_ASSESSMENT,
            {measure.category for measure in assessment.measures},
        )

    def test_regulatory_measure_categories_preserve_review_state(self):
        categories = (
            MeasureCategory.IMPORT_RESTRICTION,
            MeasureCategory.IMPORT_LICENCE,
            MeasureCategory.SPECIALIZED_INSPECTION,
            MeasureCategory.QUALITY_INSPECTION,
            MeasureCategory.CHEMICAL_CONTROL,
            MeasureCategory.MEDICAL_DEVICE_CONTROL,
            MeasureCategory.CERTIFICATE_REQUIREMENT,
        )
        for category in categories:
            measure = RegulatoryMeasure(
                category=category,
                status=MeasureStatus.REVIEW_REQUIRED,
                conclusion="Authority/source required before a conclusion.",
            )
            self.assertEqual(measure.to_dict()["status"], "REVIEW_REQUIRED")
            self.assertEqual(measure.to_dict()["category"], category.value)

        source = SourceRecord(
            jurisdiction="VN",
            authority="Vietnam Trade Information Portal",
            source_url="https://vietnamtradeportal.gov.vn/procedure/8422",
            retrieved_at="2026-08-29T09:00:00+07:00",
            product_hs_scope=("8422",),
            conclusion={
                "measures": [
                    {
                        "category": "IMPORT_RESTRICTION",
                        "status": "APPLIES",
                        "conclusion": "Source-specific restriction text requires review.",
                    }
                ]
            },
            confidence=Decimal("0.90"),
            evidence_status=EvidenceStatus.VERIFIED,
            authority_level=SourceAuthority.OFFICIAL,
        )
        assessment = assess_regulatory(
            fixture("fixture_a_industrial_machine.json"),
            source_results=[source],
        )
        self.assertEqual(assessment.assessment_status, RegulatoryAssessmentStatus.VERIFIED_FROM_SOURCE)
        self.assertEqual(assessment.measures[0].category, MeasureCategory.IMPORT_RESTRICTION)
        self.assertEqual(assessment.measures[0].evidence_status, EvidenceStatus.VERIFIED)

    def test_conflicting_or_stale_official_sources_fail_closed(self):
        for status, expected in (
            (EvidenceStatus.CONFLICTING, RegulatoryAssessmentStatus.REGULATORY_REVIEW_REQUIRED),
            (EvidenceStatus.STALE, RegulatoryAssessmentStatus.SOURCE_VERIFICATION_REQUIRED),
        ):
            assessment = assess_regulatory(
                fixture("fixture_a_industrial_machine.json"),
                source_results=[verified_tariff_source(status=status)],
            )
            self.assertEqual(assessment.assessment_status, expected)
            self.assertNotEqual(assessment.assessment_status, RegulatoryAssessmentStatus.VERIFIED_FROM_SOURCE)

    def test_official_source_with_wrong_product_scope_is_not_usable(self):
        assessment = assess_regulatory(
            fixture("fixture_a_industrial_machine.json"),
            source_results=[verified_tariff_source(hs_code="9999")],
        )
        self.assertEqual(assessment.assessment_status, RegulatoryAssessmentStatus.SOURCE_VERIFICATION_REQUIRED)
        self.assertIn("SOURCE_SCOPE_UNPROVEN", " ".join(assessment.warnings))

    def test_regulatory_source_absence_is_not_a_clean_pass(self):
        assessment = assess_regulatory(fixture("fixture_a_industrial_machine.json"))
        self.assertEqual(assessment.assessment_status, RegulatoryAssessmentStatus.SOURCE_VERIFICATION_REQUIRED)
        self.assertEqual(assessment.import_status, "UNKNOWN")
        self.assertEqual(len(assessment.legal_sources), 3)
        self.assertTrue(all(source.evidence_status is EvidenceStatus.NOT_RETRIEVED for source in assessment.legal_sources))

    def test_known_hs_without_tariff_source_withholds_rate_and_tax(self):
        scope = fixture("fixture_f_known_hs_no_tariff_source.json")
        snapshot = build_tax_snapshot(**scope)
        self.assertEqual(snapshot.status, TaxSnapshotStatus.SOURCE_VERIFICATION_REQUIRED)
        self.assertIsNone(snapshot.mfn_import_duty)
        result = calculate_import_taxes(snapshot, Decimal("1000"), other_tax_amount=Decimal("0"))
        self.assertEqual(result.status, TaxCalculationStatus.INCOMPLETE)
        self.assertIsNone(result.total_tax)
        self.assertIn("verified_tariff_snapshot", result.missing_inputs)

    def test_verified_tariff_requires_explicit_final_hs_and_keeps_rates_separate(self):
        source = verified_tariff_source()
        candidate_snapshot = build_tax_snapshot(
            origin_country="CN",
            destination_country="VN",
            hs_code="8422",
            assessment_date="2026-08-29",
            source_result=source,
            hs_is_final=False,
        )
        self.assertEqual(candidate_snapshot.status, TaxSnapshotStatus.SOURCE_VERIFICATION_REQUIRED)
        self.assertIsNone(candidate_snapshot.mfn_import_duty)

        snapshot = build_tax_snapshot(
            origin_country="CN",
            destination_country="VN",
            hs_code="8422",
            assessment_date="2026-08-29",
            source_result=source,
            hs_is_final=True,
        )
        self.assertEqual(snapshot.status, TaxSnapshotStatus.VERIFIED_FROM_SOURCE)
        self.assertEqual(snapshot.mfn_import_duty, Decimal("0.10"))
        self.assertEqual(snapshot.preferential_duty, Decimal("0.05"))
        self.assertEqual(snapshot.vat_rate, Decimal("0.08"))
        self.assertEqual(snapshot.preferential_eligibility, PreferenceEligibility.POTENTIALLY_AVAILABLE)

        result = calculate_import_taxes(snapshot, Decimal("1000"), other_tax_amount=Decimal("0"))
        self.assertEqual(result.status, TaxCalculationStatus.CALCULATED)
        self.assertEqual(result.total_tax, Decimal("188.00"))
        self.assertEqual(
            [step.name for step in result.steps],
            ["CUSTOMS_VALUE", "IMPORT_DUTY", "OTHER_TAX", "VAT_TAXABLE_BASE", "VAT", "TOTAL_TAX"],
        )
        self.assertEqual(result.steps[1].inputs["rate_type"], "MFN")
        self.assertIn("customs_value × duty_rate", result.steps[1].formula)

        preferential_result = calculate_import_taxes(
            snapshot,
            Decimal("1000"),
            other_tax_amount=Decimal("0"),
            use_preferential=True,
        )
        self.assertEqual(preferential_result.status, TaxCalculationStatus.INCOMPLETE)
        self.assertIn("verified_preferential_eligibility", preferential_result.missing_inputs)

    def test_tax_calculation_does_not_guess_missing_or_invalid_inputs(self):
        snapshot = build_tax_snapshot(
            origin_country="CN",
            destination_country="VN",
            hs_code="8422",
            assessment_date="2026-08-29",
            source_result=verified_tariff_source(),
            hs_is_final=True,
        )
        missing_value = calculate_import_taxes(snapshot, None, other_tax_amount=Decimal("0"))
        self.assertEqual(missing_value.status, TaxCalculationStatus.INCOMPLETE)
        self.assertIsNone(missing_value.total_tax)
        invalid_other_tax = calculate_import_taxes(snapshot, Decimal("1000"), other_tax_amount=Decimal("-1"))
        self.assertEqual(invalid_other_tax.status, TaxCalculationStatus.INCOMPLETE)
        self.assertIsNone(invalid_other_tax.total_tax)

        forged_snapshot = TradeTaxSnapshot(
            origin_country="CN",
            destination_country="VN",
            hs_code="8422",
            assessment_date="2026-08-29",
            mfn_import_duty=Decimal("0.10"),
            vat_rate=Decimal("0.08"),
            status=TaxSnapshotStatus.VERIFIED_FROM_SOURCE,
            hs_is_final=True,
        )
        forged_result = calculate_import_taxes(forged_snapshot, Decimal("1000"), other_tax_amount=Decimal("0"))
        self.assertEqual(forged_result.status, TaxCalculationStatus.INCOMPLETE)
        self.assertIn("verified_tariff_source", forged_result.missing_inputs)

        stale_source_snapshot = TradeTaxSnapshot(
            origin_country="CN",
            destination_country="VN",
            hs_code="8422",
            assessment_date="2026-08-29",
            mfn_import_duty=Decimal("0.10"),
            vat_rate=Decimal("0.08"),
            source=replace(verified_tariff_source(), effective_to="2026-08-01"),
            status=TaxSnapshotStatus.VERIFIED_FROM_SOURCE,
            hs_is_final=True,
        )
        stale_result = calculate_import_taxes(stale_source_snapshot, Decimal("1000"), other_tax_amount=Decimal("0"))
        self.assertEqual(stale_result.status, TaxCalculationStatus.INCOMPLETE)
        self.assertIn("verified_tariff_source_scope", stale_result.missing_inputs)


if __name__ == "__main__":
    unittest.main()
