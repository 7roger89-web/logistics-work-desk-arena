"""Notification outbox và worker gửi Telegram đáng tin cậy."""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Mapping
from uuid import uuid4

import requests
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from core.config import STATUS_MAP_INV, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN
from core.database import get_db
from core.utils import escape_html, utc_now


def enqueue_raw_notification(message: str) -> bool:
    db = get_db()
    if db is None:
        return False
    try:
        db.notification_outbox.insert_one({
            "event_id": str(uuid4()),
            "event_type": "telegram.raw",
            "payload": {"message": message},
            "status": "pending",
            "attempts": 0,
            "created_at": utc_now(),
            "next_retry_at": utc_now(),
        })
        return True
    except PyMongoError:
        return False


def notify_new_shipment(ship_obj: Mapping[str, Any]) -> bool:
    data = ship_obj.get("data", {})
    mode = data.get("0.0", {}).get("mode", "Sea")
    icon = "🚢" if mode == "Sea" else "✈️"
    message = (
        f"<b>{icon} LÔ HÀNG MỚI</b>\n"
        f"🆔 <b>{escape_html(ship_obj.get('id'))}</b>\n"
        f"👤 Khách: <b>{escape_html(ship_obj.get('customer'))}</b>\n"
        f"📅 Ngày tạo: {escape_html(data.get('0.0', {}).get('created_at'))}\n"
        f"📝 Ghi chú: {escape_html(data.get('2.7', {}).get('addr', 'Không có'))}"
    )
    return enqueue_raw_notification(message)


def notify_status_change(ship_id: str, old_st: str, new_st: str, customer: str) -> bool:
    message = (
        f"<b>🔄 CẬP NHẬT TRẠNG THÁI: {escape_html(ship_id)}</b>\n"
        f"👤 Khách: {escape_html(customer)}\n"
        f"🔻 Cũ: {escape_html(STATUS_MAP_INV.get(old_st, old_st))}\n"
        f"🔺 <b>Mới: {escape_html(STATUS_MAP_INV.get(new_st, new_st))}</b>"
    )
    return enqueue_raw_notification(message)


def notify_eta_change(ship_id: str, old_eta: Any, new_eta: Any, customer: str) -> bool:
    message = (
        f"<b>📅 THAY ĐỔI ETA: {escape_html(ship_id)}</b>\n"
        f"👤 Khách: {escape_html(customer)}\n"
        f"❌ {escape_html(old_eta)} ➔ ✅ <b>{escape_html(new_eta)}</b>"
    )
    return enqueue_raw_notification(message)


def _format_domain_event(event_type: str, payload: Mapping[str, Any]) -> str:
    sid = escape_html(payload.get("shipment_id", ""))
    customer = escape_html(payload.get("customer", ""))
    if event_type == "shipment.created":
        return f"<b>🚢 LÔ HÀNG MỚI</b>\n🆔 <b>{sid}</b>\n👤 Khách: {customer}\nMode: {escape_html(payload.get('mode', ''))}"
    if event_type == "shipment.status_changed":
        old_label = STATUS_MAP_INV.get(str(payload.get("old_status")), str(payload.get("old_status", "")))
        new_label = STATUS_MAP_INV.get(str(payload.get("new_status")), str(payload.get("new_status", "")))
        return f"<b>🔄 ĐỔI TRẠNG THÁI: {sid}</b>\n👤 Khách: {customer}\n{escape_html(old_label)} ➔ <b>{escape_html(new_label)}</b>"
    if event_type == "shipment.eta_changed":
        return f"<b>📅 ĐỔI ETA: {sid}</b>\n👤 Khách: {customer}\n{escape_html(payload.get('old_eta'))} ➔ <b>{escape_html(payload.get('new_eta'))}</b>"
    return escape_html(payload)


def process_notification_outbox(batch_size: int = 20) -> dict[str, int]:
    """Xử lý tối đa batch_size sự kiện. Có thể gọi từ cron hoặc nút quản trị."""
    stats = {"sent": 0, "failed": 0, "skipped": 0}
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        stats["skipped"] = 1
        return stats
    db = get_db()
    if db is None:
        stats["failed"] = 1
        return stats

    for _ in range(max(1, int(batch_size))):
        now = utc_now()
        stale_lock = now - timedelta(minutes=15)
        event = db.notification_outbox.find_one_and_update(
            {
                "$or": [
                    {"status": "pending", "next_retry_at": {"$lte": now}},
                    {"status": "processing", "locked_at": {"$lte": stale_lock}},
                ]
            },
            {"$set": {"status": "processing", "locked_at": now}},
            sort=[("created_at", 1)],
            return_document=ReturnDocument.AFTER,
        )
        if not event:
            break
        try:
            payload = event.get("payload", {})
            message = payload.get("message") if event.get("event_type") == "telegram.raw" else _format_domain_event(event.get("event_type", ""), payload)
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
                timeout=10,
            )
            response.raise_for_status()
            db.notification_outbox.update_one({"_id": event["_id"]}, {"$set": {"status": "sent", "sent_at": utc_now()}})
            stats["sent"] += 1
        except (requests.RequestException, PyMongoError) as exc:
            attempts = int(event.get("attempts", 0)) + 1
            status = "failed" if attempts >= 5 else "pending"
            retry_at = utc_now() + timedelta(minutes=min(60, 2 ** attempts))
            db.notification_outbox.update_one(
                {"_id": event["_id"]},
                {"$set": {"status": status, "last_error": str(exc), "next_retry_at": retry_at}, "$inc": {"attempts": 1}},
            )
            stats["failed"] += 1
    return stats
