"""Trade document cross-check canary (TT-DOC-CANARY-01) — Đối chiếu chứng từ.

Deterministic, fully offline comparison of extracted trade documents
(Commercial Invoice, Packing List, Bill of Lading) for Issue #126.

This module is the canary layer on top of the existing LOG-DOC01 extraction
seam. It deliberately reuses:

- ``core.document_extraction.DocumentArtifact`` (bounded untrusted input,
  content SHA-256 provenance),
- ``core.document_extraction.extract_document(...)`` with the existing
  adapter injection seam (``trade_label_adapter``),
- the existing ``core.trade_compliance.DocumentType`` contract.

It never classifies HS codes, never picks a winner for a conflict, never
writes to a database, never touches the network, and never calls a provider.
Missing or ambiguous fields are expressed as ``None`` with an explicit
status (MISSING / UNKNOWN), never as ``""`` or ``0``.

Every extracted raw value must exist verbatim in its source document text
(no-fabrication contract); a proposed value that cannot be grounded is
marked UNREADABLE and yields UNKNOWN at fact level.

Documents are untrusted DATA, not instructions.
"""

from __future__ import annotations

import re
import string
import unicodedata
from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Callable, Mapping, Sequence

from core.document_extraction import (
    DocumentArtifact,
    DocumentSecurityError,
    ExtractionResult,
    extract_document,
)
from core.trade_compliance import DocumentType

ENGINE_ID = "trade_document_crosscheck"
ENGINE_VERSION = "1"
CLASSIFICATION_METHOD = "trade_title_rules_v1"
ADAPTER_METHOD = "trade_label_adapter"
MAX_DOCUMENTS = 32
MAX_WITHIN_DOCUMENT_VALUES = 8

#: Marker that every synthetic fixture page must visibly carry.
SYNTHETIC_PAGE_MARKER = "SYNTHETIC — NOT A REAL SHIPMENT"


class ObservationStatus(str, Enum):
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    UNREADABLE = "UNREADABLE"


class FactStatus(str, Enum):
    """Deterministic status precedence: first matching rule wins.

    1. CONFLICT  2. UNKNOWN  3. SAME  4. MISSING  5. SINGLE_SOURCE
    """

    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"
    SAME = "SAME"
    MISSING = "MISSING"
    SINGLE_SOURCE = "SINGLE_SOURCE"


# ---------------------------------------------------------------------------
# Deterministic normalization (only what the frozen canary needs)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Normalized:
    """Result of normalizing one raw value.

    ``value`` keeps the exact parsed semantics (Decimal / int / date / str).
    ``key`` is the canonical comparison string, or ``None`` when the value is
    ambiguous/unreadable and must not be compared. ``reason`` explains a
    ``None`` key.
    """

    value: Any = None
    unit: str | None = None
    key: str | None = None
    reason: str | None = None


def _ascii_upper(text: str) -> str:
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
        .upper()
    )


def normalize_name(raw: str) -> Normalized:
    """Unicode/case/punctuation normalization plus the explicit deterministic
    rule ``COMPANY LIMITED`` <=> ``CO., LTD`` for comparison only. The raw
    source string is preserved by the caller (observation layer)."""

    text = _ascii_upper(raw)
    text = re.sub(r"[^A-Z0-9]+", " ", text).strip()
    text = re.sub(r"\bCOMPANY LIMITED\b", "CO LTD", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return Normalized(reason="NAME_EMPTY_AFTER_NORMALIZATION")
    return Normalized(value=text, key=text)


def normalize_port(raw: str) -> Normalized:
    """Comparison-only port form: case-folded ASCII letters/digits only, so
    ``Hai Phong, Viet Nam`` and ``HAIPHONG, VIETNAM`` compare equal."""

    text = re.sub(r"[^A-Z0-9]+", "", _ascii_upper(raw))
    if not text:
        return Normalized(reason="PORT_EMPTY_AFTER_NORMALIZATION")
    return Normalized(value=text, key=text)


def normalize_code(raw: str) -> Normalized:
    """Codes (invoice number, voyage, seal, B/L number, HS if ever present):
    uppercase, whitespace removed, hyphens preserved, leading zeros kept."""

    text = re.sub(r"\s+", "", _ascii_upper(raw))
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9-]*", text):
        return Normalized(reason="CODE_FORMAT_UNRECOGNIZED")
    return Normalized(value=text, key=text)


