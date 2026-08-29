"""Conditional customer-evidence requests and document semantics."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .models import (
    DocumentEvidence,
    DocumentRequest,
    DocumentType,
    EvidenceRequestPlan,
    ProductIdentity,
    SourceRecord,
)
from .identity import normalize_product_identity


def _normalise_document_type(value: Any) -> DocumentType:
    if isinstance(value, DocumentType):
        return value
    text = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "CATALOGUE": DocumentType.PRODUCT_CATALOGUE,
        "PRODUCT_CATALOG": DocumentType.PRODUCT_CATALOGUE,
        "DATASHEET": DocumentType.TECHNICAL_DATASHEET,
        "TECHNICAL_DATASHEET": DocumentType.TECHNICAL_DATASHEET,
        "PHOTO": DocumentType.PRODUCT_PHOTOGRAPHS,
        "PHOTOS": DocumentType.PRODUCT_PHOTOGRAPHS,
        "NAMEPLATE": DocumentType.NAMEPLATE_PHOTOGRAPH,
        "SDS": DocumentType.SDS_MSDS,
        "MSDS": DocumentType.SDS_MSDS,
        "SDS_MSDS": DocumentType.SDS_MSDS,
        "CAS": DocumentType.CAS_NUMBER,
        "CAS_NUMBER": DocumentType.CAS_NUMBER,
        "UN": DocumentType.UN_NUMBER,
        "UN_NUMBER": DocumentType.UN_NUMBER,
        "ISO13485": DocumentType.ISO_13485,
        "ISO_13485": DocumentType.ISO_13485,
        "ISO": DocumentType.ISO_CERTIFICATE,
        "CFS": DocumentType.CFS,
        "CE": DocumentType.CE_DOCUMENTATION,
        "INTENDED_USE": DocumentType.INTENDED_USE_STATEMENT,
    }
    if text in aliases:
        return aliases[text]
    return DocumentType(text)


def _coerce_document(raw: DocumentEvidence | DocumentType | Mapping[str, Any]) -> DocumentEvidence:
    if isinstance(raw, DocumentEvidence):
        return raw
    if isinstance(raw, DocumentType):
        return DocumentEvidence(document_type=raw, present=True)
    if not isinstance(raw, Mapping):
        raise TypeError("document evidence must be a mapping or DocumentEvidence")
    document_type = _normalise_document_type(raw.get("document_type", raw.get("type")))
    source = raw.get("source")
    if source is not None and not isinstance(source, SourceRecord):
        source = None
    return DocumentEvidence(
        document_type=document_type,
        present=bool(raw.get("present", False)),
        valid=raw.get("valid"),
        relevant=raw.get("relevant"),
        sufficient=raw.get("sufficient"),
        interpretation=raw.get("interpretation"),
        source=source,
    )


def _normalise_documents(documents: Iterable[Any] | Mapping[Any, Any] | None) -> tuple[DocumentEvidence, ...]:
    if documents is None:
        return ()
    if isinstance(documents, Mapping):
        items: list[Any] = []
        for key, value in documents.items():
            if isinstance(value, Mapping):
                row = dict(value)
                row.setdefault("document_type", key)
                items.append(row)
            else:
                items.append({"document_type": key, "present": bool(value)})
    else:
        items = list(documents)
    return tuple(_coerce_document(item) for item in items)


def assess_document(
    document: DocumentEvidence | DocumentType | Mapping[str, Any],
    product: ProductIdentity | Mapping[str, Any] | str | None = None,
) -> DocumentEvidence:
    """Preserve present/valid/relevant/sufficient as independent assertions."""

    identity = normalize_product_identity(product) if product is not None else None
    current = _coerce_document(document)
    if current.document_type is DocumentType.ISO_13485:
        relevant = current.relevant
        if identity is not None and identity.category == "medical_device":
            relevant = True if current.present else relevant
        interpretation = (
            "ISO 13485 may evidence a manufacturer quality-management system; "
            "it does not establish product identity, product registration, or import approval."
        )
        return DocumentEvidence(
            document_type=current.document_type,
            present=current.present,
            valid=current.valid,
            relevant=relevant,
            sufficient=False,
            interpretation=interpretation,
            source=current.source,
        )
    return current


def build_evidence_request_plan(
    product: ProductIdentity | Mapping[str, Any] | str,
    supplied_documents: Iterable[Any] | Mapping[Any, Any] | None = None,
) -> EvidenceRequestPlan:
    """Request only documents triggered by the normalized product category."""

    identity = normalize_product_identity(product)
    supplied = tuple(
        assess_document(document, identity)
        for document in _normalise_documents(supplied_documents)
    )
    satisfied = {
        document.document_type
        for document in supplied
        if document.present and document.valid is True and document.relevant is True and document.sufficient is True
    }
    requests: list[DocumentRequest] = []
    missing_information = list(identity.missing_fields)
    warnings = [
        "CUSTOMER_DESCRIPTION != VERIFIED_PRODUCT_IDENTITY",
        "DOCUMENT_PRESENT != DOCUMENT_VALID != DOCUMENT_RELEVANT != DOCUMENT_SUFFICIENT",
    ]

    def request(
        document_type: DocumentType,
        reason: str,
        *,
        priority: str = "NORMAL",
        conditional_on: tuple[str, ...] = (),
    ) -> None:
        if document_type not in satisfied:
            requests.append(
                DocumentRequest(
                    document_type=document_type,
                    reason=reason,
                    priority=priority,
                    conditional_on=conditional_on,
                )
            )
            missing_information.append(document_type.value)

    if identity.category == "machine":
        request(
            DocumentType.PRODUCT_CATALOGUE,
            "Confirm the machine's function, operating principle, and intended use before HS reasoning.",
            priority="HIGH",
        )
        if not identity.technical_specifications:
            request(
                DocumentType.TECHNICAL_DATASHEET,
                "Provide dimensions, capacity, power, and technical operating specifications.",
                priority="HIGH",
            )
        if not identity.model:
            request(
                DocumentType.NAMEPLATE_PHOTOGRAPH,
                "Identify the exact model and manufacturer from the nameplate.",
            )
        if not identity.function or not identity.intended_use:
            request(
                DocumentType.INTENDED_USE_STATEMENT,
                "Describe what the machine does and the customer's intended use.",
                priority="HIGH",
            )
        request(
            DocumentType.PRODUCT_PHOTOGRAPHS,
            "Use photographs to distinguish the machine from adjacent HS headings.",
        )
    elif identity.category == "chemical":
        request(
            DocumentType.SDS_MSDS,
            "Classify chemical hazards and handling controls from the current SDS/MSDS.",
            priority="HIGH",
        )
        if not identity.composition:
            request(
                DocumentType.COMPOSITION,
                "Composition and concentration are needed before chemical/HS or control conclusions.",
                priority="HIGH",
            )
        if not identity.chemical_identifiers:
            request(
                DocumentType.CAS_NUMBER,
                "Provide CAS number(s) or another unambiguous chemical identifier.",
                priority="HIGH",
            )
        if not identity.intended_use:
            request(
                DocumentType.INTENDED_USE_STATEMENT,
                "State the intended use because chemical controls can depend on use.",
            )
        if identity.dangerous_goods_status in (None, "", "UNKNOWN"):
            request(
                DocumentType.UN_NUMBER,
                "Provide the UN number if the current SDS classifies the product as dangerous goods.",
                conditional_on=("if_dangerous_goods_status_is_true_or_unclear",),
            )
            request(
                DocumentType.DANGEROUS_GOODS_DECLARATION,
                "Provide dangerous-goods evidence only if the product is shipped as dangerous goods.",
                conditional_on=("if_dangerous_goods_status_is_true_or_unclear",),
            )
        warnings.append(
            "DANGEROUS_GOODS_STATUS_UNKNOWN: no conclusion that the chemical is non-dangerous without sufficient SDS/MSDS and composition."
        )
    elif identity.category == "medical_device":
        request(
            DocumentType.MEDICAL_DEVICE_DOCUMENTATION,
            "Confirm whether the specific model is a medical device and its product classification.",
            priority="HIGH",
        )
        request(
            DocumentType.PRODUCT_CATALOGUE,
            "Confirm the device's function, intended use, and model-specific characteristics.",
            priority="HIGH",
        )
        if not identity.intended_use:
            request(
                DocumentType.INTENDED_USE_STATEMENT,
                "State the intended medical use and user/patient context.",
                priority="HIGH",
            )
        if not identity.manufacturer or not identity.model:
            request(
                DocumentType.MANUFACTURER_DECLARATION,
                "Identify the manufacturer and exact model for product-specific review.",
            )
        request(
            DocumentType.CFS,
            "Provide CFS only when required by the product-specific destination procedure; it is not an automatic approval.",
            conditional_on=("if_destination_procedure_requires_cfs",),
        )
        request(
            DocumentType.CE_DOCUMENTATION,
            "Provide CE-related evidence only where relevant to the device and destination procedure.",
            conditional_on=("if_device_and_destination_procedure_require_ce_evidence",),
        )
        if any(document.document_type is DocumentType.ISO_13485 and document.present for document in supplied):
            warnings.append(
                "ISO_13485_PRESENT != PRODUCT_IMPORT_APPROVED: ISO 13485 is evidence only and does not establish registration or permission to import."
            )
    else:
        request(
            DocumentType.PRODUCT_CATALOGUE,
            "Provide a catalogue or product sheet to identify the product before any HS or compliance conclusion.",
            priority="HIGH",
        )
        request(
            DocumentType.PRODUCT_PHOTOGRAPHS,
            "Provide product photographs to resolve the generic description.",
        )
        request(
            DocumentType.INTENDED_USE_STATEMENT,
            "Describe function and intended use before selecting a product family.",
            priority="HIGH",
        )

    # A supplied but unverified document is evidence to review, not a completed request.
    for document in supplied:
        if document.present and document.sufficient is not True:
            warnings.append(
                f"{document.document_type.value}_PRESENT_BUT_NOT_SUFFICIENT: validity and relevance remain unverified."
            )

    return EvidenceRequestPlan(
        requests=tuple(requests),
        supplied_documents=supplied,
        missing_information=tuple(dict.fromkeys(missing_information)),
        warnings=tuple(dict.fromkeys(warnings)),
    )
