"""Bounded READ-ONLY reconciliation adapter for the ``/tai-chinh/doi-soat`` desk.

Presentation adapter ONLY (LOGI_RECONCILIATION_DESK_01). It exposes the
reconciliation capability that ALREADY EXISTS in Logistics Work Desk and was
previously reachable only from the orphaned Streamlit A Bò desk:

    core.financial_ledger.shipment_partner_position(shipment_id)
        → derive_obligation_position()   amount / allocated / outstanding
        → derive_transaction_position()  amount / allocated / unallocated
        → allocation history, per-record CONFIRMED / REVIEW_REQUIRED status

No new source of truth is introduced. Every figure below is a passthrough of
what ``core.financial_ledger`` already derived from the canonical
``financial_obligations`` / ``financial_transactions`` / ``financial_allocations``
collections. This module re-derives, re-allocates and re-totals NOTHING, and it
creates no database, service, router, API, store, index, model, ledger or
writer — none is implied by it.

WHAT "RECONCILIATION" MEANS HERE (and nowhere else)
---------------------------------------------------
The repo's existing reconciliation semantics are **allocation matching**:

* an OBLIGATION is ``MATCHED`` / ``PARTIAL`` / ``UNMATCHED`` against the
  allocations that already exist;
* a TRANSACTION is ``ALLOCATED`` / ``PARTIAL`` / ``UNALLOCATED`` — money that
  arrived or left and is not (yet) tied to an obligation is the unmatched side;
* a record whose allocation history is currency-incompatible or over-allocated
  is ``REVIEW_REQUIRED`` by the canonical ledger, and stays visible as such.

That is all. Nothing here invents bank-statement reconciliation, cashbook
matching, accounting-journal matching, invoice matching, VAT reconciliation,
aging buckets or period close — the backend models none of them, and the
``unavailable`` panel says so plainly instead of leaving a quiet empty tab.

BUSINESS TRUTH RULES (finance adjacent — fail honest, never fabricate):

- UNKNOWN != ZERO: a shipment with no canonical obligation/payment record
  contributes NO row, so absence is never reported as a 0 payable. When the
  database cannot be read the desk returns ``status = "NO_SOURCE"`` with zero
  rows and no totals — never a manufactured balanced book.
- Currencies stay separate. There is no FX engine, no cross-currency sum and no
  "grand total". A record whose currency the backend does not carry is grouped
  under ``UNKNOWN`` and reported on its own.
- A REVIEW_REQUIRED amount is included in a currency total AND reported
  separately as ``review``, so an unconfirmed figure can never hide inside a
  confident-looking number.
- This desk writes nothing. Recording a payable or a payment stays on the
  existing canonical surfaces it links to (see ``actions``); there is no second
  writer and no manual balance override here.

Layering: :func:`reconciliation_projection` is pure over the per-shipment
positions it is handed (so it is testable without a database), while
:func:`reconciliation_view` is the ONE-READ wrapper the view-model calls.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from views.logi_route import shipment_path

#: Existing React route for one shipment (donor route, unchanged).
SHIPMENT_ROUTE_PREFIX = "/lo-hang/"

#: Existing canonical surfaces where the WRITE already lives. Navigation only:
#: this desk never exposes a second writer for the same intent.
PAYABLE_WORKLIST_ROUTE = "/tai-chinh/cong-no-doi-tac"
RECEIVABLE_WORKLIST_ROUTE = "/tai-chinh/thu-tien"

#: Payload boundedness ceiling — the same discipline as the other adapters.
MAX_ROWS = 400

#: Currency sentinel: the record exists but the backend carries no currency for
#: it. Kept as its own group; never summed into a real currency.
UNKNOWN_CURRENCY = "UNKNOWN"

# --- Obligation-side match states (derived from allocated / outstanding) -----
MATCHED = "MATCHED"
PARTIAL = "PARTIAL"
UNMATCHED = "UNMATCHED"

# --- Money-side match states (derived from allocated / unallocated) ----------
ALLOCATED = "ALLOCATED"
UNALLOCATED = "UNALLOCATED"

OBLIGATION_STATE_LABELS = {
    MATCHED: "Đã đối soát đủ",
    PARTIAL: "Đối soát một phần",
    UNMATCHED: "Chưa đối soát",
}

MONEY_STATE_LABELS = {
    ALLOCATED: "Đã phân bổ hết",
    PARTIAL: "Phân bổ một phần",
    UNALLOCATED: "Chưa phân bổ",
}

#: Honest status of the whole slice (the UI renders a distinct state for each).
OK = "OK"
EMPTY = "EMPTY"
NO_SOURCE = "NO_SOURCE"
REVIEW_REQUIRED = "REVIEW_REQUIRED"

#: Reconciliation context a finance team usually expects but this backend does
#: not model anywhere. Surfaced verbatim so the page never looks "quietly
#: empty" and so nobody mistakes the desk for something it is not.
UNAVAILABLE_CONTEXT: tuple[str, ...] = (
    "Đối soát sao kê ngân hàng / nạp file sao kê — không có nguồn dữ liệu",
    "Tỷ giá quy đổi và tổng đa tiền tệ — không có FX, tiền tệ luôn tách riêng",
    "Tuổi nợ (aging) và hạn thanh toán tự suy ra — không có công cụ aging",
    "Khớp hóa đơn / sổ nhật ký kế toán / đối soát VAT — không có sổ kế toán",
    "Đóng kỳ, khóa sổ, phê duyệt đối soát — không có quy trình chốt kỳ",
)


def _text(value: Any) -> str | None:
    """Verbatim string passthrough; genuinely-absent values stay ``None``."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan", "null", "<na>"}:
        return None
    return text


