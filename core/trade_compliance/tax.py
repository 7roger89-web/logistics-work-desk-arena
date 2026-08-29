"""Fail-closed tariff snapshot and transparent import-tax arithmetic."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from .models import (
    DocumentType,
    EvidenceStatus,
    HSClassificationStatus,
    PreferenceEligibility,
    SourceAuthority,
    SourceRecord,
    TaxCalculationResult,
    TaxCalculationStatus,
    TaxSnapshotStatus,
    TaxTraceStep,
    TradeTaxSnapshot,
)
from .sources import parse_source_record


def _decimal(value: Any, *, field_name: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field_name} must be a decimal") from exc
    if not parsed.is_finite() or parsed < Decimal("0"):
        raise ValueError(f"{field_name} must be finite and non-negative")
    return parsed


def _date(value: str | date | datetime | None) -> date | None:
    if value is None:
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


def _doc_type(value: Any) -> DocumentType:
    if isinstance(value, DocumentType):
        return value
    text = str(value).strip().upper().replace("-", "_").replace(" ", "_")
    aliases = {
        "COO": DocumentType.CERTIFICATE_OF_ORIGIN,
        "CERTIFICATE_OF_ORIGIN": DocumentType.CERTIFICATE_OF_ORIGIN,
        "C_O": DocumentType.CERTIFICATE_OF_ORIGIN,
        "CO": DocumentType.CO,
        "CFS": DocumentType.CFS,
    }
    if text in aliases:
        return aliases[text]
    return DocumentType(text)


def _source_result(
    source_result: SourceRecord | Mapping[str, Any] | None,
    *,
    destination_country: str,
) -> SourceRecord | None:
    if source_result is None:
        return None
    if isinstance(source_result, SourceRecord):
        return source_result
    if isinstance(source_result, Mapping):
        return parse_source_record(source_result, default_jurisdiction=destination_country)
    raise TypeError("source_result must be a SourceRecord or mapping")


def _source_scope_matches(
    source: SourceRecord,
    *,
    destination_country: str,
    origin_country: str,
    hs_code: str,
    assessment_date: date,
) -> bool:
    if source.authority_level is not SourceAuthority.OFFICIAL:
        return False
    if source.evidence_status is not EvidenceStatus.VERIFIED:
        return False
    if source.jurisdiction.strip().upper() != destination_country:
        return False
    if not source.retrieved_at or not source.covers_date(assessment_date):
        return False
    conclusion = source.conclusion
    if not isinstance(conclusion, Mapping):
        return False
    scoped_hs = conclusion.get("hs_code", conclusion.get("hs"))
    if scoped_hs is None:
        scoped_hs = source.product_hs_scope[0] if len(source.product_hs_scope) == 1 else None
    if str(scoped_hs or "").strip() != hs_code:
        return False
    if source.product_hs_scope and str(scoped_hs).strip() not in source.product_hs_scope:
        return False
    scoped_origin = conclusion.get("origin_country", conclusion.get("origin"))
    if str(scoped_origin or "").strip().upper() != origin_country:
        return False
    scoped_destination = conclusion.get("destination_country", conclusion.get("destination"))
    if scoped_destination is not None and str(scoped_destination).strip().upper() != destination_country:
        return False
    return True


def _preference(value: Any) -> PreferenceEligibility:
    if value is None:
        return PreferenceEligibility.UNKNOWN
    text = str(value).strip().upper()
    aliases = {
        "UNKNOWN": PreferenceEligibility.UNKNOWN,
        "POTENTIAL": PreferenceEligibility.POTENTIALLY_AVAILABLE,
        "POTENTIALLY_AVAILABLE": PreferenceEligibility.POTENTIALLY_AVAILABLE,
        "VERIFIED_ELIGIBLE": PreferenceEligibility.VERIFIED_ELIGIBLE,
        "ELIGIBLE": PreferenceEligibility.VERIFIED_ELIGIBLE,
        "NOT_ELIGIBLE": PreferenceEligibility.NOT_ELIGIBLE,
    }
    return aliases.get(text, PreferenceEligibility.UNKNOWN)


def build_tax_snapshot(
    *,
    origin_country: str | None,
    destination_country: str | None,
    hs_code: str | None,
    assessment_date: str | date | datetime | None,
    source_result: SourceRecord | Mapping[str, Any] | None = None,
    hs_is_final: bool = False,
) -> TradeTaxSnapshot:
    """Build a tariff snapshot only from a scoped, current official result."""

    origin = str(origin_country or "").strip().upper() or None
    destination = str(destination_country or "").strip().upper() or None
    code = str(hs_code or "").strip() or None
    date_value = _date(assessment_date)
    warnings = [
        "TARIFF_RATE_REQUIRES_JURISDICTION + HS + ORIGIN + DATE",
        "MFN_RATE != PREFERENTIAL_RATE",
        "PREFERENTIAL_ELIGIBILITY != AUTOMATIC",
        "FTA_EXISTS != SHIPMENT_QUALIFIES",
        "VAT_RATE != IMPORT_DUTY_RATE",
    ]
    source = _source_result(source_result, destination_country=destination or "VN")
    if not origin or not destination or not code or date_value is None:
        warnings.append("Missing tariff scope input; no rate is inferred.")
        return TradeTaxSnapshot(
            origin_country=origin,
            destination_country=destination,
            hs_code=code,
            assessment_date=date_value.isoformat() if date_value else None,
            source=source,
            status=TaxSnapshotStatus.INCOMPLETE_INPUT,
            hs_is_final=hs_is_final,
            warnings=tuple(warnings),
        )

    if not hs_is_final:
        warnings.append("HS_CANDIDATE != FINAL_HS_CLASSIFICATION: a candidate cannot drive a tariff calculation.")
    if source is None:
        warnings.append("No current authoritative tariff source result was supplied.")
        return TradeTaxSnapshot(
            origin_country=origin,
            destination_country=destination,
            hs_code=code,
            assessment_date=date_value.isoformat(),
            source=None,
            status=TaxSnapshotStatus.SOURCE_VERIFICATION_REQUIRED,
            hs_is_final=hs_is_final,
            warnings=tuple(warnings),
        )
    if source.evidence_status is EvidenceStatus.CONFLICTING:
        warnings.append("Conflicting tariff source evidence requires review; rates are withheld.")
    elif source.evidence_status is EvidenceStatus.STALE:
        warnings.append("Stale tariff source evidence cannot establish a current rate.")
    elif not _source_scope_matches(
        source,
        destination_country=destination,
        origin_country=origin,
        hs_code=code,
        assessment_date=date_value,
    ):
        warnings.append("Tariff source is not proven official, current, and scoped to this shipment.")

    if not hs_is_final or not _source_scope_matches(
        source,
        destination_country=destination,
        origin_country=origin,
        hs_code=code,
        assessment_date=date_value,
    ):
        return TradeTaxSnapshot(
            origin_country=origin,
            destination_country=destination,
            hs_code=code,
            assessment_date=date_value.isoformat(),
            source=source,
            effective_from=source.effective_from,
            effective_to=source.effective_to,
            confidence=source.confidence or Decimal("0"),
            status=TaxSnapshotStatus.SOURCE_VERIFICATION_REQUIRED,
            hs_is_final=hs_is_final,
            warnings=tuple(warnings),
        )

    conclusion = source.conclusion
    assert isinstance(conclusion, Mapping)
    rates: dict[str, Decimal | None] = {}
    for field_name, keys in {
        "mfn_import_duty": ("mfn_import_duty", "mfn_rate", "import_duty"),
        "preferential_duty": ("preferential_duty", "preferential_rate"),
        "vat_rate": ("vat_rate", "vat"),
        "other_tax_rate": ("other_tax_rate", "other_tax"),
    }.items():
        raw_value = next((conclusion[key] for key in keys if key in conclusion and conclusion[key] is not None), None)
        if raw_value is not None:
            try:
                rates[field_name] = _decimal(raw_value, field_name=field_name)
            except ValueError:
                warnings.append(f"Invalid {field_name} in source result; the rate is withheld.")
                rates[field_name] = None
        else:
            rates[field_name] = None

    preference = _preference(conclusion.get("preferential_eligibility"))
    fta_program = str(conclusion.get("fta_program") or "").strip() or None
    if fta_program and preference is PreferenceEligibility.UNKNOWN:
        preference = PreferenceEligibility.POTENTIALLY_AVAILABLE
    required_origin_evidence: list[DocumentType] = []
    for item in conclusion.get("origin_evidence_required", ()):
        try:
            required_origin_evidence.append(_doc_type(item))
        except ValueError:
            warnings.append(f"Unrecognized origin evidence type retained as unresolved: {item}")
    if rates["preferential_duty"] is not None and preference is not PreferenceEligibility.VERIFIED_ELIGIBLE:
        warnings.append("Preferential rate is potential information only until origin rules and shipment evidence are verified.")

    rate_status = TaxSnapshotStatus.VERIFIED_FROM_SOURCE
    if rates["mfn_import_duty"] is None or rates["vat_rate"] is None:
        rate_status = TaxSnapshotStatus.PARTIALLY_VERIFIED
        warnings.append("Import duty and VAT both require verified rates before arithmetic can run.")
    return TradeTaxSnapshot(
        origin_country=origin,
        destination_country=destination,
        hs_code=code,
        assessment_date=date_value.isoformat(),
        mfn_import_duty=rates["mfn_import_duty"],
        preferential_duty=rates["preferential_duty"],
        preferential_eligibility=preference,
        fta_program=fta_program,
        origin_evidence_required=tuple(required_origin_evidence),
        vat_rate=rates["vat_rate"],
        other_tax_rate=rates["other_tax_rate"],
        source=source,
        effective_from=source.effective_from,
        effective_to=source.effective_to,
        confidence=source.confidence or Decimal("0"),
        status=rate_status,
        hs_is_final=hs_is_final,
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _incomplete(
    *,
    customs_value: Decimal | None,
    missing: list[str],
    warnings: list[str],
) -> TaxCalculationResult:
    return TaxCalculationResult(
        status=TaxCalculationStatus.INCOMPLETE,
        customs_value=customs_value,
        total_tax=None,
        steps=(),
        missing_inputs=tuple(dict.fromkeys(missing)),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_import_taxes(
    snapshot: TradeTaxSnapshot,
    customs_value: Any,
    *,
    other_tax_amount: Any = None,
    use_preferential: bool = False,
    preferential_evidence_verified: bool = False,
) -> TaxCalculationResult:
    """Calculate duty/VAT only from a verified snapshot and explicit inputs."""

    missing: list[str] = []
    warnings = list(snapshot.warnings)
    try:
        value = _decimal(customs_value, field_name="customs_value")
    except ValueError:
        return _incomplete(customs_value=None, missing=["customs_value"], warnings=["Customs value is missing or invalid; it was not guessed."])

    if snapshot.status is not TaxSnapshotStatus.VERIFIED_FROM_SOURCE:
        missing.append("verified_tariff_snapshot")
    if (
        snapshot.source is None
        or snapshot.source.authority_level is not SourceAuthority.OFFICIAL
        or snapshot.source.evidence_status is not EvidenceStatus.VERIFIED
        or not snapshot.source.retrieved_at
    ):
        missing.append("verified_tariff_source")
    snapshot_date = _date(snapshot.assessment_date)
    if (
        snapshot.source is not None
        and snapshot.destination_country
        and snapshot.origin_country
        and snapshot.hs_code
        and snapshot_date is not None
        and not _source_scope_matches(
            snapshot.source,
            destination_country=snapshot.destination_country.strip().upper(),
            origin_country=snapshot.origin_country.strip().upper(),
            hs_code=snapshot.hs_code.strip(),
            assessment_date=snapshot_date,
        )
    ):
        missing.append("verified_tariff_source_scope")
    if not snapshot.hs_is_final:
        missing.append("final_hs_classification")
    if not snapshot.destination_country:
        missing.append("destination_country")
    if not snapshot.origin_country:
        missing.append("origin_country")
    if not snapshot.hs_code:
        missing.append("hs_code")
    if not snapshot.assessment_date:
        missing.append("assessment_date")
    if use_preferential:
        if snapshot.preferential_duty is None:
            missing.append("verified_preferential_duty")
        if snapshot.preferential_eligibility is not PreferenceEligibility.VERIFIED_ELIGIBLE:
            missing.append("verified_preferential_eligibility")
        if not snapshot.origin_evidence_required:
            missing.append("origin_evidence")
        if not preferential_evidence_verified:
            missing.append("verified_origin_evidence")
    else:
        if snapshot.mfn_import_duty is None:
            missing.append("mfn_import_duty")
    if snapshot.vat_rate is None:
        missing.append("vat_rate")
    if missing:
        return _incomplete(customs_value=value, missing=missing, warnings=warnings)

    duty_rate = snapshot.preferential_duty if use_preferential else snapshot.mfn_import_duty
    assert duty_rate is not None
    duty = _money(value * duty_rate)
    steps = [
        TaxTraceStep(
            name="CUSTOMS_VALUE",
            formula="explicit customs_value input",
            inputs={"customs_value": format(value, "f")},
            output=format(_money(value), "f"),
        ),
        TaxTraceStep(
            name="IMPORT_DUTY",
            formula="customs_value × duty_rate",
            inputs={
                "customs_value": format(value, "f"),
                "duty_rate": format(duty_rate, "f"),
                "rate_type": "PREFERENTIAL" if use_preferential else "MFN",
            },
            output=format(duty, "f"),
        ),
    ]

    if other_tax_amount is not None:
        try:
            other_tax = _money(_decimal(other_tax_amount, field_name="other_tax_amount"))
        except ValueError:
            return _incomplete(
                customs_value=value,
                missing=["other_tax_amount"],
                warnings=warnings + ["Other tax amount is invalid; it was not guessed."],
            )
        other_tax_source = "explicit input"
    elif snapshot.other_tax_rate is not None:
        other_tax = _money(value * snapshot.other_tax_rate)
        other_tax_source = "verified source rate"
    else:
        return _incomplete(
            customs_value=value,
            missing=["other_tax_amount_or_verified_other_tax_rate"],
            warnings=warnings + ["Other tax is not assumed to be zero; provide the amount or a verified rate."],
        )
    steps.append(
        TaxTraceStep(
            name="OTHER_TAX",
            formula="explicit amount" if other_tax_amount is not None else "customs_value × other_tax_rate",
            inputs={
                "customs_value": format(value, "f"),
                "other_tax": format(other_tax, "f"),
                "source": other_tax_source,
            },
            output=format(other_tax, "f"),
        )
    )

    vat_base = _money(value + duty + other_tax)
    steps.append(
        TaxTraceStep(
            name="VAT_TAXABLE_BASE",
            formula="customs_value + import_duty + other_tax",
            inputs={
                "customs_value": format(value, "f"),
                "import_duty": format(duty, "f"),
                "other_tax": format(other_tax, "f"),
            },
            output=format(vat_base, "f"),
        )
    )
    vat = _money(vat_base * snapshot.vat_rate)
    steps.append(
        TaxTraceStep(
            name="VAT",
            formula="VAT taxable base × VAT rate",
            inputs={
                "vat_taxable_base": format(vat_base, "f"),
                "vat_rate": format(snapshot.vat_rate, "f"),
            },
            output=format(vat, "f"),
        )
    )
    total = _money(duty + other_tax + vat)
    steps.append(
        TaxTraceStep(
            name="TOTAL_TAX",
            formula="import_duty + other_tax + VAT",
            inputs={
                "import_duty": format(duty, "f"),
                "other_tax": format(other_tax, "f"),
                "vat": format(vat, "f"),
            },
            output=format(total, "f"),
        )
    )
    return TaxCalculationResult(
        status=TaxCalculationStatus.CALCULATED,
        customs_value=_money(value),
        total_tax=total,
        steps=tuple(steps),
        warnings=tuple(dict.fromkeys(warnings)),
    )