_ISO_LETTER_VALUES: dict[str, int] = {}
_value = 10
for _letter in string.ascii_uppercase:
    while _value % 11 == 0:
        _value += 1
    _ISO_LETTER_VALUES[_letter] = _value
    _value += 1

_CONTAINER_RE = re.compile(r"^[A-Z]{4}\d{7}$")


def iso6346_check_digit(container: str) -> int | None:
    """Compute the ISO 6346 check digit for an 11-character container code."""

    if not _CONTAINER_RE.fullmatch(container):
        return None
    total = 0
    for index, char in enumerate(container[:10]):
        if char.isalpha():
            number: int | None = _ISO_LETTER_VALUES.get(char)
        else:
            number = int(char)
        if number is None:
            return None
        total += number * (2**index)
    return total % 11 % 10


def normalize_container(raw: str) -> Normalized:
    """Whitespace/hyphen normalization + ISO 6346 check-digit validation.

    An invalid container number is NEVER auto-corrected; it becomes a ``None``
    key (fact-level UNKNOWN) with an explicit reason.
    """

    text = re.sub(r"[\s\-]+", "", _ascii_upper(raw))
    if len(text) != 11 or not _CONTAINER_RE.fullmatch(text):
        return Normalized(reason="CONTAINER_FORMAT_INVALID")
    expected = iso6346_check_digit(text)
    actual = int(text[10])
    if expected is None or expected != actual:
        return Normalized(reason="ISO_6346_CHECK_DIGIT_INVALID")
    return Normalized(value=text, key=text)


_PACKAGE_FAMILY: dict[str, str] = {
    "CTN": "CARTON",
    "CTNS": "CARTON",
    "CARTON": "CARTON",
    "CARTONS": "CARTON",
}

_NUMBER_RE = r"\d[\d,]*(?:\.\d+)?"


def _parse_decimal(text: str) -> Decimal | None:
    try:
        return Decimal(text.replace(",", "").replace(" ", ""))
    except (InvalidOperation, ValueError):
        return None


def decimal_key(value: Decimal) -> str:
    """Canonical, deterministic decimal string (exact, no float, no
    tolerance): trailing zeros stripped so 12500.000 compares as 12500."""

    if value == 0:
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def normalize_package_count(raw: str) -> Normalized:
    match = re.fullmatch(rf"\s*(?P<count>{_NUMBER_RE})\s*(?P<unit>[A-Za-z]+)\.?\s*", raw)
    if not match:
        return Normalized(reason="PACKAGE_FORMAT_UNRECOGNIZED")
    count = _parse_decimal(match.group("count"))
    if count is None or count != count.to_integral_value():
        return Normalized(reason="PACKAGE_COUNT_NOT_INTEGER")
    count_int = int(count)
    unit = match.group("unit").upper()
    family = _PACKAGE_FAMILY.get(unit, unit)
    key = f"{count_int} {family}"
    return Normalized(value=count_int, unit=family, key=key)


def normalize_weight(raw: str) -> Normalized:
    match = re.fullmatch(
        rf"\s*(?P<amount>{_NUMBER_RE})\s*(?P<unit>KGS?|KILOGRAMS?)\.?\s*",
        raw,
        re.IGNORECASE,
    )
    if not match:
        return Normalized(reason="WEIGHT_FORMAT_UNRECOGNIZED")
    value = _parse_decimal(match.group("amount"))
    if value is None:
        return Normalized(reason="WEIGHT_NOT_DECIMAL")
    return Normalized(value=value, unit="kg", key=decimal_key(value))


def normalize_cbm(raw: str) -> Normalized:
    match = re.fullmatch(
        rf"\s*(?P<amount>{_NUMBER_RE})\s*(?P<unit>CBM|M3|M³)\.?\s*",
        raw,
        re.IGNORECASE,
    )
    if not match:
        return Normalized(reason="CBM_FORMAT_UNRECOGNIZED")
    value = _parse_decimal(match.group("amount"))
    if value is None:
        return Normalized(reason="CBM_NOT_DECIMAL")
    return Normalized(value=value, unit="m3", key=decimal_key(value))


