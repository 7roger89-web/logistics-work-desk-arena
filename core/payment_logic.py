"""Công nợ khách hàng và phân bổ khoản thu FIFO."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Mapping
from uuid import uuid4

from core.logic import apply_financial_snapshot, calculate_from_shipment
from core.utils import parse_date_optional, to_decimal, utc_now


def _matches_customer(shipment: Mapping[str, Any], customer_ref: str) -> bool:
    return customer_ref in {
        str(shipment.get("customer_id", "")),
        str(shipment.get("customer", "")),
        str(shipment.get("client", "")),
    }


def get_customer_debt_overview(customer_ref: str, all_shipments: Mapping[str, dict[str, Any]]):
    customer_ships = [shipment for shipment in all_shipments.values() if _matches_customer(shipment, customer_ref)]
    customer_ships.sort(key=lambda ship: parse_date_optional(ship.get("data", {}).get("0.0", {}).get("created_at")) or date.max)

    unpaid_shipments: list[dict[str, Any]] = []
    total_debt = Decimal("0")
    total_receivable = Decimal("0")

    for raw_ship in customer_ships:
        ship = raw_ship
        summary = calculate_from_shipment(ship)
        debt = to_decimal(summary["debt"])
        total_receivable += to_decimal(summary["receivable"])
        if debt > Decimal("1000"):
            total_debt += debt

        payments = ship.get("data", {}).get("3.4", {}).get("payments", [])
        dated = [(parse_date_optional(payment.get("date")) or date.min, payment) for payment in payments]
        last_payment = max(dated, key=lambda item: item[0])[1] if dated else None
        unpaid_shipments.append({
            "id": ship.get("id"),
            "created_at": ship.get("data", {}).get("0.0", {}).get("created_at"),
            "revenue": float(to_decimal(summary["receivable"])),
            "paid": float(to_decimal(summary["paid"])),
            "debt": float(debt),
            "last_payment": last_payment.get("date", "-") if last_payment else "-",
            "status": "✅ Đủ" if debt <= Decimal("1000") else "❌ Nợ",
            "original_data": ship,
        })

    return float(total_debt), float(total_receivable), unpaid_shipments


def allocate_lump_sum(amount: Any, unpaid_shipments: list[dict[str, Any]]):
    remaining = to_decimal(amount)
    if remaining <= 0:
        return [], float(remaining)

    allocation_plan: list[dict[str, Any]] = []
    pending = [shipment for shipment in unpaid_shipments if to_decimal(shipment.get("debt")) > Decimal("1000")]
    pending.sort(key=lambda ship: parse_date_optional(ship.get("created_at")) or date.max)

    for shipment in pending:
        if remaining <= 0:
            break
        debt = to_decimal(shipment["debt"])
        pay_amount = min(debt, remaining)
        allocation_plan.append({
            "shipment_id": shipment["id"],
            "pay_amount": float(pay_amount),
            "remaining_debt": float(debt - pay_amount),
            "original_data": shipment["original_data"],
        })
        remaining -= pay_amount
    return allocation_plan, float(remaining)


def apply_lump_sum_payment(
    customer_ref: str,
    amount: Any,
    all_shipments: Mapping[str, dict[str, Any]],
    payment_date: str,
    note: str,
    idempotency_key: str,
    actor: str = "system",
) -> tuple[bool, list[dict[str, Any]], float, str]:
    """Ghi một khoản thu và phân bổ FIFO trong transaction MongoDB.

    idempotency_key bắt buộc để Streamlit rerun không ghi trùng khoản thu.
    """
    if not idempotency_key.strip():
        return False, [], float(to_decimal(amount)), "Thiếu idempotency_key."
    from core.database import get_db
    db = get_db()
    if db is None:
        return False, [], float(to_decimal(amount)), "MongoDB chưa sẵn sàng."

    total_debt, _, unpaid = get_customer_debt_overview(customer_ref, all_shipments)
    plan, remaining = allocate_lump_sum(amount, unpaid)
    if not plan:
        return False, [], remaining, "Không có công nợ phù hợp để phân bổ."

    client = db.client
    receipt_id = f"RCPT-{uuid4().hex.upper()}"
    try:
        with client.start_session() as session:
            with session.start_transaction():
                existing = db.payment_receipts.find_one({"idempotency_key": idempotency_key}, session=session)
                if existing:
                    return True, existing.get("allocations", []), float(existing.get("remaining", 0)), "Khoản thu đã được xử lý trước đó."

                saved_allocations: list[dict[str, Any]] = []
                for allocation in plan:
                    sid = allocation["shipment_id"]
                    ship = db.shipments.find_one({"id": sid, "is_deleted": {"$ne": True}}, session=session)
                    if not ship:
                        raise RuntimeError(f"Không tìm thấy lô {sid}.")
                    ship.pop("_id", None)
                    payment = {
                        "id": f"PAY-{uuid4().hex.upper()}",
                        "receipt_id": receipt_id,
                        "date": payment_date,
                        "amount": allocation["pay_amount"],
                        "note": note,
                        "created_at": utc_now(),
                        "created_by": actor,
                    }
                    ship.setdefault("data", {}).setdefault("3.4", {}).setdefault("payments", []).append(payment)
                    apply_financial_snapshot(ship)
                    expected_version = int(ship.get("version", 0) or 0)
                    version_filter: dict[str, Any] = {"id": sid}
                    if "version" not in ship and expected_version == 0:
                        version_filter["$or"] = [{"version": 0}, {"version": {"$exists": False}}]
                    else:
                        version_filter["version"] = expected_version
                    update_result = db.shipments.update_one(
                        version_filter,
                        {"$set": {"data": ship["data"], "updated_at": utc_now(), "updated_by": actor}, "$inc": {"version": 1}},
                        session=session,
                    )
                    if update_result.modified_count != 1:
                        raise RuntimeError(f"Lô {sid} vừa được người khác cập nhật; transaction đã hủy.")
                    saved_allocation = {"shipment_id": sid, "payment_id": payment["id"], "amount": allocation["pay_amount"]}
                    saved_allocations.append(saved_allocation)
                    db.audit_logs.insert_one({
                        "event_id": str(uuid4()),
                        "entity_type": "shipment",
                        "entity_id": sid,
                        "action": "payment_allocated",
                        "actor": actor,
                        "before": {"debt": allocation.get("pay_amount", 0) + allocation.get("remaining_debt", 0)},
                        "after": {"payment": payment, "remaining_debt": allocation.get("remaining_debt", 0)},
                        "created_at": utc_now(),
                    }, session=session)

                db.payment_receipts.insert_one({
                    "receipt_id": receipt_id,
                    "idempotency_key": idempotency_key,
                    "customer_ref": customer_ref,
                    "amount": float(to_decimal(amount)),
                    "payment_date": payment_date,
                    "note": note,
                    "allocations": saved_allocations,
                    "remaining": remaining,
                    "created_at": utc_now(),
                    "currency": "VND",
                    "created_by": actor,
                }, session=session)
                db.audit_logs.insert_one({
                    "event_id": str(uuid4()),
                    "entity_type": "payment_receipt",
                    "entity_id": receipt_id,
                    "action": "create_and_allocate",
                    "actor": actor,
                    "after": {
                        "customer_ref": customer_ref,
                        "amount": float(to_decimal(amount)),
                        "allocations": saved_allocations,
                        "remaining": remaining,
                        "currency": "VND",
                    },
                    "created_at": utc_now(),
                }, session=session)
        return True, saved_allocations, remaining, "Đã phân bổ khoản thu thành công."
    except Exception as exc:
        return False, [], float(to_decimal(amount)), str(exc)