def _currency_of(row: Mapping[str, Any]) -> str:
    """Currency as the canonical ledger stored it, or the UNKNOWN sentinel.

    ``derive_*_position`` upper-cases and may yield ``""``; an empty currency is
    UNKNOWN, not a currency, and must never join a real currency's total.
    """
    return (_text(row.get("currency")) or UNKNOWN_CURRENCY).upper()


def _num(value: Any) -> float | None:
    """A real number, or ``None`` when the record genuinely carries none."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _party_label(value: Any) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("name")) or _text(value.get("party_id")) or _text(value.get("key"))
    return _text(value)


def _party_id(value: Any) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("party_id")) or _text(value.get("key"))
    return _text(value)


def _ids(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item) for item in value if _text(item)]


def _review_reason(row: Mapping[str, Any]) -> str | None:
    """The ONLY review signals the canonical ledger actually derives."""
    if _ids(row.get("incompatible_allocation_ids")):
        return "Phân bổ lệch tiền tệ với chứng từ gốc"
    if row.get("overallocated"):
        return "Phân bổ vượt số phải trả/phải thu"
    return None


def _obligation_state(allocated: float, remaining: float) -> str:
    """MATCHED / PARTIAL / UNMATCHED — purely from the derived figures."""
    if allocated <= 0:
        return UNMATCHED
    if remaining > 0:
        return PARTIAL
    return MATCHED


def _money_state(allocated: float, unallocated: float) -> str:
    """ALLOCATED / PARTIAL / UNALLOCATED — purely from the derived figures."""
    if allocated <= 0:
        return UNALLOCATED
    if unallocated > 0:
        return PARTIAL
    return ALLOCATED


def _blank(currency: str) -> dict[str, Any]:
    return {
        "currency": currency,
        "obligations": {"count": 0, "amount": 0.0, "allocated": 0.0, "remaining": 0.0},
        "money": {"count": 0, "amount": 0.0, "allocated": 0.0, "unallocated": 0.0},
        "review": {"count": 0, "amount": 0.0},
        "states": {
            MATCHED: 0,
            PARTIAL: 0,
            UNMATCHED: 0,
            ALLOCATED: 0,
            UNALLOCATED: 0,
        },
    }


def reconciliation_projection(
    positions: Iterable[Mapping[str, Any]],
    *,
    known_shipment_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Pure reconciliation projection over per-shipment canonical positions.

    ``positions`` is the sequence of ``shipment_partner_position(sid)`` results
    for the shipments the caller read. The top-level ``obligations`` and
    ``payments`` lists of each position are already complete and each record
    appears once, so no de-duplication or second derivation is needed here.
    """
    known = {str(item) for item in known_shipment_ids if _text(item)} if known_shipment_ids is not None else None

    rows: list[dict[str, Any]] = []
    totals: dict[str, dict[str, Any]] = {}
    truncated = False

    for position in positions:
        if not isinstance(position, Mapping):
            continue
        sid = _text(position.get("shipment_id"))
        if not sid:
            continue

        # allocation_id → obligation_id, so a payment row can name the
        # obligations it was actually applied to (real linkage, never guessed).
        allocation_to_obligation: dict[str, str] = {}
        obligation_rows = [row for row in position.get("obligations") or [] if isinstance(row, Mapping)]
        for row in obligation_rows:
            obligation_id = _text(row.get("obligation_id"))
            if not obligation_id:
                continue
            for allocation_id in _ids(row.get("allocation_ids")):
                allocation_to_obligation.setdefault(allocation_id, obligation_id)

        # partner_key → legal/master name from the group the ledger built.
        partner_names: dict[str, str | None] = {}
        for group in position.get("partners") or []:
            if isinstance(group, Mapping):
                key = _text(group.get("partner_key"))
                if key:
                    partner_names.setdefault(key, _party_label(group.get("partner")))

        for row in obligation_rows:
            obligation_id = _text(row.get("obligation_id"))
            if not obligation_id:
                continue
            currency = _currency_of(row)
            amount = _num(row.get("amount"))
            allocated = _num(row.get("allocated"))
            remaining = _num(row.get("outstanding"))
            status = (_text(row.get("status")) or "UNKNOWN").upper()
            partner_key = _text(row.get("_partner_key")) or ""
            shipment_ids = _ids(row.get("shipment_ids")) or [sid]
            # UNKNOWN != ZERO: a derived figure the ledger did not produce stays
            # None and renders as "—"; it is never coerced to a settled 0.
            state = (
                _obligation_state(allocated, remaining)
                if allocated is not None and remaining is not None
                else None
            )
            rows.append(
                {
                    "id": f"{sid}|OB|{obligation_id}",
                    "side": "obligation",
                    "shipmentId": sid,
                    "shipmentIds": shipment_ids,
                    "partnerId": _party_id(row.get("to_party")),
                    "partnerName": partner_names.get(partner_key) or _party_label(row.get("to_party")),
                    "counterparty": _party_label(row.get("from_party")),
                    "purpose": _text(row.get("purpose")),
                    "currency": currency,
                    "amount": amount,
                    "allocated": allocated,
                    "remaining": remaining,
                    "status": status,
                    "matchState": state,
                    "matchLabel": OBLIGATION_STATE_LABELS.get(state or "") ,
                    "allocationIds": _ids(row.get("allocation_ids")),
                    "obligationIds": [obligation_id],
                    "transactionIds": [],
                    "sourceRecordIds": _ids(row.get("source_record_ids")),
                    "reviewReason": _review_reason(row),
                    "openHref": shipment_path(sid),
                    "canOpen": True if known is None else sid in known,
                }
            )
            bucket = totals.setdefault(currency, _blank(currency))
            bucket["obligations"]["count"] += 1
            bucket["obligations"]["amount"] += amount or 0.0
            bucket["obligations"]["allocated"] += allocated or 0.0
            bucket["obligations"]["remaining"] += remaining or 0.0
            if state:
                bucket["states"][state] += 1
            if status != "CONFIRMED":
                bucket["review"]["count"] += 1
                bucket["review"]["amount"] += remaining if remaining is not None else amount or 0.0

        for row in position.get("payments") or []:
            if not isinstance(row, Mapping):
                continue
            transaction_id = _text(row.get("transaction_id"))
            if not transaction_id:
                continue
            currency = _currency_of(row)
            amount = _num(row.get("amount"))
            allocated = _num(row.get("allocated"))
            unallocated = _num(row.get("unallocated"))
            status = (_text(row.get("status")) or "UNKNOWN").upper()
            allocation_ids = _ids(row.get("allocation_ids"))
            obligation_ids: list[str] = []
            for allocation_id in allocation_ids:
                obligation_id = allocation_to_obligation.get(allocation_id)
                if obligation_id and obligation_id not in obligation_ids:
                    obligation_ids.append(obligation_id)
            state = (
                _money_state(allocated, unallocated)
                if allocated is not None and unallocated is not None
                else None
            )
            rows.append(
                {
                    "id": f"{sid}|TX|{transaction_id}",
                    "side": "money",
                    "shipmentId": sid,
                    "shipmentIds": [sid],
                    "partnerId": _party_id(row.get("holder_party")),
                    "partnerName": _party_label(row.get("holder_party")),
                    "counterparty": _party_label(row.get("source_party")),
                    "purpose": _text(row.get("transaction_kind")),
                    "occurredAt": _text(row.get("occurred_at")),
                    "currency": currency,
                    "amount": amount,
                    "allocated": allocated,
                    "remaining": unallocated,
                    "status": status,
                    "matchState": state,
                    "matchLabel": MONEY_STATE_LABELS.get(state or ""),
                    "allocationIds": allocation_ids,
                    "obligationIds": obligation_ids,
                    "transactionIds": [transaction_id],
                    "sourceRecordIds": _ids(row.get("source_record_ids")),
                    "reviewReason": _review_reason(row),
                    "openHref": shipment_path(sid),
                    "canOpen": True if known is None else sid in known,
                }
            )
            bucket = totals.setdefault(currency, _blank(currency))
            bucket["money"]["count"] += 1
            bucket["money"]["amount"] += amount or 0.0
            bucket["money"]["allocated"] += allocated or 0.0
            bucket["money"]["unallocated"] += unallocated or 0.0
            if state:
                bucket["states"][state] += 1
            if status != "CONFIRMED":
                bucket["review"]["count"] += 1
                bucket["review"]["amount"] += unallocated if unallocated is not None else amount or 0.0

        # Transaction ids belong to the obligations they were applied to.
        by_obligation: dict[str, list[str]] = {}
        for row in rows:
            if row["side"] != "money":
                continue
            for obligation_id in row["obligationIds"]:
                by_obligation.setdefault(obligation_id, []).extend(row["transactionIds"])
        for row in rows:
            if row["side"] != "obligation":
                continue
            linked = by_obligation.get(row["obligationIds"][0]) if row["obligationIds"] else None
            if linked:
                row["transactionIds"] = list(dict.fromkeys(linked))

    # Counts must describe the complete canonical projection, not only the
    # bounded list payload rendered below. This carries no monetary aggregate.
    full_summary = reconciliation_summary({"rows": rows, "totals": totals})

    if len(rows) > MAX_ROWS:
        rows = rows[:MAX_ROWS]
        truncated = True

    rows.sort(key=lambda row: (row["shipmentId"], row["side"], row["id"]))
    return {
        "rows": rows,
        "totals": {currency: totals[currency] for currency in sorted(totals)},
        "summary": full_summary,
        "truncated": truncated,
        "maxRows": MAX_ROWS,
    }