def normalize_money(raw: str) -> Normalized:
    """Exact Decimal money; raw string preserved by the observation layer.
    No FX conversion, no floating point."""

    match = re.fullmatch(
        rf"\s*(?:(?P<pre>[A-Z]{{3}})\s*)?(?P<amount>{_NUMBER_RE})\s*(?:(?P<post>[A-Z]{{3}})\s*)?",
        _ascii_upper(raw),
    )
    if not match:
        return Normalized(reason="MONEY_FORMAT_UNRECOGNIZED")
    currency = match.group("pre") or match.group("post")
    if currency is None:
        return Normalized(reason="CURRENCY_MISSING")
    value = _parse_decimal(match.group("amount"))
    if value is None:
        return Normalized(reason="MONEY_NOT_DECIMAL")
    key = f"{currency} {decimal_key(value)}"
    return Normalized(value=value, unit=currency, key=key)


def normalize_date(raw: str) -> Normalized:
    """ISO dates parse; ambiguous DD/MM vs MM/DD yields ``None`` (fact-level
    UNKNOWN). No locale guessing is ever applied."""

    text = raw.strip()
    iso = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if iso:
        try:
            value = date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
        except ValueError:
            return Normalized(reason="DATE_INVALID")
        return Normalized(value=value, key=value.isoformat())
    slash = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if slash:
        first, second, year = int(slash.group(1)), int(slash.group(2)), int(slash.group(3))
        if first > 12 and second > 12:
            return Normalized(reason="DATE_INVALID")
        if first > 12:  # day-first is the only possible reading
            try:
                value = date(year, second, first)
            except ValueError:
                return Normalized(reason="DATE_INVALID")
            return Normalized(value=value, key=value.isoformat())
        if second > 12:  # month-first is the only possible reading
            try:
                value = date(year, first, second)
            except ValueError:
                return Normalized(reason="DATE_INVALID")
            return Normalized(value=value, key=value.isoformat())
        return Normalized(reason="AMBIGUOUS_DAY_MONTH_ORDER")
    return Normalized(reason="DATE_FORMAT_UNRECOGNIZED")


def normalize_text(raw: str) -> Normalized:
    text = re.sub(r"\s+", " ", _ascii_upper(raw)).strip()
    if not text:
        return Normalized(reason="TEXT_EMPTY_AFTER_NORMALIZATION")
    return Normalized(value=text, key=text)


def normalize_origin(raw: str) -> Normalized:
    text = re.sub(r"\s+", " ", _ascii_upper(raw)).strip()
    text = re.sub(r"^MADE IN\s+", "", text).strip()
    if not text:
        return Normalized(reason="ORIGIN_EMPTY_AFTER_NORMALIZATION")
    return Normalized(value=text, key=text)


# ---------------------------------------------------------------------------
# Label -> field mapping (adapter seam used by extract_document)
# ---------------------------------------------------------------------------

_LABEL_FIELDS: dict[str, str] = {
    "seller": "shipper",
    "shipper": "shipper",
    "buyer": "consignee",
    "consignee": "consignee",
    "invoice no": "invoice_number",
    "invoice number": "invoice_number",
    "invoice reference": "invoice_number",
    "invoice date": "invoice_date",
    "date": "invoice_date",
    "incoterm": "incoterm",
    "pod": "pod",
    "port of discharge": "pod",
    "discharge port": "pod",
    "pol": "pol",
    "port of loading": "pol",
    "loading port": "pol",
    "packages": "package_count",
    "total packages": "package_count",
    "gross weight": "gross_weight",
    "net weight": "net_weight",
    "cbm": "cbm",
    "container": "container",
    "container no": "container",
    "container number": "container",
    "seal": "seal",
    "seal no": "seal",
    "vessel": "vessel",
    "voyage": "voyage",
    "voyage no": "voyage",
    "origin": "origin",
    "country of origin": "origin",
    "place of origin": "origin",
    "total": "total",
    "total amount": "total",
    "total value": "total",
    "bl number": "bl_number",
    "b/l number": "bl_number",
    "hs code": "hs_code",
    "hs": "hs_code",
}

