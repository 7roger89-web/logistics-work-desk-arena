"""Bounded document extraction for LOG-DOC01.

This module extracts customer-provided document evidence. It deliberately does
not classify HS codes, decide importability, or make a legal or hazard
conclusion. The final adapter seam is the existing ``core.trade_compliance``
contract surface.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from pathlib import PurePath
from typing import Any

from core.trade_compliance import (
    DocumentEvidence,
    DocumentType,
    EvidenceRequestPlan,
    EvidenceStatus,
    ProductIdentity,
    SourceAuthority,
    SourceRecord,
    assess_document,
    build_evidence_request_plan,
    normalize_product_identity,
)

MAX_PAYLOAD_BYTES = 10 * 1024 * 1024
MAX_TEXT_CHARS = 1_000_000
MAX_PAGE_COUNT = 200
DOCLING_ADAPTER_IMPLEMENTED = True
PADDLEOCR_ADAPTER_IMPLEMENTED = True
DOCLING_RUNTIME_PROVEN = False
PADDLEOCR_RUNTIME_PROVEN = False


class ExtractionStatus(str, Enum):
    PASS = "PASS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


class DocumentSecurityError(ValueError):
    """Raised when an artifact crosses a bounded security boundary."""


_DOCUMENT_ALIASES: dict[str, DocumentType] = {
    "CATALOGUE": DocumentType.PRODUCT_CATALOGUE,
    "CATALOG": DocumentType.PRODUCT_CATALOGUE,
    "PRODUCT_CATALOGUE": DocumentType.PRODUCT_CATALOGUE,
    "DATASHEET": DocumentType.TECHNICAL_DATASHEET,
    "TECHNICAL_DATASHEET": DocumentType.TECHNICAL_DATASHEET,
    "LABEL": DocumentType.PRODUCT_LABEL_OR_NAMEPLATE,
    "NAMEPLATE": DocumentType.PRODUCT_LABEL_OR_NAMEPLATE,
    "PRODUCT_LABEL": DocumentType.PRODUCT_LABEL_OR_NAMEPLATE,
    "CERT": DocumentType.CERTIFICATE,
    "CERTIFICATE": DocumentType.CERTIFICATE,
    "SDS": DocumentType.SDS_MSDS,
    "MSDS": DocumentType.SDS_MSDS,
    "SDS_MSDS": DocumentType.SDS_MSDS,
    "UNKNOWN": DocumentType.UNKNOWN_DOCUMENT,
    "UNKNOWN_DOCUMENT": DocumentType.UNKNOWN_DOCUMENT,
    # Bounded trade-document canary extension (TT-DOC-CANARY-01).
    # COMMERCIAL_INVOICE maps onto the existing INVOICE contract on purpose;
    # PACKING_LIST already exists in the enum.
    "COMMERCIAL_INVOICE": DocumentType.INVOICE,
    "BILL_OF_LADING": DocumentType.BILL_OF_LADING,
}

_BLOCKED_EXTENSIONS = {
    ".bat",
    ".cmd",
    ".com",
    ".dll",
    ".docm",
    ".exe",
    ".jar",
    ".js",
    ".msi",
    ".php",
    ".pl",
    ".ps1",
    ".py",
    ".rb",
    ".scr",
    ".sh",
    ".so",
    ".vbe",
    ".vbs",
    ".xlsm",
    ".xlam",
    ".xltm",
    ".pptm",
}
_SUSPICIOUS_MARKERS = (
    b"<script",
    b"javascript:",
    b"powershell",
    b"vbaProject",
    b"#! /bin/",
    b"#!/bin/",
)

_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "commercial_name": ("commercial name", "commercial_name", "trade name"),
    "product_name": ("product name", "product_name", "product", "item name", "item"),
    "model": ("model", "model number", "product model"),
    "manufacturer": ("manufacturer", "maker", "manufacturer name"),
    "brand": ("brand", "trade mark"),
    "intended_use": ("intended use", "intended_use", "purpose", "application"),
    "function": ("function", "function description", "use"),
    "material": ("material", "materials"),
    "composition": ("composition", "ingredients", "chemical composition"),
    "operating_principle": ("operating principle", "principle"),
    "voltage": ("voltage", "rated voltage"),
    "power": ("power", "rated power"),
    "capacity": ("capacity", "throughput"),
    "dimensions": ("dimensions", "size"),
    "chemical_identifiers": ("cas", "cas number", "cas no", "chemical identifier"),
    "medical_device_status": ("medical device status", "medical device"),
    "dangerous_goods_status": ("dangerous goods status", "dangerous goods", "dg status"),
    "origin_country": ("origin country", "country of origin"),
    "un_number": ("un number", "un no", "un"),
    "transport_hazard_class": ("transport hazard class", "hazard class", "class"),
    "packing_group": ("packing group", "transport packing group"),
    "transport_proper_shipping_name": ("proper shipping name", "transport proper shipping name"),
    "certificate_standard": ("standard", "certificate standard", "certification standard"),
    "certificate_number": ("certificate number", "certificate no", "cert no"),
    "certificate_scope": ("certificate scope", "scope"),
    "expiry_date": ("expiry date", "expiration date", "valid until"),
    "category": ("category", "product category", "document category"),
}


def _key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def sanitize_filename(filename: str) -> str:
    """Return a safe display filename and reject traversal or empty names."""

    if not isinstance(filename, str) or not filename.strip():
        raise DocumentSecurityError("filename is required")
    if "\x00" in filename or "/" in filename or "\\" in filename:
        raise DocumentSecurityError("path separators and NUL bytes are not allowed")
    if any(part == ".." for part in PurePath(filename).parts):
        raise DocumentSecurityError("path traversal is not allowed")
    normalized = unicodedata.normalize("NFKC", filename).strip()
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", normalized).strip("._")
    if not safe or safe in {".", ".."}:
        raise DocumentSecurityError("filename becomes empty after sanitization")
    return safe[:180]


def _content_bytes(content: str | bytes) -> bytes:
    return content.encode("utf-8") if isinstance(content, str) else content


def _text_content(content: str | bytes) -> str:
    if isinstance(content, str):
        return content
    return content.decode("utf-8", errors="replace")


def _normalise_type(value: Any) -> DocumentType:
    if isinstance(value, DocumentType):
        return value
    text = _key(value).upper()
    if text in _DOCUMENT_ALIASES:
        return _DOCUMENT_ALIASES[text]
    try:
        return DocumentType(text)
    except ValueError:
        return DocumentType.UNKNOWN_DOCUMENT


def _infer_document_type(filename: str, text: str) -> DocumentType:
    haystack = f"{filename} {text[:500]}".lower()
    if "sds" in haystack or "msds" in haystack or "safety data sheet" in haystack:
        return DocumentType.SDS_MSDS
    if "certificate" in haystack or "iso 13485" in haystack or "iso13485" in haystack:
        return DocumentType.CERTIFICATE
    if "datasheet" in haystack or "data sheet" in haystack or "specification" in haystack:
        return DocumentType.TECHNICAL_DATASHEET
    if "catalogue" in haystack or "catalog" in haystack:
        return DocumentType.PRODUCT_CATALOGUE
    if "nameplate" in haystack or "label" in haystack:
        return DocumentType.PRODUCT_LABEL_OR_NAMEPLATE
    return DocumentType.UNKNOWN_DOCUMENT


@dataclass(frozen=True)
class DocumentArtifact:
    """A bounded, untrusted document payload with source identity."""

    filename: str
    content: str | bytes
    document_type: DocumentType | str | None = None
    source_url: str | None = None
    page_count: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        safe_name = sanitize_filename(self.filename)
        object.__setattr__(self, "filename", safe_name)
        if not isinstance(self.content, (str, bytes)):
            raise DocumentSecurityError("content must be text or bytes")
        payload_size = len(_content_bytes(self.content))
        if payload_size > MAX_PAYLOAD_BYTES:
            raise DocumentSecurityError("payload exceeds the bounded size limit")
        if len(_text_content(self.content)) > MAX_TEXT_CHARS:
            raise DocumentSecurityError("text exceeds the bounded size limit")
        if self.page_count is not None and (not isinstance(self.page_count, int) or self.page_count < 1):
            raise DocumentSecurityError("page_count must be a positive integer")
        if self.page_count is not None and self.page_count > MAX_PAGE_COUNT:
            raise DocumentSecurityError("page count exceeds the bounded limit")
        extension = "." + safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
        if extension in _BLOCKED_EXTENSIONS:
            raise DocumentSecurityError("executable, macro, or script documents are rejected")
        lowered = _content_bytes(self.content)[:8192].lower()
        if any(marker.lower() in lowered for marker in _SUSPICIOUS_MARKERS):
            raise DocumentSecurityError("executable or script content is rejected")
        if self.source_url is not None and not str(self.source_url).strip():
            raise DocumentSecurityError("source_url cannot be blank")
        object.__setattr__(self, "document_type", _normalise_type(self.document_type) if self.document_type else None)
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @property
    def content_sha256(self) -> str:
        return hashlib.sha256(_content_bytes(self.content)).hexdigest()


@dataclass
class StructuredExtraction:
    document_type: DocumentType
    fields: dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    source_pages: dict[str, tuple[int, ...]] = field(default_factory=dict)
    method: str = "deterministic_key_value"
    conflicts: dict[str, tuple[str, ...]] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_type": self.document_type.value,
            "fields": dict(self.fields),
            "raw_text": self.raw_text,
            "source_pages": {key: list(value) for key, value in self.source_pages.items()},
            "method": self.method,
            "conflicts": {key: list(value) for key, value in self.conflicts.items()},
            "warnings": list(self.warnings),
            "provenance": dict(self.provenance),
        }


@dataclass
class ExtractionResult:
    artifact: DocumentArtifact
    extraction: StructuredExtraction
    status: ExtractionStatus
    review_reasons: tuple[str, ...] = ()

    @property
    def fields(self) -> dict[str, Any]:
        return self.extraction.fields

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": {
                "filename": self.artifact.filename,
                "document_type": self.artifact.document_type.value if self.artifact.document_type else None,
                "source_url": self.artifact.source_url,
                "page_count": self.artifact.page_count,
                "content_sha256": _artifact_content_sha256(self.artifact),
            },
            "extraction": self.extraction.to_dict(),
            "status": self.status.value,
            "review_reasons": list(self.review_reasons),
        }


def _artifact_content_sha256(artifact: DocumentArtifact) -> str:
    source_sha256 = artifact.metadata.get("source_sha256") if artifact.metadata else None
    if isinstance(source_sha256, str) and re.fullmatch(r"[0-9a-f]{64}", source_sha256):
        return source_sha256
    return artifact.content_sha256


def _canonical_field(label: str) -> str | None:
    normalized = _key(label)
    for field_name, aliases in _FIELD_ALIASES.items():
        if normalized in {_key(alias) for alias in aliases}:
            return field_name
    return None


def _parse_key_value_lines(text: str) -> tuple[dict[str, Any], dict[str, tuple[str, ...]], dict[str, tuple[int, ...]]]:
    values: dict[str, list[str]] = {}
    pages: dict[str, list[int]] = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = re.match(r"^\s*([^:=]{2,80})\s*[:=]\s*(.*?)\s*$", line)
        if not match:
            continue
        field_name = _canonical_field(match.group(1))
        value = match.group(2).strip()
        if field_name is None or not value:
            continue
        values.setdefault(field_name, []).append(value)
        pages.setdefault(field_name, []).append(max(1, line_number // 60 + 1))
    fields: dict[str, Any] = {key: items[0] for key, items in values.items()}
    conflicts = {
        key: tuple(dict.fromkeys(items))
        for key, items in values.items()
        if len(dict.fromkeys(items)) > 1
    }
    return fields, conflicts, {key: tuple(dict.fromkeys(items)) for key, items in pages.items()}


def _certificate_type(fields: Mapping[str, Any], document_type: DocumentType) -> DocumentType:
    standard = str(fields.get("certificate_standard", "")).replace(" ", "").upper()
    if document_type is DocumentType.CERTIFICATE and standard == "ISO13485":
        return DocumentType.ISO_13485
    return document_type


def _sds_review_reasons(fields: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for key in ("product_name", "transport_hazard_class", "un_number", "packing_group"):
        if not fields.get(key):
            reasons.append(f"MISSING_{key.upper()}")
    return reasons


def extract_document(
    artifact: DocumentArtifact,
    *,
    adapter: Callable[[DocumentArtifact], str | Mapping[str, Any]] | None = None,
) -> ExtractionResult:
    """Extract explicit fields while retaining raw text and provenance.

    ``adapter`` is an optional seam for Docling or PaddleOCR. It is injected by
    callers, so this module never installs or executes an external parser.
    """

    if not isinstance(artifact, DocumentArtifact):
        raise TypeError("artifact must be a DocumentArtifact")
    text = _text_content(artifact.content)
    method = "deterministic_key_value"
    fields: dict[str, Any]
    conflicts: dict[str, tuple[str, ...]]
    pages: dict[str, tuple[int, ...]]
    if adapter is not None:
        adapted = adapter(artifact)
        method = getattr(adapter, "__name__", "optional_adapter")
        if isinstance(adapted, Mapping):
            fields = {
                str(key): value
                for key, value in adapted.items()
                if value is not None and value != ""
            }
            conflicts = {}
            pages = {key: (1,) for key in fields}
        elif isinstance(adapted, str):
            text = adapted
            fields, conflicts, pages = _parse_key_value_lines(text)
        else:
            raise TypeError("adapter must return text or a mapping")
    else:
        fields, conflicts, pages = _parse_key_value_lines(text)

    document_type = artifact.document_type or _infer_document_type(artifact.filename, text)
    document_type = _certificate_type(fields, document_type)
    warnings: list[str] = []
    review_reasons: list[str] = []
    if document_type is DocumentType.UNKNOWN_DOCUMENT:
        review_reasons.append("UNKNOWN_DOCUMENT_TYPE")
    if conflicts:
        review_reasons.append("CONFLICTING_FIELDS_PRESERVED")
        warnings.append("Conflicting extracted values are preserved and require review.")
    if document_type is DocumentType.SDS_MSDS:
        sds_reasons = _sds_review_reasons(fields)
        if sds_reasons:
            review_reasons.extend(sds_reasons)
            warnings.append(
                "SDS transport data is incomplete; dangerous-goods status remains UNKNOWN and no safe-status conclusion is inferred."
            )
    provenance = {
        "source": artifact.source_url or f"artifact:{artifact.filename}",
        "pages": {key: list(value) for key, value in pages.items()},
        "method": method,
        "content_sha256": _artifact_content_sha256(artifact),
    }
    if artifact.metadata:
        for key in ("source_file_type", "reader_method", "reader_version", "unsupported_state"):
            value = artifact.metadata.get(key)
            if value:
                provenance[key] = value
    extraction = StructuredExtraction(
        document_type=document_type,
        fields=fields,
        raw_text=text,
        source_pages=pages,
        method=method,
        conflicts=conflicts,
        warnings=tuple(dict.fromkeys(warnings)),
        provenance=provenance,
    )
    status = ExtractionStatus.REVIEW_REQUIRED if review_reasons else ExtractionStatus.PASS
    return ExtractionResult(
        artifact=artifact,
        extraction=extraction,
        status=status,
        review_reasons=tuple(dict.fromkeys(review_reasons)),
    )


def _source_for(result: ExtractionResult) -> SourceRecord | None:
    if not result.artifact.source_url:
        return None
    return SourceRecord(
        jurisdiction="VN",
        authority="Customer-provided document",
        source_url=result.artifact.source_url,
        evidence_status=EvidenceStatus.NOT_RETRIEVED,
        authority_level=SourceAuthority.CUSTOMER_PROVIDED,
        source_reference=result.artifact.filename,
    )


def to_trade_document_evidence(result: ExtractionResult) -> DocumentEvidence:
    """Adapt extraction into the existing LOG-TRADE01 DocumentEvidence type."""

    if not isinstance(result, ExtractionResult):
        raise TypeError("result must be an ExtractionResult")
    document_type = result.extraction.document_type
    fields = result.extraction.fields
    valid = result.status is not ExtractionStatus.REJECTED and bool(result.extraction.raw_text.strip())
    relevant = None if document_type is DocumentType.UNKNOWN_DOCUMENT else True
    sufficient = valid and not result.extraction.conflicts and not result.review_reasons
    interpretation: str | None = None
    if document_type is DocumentType.SDS_MSDS:
        sds_reasons = _sds_review_reasons(fields)
        sufficient = valid and not sds_reasons and not result.extraction.conflicts
        if sds_reasons:
            interpretation = (
                "SDS evidence is incomplete for transport review; dangerous-goods status remains UNKNOWN."
            )
    elif document_type is DocumentType.ISO_13485:
        interpretation = (
            "ISO 13485 may evidence a manufacturer quality-management system; "
            "it does not establish product identity, product registration, or import approval."
        )
        sufficient = False
    elif document_type is DocumentType.UNKNOWN_DOCUMENT:
        sufficient = False
    return assess_document(
        DocumentEvidence(
            document_type=document_type,
            present=bool(result.extraction.raw_text.strip()),
            valid=valid,
            relevant=relevant,
            sufficient=sufficient,
            interpretation=interpretation,
            source=_source_for(result),
        )
    )


def to_product_identity(result: ExtractionResult) -> ProductIdentity:
    """Adapt only explicit extracted fields into canonical ProductIdentity."""

    if not isinstance(result, ExtractionResult):
        raise TypeError("result must be an ExtractionResult")
    fields = dict(result.extraction.fields)
    if result.extraction.document_type is DocumentType.SDS_MSDS:
        fields.setdefault("category", "chemical")
        if fields.get("un_number"):
            fields.setdefault("dangerous_goods_status", "UNKNOWN")
    fields.pop("transport_hazard_class", None)
    fields.pop("packing_group", None)
    fields.pop("transport_proper_shipping_name", None)
    fields.pop("certificate_standard", None)
    fields.pop("certificate_number", None)
    fields.pop("certificate_scope", None)
    fields.pop("expiry_date", None)
    return normalize_product_identity(fields)


def build_trade_evidence_plan(result: ExtractionResult) -> EvidenceRequestPlan:
    """Feed extracted evidence through the canonical conditional request plan."""

    document = to_trade_document_evidence(result)
    return build_evidence_request_plan(
        to_product_identity(result),
        supplied_documents=(document,),
    )


def adapter_runtime_status() -> dict[str, bool]:
    """Report adapter structure separately from unproven optional runtimes."""

    return {
        "docling_adapter_implemented": DOCLING_ADAPTER_IMPLEMENTED,
        "docling_runtime_proven": DOCLING_RUNTIME_PROVEN,
        "paddleocr_adapter_implemented": PADDLEOCR_ADAPTER_IMPLEMENTED,
        "paddleocr_runtime_proven": PADDLEOCR_RUNTIME_PROVEN,
    }


__all__ = [
    "DOCLING_ADAPTER_IMPLEMENTED",
    "DOCLING_RUNTIME_PROVEN",
    "DocumentArtifact",
    "DocumentSecurityError",
    "ExtractionResult",
    "ExtractionStatus",
    "MAX_PAGE_COUNT",
    "MAX_PAYLOAD_BYTES",
    "MAX_TEXT_CHARS",
    "PADDLEOCR_ADAPTER_IMPLEMENTED",
    "PADDLEOCR_RUNTIME_PROVEN",
    "StructuredExtraction",
    "adapter_runtime_status",
    "build_trade_evidence_plan",
    "extract_document",
    "sanitize_filename",
    "to_product_identity",
    "to_trade_document_evidence",
]