# ---------------------------------------------------------------------------
# Filtering — only over fields the backend already supplies
# ---------------------------------------------------------------------------

ALL = "ALL"
REVIEW = "REVIEW"
OBLIGATION = "obligation"
MONEY = "money"


def _haystack(row: Mapping[str, Any]) -> str:
    parts: list[str] = []
    for key in ("shipmentId", "partnerId", "partnerName", "counterparty", "purpose", "currency"):
        value = _text(row.get(key))
        if value:
            parts.append(value)
    for key in ("obligationIds", "transactionIds", "allocationIds"):
        parts.extend(_ids(row.get(key)))
    return " ".join(parts).casefold()


def apply_filters(
    projection: Mapping[str, Any],
    *,
    query: str = "",
    currency: str = ALL,
    state: str = ALL,
    side: str = ALL,
) -> dict[str, Any]:
    """Filter the projection over existing fields only; totals stay unfiltered.

    Totals are deliberately NOT recomputed from the filtered rows: a total that
    silently followed a search box would read as the book's real position. The
    UI shows the full per-currency total and, beside it, how many rows the
    current filter left visible.
    """
    needle = (query or "").strip().casefold()
    # Every sentinel/filter comparison is upper-cased on BOTH sides so the "ALL"
    # sentinel can never be defeated by a lower-cased value such as "obligation".
    currency_filter = (currency or ALL).strip().upper() or ALL
    state_filter = (state or ALL).strip().upper() or ALL
    side_filter = (side or ALL).strip().upper() or ALL

    visible: list[dict[str, Any]] = []
    for row in projection.get("rows") or []:
        if not isinstance(row, Mapping):
            continue
        if side_filter != ALL and str(row.get("side") or "").upper() != side_filter:
            continue
        if currency_filter != ALL and _currency_of(row) != currency_filter:
            continue
        row_state = str(row.get("matchState") or "").upper()
        if state_filter == REVIEW:
            if not row.get("reviewReason"):
                continue
        elif state_filter != ALL and row_state != state_filter:
            continue
        if needle and needle not in _haystack(row):
            continue
        visible.append(dict(row))

    return {
        "rows": visible,
        "visibleCount": len(visible),
        "totalCount": len(projection.get("rows") or []),
        "query": (query or "").strip(),
        "currency": currency_filter,
        "state": state_filter,
        "side": side_filter,
    }


