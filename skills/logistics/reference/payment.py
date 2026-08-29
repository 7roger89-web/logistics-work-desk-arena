"""Deterministic, review-only payment scenarios and compliance checks."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from .common import (
    COMPLIANCE_REVIEW_REQUIRED,
    INVALID_INPUT,
    NEEDS_CUSTOMER_INPUT,
    append_unique,
    clone_mapping,
    decimal_value,
    first_present,
    is_known,
    is_present,
    money_text,
    number_text,
    source_label,
)


def _timestamp_is_valid(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        from datetime import datetime

        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _fx_rate(snapshot: Any, rate_key: str, missing: list[str]) -> tuple[Decimal | None, dict[str, Any]]:
    if not isinstance(snapshot, Mapping):
        append_unique(missing, "fx_snapshot")
        return None, {}
    result = clone_mapping(snapshot)
    if not is_known(result.get("source")):
        append_unique(missing, "fx_snapshot.source")
    captured_at = result.get("captured_at")
    if not _timestamp_is_valid(captured_at):
        append_unique(missing, "fx_snapshot.captured_at")
    raw_rate = first_present(result, rate_key, "rate")
    if not is_known(raw_rate):
        append_unique(missing, f"fx_snapshot.{rate_key}")
        return None, result
    try:
        rate = decimal_value(raw_rate, f"fx_snapshot.{rate_key}")
    except ValueError:
        append_unique(missing, f"fx_snapshot.{rate_key}")
        return None, result
    if rate <= 0:
        append_unique(missing, f"fx_snapshot.{rate_key}")
        return None, result
    return rate, result


def _fee(payload: Mapping[str, Any], key: str, missing: list[str]) -> Decimal | None:
    if key not in payload or not is_present(payload.get(key)):
        append_unique(missing, key)
        return None
    raw = payload.get(key)
    inline_source = None
    if isinstance(raw, Mapping):
        inline_source = source_label(raw)
        raw = first_present(raw, "amount", "value")
    try:
        value = decimal_value(raw, key)
    except ValueError:
        append_unique(missing, key)
        return None

    sources = payload.get("fee_sources")
    source = inline_source
    if isinstance(sources, Mapping):
        source = source or source_label(sources.get(key))
    if not source:
        append_unique(missing, f"fee_sources.{key}")
    return value


def _amount(payload: Mapping[str, Any], key: str, missing: list[str]) -> Decimal | None:
    if key not in payload or not is_present(payload.get(key)):
        append_unique(missing, key)
        return None
    try:
        return decimal_value(payload.get(key), key)
    except ValueError:
        append_unique(missing, key)
        return None


def _needs_input(scenario: str, missing: list[str]) -> dict[str, Any]:
    return {
        "status": NEEDS_CUSTOMER_INPUT,
        "scenario": scenario,
        "amounts": {},
        "calculation_trace": [],
        "missing_information": missing,
        "compliance_review": None,
        "payment_instruction": None,
        "authority": {
            "estimate_only": True,
            "transfer_authorized": False,
            "verified_business_value": False,
        },
    }


def _invalid_input(scenario: str, reason: str) -> dict[str, Any]:
    return {
        "status": INVALID_INPUT,
        "scenario": scenario,
        "amounts": {},
        "calculation_trace": [],
        "missing_information": [reason],
        "compliance_review": None,
        "payment_instruction": None,
        "authority": {
            "estimate_only": True,
            "transfer_authorized": False,
            "verified_business_value": False,
        },
    }


def _commercial_value(value: Any, label: str) -> tuple[Decimal | None, str | None, str | None]:
    if isinstance(value, Mapping):
        raw_amount = first_present(value, "amount", "value", "commercial_value")
        currency = first_present(value, "currency", "ccy")
    else:
        raw_amount = value
        currency = None
    if not is_present(raw_amount):
        return None, str(currency) if is_present(currency) else None, f"{label}.amount_missing"
    try:
        amount = decimal_value(raw_amount, f"{label}.amount")
    except ValueError:
        return None, str(currency) if is_present(currency) else None, f"{label}.amount_invalid"
    return amount, str(currency).upper() if is_present(currency) else None, None


def _commercial_values(payload: Mapping[str, Any]) -> dict[str, Any]:
    nested = payload.get("commercial_values")
    if isinstance(nested, Mapping):
        return clone_mapping(nested)
    keys = (
        "invoice_value",
        "commercial_value",
        "payment_value",
        "payment_amount",
        "declared_value",
        "customs_value",
    )
    return {key: payload[key] for key in keys if key in payload}


def assess_commercial_consistency(values: Mapping[str, Any] | None) -> dict[str, Any]:
    """Compare explicit commercial values and fail closed on mismatch."""

    supplied = clone_mapping(values)
    parsed: dict[str, dict[str, str]] = {}
    invalid: list[dict[str, Any]] = []
    for label, raw in supplied.items():
        amount, currency, error = _commercial_value(raw, label)
        if error:
            invalid.append({"field": label, "reason": error})
            continue
        if amount is not None:
            parsed[label] = {
                "amount": money_text(amount),
                "currency": currency or "UNKNOWN",
            }

    discrepancies: list[dict[str, Any]] = []
    labels = list(parsed)
    if invalid:
        discrepancies.extend(invalid)
    if len(labels) >= 2:
        baseline_label = labels[0]
        baseline_amount = Decimal(parsed[baseline_label]["amount"])
        baseline_currency = parsed[baseline_label]["currency"]
        for label in labels[1:]:
            current_amount = Decimal(parsed[label]["amount"])
            current_currency = parsed[label]["currency"]
            if current_amount != baseline_amount or current_currency != baseline_currency:
                discrepancies.append(
                    {
                        "fields": [baseline_label, label],
                        "baseline": parsed[baseline_label],
                        "observed": parsed[label],
                        "reason": "amount_or_currency_mismatch_without_authorized_reconciliation",
                    }
                )

    if discrepancies:
        return {
            "status": COMPLIANCE_REVIEW_REQUIRED,
            "observed_values": parsed,
            "discrepancies": discrepancies,
            "required_documents": [
                "invoice or commercial contract",
                "payment proof or bank statement",
                "declared/customs documents and supporting records",
            ],
            "clarifications": [
                "identify the authoritative value and currency for each document",
                "obtain written owner/compliance review before proceeding",
            ],
            "evasion_guidance": None,
        }

    return {
        "status": "NO_DISCREPANCY_FOUND",
        "observed_values": parsed,
        "discrepancies": [],
        "required_documents": [],
        "clarifications": [],
        "evasion_guidance": None,
    }


def _compliance_result(scenario: str, assessment: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": COMPLIANCE_REVIEW_REQUIRED,
        "scenario": scenario,
        "amounts": {},
        "calculation_trace": [],
        "missing_information": [],
        "compliance_review": assessment,
        "payment_instruction": None,
        "authority": {
            "estimate_only": True,
            "transfer_authorized": False,
            "verified_business_value": False,
            "concealment_or_undervaluation": False,
        },
    }


def _scenario_a(payload: Mapping[str, Any], assessment: dict[str, Any]) -> dict[str, Any]:
    scenario = "A_FACTORY_RECEIVES_USD"
    missing: list[str] = []
    invoice = _amount(payload, "invoice_amount_usd", missing)
    bank_fee = _fee(payload, "bank_service_fee_usd", missing)
    wire_fee = _fee(payload, "wire_fee_usd", missing)
    conversion_fee_vnd = _fee(payload, "bank_conversion_fee_vnd", missing)
    rate, fx_snapshot = _fx_rate(payload.get("fx_snapshot"), "usd_to_vnd", missing)
    if missing or any(value is None for value in (invoice, bank_fee, wire_fee, conversion_fee_vnd, rate)):
        result = _needs_input(scenario, missing)
        result["fx_snapshot"] = fx_snapshot
        return result
    assert invoice is not None and bank_fee is not None and wire_fee is not None
    assert conversion_fee_vnd is not None and rate is not None
    conversion_fee_usd = conversion_fee_vnd / rate
    total_fees_usd = bank_fee + wire_fee + conversion_fee_usd
    received_usd = invoice - total_fees_usd
    if received_usd < 0:
        return _invalid_input(scenario, "fees_exceed_invoice_amount")
    received_vnd = received_usd * rate
    trace = [
        {
            "stage": "INPUT",
            "expression": "invoice_amount_usd, bank_service_fee_usd, wire_fee_usd, bank_conversion_fee_vnd",
            "value": {
                "invoice_amount_usd": money_text(invoice),
                "bank_service_fee_usd": money_text(bank_fee),
                "wire_fee_usd": money_text(wire_fee),
                "bank_conversion_fee_vnd": money_text(conversion_fee_vnd),
            },
        },
        {
            "stage": "RATE",
            "expression": f"bank_conversion_fee_usd = {money_text(conversion_fee_vnd)} / {number_text(rate)}",
            "value": money_text(conversion_fee_usd),
            "source": fx_snapshot.get("source"),
        },
        {
            "stage": "FEE",
            "expression": f"total_fees_usd = {money_text(bank_fee)} + {money_text(wire_fee)} + {money_text(conversion_fee_usd)}",
            "value": money_text(total_fees_usd),
            "fee_sources": clone_mapping(payload.get("fee_sources")),
        },
        {
            "stage": "INTERMEDIATE_AMOUNT",
            "expression": f"received_usd = {money_text(invoice)} - {money_text(total_fees_usd)}",
            "value": money_text(received_usd),
        },
        {
            "stage": "FINAL_AMOUNT",
            "expression": f"received_vnd = {money_text(received_usd)} * {number_text(rate)}",
            "value": money_text(received_vnd),
        },
    ]
    return {
        "status": "CALCULATED",
        "scenario": scenario,
        "amounts": {
            "invoice_amount_usd": money_text(invoice),
            "bank_service_fee_usd": money_text(bank_fee),
            "wire_fee_usd": money_text(wire_fee),
            "bank_conversion_fee_vnd": money_text(conversion_fee_vnd),
            "bank_conversion_fee_usd": money_text(conversion_fee_usd),
            "total_fees_usd": money_text(total_fees_usd),
            "received_usd": money_text(received_usd),
            "received_vnd": money_text(received_vnd),
        },
        "fx_snapshot": fx_snapshot,
        "calculation_trace": trace,
        "missing_information": [],
        "compliance_review": assessment,
        "payment_instruction": None,
        "authority": {
            "estimate_only": True,
            "transfer_authorized": False,
            "verified_business_value": False,
        },
    }


def _scenario_b(payload: Mapping[str, Any], assessment: dict[str, Any]) -> dict[str, Any]:
    scenario = "B_FACTORY_RECEIVES_RMB"
    missing: list[str] = []
    authorized = payload.get("authorized_flow_confirmation")
    if authorized is not True:
        if authorized is False:
            return _compliance_result(
                scenario,
                {
                    "status": COMPLIANCE_REVIEW_REQUIRED,
                    "observed_values": {},
                    "discrepancies": [{"field": "authorized_flow_confirmation", "reason": "explicitly_not_authorized"}],
                    "required_documents": ["written confirmation of an authorized China-side payment/agent flow"],
                    "clarifications": ["confirm the lawful parties and documentation before any transfer discussion"],
                    "evasion_guidance": None,
                },
            )
        append_unique(missing, "authorized_flow_confirmation")
    source_usd = _amount(payload, "source_amount_usd", missing)
    transfer_fee = _fee(payload, "transfer_fee_usd", missing)
    intermediary_fee = _fee(payload, "intermediary_fee_cny", missing)
    rate, fx_snapshot = _fx_rate(payload.get("fx_snapshot"), "usd_to_cny", missing)
    if missing or any(value is None for value in (source_usd, transfer_fee, intermediary_fee, rate)):
        result = _needs_input(scenario, missing)
        result["fx_snapshot"] = fx_snapshot
        return result
    assert source_usd is not None and transfer_fee is not None
    assert intermediary_fee is not None and rate is not None
    net_usd = source_usd - transfer_fee
    if net_usd < 0:
        return _invalid_input(scenario, "transfer_fee_exceeds_source_amount")
    gross_rmb = net_usd * rate
    received_rmb = gross_rmb - intermediary_fee
    if received_rmb < 0:
        return _invalid_input(scenario, "intermediary_fee_exceeds_converted_amount")
    trace = [
        {
            "stage": "INPUT",
            "expression": "source_amount_usd, transfer_fee_usd, intermediary_fee_cny",
            "value": {
                "source_amount_usd": money_text(source_usd),
                "transfer_fee_usd": money_text(transfer_fee),
                "intermediary_fee_cny": money_text(intermediary_fee),
            },
        },
        {
            "stage": "RATE",
            "expression": f"gross_rmb = net_usd * {number_text(rate)}",
            "value": number_text(gross_rmb),
            "source": fx_snapshot.get("source"),
        },
        {
            "stage": "FEE",
            "expression": f"received_rmb = {number_text(gross_rmb)} - {money_text(intermediary_fee)}",
            "value": money_text(intermediary_fee),
            "fee_sources": clone_mapping(payload.get("fee_sources")),
        },
        {
            "stage": "INTERMEDIATE_AMOUNT",
            "expression": f"net_usd = {money_text(source_usd)} - {money_text(transfer_fee)}",
            "value": money_text(net_usd),
        },
        {
            "stage": "FINAL_AMOUNT",
            "expression": f"received_rmb = {number_text(gross_rmb)} - {money_text(intermediary_fee)}",
            "value": money_text(received_rmb),
        },
    ]
    return {
        "status": "CALCULATED",
        "scenario": scenario,
        "amounts": {
            "source_amount_usd": money_text(source_usd),
            "transfer_fee_usd": money_text(transfer_fee),
            "net_usd": money_text(net_usd),
            "gross_rmb": money_text(gross_rmb),
            "intermediary_fee_cny": money_text(intermediary_fee),
            "received_rmb": money_text(received_rmb),
        },
        "fx_snapshot": fx_snapshot,
        "calculation_trace": trace,
        "missing_information": [],
        "compliance_review": assessment,
        "payment_instruction": None,
        "authority": {
            "estimate_only": True,
            "transfer_authorized": False,
            "authorized_flow_confirmed": True,
            "verified_business_value": False,
        },
    }


def calculate_payment_scenario(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Calculate a supplied scenario, or fail closed before arithmetic."""

    request = clone_mapping(payload)
    raw_scenario = first_present(request, "scenario", "payment_scenario")
    scenario_key = str(raw_scenario).upper() if is_present(raw_scenario) else "UNKNOWN"
    assessment = assess_commercial_consistency(_commercial_values(request))
    if assessment["status"] == COMPLIANCE_REVIEW_REQUIRED:
        return _compliance_result(scenario_key, assessment)

    if scenario_key in {"A", "SCENARIO_A", "A_FACTORY_RECEIVES_USD", "USD"}:
        return _scenario_a(request, assessment)
    if scenario_key in {"B", "SCENARIO_B", "B_FACTORY_RECEIVES_RMB", "RMB"}:
        return _scenario_b(request, assessment)
    return _needs_input(scenario_key, ["scenario (A or B)"])
