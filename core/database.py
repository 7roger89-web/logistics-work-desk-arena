"""MongoDB repository layer cho LOGISTICS PRO.

Giữ API tương thích với mã cũ nhưng bổ sung:
- secrets/env thay vì hard-code URI;
- unique indexes;
- validation + financial snapshot trước khi lưu;
- optimistic locking qua trường version;
- audit log, soft delete, soft archive;
- kho dữ liệu MongoDB cho Knowledge Base, CBPG và Entrustment.
"""
from __future__ import annotations

import copy
import hashlib
import json
import logging
import re
from functools import lru_cache
from datetime import datetime
from typing import Any, Iterable, Mapping
from uuid import uuid4

import pymongo
try:
    import streamlit as st
except ImportError:
    st = None  # type: ignore[assignment]
from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError

from core.config import GETFLY_SERVICES_LIST, MONGO_DB_NAME, MONGO_URI, is_streamlit_runtime
from core.logic import apply_financial_snapshot, calculate_from_shipment
from core.utils import safe_float, to_decimal, utc_now
from core.validators import validate_shipment

LOGGER = logging.getLogger("logistics_pro.database")
_LAST_DB_ERROR = ""
_INACTIVE_PAYMENT_STATUSES = frozenset({"reversed", "cancelled", "void"})


class DatabaseUnavailableError(RuntimeError):
    pass


class ConcurrentUpdateError(RuntimeError):
    pass


def _sanitize_error(message: str) -> str:
    return re.sub(r"(mongodb(?:\+srv)?://)[^@\s]+@", r"\1***:***@", str(message))


def _set_last_error(message: str) -> None:
    global _LAST_DB_ERROR
    _LAST_DB_ERROR = _sanitize_error(message)
    if st is not None and is_streamlit_runtime():
        try:
            st.session_state.last_db_error = _LAST_DB_ERROR
        except Exception:
            pass


def get_last_db_error() -> str:
    return _LAST_DB_ERROR


def _actor_context(actor: str | None = None) -> dict[str, str]:
    from core.auth import current_actor_context

    return current_actor_context(actor)


def _actor() -> str:
    return _actor_context()["username"]


def _require_business_permission(permission: str, message: str) -> bool:
    from core.auth import can_operate_business

    if can_operate_business(permission):
        return True
    _set_last_error(message)
    return False


def _transaction_client(db):
    """Return a session-capable client or fail closed for money writes."""
    client = getattr(db, "client", None)
    if client is None or not callable(getattr(client, "start_session", None)):
        _set_last_error("MongoDB không cung cấp transaction cho financial write.")
        return None
    return client


def _financial_fingerprint(payload: Any) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _direct_payment_fingerprint(shipment_id: str, payment: Mapping[str, Any]) -> str:
    stable_payload = copy.deepcopy(dict(payment))
    for key in ("id", "request_id", "created_at", "created_by", "status", "is_reversed"):
        stable_payload.pop(key, None)
    return _financial_fingerprint({"shipment_id": shipment_id, "payment": stable_payload})


def _entrustment_batch_fingerprint(documents: Mapping[str, Mapping[str, Any]]) -> str:
    stable_documents: dict[str, dict[str, Any]] = {}
    for code, document in documents.items():
        payload = copy.deepcopy(dict(document))
        payload.pop("updated_at", None)
        stable_documents[str(code)] = payload
    return _financial_fingerprint({"documents": stable_documents})


def _payment_result(shipment_id: str, payment: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "shipment_id": shipment_id,
        "payment_id": str(payment.get("id") or ""),
        "request_id": str(payment.get("request_id") or ""),
        "amount": float(to_decimal(payment.get("amount"))),
        "date": payment.get("date"),
    }


def _payment_history_is_unchanged(old: Mapping[str, Any] | None, new: Mapping[str, Any]) -> tuple[bool, str]:
    old_rows = old.get("data", {}).get("3.4", {}).get("payments", []) if old else []
    new_rows = new.get("data", {}).get("3.4", {}).get("payments", [])
    old_rows = [row for row in old_rows if isinstance(row, Mapping)]
    new_rows = [row for row in new_rows if isinstance(row, Mapping)]

    if old is None:
        if any(not str(row.get("request_id") or "").strip() for row in new_rows):
            return False, "Khoản thu mới phải có request identity.",
        return True, ""

    if len(old_rows) != len(new_rows):
        return False, "Lịch sử thanh toán không được thêm/xoá trực tiếp.",

    old_ids = [str(row.get("id") or "") for row in old_rows]
    new_ids = [str(row.get("id") or "") for row in new_rows]
    if any(not value for value in old_ids + new_ids):
        if _financial_fingerprint(old_rows) != _financial_fingerprint(new_rows):
            return False, "Lịch sử thanh toán cũ không được ghi đè.",
        return True, ""

    old_by_id = {row_id: row for row_id, row in zip(old_ids, old_rows)}
    new_by_id = {row_id: row for row_id, row in zip(new_ids, new_rows)}
    if set(old_by_id) != set(new_by_id):
        return False, "Lịch sử thanh toán không được đổi ID hoặc xoá.",
    for payment_id, old_row in old_by_id.items():
        if _financial_fingerprint(old_row) != _financial_fingerprint(new_by_id[payment_id]):
            return False, f"Thanh toán {payment_id} phải được correction/reversal có audit.",
    return True, ""


def init_connection() -> pymongo.MongoClient | None:
    """Get MongoDB connection. Uses st.cache_resource when in Streamlit runtime."""
    if st is not None and is_streamlit_runtime():
        return _get_cached_connection()
    return _init_connection_impl()


def _get_cached_connection() -> pymongo.MongoClient | None:
    """Cached wrapper to avoid repeated re-connection overhead."""
    try:
        return st.cache_resource(_init_connection_impl, ttl=3600, show_spinner=False)()
    except Exception:
        return _init_connection_impl()


@lru_cache(maxsize=1)
def _init_connection_impl() -> pymongo.MongoClient | None:
    if not MONGO_URI:
        _set_last_error(
            "Chưa cấu hình MongoDB. Thêm [mongo].uri hoặc MONGO_URI vào "
            ".streamlit/secrets.toml, hoặc đặt biến môi trường MONGO_URI."
        )
        return None
    try:
        client = pymongo.MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
            waitQueueTimeoutMS=10000,
            retryWrites=True,
            tz_aware=True,
        )
        client.admin.command("ping")
        return client
    except Exception as exc:
        LOGGER.exception("MongoDB connection failed")
        _set_last_error(f"Không thể kết nối MongoDB: {type(exc).__name__}: {exc}")
        return None


def get_db():
    client = init_connection()
    if client is None:
        return None
    # LOG-REL-01: Mandatory identity validation in ALL modes for environment isolation
    from core.config import validate_mongo_identity
    validate_mongo_identity()
    return client[MONGO_DB_NAME]