def _currencies(projection: Mapping[str, Any]) -> list[str]:
    """Every currency actually present, UNKNOWN last so it never leads."""
    found = [currency for currency in (projection.get("totals") or {}) if currency != UNKNOWN_CURRENCY]
    found.sort()
    if UNKNOWN_CURRENCY in (projection.get("totals") or {}):
        found.append(UNKNOWN_CURRENCY)
    return found


def reconciliation_summary(projection: Mapping[str, Any]) -> dict[str, Any]:
    """Count existing canonical match states before any local list filter.

    This is a presentation-only count over ``reconciliation_projection`` rows.
    It deliberately carries no amount and does not derive a new match state:
    ``matchState`` is exactly what the existing canonical allocation projection
    already supplied. A missing match state remains visible as ``UNKNOWN``.

    ``reconciliation_projection`` stores a full count before it bounds rows for
    the list UI. Reusing it here keeps a CEO summary complete even when the
    interactive list is truncated.
    """
    existing = projection.get("summary")
    if isinstance(existing, Mapping):
        obligations = existing.get("obligations")
        money = existing.get("money")
        if isinstance(obligations, Mapping) and isinstance(money, Mapping):
            return {
                "obligations": dict(obligations),
                "money": dict(money),
                "reviewCount": existing.get("reviewCount"),
            }

    obligations = {MATCHED: 0, PARTIAL: 0, UNMATCHED: 0, UNKNOWN_CURRENCY: 0}
    money = {ALLOCATED: 0, PARTIAL: 0, UNALLOCATED: 0, UNKNOWN_CURRENCY: 0}

    for row in projection.get("rows") or []:
        if not isinstance(row, Mapping):
            continue
        side = row.get("side")
        state = row.get("matchState")
        if side == OBLIGATION:
            key = state if isinstance(state, str) and state in obligations else UNKNOWN_CURRENCY
            obligations[key] += 1
        elif side == MONEY:
            key = state if isinstance(state, str) and state in money else UNKNOWN_CURRENCY
            money[key] += 1

    # The existing per-currency projection already identifies rows requiring
    # review. Counts can be added across currencies; monetary amounts remain
    # in their original currency blocks and are intentionally absent here.
    review_count = 0
    for bucket in (projection.get("totals") or {}).values():
        if not isinstance(bucket, Mapping):
            continue
        review = bucket.get("review")
        if not isinstance(review, Mapping):
            continue
        count = _num(review.get("count"))
        if count is not None:
            review_count += int(count)
    return {
        "obligations": obligations,
        "money": money,
        "reviewCount": review_count,
    }


