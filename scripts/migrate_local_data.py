"""Chuyển dữ liệu JSON cũ sang MongoDB và chuẩn hóa Shipment.

Script an toàn khi chạy lại: mọi bản ghi dùng upsert theo id.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import (
    ensure_indexes,
    get_db,
    get_last_db_error,
    load_data,
    repair_data,
    save_cbpg_workspace,
    save_entrustment_book,
    save_knowledge_entry,
    save_shipment_atomic,
    normalize_contract_no,
)


def _read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def migrate() -> dict[str, int]:
    db = get_db()
    if db is None:
        raise RuntimeError(get_last_db_error() or "Không thể kết nối MongoDB.")
    ensure_indexes()
    stats = {"shipments": 0, "contracts": 0, "entrustments": 0, "knowledge_base": 0, "cbpg": 0}

    # Chuẩn hóa toàn bộ Shipment hiện hữu mà không đổi ID.
    existing = load_data(limit=100000, include_archived=True, include_deleted=True)
    for sid, shipment in repair_data(existing).items():
        if save_shipment_atomic(shipment, expected_version=shipment.get("version")):
            stats["shipments"] += 1

    # Bổ sung khóa chuẩn hóa cho hợp đồng cũ để chặn trùng do khoảng trắng/dấu gạch.
    for contract in db.contracts.find({}, {"_id": 1, "id": 1, "contract_no": 1, "ContractNo": 1}):
        contract_id = str(contract.get("id") or contract.get("contract_no") or contract.get("ContractNo") or "").strip()
        if not contract_id:
            continue
        result = db.contracts.update_one(
            {"_id": contract["_id"]},
            {"$set": {"id": contract_id.upper(), "contract_no": contract_id.upper(), "normalized_no": normalize_contract_no(contract_id)}},
        )
        if result.matched_count:
            stats["contracts"] += 1

    entrust_path = ROOT / "entrustment_database.json"
    if entrust_path.exists():
        payload = _read_json(entrust_path)
        if isinstance(payload, dict) and save_entrustment_book(payload):
            stats["entrustments"] = len(payload)

    kb_path = ROOT / "knowledge_base.json"
    if kb_path.exists():
        payload = _read_json(kb_path)
        if isinstance(payload, list):
            for item in payload:
                if not isinstance(item, dict):
                    continue
                item.setdefault("id", str(uuid4()))
                if save_knowledge_entry(item):
                    stats["knowledge_base"] += 1

    cbpg_path = ROOT / "cbpg_saved_data.json"
    if cbpg_path.exists():
        payload = _read_json(cbpg_path)
        if isinstance(payload, dict) and save_cbpg_workspace(
            str(payload.get("unit", "mm")),
            float(payload.get("invoice_total", 0)),
            list(payload.get("items", [])),
        ):
            stats["cbpg"] = 1

    return stats


if __name__ == "__main__":
    print(migrate())