_LABELLED_LINE_RE = re.compile(r"^\s*([^:=]{2,80}?)\s*[:=]\s*(\S.*?)\s*$")
_PAGE_MARKER_RE = re.compile(r"^\s*\[\s*PAGE\s+(\d+)\s*\]\s*$", re.IGNORECASE)


def _as_text(content: str | bytes) -> str:
    if isinstance(content, str):
        return content
    return content.decode("utf-8", errors="replace")


def _iter_page_lines(text: str):
    """Yield (page_or_None, global_line_number, line) for page-tagged text."""

    page: int | None = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        marker = _PAGE_MARKER_RE.match(line)
        if marker:
            page = int(marker.group(1))
            continue
        yield page, line_number, line


def trade_label_adapter(artifact: DocumentArtifact) -> dict[str, Any]:
    """Adapter for ``extract_document`` mapping trade labels to canonical
    field keys. Repeated labels with identical values collapse; genuinely
    different values are preserved as a list so nothing is silently dropped.
    """

    values: dict[str, list[str]] = {}
    for _, _, line in _iter_page_lines(_as_text(artifact.content)):
        match = _LABELLED_LINE_RE.match(line)
        if not match:
            continue
        field_key = _LABEL_FIELDS.get(match.group(1).strip().lower())
        value = match.group(2).strip()
        if field_key is None or not value:
            continue
        bucket = values.setdefault(field_key, [])
        if value not in bucket:
            bucket.append(value)
    return {key: values[key] for key in sorted(values)}


# ---------------------------------------------------------------------------
# Document classification (deterministic title rules; existing enum only)
# ---------------------------------------------------------------------------

_TRADE_TITLE_RULES: tuple[tuple[str, DocumentType], ...] = (
    ("COMMERCIAL INVOICE", DocumentType.INVOICE),
    ("PACKING LIST", DocumentType.PACKING_LIST),
    ("BILL OF LADING", DocumentType.BILL_OF_LADING),
)


def classify_trade_document(text: str) -> DocumentType:
    for _, _, line in _iter_page_lines(text):
        compact = re.sub(r"\s+", " ", _ascii_upper(line)).strip()
        for marker, document_type in _TRADE_TITLE_RULES:
            if marker in compact:
                return document_type
    return DocumentType.UNKNOWN_DOCUMENT


# ---------------------------------------------------------------------------
# Field expectation spec (drives observations; fixed deterministic order)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FieldSpec:
    field_key: str
    expected_on: frozenset[DocumentType]
    normalizer: Callable[[str], Normalized]
    normalization: str
    handoff: Mapping[str, str] | None = None


_HS_LOOKUP_HANDOFF: Mapping[str, str] = {
    "action": "HS_CODE_LOOKUP_REQUIRED",
    "target": "core.trade_compliance HS candidate workflow",
    "policy": "No HS code is generated or guessed by this engine; "
    "explicit lookup handoff only.",
}

FIELD_SPECS: tuple[FieldSpec, ...] = (
    FieldSpec("invoice_number", frozenset({DocumentType.INVOICE, DocumentType.PACKING_LIST}), normalize_code, "code_v1"),
    FieldSpec("invoice_date", frozenset({DocumentType.INVOICE, DocumentType.PACKING_LIST}), normalize_date, "date_v1"),
    FieldSpec("shipper", frozenset({DocumentType.INVOICE, DocumentType.BILL_OF_LADING}), normalize_name, "name_v1"),
    FieldSpec("consignee", frozenset({DocumentType.INVOICE, DocumentType.BILL_OF_LADING}), normalize_name, "name_v1"),
    FieldSpec("pod", frozenset({DocumentType.INVOICE, DocumentType.BILL_OF_LADING}), normalize_port, "port_v1"),
    FieldSpec("pol", frozenset({DocumentType.BILL_OF_LADING}), normalize_port, "port_v1"),
    FieldSpec("package_count", frozenset({DocumentType.INVOICE, DocumentType.PACKING_LIST, DocumentType.BILL_OF_LADING}), normalize_package_count, "package_v1"),
    FieldSpec("gross_weight", frozenset({DocumentType.INVOICE, DocumentType.PACKING_LIST, DocumentType.BILL_OF_LADING}), normalize_weight, "weight_v1"),
    FieldSpec("net_weight", frozenset({DocumentType.PACKING_LIST}), normalize_weight, "weight_v1"),
    FieldSpec("cbm", frozenset({DocumentType.PACKING_LIST, DocumentType.BILL_OF_LADING}), normalize_cbm, "cbm_v1"),
    FieldSpec("container", frozenset({DocumentType.PACKING_LIST, DocumentType.BILL_OF_LADING}), normalize_container, "container_v1"),
    FieldSpec("seal", frozenset({DocumentType.BILL_OF_LADING}), normalize_code, "code_v1"),
    FieldSpec("vessel", frozenset({DocumentType.BILL_OF_LADING}), normalize_name, "name_v1"),
    FieldSpec("voyage", frozenset({DocumentType.BILL_OF_LADING}), normalize_code, "code_v1"),
    FieldSpec("incoterm", frozenset({DocumentType.INVOICE}), normalize_text, "text_v1"),
    FieldSpec("total", frozenset({DocumentType.INVOICE}), normalize_money, "money_v1"),
    FieldSpec("origin", frozenset({DocumentType.INVOICE}), normalize_origin, "origin_v1"),
    FieldSpec("bl_number", frozenset({DocumentType.BILL_OF_LADING}), normalize_code, "code_v1"),
    FieldSpec("hs_code", frozenset({DocumentType.INVOICE}), normalize_code, "code_v1", _HS_LOOKUP_HANDOFF),
)