#: Navigation-only pointers to the surfaces where the WRITE already lives. This
#: desk exposes no writer of its own, so it links to the canonical ones.
ACTIONS: tuple[dict[str, str], ...] = (
    {
        "label": "Ghi nhận phải trả / thanh toán đối tác",
        "href": PAYABLE_WORKLIST_ROUTE,
        "note": "Writer canonical C2B/C2D — bàn này chỉ đọc",
    },
    {
        "label": "Thu tiền khách hàng",
        "href": RECEIVABLE_WORKLIST_ROUTE,
        "note": "Writer canonical C2C — bàn này chỉ đọc",
    },
)


def _empty(error: str | None, status: str) -> dict[str, Any]:
    return {
        "rows": [],
        "totals": {},
        "currencies": [],
        "visibleCount": 0,
        "totalCount": 0,
        "query": "",
        "currency": ALL,
        "state": ALL,
        "side": ALL,
        "truncated": False,
        "maxRows": MAX_ROWS,
        "status": status,
        "derived": True,
        "readOnly": True,
        "shipmentRoutePrefix": SHIPMENT_ROUTE_PREFIX,
        "actions": list(ACTIONS),
        # No ledger source/records means state counts are UNKNOWN too. Do not
        # manufacture a row-count zero summary for the CEO presentation.
        "summary": None,
        "unavailable": list(UNAVAILABLE_CONTEXT),
        "error": error,
    }


