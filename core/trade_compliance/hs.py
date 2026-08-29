"""Conservative HS heading hypotheses; never a final classification."""

from __future__ import annotations

import re
import unicodedata

from .identity import normalize_product_identity
from .models import (
    EvidenceStatus,
    HSAssessment,
    HSClassificationStatus,
    HSCodeCandidate,
    ProductIdentity,
)


def _fold(text: object) -> str:
    value = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", value).strip().lower()


def _facts(identity: ProductIdentity) -> tuple[str, ...]:
    facts: list[str] = []
    for field_name in (
        "product_name",
        "function",
        "intended_use",
        "material",
        "composition",
        "operating_principle",
        "technical_specifications",
        "medical_device_status",
        "dangerous_goods_status",
    ):
        value = getattr(identity, field_name)
        if isinstance(value, dict):
            if value:
                facts.append(field_name)
        elif value not in (None, "", (), []):
            facts.append(field_name)
    if identity.chemical_identifiers:
        facts.append("chemical_identifiers")
    return tuple(facts)


def generate_hs_candidates(identity: ProductIdentity) -> tuple[HSCodeCandidate, ...]:
    normalized = normalize_product_identity(identity)
    text = _fold(
        " ".join(
            str(value or "")
            for value in (
                normalized.product_name,
                normalized.function,
                normalized.intended_use,
                normalized.operating_principle,
                normalized.composition,
            )
        )
    )
    used = _facts(normalized)

    if normalized.category == "machine":
        if not normalized.function and not normalized.operating_principle:
            return ()
        if any(token in text for token in ("weigh", "scale", "can", "weighing")):
            return (
                HSCodeCandidate(
                    hs_code="8423",
                    description="Weighing machinery",
                    reasoning="The supplied function indicates weighing; verify the machine's exact operation and scope.",
                    product_facts_used=used,
                    confidence="0.52",
                ),
            )
        if any(token in text for token in ("packag", "fill", "seal", "wrap")):
            return (
                HSCodeCandidate(
                    hs_code="8422",
                    description="Dishwashing, cleaning, filling, closing, sealing or labelling machinery",
                    reasoning="The supplied function indicates packaging/filling/sealing; verify the exact machine function.",
                    product_facts_used=used,
                    confidence="0.52",
                ),
            )
        if any(token in text for token in ("metal cut", "metalwork", "milling", "turning", "lathe", "press", "forge")):
            return (
                HSCodeCandidate(
                    hs_code="8461",
                    description="Machine-tools for working metal by removing material",
                    reasoning="The function suggests metal-working; the exact process and machine operation must be confirmed.",
                    product_facts_used=used,
                    confidence="0.42",
                ),
                HSCodeCandidate(
                    hs_code="8462",
                    description="Machine-tools for working metal by forging, hammering or pressing",
                    reasoning="Pressing/forging signals could move the product to a neighbouring heading.",
                    product_facts_used=used,
                    confidence="0.38",
                ),
            )
        if any(token in text for token in ("conveyor", "convey", "lift", "material handling", "transport")):
            return (
                HSCodeCandidate(
                    hs_code="8428",
                    description="Lifting, handling, loading or unloading machinery",
                    reasoning="The function indicates material handling; verify whether the machine is a conveyor or another handling system.",
                    product_facts_used=used,
                    confidence="0.48",
                ),
                HSCodeCandidate(
                    hs_code="8479",
                    description="Machines and mechanical appliances having individual functions, not specified elsewhere",
                    reasoning="A complete function and construction review is needed to exclude the residual machinery heading.",
                    product_facts_used=used,
                    confidence="0.31",
                ),
            )
        return (
            HSCodeCandidate(
                hs_code="8479",
                description="Machines and mechanical appliances having individual functions, not specified elsewhere",
                reasoning="The product is described as an industrial machine, but the exact function and heading exclusions remain to be verified.",
                product_facts_used=used,
                confidence="0.30",
            ),
            HSCodeCandidate(
                hs_code="8428",
                description="Lifting, handling, loading or unloading machinery",
                reasoning="Material-handling machinery remains plausible until the function and operating principle are confirmed.",
                product_facts_used=used,
                confidence="0.24",
            ),
        )

    if normalized.category == "chemical":
        if not normalized.composition and not normalized.chemical_identifiers:
            return ()
        candidates: list[HSCodeCandidate] = []
        if any(token in text for token in ("detergent", "surfactant", "surface active")):
            candidates.append(
                HSCodeCandidate(
                    hs_code="3402",
                    description="Organic surface-active agents and preparations",
                    reasoning="The supplied composition/use suggests a surface-active preparation; verify concentration and formulation.",
                    product_facts_used=used,
                    confidence="0.42",
                )
            )
        candidates.append(
            HSCodeCandidate(
                hs_code="3824",
                description="Chemical products and preparations not elsewhere specified",
                reasoning="Composition evidence is not sufficient to exclude the residual chemical-preparation heading.",
                product_facts_used=used,
                confidence="0.31",
            )
        )
        return tuple(candidates)

    if normalized.category == "medical_device":
        if any(token in text for token in ("prosthe", "orthop", "implant")):
            return (
                HSCodeCandidate(
                    hs_code="9021",
                    description="Orthopaedic appliances and artificial parts of the body",
                    reasoning="The intended use suggests an orthopaedic or implant product; verify device construction and purpose.",
                    product_facts_used=used,
                    confidence="0.40",
                ),
            )
        return (
            HSCodeCandidate(
                hs_code="9018",
                description="Instruments and appliances used in medical, surgical, dental or veterinary sciences",
                reasoning="A medical-device identity is possible, but model-specific function and exclusions must be verified.",
                product_facts_used=used,
                confidence="0.34",
            ),
            HSCodeCandidate(
                hs_code="9021",
                description="Orthopaedic appliances and artificial parts of the body",
                reasoning="An orthopaedic heading remains possible until intended use and construction are documented.",
                product_facts_used=used,
                confidence="0.20",
            ),
        )

    return ()