def ensure_indexes() -> bool:
    db = get_db()
    if db is None:
        return False
    specs = [
        (db.shipments, "id", {"unique": True, "name": "uq_shipment_id", "partialFilterExpression": {"id": {"$type": "string"}}}),
        (db.shipments, [("is_deleted", 1), ("is_archived", 1), ("status", 1), ("updated_at", -1)], {"name": "ix_shipment_worklist"}),
        (db.shipments, [("customer_id", 1), ("updated_at", -1)], {"name": "ix_shipment_customer"}),
        (db.shipments, [("contract_id", 1), ("updated_at", -1)], {"name": "ix_shipment_contract"}),
        (db.customers, "id", {"unique": True, "name": "uq_customer_id", "partialFilterExpression": {"id": {"$type": "string"}}}),
        (db.contracts, "id", {"unique": True, "name": "uq_contract_id", "partialFilterExpression": {"id": {"$type": "string"}}}),
        (db.contracts, "normalized_no", {"unique": True, "name": "uq_contract_normalized_no", "partialFilterExpression": {"normalized_no": {"$type": "string"}}}),
        (db.contract_transactions, [("contract_id", 1), ("transaction_type", 1), ("date", -1)], {"name": "ix_contract_transaction"}),
        (db.proxy_payments, "id", {"unique": True, "name": "uq_proxy_payment_id", "partialFilterExpression": {"id": {"$type": "string"}}}),
        (db.rate_cards, "id", {"unique": True, "name": "uq_rate_card_id", "partialFilterExpression": {"id": {"$type": "string"}}}),
        (db.entrustments, "id", {"unique": True, "name": "uq_entrustment_id", "partialFilterExpression": {"id": {"$type": "string"}}}),
        (db.knowledge_base, "id", {"unique": True, "name": "uq_kb_id", "partialFilterExpression": {"id": {"$type": "string"}}}),
        (db.audit_logs, [("entity_type", 1), ("entity_id", 1), ("created_at", -1)], {"name": "ix_audit_entity"}),
        (db.notification_outbox, [("status", 1), ("next_retry_at", 1)], {"name": "ix_notification_queue"}),
        (db.notification_outbox, "event_id", {"unique": True, "name": "uq_notification_event", "partialFilterExpression": {"event_id": {"$type": "string"}}}),
        (db.payment_receipts, "idempotency_key", {"unique": True, "name": "uq_payment_receipt_idempotency", "partialFilterExpression": {"idempotency_key": {"$type": "string"}}}),
        (db.financial_action_requests, "request_id", {"unique": True, "name": "uq_financial_action_request", "partialFilterExpression": {"request_id": {"$type": "string"}}}),
        (db.financial_corrections, "correction_request_id", {"unique": True, "name": "uq_financial_correction_request", "partialFilterExpression": {"correction_request_id": {"$type": "string"}}}),
        (db.financial_corrections, [("original_type", 1), ("original_id", 1)], {"name": "ix_financial_correction_original"}),
        (db.financial_obligations, "id", {"unique": True, "name": "uq_financial_obligation_id", "partialFilterExpression": {"id": {"$type": "string"}}}),
        (db.financial_obligations, [("from_party_key", 1), ("to_party_key", 1), ("status", 1)], {"name": "ix_financial_obligation_parties"}),
        (db.financial_obligations, [("shipment_ids", 1), ("internal_sale_owner", 1)], {"name": "ix_financial_obligation_scope"}),
        (db.financial_transactions, "id", {"unique": True, "name": "uq_financial_transaction_id", "partialFilterExpression": {"id": {"$type": "string"}}}),
        (db.financial_transactions, [("holder_party_key", 1), ("beneficial_owner_key", 1), ("status", 1)], {"name": "ix_financial_transaction_ownership"}),
        (db.financial_transactions, [("shipment_ids", 1), ("internal_sale_owner", 1)], {"name": "ix_financial_transaction_scope"}),
        (db.financial_allocations, "id", {"unique": True, "name": "uq_financial_allocation_id", "partialFilterExpression": {"id": {"$type": "string"}}}),
        (db.financial_allocations, [("transaction_id", 1), ("status", 1)], {"name": "ix_financial_allocation_transaction"}),
        (db.financial_allocations, [("obligation_id", 1), ("status", 1)], {"name": "ix_financial_allocation_obligation"}),
    ]
    all_ok = True
    errors: list[str] = []
    for collection, keys, kwargs in specs:
        try:
            collection.create_index(keys, **kwargs)
        except PyMongoError as exc:
            all_ok = False
            errors.append(f"{kwargs.get('name')}: {exc}")
            LOGGER.warning("Cannot create index %s: %s", kwargs.get("name"), exc)
    if errors:
        _set_last_error("; ".join(errors))
    return all_ok

def smart_money_parse(value: Any) -> float:
    return safe_float(value)


def normalize_contract_no(value: Any) -> str:
    return re.sub(r"[\s-]+", "", str(value or "").upper()).strip()


def find_best_match_code(input_name: Any) -> str:
    if not input_name:
        return "DVK"
    clean_input = str(input_name).lower().strip()
    for service in GETFLY_SERVICES_LIST:
        if service["name"].lower().strip() == clean_input:
            return service["code"]
    for service in GETFLY_SERVICES_LIST:
        service_name = service["name"].lower().strip()
        if clean_input in service_name or service_name in clean_input:
            return service["code"]
    return "DVK"


