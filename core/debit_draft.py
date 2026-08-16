"""Deterministic manager-report and A Bò debit-draft projections.

The functions in this module consume the canonical partner projection and
return presentation-ready data.  They never import Streamlit, MongoDB, an AI
client, or a payment service, and they never persist a derived amount.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from datetime import date
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any

from core.reconciliation import BUCKET_LABELS, REVIEW_CATEGORY_LABELS
from core.utils import to_decimal


DEBIT_STATUS_DRAFT = "DRAFT"
DEBIT_STATUS_READY_FOR_REVIEW = "READY_FOR_REVIEW"
DEBIT_STATUS_SUPERSEDED = "SUPERSEDED"
REPORT_STATUS_DRAFT = DEBIT_STATUS_DRAFT
REPORT_STATUS_READY_FOR_REVIEW = DEBIT_STATUS_READY_FOR_REVIEW

_ACTIVE_STATUSES = frozenset({"", "active", "confirmed", "open", "pending"})
_INACTIVE_STATUSES = frozenset({"reversed", "cancelled", "canceled", "void", "inactive"})
_CONFIRMED_STATES = frozenset({"", "CONFIRMED", "KNOWN", "ACTIVE", "OK"})
_REVIEW_STATES = frozenset({"UNKNOWN", "REVIEW_REQUIRED", "REVIEW", "UNCONFIRMED"})
_NONE_RESTRICTIONS = frozenset({"", "NONE", "ALLOWED", "UNRESTRICTED"})
_SETTLED_STATES = frozenset({"SETTLED", "PAID", "CANCELLED", "CANCELED", "REVERSED", "VOID"})

EXCLUSION_LABELS = {
    "unknown": "UNKNOWN / chưa xác minh",
    "restricted": "Restricted / bị giới hạn",
    "unallocated": "Chưa phân bổ hoặc chưa được duyệt",
    "missing_evidence": "Thiếu chứng từ tối thiểu",
    "currency_mismatch": "Lệch tiền tệ",
    "reversed": "Đã reverse/cancel",
    "already_settled": "Đã thanh toán hoặc đã nằm trong Debit khác",
    "owner_unknown": "Chưa xác định owner",
    "partner_difference": "Cần đối soát chênh lệch với A Bò",
    "no_outstanding": "Không còn số dư đủ điều kiện",
}


def _currency(row: Mapping[str, Any]) -> str:
    raw = str(row.get("currency") or "").strip().upper()
    return raw or "UNKNOWN"


def _row_id(row: Mapping[str, Any]) -> str:
    return str(
        row.get("record_id")
        or row.get("obligation_id")
        or row.get("transaction_id")
        or row.get("allocation_id")
        or ""
    ).strip()


def _source_record_ids(row: Mapping[str, Any]) -> list[str]:
    values = list(row.get("source_record_ids") or [])
    if not values:
        values = [_row_id(row)]
    result: list[str] = []
    for value in values:
        token = str(value or "").strip()
        if token and token not in result:
            result.append(token)
    return result


def _row_amount(row: Mapping[str, Any], bucket: str) -> Decimal:
    if bucket == "payable_to_partner":
        return to_decimal(row.get("outstanding", row.get("amount")))
    if bucket == "paid_on_behalf":
        return to_decimal(row.get("spent_amount", row.get("amount")))
    if bucket == "received_on_behalf":
        return to_decimal(row.get("allocated", 0))
    if bucket == "held_credit":
        return to_decimal(row.get("unallocated", row.get("remaining_unallocated", row.get("amount"))))
    if bucket == "unallocated":
        return to_decimal(row.get("unallocated", row.get("remaining_unallocated", row.get("amount"))))
    return to_decimal(row.get("amount"))


def _full_amount(row: Mapping[str, Any], bucket: str) -> Decimal:
    if bucket == "received_on_behalf":
        return to_decimal(row.get("received_amount", row.get("amount")))
    if bucket == "paid_on_behalf":
        return to_decimal(row.get("spent_amount", row.get("amount")))
    return to_decimal(row.get("amount", row.get("outstanding", row.get("unallocated"))))


def _row_label(row: Mapping[str, Any], bucket: str) -> str:
    return str(
        row.get("purpose")
        or row.get("note")
        or row.get("transaction_kind")
        or BUCKET_LABELS.get(bucket, bucket)
    )


def _row_shipment_ids(row: Mapping[str, Any]) -> list[str]:
    raw = row.get("shipment_ids") or []
    if isinstance(raw, str):
        raw = [raw]
    result: list[str] = []
    for value in raw:
        token = str(value or "").strip()
        if token and token not in result:
            result.append(token)
    return result


def _all_bucket_rows(position: Mapping[str, Any], bucket: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for raw in (position.get("buckets") or {}).get(bucket) or []:
        if isinstance(raw, Mapping):
            row = deepcopy(dict(raw))
            row.setdefault("bucket", bucket)
            result.append(row)
    return result


def _currencies(position: Mapping[str, Any], reported_by_currency: Mapping[str, Any] | None = None) -> list[str]:
    values: set[str] = set()
    values.update(str(key).strip().upper() for key in (position.get("totals_by_currency") or {}))
    for rows in (position.get("buckets") or {}).values():
        for row in rows or []:
            if isinstance(row, Mapping):
                values.add(_currency(row))
    for key in (reported_by_currency or {}):
        values.add(str(key).strip().upper() or "UNKNOWN")
    return sorted(value for value in values if value)


def _date_text(value: date | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _has_evidence(row: Mapping[str, Any]) -> bool:
    return bool(row.get("evidence_refs") or row.get("source_refs") or row.get("provenance"))


def _classification(row: Mapping[str, Any], bucket: str) -> str:
    value = row.get("classification_status")
    if value in (None, ""):
        value = row.get("review_status")
    if value in (None, ""):
        # The canonical projection only emits payable/confirmed buckets after
        # its own allocation/restriction checks.  Unknown/review rows are
        # still guarded by their bucket and review_reason below.
        return "CONFIRMED" if bucket not in {"unknown", "restricted"} else "UNKNOWN"
    return str(value).strip().upper()


def _restriction_status(row: Mapping[str, Any]) -> str:
    restriction = row.get("restriction")
    if isinstance(restriction, Mapping):
        value = restriction.get("status")
    else:
        value = restriction or row.get("restriction_status")
    return str(value or "NONE").strip().upper()


def _is_already_settled(row: Mapping[str, Any]) -> bool:
    if any(
        row.get(key) is True
        for key in (
            "already_settled",
            "already_included_in_debit",
            "debit_included",
            "settled_in_effective_debit",
        )
    ):
        return True
    status = str(row.get("settlement_status") or "").strip().upper()
    return status in _SETTLED_STATES


def _eligibility_reason(
    row: Mapping[str, Any],
    bucket: str,
    position: Mapping[str, Any],
    amount: Decimal,
) -> str | None:
    review_reason = str(row.get("review_reason") or "").strip().lower()
    if "currency" in review_reason or "tiền tệ" in review_reason or row.get("currency_mismatch") is True:
        return "currency_mismatch"
    if bucket == "unknown" or _classification(row, bucket) in _REVIEW_STATES:
        return "unknown"
    if bucket == "restricted" or _restriction_status(row) not in _NONE_RESTRICTIONS:
        return "restricted"
    if _currency(row) == "UNKNOWN":
        return "currency_mismatch"
    status = str(row.get("status") or "").strip().lower()
    if status in _INACTIVE_STATUSES or row.get("is_reversed") is True:
        return "reversed"
    if _is_already_settled(row):
        return "already_settled"
    requested_owner = str(position.get("internal_sale_owner") or "").strip()
    owner = str(row.get("internal_sale_owner") or "").strip()
    if not owner or (requested_owner and owner != requested_owner):
        return "owner_unknown"
    if row.get("review_reason") and bucket not in {"payable_to_partner", "paid_on_behalf"}:
        return "unknown"
    if not _has_evidence(row):
        return "missing_evidence"
    if amount <= 0:
        return "no_outstanding"
    return None


def _line(row: Mapping[str, Any], bucket: str, amount: Decimal, sign: str, label: str | None = None) -> dict[str, Any]:
    record_id = _row_id(row)
    line = {
        "bucket": bucket,
        "label": label or _row_label(row, bucket),
        "record_id": record_id,
        "obligation_id": row.get("obligation_id"),
        "transaction_id": row.get("transaction_id"),
        "allocation_ids": list(row.get("allocation_ids") or []),
        "source_record_ids": _source_record_ids(row),
        "shipment_ids": _row_shipment_ids(row),
        "currency": _currency(row),
        "amount": float(amount),
        "sign": sign,
        "signed_amount": float(amount if sign == "+" else -amount),
        "evidence_refs": deepcopy(row.get("evidence_refs") or []),
        "source_refs": deepcopy(row.get("source_refs") or []),
        "provenance": deepcopy(row.get("provenance") or {}),
        "correction_reversal_state": {
            "status": row.get("status"),
            "is_reversed": bool(row.get("is_reversed")),
            "reversed_by": row.get("reversed_by"),
            "correction_id": row.get("correction_id"),
        },
    }
    if bucket == "payable_to_partner":
        gross = to_decimal(row.get("amount"))
        outstanding = to_decimal(row.get("outstanding", amount))
        line["gross_amount"] = float(gross)
        line["settled_amount"] = float(max(gross - outstanding, Decimal("0")))
        line["allocation_ids"] = list(row.get("allocation_ids") or [])
    if bucket == "received_on_behalf":
        line["received_amount"] = float(_full_amount(row, bucket))
        line["allocated_amount"] = float(amount)
    return line


def _excluded(row: Mapping[str, Any], bucket: str, reason: str, amount: Decimal) -> dict[str, Any]:
    return {
        **_line(row, bucket, max(amount, Decimal("0")), "?", label=BUCKET_LABELS.get(bucket, bucket)),
        "category": reason,
        "reason": EXCLUSION_LABELS.get(reason, reason),
        "excluded_from_debit": True,
    }


def _append_unique(items: list[dict[str, Any]], item: dict[str, Any], seen: set[tuple[str, str, str]]) -> None:
    key = (str(item.get("bucket") or ""), str(item.get("record_id") or ""), str(item.get("category") or ""))
    if key not in seen:
        seen.add(key)
        items.append(item)


def _reference_sets(lines: Iterable[Mapping[str, Any]]) -> dict[str, list[str]]:
    references = {
        "ledger_record_ids": [],
        "obligation_ids": [],
        "transaction_ids": [],
        "allocation_ids": [],
        "correction_ids": [],
    }

    def add(name: str, value: Any) -> None:
        token = str(value or "").strip()
        if token and token not in references[name]:
            references[name].append(token)

    for line in lines:
        for value in line.get("source_record_ids") or []:
            add("ledger_record_ids", value)
        add("obligation_ids", line.get("obligation_id"))
        add("transaction_ids", line.get("transaction_id"))
        for value in line.get("allocation_ids") or []:
            add("allocation_ids", value)
        state = line.get("correction_reversal_state") or {}
        add("correction_ids", state.get("correction_id"))
        add("correction_ids", state.get("reversed_by"))
    return references


def _period_value(start: date | str | None, end: date | str | None) -> dict[str, str | None]:
    return {"start": _date_text(start), "end": _date_text(end)}


def _partner_difference(
    position: Mapping[str, Any],
    reported_by_currency: Mapping[str, Any] | None,
    confirmed_by_currency: Mapping[str, Decimal],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for currency in sorted(
        {str(key).upper() for key in confirmed_by_currency}
        | {str(key).upper() for key in (reported_by_currency or {})}
    ):
        reported = to_decimal(
            (reported_by_currency or {}).get(currency, (reported_by_currency or {}).get(currency.lower(), 0))
        )
        system = confirmed_by_currency.get(currency, Decimal("0"))
        difference = system - reported
        result.append(
            {
                "currency": currency,
                "system_confirmed": float(system),
                "partner_reported": float(reported),
                "difference": float(difference),
                "has_difference": difference != 0,
                "action": EXCLUSION_LABELS["partner_difference"] if difference else "Không có chênh lệch",
                "candidate_categories": _candidate_difference_categories(position, currency) if difference else [],
                "deterministic": True,
            }
        )
    return result


def _candidate_difference_categories(position: Mapping[str, Any], currency: str) -> list[str]:
    categories: list[str] = []
    buckets = position.get("buckets") or {}
    if any(_currency(row) == currency for row in buckets.get("unallocated") or [] if isinstance(row, Mapping)):
        categories.append("unallocated")
    if any(_currency(row) == currency for row in buckets.get("unknown") or [] if isinstance(row, Mapping)):
        categories.append("unknown")
    if any(_currency(row) == currency for row in buckets.get("restricted") or [] if isinstance(row, Mapping)):
        categories.append("restricted")
    if any(_currency(row) == currency for row in buckets.get("received_on_behalf") or [] if isinstance(row, Mapping)):
        categories.append("unlinked_receipt")
    return list(dict.fromkeys(categories))


def _build_currency_draft(
    position: Mapping[str, Any],
    currency: str,
    reported_by_currency: Mapping[str, Any] | None,
) -> dict[str, Any]:
    payable_lines: list[dict[str, Any]] = []
    credit_lines: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    excluded_seen: set[tuple[str, str, str]] = set()
    represented_ids: set[str] = set()
    payable_rows = [
        row for row in _all_bucket_rows(position, "payable_to_partner") if _currency(row) == currency
    ]
    paid_rows = [row for row in _all_bucket_rows(position, "paid_on_behalf") if _currency(row) == currency]
    held_rows = [row for row in _all_bucket_rows(position, "held_credit") if _currency(row) == currency]
    received_rows = [row for row in _all_bucket_rows(position, "received_on_behalf") if _currency(row) == currency]

    def process_payable(row: dict[str, Any], bucket: str, amount: Decimal, label: str | None = None) -> None:
        reason = _eligibility_reason(row, bucket, position, amount)
        if reason:
            _append_unique(excluded, _excluded(row, bucket, reason, amount), excluded_seen)
            return
        line = _line(row, bucket, amount, "+", label=label)
        payable_lines.append(line)
        if line.get("record_id"):
            represented_ids.add(str(line["record_id"]))

    for row in payable_rows:
        process_payable(row, "payable_to_partner", _row_amount(row, "payable_to_partner"))
    for row in paid_rows:
        process_payable(row, "paid_on_behalf", _row_amount(row, "paid_on_behalf"), label="A Bò đã chi hộ")

    def process_credit(row: dict[str, Any], bucket: str, amount: Decimal, label: str | None = None) -> None:
        reason = _eligibility_reason(row, bucket, position, amount)
        if reason:
            _append_unique(excluded, _excluded(row, bucket, reason, amount), excluded_seen)
            return
        line = _line(row, bucket, amount, "-", label=label)
        credit_lines.append(line)
        if line.get("record_id"):
            represented_ids.add(str(line["record_id"]))

    for row in held_rows:
        process_credit(row, "held_credit", _row_amount(row, "held_credit"), label="A Bò đang giữ / credit")
    for row in received_rows:
        allocated = _row_amount(row, "received_on_behalf")
        if allocated > 0:
            process_credit(row, "received_on_behalf", allocated, label="A Bò đã nhận hộ — phần đã phân bổ")

    # A row can be present in several C04 buckets because the projection keeps
    # both the full history and its remaining amount.  Only the component
    # represented by a held/received/paid line is excluded from this catch-all
    # review list; it must never be counted a second time as a debit credit.
    for row in _all_bucket_rows(position, "unallocated"):
        if _currency(row) != currency:
            continue
        if _row_id(row) in represented_ids:
            continue
        _append_unique(
            excluded,
            _excluded(row, "unallocated", "unallocated", _row_amount(row, "unallocated")),
            excluded_seen,
        )

    for bucket, reason in (("unknown", "unknown"), ("restricted", "restricted")):
        for row in _all_bucket_rows(position, bucket):
            if _currency(row) == currency:
                _append_unique(excluded, _excluded(row, bucket, reason, _row_amount(row, bucket)), excluded_seen)

    reported_difference = None
    if reported_by_currency:
        reported = to_decimal(
            reported_by_currency.get(currency, reported_by_currency.get(currency.lower(), 0))
        )
        current_confirmed = sum(to_decimal(line["signed_amount"]) for line in [*payable_lines, *credit_lines])
        difference = current_confirmed - reported
        if difference:
            reported_difference = {
                "currency": currency,
                "system_confirmed": float(current_confirmed),
                "partner_reported": float(reported),
                "difference": float(difference),
                "reason": EXCLUSION_LABELS["partner_difference"],
                "excluded_from_debit": True,
            }
            excluded.append(
                {
                    "bucket": "partner_difference",
                    "category": "partner_difference",
                    "label": "Chênh lệch A Bò báo lại",
                    "record_id": "",
                    "source_record_ids": [],
                    "shipment_ids": [],
                    "currency": currency,
                    "amount": abs(float(difference)),
                    "sign": "?",
                    "signed_amount": 0.0,
                    "reason": EXCLUSION_LABELS["partner_difference"],
                    "excluded_from_debit": True,
                }
            )

    payable_subtotal = sum(to_decimal(line["amount"]) for line in payable_lines)
    credit_subtotal = sum(to_decimal(line["amount"]) for line in credit_lines)
    debit_ready = payable_subtotal - credit_subtotal
    settled_amount = sum(to_decimal(line.get("settled_amount")) for line in payable_lines)
    received_allocated = sum(
        to_decimal(line.get("allocated_amount")) for line in credit_lines if line.get("bucket") == "received_on_behalf"
    )
    formula_lines: list[str] = []
    for line in payable_lines:
        gross_amount = to_decimal(line.get("gross_amount"))
        settled_line_amount = to_decimal(line.get("settled_amount"))
        if gross_amount > settled_line_amount > 0:
            formula_lines.append(f"+ {float(gross_amount):g} {currency} · {line['label']}")
            formula_lines.append(
                f"- {float(settled_line_amount):g} {currency} · Đã thanh toán / đã cấn"
            )
        else:
            formula_lines.append(f"+ {float(line['amount']):g} {currency} · {line['label']}")
    formula_lines.extend(
        f"- {float(line['amount']):g} {currency} · {line['label']}"
        for line in credit_lines
    )
    formula = " ".join(formula_lines) if formula_lines else f"0 {currency}"
    formula = f"{formula} = {float(debit_ready):g} {currency}"
    included = [*payable_lines, *credit_lines]
    return {
        "currency": currency,
        "payable_lines": payable_lines,
        "credit_lines": credit_lines,
        "included_items": included,
        "excluded_items": excluded,
        "payable_subtotal": float(payable_subtotal),
        "credit_subtotal": float(credit_subtotal),
        "settled_amount": float(settled_amount),
        "received_on_behalf_allocated": float(received_allocated),
        "debit_ready_amount": float(debit_ready),
        "confirmed_position": float(debit_ready),
        "formula": formula,
        "reported_difference": reported_difference,
        "references": _reference_sets([*included, *excluded]),
        "deterministic": True,
    }


def build_debit_draft(
    position: Mapping[str, Any],
    *,
    period_start: date | str | None = None,
    period_end: date | str | None = None,
    reported_by_currency: Mapping[str, Any] | None = None,
    status: str = DEBIT_STATUS_DRAFT,
) -> dict[str, Any]:
    """Build a currency-separated Debit Draft from the canonical projection."""

    status = str(status or DEBIT_STATUS_DRAFT).strip().upper()
    if status not in {DEBIT_STATUS_DRAFT, DEBIT_STATUS_READY_FOR_REVIEW, DEBIT_STATUS_SUPERSEDED}:
        raise ValueError(f"unsupported debit draft status: {status}")
    by_currency = {
        currency: _build_currency_draft(position, currency, reported_by_currency)
        for currency in _currencies(position, reported_by_currency)
    }
    references = _reference_sets(
        line
        for values in by_currency.values()
        for line in [*(values.get("included_items") or []), *(values.get("excluded_items") or [])]
    )
    return {
        "document_type": "DEBIT_A_BO",
        "title": "DEBIT A BÒ",
        "status": status,
        "period": _period_value(period_start, period_end),
        "party": deepcopy(position.get("party") or {}),
        "party_key": position.get("party_key"),
        "internal_sale_owner": position.get("internal_sale_owner"),
        "currencies": list(by_currency),
        "by_currency": by_currency,
        "references": references,
        "read_only": True,
        "financial_effect_write_count": 0,
        "deterministic": True,
    }


def _summary_for_currency(
    position: Mapping[str, Any],
    currency: str,
    draft: Mapping[str, Any],
) -> dict[str, Any]:
    buckets = position.get("buckets") or {}
    held_rows = [row for row in buckets.get("held_credit") or [] if isinstance(row, Mapping) and _currency(row) == currency]
    received_rows = [row for row in buckets.get("received_on_behalf") or [] if isinstance(row, Mapping) and _currency(row) == currency]
    paid_rows = [row for row in buckets.get("paid_on_behalf") or [] if isinstance(row, Mapping) and _currency(row) == currency]
    unallocated_rows = [row for row in buckets.get("unallocated") or [] if isinstance(row, Mapping) and _currency(row) == currency]
    unknown_rows = [row for row in buckets.get("unknown") or [] if isinstance(row, Mapping) and _currency(row) == currency]
    restricted_rows = [row for row in buckets.get("restricted") or [] if isinstance(row, Mapping) and _currency(row) == currency]
    held_total = sum(_row_amount(row, "held_credit") for row in held_rows)
    received_total = sum(_full_amount(row, "received_on_behalf") for row in received_rows)
    received_allocated = sum(to_decimal(row.get("allocated")) for row in received_rows)
    received_remaining = sum(to_decimal(row.get("remaining_unallocated", row.get("unallocated"))) for row in received_rows)
    paid_total = sum(_row_amount(row, "paid_on_behalf") for row in paid_rows)
    known_credit_ids = {_row_id(row) for row in held_rows + received_rows + paid_rows}
    unallocated_total = sum(
        _row_amount(row, "unallocated")
        for row in unallocated_rows
        if _row_id(row) not in known_credit_ids
    )
    unknown_total = sum(_row_amount(row, "unknown") for row in unknown_rows)
    restricted_total = sum(_row_amount(row, "restricted") for row in restricted_rows)
    values = draft or {}
    return {
        "currency": currency,
        "payable_to_partner": values.get("payable_subtotal", 0.0),
        "held_credit": float(held_total),
        "received_on_behalf": float(received_total),
        "received_on_behalf_allocated": float(received_allocated),
        "received_on_behalf_remaining": float(received_remaining),
        "paid_on_behalf": float(paid_total),
        "settled_or_allocated": float(to_decimal(values.get("settled_amount")) + received_allocated),
        "unallocated": float(unallocated_total),
        "unknown": float(unknown_total),
        "restricted": float(restricted_total),
        "confirmed_position": values.get("confirmed_position", 0.0),
        "debit_eligible_amount": values.get("debit_ready_amount", 0.0),
        "review_required_amount": float(unknown_total + restricted_total + unallocated_total),
        "deterministic": True,
    }


def _important_shipments(draft: Mapping[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    totals: dict[tuple[str, str], dict[str, Any]] = {}
    for values in (draft.get("by_currency") or {}).values():
        for line in values.get("included_items") or []:
            shipment_ids = line.get("shipment_ids") or []
            if not shipment_ids:
                continue
            for shipment_id in shipment_ids:
                key = (str(shipment_id), str(line.get("currency") or "UNKNOWN"))
                current = totals.setdefault(
                    key,
                    {
                        "shipment_id": str(shipment_id),
                        "currency": str(line.get("currency") or "UNKNOWN"),
                        "impact_amount": 0.0,
                        "line_count": 0,
                        "source_record_ids": [],
                    },
                )
                current["impact_amount"] += float(line.get("signed_amount") or 0)
                current["line_count"] += 1
                for source_id in line.get("source_record_ids") or []:
                    if source_id not in current["source_record_ids"]:
                        current["source_record_ids"].append(source_id)
    rows = list(totals.values())
    rows.sort(key=lambda item: (-abs(float(item["impact_amount"])), item["currency"], item["shipment_id"]))
    return rows[:limit]


def build_manager_report(
    position: Mapping[str, Any],
    *,
    period_start: date | str | None = None,
    period_end: date | str | None = None,
    report_date: date | str | None = None,
    reported_by_currency: Mapping[str, Any] | None = None,
    status: str = REPORT_STATUS_DRAFT,
) -> dict[str, Any]:
    """Build the manager-facing report from the same debit read model."""

    status = str(status or REPORT_STATUS_DRAFT).strip().upper()
    if status not in {REPORT_STATUS_DRAFT, REPORT_STATUS_READY_FOR_REVIEW}:
        raise ValueError(f"unsupported report status: {status}")
    debit = build_debit_draft(
        position,
        period_start=period_start,
        period_end=period_end,
        reported_by_currency=reported_by_currency,
        status=DEBIT_STATUS_DRAFT,
    )
    summaries = {
        currency: _summary_for_currency(position, currency, values)
        for currency, values in (debit.get("by_currency") or {}).items()
    }
    confirmed_by_currency = {
        currency: to_decimal(values.get("confirmed_position"))
        for currency, values in summaries.items()
    }
    partner_difference = _partner_difference(position, reported_by_currency, confirmed_by_currency)
    explanations: dict[str, dict[str, Any]] = {}
    for currency, values in (debit.get("by_currency") or {}).items():
        lines = values.get("included_items") or []
        formula = values.get("formula") or f"0 {currency} = 0 {currency}"
        explanations[currency] = {
            "title": "DIỄN GIẢI SỐ LIỆU",
            "currency": currency,
            "formula": formula,
            "included_lines": deepcopy(lines),
            "excluded_lines": deepcopy(values.get("excluded_items") or []),
            "confirmed_amount": values.get("confirmed_position", 0.0),
            "review_amount": summaries[currency].get("review_required_amount", 0.0),
            "source_record_ids": values.get("references", {}).get("ledger_record_ids", []),
            "deterministic": True,
        }
    return {
        "document_type": "MANAGER_REPORT_A_BO",
        "title": "BÁO CÁO CÔNG NỢ A BÒ — SALE THÀNH",
        "status": status,
        "period": _period_value(period_start, period_end),
        "report_date": _date_text(report_date),
        "prepared_for": "Sếp",
        "sale_owner": position.get("internal_sale_owner") or "Thành",
        "party": deepcopy(position.get("party") or {}),
        "party_key": position.get("party_key"),
        "currencies": list(summaries),
        "summary_by_currency": summaries,
        "explanations": explanations,
        "important_shipments": _important_shipments(debit),
        "review_items": deepcopy(
            [
                item
                for values in (debit.get("by_currency") or {}).values()
                for item in values.get("excluded_items") or []
            ]
        ),
        "partner_difference": partner_difference,
        "debit_preview": debit,
        "read_only": True,
        "financial_effect_write_count": 0,
        "deterministic": True,
    }


def snapshot_content_hash(document: Mapping[str, Any]) -> str:
    """Return a stable hash for a report/debit payload excluding runtime metadata."""

    payload = deepcopy(dict(document))
    for key in ("generated_at", "prepared_by", "snapshot_id", "request_id", "version", "status"):
        payload.pop(key, None)
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(canonical.encode("utf-8")).hexdigest()


__all__ = [
    "DEBIT_STATUS_DRAFT",
    "DEBIT_STATUS_READY_FOR_REVIEW",
    "DEBIT_STATUS_SUPERSEDED",
    "EXCLUSION_LABELS",
    "REPORT_STATUS_DRAFT",
    "REPORT_STATUS_READY_FOR_REVIEW",
    "build_debit_draft",
    "build_manager_report",
    "snapshot_content_hash",
]
