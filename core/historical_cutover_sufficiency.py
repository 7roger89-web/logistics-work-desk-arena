"""Deterministic LOG-C06 opening-impact and cutover-sufficiency analysis.

This module consumes staging dictionaries and returns derived evidence only.
It never changes review status, writes staging data, publishes an opening, or
touches the canonical ledger.  The purpose is to distinguish historical rows
that are still unresolved from rows that can actually change the verified
opening position.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping
from unicodedata import combining, normalize as unicode_normalize

from core.historical_owner_reconciliation import (
    CHECKPOINT_COMPONENT_ROWS,
    CHECKPOINT_SOURCE_ROW,
    CREDIT_SOURCE_ROW,
    FULL_PAID_ON_BEHALF_AMOUNT,
    PAID_GROUP_KEY,
    RECEIVED_GROUP_EXPECTED_AMOUNT,
    RECEIVED_GROUP_ROWS,
    SHIPMENT_COST_EXPECTED_AMOUNT,
    SNAPSHOT_AMOUNT,
)
from core.log_c06_p6_reconciliation import (
    build_p6_reconciliation,
    is_verified_goods_detail_reference,
)


SUFFICIENCY_VERSION = "log-c06-cutover-sufficiency-v1"
VERIFIED_SOURCE_HASH = "857db72b86220a4af302c0de6900710c49f44b2223c458c009748dd767840b70"
VERIFIED_BASE_AMOUNT = Decimal("161576.5473994435")
VERIFIED_BASE_CURRENCY = "CNY"
KNOWN_BASE_SOURCE_AS_OF = date(2026, 5, 28)
SNAPSHOT_AS_OF = date(2026, 3, 25)
PAID_GROUP_LATEST_DATE = date(2026, 3, 21)
RECEIVED_GROUP_LATEST_SOURCE_ROW = 200
SOURCE_RANGE = "Sheet2!A1:Z282"

CATEGORY_EMBEDDED = "EMBEDDED_IN_VERIFIED_BASE"
CATEGORY_POST_CONFIRMED = "POST_BASE_CONFIRMED"
CATEGORY_POST_REVIEW = "POST_BASE_REVIEW_REQUIRED"
CATEGORY_REFERENCE = "REFERENCE_ONLY"
CATEGORY_NOT_APPLICABLE = "NOT_APPLICABLE"
CATEGORY_NON_MATERIAL = "UNRESOLVED_NON_MATERIAL"
CATEGORY_MATERIAL = "UNRESOLVED_MATERIAL"
CATEGORIES = (
    CATEGORY_EMBEDDED,
    CATEGORY_POST_CONFIRMED,
    CATEGORY_POST_REVIEW,
    CATEGORY_REFERENCE,
    CATEGORY_NOT_APPLICABLE,
    CATEGORY_NON_MATERIAL,
    CATEGORY_MATERIAL,
)

# The source workbook has several independent tables.  These columns are the
# structured SALE columns observed in the source headers; free-text notes are
# deliberately not used as a SALE confirmation signal.
STRUCTURED_SALE_COLUMNS = (
    (1, 83, "C"),
    (88, 131, "H"),
    (134, 147, "M"),
    (149, 175, "N"),
    (177, 184, "L"),
    (211, 236, "O"),
)

# These are source summaries or section markers.  They are evidence about
# other rows and never become opening events themselves.
REFERENCE_ROWS = frozenset(
    {
        9,
        10,
        11,
        17,
        22,
        23,
        27,
        36,
        37,
        50,
        51,
        65,
        66,
        75,
        76,
        77,
        84,
        85,
        86,
        89,
        90,
        91,
        127,
        129,
        130,
        145,
        146,
        147,
        161,
        162,
        163,
        164,
        173,
        174,
        175,
        181,
        182,
        183,
        184,
        185,
        186,
        187,
        188,
        189,
        207,
        210,
        211,
        223,
        224,
        225,
        226,
        232,
        233,
        234,
        235,
        236,
        237,
        238,
        239,
        240,
        242,
        245,
        246,
        259,
    }
)

# Total columns for structured freight tables.  When a total is not present,
# the source amount remains unresolved rather than being inferred from a
# goods-price column.
FREIGHT_TOTAL_COLUMNS = (
    (134, 147, "K"),
    (149, 164, "L"),
    (166, 175, "L"),
    (177, 184, "J"),
    (211, 236, "N"),
)

# Rows immediately after the verified received-source boundary are in the
# same received-money table and have known CNY conversion amounts but no
# structured SALE/owner field.  They are potential post-base events, not
# automatic inclusions.
POST_BASE_RECEIVED_CANDIDATE_ROWS = frozenset({201, 202, 203, 204, 205})

# The received group is confirmed by physical rows 192/199/200, while the
# historical oracle labels remain C190/C197/C198.  This set is the complete
# source-component lineage already represented by the verified base.
EXPLICIT_BASE_COMPONENT_ROWS = frozenset(
    {
        CREDIT_SOURCE_ROW,
        99,
        102,
        103,
        104,
        105,
        106,
        107,
        108,
        109,
        111,
        114,
        115,
        116,
        120,
        121,
        192,
        199,
        200,
    }
)


def _decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool) or value == "":
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return result if result.is_finite() else None


def _row(item: Mapping[str, Any]) -> int:
    try:
        return int(item.get("source_row") or 0)
    except (TypeError, ValueError):
        return 0


def _proposal(item: Mapping[str, Any]) -> Mapping[str, Any]:
    value = item.get("proposal")
    return value if isinstance(value, Mapping) else {}


def _amount(item: Mapping[str, Any]) -> Decimal | None:
    proposal = _proposal(item)
    return _decimal(proposal.get("amount", item.get("raw_amount")))


def _currency(item: Mapping[str, Any]) -> str:
    proposal = _proposal(item)
    return str(proposal.get("currency") or item.get("raw_currency") or "UNKNOWN").upper()


def _date_for(item: Mapping[str, Any]) -> date | None:
    raw = item.get("raw_date") or item.get("inherited_date_context")
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def _ascii_token(value: Any) -> str:
    text = unicode_normalize("NFKD", str(value or ""))
    return "".join(char for char in text if not combining(char)).casefold().strip()


def _source_values(item: Mapping[str, Any]) -> Mapping[str, Any]:
    values = item.get("raw_values")
    return values if isinstance(values, Mapping) else {}


def _cell_value(item: Mapping[str, Any], column: str) -> Any:
    """Read a source cell while respecting the staging row-number offset."""

    values = _source_values(item)
    source_row = _row(item)
    # Historical staging retains the workbook row in raw_values while its
    # deterministic source_row is offset for the parser's section model.
    for candidate_row in (source_row + 1, source_row, source_row - 1):
        if candidate_row < 1:
            continue
        key = f"{column}{candidate_row}"
        if key in values and values[key] not in (None, ""):
            return values[key]
    return None


def _structured_sale_column(source_row: int) -> str | None:
    for first, last, column in STRUCTURED_SALE_COLUMNS:
        if first <= source_row <= last:
            return column
    return None


def _structured_sale_value(item: Mapping[str, Any]) -> str | None:
    source_row = _row(item)
    column = _structured_sale_column(source_row)
    if not column:
        return None
    value = _cell_value(item, column)
    if value in (None, ""):
        return None
    return str(value).strip()


def _structured_sale_is_thanh(item: Mapping[str, Any]) -> bool:
    return _ascii_token(_structured_sale_value(item)) == "thanh"


def _structured_sale_is_other(item: Mapping[str, Any]) -> bool:
    value = _structured_sale_value(item)
    return value not in (None, "") and not _structured_sale_is_thanh(item)


def _freight_total(item: Mapping[str, Any]) -> Decimal | None:
    source_row = _row(item)
    values = _source_values(item)
    for first, last, column in FREIGHT_TOTAL_COLUMNS:
        if first <= source_row <= last:
            return _decimal(_cell_value(item, column))
    return None


def _source_amount(item: Mapping[str, Any]) -> tuple[Decimal | None, str]:
    freight_total = _freight_total(item)
    if freight_total is not None:
        return freight_total, "structured_freight_total_cell"
    amount = _amount(item)
    return amount, "staged_normalized_amount"


def _is_summary_or_checkpoint(item: Mapping[str, Any]) -> bool:
    source_row = _row(item)
    proposal = _proposal(item)
    if source_row in REFERENCE_ROWS:
        return True
    if proposal.get("checkpoint_key") or proposal.get("reconciliation_role") in {
        "summary_checkpoint",
        "snapshot_checkpoint",
    }:
        return True
    if proposal.get("event_type") == "adjustment":
        return True
    text = _ascii_token(item.get("raw_text") or "")
    return any(marker in text for marker in ("tong", "cong no", "cn t", "phi hang tap"))


def _is_source_hash_known(items: list[Mapping[str, Any]]) -> bool:
    hashes = {str(item.get("source_file_hash") or "").lower() for item in items}
    return VERIFIED_SOURCE_HASH in hashes


def _is_pre_base_snapshot_component(item: Mapping[str, Any]) -> bool:
    source_row = _row(item)
    if source_row in EXPLICIT_BASE_COMPONENT_ROWS:
        return True
    # The workbook's E86 checkpoint is E77 + E85.  Explicit SALE=Thành rows
    # before row 86 are therefore pre-base source components of the cumulative
    # snapshot lineage, not post-base events.
    return 1 <= source_row < 86 and _structured_sale_is_thanh(item)


def _category_for(
    item: Mapping[str, Any],
    *,
    source_hash_known: bool = False,
) -> tuple[str, str]:
    source_row = _row(item)
    status = str(item.get("review_status") or "RAW")
    amount, amount_basis = _source_amount(item)

    if _is_pre_base_snapshot_component(item):
        return CATEGORY_EMBEDDED, "Pre-base source component represented by the verified snapshot/component lineage."
    if _is_summary_or_checkpoint(item):
        return CATEGORY_REFERENCE, "Checkpoint, subtotal, section marker, or derived representation; not a new money event."

    # P6 source reconstruction proves that rows 213–219 are goods-detail
    # lines.  Their H values are goods amount/THANH TIEN, H224 is the exact
    # subtotal, and no row-level freight total exists.  Keep the operational
    # evidence visible, but do not escalate it as an opening blocker.
    if source_hash_known and is_verified_goods_detail_reference(item):
        return CATEGORY_REFERENCE, (
            "Verified P6 goods-detail row: H is goods value, H213:H219 rolls to "
            "the H224 subtotal, and no A Bo freight amount is established."
        )

    post_base = source_row > RECEIVED_GROUP_LATEST_SOURCE_ROW or (
        _date_for(item) is not None and _date_for(item) > KNOWN_BASE_SOURCE_AS_OF
    )
    structured_thanh = _structured_sale_is_thanh(item)
    structured_other = _structured_sale_is_other(item)

    if post_base and status == "CONFIRMED":
        return CATEGORY_POST_CONFIRMED, "Confirmed event after the known received-group source boundary."
    if post_base and (structured_thanh or source_row in POST_BASE_RECEIVED_CANDIDATE_ROWS):
        # In freight tables, staged_normalized_amount may be weight, volume,
        # or goods value.  Only the dedicated freight-total cell is an amount
        # basis for the A Bò opening; an absent total is still material but
        # must not be fabricated from an operational goods column.
        if structured_thanh and _freight_total(item) is None:
            return CATEGORY_MATERIAL, (
                "Post-base SALE Thành shipment row has no structured freight total; "
                "goods/weight fields cannot be used as an A Bò amount."
            )
        if amount is None or amount == 0:
            return CATEGORY_MATERIAL, "Post-base structured SALE/received row has no reliable positive amount basis."
        return CATEGORY_POST_REVIEW, (
            "Post-base amount-bearing row may change the opening; source ownership/allocation is not confirmed."
        )
    if status == "NOT_APPLICABLE" or structured_other:
        return CATEGORY_NOT_APPLICABLE, "Structured source evidence places the row outside SALE Thành ↔ A Bò."

    # Explicit SALE=Thành freight rows between the snapshot and the known
    # received boundary are material until the 418,060.79 checkpoint is mapped
    # to a source range/date.  They cannot be silently called embedded.
    if structured_thanh and source_row > 129 and source_row <= RECEIVED_GROUP_LATEST_SOURCE_ROW:
        return CATEGORY_MATERIAL, (
            "SALE Thành freight row is financially relevant, but inclusion in the 418,060.79 cost checkpoint is not proven."
        )
    if status == "RAW" and amount is None:
        return CATEGORY_NON_MATERIAL, "No amount-bearing financial evidence for the opening."
    if source_row == 96:
        return CATEGORY_NON_MATERIAL, (
            "Owner-preserved exclusion; pre-base inherited-date row is not in the verified component lineage."
        )
    return CATEGORY_NON_MATERIAL, (
        "Historical row remains unresolved, but no structured SALE Thành/A Bò financial relationship proves an opening effect."
    )


def _date_text(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _item_evidence(item: Mapping[str, Any], category: str, reason: str) -> dict[str, Any]:
    source_row = _row(item)
    amount, amount_basis = _source_amount(item)
    if category == CATEGORY_MATERIAL and _structured_sale_is_thanh(item) and _freight_total(item) is None:
        # Preserve the unresolved financial possibility without reporting a
        # goods/weight value as if it were an A Bò money amount.
        amount = None
        amount_basis = "no_reliable_freight_total"
    if category == CATEGORY_REFERENCE and is_verified_goods_detail_reference(item):
        # A goods-value subtotal must never appear as a financial amount in
        # the opening-impact aggregation, even though the source value is
        # preserved in the separate P6 source reconstruction.
        amount = None
        amount_basis = "operational_goods_detail_not_financial"
    event_date = _date_for(item)
    return {
        "source_item_id": item.get("source_item_id"),
        "source_reference": item.get("source_reference") or f"Sheet2!row {source_row}",
        "source_row": source_row,
        "date": _date_text(event_date),
        "amount": float(amount) if amount is not None else None,
        "staged_amount": float(_amount(item)) if _amount(item) is not None else None,
        "amount_basis": amount_basis,
        "currency": _currency(item),
        "structured_sale": _structured_sale_value(item),
        "current_review_status": item.get("review_status") or "RAW",
        "event_type": _proposal(item).get("event_type"),
        "a_bo_relationship": _proposal(item).get("a_bo_relationship"),
        "raw_note": item.get("raw_note") or item.get("raw_text") or "",
        "category": category,
        "reason": reason,
        "financial_effect": (
            "candidate increase if A Bò paid/held for Thành"
            if category in {CATEGORY_POST_REVIEW, CATEGORY_MATERIAL}
            else "no standalone opening effect"
        ),
    }


def _amounts_by_currency(rows: Iterable[Mapping[str, Any]]) -> dict[str, float]:
    totals: defaultdict[str, Decimal] = defaultdict(Decimal)
    for row in rows:
        amount = _decimal(row.get("amount"))
        if amount is not None:
            totals[str(row.get("currency") or "UNKNOWN")] += amount
    return {currency: float(totals[currency]) for currency in sorted(totals)}


def _temporal_scope(items: list[Mapping[str, Any]]) -> dict[str, Any]:
    by_row = {_row(item): item for item in items}
    latest_received = by_row.get(RECEIVED_GROUP_LATEST_SOURCE_ROW)
    latest_received_date = _date_for(latest_received or {})
    return {
        "checkpoint_as_of": _date_text(latest_received_date or KNOWN_BASE_SOURCE_AS_OF),
        "latest_included_event": {
            "received_group": "C198 / Sheet2!C200",
            "paid_on_behalf_group": "Sheet2!D121",
            "snapshot": "Sheet2!E86",
            "shipment_cost_checkpoint": "not provable from a single workbook source cell",
        },
        "latest_included_date": {
            "received_group_source_date": _date_text(latest_received_date),
            "received_group_business_note_date": "2026-04-21",
            "paid_on_behalf_group_source_date": _date_text(PAID_GROUP_LATEST_DATE),
            "snapshot_as_of_date": _date_text(SNAPSHOT_AS_OF),
            "shipment_cost_checkpoint_date": None,
        },
        "source_range": SOURCE_RANGE,
        "component_source_rows": sorted(
            set(EXPLICIT_BASE_COMPONENT_ROWS)
            | set(CHECKPOINT_COMPONENT_ROWS)
            | {CHECKPOINT_SOURCE_ROW, 86}
            | set(RECEIVED_GROUP_ROWS)
        ),
        "temporal_confidence": "LOW",
        "scope_limitations": [
            "418,060.79 CNY is a verified checkpoint constant but has no direct cached source cell in the workbook.",
            "The physical source date 2026-05-28 and the note date 2026-04-21 are both preserved for C198.",
            "Rows after physical row 200 require post-base impact classification; they are not silently added.",
        ],
    }


def _supersession_graph() -> dict[str, Any]:
    nodes = [
        {"id": "SOURCE_24576_CNY", "kind": "source_component", "amount": 24576.0, "currency": "CNY", "event": False},
        {"id": "CHECKPOINT_99824_43_CNY", "kind": "checkpoint", "amount": float(SNAPSHOT_AMOUNT), "currency": "CNY", "event": False},
        {"id": "CHECKPOINT_134973_CNY", "kind": "checkpoint", "amount": 134973.0, "currency": "CNY", "event": False},
        {"id": "DERIVED_159998_CNY", "kind": "derived_group", "amount": float(FULL_PAID_ON_BEHALF_AMOUNT), "currency": "CNY", "event": False},
        {"id": "SUPERSEDED_M89_170374_18739944347", "kind": "superseded_checkpoint", "amount": 170374.18739944347, "currency": "CNY", "event": False},
        {"id": "CHECKPOINT_RECEIVED_416482_2426005565_CNY", "kind": "checkpoint_expectation", "amount": float(RECEIVED_GROUP_EXPECTED_AMOUNT), "currency": "CNY", "event": False},
        {"id": "CURRENT_VERIFIED_BASE_161576_5473994435_CNY", "kind": "current_verified_base", "amount": float(VERIFIED_BASE_AMOUNT), "currency": "CNY", "event": False},
    ]
    edges = [
        {"from": "SOURCE_24576_CNY", "to": "CHECKPOINT_99824_43_CNY", "relationship": "embedded_in", "counts_as_event": False},
        {"from": "CHECKPOINT_99824_43_CNY", "to": "CURRENT_VERIFIED_BASE_161576_5473994435_CNY", "relationship": "opening_lineage", "counts_as_event": False},
        {"from": "CHECKPOINT_134973_CNY", "to": "DERIVED_159998_CNY", "relationship": "summary_component_group", "counts_as_event": False},
        {"from": "DERIVED_159998_CNY", "to": "CURRENT_VERIFIED_BASE_161576_5473994435_CNY", "relationship": "positive_formula_leg", "counts_as_event": False},
        {"from": "CHECKPOINT_RECEIVED_416482_2426005565_CNY", "to": "CURRENT_VERIFIED_BASE_161576_5473994435_CNY", "relationship": "negative_formula_leg", "counts_as_event": False},
        {"from": "SUPERSEDED_M89_170374_18739944347", "to": "CURRENT_VERIFIED_BASE_161576_5473994435_CNY", "relationship": "superseded_by", "counts_as_event": False},
    ]
    return {
        "nodes": nodes,
        "edges": edges,
        "current_verified_base": "CURRENT_VERIFIED_BASE_161576_5473994435_CNY",
        "checkpoint_events_counted": 0,
        "double_count_guard": "No checkpoint, derived total, or superseded M89 snapshot is an additional event.",
    }


def _post_base_pack(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pack: list[dict[str, Any]] = []
    for row in rows:
        pack.append(
            {
                "source_row": row["source_row"],
                "category": row["category"],
                "business_date": row["date"],
                "amount": row["amount"],
                "currency": row["currency"],
                "explicit_sale": row["structured_sale"],
                "event_type": row["event_type"],
                "a_bo_relationship": row["a_bo_relationship"],
                "review_status": row["current_review_status"],
                "financial_effect": row["financial_effect"],
                "already_embedded": row["category"] == CATEGORY_EMBEDDED,
                "raw_note": row["raw_note"],
                "why_material": row["reason"],
                "recommended_interpretation": "Do not include until Owner confirms that this is a SALE Thành ↔ A Bò financial leg and identifies the amount basis.",
                "effect_if_option_a": "Add the confirmed opening-currency amount once as a post-base A Bò-paid/held cost or receipt leg.",
                "effect_if_option_b": "Exclude as another sale/receipt or reference-only source; candidate opening remains unchanged.",
            }
        )
    return pack


def build_cutover_sufficiency(items: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Return deterministic opening-impact classification for every staging row."""

    rows = [dict(item) for item in items]
    source_hash_known = _is_source_hash_known(rows)
    classified: list[dict[str, Any]] = []
    for item in rows:
        category, reason = _category_for(item, source_hash_known=source_hash_known)
        classified.append(_item_evidence(item, category, reason))
    classified.sort(key=lambda item: (int(item.get("source_row") or 0), str(item.get("source_item_id") or "")))

    counts = Counter(str(row["category"]) for row in classified)
    category_counts = {category: int(counts.get(category, 0)) for category in CATEGORIES}
    category_amounts = {
        category: _amounts_by_currency(row for row in classified if row["category"] == category)
        for category in CATEGORIES
    }
    post_base_confirmed = [row for row in classified if row["category"] == CATEGORY_POST_CONFIRMED]
    post_base_review = [row for row in classified if row["category"] == CATEGORY_POST_REVIEW]
    unresolved_material = [row for row in classified if row["category"] == CATEGORY_MATERIAL]
    opening_material_blockers = post_base_review + unresolved_material
    material_pack = _post_base_pack(opening_material_blockers)
    p6_reconciliation = build_p6_reconciliation(rows)

    temporal = _temporal_scope(rows)
    readiness_reasons: list[str] = []
    if not source_hash_known:
        readiness_reasons.append("SOURCE_PROVENANCE_NOT_VERIFIED")
    if temporal["temporal_confidence"] != "HIGH":
        readiness_reasons.append("TEMPORAL_SCOPE_UNCERTAIN")
    if post_base_review:
        readiness_reasons.append("POST_BASE_REVIEW_REQUIRED")
    if unresolved_material:
        readiness_reasons.append("UNRESOLVED_MATERIAL_ITEMS")
    opening_material_rows = post_base_confirmed + post_base_review + unresolved_material
    if any(row.get("currency") == "UNKNOWN" for row in opening_material_rows):
        readiness_reasons.append("OPENING_CURRENCY_UNKNOWN")

    confirmed_increases = sum(
        (_decimal(row.get("amount")) or Decimal("0"))
        for row in post_base_confirmed
        if (_decimal(row.get("amount")) or Decimal("0")) > 0
    )
    confirmed_reductions = sum(
        abs(_decimal(row.get("amount")) or Decimal("0"))
        for row in post_base_confirmed
        if (_decimal(row.get("amount")) or Decimal("0")) < 0
    )
    candidate = VERIFIED_BASE_AMOUNT + confirmed_increases - confirmed_reductions
    review_status_counts = {
        status: sum(1 for item in rows if str(item.get("review_status") or "RAW") == status)
        for status in ("CONFIRMED", "REVIEW_REQUIRED", "NOT_APPLICABLE", "RAW", "REJECTED")
    }
    proposal_classification_counts = dict(
        sorted(
            Counter(
                str(_proposal(item).get("classification") or "unknown")
                for item in rows
            ).items()
        )
    )
    review_unknown_count = proposal_classification_counts.get("unknown", 0)
    return {
        "analysis_version": SUFFICIENCY_VERSION,
        "source_hash_known": source_hash_known,
        "verified_base": {
            "amount": float(VERIFIED_BASE_AMOUNT),
            "currency": VERIFIED_BASE_CURRENCY,
            "checkpoint_key": "HISTORICAL_ABO_POSITION_161576_5473994435",
            "formula": "418,060.79 + 159,998 - 416,482.2426005565 = 161,576.5473994435 CNY",
            "opening_truth": "verified base only; not published",
        },
        "temporal_scope": temporal,
        "p6_reconciliation": p6_reconciliation,
        "temporal_boundary": p6_reconciliation["temporal_boundary"],
        "supersession_graph": _supersession_graph(),
        "items": classified,
        "category_counts": category_counts,
        "category_amounts_by_currency": category_amounts,
        "review_status_counts": review_status_counts,
        "review_classification_counts": {
            "CONFIRMED": review_status_counts["CONFIRMED"],
            "REVIEW_REQUIRED": review_status_counts["REVIEW_REQUIRED"],
            "UNKNOWN": review_unknown_count,
        },
        "post_base_material_event_list": material_pack,
        "post_base_confirmed_events": post_base_confirmed,
        "post_base_review_required_events": post_base_review,
        "unresolved_material_items": unresolved_material,
        "opening_material_blocker_count": len(opening_material_blockers),
        "unresolved_material_count": len(unresolved_material),
        "candidate_opening": {
            "currency": VERIFIED_BASE_CURRENCY,
            "verified_base": float(VERIFIED_BASE_AMOUNT),
            "post_base_confirmed_increases": float(confirmed_increases),
            "post_base_confirmed_reductions": float(confirmed_reductions),
            "amount": float(candidate),
            "formula": "VERIFIED_BASE + POST_BASE_CONFIRMED_INCREASES - POST_BASE_CONFIRMED_REDUCTIONS",
            "status": "PROVISIONAL_PENDING_MATERIAL_REVIEW" if readiness_reasons else "DETERMINISTIC",
        },
        "readiness": "READY_FOR_OWNER_APPROVAL" if not readiness_reasons else "NOT_READY",
        "readiness_reasons": sorted(set(readiness_reasons)),
        "cutover_lock": "NOT_APPROVED / NOT_LIVE",
        "canonical_mutation_oracle": {
            "canonical_writes": 0,
            "canonical_collections_touched": [],
            "opening_published": False,
        },
        "owner_decision_pack": material_pack,
        "beginner_owner_decision_pack": p6_reconciliation["beginner_owner_decision_pack"],
    }


__all__ = [
    "CATEGORY_EMBEDDED",
    "CATEGORY_MATERIAL",
    "CATEGORY_NON_MATERIAL",
    "CATEGORY_NOT_APPLICABLE",
    "CATEGORY_POST_CONFIRMED",
    "CATEGORY_POST_REVIEW",
    "CATEGORY_REFERENCE",
    "CATEGORIES",
    "SUFFICIENCY_VERSION",
    "VERIFIED_BASE_AMOUNT",
    "VERIFIED_SOURCE_HASH",
    "build_cutover_sufficiency",
]
