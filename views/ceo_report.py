"""LOGI_CEO_REPORT_01 — bounded, read-only CEO presentation adapter.

This is deliberately *not* an analytics service.  It receives projections that
``views.logi_view_model`` has already read and derived, then groups only their
existing, current-position facts for ``/bao-cao-ceo``:

    shipment/home/task projections
    C2C customer receivables
    C2D partner payables
    reconciliation allocation-state summary
        → one CEO presentation slice

It opens no database, persists nothing, dispatches no event, applies no FX, and
introduces no finance calculation.  In particular, revenue, cost, profit,
margin, targets, forecasts and trends are deliberately outside this slice.
"""

from __future__ import annotations

from collections import Counter
from math import isfinite
from typing import Any, Mapping


# This is the existing work-desk meaning used by the shell's real open-work
# badge: only Khẩn + Cần xử lý are actionable work.  This adapter does not
# redefine task completion from a presentation-only status string.
ACTIONABLE_TASK_LEVELS = frozenset({"Khan", "CanXuLy"})

# Navigation only; each target already owns its own business capability.
QUICK_LINKS: tuple[dict[str, str], ...] = (
    {
        "label": "Mở lô hàng",
        "href": "/lo-hang",
        "note": "Danh sách lô và trạng thái hiện tại",
    },
    {
        "label": "Mở phải thu khách",
        "href": "/tai-chinh/thu-tien",
        "note": "C2C · phải thu theo tiền tệ",
    },
    {
        "label": "Mở phải trả đối tác",
        "href": "/tai-chinh/cong-no-doi-tac",
        "note": "C2D · nghĩa vụ đối tác theo tiền tệ",
    },
    {
        "label": "Mở đối soát",
        "href": "/tai-chinh/doi-soat",
        "note": "Ledger allocation · chỉ đọc",
    },
)

# These are explicit exclusions, not missing values that the page may fill.
UNAVAILABLE_CONTEXT: tuple[str, ...] = (
    "Chỉ hiển thị vị thế hiện tại có nguồn dữ liệu; không tạo chỉ số thay thế.",
    "Không có quy đổi tiền tệ, mục tiêu, dự báo hoặc xu hướng trên trang này.",
)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _rows(value: Any) -> list[Mapping[str, Any]]:
    return [item for item in (value or []) if isinstance(item, Mapping)] if isinstance(value, list) else []


def _text(value: Any) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _number(value: Any) -> float | None:
    """Return a real finite number, never turn an unknown into zero."""
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if isfinite(result) else None


def _count(value: Any) -> int | None:
    """A non-negative whole count, or UNKNOWN when the source did not provide it."""
    number = _number(value)
    if number is None or number < 0 or not number.is_integer():
        return None
    return int(number)


def _currency(value: Any) -> str:
    # The source projections already use uppercase currency codes.  A malformed
    # key remains visibly UNKNOWN and is never merged into a real currency.
    return (_text(value) or "UNKNOWN").upper()


def _ordered_currencies(values: Mapping[str, Any]) -> list[str]:
    currencies = [_currency(currency) for currency in values]
    known = sorted(currency for currency in currencies if currency != "UNKNOWN")
    return [*known, *( ["UNKNOWN"] if "UNKNOWN" in currencies else [])]