_FIELD_ORDER = {spec.field_key: index for index, spec in enumerate(FIELD_SPECS)}

#: Canonical business ordering of document types for deterministic output
#: (INVOICE -> PACKING_LIST -> BILL_OF_LADING); unknown types sort last.
_DOCUMENT_TYPE_ORDER: dict[DocumentType, int] = {
    DocumentType.INVOICE: 0,
    DocumentType.PACKING_LIST: 1,
    DocumentType.BILL_OF_LADING: 2,
}


def _observation_sort_key(observation: "TradeObservation") -> tuple[int, str, str]:
    return (
        _DOCUMENT_TYPE_ORDER.get(observation.document_type, 99),
        observation.document_label,
        observation.raw_value or "",
    )


# ---------------------------------------------------------------------------
# Observation / Fact model (issue #126 contract)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TradeObservation:
    field_key: str
    document_label: str
    content_sha256: str
    document_type: DocumentType
    status: ObservationStatus
    raw_value: str | None
    source_location: tuple[int, int] | None  # (page, global line) only when genuinely known
    normalized_value: Any
    normalized_key: str | None
    unit: str | None
    reason: str
    extraction_method: str
    normalization: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_key": self.field_key,
            "document_label": self.document_label,
            "content_sha256": self.content_sha256,
            "document_type": self.document_type.value,
            "status": self.status.value,
            "raw_value": self.raw_value,
            "source_location": list(self.source_location) if self.source_location else None,
            "normalized_value": _json_safe(self.normalized_value),
            "normalized_key": self.normalized_key,
            "unit": self.unit,
            "reason": self.reason,
            "extraction_method": self.extraction_method,
            "normalization": self.normalization,
        }


@dataclass(frozen=True)
class TradeFact:
    field_key: str
    status: FactStatus
    observations: tuple[TradeObservation, ...]
    observed_values: tuple[str, ...]
    handoff: Mapping[str, str] | None
    operator_decision: str = "NONE"  # engine never sets an operator decision
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_key": self.field_key,
            "status": self.status.value,
            "observed_values": list(self.observed_values),
            "handoff": dict(self.handoff) if self.handoff else None,
            "operator_decision": self.operator_decision,
            "reason": self.reason,
            "observations": [observation.to_dict() for observation in self.observations],
        }


@dataclass(frozen=True)
class CrossCheckDocument:
    document_label: str
    content_sha256: str
    document_type: DocumentType
    classification_method: str
    extraction_status: str
    extraction_review_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_label": self.document_label,
            "content_sha256": self.content_sha256,
            "document_type": self.document_type.value,
            "classification_method": self.classification_method,
            "extraction_status": self.extraction_status,
            "extraction_review_reasons": list(self.extraction_review_reasons),
        }


