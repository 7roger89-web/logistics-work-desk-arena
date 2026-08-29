"""Fail-closed regulatory assessment composition."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date
from decimal import Decimal
from typing import Any

from .evidence import build_evidence_request_plan
from .hs import generate_hs_assessment
from .identity import normalize_product_identity
from .models import (
    DocumentType,
    EvidenceStatus,
    HSAssessment,
    HSClassificationStatus,
    MeasureCategory,
    MeasureStatus,
    ProductIdentity,
    RegulatoryAssessment,
    RegulatoryAssessmentStatus,
    RegulatoryMeasure,
    SourceAuthority,
    SourceRecord,
)
from .sources import OfficialSourceRegistry, load_official_source_registry, parse_source_record


def _source_list(
    source_results: Iterable[SourceRecord | Mapping[str, Any]] | SourceRecord | Mapping[str, Any] | None,
    *,
    destination_country: str,
) -> tuple[SourceRecord, ...]:
    if source_results is None:
        return ()
    if isinstance(source_results, SourceRecord) or isinstance(source_results, Mapping):
        source_results = (source_results,)
    records: list[SourceRecord] = []
    for source in source_results:
        if isinstance(source, SourceRecord):
            records.append(source)
        else:
            records.append(parse_source_record(source, default_jurisdiction=destination_country))
    return tuple(records)


def _dedupe_sources(sources: Iterable[SourceRecord]) -> tuple[SourceRecord, ...]:
    seen: set[tuple[str, str]] = set()
    result: list[SourceRecord] = []
    for source in sources:
        key = (source.source_url, source.source_reference or "")
        if key in seen:
            continue
        seen.add(key)
        result.append(source)
    return tuple(result)


def _source_scope_matches(
    source: SourceRecord,
    *,
    identity: ProductIdentity,
    hs: HSAssessment,
    destination_country: str,
    assessment_date: date,
) -> bool:
    if source.authority_level is not SourceAuthority.OFFICIAL:
        return False
    if source.evidence_status not in {EvidenceStatus.VERIFIED, EvidenceStatus.PARTIALLY_VERIFIED}:
        return False
    if not source.retrieved_at or source.jurisdiction.strip().upper() != destination_country:
        return False
    if not source.covers_date(assessment_date):
        return False
    candidate_codes = {candidate.hs_code for candidate in hs.candidates}
    conclusion = source.conclusion if isinstance(source.conclusion, Mapping) else {}
    conclusion_hs = conclusion.get("hs_code", conclusion.get("hs"))
    if conclusion_hs is not None:
        scoped_hs = str(conclusion_hs).strip()
        if source.product_hs_scope and scoped_hs not in source.product_hs_scope:
            return False
        if scoped_hs not in candidate_codes:
            return False
    elif not candidate_codes.intersection(set(source.product_hs_scope)):
        return False
    scoped_origin = conclusion.get("origin_country", conclusion.get("origin"))
    if scoped_origin is not None:
        if not identity.origin_country or str(scoped_origin).strip().upper() != identity.origin_country.strip().upper():
            return False
    scoped_destination = conclusion.get("destination_country", conclusion.get("destination"))
    if scoped_destination is not None and str(scoped_destination).strip().upper() != destination_country:
        return False
    return True


def _usable_sources(
    sources: Iterable[SourceRecord],
    *,
    identity: ProductIdentity,
    hs: HSAssessment,
    destination_country: str,
    assessment_date: date,
) -> tuple[SourceRecord, ...]:
    return tuple(
        source
        for source in sources
        if _source_scope_matches(
            source,
            identity=identity,
            hs=hs,
            destination_country=destination_country,
            assessment_date=assessment_date,
        )
    )


def _document_type(value: Any) -> DocumentType:
    if isinstance(value, DocumentType):
        return value
    text = str(value).strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "CATALOGUE": DocumentType.PRODUCT_CATALOGUE,
        "DATASHEET": DocumentType.TECHNICAL_DATASHEET,
        "SDS": DocumentType.SDS_MSDS,
        "MSDS": DocumentType.SDS_MSDS,
        "CAS": DocumentType.CAS_NUMBER,
        "ISO13485": DocumentType.ISO_13485,
        "ISO_13485": DocumentType.ISO_13485,
        "CFS": DocumentType.CFS,
        "CE": DocumentType.CE_DOCUMENTATION,
    }
    if text in aliases:
        return aliases[text]
    return DocumentType(text)


def _source_measures(source: SourceRecord) -> tuple[RegulatoryMeasure, ...]:
    conclusion = source.conclusion
    if not isinstance(conclusion, Mapping):
        return ()
    raw_measures = conclusion.get("measures", ())
    if not isinstance(raw_measures, (list, tuple)):
        return ()
    measures: list[RegulatoryMeasure] = []
    for raw in raw_measures:
        if not isinstance(raw, Mapping):
            continue
        try:
            category = MeasureCategory(str(raw.get("category")))
            status = MeasureStatus(str(raw.get("status", MeasureStatus.UNKNOWN.value)))
            if source.evidence_status not in {EvidenceStatus.VERIFIED, EvidenceStatus.PARTIALLY_VERIFIED}:
                status = MeasureStatus.REVIEW_REQUIRED
            required_documents = tuple(
                _document_type(item) for item in raw.get("required_documents", ())
            )
        except (TypeError, ValueError):
            continue
        confidence = raw.get("confidence", source.confidence or Decimal("0"))
        measures.append(
            RegulatoryMeasure(
                category=category,
                status=status,
                conclusion=str(raw.get("conclusion")) if raw.get("conclusion") is not None else None,
                required_documents=required_documents,
                responsible_authority=str(raw.get("responsible_authority")) if raw.get("responsible_authority") else source.authority,
                legal_sources=(source,),
                confidence=confidence,
                evidence_status=source.evidence_status,
            )
        )
    return tuple(measures)


def _append_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def assess_regulatory(
    product: ProductIdentity | Mapping[str, Any] | str,
    *,
    hs_assessment: HSAssessment | None = None,
    documents: Iterable[Any] | Mapping[Any, Any] | None = None,
    source_results: Iterable[SourceRecord | Mapping[str, Any]] | SourceRecord | Mapping[str, Any] | None = None,
    source_registry: OfficialSourceRegistry | None = None,
    destination_country: str = "VN",
) -> RegulatoryAssessment:
    """Compose identity, HS, evidence, and source state without legal guessing."""

    identity = normalize_product_identity(product)
    plan = build_evidence_request_plan(identity, documents)
    hs = hs_assessment or generate_hs_assessment(identity)
    destination = str(destination_country or "VN").strip().upper()
    registry_error: str | None = None
    if source_registry is not None:
        registry = source_registry
    else:
        try:
            registry = load_official_source_registry()
        except (OSError, ValueError) as exc:
            registry = None
            registry_error = str(exc)
    discovered = registry.for_jurisdiction(destination) if registry is not None else ()
    supplied_sources = _source_list(source_results, destination_country=destination)
    legal_sources = _dedupe_sources((*supplied_sources, *discovered))
    today = date.today()
    usable_sources = _usable_sources(
        supplied_sources,
        identity=identity,
        hs=hs,
        destination_country=destination,
        assessment_date=today,
    )

    conflicts = tuple(source for source in supplied_sources if source.evidence_status is EvidenceStatus.CONFLICTING)
    stale = tuple(source for source in supplied_sources if source.evidence_status is EvidenceStatus.STALE)
    expired = tuple(
        source
        for source in supplied_sources
        if source.evidence_status in {EvidenceStatus.VERIFIED, EvidenceStatus.PARTIALLY_VERIFIED}
        and source.effective_to
        and not source.covers_date(today)
    )
    stale = (*stale, *expired)
    scoped_out = tuple(
        source
        for source in supplied_sources
        if source not in usable_sources
        and source not in conflicts
        and source not in stale
        and source.evidence_status in {EvidenceStatus.VERIFIED, EvidenceStatus.PARTIALLY_VERIFIED}
    )
    measures: list[RegulatoryMeasure] = list(
        measure for source in supplied_sources for measure in _source_measures(source)
    )
    unproven_source_urls = {
        source.source_url for source in (*conflicts, *stale, *scoped_out)
    }
    for measure in measures:
        if measure.status is MeasureStatus.APPLIES and any(
            source.source_url in unproven_source_urls for source in measure.legal_sources
        ):
            measure.status = MeasureStatus.REVIEW_REQUIRED
    measure_categories = {measure.category for measure in measures}
    warnings = list(plan.warnings)
    missing_information = list(plan.missing_information)
    authorities = [source.authority for source in usable_sources]

    if identity.category == "chemical":
        if MeasureCategory.CHEMICAL_CONTROL not in measure_categories:
            measures.append(
                RegulatoryMeasure(
                    category=MeasureCategory.CHEMICAL_CONTROL,
                    status=MeasureStatus.REVIEW_REQUIRED,
                    conclusion="Chemical-control scope is unresolved; do not infer an import requirement from category alone.",
                    required_documents=(DocumentType.SDS_MSDS, DocumentType.COMPOSITION, DocumentType.CAS_NUMBER),
                    responsible_authority=None,
                    legal_sources=(),
                    confidence=Decimal("0"),
                    evidence_status=EvidenceStatus.NOT_RETRIEVED,
                )
            )
        if MeasureCategory.DANGEROUS_GOODS not in measure_categories:
            measures.append(
                RegulatoryMeasure(
                    category=MeasureCategory.DANGEROUS_GOODS,
                    status=MeasureStatus.REVIEW_REQUIRED,
                    conclusion="Dangerous-goods status is unresolved pending SDS/composition evidence.",
                    required_documents=(DocumentType.SDS_MSDS, DocumentType.UN_NUMBER),
                    responsible_authority=None,
                    legal_sources=(),
                    confidence=Decimal("0"),
                    evidence_status=EvidenceStatus.NOT_RETRIEVED,
                )
            )
    elif identity.category == "medical_device":
        if MeasureCategory.MEDICAL_DEVICE_CONTROL not in measure_categories:
            measures.append(
                RegulatoryMeasure(
                    category=MeasureCategory.MEDICAL_DEVICE_CONTROL,
                    status=MeasureStatus.REVIEW_REQUIRED,
                    conclusion="Medical-device scope and product-specific procedure require regulatory review.",
                    required_documents=(DocumentType.MEDICAL_DEVICE_DOCUMENTATION, DocumentType.INTENDED_USE_STATEMENT),
                    responsible_authority=None,
                    legal_sources=(),
                    confidence=Decimal("0"),
                    evidence_status=EvidenceStatus.NOT_RETRIEVED,
                )
            )
        if MeasureCategory.CONFORMITY_ASSESSMENT not in measure_categories:
            measures.append(
                RegulatoryMeasure(
                    category=MeasureCategory.CONFORMITY_ASSESSMENT,
                    status=MeasureStatus.REVIEW_REQUIRED,
                    conclusion="Conformity/certification relevance is unresolved; ISO 13485 alone is not approval.",
                    required_documents=(DocumentType.TEST_REPORT, DocumentType.MANUFACTURER_DECLARATION),
                    responsible_authority=None,
                    legal_sources=(),
                    confidence=Decimal("0"),
                    evidence_status=EvidenceStatus.NOT_RETRIEVED,
                )
            )

    assumptions = [
        "Customer-supplied descriptions and documents are normalized evidence, not verified product identity or legal truth.",
        "HS output is candidate-only and cannot be used as a final classification.",
    ]
    if conflicts:
        warnings.append("CONFLICTING_OFFICIAL_SOURCES: retain the conflict and escalate to regulatory review.")
    if stale:
        warnings.append("STALE_SOURCE: current legal conclusion is not established from the supplied source.")
    if scoped_out:
        warnings.append("SOURCE_SCOPE_UNPROVEN: official evidence is not scoped to this product, HS candidate, origin, and date.")
    if not usable_sources:
        warnings.append(
            "No current substantive official source result was supplied; discovery URLs do not prove a regulatory conclusion."
        )
    if registry_error:
        warnings.append(f"SOURCE_UNAVAILABLE: official source registry could not be loaded ({registry_error}).")
    if not legal_sources:
        warnings.append("SOURCE_UNAVAILABLE: no official source registry or source result is available.")
    if identity.category in {"chemical", "medical_device"}:
        warnings.append("Sensitive product scope remains subject to human/regulatory review.")

    if conflicts:
        status = RegulatoryAssessmentStatus.REGULATORY_REVIEW_REQUIRED
        confidence = Decimal("0")
    elif stale:
        status = RegulatoryAssessmentStatus.SOURCE_VERIFICATION_REQUIRED
        confidence = Decimal("0")
    elif scoped_out:
        status = RegulatoryAssessmentStatus.SOURCE_VERIFICATION_REQUIRED
        confidence = Decimal("0")
    elif identity.category in {"chemical", "medical_device"} and not identity.missing_fields and not usable_sources:
        status = RegulatoryAssessmentStatus.REGULATORY_REVIEW_REQUIRED
        confidence = Decimal("0")
    elif len(hs.candidates) > 1 or hs.final_classification_status is HSClassificationStatus.HUMAN_CLASSIFICATION_REQUIRED:
        status = RegulatoryAssessmentStatus.NEEDS_HS_CONFIRMATION
        confidence = hs.confidence
    elif identity.missing_fields:
        status = RegulatoryAssessmentStatus.NEEDS_CUSTOMER_INPUT
        confidence = min(hs.confidence, Decimal("0.25"))
    elif hs.final_classification_status is HSClassificationStatus.NEEDS_MORE_PRODUCT_DATA:
        status = RegulatoryAssessmentStatus.NEEDS_CUSTOMER_INPUT
        confidence = hs.confidence
    elif not legal_sources:
        status = RegulatoryAssessmentStatus.SOURCE_UNAVAILABLE
        confidence = Decimal("0")
    elif not usable_sources:
        status = RegulatoryAssessmentStatus.SOURCE_VERIFICATION_REQUIRED
        confidence = Decimal("0")
    elif any(source.evidence_status is EvidenceStatus.PARTIALLY_VERIFIED for source in usable_sources):
        status = RegulatoryAssessmentStatus.PARTIALLY_VERIFIED
        confidence = min(hs.confidence, Decimal("0.60"))
    else:
        status = RegulatoryAssessmentStatus.VERIFIED_FROM_SOURCE
        confidence = min(hs.confidence, Decimal("0.80"))

    if not authorities:
        authorities.append("UNKNOWN")
    for measure in measures:
        if measure.responsible_authority:
            _append_unique(authorities, measure.responsible_authority)

    return RegulatoryAssessment(
        product_identity=identity,
        hs_candidates=hs,
        import_status="UNKNOWN",
        measures=tuple(measures),
        required_documents=plan.requests,
        responsible_authorities=tuple(authorities),
        legal_sources=legal_sources,
        missing_information=tuple(dict.fromkeys((*missing_information, *hs.missing_facts))),
        assumptions=tuple(assumptions),
        warnings=tuple(dict.fromkeys(warnings)),
        confidence=confidence,
        assessment_status=status,
    )