def repair_data(db_data: dict[str, dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    if not db_data:
        return {}
    repaired = copy.deepcopy(db_data)
    for key, item in repaired.items():
        if not isinstance(item, dict):
            continue
        item.setdefault("id", key)
        item.setdefault("shipment_id", item["id"])
        item.setdefault("customer", item.get("client", ""))
        item.setdefault("client", item.get("customer", ""))
        item.setdefault("status", item.get("data", {}).get("0.0", {}).get("st", "wait"))
        item.setdefault("version", 0)
        item.setdefault("is_deleted", False)
        item.setdefault("is_archived", False)

        if not isinstance(item.get("data"), dict):
            item["data"] = {}
        data = item["data"]
        for section in ("0.0", "1.2", "2.4", "2.6", "2.7", "3.4", "entrustment"):
            if not isinstance(data.get(section), dict):
                data[section] = {}
        data["0.0"].setdefault("st", item["status"])
        data["0.0"].setdefault("mode", "Sea")
        data["0.0"].setdefault("incoterm", "EXW")

        finance = data["3.4"]
        finance.setdefault("details", [])
        finance.setdefault("payments", [])
        commission = finance.setdefault("commission", {})
        if isinstance(commission, list):
            commission = {"list": commission, "total": 0}
            finance["commission"] = commission
        commission.setdefault("list", [])
        commission.setdefault("total", 0)

        details = finance.get("details")
        if not isinstance(details, list):
            details = []
            finance["details"] = details
        if not details:
            for index in range(1, 21):
                raw_name = finance.get(f"DV_{index}") or item.get(f"DV_{index}")
                if not raw_name or not str(raw_name).strip():
                    continue
                price = smart_money_parse(finance.get(f"Thu_{index}") or item.get(f"Thu_{index}"))
                cost = smart_money_parse(finance.get(f"Chi_{index}") or item.get(f"Chi_{index}"))
                details.append({
                    "id": str(uuid4()),
                    "name_full": str(raw_name).strip(),
                    "display_name": str(raw_name).strip(),
                    "code": find_best_match_code(raw_name),
                    "qty": 1.0,
                    "price": price,
                    "cost": cost,
                    "vat_line": 0.0,
                    "note": str(finance.get(f"Note_{index}") or item.get(f"Note_{index}") or ""),
                })

        for line in details:
            line.setdefault("id", str(uuid4()))
            line["qty"] = smart_money_parse(line.get("qty", 1)) or 1.0
            line["price"] = smart_money_parse(line.get("price", line.get("price_out", 0)))
            line["cost"] = smart_money_parse(line.get("cost", line.get("price_in", 0)))
            line["vat_line"] = smart_money_parse(line.get("vat_line", line.get("vat", 0)))
            line["price_out"] = line["price"]
            line["price_in"] = line["cost"]
            line["vat"] = line["vat_line"]
            current_name = str(line.get("name_full", line.get("name", ""))).strip()
            line.setdefault("name_full", current_name)
            line.setdefault("display_name", current_name)
            if not str(line.get("code", "")).strip() or line.get("code") in {"DV", "DV-KHAC", "None"}:
                line["code"] = find_best_match_code(current_name)

        for payment in finance["payments"]:
            payment.setdefault("id", str(uuid4()))
        apply_financial_snapshot(item)
    return repaired


def load_data(limit: int = 2000, include_archived: bool = False, include_deleted: bool = False) -> dict[str, dict[str, Any]]:
    """Load shipment data. Cached in Streamlit runtime for performance."""
    if st is not None and is_streamlit_runtime():
        return st.cache_data(
            _load_data_impl, ttl=30, show_spinner=False,
        )(limit, include_archived, include_deleted)
    return _load_data_impl(limit, include_archived, include_deleted)


def _load_data_impl(limit: int = 2000, include_archived: bool = False, include_deleted: bool = False) -> dict[str, dict[str, Any]]:
    db = get_db()
    if db is None:
        return {}
    query: dict[str, Any] = {}
    if not include_deleted:
        query["is_deleted"] = {"$ne": True}
    if not include_archived:
        query["is_archived"] = {"$ne": True}
    try:
        cursor = db.shipments.find(query, {"_id": 0}).sort([("updated_at", -1), ("created_at", -1)]).limit(int(limit))
        return repair_data({doc["id"]: doc for doc in cursor if doc.get("id")})
    except PyMongoError as exc:
        LOGGER.exception("load_data failed")
        _set_last_error(str(exc))
        return {}


def load_archived_data(limit: int = 5000) -> dict[str, dict[str, Any]]:
    db = get_db()
    if db is None:
        return {}
    try:
        cursor = db.shipments.find({"is_archived": True, "is_deleted": {"$ne": True}}, {"_id": 0}).sort("archived_at", -1).limit(limit)
        return repair_data({doc["id"]: doc for doc in cursor if doc.get("id")})
    except PyMongoError as exc:
        _set_last_error(str(exc))
        return {}


def _audit(db, entity_type: str, entity_id: str, action: str, before: Any = None, after: Any = None, actor: str | None = None, session=None) -> None:
    # LOG-LG08.1: Prevent password_hash leakage into audit logs
    from core.users import redact_password_material

    actor_context = _actor_context(actor)
    safe_before = redact_password_material(before) if isinstance(before, Mapping) else before
    safe_after = redact_password_material(after) if isinstance(after, Mapping) else after

    db.audit_logs.insert_one({
        "event_id": str(uuid4()),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "actor": actor_context["username"],
        "actor_user_id": actor_context["user_id"],
        "actor_username": actor_context["username"],
        "actor_role": actor_context["role"],
        "before": safe_before,
        "after": safe_after,
        "created_at": utc_now(),
    }, session=session)


def _enqueue_domain_event(db, event_type: str, payload: Mapping[str, Any], session=None) -> None:
    db.notification_outbox.insert_one({
        "event_id": str(uuid4()),
        "event_type": event_type,
        "payload": dict(payload),
        "status": "pending",
        "attempts": 0,
        "created_at": utc_now(),
        "next_retry_at": utc_now(),
    }, session=session)


def save_shipment_atomic(ship_obj: dict[str, Any], expected_version: int | None = None, actor: str | None = None) -> bool:
    from core.auth import can_operate_business

    if not (can_operate_business("shipment_edit") or can_operate_business("shipment_create")):
        _set_last_error("Bạn không có quyền ghi dữ liệu lô hàng.")
        return False
    db = get_db()
    if db is None:
        _set_last_error("MongoDB chưa sẵn sàng.")
        return False

    shipment = repair_data({str(ship_obj.get("id") or ship_obj.get("shipment_id") or ""): ship_obj})
    shipment = next(iter(shipment.values()), {})
    sid = str(shipment.get("id", "")).strip()
    validation = validate_shipment(shipment)
    if not validation.is_valid:
        _set_last_error(validation.message)
        return False

    try:
        existing = db.shipments.find_one({"id": sid}, {"_id": 0})
    except PyMongoError as exc:
        _set_last_error(str(exc))
        return False
    required_permission = "shipment_edit" if existing is not None else "shipment_create"
    if not _require_business_permission(required_permission, "Bạn không có quyền ghi dữ liệu lô hàng."):
        return False
    actor_context = _actor_context(actor)
    effective_actor = actor_context["username"]

    shipment.pop("_id", None)
    shipment.pop("version", None)
    shipment["shipment_id"] = sid
    shipment["status"] = shipment.get("status") or shipment["data"]["0.0"].get("st", "wait")
    shipment["data"]["0.0"]["st"] = shipment["status"]
    shipment["updated_at"] = utc_now()
    shipment["updated_by"] = effective_actor
    shipment["updated_by_user_id"] = actor_context["user_id"]
    shipment["updated_by_role"] = actor_context["role"]
    shipment.setdefault("is_deleted", False)
    shipment.setdefault("is_archived", False)

    client = getattr(db, "client", None)
    if client is None or not hasattr(client, "start_session"):
        _set_last_error("MongoDB không cung cấp transaction cho cập nhật lô hàng.")
        return False

    try:
        with client.start_session() as session:
            with session.start_transaction():
                old = db.shipments.find_one({"id": sid}, {"_id": 0}, session=session)
                payment_history_ok, payment_history_error = _payment_history_is_unchanged(old, shipment)
                if not payment_history_ok:
                    _set_last_error(payment_history_error)
                    return False
                query: dict[str, Any] = {"id": sid}
                if expected_version is not None and old is not None:
                    expected = int(expected_version)
                    if "version" not in old and expected == 0:
                        # Tương thích document cũ chưa có trường version.
                        query["$or"] = [{"version": 0}, {"version": {"$exists": False}}]
                    else:
                        query["version"] = expected
                set_on_insert = {
                    "created_by": effective_actor,
                    "created_by_user_id": actor_context["user_id"],
                    "created_by_role": actor_context["role"],
                }
                if "created_at" not in shipment:
                    set_on_insert["created_at"] = utc_now()
                update_fields = {
                    key: value
                    for key, value in shipment.items()
                    if key not in {"created_by", "created_by_user_id", "created_by_role"}
                }
                result = db.shipments.find_one_and_update(
                    query,
                    {
                        "$set": update_fields,
                        "$setOnInsert": set_on_insert,
                        "$inc": {"version": 1},
                    },
                    upsert=old is None,
                    return_document=ReturnDocument.AFTER,
                    session=session,
                )
                if result is None:
                    raise ConcurrentUpdateError("Dữ liệu đã được người khác cập nhật. Hãy Reload Data rồi lưu lại.")
                _audit(db, "shipment", sid, "create" if old is None else "update", before=old, after={k: v for k, v in result.items() if k != "_id"}, actor=effective_actor, session=session)

                if old is None:
                    _enqueue_domain_event(db, "shipment.created", {"shipment_id": sid, "customer": shipment.get("customer", ""), "mode": shipment["data"]["0.0"].get("mode", "")}, session=session)
                else:
                    old_status = old.get("status") or old.get("data", {}).get("0.0", {}).get("st")
                    if old_status != shipment["status"]:
                        _enqueue_domain_event(db, "shipment.status_changed", {"shipment_id": sid, "customer": shipment.get("customer", ""), "old_status": old_status, "new_status": shipment["status"]}, session=session)
                    old_eta = old.get("data", {}).get("2.6", {}).get("arrival_date")
                    new_eta = shipment.get("data", {}).get("2.6", {}).get("arrival_date")
                    if old_eta != new_eta:
                        _enqueue_domain_event(db, "shipment.eta_changed", {"shipment_id": sid, "customer": shipment.get("customer", ""), "old_eta": old_eta, "new_eta": new_eta}, session=session)
                _set_last_error("")
                return True
    except (PyMongoError, ConcurrentUpdateError, DuplicateKeyError) as exc:
        LOGGER.exception("save_shipment_atomic failed")
        _set_last_error(str(exc))
        return False


def save_direct_shipment_payment(
    shipment_id: str,
    payment_document: Mapping[str, Any],
    actor: str | None = None,
) -> tuple[bool, dict[str, Any], str]:
    """Persist one direct shipment payment with stable request identity.

    The request registry is intentionally shipment-optional so the same
    primitive can later support payment-only or held-money actions. This
    helper is the persistence boundary for the current shipment-linked path.
    """
    sid = str(shipment_id or "").strip()
    payment = copy.deepcopy(dict(payment_document))
    request_id = str(payment.get("request_id") or payment.get("idempotency_key") or "").strip()
    amount = to_decimal(payment.get("amount"))
    if not sid or not request_id:
        _set_last_error("Khoản thu phải có shipment_id và request identity.")
        return False, {}, get_last_db_error()
    if amount <= 0:
        _set_last_error("Số tiền thanh toán phải lớn hơn 0.")
        return False, {}, get_last_db_error()
    
    # LOG-LG08.1: Boundary RBAC enforcement
    from core.auth import can_operate_business
    if not can_operate_business("finance_write"):
        _set_last_error("Bạn không có quyền thực hiện giao dịch tài chính.")
        return False, {}, get_last_db_error()
    actor_context = _actor_context(actor)
    effective_actor = actor_context["username"]
        
    payment["request_id"] = request_id
    payment.setdefault("id", f"PAY-{uuid4().hex.upper()}")
    payment.pop("_id", None)
    fingerprint = _direct_payment_fingerprint(sid, payment)
    db = get_db()
    if db is None:
        _set_last_error("MongoDB chưa sẵn sàng.")
        return False, {}, get_last_db_error()
    client = _transaction_client(db)
    if client is None:
        return False, {}, get_last_db_error()

    def _existing_result(existing: Mapping[str, Any]) -> tuple[bool, dict[str, Any], str]:
        if existing.get("action_type") != "direct_shipment_payment" or existing.get("fingerprint") != fingerprint:
            _set_last_error("Request identity Đã được dùng cho financial action khác.")
            return False, {}, get_last_db_error()
        return True, dict(existing.get("result") or {}), "Khoản thu Đã được xử lý trước đó."

    try:
        with client.start_session() as session:
            with session.start_transaction():
                existing = db.financial_action_requests.find_one({"request_id": request_id}, session=session)
                if existing:
                    return _existing_result(existing)

                old = db.shipments.find_one({"id": sid, "is_deleted": {"$ne": True}}, {"_id": 0}, session=session)
                if not old:
                    raise RuntimeError(f"Không tìm thấy lô {sid}.")
                finance = old.setdefault("data", {}).setdefault("3.4", {})
                payments = finance.setdefault("payments", [])
                for existing_payment in payments:
                    if not isinstance(existing_payment, Mapping):
                        continue
                    if str(existing_payment.get("request_id") or "").strip() == request_id:
                        if _direct_payment_fingerprint(sid, existing_payment) != fingerprint:
                            raise RuntimeError("Request identity Đã có nội dung khác.")
                        result = _payment_result(sid, existing_payment)
                        db.financial_action_requests.insert_one(
                            {
                                "request_id": request_id,
                                "action_type": "direct_shipment_payment",
                                "fingerprint": fingerprint,
                                "status": "applied",
                                "shipment_id": sid,
                                "result": result,
                                "created_at": utc_now(),
                                "created_by": effective_actor,
                                "created_by_user_id": actor_context["user_id"],
                                "created_by_role": actor_context["role"],
                            },
                            session=session,
                        )
                        return True, result, "Khoản thu Đã tồn tại và được khóa theo request identity."

                ship = copy.deepcopy(old)
                ship.pop("_id", None)
                ship.setdefault("data", {}).setdefault("3.4", {}).setdefault("payments", []).append(
                    {
                        **payment,
                        "amount": float(amount),
                        "created_at": utc_now(),
                        "created_by": effective_actor,
                        "created_by_user_id": actor_context["user_id"],
                        "created_by_role": actor_context["role"],
                    }
                )
                summary = apply_financial_snapshot(ship)
                expected_version = int(old.get("version", 0) or 0)
                version_filter: dict[str, Any] = {"id": sid}
                if "version" not in old and expected_version == 0:
                    version_filter["$or"] = [{"version": 0}, {"version": {"$exists": False}}]
                else:
                    version_filter["version"] = expected_version
                updated = db.shipments.update_one(
                    version_filter,
                    {
                        "$set": {
                            "data": ship["data"],
                            "updated_at": utc_now(),
                            "updated_by": effective_actor,
                            "updated_by_user_id": actor_context["user_id"],
                            "updated_by_role": actor_context["role"],
                        },
                        "$inc": {"version": 1},
                    },
                    session=session,
                )
                if updated.modified_count != 1:
                    raise ConcurrentUpdateError(f"Lô {sid} vừa được người khác cập nhật. Hãy Reload Data rồi lưu lại.")
                saved_payment = ship["data"]["3.4"]["payments"][-1]
                result = {
                    **_payment_result(sid, saved_payment),
                    "version": expected_version + 1,
                    "derived_paid": summary["paid"],
                    "derived_debt": summary["debt"],
                }
                db.financial_action_requests.insert_one(
                    {
                        "request_id": request_id,
                        "action_type": "direct_shipment_payment",
                        "fingerprint": fingerprint,
                        "status": "applied",
                        "shipment_id": sid,
                        "result": result,
                        "created_at": utc_now(),
                        "created_by": effective_actor,
                        "created_by_user_id": actor_context["user_id"],
                        "created_by_role": actor_context["role"],
                    },
                    session=session,
                )
                # LOG-LG08.1: Audit and event MUST use the same session to ensure atomicity
                _audit(
                    db,
                    "shipment",
                    sid,
                    "direct_payment_created",
                    before={"paid": calculate_from_shipment(old)["paid"]},
                    after={"payment": saved_payment, "paid": summary["paid"], "debt": summary["debt"]},
                    actor=effective_actor,
                    session=session,
                )
                _enqueue_domain_event(
                    db,
                    "shipment.payment_recorded",
                    {"shipment_id": sid, "payment_id": saved_payment["id"], "request_id": request_id},
                    session=session,
                )
                return True, result, "Đã ghi nhận khoản thu."
    except DuplicateKeyError:
        existing = db.financial_action_requests.find_one({"request_id": request_id})
        if existing:
            return _existing_result(existing)
        _set_last_error("Financial action request bị trùng nhưng không đọc lại được.")
        return False, {}, get_last_db_error()
    except (PyMongoError, ConcurrentUpdateError, RuntimeError, ValueError) as exc:
        LOGGER.exception("save_direct_shipment_payment failed")
        _set_last_error(str(exc))
        return False, {}, get_last_db_error()


def save_direct_payment_correction(
    shipment_id: str,
    payment_id: str,
    correction_request_id: str,
    reason: str,
    evidence: Any = None,
    actor: str | None = None,
) -> tuple[bool, dict[str, Any], str]:
    """Traceably reverse one direct payment without deleting its history."""
    sid = str(shipment_id or "").strip()
    pid = str(payment_id or "").strip()
    request_id = str(correction_request_id or "").strip()
    reason = str(reason or "").strip()
    if not sid or not pid or not request_id or not reason:
        _set_last_error("Correction phải có original, request identity và reason.")
        return False, {}, get_last_db_error()
    from core.auth import can_operate_business
    if not can_operate_business("finance_write"):
        _set_last_error("Bạn không có quyền thực hiện correction tài chính.")
        return False, {}, get_last_db_error()
    actor_context = _actor_context(actor)
    effective_actor = actor_context["username"]
    fingerprint = _financial_fingerprint(
        {
            "shipment_id": sid,
            "payment_id": pid,
            "reason": reason,
            "evidence": evidence,
        }
    )
    db = get_db()
    if db is None:
        _set_last_error("MongoDB chưa sẵn sàng.")
        return False, {}, get_last_db_error()
    client = _transaction_client(db)
    if client is None:
        return False, {}, get_last_db_error()

    def _existing_correction(existing: Mapping[str, Any]) -> tuple[bool, dict[str, Any], str]:
        if existing.get("fingerprint") != fingerprint:
            _set_last_error("Correction request identity Đã được dùng cho nội dung khác.")
            return False, {}, get_last_db_error()
        return True, dict(existing.get("result") or {}), "Correction Đã được xử lý trước đó."

    try:
        with client.start_session() as session:
            with session.start_transaction():
                existing = db.financial_corrections.find_one({"correction_request_id": request_id}, session=session)
                if existing:
                    return _existing_correction(existing)
                old = db.shipments.find_one({"id": sid, "is_deleted": {"$ne": True}}, {"_id": 0}, session=session)
                if not old:
                    raise RuntimeError(f"Không tìm thấy lô {sid}.")
                ship = copy.deepcopy(old)
                payments = ship.setdefault("data", {}).setdefault("3.4", {}).setdefault("payments", [])
                target = next((row for row in payments if isinstance(row, Mapping) and str(row.get("id") or "") == pid), None)
                if target is None:
                    raise RuntimeError(f"Không tìm thấy payment {pid}.")
                if str(target.get("status") or "").strip().lower() in _INACTIVE_PAYMENT_STATUSES or target.get("is_reversed"):
                    raise RuntimeError(f"Payment {pid} Đã được reversal trước đó.")
                original = copy.deepcopy(dict(target))
                correction_id = f"CORR-{uuid4().hex.upper()}"
                target["status"] = "reversed"
                target["is_reversed"] = True
                target["reversed_by"] = correction_id
                target["reversed_at"] = utc_now()
                target["reversal_reason"] = reason
                target["reversed_by_actor"] = effective_actor
                target["reversed_by_user_id"] = actor_context["user_id"]
                target["reversed_by_role"] = actor_context["role"]
                summary = apply_financial_snapshot(ship)
                expected_version = int(old.get("version", 0) or 0)
                version_filter: dict[str, Any] = {"id": sid}
                if "version" not in old and expected_version == 0:
                    version_filter["$or"] = [{"version": 0}, {"version": {"$exists": False}}]
                else:
                    version_filter["version"] = expected_version
                updated = db.shipments.update_one(
                    version_filter,
                    {
                        "$set": {
                            "data": ship["data"],
                            "updated_at": utc_now(),
                            "updated_by": effective_actor,
                            "updated_by_user_id": actor_context["user_id"],
                            "updated_by_role": actor_context["role"],
                        },
                        "$inc": {"version": 1},
                    },
                    session=session,
                )
                if updated.modified_count != 1:
                    raise ConcurrentUpdateError(f"Lô {sid} vừa được người khác cập nhật. Hãy Reload Data rồi lưu lại.")
                result = {
                    "correction_id": correction_id,
                    "shipment_id": sid,
                    "original_payment_id": pid,
                    "derived_paid": summary["paid"],
                    "derived_debt": summary["debt"],
                    "version": expected_version + 1,
                }
                correction = {
                    "correction_request_id": request_id,
                    "correction_id": correction_id,
                    "correction_type": "payment_reversal",
                    "original_type": "shipment_payment",
                    "original_id": pid,
                    "shipment_id": sid,
                    "reason": reason,
                    "evidence": copy.deepcopy(evidence),
                    "actor": effective_actor,
                    "actor_user_id": actor_context["user_id"],
                    "actor_role": actor_context["role"],
                    "created_at": utc_now(),
                    "status": "applied",
                    "fingerprint": fingerprint,
                    "result": result,
                }
                db.financial_corrections.insert_one(correction, session=session)
                _audit(db, "shipment", sid, "payment_reversed", before={"payment": original}, after={"correction": correction}, actor=effective_actor, session=session)
                _audit(db, "financial_correction", correction_id, "create", before=None, after=correction, actor=effective_actor, session=session)
                _enqueue_domain_event(
                    db,
                    "shipment.payment_reversed",
                    {"shipment_id": sid, "payment_id": pid, "correction_id": correction_id},
                    session=session,
                )
                return True, result, "Đã ghi correction/reversal có liên kết."
    except DuplicateKeyError:
        existing = db.financial_corrections.find_one({"correction_request_id": request_id})
        if existing:
            return _existing_correction(existing)
        _set_last_error("Correction request bị trùng nhưng không đọc lại được.")
        return False, {}, get_last_db_error()
    except (PyMongoError, ConcurrentUpdateError, RuntimeError, ValueError) as exc:
        LOGGER.exception("save_direct_payment_correction failed")
        _set_last_error(str(exc))
        return False, {}, get_last_db_error()


def delete_shipment(sid: str, reason: str = "") -> bool:
    # LOG-LG02 R4 bounded tightening: backend gate, so soft delete can never
    # execute through a UI-only authorization defect.
    from core.auth import has_write_permission  # noqa: PLC0415
    if not has_write_permission("shipment_delete"):
        from core.auth import PermissionDeniedError  # noqa: PLC0415
        raise PermissionDeniedError("shipment_delete")
    db = get_db()
    if db is None:
        return False
    try:
        old = db.shipments.find_one({"id": sid}, {"_id": 0})
        actor_context = _actor_context()
        result = db.shipments.update_one(
            {"id": sid, "is_deleted": {"$ne": True}},
            {"$set": {
                "is_deleted": True,
                "deleted_at": utc_now(),
                "deleted_by": actor_context["username"],
                "deleted_by_user_id": actor_context["user_id"],
                "deleted_by_role": actor_context["role"],
                "delete_reason": reason,
            }},
        )
        if result.modified_count:
            _audit(db, "shipment", sid, "soft_delete", before=old, after={"reason": reason})
            return True
        return False
    except PyMongoError as exc:
        _set_last_error(str(exc))
        return False


def rename_shipment_id(old_id: str, new_id: str) -> bool:
    old_id, new_id = old_id.strip(), new_id.strip()
    if not old_id or not new_id or old_id == new_id:
        return old_id == new_id
    if not _require_business_permission("shipment_edit", "Bạn không có quyền đổi mã lô hàng."):
        return False
    db = get_db()
    if db is None:
        return False
    try:
        if db.shipments.find_one({"id": new_id, "is_deleted": {"$ne": True}}):
            _set_last_error("Mã lô mới đã tồn tại.")
            return False
        old = db.shipments.find_one({"id": old_id}, {"_id": 0})
        if not old:
            return False
        actor_context = _actor_context()
        db.shipments.update_one(
            {"id": old_id},
            {"$set": {
                "id": new_id,
                "shipment_id": new_id,
                "updated_at": utc_now(),
                "updated_by": actor_context["username"],
                "updated_by_user_id": actor_context["user_id"],
                "updated_by_role": actor_context["role"],
            }, "$inc": {"version": 1}},
        )
        db.proxy_payments.update_many({"linked_id": old_id}, {"$set": {"linked_id": new_id}})
        db.entrustments.update_many({"linked_id": old_id}, {"$set": {"linked_id": new_id}})
        _audit(db, "shipment", new_id, "rename", before={"id": old_id}, after={"id": new_id})
        return True
    except (PyMongoError, DuplicateKeyError) as exc:
        _set_last_error(str(exc))
        return False


def update_shipment_customer(sid: str, new_customer_name: str, customer_id: str = "") -> bool:
    if not _require_business_permission("shipment_edit", "Bạn không có quyền cập nhật khách hàng của lô hàng."):
        return False
    db = get_db()
    if db is None:
        return False
    old = db.shipments.find_one({"id": sid}, {"_id": 0})
    actor_context = _actor_context()
    fields = {
        "client": new_customer_name,
        "customer": new_customer_name,
        "updated_at": utc_now(),
        "updated_by": actor_context["username"],
        "updated_by_user_id": actor_context["user_id"],
        "updated_by_role": actor_context["role"],
    }
    if customer_id:
        fields["customer_id"] = customer_id
    try:
        result = db.shipments.update_one({"id": sid}, {"$set": fields, "$inc": {"version": 1}})
        if result.modified_count > 0:
            _audit(db, "shipment", sid, "customer_updated", before=old, after=fields)
        return result.modified_count > 0
    except PyMongoError as exc:
        _set_last_error(str(exc))
        return False


def generate_shipment_id(prefix: str = "SHP") -> str:
    db = get_db()
    today = datetime.now().strftime("%Y%m%d")
    if db is None:
        return f"{prefix}-{today}-{uuid4().hex[:4].upper()}"
    counter = db.counters.find_one_and_update(
        {"_id": f"shipment_{today}"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return f"{prefix}-{today}-{int(counter['seq']):03d}"


def _load_dict(collection: str, key: str = "id", query: Mapping[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    db = get_db()
    if db is None:
        return {}
    try:
        return {str(doc.get(key)): doc for doc in db[collection].find(dict(query or {}), {"_id": 0}) if doc.get(key) is not None}
    except PyMongoError as exc:
        _set_last_error(str(exc))
        return {}


def _save_document(
    collection: str,
    document: dict[str, Any],
    key: str = "id",
    *,
    db=None,
    session=None,
) -> bool:
    db = db if db is not None else get_db()
    if db is None or not document.get(key):
        return False
    payload = copy.deepcopy(document)
    payload.pop("_id", None)
    actor_context = _actor_context()
    payload["updated_at"] = utc_now()
    payload["updated_by"] = actor_context["username"]
    payload["updated_by_user_id"] = actor_context["user_id"]
    payload["updated_by_role"] = actor_context["role"]
    try:
        set_on_insert = {
            "created_by": actor_context["username"],
            "created_by_user_id": actor_context["user_id"],
            "created_by_role": actor_context["role"],
        }
        if "created_at" not in payload:
            set_on_insert["created_at"] = utc_now()
        update = {"$set": payload}
        if set_on_insert:
            update["$setOnInsert"] = set_on_insert
        db[collection].update_one({key: payload[key]}, update, upsert=True, session=session)
        return True
    except PyMongoError as exc:
        _set_last_error(str(exc))
        return False


def load_customers() -> dict[str, dict[str, Any]]:
    """Load customers. Cached in Streamlit runtime for performance."""
    if st is not None and is_streamlit_runtime():
        return st.cache_data(_load_customers_impl, ttl=30, show_spinner=False)()
    return _load_customers_impl()


def _load_customers_impl() -> dict[str, dict[str, Any]]:
    return _load_dict("customers", query={"is_deleted": {"$ne": True}})


def save_customer_to_cloud(document: dict[str, Any]) -> bool:
    if not _require_business_permission("customers", "Bạn không có quyền cập nhật khách hàng."):
        return False
    db = get_db()
    if db is None or not document.get("id"):
        return False
    customer_id = str(document["id"])
    old = db.customers.find_one({"id": customer_id}, {"_id": 0})
    ok = _save_document("customers", document)
    if ok:
        _audit(db, "customer", customer_id, "create" if old is None else "update", before=old, after=document)
    return ok


def delete_customer(cust_id: str, reason: str = "") -> bool:
    if not _require_business_permission("customer_delete", "Bạn không có quyền lưu trữ khách hàng."):
        return False
    db = get_db()
    if db is None:
        return False
    old = db.customers.find_one({"id": cust_id}, {"_id": 0})
    result = db.customers.update_one(
        {"id": cust_id, "is_deleted": {"$ne": True}},
        {"$set": {"is_deleted": True, "deleted_at": utc_now(), "deleted_by": _actor(), "delete_reason": reason}},
    )
    if result.modified_count:
        _audit(db, "customer", cust_id, "soft_delete", before=old, after={"reason": reason})
        return True
    return False


def load_contracts() -> dict[str, dict[str, Any]]:
    """Load contracts. Cached in Streamlit runtime for performance."""
    if st is not None and is_streamlit_runtime():
        return st.cache_data(_load_contracts_impl, ttl=30, show_spinner=False)()
    return _load_contracts_impl()


def _load_contracts_impl() -> dict[str, dict[str, Any]]:
    raw = _load_dict("contracts", query={"is_deleted": {"$ne": True}})
    return {str(value.get("ContractNo") or value.get("id")): value for value in raw.values()}


def save_contract_to_cloud(document: dict[str, Any]) -> bool:
    from core.auth import can_edit_contract

    if not can_edit_contract():
        _set_last_error("Bạn không có quyền sửa hợp đồng.")
        return False
    db = get_db()
    if db is None or not document.get("id"):
        return False
    payload = copy.deepcopy(document)
    contract_id = str(payload["id"]).strip().upper()
    payload["id"] = contract_id
    payload["contract_no"] = str(payload.get("contract_no") or contract_id)
    payload["normalized_no"] = normalize_contract_no(payload.get("normalized_no") or contract_id)
    old = db.contracts.find_one({"id": contract_id}, {"_id": 0})
    ok = _save_document("contracts", payload)
    if ok:
        _audit(db, "contract", contract_id, "create" if old is None else "update", before=old, after=payload)
    return ok


def load_contract_transactions(contract_id: str | None = None) -> dict[str, dict[str, Any]]:
    """Load contract transactions. Cached in Streamlit runtime for performance."""
    if st is not None and is_streamlit_runtime():
        return st.cache_data(_load_contract_transactions_impl, ttl=30, show_spinner=False)(contract_id)
    return _load_contract_transactions_impl(contract_id)


def _load_contract_transactions_impl(contract_id: str | None = None) -> dict[str, dict[str, Any]]:
    """Load typed contract-finance rows, optionally scoped to one contract."""
    query: dict[str, Any] = {"is_deleted": {"$ne": True}}
    if contract_id:
        query["contract_id"] = str(contract_id).strip().upper()
    return _load_dict("contract_transactions", query=query)


def save_contract_transaction(document: dict[str, Any]) -> bool:
    """Persist a contract finance row without changing legacy payment stores."""
    from core.auth import can_edit_contract

    if not can_edit_contract():
        _set_last_error("Bạn không có quyền sửa giao dịch hợp đồng.")
        return False
    db = get_db()
    if db is None or not document.get("id") or not document.get("contract_id"):
        _set_last_error("Giao dịch hợp đồng cần có mã giao dịch và mã hợp đồng.")
        return False
    payload = copy.deepcopy(document)
    payload["id"] = str(payload["id"]).strip().upper()
    payload["contract_id"] = str(payload["contract_id"]).strip().upper()
    payload["transaction_type"] = str(payload.get("transaction_type") or "other").strip().lower()
    old = db.contract_transactions.find_one({"id": payload["id"]}, {"_id": 0})
    ok = _save_document("contract_transactions", payload)
    if ok:
        _audit(
            db,
            "contract_transaction",
            payload["id"],
            "create" if old is None else "update",
            before=old,
            after=payload,
        )
    return ok


def save_contract_proxy_payment_atomic(
    payment_document: dict[str, Any],
    transaction_document: dict[str, Any],
    actor: str | None = None,
) -> bool:
    """Persist a contract proxy payment and its typed transaction together.

    The contract form represents one financial event in two collections.  Both
    writes and both audit rows must share one Mongo transaction.  If the
    deployment cannot start a transaction, this function fails closed before
    either document is persisted; it does not fall back to two independent
    saves or compensation logic.
    """
    from core.auth import can_edit_contract

    if not can_edit_contract():
        _set_last_error("Bạn không có quyền sửa thanh toán trong hợp đồng.")
        return False
    db = get_db()
    if db is None:
        _set_last_error("MongoDB chưa sẵn sàng.")
        return False
    if not payment_document.get("id") or not transaction_document.get("id"):
        _set_last_error("Thanh toán hộ cần có mã giao dịch.")
        return False
    if not payment_document.get("contract_id") or not transaction_document.get("contract_id"):
        _set_last_error("Thanh toán hộ cần có mã hợp đồng.")
        return False

    payment = copy.deepcopy(payment_document)
    transaction = copy.deepcopy(transaction_document)
    payment["id"] = str(payment["id"]).strip().upper()
    payment["contract_id"] = str(payment["contract_id"]).strip().upper()
    transaction["id"] = str(transaction["id"]).strip().upper()
    transaction["contract_id"] = str(transaction["contract_id"]).strip().upper()
    transaction["transaction_type"] = str(transaction.get("transaction_type") or "other").strip().lower()

    client = getattr(db, "client", None)
    if client is None or not hasattr(client, "start_session"):
        _set_last_error("MongoDB không cung cấp transaction cho giao dịch hợp đồng.")
        return False

    try:
        with client.start_session() as session:
            with session.start_transaction():
                old_payment = db.proxy_payments.find_one({"id": payment["id"]}, {"_id": 0}, session=session)
                if not _save_document("proxy_payments", payment, db=db, session=session):
                    raise RuntimeError("Không lưu được thanh toán hộ.")
                _audit(
                    db,
                    "proxy_payment",
                    payment["id"],
                    "create" if old_payment is None else "update",
                    before=old_payment,
                    after=payment,
                    actor=actor,
                    session=session,
                )

                old_transaction = db.contract_transactions.find_one(
                    {"id": transaction["id"]},
                    {"_id": 0},
                    session=session,
                )
                if not _save_document("contract_transactions", transaction, db=db, session=session):
                    raise RuntimeError("Không lưu được giao dịch hợp đồng.")
                _audit(
                    db,
                    "contract_transaction",
                    transaction["id"],
                    "create" if old_transaction is None else "update",
                    before=old_transaction,
                    after=transaction,
                    actor=actor,
                    session=session,
                )
        _set_last_error("")
        return True
    except Exception as exc:
        LOGGER.exception("save_contract_proxy_payment_atomic failed")
        _set_last_error(str(exc))
        return False


def load_quotes() -> dict[str, dict[str, Any]]:
    return _load_dict("quotes", query={"is_deleted": {"$ne": True}})


def save_quotes_to_cloud(quotes_dict: Mapping[str, dict[str, Any]]) -> bool:
    if not _require_business_permission("sales_write", "Bạn không có quyền lưu báo giá."):
        return False
    db = get_db()
    if db is None:
        return False
    for document in quotes_dict.values():
        quote_id = str(document.get("id") or "").strip()
        if not quote_id:
            return False
        old = db["quotes"].find_one({"id": quote_id}, {"_id": 0})
        if not _save_document("quotes", document):
            return False
        _audit(db, "quote", quote_id, "create" if old is None else "update", before=old, after=document)
    return True


def load_rate_cards() -> dict[str, dict[str, Any]]:
    return _load_dict("rate_cards", query={"is_deleted": {"$ne": True}})


def save_rate_card(document: dict[str, Any]) -> bool:
    if not _require_business_permission("tariff", "Bạn không có quyền cập nhật báo giá khung."):
        return False
    db = get_db()
    if db is None or not document.get("id"):
        return False
    rate_card_id = str(document["id"])
    old = db.rate_cards.find_one({"id": rate_card_id}, {"_id": 0})
    ok = _save_document("rate_cards", document)
    if ok:
        _audit(db, "rate_card", rate_card_id, "create" if old is None else "update", before=old, after=document)
    return ok


def load_tasks() -> list[dict[str, Any]]:
    db = get_db()
    if db is None:
        return []
    try:
        return list(db.tasks.find({"is_deleted": {"$ne": True}}).sort("created_at", -1))
    except PyMongoError as exc:
        _set_last_error(str(exc))
        return []


def add_task(content: str, assignee: str = "All", deadline_str: str = "", assignee_user_id: str = "", assigned_by_user_id: str = "") -> bool:
    if not _require_business_permission("shipment_edit", "Bạn không có quyền giao việc."):
        return False
    db = get_db()
    if db is None:
        return False
    actor_context = _actor_context()
    doc = {
        "task_id": str(uuid4()),
        "content": content,
        "assignee": assignee,
        "deadline": deadline_str,
        "done": False,
        "created_at": utc_now(),
        "created_by": actor_context["username"],
        "created_by_user_id": actor_context["user_id"],
        "created_by_role": actor_context["role"],
    }
    if assignee_user_id:
        doc["assignee_user_id"] = assignee_user_id
    if assigned_by_user_id:
        doc["assigned_by_user_id"] = assigned_by_user_id
    db.tasks.insert_one(doc)
    _audit(db, "task", doc["task_id"], "create", after=doc)
    return True


def delete_task(tid: str) -> bool:
    if not _require_business_permission("task_delete", "Bạn không có quyền xóa công việc."):
        return False
    db = get_db()
    if db is None:
        return False
    old = db.tasks.find_one({"_id": ObjectId(tid)}, {"_id": 0})
    actor_context = _actor_context()
    result = db.tasks.update_one(
        {"_id": ObjectId(tid)},
        {"$set": {
            "is_deleted": True,
            "deleted_at": utc_now(),
            "deleted_by": actor_context["username"],
            "deleted_by_user_id": actor_context["user_id"],
            "deleted_by_role": actor_context["role"],
        }},
    )
    if result.modified_count > 0:
        _audit(db, "task", tid, "soft_delete", before=old, after={"is_deleted": True})
    return result.modified_count > 0


def toggle_task(tid: str, status: bool) -> bool:
    if not _require_business_permission("shipment_edit", "Bạn không có quyền cập nhật công việc."):
        return False
    db = get_db()
    if db is None:
        return False
    old = db.tasks.find_one({"_id": ObjectId(tid)}, {"_id": 0})
    actor_context = _actor_context()
    result = db.tasks.update_one(
        {"_id": ObjectId(tid)},
        {"$set": {
            "done": bool(status),
            "updated_at": utc_now(),
            "updated_by": actor_context["username"],
            "updated_by_user_id": actor_context["user_id"],
            "updated_by_role": actor_context["role"],
        }},
    )
    if result.modified_count > 0:
        _audit(db, "task", tid, "status_updated", before=old, after={"done": bool(status)})
    return result.modified_count > 0


def load_quick_note() -> tuple[str, str]:
    db = get_db()
    if db is None:
        return "", ""
    doc = db.quick_notes.find_one({"id": "team_note"})
    return (doc.get("content", ""), str(doc.get("updated_at", ""))) if doc else ("", "")


def save_quick_note(content: str) -> bool:
    if not _require_business_permission("shipment_edit", "Bạn không có quyền cập nhật sổ tay."):
        return False
    db = get_db()
    if db is None:
        return False
    old = db.quick_notes.find_one({"id": "team_note"}, {"_id": 0})
    ok = _save_document("quick_notes", {"id": "team_note", "content": content})
    if ok:
        _audit(db, "quick_note", "team_note", "update", before=old, after={"content": content})
    return ok


def load_entrustments() -> dict[str, dict[str, Any]]:
    return _load_dict("entrustments", query={"is_deleted": {"$ne": True}})


def save_entrustment(document: dict[str, Any]) -> bool:
    if not _require_business_permission("entrustment", "Bạn không có quyền cập nhật thanh toán hộ."):
        return False
    db = get_db()
    if db is None or not document.get("id"):
        return False
    identifier = str(document["id"])
    old = db["entrustments"].find_one({"id": identifier}, {"_id": 0})
    ok = _save_document("entrustments", document)
    if ok:
        _audit(db, "entrustment", identifier, "create" if old is None else "update", before=old, after=document)
    return ok


def save_entrustment_book(
    documents: Mapping[str, dict[str, Any]],
    request_id: str | None = None,
    actor: str | None = None,
) -> bool:
    """Persist an entrustment UI batch atomically and idempotently."""
    if not documents:
        return True
    if not _require_business_permission("entrustment", "Bạn không có quyền cập nhật thanh toán hộ."):
        return False
    stable_request_id = str(request_id or "").strip()
    if not stable_request_id:
        _set_last_error("Entrustment batch phải có request identity.")
        return False
    db = get_db()
    if db is None:
        _set_last_error("MongoDB chưa sẵn sàng.")
        return False
    client = _transaction_client(db)
    if client is None:
        return False
    fingerprint = _entrustment_batch_fingerprint(documents)
    actor_context = _actor_context(actor)

    def _matches_existing(existing: Mapping[str, Any]) -> bool:
        if existing.get("action_type") == "entrustment_batch" and existing.get("fingerprint") == fingerprint:
            _set_last_error("")
            return True
        _set_last_error("Entrustment request identity Đã được dùng cho batch khác.")
        return False

    try:
        with client.start_session() as session:
            with session.start_transaction():
                existing = db.financial_action_requests.find_one({"request_id": stable_request_id}, session=session)
                if existing:
                    return _matches_existing(existing)
                saved_ids: list[str] = []
                for code, document in documents.items():
                    payload = copy.deepcopy(dict(document))
                    payload["id"] = str(code)
                    old = db.entrustments.find_one({"id": str(code)}, {"_id": 0}, session=session)
                    if not _save_document("entrustments", payload, db=db, session=session):
                        raise RuntimeError(f"Không lưu được entrustment {code}.")
                    _audit(
                        db,
                        "entrustment",
                        str(code),
                        "create" if old is None else "update",
                        before=old,
                        after=payload,
                        actor=actor,
                        session=session,
                    )
                    saved_ids.append(str(code))
                result = {"entrustment_ids": saved_ids, "count": len(saved_ids)}
                db.financial_action_requests.insert_one(
                    {
                        "request_id": stable_request_id,
                        "action_type": "entrustment_batch",
                        "fingerprint": fingerprint,
                        "status": "applied",
                        "shipment_id": None,
                        "result": result,
                        "created_at": utc_now(),
                        "created_by": actor_context["username"],
                        "created_by_user_id": actor_context["user_id"],
                        "created_by_role": actor_context["role"],
                    },
                    session=session,
                )
                _set_last_error("")
                return True
    except DuplicateKeyError:
        existing = db.financial_action_requests.find_one({"request_id": stable_request_id})
        if existing:
            return _matches_existing(existing)
        _set_last_error("Entrustment request bị trùng nhưng không đọc lại được.")
        return False
    except (PyMongoError, RuntimeError, ValueError) as exc:
        LOGGER.exception("save_entrustment_book failed")
        _set_last_error(str(exc))
        return False


def load_knowledge_base() -> list[dict[str, Any]]:
    db = get_db()
    if db is None:
        return []
    return list(db.knowledge_base.find({"is_deleted": {"$ne": True}}, {"_id": 0}).sort("created_at", -1))


def save_knowledge_entry(document: dict[str, Any]) -> bool:
    payload = dict(document)
    payload.setdefault("id", str(uuid4()))
    payload.setdefault("created_at", utc_now())
    return _save_document("knowledge_base", payload)


def delete_knowledge_entry(entry_id: str) -> bool:
    if not _require_business_permission("knowledge_delete", "Bạn không có quyền xóa ghi chú."):
        return False
    db = get_db()
    if db is None:
        return False
    old = db.knowledge_base.find_one({"id": entry_id}, {"_id": 0})
    actor_context = _actor_context()
    result = db.knowledge_base.update_one(
        {"id": entry_id},
        {"$set": {
            "is_deleted": True,
            "deleted_at": utc_now(),
            "deleted_by": actor_context["username"],
            "deleted_by_user_id": actor_context["user_id"],
            "deleted_by_role": actor_context["role"],
        }},
    )
    if result.modified_count:
        _audit(db, "knowledge_entry", entry_id, "soft_delete", before=old, after={"is_deleted": True})
    return result.modified_count > 0


def load_cbpg_workspace() -> dict[str, Any] | None:
    db = get_db()
    if db is None:
        return None
    return db.cbpg_workspaces.find_one({"id": "default"}, {"_id": 0})


def save_cbpg_workspace(unit: str, invoice_total: float, items: list[dict[str, Any]]) -> bool:
    if not _require_business_permission("tariff", "Bạn không có quyền cập nhật workspace CBPG."):
        return False
    db = get_db()
    if db is None:
        return False
    payload = {"id": "default", "unit": unit, "invoice_total": invoice_total, "items": items}
    old = db.cbpg_workspaces.find_one({"id": "default"}, {"_id": 0})
    ok = _save_document("cbpg_workspaces", payload)
    if ok:
        _audit(db, "cbpg_workspace", "default", "create" if old is None else "update", before=old, after=payload)
    return ok


def load_audit_logs(entity_type: str, entity_id: str, limit: int = 100) -> list[dict[str, Any]]:
    db = get_db()
    if db is None:
        return []
    return list(db.audit_logs.find({"entity_type": entity_type, "entity_id": entity_id}, {"_id": 0}).sort("created_at", -1).limit(limit))


def load_proxy_payments() -> dict[str, dict[str, Any]]:
    return _load_dict("proxy_payments", query={"is_deleted": {"$ne": True}})


def save_proxy_payment(document: dict[str, Any]) -> bool:
    if not _require_business_permission("proxy_payment", "Bạn không có quyền cập nhật thanh toán hộ."):
        return False
    db = get_db()
    if db is None or not document.get("id"):
        return False
    old = db.proxy_payments.find_one({"id": document["id"]}, {"_id": 0})
    ok = _save_document("proxy_payments", document)
    if ok:
        _audit(db, "proxy_payment", str(document["id"]), "create" if old is None else "update", before=old, after=document)
    return ok


def delete_proxy_payment(payment_id: str, reason: str = "") -> bool:
    if not _require_business_permission("proxy_payment_delete", "Bạn không có quyền lưu trữ thanh toán hộ."):
        return False
    db = get_db()
    if db is None:
        return False
    old = db.proxy_payments.find_one({"id": payment_id}, {"_id": 0})
    actor_context = _actor_context()
    result = db.proxy_payments.update_one(
        {"id": payment_id},
        {"$set": {
            "is_deleted": True,
            "deleted_at": utc_now(),
            "deleted_by": actor_context["username"],
            "deleted_by_user_id": actor_context["user_id"],
            "deleted_by_role": actor_context["role"],
            "delete_reason": reason,
        }},
    )
    if result.modified_count:
        _audit(db, "proxy_payment", payment_id, "soft_delete", before=old, after={"reason": reason})
        return True
    return False


# ---------- LG03 restore (4578d3f): user persistence API ----------
# Da bi mat trong commit 0d6ce55 (LG02 mojibake hotfix). Phuc hoi co gioi han.

def load_users() -> dict[str, dict[str, Any]]:
    """Toan bo user documents (gom password_hash — chi core.auth dung de xac thuc)."""
    db = get_db()
    if db is None:
        return {}
    return {
        str(doc["username"]): {k: v for k, v in doc.items() if k != "_id"}
        for doc in db.users.find({}, {"_id": 0})
        if doc.get("username") and not doc.get("is_deleted")
    }

def save_user(document: dict[str, Any]) -> bool:
    """Tao hoac cap nhat user theo khoa username; ghi audit."""
    if not document.get("username"):
        return False
    from core.auth import can_operate_business, current_user

    authenticated_user = current_user()
    if authenticated_user.get("username") and not can_operate_business("*"):
        _set_last_error("Chỉ Admin mới được quản lý tài khoản người dùng.")
        return False
    db = get_db()
    if db is None:
        return False
    if not can_operate_business("*"):
        # The only unauthenticated exception is first-admin bootstrap. Once a
        # user exists, an actor string cannot substitute for Admin auth.
        if db.users.find_one({}, {"_id": 1}) is not None:
            _set_last_error("Chỉ Admin mới được quản lý tài khoản người dùng.")
            return False
    try:
        safe = {k: v for k, v in document.items() if k != "_id"}
        db.users.update_one(
            {"username": str(document["username"])},
            {"$set": safe},
            upsert=True,
        )
        _audit(db, "user", str(document["username"]), "create", after=safe)
        return True
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("save_user failed")
        return False

def update_user(username: str, payload: dict[str, Any] | None = None, *, document: dict[str, Any] | None = None, actor: str = "system") -> bool:
    """Cap nhat user da ton tai; khong tao moi.
    - payload={{...}}: partial $set (caller hien tai views/web_app.py)
    - document={{...}}: full $set document (caller legacy)
    """
    if not _require_business_permission("*", "Chỉ Admin mới được cập nhật tài khoản người dùng."):
        return False
    db = get_db()
    if db is None:
        return False
    safe = (payload or document) or {}
    if not safe:
        return False
    try:
        result = db.users.update_one({"username": str(username)}, {"$set": safe})
        _audit(db, "user", str(username), "update", after=safe, actor=actor)
        return bool(result.matched_count)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("update_user failed")
        return False

def delete_user(username: str, actor: str = "system") -> bool:
    """Soft delete user (giu audit trail); hard delete chi khi is_deleted san."""
    if not _require_business_permission("*", "Chỉ Admin mới được xóa tài khoản người dùng."):
        return False
    db = get_db()
    if db is None:
        return False
    old = db.users.find_one({"username": str(username)}, {"_id": 0})
    if old is None:
        return False
    if old.get("is_deleted"):
        result = db.users.delete_one({"username": str(username)})
        if result.deleted_count:
            _audit(db, "user", str(username), "hard_delete", before=old, actor=actor)
            return True
        return False
    result = db.users.update_one(
        {"username": str(username)},
        {"$set": {"is_deleted": True, "deleted_at": utc_now(), "deleted_by": str(actor)}},
    )
    if result.modified_count:
        _audit(db, "user", str(username), "soft_delete", before=old, actor=actor)
        return True
    return False
# ---------- /LG03 restore ----------


# ---------- LG03 restore #2 (83a567c): agreements API ----------

def load_agreements() -> dict[str, dict[str, Any]]:
    """Load LOG-C13 commercial agreements (agreed commercial terms, not finance)."""
    return _load_dict("agreements", query={"is_deleted": {"$ne": True}})

def save_agreements_to_cloud(agreements_dict: dict[str, dict[str, Any]]) -> bool:
    """Upsert commercial agreements. 0 canonical finance writes by contract."""
    if not _require_business_permission("commercial_write", "Bạn không có quyền cập nhật thỏa thuận thương mại."):
        return False
    db = get_db()
    if db is None:
        return False
    for document in agreements_dict.values():
        agreement_id = str(document.get("id") or document.get("agreement_id") or "").strip()
        if not agreement_id:
            return False
        old = db["agreements"].find_one({"id": agreement_id}, {"_id": 0})
        if not _save_document("agreements", document):
            return False
        _audit(db, "agreement", agreement_id, "create" if old is None else "update", before=old, after=document)
    return True

# ---------- /LG03 restore #2 ----------