def _status_counts(shipments: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for shipment in shipments:
        # Shipment projection normally always provides a label.  When it does
        # not, expose that uncertainty instead of placing the shipment in an
        # arbitrary operational stage.
        counts[_text(shipment.get("status")) or "Chưa xác định"] += 1
    return [{"status": status, "count": count} for status, count in counts.items()]


def _operations(
    shipments: list[Mapping[str, Any]],
    home: Mapping[str, Any],
    tasks: list[Mapping[str, Any]],
) -> dict[str, Any]:
    # `runningCount` is the existing Home projection's definition of an open
    # shipment (not delivered and not cancelled).  Do not re-implement it here.
    open_shipments = _count(home.get("runningCount"))
    return {
        "totalShipmentCount": len(shipments),
        "openShipmentCount": open_shipments,
        "statusCounts": _status_counts(shipments),
        "actionableTaskCount": sum(
            1 for task in tasks if _text(task.get("level")) in ACTIONABLE_TASK_LEVELS
        ),
    }


def _receivables(payload: Mapping[str, Any]) -> tuple[dict[str, Any], int]:
    """Pass C2C's already-safe currency totals through without a new total."""
    rows = _rows(payload.get("rows"))
    totals = _mapping(payload.get("totals"))
    positions: list[dict[str, Any]] = []

    for currency in _ordered_currencies(totals):
        raw_total = _mapping(totals.get(currency))
        currency_rows = [row for row in rows if _currency(row.get("currency")) == currency]
        known_rows = [
            row
            for row in currency_rows
            if bool(row.get("hasActualLines")) and _number(row.get("outstanding")) is not None
        ]
        positions.append(
            {
                "currency": currency,
                # C2C emits this only from complete Finance Actual rows. Keep
                # None as None if a malformed source lacks a safe amount.
                "outstanding": _number(raw_total.get("outstanding")),
                # This is an explicitly known-subset count, not a claim that
                # incomplete rows have zero outstanding amount.
                "openCount": sum(1 for row in known_rows if _number(row.get("outstanding")) > 0),
                "rowCount": len(known_rows),
                "incompleteRowCount": len(currency_rows) - len(known_rows),
            }
        )

    # Finance Actual is incomplete if the C2C row explicitly says no actual
    # service line or cannot safely state its outstanding amount. These rows
    # are excluded from C2C totals; this count makes that limitation visible.
    incomplete = sum(
        1
        for row in rows
        if not bool(row.get("hasActualLines")) or _number(row.get("outstanding")) is None
    )
    return {
        "positions": positions,
        "shipmentRowCount": len(rows),
        "hasAuthoritativeAmounts": any(position["outstanding"] is not None for position in positions),
    }, incomplete


def _payables(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Pass C2D's canonical-ledger currency totals through without an FX sum."""
    rows = _rows(payload.get("rows"))
    totals = _mapping(payload.get("totals"))
    positions: list[dict[str, Any]] = []

    for currency in _ordered_currencies(totals):
        raw_total = _mapping(totals.get(currency))
        currency_rows = [row for row in rows if _currency(row.get("currency")) == currency]
        known_rows = [row for row in currency_rows if _number(row.get("remaining")) is not None]
        positions.append(
            {
                "currency": currency,
                "outstanding": _number(raw_total.get("remaining")),
                "openCount": sum(1 for row in known_rows if _number(row.get("remaining")) > 0),
                "rowCount": len(known_rows),
                "incompleteRowCount": len(currency_rows) - len(known_rows),
            }
        )

    return {
        "positions": positions,
        "recordCount": len(rows),
        "hasCanonicalRecords": bool(rows),
        "status": _text(payload.get("status")) or "UNKNOWN",
        "error": _text(payload.get("error")),
    }


def _state_counts(source: Mapping[str, Any], states: tuple[str, ...]) -> dict[str, int | None]:
    # A state may be zero only when the existing reconciliation summary actually
    # supplied its known count.  An absent value stays UNKNOWN (None).
    return {state: _count(source.get(state)) if state in source else None for state in states}


def _reconciliation(payload: Mapping[str, Any]) -> dict[str, Any]:
    status = _text(payload.get("status")) or "NO_SOURCE"
    summary = _mapping(payload.get("summary"))
    obligations = _mapping(summary.get("obligations"))
    money = _mapping(summary.get("money"))
    available = status in {"OK", "REVIEW_REQUIRED"} and bool(summary)

    return {
        "status": status,
        "available": available,
        "obligations": (
            _state_counts(obligations, ("MATCHED", "PARTIAL", "UNMATCHED", "UNKNOWN"))
            if available else None
        ),
        "money": (
            _state_counts(money, ("ALLOCATED", "PARTIAL", "UNALLOCATED", "UNKNOWN"))
            if available else None
        ),
        "reviewCount": _count(summary.get("reviewCount")) if available and "reviewCount" in summary else None,
        "error": _text(payload.get("error")),
    }


def ceo_report_projection(
    *,
    shipments: Any,
    home: Any,
    tasks: Any,
    receivables: Any,
    payables: Any,
    reconciliation: Any,
) -> dict[str, Any]:
    """Build the one bounded CEO summary from existing view-model projections.

    There are intentionally no database reads or business calculations here.
    Money arrives only as C2C/C2D's already-authoritative *per-currency* totals.
    """
    shipment_rows = _rows(shipments)
    task_rows = _rows(tasks)
    receivable_section, incomplete_finance_count = _receivables(_mapping(receivables))

    return {
        "classification": "PARTIAL_BACKED_READY",
        "readOnly": True,
        "operations": _operations(shipment_rows, _mapping(home), task_rows),
        "receivables": receivable_section,
        "payables": _payables(_mapping(payables)),
        "finance": {
            "incompleteShipmentCount": incomplete_finance_count,
        },
        "reconciliation": _reconciliation(_mapping(reconciliation)),
        "quickLinks": [dict(link) for link in QUICK_LINKS],
        "unavailable": list(UNAVAILABLE_CONTEXT),
    }


__all__ = [
    "ACTIONABLE_TASK_LEVELS",
    "QUICK_LINKS",
    "UNAVAILABLE_CONTEXT",
    "ceo_report_projection",
]
