"""Pure, read-only reconciliation helpers for the A Bò / SALE Thành desk.

This module deliberately does not import the database or Streamlit.  It turns
the canonical partner projection into business-facing explanations, review
queues, bounded search, a draft period summary, and money-location traces.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from copy import deepcopy
from datetime import date, timedelta
import json
from typing import Any

from core.utils import parse_date_optional, to_decimal


BUCKET_LABELS = {
    "payable_to_partner": "TT phải trả A Bò",
    "held_credit": "A Bò đang giữ / có credit cho TT",
    "received_on_behalf": "A Bò đã nhận hộ",
    "paid_on_behalf": "A Bò đã chi hộ",
    "unallocated": "Chưa phân bổ",
    "unknown": "Chưa xác minh",
    "restricted": "Tiền bị giới hạn",
}

REVIEW_CATEGORY_LABELS = {
    "unknown": "Chưa xác minh",
    "restricted": "Tiền bị giới hạn",
    "missing_evidence": "Thiếu chứng từ",
    "unallocated": "Chưa biết dùng / cấn vào lô nào",
    "unlinked_receipt": "Khoản nhận chưa gắn",
    "unlinked_payment": "Khoản chi chưa gắn",
    "currency_mismatch": "Lệch tiền tệ",
    "legacy": "Khoản lịch sử chờ mapping",
}


def _currency(row: Mapping[str, Any]) -> str:
    return str(row.get("currency") or "UNKNOWN").strip().upper()


def _row_id(row: Mapping[str, Any]) -> str:
    return str(
        row.get("record_id")
        or row.get("obligation_id")
        or row.get("transaction_id")
        or row.get("allocation_id")
        or ""
    )


def _number(value: Any) -> str:
    amount = float(to_decimal(value))
    if amount.is_integer():
        return f"{int(amount):,}"
    return f"{amount:,.2f}".rstrip("0").rstrip(".")


def _row_amount(row: Mapping[str, Any], bucket: str | None = None) -> float:
    if bucket == "payable_to_partner":
        return float(to_decimal(row.get("outstanding")))
    if bucket == "received_on_behalf":
        return float(to_decimal(row.get("received_amount", row.get("amount"))))
    if bucket == "paid_on_behalf":
        return float(to_decimal(row.get("spent_amount", row.get("amount"))))
    return float(
        to_decimal(
            row.get(
                "unallocated",
                row.get("outstanding", row.get("amount")),
            )
        )
    )


def _row_date(row: Mapping[str, Any]) -> date | None:
    for key in ("occurred_at", "created_at", "due_date"):
        parsed = parse_date_optional(row.get(key))
        if parsed is not None:
            return parsed
    return None


def _in_period(value: date | None, start: date, end: date) -> bool:
    return value is not None and start <= value <= end


def _party_label(value: Any) -> str:
    if isinstance(value, Mapping):
        return str(value.get("name") or value.get("party_id") or value.get("key") or "Chưa rõ")
    return str(value or "Chưa rõ")


def _unique_ids(rows: Iterable[Mapping[str, Any]]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for value in row.get("source_record_ids") or [_row_id(row)]:
            token = str(value or "").strip()
            if token and token not in seen:
                seen.add(token)
                result.append(token)
    return result


def _all_bucket_rows(position: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    buckets = position.get("buckets") or {}
    for bucket in BUCKET_LABELS:
        for raw in buckets.get(bucket) or []:
            if not isinstance(raw, Mapping):
                continue
            row = deepcopy(dict(raw))
            row.setdefault("bucket", bucket)
            key = (str(row.get("bucket") or bucket), _row_id(row))
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


def build_currency_explanation(position: Mapping[str, Any], currency: str) -> dict[str, Any]:
    """Explain the confirmed position for one currency from source rows only."""

    currency = str(currency or "UNKNOWN").strip().upper()
    buckets = position.get("buckets") or {}
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []

    for bucket in ("payable_to_partner", "held_credit"):
        for raw in buckets.get(bucket) or []:
            if not isinstance(raw, Mapping) or _currency(raw) != currency:
                continue
            amount = _row_amount(raw, bucket)
            sign = "+" if bucket == "payable_to_partner" else "-"
            included.append(
                {
                    "bucket": bucket,
                    "label": BUCKET_LABELS[bucket],
                    "sign": sign,
                    "amount": amount,
                    "signed_amount": amount if sign == "+" else -amount,
                    "currency": currency,
                    "formula": raw.get("formula") or f"{_number(amount)} {currency}",
                    "source_record_ids": list(raw.get("source_record_ids") or [_row_id(raw)]),
                    "excluded_from_confirmed": False,
                }
            )

    for bucket in ("unknown", "restricted"):
        for raw in buckets.get(bucket) or []:
            if not isinstance(raw, Mapping) or _currency(raw) != currency:
                continue
            amount = _row_amount(raw, bucket)
            excluded.append(
                {
                    "bucket": bucket,
                    "label": BUCKET_LABELS[bucket],
                    "sign": "?",
                    "amount": amount,
                    "signed_amount": 0.0,
                    "currency": currency,
                    "formula": raw.get("formula") or f"{_number(amount)} {currency}",
                    "source_record_ids": list(raw.get("source_record_ids") or [_row_id(raw)]),
                    "excluded_from_confirmed": True,
                    "review_reason": raw.get("review_reason") or "Cần đối soát",
                }
            )

    included.sort(key=lambda item: (item["bucket"], item["source_record_ids"]))
    excluded.sort(key=lambda item: (item["bucket"], item["source_record_ids"]))
    confirmed_total = sum(to_decimal(item["signed_amount"]) for item in included)
    excluded_total = sum(to_decimal(item["amount"]) for item in excluded)
    terms = [
        f"{item['sign']} {_number(item['amount'])} {currency} · {item['label']}"
        for item in included
    ]
    formula = " ".join(terms) if terms else f"0 {currency}"
    formula = f"{formula} = {_number(confirmed_total)} {currency}"
    return {
        "currency": currency,
        "label": "Vì sao ra số này?",
        "lines": included,
        "excluded_lines": excluded,
        "confirmed_total": float(confirmed_total),
        "excluded_total": float(excluded_total),
        "formula": formula,
        "source_record_ids": _unique_ids([*included, *excluded]),
        "deterministic": True,
    }


def build_all_currency_explanations(position: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    currencies = set((position.get("totals_by_currency") or {}).keys())
    for row in _all_bucket_rows(position):
        currencies.add(_currency(row))
    return {
        currency: build_currency_explanation(position, currency)
        for currency in sorted(currency for currency in currencies if currency)
    }


def _review_category(row: Mapping[str, Any], bucket: str) -> str:
    reason = str(row.get("review_reason") or "").lower()
    if bucket == "restricted" or "restrict" in reason:
        return "restricted"
    if "currency" in reason or "tiền tệ" in reason:
        return "currency_mismatch"
    if not (
        row.get("evidence_refs")
        or row.get("source_refs")
        or row.get("provenance")
    ):
        return "missing_evidence"
    if "classification" in reason or bucket == "unknown":
        return "unknown"
    if "allocation" in reason or row.get("unallocated", 0) > 0:
        if str(row.get("transaction_kind") or "").lower() in {
            "received_on_behalf",
            "received_for_beneficiary",
        }:
            return "unlinked_receipt"
        return "unallocated"
    return "legacy"


def build_review_inbox(position: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return only rows that need an actual review decision."""

    inbox: list[dict[str, Any]] = []
    buckets = position.get("buckets") or {}
    for bucket in ("unknown", "restricted"):
        for raw in buckets.get(bucket) or []:
            if not isinstance(raw, Mapping):
                continue
            row = deepcopy(dict(raw))
            category = _review_category(row, bucket)
            row["review_category"] = category
            row["review_label"] = REVIEW_CATEGORY_LABELS[category]
            row["excluded_from_confirmed"] = True
            inbox.append(row)
    inbox.sort(key=lambda row: (_currency(row), row.get("review_category", ""), _row_id(row)))
    return inbox


