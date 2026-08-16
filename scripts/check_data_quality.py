"""Kiểm tra dữ liệu trước khi bật unique indexes và migration."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import get_db, get_last_db_error
from core.validators import validate_shipment


def duplicate_ids(collection):
    return list(collection.aggregate([
        {"$group": {"_id": "$id", "count": {"$sum": 1}}},
        {"$match": {"_id": {"$nin": [None, ""]}, "count": {"$gt": 1}}},
        {"$sort": {"count": -1}},
    ]))


def run():
    db = get_db()
    if db is None:
        raise RuntimeError(get_last_db_error() or "Không thể kết nối MongoDB.")
    result = {"duplicates": {}, "invalid_shipments": []}
    for name in ("shipments", "customers", "contracts", "proxy_payments", "rate_cards"):
        result["duplicates"][name] = duplicate_ids(db[name])
    result["duplicates"]["contracts_normalized"] = list(db.contracts.aggregate([
        {"$match": {"normalized_no": {"$type": "string", "$ne": ""}}},
        {"$group": {"_id": "$normalized_no", "count": {"$sum": 1}, "ids": {"$push": "$id"}}},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}},
    ]))
    for shipment in db.shipments.find({"is_deleted": {"$ne": True}}, {"_id": 0}):
        validation = validate_shipment(shipment)
        if not validation.is_valid or validation.warnings:
            result["invalid_shipments"].append({
                "id": shipment.get("id"),
                "errors": [issue.message for issue in validation.errors],
                "warnings": [issue.message for issue in validation.warnings],
            })
    return result


if __name__ == "__main__":
    from pprint import pprint
    pprint(run(), sort_dicts=False)