def reconciliation_view(
    selection: Mapping[str, Any] | None = None,
    *,
    db: Any = None,
    known_shipment_ids: Iterable[str] | None = None,
    shipment_ids: Iterable[str] | None = None,
    records: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The ONE-READ wrapper: canonical ledger → filter → bounded payload.

    ``selection`` is the bounded read-only filter the dispatcher recorded. It is
    a lookup input only and is never trusted as data.

    PERFORMANCE REPAIR — the component build path passes the render-local
    snapshot it already read: ``shipment_ids`` (``core.database.load_shipment_ids``,
    the identical query/projection this wrapper used to run) and ``records``
    (``core.financial_ledger.load_ledger_snapshot``), so the per-shipment
    derivation reads no collection. Both are optional: a standalone caller keeps
    the original reads.
    """
    from core.database import get_db
    from core.financial_ledger import shipment_partner_position

    selection = selection if isinstance(selection, Mapping) else {}
    db = get_db() if db is None else db
    if db is None:
        return _empty("MongoDB is not available", NO_SOURCE)

    if shipment_ids is None:
        try:
            shipment_ids = [
                _text(doc.get("id"))
                for doc in db.shipments.find({"is_deleted": {"$ne": True}}, {"_id": 0, "id": 1})
                if isinstance(doc, Mapping)
            ]
        except Exception as exc:  # noqa: BLE001 - read path fails honest, never fabricates
            return _empty(str(exc), NO_SOURCE)

    positions = [
        shipment_partner_position(sid, db=db, records=records)
        for sid in shipment_ids
        if sid
    ]
    projection = reconciliation_projection(positions, known_shipment_ids=known_shipment_ids)

    if not projection["rows"]:
        return _empty(None, EMPTY)

    filtered = apply_filters(
        projection,
        query=str(selection.get("query") or ""),
        currency=str(selection.get("currency") or ALL),
        state=str(selection.get("state") or ALL),
        side=str(selection.get("side") or ALL),
    )

    needs_review = any(row.get("reviewReason") for row in projection["rows"])
    # Keep this unfiltered. A filter is only a list-view choice and must not
    # alter the management summary of the canonical ledger.
    summary = reconciliation_summary(projection)
    return {
        **filtered,
        "totals": projection["totals"],
        "summary": summary,
        "currencies": _currencies(projection),
        "truncated": projection["truncated"],
        "maxRows": projection["maxRows"],
        "status": REVIEW_REQUIRED if needs_review else OK,
        "derived": True,
        "readOnly": True,
        "shipmentRoutePrefix": SHIPMENT_ROUTE_PREFIX,
        "actions": list(ACTIONS),
        "unavailable": list(UNAVAILABLE_CONTEXT),
        "error": None,
    }


__all__ = [
    "ACTIONS",
    "ALLOCATED",
    "ALL",
    "EMPTY",
    "MATCHED",
    "MAX_ROWS",
    "MONEY",
    "NO_SOURCE",
    "OBLIGATION",
    "OK",
    "PARTIAL",
    "REVIEW",
    "REVIEW_REQUIRED",
    "UNALLOCATED",
    "UNAVAILABLE_CONTEXT",
    "UNMATCHED",
    "apply_filters",
    "reconciliation_projection",
    "reconciliation_summary",
    "reconciliation_view",
]
