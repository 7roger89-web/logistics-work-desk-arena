"""Soft-archive Shipment đã hoàn thành và hết nợ.

Chạy:
    python scripts/archiver.py

Script không di chuyển/xóa document khỏi collection shipments, vì báo cáo lịch sử
vẫn cần dữ liệu. Nó chỉ đánh dấu is_archived=True và ghi audit log.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import get_db, get_last_db_error, repair_data
from core.logic import calculate_from_shipment
from core.utils import to_decimal, utc_now


def run_archive_process(debt_tolerance: int = 1000) -> dict[str, object]:
    db = get_db()
    if db is None:
        raise RuntimeError(get_last_db_error() or "Không thể kết nối MongoDB.")

    candidates = list(db.shipments.find({
        "status": {"$in": ["done", "Done", "Hoàn thành"]},
        "is_deleted": {"$ne": True},
        "is_archived": {"$ne": True},
    }, {"_id": 0}))

    archived_ids: list[str] = []
    skipped_ids: list[str] = []
    for raw in candidates:
        sid = str(raw.get("id", ""))
        if not sid:
            continue
        shipment = repair_data({sid: raw})[sid]
        summary = calculate_from_shipment(shipment)
        if abs(to_decimal(summary["debt"])) > to_decimal(debt_tolerance):
            skipped_ids.append(sid)
            continue

        result = db.shipments.update_one(
            {"id": sid, "is_archived": {"$ne": True}},
            {"$set": {"is_archived": True, "archived_at": utc_now(), "archived_by": "archiver"}, "$inc": {"version": 1}},
        )
        if result.modified_count:
            db.audit_logs.insert_one({
                "entity_type": "shipment",
                "entity_id": sid,
                "action": "archive",
                "actor": "archiver",
                "created_at": utc_now(),
                "after": {"is_archived": True, "debt": summary["debt"]},
            })
            archived_ids.append(sid)

    return {"archived": len(archived_ids), "archived_ids": archived_ids, "skipped_ids": skipped_ids}


if __name__ == "__main__":
    result = run_archive_process()
    print(f"Archived: {result['archived']}")
    if result["archived_ids"]:
        print("IDs:", ", ".join(result["archived_ids"]))
    if result["skipped_ids"]:
        print("Skipped because debt remains:", ", ".join(result["skipped_ids"]))
