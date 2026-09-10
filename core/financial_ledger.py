"""Canonical, shipment-optional financial ledger primitives.

The existing application has several legacy financial stores.  B2 adds one
small source of truth for new canonical records without migrating or
overwriting those stores.  Amounts that can be derived from history are never
persisted as editable fields: projections calculate effective allocations at
read time.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from copy import deepcopy
from decimal import Decimal
from typing import Any
from uuid import uuid4

from pymongo.errors import DuplicateKeyError, PyMongoError

import core.database as database
from core.utils import to_decimal, utc_now


OBLIGATIONS = "financial_obligations"
TRANSACTIONS = "financial_transactions"
ALLOCATIONS = "financial_allocations"
CORRECTIONS = "financial_corrections"
ACTION_REQUESTS = "financial_action_requests"

ACTIVE = "active"
INACTIVE_STATUSES = frozenset({"reversed", "cancelled", "void", "inactive"})
CONFIRMED = "CONFIRMED"
UNKNOWN = "UNKNOWN"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
NONE_RESTRICTION = "NONE"
RESTRICTED = "RESTRICTED"

RECEIVED_ON_BEHALF_KINDS = frozenset(
    {
        "received_on_behalf",
        "received_on_behalf_payment",
        "received_for_beneficiary",
    }
)
PAID_ON_BEHALF_KINDS = frozenset(
    {
        "paid_on_behalf",
        "spent_on_behalf",
        "paid_for_beneficiary",
    }
)


class FinancialLedgerValidationError(ValueError):
    """Raised for a request that cannot be represented safely."""


def _error(message: str) -> tuple[bool, dict[str, Any], str]:
    database._set_last_error(message)
    return False, {}, message


def _require_finance_write() -> bool:
    """Fail closed before any canonical finance mutation is attempted."""

    from core.auth import can_operate_business

    if can_operate_business("finance_write"):
        return True
    database._set_last_error("Bạn không có quyền ghi nhận Finance Actual.")
    return False


def _party(value: Any, *, required: bool = True) -> dict[str, Any] | None:
    if value is None or value == "":
        if required:
            raise FinancialLedgerValidationError("party is required")
        return None
    if isinstance(value, str):
        party_id = value.strip()
        if not party_id:
            if required:
                raise FinancialLedgerValidationError("party id is required")
            return None
        return {"party_type": "unknown", "party_id": party_id, "name": party_id}
    if not isinstance(value, Mapping):
        raise FinancialLedgerValidationError("party must be a string or mapping")
    party_id = str(value.get("party_id") or value.get("id") or value.get("key") or "").strip()
    if not party_id:
        if required:
            raise FinancialLedgerValidationError("party_id is required")
        return None
    result = {
        "party_type": str(value.get("party_type") or value.get("type") or "unknown").strip().lower(),
        "party_id": party_id,
        "name": str(value.get("name") or value.get("display_name") or party_id).strip(),
    }
    if value.get("source_system") not in (None, ""):
        result["source_system"] = str(value["source_system"]).strip()
    if value.get("raw_term") not in (None, ""):
        result["raw_term"] = deepcopy(value["raw_term"])
    return result


def party_key(value: Any) -> str:
    """Return a stable comparison key without merging party semantics."""

    normalized = _party(value, required=False)
    if not normalized:
        return ""
    return f"{normalized['party_type']}:{normalized['party_id'].strip().upper()}"


def _optional_party(value: Any) -> dict[str, Any] | None:
    return _party(value, required=False)


def _string_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, Iterable) and not isinstance(value, (bytes, Mapping)):
        values = list(value)
    else:
        values = [value]
    result: list[str] = []
    for item in values:
        clean = str(item or "").strip()
        if clean and clean not in result:
            result.append(clean)
    return result


def _shipment_ids(document: Mapping[str, Any]) -> list[str]:
    values = _string_list(document.get("shipment_ids"))
    values.extend(_string_list(document.get("shipment_id")))
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def _shipment_fields(shipment_ids: Iterable[str]) -> dict[str, Any]:
    values = _string_list(list(shipment_ids))
    return {"shipment_ids": values, "shipment_id": values[0] if len(values) == 1 else None}


def _references(value: Any) -> list[dict[str, Any]]:
    if value is None or value == "":
        return []
    if isinstance(value, Mapping):
        values = [value]
    elif isinstance(value, str):
        values = [{"reference": value}]
    elif isinstance(value, Iterable) and not isinstance(value, (bytes, str)):
        values = list(value)
    else:
        values = [{"raw": deepcopy(value)}]
    result: list[dict[str, Any]] = []
    for item in values:
        if isinstance(item, Mapping):
            result.append(deepcopy(dict(item)))
        else:
            result.append({"raw": deepcopy(item)})
    return result


def _provenance(document: Mapping[str, Any]) -> dict[str, Any]:
    value = document.get("provenance")
    result = deepcopy(dict(value)) if isinstance(value, Mapping) else {}
    aliases = {
        "source_file": "source_file",
        "source_sheet": "sheet",
        "sheet": "sheet",
        "source_row": "row",
        "row": "row",
        "source_cell_range": "cell_range",
        "cell_range": "cell_range",
        "source_reference": "reference",
        "raw_note": "raw_note",
        "mapping_status": "mapping_status",
        "review_status": "review_status",
    }
    for source, target in aliases.items():
        if source in document and document[source] not in (None, ""):
            result[target] = deepcopy(document[source])
    return result


def _currency(value: Any) -> str:
    currency = str(value or "").strip().upper()
    if not currency:
        raise FinancialLedgerValidationError("currency is required")
    return currency


def _amount(value: Any) -> float:
    parsed = to_decimal(value)
    if not parsed.is_finite() or parsed <= 0:
        raise FinancialLedgerValidationError("amount must be greater than zero")
    return float(parsed)


def _status(value: Any, default: str = CONFIRMED) -> str:
    clean = str(value or default).strip().upper()
    if clean in {"KNOWN", "CONFIRMED", "ACTIVE", "OK"}:
        return CONFIRMED
    if clean in {UNKNOWN, REVIEW_REQUIRED, "REVIEW", "UNCONFIRMED"}:
        return REVIEW_REQUIRED if clean in {REVIEW_REQUIRED, "REVIEW", "UNCONFIRMED"} else UNKNOWN
    return clean


def _restriction(document: Mapping[str, Any]) -> dict[str, Any]:
    raw = document.get("restriction")
    if isinstance(raw, Mapping):
        result = deepcopy(dict(raw))
    elif raw not in (None, ""):
        result = {"status": raw}
    else:
        result = {}

    allowed_use = document.get("allowed_use")
    if isinstance(allowed_use, Mapping):
        result.setdefault("allowed_use", deepcopy(dict(allowed_use)))
        if "allowed_purposes" not in result:
            result["allowed_purposes"] = deepcopy(
                allowed_use.get("allowed_purposes")
                or allowed_use.get("purposes")
                or allowed_use.get("obligation_purposes")
                or []
            )
        if "allowed_to_party_keys" not in result:
            result["allowed_to_party_keys"] = deepcopy(
                allowed_use.get("allowed_to_party_keys")
                or allowed_use.get("allowed_party_keys")
                or []
            )
    status = str(result.get("status") or document.get("restriction_status") or "").strip().upper()
    if document.get("restricted") is True:
        status = RESTRICTED
    if status in {"", "ALLOWED", "NONE", "UNRESTRICTED"}:
        status = NONE_RESTRICTION
    elif status not in {RESTRICTED, UNKNOWN, REVIEW_REQUIRED}:
        status = REVIEW_REQUIRED
    result["status"] = status
    result["allowed_purposes"] = _string_list(result.get("allowed_purposes"))
    result["allowed_to_party_keys"] = _string_list(result.get("allowed_to_party_keys"))
    result["allowed_from_party_keys"] = _string_list(result.get("allowed_from_party_keys"))
    return result


def _stable_fingerprint(document: Mapping[str, Any]) -> str:
    stable = deepcopy(dict(document))
    for key in ("id", "request_id", "created_at", "created_by", "updated_at", "updated_by", "status"):
        stable.pop(key, None)
    return database._financial_fingerprint(stable)


def _record_result(document: Mapping[str, Any], record_type: str) -> dict[str, Any]:
    return {
        "record_type": record_type,
        "id": str(document.get("id") or ""),
        "request_id": str(document.get("request_id") or ""),
        "shipment_ids": deepcopy(document.get("shipment_ids") or []),
        "currency": document.get("currency"),
        "amount": float(to_decimal(document.get("amount"))),
        "status": document.get("status") or ACTIVE,
    }


def _existing_action(existing: Mapping[str, Any], action_type: str, fingerprint: str) -> tuple[bool, dict[str, Any], str]:
    if existing.get("action_type") != action_type or existing.get("fingerprint") != fingerprint:
        return _error("request identity is already bound to a different financial action")
    return True, deepcopy(dict(existing.get("result") or {})), "financial action already applied"


def _all(db: Any, collection: str, session: Any = None) -> list[dict[str, Any]]:
    cursor = db[collection].find({}, {"_id": 0}, session=session)
    return [deepcopy(dict(item)) for item in cursor if isinstance(item, Mapping)]


def _effective(document: Mapping[str, Any]) -> bool:
    status = str(document.get("status") or ACTIVE).strip().lower()
    return status not in INACTIVE_STATUSES and not document.get("is_reversed")


def _allocation_rows(
    allocations: Iterable[Mapping[str, Any]],
    *,
    transaction_id: str | None = None,
    obligation_id: str | None = None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for allocation in allocations:
        if not _effective(allocation):
            continue
        if transaction_id is not None and str(allocation.get("transaction_id") or "") != transaction_id:
            continue
        if obligation_id is not None and str(allocation.get("obligation_id") or "") != obligation_id:
            continue
        result.append(deepcopy(dict(allocation)))
    return result


def derive_transaction_position(
    transaction: Mapping[str, Any],
    allocations: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Derive allocated/unallocated values; never writes a balance."""

    amount = to_decimal(transaction.get("amount"))
    currency = str(transaction.get("currency") or "").upper()
    rows = _allocation_rows(allocations, transaction_id=str(transaction.get("id") or ""))
    allocated = Decimal("0")
    allocation_ids: list[str] = []
    incompatible: list[str] = []
    for row in rows:
        row_currency = str(row.get("currency") or "").upper()
        row_amount = to_decimal(row.get("amount"))
        if row_currency != currency:
            incompatible.append(str(row.get("id") or ""))
            continue
        allocated += row_amount
        allocation_ids.append(str(row.get("id") or ""))
    remaining = amount - allocated
    overallocated = remaining < 0
    result = {
        "transaction_id": str(transaction.get("id") or ""),
        "amount": float(amount),
        "currency": currency,
        "allocated": float(allocated),
        "unallocated": float(remaining),
        "allocation_ids": allocation_ids,
        "status": REVIEW_REQUIRED if incompatible or overallocated else CONFIRMED,
        "incompatible_allocation_ids": incompatible,
        "overallocated": overallocated,
        "formula": f"{float(amount):g} - {float(allocated):g} = {float(remaining):g} {currency}",
    }
    return result


