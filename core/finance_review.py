"""Read-only Finance Review projection for LOG-C11.

The module composes canonical obligations, transactions, allocations and
corrections. It never writes, edits balances, auto-allocates, or converts
currencies.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from core.financial_ledger import (
    ALLOCATIONS,
    CORRECTIONS,
    OBLIGATIONS,
    RESTRICTED,
    REVIEW_REQUIRED,
    TRANSACTIONS,
    UNKNOWN,
    build_partner_financial_position,
    derive_obligation_position,
    derive_transaction_position,
)
from core import database

STATUS_CONFIRMED = "CONFIRMED"
STATUS_DUE_SOON = "DUE SOON"
STATUS_OVERDUE = "OVERDUE"
STATUS_HELD = "HELD CREDIT"
STATUS_UNALLOCATED = "UNALLOCATED"
STATUS_REVIEW = "REVIEW REQUIRED"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_RESTRICTED = "RESTRICTED"
STATUS_MISSING_EVIDENCE = "MISSING EVIDENCE"
STATUS_SETTLED = "SETTLED"

BUCKET_OBLIGATION = "OBLIGATION"
BUCKET_TRANSACTION = "TRANSACTION"
BUCKET_ALLOCATION = "ALLOCATION"
BUCKET_CORRECTION = "CORRECTION / REVERSAL"

ACTIONABLE_STATUSES = (
    STATUS_OVERDUE,
    STATUS_DUE_SOON,
    STATUS_UNALLOCATED,
    STATUS_HELD,
    STATUS_REVIEW,
    STATUS_UNKNOWN,
    STATUS_RESTRICTED,
    STATUS_MISSING_EVIDENCE,
)


def _text(value: Any, default: str = UNKNOWN) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text and text.casefold() not in {"none", "null", "nan"} else default


def _amount(value: Any) -> float:
    try:
        parsed = Decimal(str(value or 0))
    except (InvalidOperation, ValueError, TypeError):
        return 0.0
    return float(parsed) if parsed.is_finite() else 0.0


def _date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = _text(value, "")
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw[:19], fmt).date()
        except ValueError:
            continue
    return None


def _party(raw: Any) -> dict[str, str]:
    if isinstance(raw, Mapping):
        party_type = _text(raw.get("party_type") or raw.get("type"), UNKNOWN)
        party_id = _text(raw.get("party_id") or raw.get("id") or raw.get("key"), UNKNOWN)
        name = _text(raw.get("name") or raw.get("label") or party_id, UNKNOWN)
        return {"party_type": party_type, "party_id": party_id, "name": name}
    value = _text(raw)
    return {"party_type": UNKNOWN, "party_id": value, "name": value}


def _party_from(record: Mapping[str, Any], *aliases: str) -> dict[str, str]:
    for alias in aliases:
        if record.get(alias) not in (None, ""):
            return _party(record.get(alias))
    return _party(None)


def _shipment_ids(record: Mapping[str, Any]) -> list[str]:
    raw = record.get("shipment_ids")
    values = list(raw) if isinstance(raw, (list, tuple, set)) else [raw]
    values.append(record.get("shipment_id"))
    result: list[str] = []
    for value in values:
        text = _text(value, "")
        if text and text not in result:
            result.append(text)
    return result


def _currency(record: Mapping[str, Any]) -> str:
    return _text(record.get("currency") or record.get("currency_code"), UNKNOWN).upper()


def _record_id(record: Mapping[str, Any], fallback: str) -> str:
    return _text(record.get("id") or record.get("record_id") or record.get("_id"), fallback)


def _classification(record: Mapping[str, Any]) -> str:
    value = _text(record.get("classification_status") or record.get("status"), STATUS_CONFIRMED).upper()
    if value in {"KNOWN", "ACTIVE", "OK"}:
        return STATUS_CONFIRMED
    if value in {UNKNOWN, "UNCONFIRMED"}:
        return STATUS_UNKNOWN
    if value in {REVIEW_REQUIRED, "REVIEW"}:
        return STATUS_REVIEW
    return value


def _restriction(record: Mapping[str, Any]) -> str:
    raw = record.get("restriction")
    if isinstance(raw, Mapping):
        value = raw.get("status")
    else:
        value = raw or record.get("restriction_status")
    value = _text(value, "NONE").upper()
    if record.get("restricted") is True:
        return STATUS_RESTRICTED
    if value in {RESTRICTED, STATUS_RESTRICTED}:
        return STATUS_RESTRICTED
    if value in {UNKNOWN, STATUS_UNKNOWN}:
        return STATUS_UNKNOWN
    if value in {REVIEW_REQUIRED, STATUS_REVIEW}:
        return STATUS_REVIEW
    return "NONE"


def _has_evidence(record: Mapping[str, Any]) -> bool:
    for key in ("evidence_refs", "source_refs", "evidence", "source", "provenance"):
        value = record.get(key)
        if value not in (None, "", [], {}):
            return True
    return False


def _evidence(record: Mapping[str, Any]) -> list[Any]:
    values: list[Any] = []
    for key in ("evidence_refs", "source_refs", "evidence", "source", "provenance"):
        value = record.get(key)
        if value not in (None, "", [], {}):
            values.append(deepcopy(value))
    return values


def _reason(status: str, record: Mapping[str, Any], *, amount: float = 0.0) -> str:
    if status == STATUS_UNKNOWN:
        return "Canonical record chưa xác định; không đưa vào confirmed total."
    if status == STATUS_RESTRICTED:
        return "Khoản tiền bị restricted hoặc chưa xác định allowed use; không tự động sử dụng."
    if status == STATUS_MISSING_EVIDENCE:
        return "Record thiếu evidence/provenance để kiểm tra độc lập."
    if status == STATUS_UNALLOCATED:
        return "Transaction còn remainder chưa allocation; không ép vào shipment."
    if status == STATUS_HELD:
        return "Credit đang được holder giữ; cần xác định mục đích và beneficial owner."
    if status == STATUS_OVERDUE:
        return "Obligation đã quá due date theo canonical due date."
    if status == STATUS_DUE_SOON:
        return "Obligation sắp đến hạn theo canonical due date."
    if status == STATUS_REVIEW:
        return "Record có classification hoặc reconciliation state cần review."
    if status == STATUS_SETTLED:
        return "Obligation đã được settle theo allocation history."
    return str(record.get("review_reason") or "Record confirmed từ canonical source.")


def _record_status(record: Mapping[str, Any], *, due: date | None, today: date, remaining: float = 0.0) -> str:
    classification = _classification(record)
    restriction = _restriction(record)
    if restriction == STATUS_RESTRICTED:
        return STATUS_RESTRICTED
    if classification == STATUS_UNKNOWN:
        return STATUS_UNKNOWN
    if classification == STATUS_REVIEW or restriction == STATUS_REVIEW:
        return STATUS_REVIEW
    if not _has_evidence(record):
        return STATUS_MISSING_EVIDENCE
    if due is not None and remaining > 0:
        if due < today:
            return STATUS_OVERDUE
        if (due - today).days <= 7:
            return STATUS_DUE_SOON
    return STATUS_CONFIRMED


def _party_matches(record: Mapping[str, Any], party_type: str | None, party_id: str | None) -> bool:
    if not party_id:
        return True
    wanted = party_id.strip().casefold()
    candidates: list[dict[str, str]] = []
    for key in ("party", "from_party", "to_party", "source_party", "payer", "payee", "holder", "holder_party", "beneficial_owner", "customer", "partner"):
        if record.get(key) not in (None, ""):
            candidates.append(_party(record.get(key)))
    for key in ("customer_id", "partner_id", "party_id"):
        if record.get(key) not in (None, ""):
            candidates.append(_party({"party_type": party_type or UNKNOWN, "party_id": record.get(key), "name": record.get(key)}))
    for candidate in candidates:
        if party_type and party_type.casefold() not in {"", "all", "tất cả"}:
            if candidate["party_type"].casefold() not in {party_type.casefold(), UNKNOWN.casefold()}:
                continue
        if wanted in {candidate["party_id"].casefold(), candidate["name"].casefold()}:
            return True
    return False


def _search_matches(item: Mapping[str, Any], search: str) -> bool:
    if not search:
        return True
    haystack = " ".join(str(item.get(key) or "") for key in (
        "record_id", "record_type", "bucket", "payer", "payee", "holder",
        "beneficial_owner", "party", "shipment_ids", "currency", "reason",
        "reference", "source",
    )).casefold()
    return search.casefold() in haystack


def _item(*, record: Mapping[str, Any], record_type: str, bucket: str, status: str,
          amount: float, outstanding: float = 0.0, allocated: float = 0.0,
          due: date | None = None, reason: str, formula: str, payer: dict[str, str],
          payee: dict[str, str], holder: dict[str, str], beneficial_owner: dict[str, str],
          source_ids: list[str] | None = None) -> dict[str, Any]:
    record_id = _record_id(record, record_type)
    shipment_ids = _shipment_ids(record)
    return {
        "item_id": f"{record_type}:{record_id}",
        "record_id": record_id,
        "record_type": record_type,
        "bucket": bucket,
        "status": status,
        "currency": _currency(record),
        "amount": round(amount, 6),
        "allocated": round(allocated, 6),
        "outstanding": round(outstanding, 6),
        "due_date": due.isoformat() if due else UNKNOWN,
        "payer": payer["name"],
        "payer_id": payer["party_id"],
        "payee": payee["name"],
        "payee_id": payee["party_id"],
        "holder": holder["name"],
        "holder_id": holder["party_id"],
        "beneficial_owner": beneficial_owner["name"],
        "beneficial_owner_id": beneficial_owner["party_id"],
        "party": (payee["name"] if payee["name"] != UNKNOWN else holder["name"] if holder["name"] != UNKNOWN else payer["name"]),
        "party_id": (payee["party_id"] if payee["party_id"] != UNKNOWN else holder["party_id"] if holder["party_id"] != UNKNOWN else payer["party_id"]),
        "party_type": (payee["party_type"] if payee["party_type"] != UNKNOWN else holder["party_type"] if holder["party_type"] != UNKNOWN else payer["party_type"]),
        "shipment_ids": shipment_ids,
        "reason": reason,
        "next_action": "Mở detail và kiểm tra canonical evidence; không tự sửa số dư.",
        "formula": formula,
        "source_record_ids": source_ids or [record_id],
        "evidence": _evidence(record),
        "read_only": True,
        "source": record.get("source") or record.get("provenance") or "canonical financial ledger",
        "raw_record": deepcopy(dict(record)),
    }


def _retarget_item(item: dict[str, Any], party_type: str | None, party_id: str | None) -> dict[str, Any]:
    if not party_id:
        return item
    wanted = party_id.casefold()
    candidates = (
        ("payer", "payer_id"),
        ("payee", "payee_id"),
        ("holder", "holder_id"),
        ("beneficial_owner", "beneficial_owner_id"),
    )
    for name_key, id_key in candidates:
        value = _text(item.get(name_key), "")
        identifier = _text(item.get(id_key), "")
        if wanted not in {value.casefold(), identifier.casefold()}:
            continue
        if party_type and party_type.casefold() not in {"", "all", "tất cả"}:
            if name_key == "payer" and item.get("payer_id") != UNKNOWN and party_type.casefold() not in {"customer", "partner", "factory"}:
                continue
        item["party"] = value or UNKNOWN
        item["party_id"] = identifier or UNKNOWN
        item["party_type"] = party_type or item.get("party_type") or UNKNOWN
        return item
    return item


def build_finance_review_items(
    obligations: Iterable[Mapping[str, Any]],
    transactions: Iterable[Mapping[str, Any]],
    allocations: Iterable[Mapping[str, Any]],
    corrections: Iterable[Mapping[str, Any]] | None = None,
    *,
    today: date | None = None,
    party_type: str | None = None,
    party_id: str | None = None,
    shipment_id: str | None = None,
    internal_sale_owner: str | None = None,
    currency: str | None = None,
    search: str = "",
) -> list[dict[str, Any]]:
    as_of = today or date.today()
    obligations_rows = [dict(row) for row in obligations if isinstance(row, Mapping)]
    transactions_rows = [dict(row) for row in transactions if isinstance(row, Mapping)]
    allocation_rows = [dict(row) for row in allocations if isinstance(row, Mapping)]
    correction_rows = [dict(row) for row in (corrections or []) if isinstance(row, Mapping)]
    items: list[dict[str, Any]] = []

    def selected(record: Mapping[str, Any]) -> bool:
        if not _party_matches(record, party_type, party_id):
            return False
        if shipment_id and shipment_id.casefold() not in {value.casefold() for value in _shipment_ids(record)}:
            return False
        if internal_sale_owner:
            owner = _text(record.get("internal_sale_owner"), "").casefold()
            if owner != internal_sale_owner.casefold():
                return False
        if currency and _currency(record) != currency.upper():
            return False
        return True

    allocation_by_obligation: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    allocation_by_transaction: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for allocation in allocation_rows:
        allocation_by_obligation[_text(allocation.get("obligation_id"), "")].append(allocation)
        allocation_by_transaction[_text(allocation.get("transaction_id"), "")].append(allocation)

    for obligation in obligations_rows:
        if not selected(obligation):
            continue
        record_id = _record_id(obligation, "obligation")
        position = derive_obligation_position(obligation, allocation_by_obligation.get(record_id, []))
        amount = _amount(obligation.get("amount"))
        outstanding = _amount(position.get("outstanding"))
        allocated = max(amount - outstanding, 0.0)
        due = _date(obligation.get("due_date") or obligation.get("due"))
        status = _record_status(obligation, due=due, today=as_of, remaining=outstanding)
        if status == STATUS_CONFIRMED and outstanding <= 0:
            status = STATUS_SETTLED
        item = _item(
            record=obligation,
            record_type="obligation",
            bucket=BUCKET_OBLIGATION,
            status=status,
            amount=amount,
            outstanding=outstanding,
            allocated=allocated,
            due=due,
            reason=_reason(status, obligation, amount=outstanding),
            formula="outstanding = obligation.amount - effective allocations",
            payer=_party_from(obligation, "from_party", "obligor", "payer"),
            payee=_party_from(obligation, "to_party", "creditor", "payee", "party"),
            holder=_party_from(obligation, "holder"),
            beneficial_owner=_party_from(obligation, "beneficial_owner"),
            source_ids=[record_id] + [_record_id(row, "allocation") for row in allocation_by_obligation.get(record_id, [])],
        )
        items.append(item)

    for transaction in transactions_rows:
        if not selected(transaction):
            continue
        record_id = _record_id(transaction, "transaction")
        position = derive_transaction_position(transaction, allocation_by_transaction.get(record_id, []))
        amount = _amount(transaction.get("amount"))
        unallocated = _amount(position.get("unallocated"))
        due = _date(transaction.get("value_date") or transaction.get("transaction_date") or transaction.get("date"))
        status = _record_status(transaction, due=due, today=as_of, remaining=unallocated)
        if unallocated > 0 and status == STATUS_CONFIRMED:
            status = STATUS_UNALLOCATED
        elif unallocated <= 0 and status == STATUS_CONFIRMED:
            status = STATUS_CONFIRMED
        bucket = BUCKET_TRANSACTION
        items.append(_item(
            record=transaction,
            record_type="transaction",
            bucket=bucket,
            status=status,
            amount=amount,
            outstanding=unallocated,
            allocated=max(amount - unallocated, 0.0),
            due=due,
            reason=_reason(status, transaction, amount=unallocated),
            formula="unallocated = transaction.amount - effective allocations",
            payer=_party_from(transaction, "from_party", "source_party", "payer", "party"),
            payee=_party_from(transaction, "to_party", "payee"),
            holder=_party_from(transaction, "holder", "holder_party"),
            beneficial_owner=_party_from(transaction, "beneficial_owner"),
            source_ids=[record_id] + [_record_id(row, "allocation") for row in allocation_by_transaction.get(record_id, [])],
        ))

    for allocation in allocation_rows:
        if not selected(allocation):
            continue
        allocation_id = _record_id(allocation, "allocation")
        status = _record_status(allocation, due=None, today=as_of, remaining=0.0)
        if status == STATUS_CONFIRMED:
            status = "ALLOCATED"
        amount = _amount(allocation.get("amount"))
        items.append(_item(
            record=allocation,
            record_type="allocation",
            bucket=BUCKET_ALLOCATION,
            status=status,
            amount=amount,
            allocated=amount,
            reason=_reason(status, allocation, amount=amount),
            formula="allocation is linked to one transaction and one obligation",
            payer=_party_from(allocation, "from_party", "payer"),
            payee=_party_from(allocation, "to_party", "payee"),
            holder=_party_from(allocation, "holder"),
            beneficial_owner=_party_from(allocation, "beneficial_owner"),
        ))

    for correction in correction_rows:
        if not selected(correction):
            continue
        status = _record_status(correction, due=None, today=as_of, remaining=0.0)
        if status == STATUS_CONFIRMED:
            status = STATUS_REVIEW
        amount = _amount(correction.get("amount") or correction.get("reversed_amount"))
        items.append(_item(
            record=correction,
            record_type="correction",
            bucket=BUCKET_CORRECTION,
            status=status,
            amount=amount,
            reason=_reason(status, correction, amount=amount),
            formula="correction/reversal preserves original history and changes derived position",
            payer=_party_from(correction, "from_party", "payer"),
            payee=_party_from(correction, "to_party", "payee"),
            holder=_party_from(correction, "holder"),
            beneficial_owner=_party_from(correction, "beneficial_owner"),
        ))

    result = [item for item in items if _search_matches(item, search)]
    for item in result:
        _retarget_item(item, party_type, party_id)
    status_rank = {
        STATUS_OVERDUE: 0, STATUS_RESTRICTED: 1, STATUS_UNKNOWN: 2,
        STATUS_MISSING_EVIDENCE: 3, STATUS_UNALLOCATED: 4, STATUS_HELD: 5,
        STATUS_REVIEW: 6, STATUS_DUE_SOON: 7, STATUS_CONFIRMED: 8,
        STATUS_SETTLED: 9, "ALLOCATED": 10,
    }
    result.sort(key=lambda item: (status_rank.get(item["status"], 20), item["currency"], item["record_type"], item["record_id"]))
    return result


def summarize_finance_review(items: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    totals: dict[str, dict[str, float]] = defaultdict(lambda: {
        "confirmed_outstanding": 0.0,
        "confirmed_unallocated": 0.0,
        "excluded_amount": 0.0,
        "transaction_amount": 0.0,
        "obligation_amount": 0.0,
    })
    counts: dict[str, int] = defaultdict(int)
    for item in items:
        currency = _text(item.get("currency"), UNKNOWN)
        status = _text(item.get("status"), STATUS_UNKNOWN)
        bucket = _text(item.get("bucket"), "")
        amount = _amount(item.get("amount"))
        outstanding = _amount(item.get("outstanding"))
        counts[status] += 1
        if status in {STATUS_UNKNOWN, STATUS_RESTRICTED, STATUS_MISSING_EVIDENCE, STATUS_REVIEW}:
            totals[currency]["excluded_amount"] += amount
            continue
        if bucket == BUCKET_OBLIGATION:
            totals[currency]["obligation_amount"] += amount
            totals[currency]["confirmed_outstanding"] += outstanding
        if bucket == BUCKET_TRANSACTION:
            totals[currency]["transaction_amount"] += amount
            totals[currency]["confirmed_unallocated"] += outstanding
    return {
        "totals_by_currency": {currency: dict(values) for currency, values in sorted(totals.items())},
        "counts": dict(counts),
        "currencies": sorted(totals),
        "read_only": True,
        "derived": True,
        "formula": "confirmed totals exclude UNKNOWN, RESTRICTED, MISSING EVIDENCE and REVIEW REQUIRED items; currencies are never combined",
    }


def _read_collection(db: Any, collection_name: str) -> list[dict[str, Any]]:
    if db is None:
        return []
    try:
        return [dict(row) for row in db[collection_name].find({})]
    except Exception:
        return []


def build_finance_review_from_db(
    *,
    db: Any = None,
    party_type: str | None = None,
    party_id: str | None = None,
    shipment_id: str | None = None,
    internal_sale_owner: str | None = None,
    currency: str | None = None,
    search: str = "",
    today: date | None = None,
) -> dict[str, Any]:
    db = db if db is not None else database.get_db()
    if db is None:
        return {
            "items": [],
            "summary": summarize_finance_review([]),
            "status": STATUS_UNKNOWN,
            "error": "Canonical financial database is not available.",
            "read_only": True,
        }
    obligations = _read_collection(db, OBLIGATIONS)
    transactions = _read_collection(db, TRANSACTIONS)
    allocations = _read_collection(db, ALLOCATIONS)
    corrections = _read_collection(db, CORRECTIONS)
    items = build_finance_review_items(
        obligations, transactions, allocations, corrections,
        today=today, party_type=party_type, party_id=party_id,
        shipment_id=shipment_id, internal_sale_owner=internal_sale_owner,
        currency=currency, search=search,
    )
    result = {
        "items": items,
        "summary": summarize_finance_review(items),
        "status": STATUS_REVIEW if any(item["status"] in ACTIONABLE_STATUSES for item in items) else STATUS_CONFIRMED,
        "read_only": True,
        "source": "core.financial_ledger canonical collections",
        "filters": {"party_type": party_type or "ALL", "party_id": party_id or "", "shipment_id": shipment_id or "", "internal_sale_owner": internal_sale_owner or "", "currency": currency or "ALL", "search": search},
    }
    if party_type and party_type.casefold() == "partner" and party_id:
        result["partner_position"] = build_partner_financial_position({"party_type": "partner", "party_id": party_id, "name": party_id}, internal_sale_owner=internal_sale_owner, db=db)
    return result


__all__ = [
    "ACTIONABLE_STATUSES", "BUCKET_ALLOCATION", "BUCKET_CORRECTION", "BUCKET_OBLIGATION", "BUCKET_TRANSACTION",
    "STATUS_CONFIRMED", "STATUS_DUE_SOON", "STATUS_OVERDUE", "STATUS_HELD", "STATUS_UNALLOCATED", "STATUS_REVIEW", "STATUS_UNKNOWN", "STATUS_RESTRICTED", "STATUS_MISSING_EVIDENCE", "STATUS_SETTLED",
    "build_finance_review_items", "build_finance_review_from_db", "summarize_finance_review",
]