@dataclass(frozen=True)
class TradeCrossCheckResult:
    documents: tuple[CrossCheckDocument, ...]
    facts: tuple[TradeFact, ...]

    def status_counts(self) -> dict[str, int]:
        counts = {status.value: 0 for status in FactStatus}
        for fact in self.facts:
            counts[fact.status.value] += 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_id": ENGINE_ID,
            "engine_version": ENGINE_VERSION,
            "documents": [document.to_dict() for document in self.documents],
            "facts": [fact.to_dict() for fact in self.facts],
            "status_counts": self.status_counts(),
        }


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    return value


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def _locate(lines: Sequence[tuple[int | None, int, str]], raw_value: str) -> tuple[int, int] | None:
    """Real source location only when the exact raw value occurs on exactly
    one line of the document text; otherwise honestly unknown."""

    occurrences = [(page, line_number) for page, line_number, line in lines if raw_value in line]
    if len(occurrences) == 1:
        return occurrences[0]
    return None


def _decide_status(observations: Sequence[TradeObservation]) -> tuple[FactStatus, str]:
    """Deterministic precedence: CONFLICT > UNKNOWN > SAME > MISSING >
    SINGLE_SOURCE. The engine never selects a winner."""

    grounded = [
        observation
        for observation in observations
        if observation.status is ObservationStatus.FOUND and observation.normalized_key is not None
    ]
    unresolved = [
        observation
        for observation in observations
        if observation.status is ObservationStatus.UNREADABLE
        or (observation.status is ObservationStatus.FOUND and observation.normalized_key is None)
    ]
    keys: list[str] = []
    for observation in grounded:
        if observation.normalized_key not in keys:
            keys.append(observation.normalized_key)
    if len(keys) >= 2:
        return FactStatus.CONFLICT, "FOUND_VALUES_DIFFER_NO_WINNER_SELECTED"
    if unresolved:
        return FactStatus.UNKNOWN, "AMBIGUOUS_OR_UNGROUNDED_VALUE_PREVENTS_SAME"
    independent_types = {observation.document_type for observation in grounded}
    if len(independent_types) >= 2:
        return FactStatus.SAME, "INDEPENDENT_SOURCES_NORMALIZE_EQUAL"
    if grounded:
        return FactStatus.SINGLE_SOURCE, "SINGLE_INDEPENDENT_SOURCE"
    return FactStatus.MISSING, "NO_VALUE_FOUND_IN_EXPECTED_DOCUMENTS"


def _observations_for_field(
    spec: FieldSpec,
    artifact: DocumentArtifact,
    extraction: ExtractionResult,
    lines: Sequence[tuple[int | None, int, str]],
) -> list[TradeObservation]:
    document_type: DocumentType = extraction.extraction.document_type
    base = {
        "field_key": spec.field_key,
        "document_label": artifact.filename,
        "content_sha256": artifact.content_sha256,
        "extraction_method": extraction.extraction.method,
        "normalization": spec.normalization,
    }
    values = extraction.extraction.fields.get(spec.field_key)
    if values is None:
        return [
            TradeObservation(
                document_type=document_type,
                status=ObservationStatus.NOT_FOUND,
                raw_value=None,
                source_location=None,
                normalized_value=None,
                normalized_key=None,
                unit=None,
                reason="EXPECTED_FIELD_NOT_PRESENT",
                **base,
            )
        ]
    raw_values = values if isinstance(values, list) else [values]
    raw_values = [str(value) for value in raw_values]
    if len(raw_values) > MAX_WITHIN_DOCUMENT_VALUES:
        raw_values = raw_values[:MAX_WITHIN_DOCUMENT_VALUES]
    text = _as_text(artifact.content)
    observations: list[TradeObservation] = []
    for raw_value in raw_values:
        if raw_value not in text:
            # No-fabrication contract: an ungrounded adapter proposal is
            # marked UNREADABLE, never surfaced as extracted data.
            observations.append(
                TradeObservation(
                    document_type=document_type,
                    status=ObservationStatus.UNREADABLE,
                    raw_value=raw_value,
                    source_location=None,
                    normalized_value=None,
                    normalized_key=None,
                    unit=None,
                    reason="RAW_VALUE_NOT_GROUNDED_IN_SOURCE",
                    **base,
                )
            )
            continue
        normalized = spec.normalizer(raw_value)
        observations.append(
            TradeObservation(
                document_type=document_type,
                status=ObservationStatus.FOUND,
                raw_value=raw_value,
                source_location=_locate(lines, raw_value),
                normalized_value=normalized.value,
                normalized_key=normalized.key,
                unit=normalized.unit,
                reason=normalized.reason or "LABELLED_LINE_MATCH",
                **base,
            )
        )
    return observations


