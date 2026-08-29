"""Source-labelled, no-fabrication quotation reasoning."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any

from .common import (
    INCOMPLETE,
    UNKNOWN,
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

KNOWN_COST = "KNOWN_COST"
ESTIMATED_COST = "ESTIMATED_COST"
CUSTOMER_PRICE = "CUSTOMER_PRICE"
UNKNOWN_COST = "UNKNOWN_COST"
ASSUMPTION = "ASSUMPTION"


def _timestamp_is_valid(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _fx_rate_to_vnd(
    snapshot: Any, currency: str, missing: list[str], path: str
) -> tuple[Decimal | None, dict[str, Any]]:
    currency = currency.upper()
    if currency == "VND":
        return Decimal("1"), clone_mapping(snapshot)
    if not isinstance(snapshot, Mapping):
        append_unique(missing, "fx_snapshot")
        return None, {}
    result = clone_mapping(snapshot)
    if not is_known(result.get("source")):
        append_unique(missing, "fx_snapshot.source")
    if not _timestamp_is_valid(result.get("captured_at")):
        append_unique(missing, "fx_snapshot.captured_at")
    rates = result.get("rates_to_vnd")
    if not isinstance(rates, Mapping) or not is_present(rates.get(currency)):
        append_unique(missing, f"fx_snapshot.rates_to_vnd.{currency}")
        return None, result
    try:
        rate = decimal_value(rates[currency], f"fx_snapshot.rates_to_vnd.{currency}")
    except ValueError:
        append_unique(missing, f"fx_snapshot.rates_to_vnd.{currency}")
        return None, result
    if rate <= 0:
        append_unique(missing, f"fx_snapshot.rates_to_vnd.{currency}")
        return None, result
    return rate, result


def _convert_to_vnd(
    amount: Decimal, currency: str, fx_snapshot: Any, missing: list[str], path: str
) -> tuple[Decimal | None, dict[str, Any]]:
    rate, snapshot = _fx_rate_to_vnd(fx_snapshot, currency, missing, path)
    return (amount * rate if rate is not None else None), snapshot


def _convert_between(
    amount: Decimal,
    from_currency: str,
    to_currency: str,
    fx_snapshot: Any,
    missing: list[str],
    path: str,
) -> Decimal | None:
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    if from_currency == to_currency:
        return amount
    from_vnd, _ = _convert_to_vnd(amount, from_currency, fx_snapshot, missing, path)
    to_rate, _ = _fx_rate_to_vnd(fx_snapshot, to_currency, missing, path)
    if from_vnd is None or to_rate is None:
        return None
    return from_vnd / to_rate


def _line_source(line: Mapping[str, Any]) -> str | None:
    for key in ("cost_source", "source"):
        marker = source_label(line.get(key))
        if marker:
            return marker
    for key in ("manual_input", "manual_cost", "manual_source"):
        candidate = line.get(key)
        if candidate is True:
            return "manual_input"
        marker = source_label(candidate)
        if marker:
            return marker
    return None


def _raw_price(line: Mapping[str, Any]) -> Any:
    return first_present(line, "selling_unit_price", "customer_price", "unit_price")


def _raw_cost(line: Mapping[str, Any]) -> Any:
    return first_present(line, "unit_cost", "cost_per_unit", "cost")


def _normalise_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if is_present(value):
        return [value]
    return []


def _line_result(
    line: Mapping[str, Any],
    index: int,
    quote_currency: str,
    fx_snapshot: Any,
    missing: list[str],
    trace: list[dict[str, Any]],
    assumptions: list[Any],
    labels: list[str],
) -> dict[str, Any]:
    prefix = f"service_lines[{index}]"
    line_id = first_present(line, "line_id", "id", "description") or f"LINE_{index + 1}"
    description = first_present(line, "description", "name") or UNKNOWN
    cost_type = str(first_present(line, "cost_type", "type") or "other").lower()
    source = _line_source(line)
    line_labels: list[str] = []
    raw_quantity = first_present(line, "quantity", "qty")
    quantity: Decimal | None = None
    if not is_present(raw_quantity):
        append_unique(missing, f"{prefix}.quantity")
    else:
        try:
            quantity = decimal_value(raw_quantity, f"{prefix}.quantity")
            if quantity <= 0:
                append_unique(missing, f"{prefix}.quantity")
                quantity = None
        except ValueError:
            append_unique(missing, f"{prefix}.quantity")

    cost_currency_raw = first_present(line, "cost_currency", "unit_currency", "currency")
    cost_currency = str(cost_currency_raw).upper() if is_known(cost_currency_raw) else UNKNOWN
    raw_cost = _raw_cost(line)
    unit_cost: Decimal | None = None
    if not is_present(raw_cost):
        append_unique(missing, f"{prefix}.unit_cost")
    else:
        if isinstance(raw_cost, Mapping):
            raw_cost = first_present(raw_cost, "amount", "value")
        try:
            unit_cost = decimal_value(raw_cost, f"{prefix}.unit_cost")
        except ValueError:
            append_unique(missing, f"{prefix}.unit_cost")

    cost_missing: list[str] = []
    if not source:
        cost_missing.append(f"{prefix}.cost_source_or_manual_input")
    if not is_known(cost_currency_raw):
        cost_missing.append(f"{prefix}.cost_currency")
    estimated = line.get("estimated") is True or str(line.get("cost_status", "")).upper() == ESTIMATED_COST
    assumption = first_present(line, "assumption", "estimate_assumption")
    if estimated:
        if not is_present(assumption):
            cost_missing.append(f"{prefix}.assumption")
        else:
            line_labels.append(ASSUMPTION)
            assumptions.append({"line_id": line_id, "text": assumption, "classification": ASSUMPTION})
    if is_known(cost_currency_raw) and str(cost_currency_raw).upper() != "VND":
        # Validate the dynamic FX boundary even when the line is already
        # unknown for another reason, so every missing dependency is visible.
        _fx_rate_to_vnd(fx_snapshot, str(cost_currency_raw), missing, f"{prefix}.cost_currency")
    if cost_missing:
        for item in cost_missing:
            append_unique(missing, item)

    cost_status = UNKNOWN_COST
    cost_total: Decimal | None = None
    cost_total_vnd: Decimal | None = None
    if unit_cost is not None and quantity is not None and source and is_known(cost_currency_raw) and not cost_missing:
        cost_total = unit_cost * quantity
        cost_total_vnd, _ = _convert_to_vnd(
            cost_total, str(cost_currency_raw), fx_snapshot, missing, f"{prefix}.cost_currency"
        )
        if cost_total_vnd is not None:
            cost_status = ESTIMATED_COST if estimated else KNOWN_COST
    if cost_status == UNKNOWN_COST:
        line_labels.insert(0, UNKNOWN_COST)
        trace.append(
            {
                "stage": "UNKNOWN_COST",
                "line_id": line_id,
                "expression": "cost total withheld until explicit cost/source/currency/FX evidence is complete",
                "reason": [item for item in missing if item.startswith(prefix + ".") or item.startswith("fx_snapshot")],
            }
        )
    else:
        line_labels.insert(0, cost_status)
        trace.append(
            {
                "stage": "LINE_TOTAL",
                "line_id": line_id,
                "expression": f"{number_text(quantity)} * {money_text(unit_cost)} {str(cost_currency_raw).upper()}",
                "value": money_text(cost_total),
                "currency": str(cost_currency_raw).upper(),
                "cost_status": cost_status,
                "source": source,
            }
        )

    raw_selling = _raw_price(line)
    selling_currency_raw = first_present(line, "selling_currency", "price_currency", "currency")
    selling_unit: Decimal | None = None
    selling_total: Decimal | None = None
    selling_total_quote: Decimal | None = None
    if is_present(raw_selling):
        if isinstance(raw_selling, Mapping):
            raw_selling = first_present(raw_selling, "amount", "value")
        try:
            selling_unit = decimal_value(raw_selling, f"{prefix}.selling_unit_price")
        except ValueError:
            append_unique(missing, f"{prefix}.selling_unit_price")
        if not is_known(selling_currency_raw):
            append_unique(missing, f"{prefix}.selling_currency")
        elif quantity is not None and selling_unit is not None:
            selling_total = selling_unit * quantity
            selling_total_quote = _convert_between(
                selling_total,
                str(selling_currency_raw),
                quote_currency,
                fx_snapshot,
                missing,
                f"{prefix}.selling_currency",
            )
        if selling_total_quote is not None:
            line_labels.append(CUSTOMER_PRICE)
            trace.append(
                {
                    "stage": "CUSTOMER_PRICE",
                    "line_id": line_id,
                    "expression": f"{number_text(quantity)} * {money_text(selling_unit)} {str(selling_currency_raw).upper()}",
                    "value": money_text(selling_total_quote),
                    "currency": quote_currency,
                    "classification": CUSTOMER_PRICE,
                }
            )
    if line_labels and CUSTOMER_PRICE in line_labels:
        labels.append(CUSTOMER_PRICE)
    if cost_status not in labels:
        labels.append(cost_status)
    if ASSUMPTION in line_labels and ASSUMPTION not in labels:
        labels.append(ASSUMPTION)

    return {
        "line_id": line_id,
        "description": description,
        "cost_type": cost_type,
        "quantity": number_text(quantity) if quantity is not None else UNKNOWN,
        "unit_cost": money_text(unit_cost) if unit_cost is not None else UNKNOWN,
        "cost_currency": cost_currency,
        "cost_source": source or UNKNOWN,
        "cost_status": cost_status,
        "cost_total": money_text(cost_total) if cost_total is not None else UNKNOWN,
        "cost_total_vnd": money_text(cost_total_vnd) if cost_total_vnd is not None else UNKNOWN,
        "selling_unit_price": money_text(selling_unit) if selling_unit is not None else UNKNOWN,
        "selling_currency": str(selling_currency_raw).upper() if is_known(selling_currency_raw) else UNKNOWN,
        "customer_price_total": money_text(selling_total_quote) if selling_total_quote is not None else UNKNOWN,
        "labels": line_labels,
        "assumption": assumption if is_present(assumption) else UNKNOWN,
    }


def build_quote(request: Mapping[str, Any] | None) -> dict[str, Any]:
    """Build an advisory quote without inventing dynamic business values."""

    source = clone_mapping(request)
    missing: list[str] = []
    trace: list[dict[str, Any]] = []
    labels: list[str] = []
    assumptions: list[Any] = _normalise_list(source.get("assumptions"))
    exclusions: list[Any] = _normalise_list(source.get("exclusions"))
    risks: list[Any] = _normalise_list(source.get("risks"))

    quote_id = first_present(source, "quote_id", "id")
    version = first_present(source, "version", "quote_version")
    quote_currency_raw = first_present(source, "currency", "quote_currency")
    quote_currency = str(quote_currency_raw).upper() if is_known(quote_currency_raw) else UNKNOWN
    if not is_known(quote_id):
        append_unique(missing, "quote_id")
    if not is_known(version):
        append_unique(missing, "version")
    if not is_known(quote_currency_raw):
        append_unique(missing, "currency")

    validity = source.get("validity") if isinstance(source.get("validity"), Mapping) else {}
    valid_until = first_present(source, "valid_until", "expiry", "expires_at") or first_present(
        validity, "valid_until", "expires_at"
    )
    if not is_known(valid_until):
        append_unique(missing, "valid_until")

    customer = source.get("customer")
    if not is_present(customer):
        intake = source.get("intake")
        customer = intake.get("customer") if isinstance(intake, Mapping) else None
    if not is_present(customer):
        customer = UNKNOWN
        append_unique(missing, "customer")

    route = source.get("route")
    if not is_present(route):
        intake = source.get("intake")
        shipment = intake.get("shipment") if isinstance(intake, Mapping) else None
        if isinstance(shipment, Mapping) and is_known(shipment.get("origin")) and is_known(shipment.get("destination")):
            route = {"origin": shipment["origin"], "destination": shipment["destination"]}
        else:
            route = UNKNOWN
            append_unique(missing, "route")

    shipment_summary = source.get("shipment_summary")
    if not is_present(shipment_summary):
        intake = source.get("intake")
        shipment_summary = intake.get("shipment") if isinstance(intake, Mapping) else None
    if not is_present(shipment_summary):
        shipment_summary = UNKNOWN
        append_unique(missing, "shipment_summary")

    fx_snapshot = clone_mapping(source.get("fx_snapshot"))
    raw_lines = source.get("service_lines")
    if not isinstance(raw_lines, list) or not raw_lines:
        append_unique(missing, "service_lines")
        raw_lines = []
    service_lines: list[dict[str, Any]] = []
    for index, item in enumerate(raw_lines):
        if not isinstance(item, Mapping):
            append_unique(missing, f"service_lines[{index}]")
            continue
        service_lines.append(
            _line_result(item, index, quote_currency, fx_snapshot, missing, trace, assumptions, labels)
        )

    known_total_vnd = Decimal("0")
    estimated_total_vnd = Decimal("0")
    unknown_present = False
    all_customer_prices = bool(service_lines)
    customer_price_total = Decimal("0")
    for line in service_lines:
        if line["cost_status"] == KNOWN_COST:
            known_total_vnd += Decimal(line["cost_total_vnd"])
        elif line["cost_status"] == ESTIMATED_COST:
            estimated_total_vnd += Decimal(line["cost_total_vnd"])
        else:
            unknown_present = True
        if line["customer_price_total"] == UNKNOWN:
            all_customer_prices = False
        else:
            customer_price_total += Decimal(line["customer_price_total"])

    if unknown_present:
        trace.append(
            {
                "stage": "TOTAL_COST",
                "expression": "known + estimated + unknown line(s)",
                "value": UNKNOWN,
                "reason": "at least one cost line is not source-complete",
            }
        )
    else:
        trace.append(
            {
                "stage": "TOTAL_COST",
                "expression": f"{money_text(known_total_vnd)} + {money_text(estimated_total_vnd)} VND",
                "value": money_text(known_total_vnd + estimated_total_vnd),
                "currency": "VND",
            }
        )
    if all_customer_prices and not is_known(quote_currency_raw):
        all_customer_prices = False
    if all_customer_prices:
        trace.append(
            {
                "stage": "TOTAL_CUSTOMER_PRICE",
                "expression": "sum of explicit customer price lines",
                "value": money_text(customer_price_total),
                "currency": quote_currency,
            }
        )

    advice = source.get("pricing_strategy_advice")
    if is_present(advice):
        pricing_advice = {
            "classification": "MARKETING_PRICING_ADVICE",
            "value": advice,
            "used_in_cost_calculation": False,
        }
    else:
        pricing_advice = None

    if unknown_present:
        append_unique(risks, "one or more dynamic or source-gated costs remain unknown")
    if missing:
        append_unique(risks, "quote requires human review before customer use")

    return {
        "status": "READY_FOR_REVIEW" if not missing else INCOMPLETE,
        "quote_id": quote_id if is_known(quote_id) else UNKNOWN,
        "version": version if is_known(version) else UNKNOWN,
        "customer": customer,
        "route": route,
        "shipment_summary": shipment_summary,
        "service_lines": service_lines,
        "cost_basis": {
            "known_cost_vnd": money_text(known_total_vnd),
            "estimated_cost_vnd": money_text(estimated_total_vnd),
            "unknown_cost_vnd": UNKNOWN if unknown_present else money_text(Decimal("0")),
            "total_cost_vnd": UNKNOWN if unknown_present else money_text(known_total_vnd + estimated_total_vnd),
            "labels": labels,
        },
        "selling_price": {
            "currency": quote_currency,
            "total": money_text(customer_price_total) if all_customer_prices else UNKNOWN,
            "status": CUSTOMER_PRICE if all_customer_prices else UNKNOWN_COST,
        },
        "currency": quote_currency,
        "fx_snapshot": fx_snapshot or UNKNOWN,
        "assumptions": assumptions,
        "exclusions": exclusions,
        "validity": {"valid_until": valid_until if is_known(valid_until) else UNKNOWN},
        "risks": risks,
        "missing_information": missing,
        "calculation_trace": trace,
        "pricing_advice": pricing_advice,
        "authority": {
            "quote_is_invoice": False,
            "quote_is_customs_declaration": False,
            "quote_is_finance_ledger": False,
            "customer_acceptance": False,
            "dynamic_values_verified": False,
        },
    }
