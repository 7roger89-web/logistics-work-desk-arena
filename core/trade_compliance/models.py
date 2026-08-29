"""Typed contracts for the bounded LOG-TRADE01 compliance foundation.

The models deliberately distinguish normalized customer evidence from verified
legal conclusions.  They are standard-library dataclasses so the current
Streamlit application does not acquire a new runtime framework or persistence
dependency for this tranche.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from urllib.parse import urlparse

UNKNOWN = "UNKNOWN"


class FieldState(str, Enum):
    PROVIDED = "PROVIDED"
    REQUIRED_FOR_THIS_PRODUCT = "REQUIRED_FOR_THIS_PRODUCT"
    NOT_RELEVANT = "NOT_RELEVANT"
    UNKNOWN = UNKNOWN


class SourceAuthority(str, Enum):
    OFFICIAL = "OFFICIAL"
    OFFICIAL_DISCOVERY = "OFFICIAL_DISCOVERY"
    THIRD_PARTY_DISCOVERY = "THIRD_PARTY_DISCOVERY"
    CUSTOMER_PROVIDED = "CUSTOMER_PROVIDED"
    AI_INTERPRETATION = "AI_INTERPRETATION"


class EvidenceStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    NOT_RETRIEVED = "NOT_RETRIEVED"
    STALE = "STALE"
    CONFLICTING = "CONFLICTING"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


class DocumentType(str, Enum):
    PRODUCT_CATALOGUE = "PRODUCT_CATALOGUE"
    TECHNICAL_DATASHEET = "TECHNICAL_DATASHEET"
    PRODUCT_LABEL_OR_NAMEPLATE = "PRODUCT_LABEL_OR_NAMEPLATE"
    CERTIFICATE = "CERTIFICATE"
    UNKNOWN_DOCUMENT = "UNKNOWN_DOCUMENT"
    PRODUCT_PHOTOGRAPHS = "PRODUCT_PHOTOGRAPHS"
    NAMEPLATE_PHOTOGRAPH = "NAMEPLATE_PHOTOGRAPH"
    COMPOSITION = "COMPOSITION"
    SDS_MSDS = "SDS_MSDS"
    CAS_NUMBER = "CAS_NUMBER"
    UN_NUMBER = "UN_NUMBER"
    TEST_REPORT = "TEST_REPORT"
    CO = "CO"
    CQ = "CQ"
    CERTIFICATE_OF_ANALYSIS = "CERTIFICATE_OF_ANALYSIS"
    ISO_13485 = "ISO_13485"
    ISO_CERTIFICATE = "ISO_CERTIFICATE"
    CFS = "CFS"
    CE_DOCUMENTATION = "CE_DOCUMENTATION"
    MEDICAL_DEVICE_DOCUMENTATION = "MEDICAL_DEVICE_DOCUMENTATION"
    MANUFACTURER_DECLARATION = "MANUFACTURER_DECLARATION"
    PRODUCT_LABEL = "PRODUCT_LABEL"
    PACKING_INFORMATION = "PACKING_INFORMATION"
    INTENDED_USE_STATEMENT = "INTENDED_USE_STATEMENT"
    INVOICE = "INVOICE"
    PACKING_LIST = "PACKING_LIST"
    CERTIFICATE_OF_ORIGIN = "CERTIFICATE_OF_ORIGIN"
    DANGEROUS_GOODS_DECLARATION = "DANGEROUS_GOODS_DECLARATION"


class HSClassificationStatus(str, Enum):
    CANDIDATE_ONLY = "CANDIDATE_ONLY"
    NEEDS_MORE_PRODUCT_DATA = "NEEDS_MORE_PRODUCT_DATA"
    HUMAN_CLASSIFICATION_REQUIRED = "HUMAN_CLASSIFICATION_REQUIRED"
    SOURCE_VERIFICATION_REQUIRED = "SOURCE_VERIFICATION_REQUIRED"


class MeasureCategory(str, Enum):
    IMPORT_PROHIBITION = "IMPORT_PROHIBITION"
    IMPORT_RESTRICTION = "IMPORT_RESTRICTION"
    IMPORT_LICENCE = "IMPORT_LICENCE"
    SPECIALIZED_INSPECTION = "SPECIALIZED_INSPECTION"
    QUALITY_INSPECTION = "QUALITY_INSPECTION"
    FOOD_SAFETY_INSPECTION = "FOOD_SAFETY_INSPECTION"
    ANIMAL_QUARANTINE = "ANIMAL_QUARANTINE"
    PLANT_QUARANTINE = "PLANT_QUARANTINE"
    CHEMICAL_CONTROL = "CHEMICAL_CONTROL"
    DANGEROUS_GOODS = "DANGEROUS_GOODS"
    MEDICAL_DEVICE_CONTROL = "MEDICAL_DEVICE_CONTROL"
    ENERGY_EFFICIENCY = "ENERGY_EFFICIENCY"
    CONFORMITY_ASSESSMENT = "CONFORMITY_ASSESSMENT"
    LABELLING = "LABELLING"
    CERTIFICATE_REQUIREMENT = "CERTIFICATE_REQUIREMENT"
    OTHER_DOCUMENTARY_REQUIREMENT = "OTHER_DOCUMENTARY_REQUIREMENT"


class MeasureStatus(str, Enum):
    APPLIES = "APPLIES"
    DOES_NOT_APPLY = "DOES_NOT_APPLY"
    UNKNOWN = UNKNOWN
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class RegulatoryAssessmentStatus(str, Enum):
    VERIFIED_FROM_SOURCE = "VERIFIED_FROM_SOURCE"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    NEEDS_CUSTOMER_INPUT = "NEEDS_CUSTOMER_INPUT"
    NEEDS_HS_CONFIRMATION = "NEEDS_HS_CONFIRMATION"
    REGULATORY_REVIEW_REQUIRED = "REGULATORY_REVIEW_REQUIRED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    SOURCE_VERIFICATION_REQUIRED = "SOURCE_VERIFICATION_REQUIRED"


class TaxSnapshotStatus(str, Enum):
    VERIFIED_FROM_SOURCE = "VERIFIED_FROM_SOURCE"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    SOURCE_VERIFICATION_REQUIRED = "SOURCE_VERIFICATION_REQUIRED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    INCOMPLETE_INPUT = "INCOMPLETE_INPUT"


class PreferenceEligibility(str, Enum):
    UNKNOWN = UNKNOWN
    POTENTIALLY_AVAILABLE = "POTENTIALLY_AVAILABLE"
    VERIFIED_ELIGIBLE = "VERIFIED_ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"


class TaxCalculationStatus(str, Enum):
    CALCULATED = "CALCULATED"
    INCOMPLETE = "INCOMPLETE"


def _serialise(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value):
        return {
            item.name: _serialise(getattr(value, item.name))
            for item in fields(value)
        }
    if isinstance(value, dict):
        return {str(key): _serialise(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_serialise(item) for item in value]
    return value


def _normalise_tuple(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (tuple, list, set, frozenset)):
        return tuple(value)
    return (value,)


def _date_value(value: str | date | datetime | None) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _parse_temporal_value(value: str, *, allow_datetime: bool) -> date | datetime:
    text = str(value).strip()
    try:
        if allow_datetime and "T" in text:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise ValueError(f"invalid source date/time: {value}") from exc


@dataclass(frozen=True)
class SourceRecord:
    jurisdiction: str
    authority: str
    source_url: str
    retrieved_at: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    product_hs_scope: tuple[str, ...] = ()
    scope_description: str | None = None
    conclusion: Any = None
    confidence: Decimal | None = None
    evidence_status: EvidenceStatus = EvidenceStatus.NOT_RETRIEVED
    authority_level: SourceAuthority = SourceAuthority.OFFICIAL
    source_reference: str | None = None

    def __post_init__(self) -> None:
        if not str(self.jurisdiction).strip():
            raise ValueError("jurisdiction is required")
        if not str(self.authority).strip():
            raise ValueError("authority is required")
        if not str(self.source_url).strip():
            raise ValueError("source_url is required")
        parsed_url = urlparse(str(self.source_url).strip())
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            raise ValueError("source_url must use HTTPS")
        if not isinstance(self.evidence_status, EvidenceStatus):
            object.__setattr__(self, "evidence_status", EvidenceStatus(str(self.evidence_status)))
        if not isinstance(self.authority_level, SourceAuthority):
            object.__setattr__(self, "authority_level", SourceAuthority(str(self.authority_level)))
        object.__setattr__(
            self,
            "product_hs_scope",
            tuple(str(item).strip() for item in _normalise_tuple(self.product_hs_scope) if str(item).strip()),
        )
        for temporal_name, allow_datetime in (("retrieved_at", True), ("effective_from", False), ("effective_to", False)):
            temporal_value = getattr(self, temporal_name)
            if temporal_value:
                _parse_temporal_value(str(temporal_value), allow_datetime=allow_datetime)
        if self.confidence is not None:
            confidence = Decimal(str(self.confidence))
            if not confidence.is_finite() or not Decimal("0") <= confidence <= Decimal("1"):
                raise ValueError("confidence must be between 0 and 1")
            object.__setattr__(self, "confidence", confidence)
        if self.evidence_status in {
            EvidenceStatus.VERIFIED,
            EvidenceStatus.PARTIALLY_VERIFIED,
            EvidenceStatus.STALE,
            EvidenceStatus.CONFLICTING,
        } and not self.retrieved_at:
            raise ValueError("retrieved_at is required for retrieved source evidence")
        if self.evidence_status in {
            EvidenceStatus.VERIFIED,
            EvidenceStatus.PARTIALLY_VERIFIED,
            EvidenceStatus.STALE,
            EvidenceStatus.CONFLICTING,
        } and self.conclusion is not None and self.confidence is None:
            raise ValueError("confidence is required for a retrieved source conclusion")

    def covers_date(self, assessment_date: str | date | datetime) -> bool:
        point = _date_value(assessment_date)
        if point is None:
            return False
        start = _date_value(self.effective_from)
        end = _date_value(self.effective_to)
        return (start is None or start <= point) and (end is None or point <= end)

    def to_dict(self) -> dict[str, Any]:
        return _serialise(self)


IDENTITY_FIELD_NAMES = (
    "commercial_name",
    "product_name",
    "model",
    "manufacturer",
    "brand",
    "intended_use",
    "function",
    "material",
    "composition",
    "operating_principle",
    "technical_specifications",
    "voltage",
    "power",
    "capacity",
    "dimensions",
    "chemical_identifiers",
    "medical_device_status",
    "dangerous_goods_status",
    "origin_country",
)


@dataclass
class ProductIdentity:
    commercial_name: str | None = None
    product_name: str | None = None
    model: str | None = None
    manufacturer: str | None = None
    brand: str | None = None
    intended_use: str | None = None
    function: str | None = None
    material: str | None = None
    composition: str | None = None
    operating_principle: str | None = None
    technical_specifications: dict[str, Any] = field(default_factory=dict)
    voltage: str | None = None
    power: str | None = None
    capacity: str | None = None
    dimensions: str | None = None
    chemical_identifiers: tuple[str, ...] = ()
    medical_device_status: str | None = None
    dangerous_goods_status: str | None = None
    origin_country: str | None = None
    category: str = "unknown"
    customer_description: str | None = None
    identity_status: str = "NORMALIZED_UNVERIFIED"
    field_states: dict[str, FieldState] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.chemical_identifiers = tuple(str(item) for item in _normalise_tuple(self.chemical_identifiers))
        self.technical_specifications = dict(self.technical_specifications or {})
        self.field_states = {
            str(key): value if isinstance(value, FieldState) else FieldState(str(value))
            for key, value in (self.field_states or {}).items()
        }
        self.validate()

    def validate(self) -> None:
        unknown_fields = set(self.field_states) - set(IDENTITY_FIELD_NAMES)
        if unknown_fields:
            raise ValueError(f"unknown product field states: {sorted(unknown_fields)}")
        if not str(self.category).strip():
            raise ValueError("category is required")

    @property
    def missing_fields(self) -> tuple[str, ...]:
        return tuple(
            name
            for name, state in self.field_states.items()
            if state is FieldState.REQUIRED_FOR_THIS_PRODUCT
        )

    def to_dict(self) -> dict[str, Any]:
        return _serialise(self)


@dataclass
class DocumentEvidence:
    document_type: DocumentType
    present: bool = False
    valid: bool | None = None
    relevant: bool | None = None
    sufficient: bool | None = None
    interpretation: str | None = None
    source: SourceRecord | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.document_type, DocumentType):
            self.document_type = DocumentType(str(self.document_type))
        if not self.present:
            self.valid = False if self.valid is True else self.valid
            self.sufficient = False if self.sufficient is True else self.sufficient
        if self.sufficient is True and (self.present is not True or self.valid is not True or self.relevant is not True):
            raise ValueError("sufficient evidence must be present, valid, and relevant")

    def to_dict(self) -> dict[str, Any]:
        return _serialise(self)


@dataclass(frozen=True)
class DocumentRequest:
    document_type: DocumentType
    reason: str
    priority: str = "NORMAL"
    conditional_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.document_type, DocumentType):
            object.__setattr__(self, "document_type", DocumentType(str(self.document_type)))
        object.__setattr__(self, "conditional_on", tuple(str(item) for item in _normalise_tuple(self.conditional_on)))

    def to_dict(self) -> dict[str, Any]:
        return _serialise(self)


@dataclass
class EvidenceRequestPlan:
    requests: tuple[DocumentRequest, ...] = ()
    supplied_documents: tuple[DocumentEvidence, ...] = ()
    missing_information: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return _serialise(self)


@dataclass(frozen=True)
class HSCodeCandidate:
    hs_code: str
    description: str
    reasoning: str
    product_facts_used: tuple[str, ...] = ()
    confidence: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        code = str(self.hs_code).strip()
        if not code or not code.isdigit():
            raise ValueError("HS candidate must be numeric")
        object.__setattr__(self, "hs_code", code)
        confidence = Decimal(str(self.confidence))
        if not confidence.is_finite() or not Decimal("0") <= confidence <= Decimal("1"):
            raise ValueError("candidate confidence must be between 0 and 1")
        object.__setattr__(self, "confidence", confidence)
        object.__setattr__(self, "product_facts_used", tuple(str(item) for item in _normalise_tuple(self.product_facts_used)))

    def to_dict(self) -> dict[str, Any]:
        return _serialise(self)


@dataclass
class HSAssessment:
    candidates: tuple[HSCodeCandidate, ...] = ()
    candidate_reasoning: str = ""
    product_facts_used: tuple[str, ...] = ()
    missing_facts: tuple[str, ...] = ()
    ambiguity: tuple[str, ...] = ()
    confidence: Decimal = Decimal("0")
    final_classification_status: HSClassificationStatus = HSClassificationStatus.NEEDS_MORE_PRODUCT_DATA
    source_status: EvidenceStatus = EvidenceStatus.NOT_RETRIEVED

    def __post_init__(self) -> None:
        self.candidates = tuple(self.candidates or ())
        self.product_facts_used = tuple(str(item) for item in _normalise_tuple(self.product_facts_used))
        self.missing_facts = tuple(str(item) for item in _normalise_tuple(self.missing_facts))
        self.ambiguity = tuple(str(item) for item in _normalise_tuple(self.ambiguity))
        if not isinstance(self.final_classification_status, HSClassificationStatus):
            self.final_classification_status = HSClassificationStatus(str(self.final_classification_status))
        if not isinstance(self.source_status, EvidenceStatus):
            self.source_status = EvidenceStatus(str(self.source_status))
        confidence = Decimal(str(self.confidence))
        if not confidence.is_finite() or not Decimal("0") <= confidence <= Decimal("1"):
            raise ValueError("HS confidence must be between 0 and 1")
        self.confidence = confidence

    def to_dict(self) -> dict[str, Any]:
        return _serialise(self)


@dataclass
class RegulatoryMeasure:
    category: MeasureCategory
    status: MeasureStatus = MeasureStatus.UNKNOWN
    conclusion: str | None = None
    required_documents: tuple[DocumentType, ...] = ()
    responsible_authority: str | None = None
    legal_sources: tuple[SourceRecord, ...] = ()
    confidence: Decimal = Decimal("0")
    evidence_status: EvidenceStatus = EvidenceStatus.NOT_RETRIEVED

    def __post_init__(self) -> None:
        if not isinstance(self.category, MeasureCategory):
            self.category = MeasureCategory(str(self.category))
        if not isinstance(self.status, MeasureStatus):
            self.status = MeasureStatus(str(self.status))
        self.required_documents = tuple(
            item if isinstance(item, DocumentType) else DocumentType(str(item))
            for item in _normalise_tuple(self.required_documents)
        )
        self.legal_sources = tuple(self.legal_sources or ())
        self.evidence_status = (
            self.evidence_status
            if isinstance(self.evidence_status, EvidenceStatus)
            else EvidenceStatus(str(self.evidence_status))
        )
        confidence = Decimal(str(self.confidence))
        if not confidence.is_finite() or not Decimal("0") <= confidence <= Decimal("1"):
            raise ValueError("measure confidence must be between 0 and 1")
        self.confidence = confidence

    def to_dict(self) -> dict[str, Any]:
        return _serialise(self)


@dataclass
class RegulatoryAssessment:
    product_identity: ProductIdentity
    hs_candidates: HSAssessment
    import_status: str = UNKNOWN
    measures: tuple[RegulatoryMeasure, ...] = ()
    required_documents: tuple[DocumentRequest, ...] = ()
    responsible_authorities: tuple[str, ...] = ()
    legal_sources: tuple[SourceRecord, ...] = ()
    missing_information: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    confidence: Decimal = Decimal("0")
    assessment_status: RegulatoryAssessmentStatus = RegulatoryAssessmentStatus.NEEDS_CUSTOMER_INPUT

    def __post_init__(self) -> None:
        if not isinstance(self.assessment_status, RegulatoryAssessmentStatus):
            self.assessment_status = RegulatoryAssessmentStatus(str(self.assessment_status))
        self.measures = tuple(self.measures or ())
        self.required_documents = tuple(self.required_documents or ())
        self.responsible_authorities = tuple(str(item) for item in _normalise_tuple(self.responsible_authorities))
        self.legal_sources = tuple(self.legal_sources or ())
        self.missing_information = tuple(str(item) for item in _normalise_tuple(self.missing_information))
        self.assumptions = tuple(str(item) for item in _normalise_tuple(self.assumptions))
        self.warnings = tuple(str(item) for item in _normalise_tuple(self.warnings))
        confidence = Decimal(str(self.confidence))
        if not confidence.is_finite() or not Decimal("0") <= confidence <= Decimal("1"):
            raise ValueError("assessment confidence must be between 0 and 1")
        self.confidence = confidence

    def to_dict(self) -> dict[str, Any]:
        return _serialise(self)


@dataclass
class TradeTaxSnapshot:
    origin_country: str | None
    destination_country: str | None
    hs_code: str | None
    assessment_date: str | None
    mfn_import_duty: Decimal | None = None
    preferential_duty: Decimal | None = None
    preferential_eligibility: PreferenceEligibility = PreferenceEligibility.UNKNOWN
    fta_program: str | None = None
    origin_evidence_required: tuple[DocumentType, ...] = ()
    vat_rate: Decimal | None = None
    other_tax_rate: Decimal | None = None
    source: SourceRecord | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    confidence: Decimal = Decimal("0")
    status: TaxSnapshotStatus = TaxSnapshotStatus.INCOMPLETE_INPUT
    hs_classification_status: HSClassificationStatus = HSClassificationStatus.CANDIDATE_ONLY
    hs_is_final: bool = False
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.preferential_eligibility, PreferenceEligibility):
            self.preferential_eligibility = PreferenceEligibility(str(self.preferential_eligibility))
        if not isinstance(self.status, TaxSnapshotStatus):
            self.status = TaxSnapshotStatus(str(self.status))
        if not isinstance(self.hs_classification_status, HSClassificationStatus):
            self.hs_classification_status = HSClassificationStatus(str(self.hs_classification_status))
        self.origin_evidence_required = tuple(
            item if isinstance(item, DocumentType) else DocumentType(str(item))
            for item in _normalise_tuple(self.origin_evidence_required)
        )
        self.warnings = tuple(str(item) for item in _normalise_tuple(self.warnings))
        for name in ("mfn_import_duty", "preferential_duty", "vat_rate", "other_tax_rate", "confidence"):
            value = getattr(self, name)
            if value is not None:
                parsed = Decimal(str(value))
                if not parsed.is_finite() or parsed < Decimal("0"):
                    raise ValueError(f"{name} must be a finite non-negative decimal")
                if name == "confidence" and parsed > Decimal("1"):
                    raise ValueError("confidence must be between 0 and 1")
                setattr(self, name, parsed)

    def to_dict(self) -> dict[str, Any]:
        return _serialise(self)


@dataclass(frozen=True)
class TaxTraceStep:
    name: str
    formula: str
    inputs: dict[str, str]
    output: str

    def to_dict(self) -> dict[str, Any]:
        return _serialise(self)


@dataclass
class TaxCalculationResult:
    status: TaxCalculationStatus
    customs_value: Decimal | None = None
    total_tax: Decimal | None = None
    steps: tuple[TaxTraceStep, ...] = ()
    missing_inputs: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, TaxCalculationStatus):
            self.status = TaxCalculationStatus(str(self.status))
        self.steps = tuple(self.steps or ())
        self.missing_inputs = tuple(str(item) for item in _normalise_tuple(self.missing_inputs))
        self.warnings = tuple(str(item) for item in _normalise_tuple(self.warnings))
        if self.customs_value is not None:
            self.customs_value = Decimal(str(self.customs_value))
        if self.total_tax is not None:
            self.total_tax = Decimal(str(self.total_tax))

    def to_dict(self) -> dict[str, Any]:
        return _serialise(self)
