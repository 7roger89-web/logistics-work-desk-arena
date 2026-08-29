"""Small shared helpers for the pure Logistics reference functions."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from typing import Any

UNKNOWN = "UNKNOWN"
NEEDS_CUSTOMER_INPUT = "NEEDS_CUSTOMER_INPUT"
READY = "READY"
READY_FOR_REVIEW = "READY_FOR_REVIEW"
INCOMPLETE = "INCOMPLETE"
INVALID_INPUT = "INVALID_INPUT"
COMPLIANCE_REVIEW_REQUIRED = "COMPLIANCE_REVIEW_REQUIRED"


def clone_mapping(value: Any) -> dict[str, Any]:
    """Return a deep copy of a mapping without mutating the caller's payload."""

    return deepcopy(dict(value)) if isinstance(value, Mapping) else {}


def is_present(value: Any) -> bool:
    """Presence means an explicit, non-blank value; ``0`` remains present."""

    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def is_known(value: Any) -> bool:
    """Reject sentinel values as facts while preserving them in output."""

    if isinstance(value, str):
        return is_present(value) and value not in {UNKNOWN, NEEDS_CUSTOMER_INPUT}
    return is_present(value)


def first_present(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and is_present(mapping[key]):
            return mapping[key]
    return None


def decimal_value(value: Any, field: str) -> Decimal:
    """Parse a finite Decimal and reject booleans/non-numeric values."""

    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric, not boolean")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field} must be finite")
    return parsed


def money_text(value: Decimal) -> str:
    """Serialize money consistently without binary floating-point rounding."""

    return format(value.quantize(Decimal("0.01")), "f")


def number_text(value: Decimal) -> str:
    """Serialize a decimal rate/quantity without unnecessary exponent notation."""

    return format(value.normalize(), "f")


def append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def source_label(value: Any) -> str | None:
    """Read a human-auditable source/manual marker, never create one."""

    if isinstance(value, Mapping):
        for key in ("source", "cost_source", "manual_input", "manual_source"):
            candidate = value.get(key)
            if is_present(candidate) and candidate is not False:
                return str(candidate)
    elif is_present(value) and value is not False:
        return str(value)
    return None