def generate_hs_assessment(product: ProductIdentity) -> HSAssessment:
    identity = normalize_product_identity(product)
    candidates = generate_hs_candidates(identity)
    used = _facts(identity)
    missing = identity.missing_fields
    ambiguity: list[str] = []
    if not candidates:
        reasoning = "No HS candidate is emitted because product identity facts are insufficient."
        status = HSClassificationStatus.NEEDS_MORE_PRODUCT_DATA
        confidence = "0"
    elif len(candidates) > 1:
        ambiguity.append("Multiple headings remain plausible; the candidate list is not a final classification.")
        if missing:
            ambiguity.append("Missing required product facts: " + ", ".join(missing) + ".")
        reasoning = "Several headings are plausible from the supplied facts; human classification and source verification are required."
        status = HSClassificationStatus.HUMAN_CLASSIFICATION_REQUIRED
        confidence = max(candidate.confidence for candidate in candidates)
    elif missing:
        ambiguity.append("A single provisional heading is not sufficient while required product facts are missing.")
        reasoning = "One provisional heading is shown only as a candidate; more product data is required before classification review."
        status = HSClassificationStatus.NEEDS_MORE_PRODUCT_DATA
        confidence = candidates[0].confidence
    else:
        reasoning = "One provisional heading hypothesis is available; it remains candidate-only pending human and source review."
        status = HSClassificationStatus.CANDIDATE_ONLY
        confidence = candidates[0].confidence
    return HSAssessment(
        candidates=candidates,
        candidate_reasoning=reasoning,
        product_facts_used=used,
        missing_facts=missing,
        ambiguity=tuple(ambiguity),
        confidence=confidence,
        final_classification_status=status,
        source_status=EvidenceStatus.NOT_RETRIEVED,
    )