def derive_obligation_position(
    obligation: Mapping[str, Any],
    allocations: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Derive outstanding obligation from effective allocations."""

    amount = to_decimal(obligation.get("amount"))
    currency = str(obligation.get("currency") or "").upper()
    rows = _allocation_rows(allocations, obligation_id=str(obligation.get("id") or ""))
    allocated = Decimal("0")
    allocation_ids: list[str] = []
    incompatible: list[str] = []
    for row in rows:
        row_currency = str(row.get("currency") or "").upper()
        row_amount = to_decimal(row.get("amount"))
        if row_currency != currency:
            incompatible.append(str(row.get("id") or ""))
            continue
        allocated += row_amount
        allocation_ids.append(str(row.get("id") or ""))
    remaining = amount - allocated
    overallocated = remaining < 0
    return {
        "obligation_id": str(obligation.get("id") or ""),
        "amount": float(amount),
        "currency": currency,
        "allocated": float(allocated),
        "outstanding": float(remaining),
        "allocation_ids": allocation_ids,
        "status": REVIEW_REQUIRED if incompatible or overallocated else CONFIRMED,
        "incompatible_allocation_ids": incompatible,
        "overallocated": overallocated,
        "formula": f"{float(amount):g} - {float(allocated):g} = {float(remaining):g} {currency}",
    }


def _obligation_payload(document: Mapping[str, Any], request_id: str, actor: str | None) -> dict[str, Any]:
    from_party = _party(document.get("from_party") or document.get("debtor"))
    to_party = _party(document.get("to_party") or document.get("creditor"))
    amount = _amount(document.get("amount"))
    currency = _currency(document.get("currency"))
    purpose = str(document.get("purpose") or document.get("nature") or "").strip()
    if not purpose:
        raise FinancialLedgerValidationError("obligation purpose is required")
    shipment_fields = _shipment_fields(_shipment_ids(document))
    actor_context = database._actor_context(actor)
    record = {
        "id": str(document.get("id") or f"OBL-{uuid4().hex.upper()}"),
        "record_type": "obligation",
        "from_party": from_party,
        "from_party_key": party_key(from_party),
        "to_party": to_party,
        "to_party_key": party_key(to_party),
        "amount": amount,
        "currency": currency,
        "original_amount": amount,
        "original_currency": currency,
        "purpose": purpose,
        "due_date": deepcopy(document.get("due_date")),
        "internal_sale_owner": str(document.get("internal_sale_owner") or "").strip() or None,
        "evidence_refs": _references(document.get("evidence_refs") or document.get("evidence")),
        "source_refs": _references(document.get("source_refs") or document.get("source")),
        "provenance": _provenance(document),
        "review_status": _status(document.get("review_status") or document.get("mapping_status")),
        "status": ACTIVE,
        "request_id": request_id,
        "created_at": deepcopy(document.get("created_at") or utc_now()),
        "created_by": actor_context["username"],
        "created_by_user_id": actor_context["user_id"],
        "created_by_role": actor_context["role"],
        "updated_at": utc_now(),
        "updated_by": actor_context["username"],
        "updated_by_user_id": actor_context["user_id"],
        "updated_by_role": actor_context["role"],
    }
    record.update(shipment_fields)
    if document.get("note") not in (None, ""):
        record["note"] = deepcopy(document["note"])
    return record


def _transaction_payload(document: Mapping[str, Any], request_id: str, actor: str | None) -> dict[str, Any]:
    source_party = _party(document.get("source_party") or document.get("from_party") or document.get("payer"))
    holder_party = _party(document.get("holder_party") or document.get("to_party") or document.get("receiver"))
    beneficial_owner = _optional_party(document.get("beneficial_owner") or document.get("fund_owner"))
    beneficiary_party = _optional_party(document.get("beneficiary_party") or document.get("beneficiary"))
    amount = _amount(document.get("amount"))
    currency = _currency(document.get("currency"))
    kind = str(document.get("transaction_kind") or document.get("kind") or "payment").strip().lower()
    classification_explicit = any(
        key in document for key in ("classification_status", "mapping_status", "review_status", "unknown")
    )
    classification = _status(
        document.get("classification_status")
        or document.get("mapping_status")
        or document.get("review_status")
        or (UNKNOWN if document.get("unknown") else CONFIRMED)
    )
    if not classification_explicit and beneficial_owner is None:
        classification = REVIEW_REQUIRED
    restriction = _restriction(document)
    shipment_fields = _shipment_fields(_shipment_ids(document))
    actor_context = database._actor_context(actor)
    record = {
        "id": str(document.get("id") or f"TX-{uuid4().hex.upper()}"),
        "record_type": "transaction",
        "source_party": source_party,
        "source_party_key": party_key(source_party),
        "holder_party": holder_party,
        "holder_party_key": party_key(holder_party),
        "beneficial_owner": beneficial_owner,
        "beneficial_owner_key": party_key(beneficial_owner),
        "beneficiary_party": beneficiary_party,
        "beneficiary_party_key": party_key(beneficiary_party),
        "amount": amount,
        "currency": currency,
        "original_amount": amount,
        "original_currency": currency,
        "transaction_kind": kind,
        "occurred_at": deepcopy(document.get("occurred_at") or document.get("date") or utc_now()),
        "request_id": request_id,
        "internal_sale_owner": str(document.get("internal_sale_owner") or "").strip() or None,
        "classification_status": classification,
        "restriction": restriction,
        "evidence_refs": _references(document.get("evidence_refs") or document.get("evidence")),
        "source_refs": _references(document.get("source_refs") or document.get("source")),
        "provenance": _provenance(document),
        "status": ACTIVE,
        "created_at": deepcopy(document.get("created_at") or utc_now()),
        "created_by": actor_context["username"],
        "created_by_user_id": actor_context["user_id"],
        "created_by_role": actor_context["role"],
        "updated_at": utc_now(),
        "updated_by": actor_context["username"],
        "updated_by_user_id": actor_context["user_id"],
        "updated_by_role": actor_context["role"],
    }
    record.update(shipment_fields)
    if document.get("fx_snapshot") is not None or document.get("fx") is not None:
        record["fx_snapshot"] = deepcopy(document.get("fx_snapshot") or document.get("fx"))
    if document.get("settlement") is not None:
        record["settlement"] = deepcopy(document["settlement"])
    for key in ("settlement_currency", "actual_amount_received", "bank_fee", "agent_fee"):
        if key in document:
            record[key] = deepcopy(document[key])
    if document.get("note") not in (None, ""):
        record["note"] = deepcopy(document["note"])
    return record


def _persist_new_record(
    collection: str,
    action_type: str,
    event_type: str,
    record_type: str,
    document: Mapping[str, Any],
    request_id: str,
    actor: str | None,
) -> tuple[bool, dict[str, Any], str]:
    if not _require_finance_write():
        return _error("Bạn không có quyền ghi nhận Finance Actual.")
    db = database.get_db()
    if db is None:
        return _error("MongoDB is not available")
    client = database._transaction_client(db)
    if client is None:
        return _error("financial ledger requires Mongo transaction support")
    payload = deepcopy(dict(document))
    payload.pop("_id", None)
    fingerprint = _stable_fingerprint(payload)
    actor_context = database._actor_context(actor)
    try:
        with client.start_session() as session:
            with session.start_transaction():
                existing = db[ACTION_REQUESTS].find_one({"request_id": request_id}, session=session)
                if existing:
                    return _existing_action(existing, action_type, fingerprint)
                db[collection].insert_one(payload, session=session)
                result = _record_result(payload, record_type)
                db[ACTION_REQUESTS].insert_one(
                    {
                        "request_id": request_id,
                        "action_type": action_type,
                        "fingerprint": fingerprint,
                        "status": "applied",
                        "shipment_id": payload.get("shipment_id"),
                        "result": result,
                        "created_at": utc_now(),
                        "created_by": actor_context["username"],
                        "created_by_user_id": actor_context["user_id"],
                        "created_by_role": actor_context["role"],
                    },
                    session=session,
                )
                database._audit(db, collection, str(payload["id"]), "create", before=None, after=payload, actor=actor, session=session)
                database._enqueue_domain_event(
                    db,
                    event_type,
                    {"record_type": record_type, "record_id": str(payload["id"]), "request_id": request_id},
                    session=session,
                )
                database._set_last_error("")
                return True, result, "financial record created"
    except DuplicateKeyError:
        existing = db[ACTION_REQUESTS].find_one({"request_id": request_id})
        if existing:
            return _existing_action(existing, action_type, fingerprint)
        return _error("financial request conflicted and could not be read back")
    except (PyMongoError, RuntimeError, ValueError) as exc:
        database.LOGGER.exception("financial ledger record write failed")
        return _error(str(exc))


def save_obligation(document: Mapping[str, Any], request_id: str, actor: str | None = None) -> tuple[bool, dict[str, Any], str]:
    """Create one obligation; shipment linkage is optional."""

    if not _require_finance_write():
        return _error("Bạn không có quyền ghi nhận Finance Actual.")
    request_id = str(request_id or "").strip()
    if not request_id:
        return _error("obligation requires request identity")
    try:
        payload = _obligation_payload(document, request_id, actor)
    except (FinancialLedgerValidationError, TypeError, ValueError) as exc:
        return _error(str(exc))
    return _persist_new_record(
        OBLIGATIONS,
        "financial_obligation_create",
        "financial.obligation.created",
        "obligation",
        payload,
        request_id,
        actor,
    )


def save_transaction(document: Mapping[str, Any], request_id: str, actor: str | None = None) -> tuple[bool, dict[str, Any], str]:
    """Create one money event; it may exist before or without a shipment."""

    if not _require_finance_write():
        return _error("Bạn không có quyền ghi nhận Finance Actual.")
    request_id = str(request_id or "").strip()
    if not request_id:
        return _error("transaction requires request identity")
    try:
        payload = _transaction_payload(document, request_id, actor)
    except (FinancialLedgerValidationError, TypeError, ValueError) as exc:
        return _error(str(exc))
    return _persist_new_record(
        TRANSACTIONS,
        "financial_transaction_create",
        "financial.transaction.created",
        "transaction",
        payload,
        request_id,
        actor,
    )


def _restriction_allows(transaction: Mapping[str, Any], obligation: Mapping[str, Any]) -> str | None:
    classification = str(transaction.get("classification_status") or REVIEW_REQUIRED).upper()
    if classification != CONFIRMED:
        return "transaction is UNKNOWN or REVIEW_REQUIRED"
    restriction = transaction.get("restriction") or {}
    restriction_status = str(restriction.get("status") or REVIEW_REQUIRED).upper()
    if restriction_status != NONE_RESTRICTION:
        return "transaction is RESTRICTED or has unknown allowed use"

    source_key = party_key(transaction.get("source_party"))
    beneficial_key = party_key(transaction.get("beneficial_owner"))
    holder_key = party_key(transaction.get("holder_party"))
    from_key = party_key(obligation.get("from_party"))
    to_key = party_key(obligation.get("to_party"))
    allowed_from = set(_string_list(restriction.get("allowed_from_party_keys")))
    allowed_to = set(_string_list(restriction.get("allowed_to_party_keys")))
    if allowed_from and from_key not in allowed_from:
        return "obligation payer is outside the allowed source parties"
    if allowed_to and to_key not in allowed_to:
        return "obligation beneficiary is outside the allowed target parties"
    if not holder_key:
        return "transaction holder is unknown"
    if source_key != from_key and beneficial_key != from_key and from_key not in allowed_from:
        return "fund ownership does not match the obligation payer"
    if holder_key != to_key and to_key not in allowed_to:
        return "holder/receiver is not the obligation beneficiary and no explicit intermediary rule exists"
    purposes = {value.strip().lower() for value in _string_list(restriction.get("allowed_purposes"))}
    if purposes and str(obligation.get("purpose") or "").strip().lower() not in purposes:
        return "obligation purpose is outside the allowed use"
    return None


def allocate_transaction(
    transaction_id: str,
    obligation_id: str,
    amount: Any,
    request_id: str,
    *,
    currency: str | None = None,
    shipment_ids: Iterable[str] | None = None,
    evidence_refs: Any = None,
    source_refs: Any = None,
    actor: str | None = None,
) -> tuple[bool, dict[str, Any], str]:
    """Allocate an effective credit to an obligation with all guards active."""

    if not _require_finance_write():
        return _error("Bạn không có quyền ghi nhận Finance Actual.")
    transaction_id = str(transaction_id or "").strip()
    obligation_id = str(obligation_id or "").strip()
    request_id = str(request_id or "").strip()
    if not transaction_id or not obligation_id or not request_id:
        return _error("allocation requires transaction, obligation, and request identity")
    try:
        allocation_amount = _amount(amount)
    except (FinancialLedgerValidationError, TypeError, ValueError) as exc:
        return _error(str(exc))
    fingerprint = database._financial_fingerprint(
        {
            "transaction_id": transaction_id,
            "obligation_id": obligation_id,
            "amount": allocation_amount,
            "currency": str(currency or "").upper() or None,
            "shipment_ids": _string_list(list(shipment_ids or [])),
            "evidence_refs": _references(evidence_refs),
            "source_refs": _references(source_refs),
        }
    )
    db = database.get_db()
    if db is None:
        return _error("MongoDB is not available")
    client = database._transaction_client(db)
    if client is None:
        return _error("financial ledger requires Mongo transaction support")
    actor_context = database._actor_context(actor)
    try:
        with client.start_session() as session:
            with session.start_transaction():
                existing = db[ACTION_REQUESTS].find_one({"request_id": request_id}, session=session)
                if existing:
                    return _existing_action(existing, "financial_allocation_create", fingerprint)
                transaction = db[TRANSACTIONS].find_one({"id": transaction_id}, {"_id": 0}, session=session)
                obligation = db[OBLIGATIONS].find_one({"id": obligation_id}, {"_id": 0}, session=session)
                if not transaction or not obligation:
                    raise FinancialLedgerValidationError("allocation target record was not found")
                if not _effective(transaction) or not _effective(obligation):
                    raise FinancialLedgerValidationError("allocation target is inactive or reversed")
                transaction_currency = str(transaction.get("currency") or "").upper()
                obligation_currency = str(obligation.get("currency") or "").upper()
                requested_currency = str(currency or transaction_currency).strip().upper()
                if transaction_currency != obligation_currency or requested_currency != transaction_currency:
                    raise FinancialLedgerValidationError("cross-currency allocation requires an explicit FX event")
                ownership_error = _restriction_allows(transaction, obligation)
                if ownership_error:
                    raise FinancialLedgerValidationError(ownership_error)
                allocations = _all(db, ALLOCATIONS, session=session)
                transaction_position = derive_transaction_position(transaction, allocations)
                obligation_position = derive_obligation_position(obligation, allocations)
                if transaction_position["status"] != CONFIRMED or obligation_position["status"] != CONFIRMED:
                    raise FinancialLedgerValidationError("allocation history has incompatible currency rows")
                if allocation_amount > to_decimal(transaction_position["unallocated"]):
                    raise FinancialLedgerValidationError("allocation exceeds transaction available amount")
                if allocation_amount > to_decimal(obligation_position["outstanding"]):
                    raise FinancialLedgerValidationError("allocation exceeds obligation outstanding amount")
                allocation = {
                    "id": f"ALC-{uuid4().hex.upper()}",
                    "record_type": "allocation",
                    "transaction_id": transaction_id,
                    "obligation_id": obligation_id,
                    "amount": allocation_amount,
                    "currency": transaction_currency,
                    "status": ACTIVE,
                    "request_id": request_id,
                    "internal_sale_owner": transaction.get("internal_sale_owner") or obligation.get("internal_sale_owner"),
                    "shipment_ids": _string_list(list(shipment_ids or [])),
                    "shipment_id": None,
                    "evidence_refs": _references(evidence_refs),
                    "source_refs": _references(source_refs),
                    "provenance": {"mapping_status": CONFIRMED, "review_status": CONFIRMED},
                    "created_at": utc_now(),
                    "created_by": actor_context["username"],
                    "created_by_user_id": actor_context["user_id"],
                    "created_by_role": actor_context["role"],
                    "updated_at": utc_now(),
                    "updated_by": actor_context["username"],
                    "updated_by_user_id": actor_context["user_id"],
                    "updated_by_role": actor_context["role"],
                }
                allocation.update(_shipment_fields(allocation["shipment_ids"]))
                db[ALLOCATIONS].insert_one(allocation, session=session)
                transaction_position_after = derive_transaction_position(transaction, allocations + [allocation])
                obligation_position_after = derive_obligation_position(obligation, allocations + [allocation])
                result = {
                    "record_type": "allocation",
                    "id": allocation["id"],
                    "request_id": request_id,
                    "transaction_id": transaction_id,
                    "obligation_id": obligation_id,
                    "amount": allocation_amount,
                    "currency": transaction_currency,
                    "transaction_unallocated": transaction_position_after["unallocated"],
                    "obligation_outstanding": obligation_position_after["outstanding"],
                }
                db[ACTION_REQUESTS].insert_one(
                    {
                        "request_id": request_id,
                        "action_type": "financial_allocation_create",
                        "fingerprint": fingerprint,
                        "status": "applied",
                        "shipment_id": allocation.get("shipment_id"),
                        "result": result,
                        "created_at": utc_now(),
                        "created_by": actor_context["username"],
                        "created_by_user_id": actor_context["user_id"],
                        "created_by_role": actor_context["role"],
                    },
                    session=session,
                )
                database._audit(db, ALLOCATIONS, allocation["id"], "create", before=None, after=allocation, actor=actor, session=session)
                database._enqueue_domain_event(
                    db,
                    "financial.allocation.created",
                    {"allocation_id": allocation["id"], "transaction_id": transaction_id, "obligation_id": obligation_id, "request_id": request_id},
                    session=session,
                )
                database._set_last_error("")
                return True, result, "financial allocation created"
    except DuplicateKeyError:
        existing = db[ACTION_REQUESTS].find_one({"request_id": request_id})
        if existing:
            return _existing_action(existing, "financial_allocation_create", fingerprint)
        return _error("allocation request conflicted and could not be read back")
    except FinancialLedgerValidationError as exc:
        return _error(str(exc))
    except (PyMongoError, RuntimeError, ValueError) as exc:
        database.LOGGER.exception("financial allocation failed")
        return _error(str(exc))


def reverse_allocation(
    allocation_id: str,
    correction_request_id: str,
    reason: str,
    evidence: Any = None,
    actor: str | None = None,
) -> tuple[bool, dict[str, Any], str]:
    """Reverse an allocation without deleting its original history."""

    if not _require_finance_write():
        return _error("Bạn không có quyền ghi nhận Finance Actual.")
    allocation_id = str(allocation_id or "").strip()
    request_id = str(correction_request_id or "").strip()
    reason = str(reason or "").strip()
    if not allocation_id or not request_id or not reason:
        return _error("allocation reversal requires original id, request identity, and reason")
    fingerprint = database._financial_fingerprint(
        {"allocation_id": allocation_id, "reason": reason, "evidence": deepcopy(evidence)}
    )
    db = database.get_db()
    if db is None:
        return _error("MongoDB is not available")
    client = database._transaction_client(db)
    if client is None:
        return _error("financial ledger requires Mongo transaction support")
    actor_context = database._actor_context(actor)

    def existing_result(existing: Mapping[str, Any]) -> tuple[bool, dict[str, Any], str]:
        if existing.get("fingerprint") != fingerprint:
            return _error("correction request identity is already bound to different content")
        return True, deepcopy(dict(existing.get("result") or {})), "allocation reversal already applied"

    try:
        with client.start_session() as session:
            with session.start_transaction():
                existing = db[CORRECTIONS].find_one({"correction_request_id": request_id}, session=session)
                if existing:
                    return existing_result(existing)
                allocation = db[ALLOCATIONS].find_one({"id": allocation_id}, {"_id": 0}, session=session)
                if not allocation:
                    raise FinancialLedgerValidationError("allocation was not found")
                if not _effective(allocation):
                    raise FinancialLedgerValidationError("allocation is already inactive or reversed")
                correction_id = f"CORR-{uuid4().hex.upper()}"
                original = deepcopy(dict(allocation))
                updated_allocation = deepcopy(dict(allocation))
                updated_allocation.update(
                    {
                        "status": "reversed",
                        "is_reversed": True,
                        "reversed_by": correction_id,
                        "reversed_at": utc_now(),
                        "reversal_reason": reason,
                        "reversed_by_actor": actor_context["username"],
                        "reversed_by_user_id": actor_context["user_id"],
                        "reversed_by_role": actor_context["role"],
                        "updated_at": utc_now(),
                        "updated_by": actor_context["username"],
                        "updated_by_user_id": actor_context["user_id"],
                        "updated_by_role": actor_context["role"],
                    }
                )
                updated = db[ALLOCATIONS].update_one(
                    {"id": allocation_id, "status": {"$nin": list(INACTIVE_STATUSES)}},
                    {"$set": {key: value for key, value in updated_allocation.items() if key != "_id"}},
                    session=session,
                )
                if getattr(updated, "modified_count", 0) != 1:
                    raise RuntimeError("allocation changed before reversal could be applied")
                result = {
                    "correction_id": correction_id,
                    "record_type": "allocation_reversal",
                    "original_allocation_id": allocation_id,
                    "transaction_id": allocation.get("transaction_id"),
                    "obligation_id": allocation.get("obligation_id"),
                    "amount": float(to_decimal(allocation.get("amount"))),
                    "currency": allocation.get("currency"),
                }
                correction = {
                    "correction_request_id": request_id,
                    "correction_id": correction_id,
                    "correction_type": "allocation_reversal",
                    "original_type": "financial_allocation",
                    "original_id": allocation_id,
                    "reason": reason,
                    "evidence": deepcopy(evidence),
                    "actor": actor_context["username"],
                    "actor_user_id": actor_context["user_id"],
                    "actor_role": actor_context["role"],
                    "created_at": utc_now(),
                    "status": "applied",
                    "fingerprint": fingerprint,
                    "result": result,
                }
                db[CORRECTIONS].insert_one(correction, session=session)
                database._audit(db, ALLOCATIONS, allocation_id, "reversed", before=original, after=updated_allocation, actor=actor, session=session)
                database._audit(db, "financial_correction", correction_id, "create", before=None, after=correction, actor=actor, session=session)
                database._enqueue_domain_event(
                    db,
                    "financial.allocation.reversed",
                    {"allocation_id": allocation_id, "correction_id": correction_id, "request_id": request_id},
                    session=session,
                )
                database._set_last_error("")
                return True, result, "financial allocation reversed"
    except DuplicateKeyError:
        existing = db[CORRECTIONS].find_one({"correction_request_id": request_id})
        if existing:
            return existing_result(existing)
        return _error("correction request conflicted and could not be read back")
    except FinancialLedgerValidationError as exc:
        return _error(str(exc))
    except (PyMongoError, RuntimeError, ValueError) as exc:
        database.LOGGER.exception("financial allocation reversal failed")
        return _error(str(exc))


def link_financial_record_to_shipment(
    record_type: str,
    record_id: str,
    shipment_id: str,
    request_id: str,
    actor: str | None = None,
) -> tuple[bool, dict[str, Any], str]:
    """Add shipment context later without creating another financial event."""

    if not _require_finance_write():
        return _error("Bạn không có quyền ghi nhận Finance Actual.")
    record_type = str(record_type or "").strip().lower()
    record_id = str(record_id or "").strip()
    shipment_id = str(shipment_id or "").strip()
    request_id = str(request_id or "").strip()
    collections = {"obligation": OBLIGATIONS, "transaction": TRANSACTIONS, "allocation": ALLOCATIONS}
    if record_type not in collections or not record_id or not shipment_id or not request_id:
        return _error("financial link requires a supported record, shipment, and request identity")
    fingerprint = database._financial_fingerprint(
        {"record_type": record_type, "record_id": record_id, "shipment_id": shipment_id}
    )
    db = database.get_db()
    if db is None:
        return _error("MongoDB is not available")
    client = database._transaction_client(db)
    if client is None:
        return _error("financial ledger requires Mongo transaction support")
    actor_context = database._actor_context(actor)
    action_type = "financial_record_shipment_link"
    collection = collections[record_type]
    try:
        with client.start_session() as session:
            with session.start_transaction():
                existing_action = db[ACTION_REQUESTS].find_one({"request_id": request_id}, session=session)
                if existing_action:
                    return _existing_action(existing_action, action_type, fingerprint)
                old = db[collection].find_one({"id": record_id}, {"_id": 0}, session=session)
                if not old:
                    raise FinancialLedgerValidationError("financial record was not found")
                shipment_ids = _shipment_ids(old)
                if shipment_id not in shipment_ids:
                    shipment_ids.append(shipment_id)
                fields = _shipment_fields(shipment_ids)
                fields.update(
                    {
                        "updated_at": utc_now(),
                        "updated_by": actor_context["username"],
                        "updated_by_user_id": actor_context["user_id"],
                        "updated_by_role": actor_context["role"],
                    }
                )
                updated = db[collection].update_one({"id": record_id}, {"$set": fields}, session=session)
                if getattr(updated, "matched_count", 0) != 1:
                    raise RuntimeError("financial record changed before shipment link")
                result = {
                    "record_type": record_type,
                    "id": record_id,
                    "request_id": request_id,
                    "shipment_ids": shipment_ids,
                    "financial_event_duplicated": False,
                }
                db[ACTION_REQUESTS].insert_one(
                    {
                        "request_id": request_id,
                        "action_type": action_type,
                        "fingerprint": fingerprint,
                        "status": "applied",
                        "shipment_id": shipment_id,
                        "result": result,
                        "created_at": utc_now(),
                        "created_by": actor_context["username"],
                        "created_by_user_id": actor_context["user_id"],
                        "created_by_role": actor_context["role"],
                    },
                    session=session,
                )
                database._audit(db, collection, record_id, "shipment_linked", before=old, after={**old, **fields}, actor=actor, session=session)
                database._enqueue_domain_event(
                    db,
                    "financial.record.shipment_linked",
                    {"record_type": record_type, "record_id": record_id, "shipment_id": shipment_id, "request_id": request_id},
                    session=session,
                )
                database._set_last_error("")
                return True, result, "financial record linked to shipment"
    except DuplicateKeyError:
        existing_action = db[ACTION_REQUESTS].find_one({"request_id": request_id})
        if existing_action:
            return _existing_action(existing_action, action_type, fingerprint)
        return _error("shipment link request conflicted and could not be read back")
    except FinancialLedgerValidationError as exc:
        return _error(str(exc))
    except (PyMongoError, RuntimeError, ValueError) as exc:
        database.LOGGER.exception("financial shipment link failed")
        return _error(str(exc))


def project_partner_financial_position(
    party: Mapping[str, Any] | str,
    obligations: Iterable[Mapping[str, Any]],
    transactions: Iterable[Mapping[str, Any]],
    allocations: Iterable[Mapping[str, Any]],
    *,
    internal_sale_owner: str | None = None,
) -> dict[str, Any]:
    """Build the read-only A Bò/partner projection from canonical history."""

    target = _party(party)
    target_key = party_key(target)
    owner_filter = str(internal_sale_owner or "").strip() or None
    obligation_rows = [dict(item) for item in obligations if isinstance(item, Mapping) and _effective(item)]
    transaction_rows = [dict(item) for item in transactions if isinstance(item, Mapping) and _effective(item)]
    allocation_rows = [dict(item) for item in allocations if isinstance(item, Mapping)]
    buckets: dict[str, list[dict[str, Any]]] = {
        "payable_to_partner": [],
        "held_credit": [],
        "received_on_behalf": [],
        "paid_on_behalf": [],
        "unallocated": [],
        "restricted": [],
        "unknown": [],
    }
    explanations: list[dict[str, Any]] = []
    recent_allocations: list[dict[str, Any]] = []
    owner_coverage = {
        "requested_owner": owner_filter,
        "related_record_count": 0,
        "matching_owner_count": 0,
        "normalized_owner_count": 0,
        "missing_owner_count": 0,
        "known_owners": set(),
    }

    def owner_matches(record: Mapping[str, Any]) -> bool:
        return owner_filter is None or str(record.get("internal_sale_owner") or "").strip() == owner_filter

    def record_owner_coverage(record: Mapping[str, Any]) -> None:
        owner_coverage["related_record_count"] += 1
        owner = str(record.get("internal_sale_owner") or "").strip()
        if owner:
            owner_coverage["normalized_owner_count"] += 1
            owner_coverage["known_owners"].add(owner)
            if owner_filter is None or owner == owner_filter:
                owner_coverage["matching_owner_count"] += 1
        else:
            owner_coverage["missing_owner_count"] += 1

    def trace_fields(record: Mapping[str, Any], position: Mapping[str, Any], *, record_type: str, record_id_key: str) -> dict[str, Any]:
        allocation_history = _allocation_rows(
            allocation_rows,
            transaction_id=record.get("id") if record_type == "transaction" else None,
            obligation_id=record.get("id") if record_type == "obligation" else None,
        )
        return {
            "record_type": record_type,
            "record_id": record.get("id"),
            record_id_key: record.get("id"),
            "created_at": deepcopy(record.get("created_at")),
            "occurred_at": deepcopy(record.get("occurred_at")),
            "due_date": deepcopy(record.get("due_date")),
            "note": deepcopy(record.get("note")),
            "evidence_refs": deepcopy(record.get("evidence_refs") or []),
            "source_refs": deepcopy(record.get("source_refs") or []),
            "provenance": deepcopy(record.get("provenance") or {}),
            "allocation_history": allocation_history,
            "allocation_ids": list(position.get("allocation_ids") or []),
        }

    for obligation in obligation_rows:
        if party_key(obligation.get("to_party")) != target_key:
            continue
        record_owner_coverage(obligation)
        if not owner_matches(obligation):
            continue
        position = derive_obligation_position(obligation, allocation_rows)
        if position["status"] != CONFIRMED:
            row = {
                "bucket": "unknown",
                "obligation_id": obligation.get("id"),
                "shipment_ids": deepcopy(obligation.get("shipment_ids") or []),
                "from_party": deepcopy(obligation.get("from_party")),
                "to_party": deepcopy(obligation.get("to_party")),
                "purpose": obligation.get("purpose"),
                "amount": position["amount"],
                "allocated": position["allocated"],
                "outstanding": position["outstanding"],
                "currency": position["currency"],
                "internal_sale_owner": obligation.get("internal_sale_owner"),
                "formula": position["formula"],
                "source_record_ids": [obligation.get("id"), *position["allocation_ids"]],
                "review_reason": "obligation has incompatible or over-allocated allocation history",
            }
            row.update(trace_fields(obligation, position, record_type="obligation", record_id_key="obligation_id"))
            buckets["unknown"].append(row)
            explanations.append(
                {
                    "bucket": "unknown",
                    "label": "Nghĩa vụ có chênh lệch cần rà soát",
                    "currency": position["currency"],
                    "value": position["outstanding"],
                    "formula": position["formula"],
                    "source_record_ids": row["source_record_ids"],
                    "excluded_from_confirmed": True,
                }
            )
            continue
        if position["outstanding"] <= 0:
            continue
        row = {
            "bucket": "payable_to_partner",
            "obligation_id": obligation.get("id"),
            "shipment_ids": deepcopy(obligation.get("shipment_ids") or []),
            "from_party": deepcopy(obligation.get("from_party")),
            "to_party": deepcopy(obligation.get("to_party")),
            "purpose": obligation.get("purpose"),
            "amount": position["amount"],
            "allocated": position["allocated"],
            "outstanding": position["outstanding"],
            "currency": position["currency"],
            "internal_sale_owner": obligation.get("internal_sale_owner"),
            "formula": position["formula"],
            "source_record_ids": [obligation.get("id"), *position["allocation_ids"]],
        }
        row.update(trace_fields(obligation, position, record_type="obligation", record_id_key="obligation_id"))
        buckets["payable_to_partner"].append(row)
        explanations.append(
            {
                "bucket": "payable_to_partner",
                "label": "TT phải trả A Bò",
                "currency": position["currency"],
                "value": position["outstanding"],
                "formula": position["formula"],
                "source_record_ids": row["source_record_ids"],
            }
        )

    for transaction in transaction_rows:
        holder_key = party_key(transaction.get("holder_party"))
        beneficial_key = party_key(transaction.get("beneficial_owner"))
        source_key = party_key(transaction.get("source_party"))
        relates_to_target = holder_key == target_key or beneficial_key == target_key or source_key == target_key
        if not relates_to_target:
            continue
        record_owner_coverage(transaction)
        if not owner_matches(transaction):
            continue
        position = derive_transaction_position(transaction, allocation_rows)
        transaction_kind = str(transaction.get("transaction_kind") or "").strip().lower().replace("-", "_")
        is_received_on_behalf = transaction_kind in RECEIVED_ON_BEHALF_KINDS
        is_paid_on_behalf = transaction_kind in PAID_ON_BEHALF_KINDS or (
            source_key == target_key and holder_key != target_key
        )
        row = {
            "transaction_id": transaction.get("id"),
            "transaction_kind": transaction.get("transaction_kind"),
            "source_party": deepcopy(transaction.get("source_party")),
            "holder_party": deepcopy(transaction.get("holder_party")),
            "beneficial_owner": deepcopy(transaction.get("beneficial_owner")),
            "beneficiary_party": deepcopy(transaction.get("beneficiary_party")),
            "shipment_ids": deepcopy(transaction.get("shipment_ids") or []),
            "amount": position["amount"],
            "allocated": position["allocated"],
            "unallocated": position["unallocated"],
            "currency": position["currency"],
            "classification_status": transaction.get("classification_status"),
            "restriction_status": (transaction.get("restriction") or {}).get("status"),
            "internal_sale_owner": transaction.get("internal_sale_owner"),
            "formula": position["formula"],
            "source_record_ids": [transaction.get("id"), *position["allocation_ids"]],
        }
        row.update(trace_fields(transaction, position, record_type="transaction", record_id_key="transaction_id"))
        classification = str(transaction.get("classification_status") or REVIEW_REQUIRED).upper()
        restriction_status = str((transaction.get("restriction") or {}).get("status") or REVIEW_REQUIRED).upper()
        if classification != CONFIRMED:
            buckets["unknown"].append({**row, "review_reason": "classification is UNKNOWN/REVIEW_REQUIRED"})
            explanations.append(
                {
                    "bucket": "unknown",
                    "label": "Khoản chưa xác minh",
                    "currency": position["currency"],
                    "value": position["unallocated"],
                    "formula": position["formula"],
                    "source_record_ids": row["source_record_ids"],
                    "excluded_from_confirmed": True,
                }
            )
            continue
        if restriction_status != NONE_RESTRICTION:
            buckets["restricted"].append({**row, "review_reason": "restriction is not NONE"})
            explanations.append(
                {
                    "bucket": "restricted",
                    "label": "Tiền bị giới hạn mục đích",
                    "currency": position["currency"],
                    "value": position["unallocated"],
                    "formula": position["formula"],
                    "source_record_ids": row["source_record_ids"],
                    "excluded_from_confirmed": True,
                }
            )
            continue
        if position["status"] != CONFIRMED:
            buckets["unknown"].append({**row, "review_reason": "incompatible allocation currency"})
            continue

        if is_received_on_behalf:
            buckets["received_on_behalf"].append(
                {
                    **row,
                    "bucket": "received_on_behalf",
                    "received_amount": position["amount"],
                    "remaining_unallocated": position["unallocated"],
                    "allocation_status": "Đã cấn" if position["unallocated"] <= 0 else "Chưa cấn",
                }
            )
        if is_paid_on_behalf:
            buckets["paid_on_behalf"].append(
                {
                    **row,
                    "bucket": "paid_on_behalf",
                    "spent_amount": position["amount"],
                    "spent_allocated": position["allocated"],
                    "spent_remaining_unallocated": position["unallocated"],
                }
            )
        if position["unallocated"] <= 0:
            continue
        buckets["unallocated"].append({**row, "bucket": "unallocated"})
        if holder_key == target_key:
            buckets["held_credit"].append({**row, "bucket": "held_credit"})
        explanations.append(
            {
                "bucket": "unallocated",
                "label": "Tiền/credit chưa phân bổ",
                "currency": position["currency"],
                "value": position["unallocated"],
                "formula": position["formula"],
                "source_record_ids": row["source_record_ids"],
            }
        )

    for allocation in allocation_rows:
        if _effective(allocation) and owner_matches(allocation):
            recent_allocations.append(
                {
                    "allocation_id": allocation.get("id"),
                    "transaction_id": allocation.get("transaction_id"),
                    "obligation_id": allocation.get("obligation_id"),
                    "amount": float(to_decimal(allocation.get("amount"))),
                    "currency": allocation.get("currency"),
                    "shipment_ids": deepcopy(allocation.get("shipment_ids") or []),
                    "created_at": allocation.get("created_at"),
                }
            )
    recent_allocations.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)

    totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {
            "payable_to_partner": 0.0,
            "held_credit": 0.0,
            "received_on_behalf": 0.0,
            "received_on_behalf_allocated": 0.0,
            "received_on_behalf_remaining": 0.0,
            "paid_on_behalf": 0.0,
            "unallocated": 0.0,
            "net_after_valid_allocations": 0.0,
        }
    )
    for row in buckets["payable_to_partner"]:
        totals[row["currency"]]["payable_to_partner"] += float(row["outstanding"])
    for row in buckets["held_credit"]:
        totals[row["currency"]]["held_credit"] += float(row["unallocated"])
    for row in buckets["received_on_behalf"]:
        totals[row["currency"]]["received_on_behalf"] += float(row.get("received_amount", row.get("amount", 0)))
        totals[row["currency"]]["received_on_behalf_allocated"] += float(row.get("allocated", 0))
        totals[row["currency"]]["received_on_behalf_remaining"] += float(
            row.get("remaining_unallocated", row.get("unallocated", 0))
        )
    for row in buckets["paid_on_behalf"]:
        totals[row["currency"]]["paid_on_behalf"] += float(row.get("spent_amount", row.get("amount", 0)))
    for row in buckets["unallocated"]:
        totals[row["currency"]]["unallocated"] += float(row["unallocated"])
    for currency, values in totals.items():
        values["net_after_valid_allocations"] = values["payable_to_partner"] - values["held_credit"]

    unknown_count = len(buckets["unknown"])
    restricted_count = len(buckets["restricted"])
    owner_coverage["known_owners"] = sorted(owner_coverage["known_owners"])
    return {
        "party": target,
        "party_key": target_key,
        "internal_sale_owner": owner_filter,
        "buckets": buckets,
        "totals_by_currency": dict(totals),
        "net_position_by_currency": {
            currency: values["net_after_valid_allocations"] for currency, values in totals.items()
        },
        "recent_allocations": recent_allocations[:20],
        "explanations": explanations,
        "owner_coverage": owner_coverage,
        "unknown_count": unknown_count,
        "restricted_count": restricted_count,
        "status": REVIEW_REQUIRED if unknown_count or restricted_count else CONFIRMED,
        "derived": True,
        "read_only": True,
    }


def shipment_partner_position(
    shipment_id: str,
    *,
    db: Any = None,
) -> dict[str, Any]:
    """Derive the payable/paid/remaining truth for ONE shipment's partner debt.

    Read-only projection over the canonical collections, filtered by shipment
    linkage on the records themselves.  UNKNOWN != ZERO: when no obligation or
    payment record exists for the shipment, every money figure stays ``None``
    — absence of a record is never reported as 0.  With an obligation present,
    its allocation history is complete information, so derived values (including
    a true 0) are reported per currency and never combined across currencies.
    """

    sid = str(shipment_id or "").strip()
    empty: dict[str, Any] = {
        "shipment_id": sid,
        "partners": [],
        "partner": None,
        "partner_key": None,
        "currency": None,
        "payable": None,
        "paid": None,
        "remaining": None,
        "totals_by_currency": {},
        "obligations": [],
        "payments": [],
        "status": UNKNOWN if sid else REVIEW_REQUIRED,
        "derived": True,
        "read_only": True,
    }
    if not sid:
        empty["error"] = "shipment id is required"
        return empty
    db = db if db is not None else database.get_db()
    if db is None:
        return {**empty, "status": UNKNOWN, "error": "MongoDB is not available"}
    try:
        obligations = [
            dict(item)
            for item in _all(db, OBLIGATIONS)
            if isinstance(item, Mapping) and _effective(item) and sid in _shipment_ids(item)
        ]
        transactions = [
            dict(item)
            for item in _all(db, TRANSACTIONS)
            if isinstance(item, Mapping) and _effective(item) and sid in _shipment_ids(item)
        ]
        allocations = _all(db, ALLOCATIONS)
        if not obligations and not transactions:
            return empty

        obligation_rows: list[dict[str, Any]] = []
        groups: dict[str, dict[str, Any]] = {}
        for obligation in obligations:
            position = derive_obligation_position(obligation, allocations)
            partner = deepcopy(obligation.get("to_party"))
            partner_key = str(obligation.get("to_party_key") or party_key(partner))
            group = groups.setdefault(
                partner_key,
                {"partner": partner, "partner_key": partner_key, "obligations": [], "payments": []},
            )
            row = {
                "obligation_id": obligation.get("id"),
                "purpose": obligation.get("purpose"),
                "note": deepcopy(obligation.get("note")),
                "due_date": deepcopy(obligation.get("due_date")),
                "created_at": deepcopy(obligation.get("created_at")),
                "shipment_ids": deepcopy(obligation.get("shipment_ids") or []),
                "from_party": deepcopy(obligation.get("from_party")),
                "to_party": deepcopy(obligation.get("to_party")),
                "evidence_refs": deepcopy(obligation.get("evidence_refs") or []),
                "source_record_ids": [obligation.get("id"), *position["allocation_ids"]],
                **position,
            }
            group["obligations"].append(row)
            obligation_rows.append({**row, "_partner_key": partner_key})

        payment_rows: list[dict[str, Any]] = []
        for transaction in transactions:
            position = derive_transaction_position(transaction, allocations)
            payment_rows.append(
                {
                    "transaction_id": transaction.get("id"),
                    "request_id": transaction.get("request_id"),
                    "transaction_kind": transaction.get("transaction_kind"),
                    "occurred_at": deepcopy(transaction.get("occurred_at")),
                    "note": deepcopy(transaction.get("note")),
                    "source_party": deepcopy(transaction.get("source_party")),
                    "holder_party": deepcopy(transaction.get("holder_party")),
                    "holder_party_key": transaction.get("holder_party_key"),
                    "source_record_ids": [transaction.get("id"), *position["allocation_ids"]],
                    **position,
                }
            )

        result_partners: list[dict[str, Any]] = []
        for partner_key, group in groups.items():
            group_payments = [
                row
                for row in payment_rows
                if row["holder_party_key"] == partner_key
                or any(
                    allocation.get("obligation_id") == obligation["obligation_id"]
                    for allocation in allocations
                    if _effective(allocation) and allocation.get("transaction_id") == row["transaction_id"]
                )
            ]
            confirmed_currencies = {
                row["currency"] for row in group["obligations"] if row["status"] == CONFIRMED
            }
            mixed = len(confirmed_currencies) > 1
            totals: dict[str, dict[str, float]] = {
                currency: {"payable": 0.0, "paid": 0.0, "remaining": 0.0}
                for currency in confirmed_currencies
            }
            for row in group["obligations"]:
                if row["status"] != CONFIRMED:
                    continue
                bucket = totals.setdefault(row["currency"], {"payable": 0.0, "paid": 0.0, "remaining": 0.0})
                bucket["payable"] += float(row["amount"])
                bucket["paid"] += float(row["allocated"])
                bucket["remaining"] += float(row["outstanding"])
            group_status = (
                REVIEW_REQUIRED
                if mixed or any(row["status"] != CONFIRMED for row in group["obligations"])
                else CONFIRMED
            )
            result_partners.append(
                {
                    "partner": group["partner"],
                    "partner_key": partner_key,
                    "status": group_status,
                    "totals_by_currency": totals,
                    "obligations": group["obligations"],
                    "payments": group_payments,
                }
            )

        result_partners.sort(key=lambda item: str(item["partner_key"]))
        result = {
            **empty,
            "partners": result_partners,
            "payments": payment_rows,
            "obligations": obligation_rows,
        }
        if len(result_partners) == 1:
            group = result_partners[0]
            result["partner"] = group["partner"]
            result["partner_key"] = group["partner_key"]
            result["status"] = group["status"]
            result["totals_by_currency"] = group["totals_by_currency"]
            if group["status"] == CONFIRMED and len(group["totals_by_currency"]) == 1:
                currency = next(iter(group["totals_by_currency"]))
                values = group["totals_by_currency"][currency]
                result["currency"] = currency
                result["payable"] = values["payable"]
                result["paid"] = values["paid"]
                result["remaining"] = values["remaining"]
        elif len(result_partners) > 1:
            result["status"] = REVIEW_REQUIRED
        return result
    except (PyMongoError, FinancialLedgerValidationError, TypeError, ValueError) as exc:
        database._set_last_error(str(exc))
        return {**empty, "status": UNKNOWN, "error": str(exc)}


def build_partner_financial_position(
    party: Mapping[str, Any] | str,
    *,
    internal_sale_owner: str | None = None,
    db: Any = None,
) -> dict[str, Any]:
    """Read canonical records and return the derived partner position."""

    db = db if db is not None else database.get_db()
    if db is None:
        return {
            "party": deepcopy(dict(party)) if isinstance(party, Mapping) else {"name": str(party)},
            "buckets": {},
            "totals_by_currency": {},
            "net_position_by_currency": {},
            "explanations": [],
            "status": UNKNOWN,
            "derived": True,
            "read_only": True,
            "error": "MongoDB is not available",
        }
    try:
        return project_partner_financial_position(
            party,
            _all(db, OBLIGATIONS),
            _all(db, TRANSACTIONS),
            _all(db, ALLOCATIONS),
            internal_sale_owner=internal_sale_owner,
        )
    except (PyMongoError, FinancialLedgerValidationError, TypeError, ValueError) as exc:
        database._set_last_error(str(exc))
        return {
            "party": deepcopy(dict(party)) if isinstance(party, Mapping) else {"name": str(party)},
            "buckets": {},
            "totals_by_currency": {},
            "net_position_by_currency": {},
            "explanations": [],
            "status": UNKNOWN,
            "derived": True,
            "read_only": True,
            "error": str(exc),
        }


__all__ = [
    "ALLOCATIONS",
    "CORRECTIONS",
    "OBLIGATIONS",
    "TRANSACTIONS",
    "CONFIRMED",
    "NONE_RESTRICTION",
    "PAID_ON_BEHALF_KINDS",
    "RECEIVED_ON_BEHALF_KINDS",
    "RESTRICTED",
    "REVIEW_REQUIRED",
    "UNKNOWN",
    "allocate_transaction",
    "build_partner_financial_position",
    "derive_obligation_position",
    "derive_transaction_position",
    "link_financial_record_to_shipment",
    "party_key",
    "project_partner_financial_position",
    "reverse_allocation",
    "save_obligation",
    "save_transaction",
    "shipment_partner_position",
]