def search_partner_position(position: Mapping[str, Any], term: str) -> list[dict[str, Any]]:
    """Search the bounded partner desk surface, not the whole enterprise app."""

    query = str(term or "").strip().casefold()
    if not query:
        return []
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in _all_bucket_rows(position):
        serialized = json.dumps(row, ensure_ascii=False, sort_keys=True, default=str).casefold()
        if query not in serialized:
            continue
        row_id = _row_id(row)
        if row_id and row_id in seen:
            continue
        if row_id:
            seen.add(row_id)
        row["matched_query"] = term
        result.append(row)
    result.sort(key=lambda row: (_currency(row), _row_id(row)))
    return result


def build_money_location_trace(row: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic source → holder → beneficiary → allocation trace."""

    record_type = str(row.get("record_type") or "transaction")
    steps: list[dict[str, Any]] = []
    if record_type == "obligation":
        steps.append(
            {
                "from": _party_label(row.get("from_party")),
                "to": _party_label(row.get("to_party")),
                "label": "Nghĩa vụ TT phải trả A Bò",
            }
        )
    else:
        source = _party_label(row.get("source_party"))
        holder = _party_label(row.get("holder_party"))
        beneficial = _party_label(row.get("beneficial_owner"))
        if source != "Chưa rõ" or holder != "Chưa rõ":
            steps.append({"from": source, "to": holder, "label": "Luồng tiền ban đầu"})
        if beneficial != "Chưa rõ" and beneficial != holder:
            steps.append({"from": holder, "to": beneficial, "label": "Chủ sở hữu hưởng lợi"})

    allocation_history = [
        deepcopy(dict(item))
        for item in row.get("allocation_history") or []
        if isinstance(item, Mapping)
    ]
    for allocation in allocation_history:
        shipment_ids = [str(value) for value in allocation.get("shipment_ids") or [] if str(value)]
        destination = ", ".join(shipment_ids) or str(allocation.get("obligation_id") or "chưa gắn lô")
        steps.append(
            {
                "from": "Số tiền đang theo dõi",
                "to": destination,
                "label": f"Đã phân bổ {_number(allocation.get('amount'))} {_currency(allocation)}",
                "allocation_id": allocation.get("id"),
            }
        )

    remaining = row.get("unallocated", row.get("remaining_unallocated", row.get("outstanding", 0)))
    remaining_value = float(to_decimal(remaining))
    if remaining_value > 0:
        holder = _party_label(row.get("holder_party"))
        location = f"{holder} đang giữ — còn {_number(remaining_value)} {_currency(row)} chưa phân bổ"
        steps.append({"from": holder, "to": "Chưa phân bổ", "label": location})
    elif record_type == "transaction" and allocation_history:
        steps.append({"from": "Số tiền đang theo dõi", "to": "Đã cấn hết", "label": "Đã phân bổ hết"})

    return {
        "record_id": _row_id(row),
        "record_type": record_type,
        "currency": _currency(row),
        "amount": float(to_decimal(row.get("amount"))),
        "remaining": remaining_value,
        "steps": steps,
        "allocation_history": allocation_history,
        "source_record_ids": list(row.get("source_record_ids") or [_row_id(row)]),
        "evidence_refs": deepcopy(row.get("evidence_refs") or []),
        "source_refs": deepcopy(row.get("source_refs") or []),
        "provenance": deepcopy(row.get("provenance") or {}),
        "deterministic": True,
    }


def compare_reported_position(
    position: Mapping[str, Any], reported_by_currency: Mapping[str, Any]
) -> dict[str, Any]:
    """Compare a partner-reported amount without guessing a correction."""

    system_by_currency = position.get("net_position_by_currency") or {}
    currencies = sorted(
        {str(key).upper() for key in system_by_currency}
        | {str(key).upper() for key in (reported_by_currency or {})}
    )
    comparisons: list[dict[str, Any]] = []
    buckets = position.get("buckets") or {}
    for currency in currencies:
        system = to_decimal(system_by_currency.get(currency, 0))
        reported = to_decimal(
            (reported_by_currency or {}).get(currency, (reported_by_currency or {}).get(currency.lower(), 0))
        )
        difference = system - reported
        categories: list[str] = []
        if difference:
            if any(_currency(row) == currency for row in buckets.get("unallocated") or []):
                categories.append("unallocated")
            if any(_currency(row) == currency for row in buckets.get("unknown") or []):
                categories.append("unknown")
            if any(
                _currency(row) == currency
                and not (row.get("evidence_refs") or row.get("source_refs") or row.get("provenance"))
                for row in build_review_inbox(position)
            ):
                categories.append("missing_evidence")
            if any(_currency(row) == currency for row in buckets.get("received_on_behalf") or []):
                categories.append("unlinked_receipt")
            if any(_currency(row) == currency for row in buckets.get("paid_on_behalf") or []):
                categories.append("unlinked_payment")
            if any(_currency(row) == currency for row in buckets.get("restricted") or []):
                categories.append("restricted")
            if len(currencies) > 1 and currency not in system_by_currency:
                categories.append("currency_mismatch")
        comparisons.append(
            {
                "currency": currency,
                "system_confirmed": float(system),
                "partner_reported": float(reported),
                "difference": float(difference),
                "candidate_unmatched_categories": list(dict.fromkeys(categories)),
                "deterministic": True,
            }
        )
    return {
        "comparisons": comparisons,
        "has_difference": any(item["difference"] != 0 for item in comparisons),
        "rule_based": True,
    }


def _allocation_rows_in_period(row: Mapping[str, Any], start: date, end: date) -> list[Mapping[str, Any]]:
    return [
        allocation
        for allocation in row.get("allocation_history") or []
        if isinstance(allocation, Mapping) and _in_period(_row_date(allocation), start, end)
    ]


def build_period_reconciliation(
    position: Mapping[str, Any],
    start: date,
    end: date,
) -> dict[str, Any]:
    """Create a bounded, explicitly draft period summary.

    The canonical current position remains authoritative.  The movement lines
    are independently derived from dated source rows and are accompanied by a
    draft difference when the available history cannot balance without review.
    """

    if start > end:
        raise ValueError("period start must be on or before period end")
    rows = _all_bucket_rows(position)
    currencies = set((position.get("totals_by_currency") or {}).keys())
    currencies.update(_currency(row) for row in rows)
    by_currency: dict[str, dict[str, Any]] = {}
    for currency in sorted(value for value in currencies if value):
        opening = 0.0
        new_obligations = 0.0
        payments = 0.0
        received_on_behalf = 0.0
        held_funds = 0.0
        allocations_netting = 0.0
        reversals_corrections = 0.0
        counted_allocation_ids: set[str] = set()
        for row in rows:
            if _currency(row) != currency:
                continue
            row_date = _row_date(row)
            bucket = str(row.get("bucket") or "")
            amount = _row_amount(row, bucket)
            if row_date is not None and row_date < start:
                if bucket == "payable_to_partner":
                    opening += amount
                elif bucket == "held_credit":
                    opening -= amount
            if _in_period(row_date, start, end):
                if bucket == "payable_to_partner":
                    new_obligations += amount
                elif bucket == "paid_on_behalf":
                    payments += amount
                elif bucket == "received_on_behalf":
                    received_on_behalf -= amount
                elif bucket == "held_credit":
                    held_funds -= amount
            for allocation in _allocation_rows_in_period(row, start, end):
                if _currency(allocation) != currency:
                    continue
                allocation_id = str(allocation.get("id") or "")
                if allocation_id and allocation_id in counted_allocation_ids:
                    continue
                if allocation_id:
                    counted_allocation_ids.add(allocation_id)
                allocations_netting -= float(to_decimal(allocation.get("amount")))

        current = float(to_decimal((position.get("net_position_by_currency") or {}).get(currency, 0)))
        draft_current = (
            opening
            + new_obligations
            + payments
            + received_on_behalf
            + held_funds
            + allocations_netting
            + reversals_corrections
        )
        by_currency[currency] = {
            "currency": currency,
            "opening_prior_position": opening,
            "new_obligations": new_obligations,
            "payments": payments,
            "received_on_behalf": received_on_behalf,
            "held_funds": held_funds,
            "allocations_netting": allocations_netting,
            "reversals_corrections": reversals_corrections,
            "draft_current_position": draft_current,
            "current_confirmed_position": current,
            "draft_difference": current - draft_current,
            "balanced": current == draft_current,
            "review_required": bool((position.get("buckets") or {}).get("unknown"))
            or bool((position.get("buckets") or {}).get("restricted"))
            or current != draft_current,
            "formula": (
                f"{_number(opening)} + {_number(new_obligations)} + {_number(payments)} + "
                f"({_number(received_on_behalf)}) + ({_number(held_funds)}) + "
                f"({_number(allocations_netting)}) + {_number(reversals_corrections)} "
                f"= {_number(draft_current)} {currency}"
            ),
        }
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "draft": True,
        "close_or_lock": False,
        "by_currency": by_currency,
        "confirmed": {
            currency: values["current_confirmed_position"]
            for currency, values in by_currency.items()
        },
        "review_required": {
            currency: values["draft_difference"]
            for currency, values in by_currency.items()
            if values["review_required"]
        },
        "deterministic": True,
        "note": "Bản nháp đối soát; vị trí confirmed vẫn lấy từ canonical ledger, không tự chốt kỳ.",
    }


__all__ = [
    "BUCKET_LABELS",
    "REVIEW_CATEGORY_LABELS",
    "build_all_currency_explanations",
    "build_currency_explanation",
    "build_money_location_trace",
    "build_period_reconciliation",
    "build_review_inbox",
    "compare_reported_position",
    "search_partner_position",
]
