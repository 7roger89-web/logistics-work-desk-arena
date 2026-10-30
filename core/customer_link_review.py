"""Read-only customer/lot linkage diagnostics for the G1 production audit.

The master customer's immutable ID is the ONLY ownership authority. Legacy
names can create a review candidate but never bind a customer, grant portal
access or mutate either input. No financial or contact data enters the result.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from core.shipment_execution_profile import canonical_mode

VERIFIED_ID = "VERIFIED_ID"
CANDIDATE_REVIEW = "CANDIDATE_REVIEW"
CONFLICT = "CONFLICT"
UNRESOLVED = "UNRESOLVED"
BUCKETS = (VERIFIED_ID, CANDIDATE_REVIEW, CONFLICT, UNRESOLVED)


def _literal(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


@dataclass(frozen=True)
class LinkAssessment:
    shipment_id: str
    bucket: str
    confirmed_customer_id: str | None
    candidate_customer_id: str | None
    transport_mode: str
    reason_codes: tuple[str, ...]

    @property
    def linked_by_id(self) -> bool:
        """A verified ID is safe for identity checks, NOT publication approval."""
        return self.bucket == VERIFIED_ID


@dataclass(frozen=True)
class CustomerIndex:
    by_id: Mapping[str, tuple[Mapping[str, Any], ...]]
    by_name: Mapping[str, tuple[Mapping[str, Any], ...]]


def index_customers(customers: Iterable[Mapping[str, Any]]) -> CustomerIndex:
    ids: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    names: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for customer in customers:
        if not isinstance(customer, Mapping) or customer.get("is_deleted") is True:
            continue
        customer_id, name = _literal(customer.get("id")), _literal(customer.get("name"))
        if customer_id:
            ids[customer_id].append(customer)
        if name:
            names[name].append(customer)
    return CustomerIndex(
        by_id={key: tuple(rows) for key, rows in ids.items()},
        by_name={key: tuple(rows) for key, rows in names.items()},
    )


def _mode(shipment: Mapping[str, Any]) -> str:
    data = shipment.get("data")
    header = data.get("0.0") if isinstance(data, Mapping) else None
    raw = header.get("mode") if isinstance(header, Mapping) else None
    return canonical_mode(raw) or "UNKNOWN"


def assess_customer_link(shipment: Mapping[str, Any], index: CustomerIndex) -> LinkAssessment:
    """Classify only. No name-based auto-binding, persistence or public grants."""
    raw_id = _literal(shipment.get("id"))
    alternate = _literal(shipment.get("shipment_id"))
    shipment_id = raw_id or alternate
    mode = _mode(shipment)
    problems: list[str] = []
    if mode == "UNKNOWN":
        problems.append("MODE_UNKNOWN")

    def decision(bucket: str, confirmed: str | None = None,
                 candidate: str | None = None, reason: str | None = None) -> LinkAssessment:
        codes = tuple(problems + ([reason] if reason else []))
        return LinkAssessment(shipment_id, bucket, confirmed, candidate, mode, codes)

    if shipment.get("is_deleted") is True:
        return decision(UNRESOLVED, reason="SHIPMENT_DELETED")
    if not shipment_id:
        return decision(UNRESOLVED, reason="SHIPMENT_ID_MISSING")
    if raw_id and alternate and raw_id != alternate:
        return decision(CONFLICT, reason="SHIPMENT_ID_MISMATCH")

    primary, secondary = _literal(shipment.get("customer")), _literal(shipment.get("client"))
    if primary and secondary and primary != secondary:
        return decision(CONFLICT, reason="CACHED_CUSTOMER_NAMES_DIFFER")
    display_name = primary or secondary or _literal(shipment.get("customer_name"))

    declared_id = _literal(shipment.get("customer_id"))
    if declared_id:
        matched = index.by_id.get(declared_id, ())
        if len(matched) != 1:
            return decision(CONFLICT, reason="CUSTOMER_ID_NOT_UNIQUE_OR_NOT_FOUND")
        # An old legal/display name is acceptable, but an exact name pointing
        # at ANOTHER existing customer is a hard conflict, not an override.
        if display_name:
            name_matches = index.by_name.get(display_name, ())
            if len(name_matches) > 1:
                return decision(CONFLICT, reason="CUSTOMER_NAME_AMBIGUOUS")
            if len(name_matches) == 1 and _literal(name_matches[0].get("id")) != declared_id:
                return decision(CONFLICT, reason="CUSTOMER_ID_AND_NAME_DISAGREE")
            if display_name != _literal(matched[0].get("name")):
                problems.append("CACHED_NAME_STALE")
        return decision(VERIFIED_ID, confirmed=declared_id)

    if not display_name:
        return decision(UNRESOLVED, reason="NO_CUSTOMER_REFERENCE")
    matches = index.by_name.get(display_name, ())
    if len(matches) > 1:
        return decision(CONFLICT, reason="CUSTOMER_NAME_AMBIGUOUS")
    if len(matches) != 1:
        return decision(UNRESOLVED, reason="NAME_NOT_FOUND")
    candidate = _literal(matches[0].get("id"))
    if not candidate or len(index.by_id.get(candidate, ())) != 1:
        return decision(CONFLICT, reason="CANDIDATE_ID_INVALID")
    return decision(CANDIDATE_REVIEW, candidate=candidate, reason="NAME_ONLY_REQUIRES_REVIEW")


def assess_shipments(shipments: Iterable[Mapping[str, Any]],
                     customers: Iterable[Mapping[str, Any]]) -> tuple[LinkAssessment, ...]:
    index = index_customers(customers)
    return tuple(assess_customer_link(shipment, index) for shipment in shipments)


def summarize_assessments(assessments: Iterable[LinkAssessment]) -> dict[str, Any]:
    """Aggregate-only output, safe for a shared G0/G1 evidence report."""
    rows = tuple(assessments)
    buckets = Counter(item.bucket for item in rows)
    modes = Counter(item.transport_mode for item in rows)
    reasons = Counter(code for row in rows for code in row.reason_codes)
    return {
        "total": len(rows),
        "buckets": {bucket: buckets[bucket] for bucket in BUCKETS},
        "modes": {mode: modes[mode] for mode in ("ROAD", "SEA", "AIR", "RAIL", "UNKNOWN")},
        "reason_counts": dict(sorted(reasons.items())),
        "auto_link_operations": 0,
    }