def run_trade_document_crosscheck(
    artifacts: Sequence[DocumentArtifact],
    *,
    adapter: Callable[[DocumentArtifact], Mapping[str, Any]] | None = None,
) -> TradeCrossCheckResult:
    """Run the deterministic offline cross-check over bounded documents.

    ``adapter`` defaults to :func:`trade_label_adapter`; callers may inject a
    different adapter through the existing ``extract_document`` seam.
    """

    if not artifacts:
        raise ValueError("at least one document artifact is required")
    if len(artifacts) > MAX_DOCUMENTS:
        raise DocumentSecurityError("document count exceeds the bounded canary limit")

    summaries: list[CrossCheckDocument] = []
    observations: list[TradeObservation] = []
    seen_labels: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, DocumentArtifact):
            raise TypeError("each input must be a DocumentArtifact")
        if artifact.filename in seen_labels:
            raise ValueError("duplicate document label: " + artifact.filename)
        seen_labels.add(artifact.filename)
        if artifact.document_type is None:
            document_type = classify_trade_document(_as_text(artifact.content))
            classification_method = CLASSIFICATION_METHOD
            artifact = replace(artifact, document_type=document_type)
        else:
            document_type = artifact.document_type
            classification_method = "explicit_input"
        text = _as_text(artifact.content)
        lines = list(_iter_page_lines(text))
        extraction = extract_document(artifact, adapter=adapter or trade_label_adapter)
        summaries.append(
            CrossCheckDocument(
                document_label=artifact.filename,
                content_sha256=artifact.content_sha256,
                document_type=document_type,
                classification_method=classification_method,
                extraction_status=extraction.status.value,
                extraction_review_reasons=extraction.review_reasons,
            )
        )
        for spec in FIELD_SPECS:
            if document_type not in spec.expected_on:
                continue
            observations.extend(_observations_for_field(spec, artifact, extraction, lines))

    facts: list[TradeFact] = []
    for spec in FIELD_SPECS:
        field_observations = [
            observation
            for observation in observations
            if observation.field_key == spec.field_key
        ]
        if not field_observations:
            continue  # field not expected on any provided document type
        field_observations.sort(key=_observation_sort_key)
        status, reason = _decide_status(field_observations)
        observed_values: list[str] = []
        for observation in field_observations:
            if observation.status is ObservationStatus.FOUND and observation.normalized_key is not None:
                # Multiplicity is preserved: one entry per observing document,
                # so a CONFLICT shows every side (e.g. 120 / 120 / 118).
                observed_values.append(observation.normalized_key)
        facts.append(
            TradeFact(
                field_key=spec.field_key,
                status=status,
                observations=tuple(field_observations),
                observed_values=tuple(observed_values),
                handoff=dict(spec.handoff) if spec.handoff else None,
                reason=reason,
            )
        )

    summaries.sort(key=lambda summary: summary.document_label)
    return TradeCrossCheckResult(documents=tuple(summaries), facts=tuple(facts))


__all__ = [
    "ADAPTER_METHOD",
    "CLASSIFICATION_METHOD",
    "ENGINE_ID",
    "ENGINE_VERSION",
    "CrossCheckDocument",
    "FactStatus",
    "FieldSpec",
    "FIELD_SPECS",
    "ObservationStatus",
    "SYNTHETIC_PAGE_MARKER",
    "TradeCrossCheckResult",
    "TradeFact",
    "TradeObservation",
    "classify_trade_document",
    "decimal_key",
    "iso6346_check_digit",
    "normalize_cbm",
    "normalize_code",
    "normalize_container",
    "normalize_date",
    "normalize_money",
    "normalize_name",
    "normalize_origin",
    "normalize_package_count",
    "normalize_port",
    "normalize_text",
    "normalize_weight",
    "run_trade_document_crosscheck",
    "trade_label_adapter",
]
