"""DEV-only demo seed backed by an in-memory Mongo stand-in.

Activates only when no live Mongo is reachable and identity != PRODUCTION/
STAGING/PREVIEW. Demo docs use the same canonical shipment/customer/contract
shape the real readers and deterministic builders consume, so the donor UI
renders real projections over sample records. Clearly demo; never real truth.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from core.utils import utc_now

# Day anchor keeps the preview fresh regardless of run date.
_TODAY = datetime.now()
_D = lambda days: (_TODAY + timedelta(days=days)).strftime("%Y-%m-%d")

DEMO_CUSTOMERS = [
    {"id": "CUS-0001", "name": "Công ty TNHH Minh Phát Textile", "short": "Minh Phát",
     "mst": "0101234567", "contact": "Nguyễn Thị Lan", "phone": "0901234567",
     "type": "Khách hàng", "sale_owner": "owner01", "city": "Hà Nội"},
    {"id": "CUS-0002", "name": "Công ty CP An Lộc Electronics", "short": "An Lộc",
     "mst": "0107654321", "contact": "Trần Văn Đức", "phone": "0912345678",
     "type": "Khách hàng", "sale_owner": "owner01", "city": "Hải Phòng"},
]


def _ship(sid, customer_id, customer, mode, pol, pod, status, sale, support,
          container, booking, eta_days, owner_note="") -> dict:
    return {
        "id": sid,
        "shipment_id": sid,
        "customer_id": customer_id,
        "customer": customer,
        "status": status,
        "internal_sale_owner": sale,
        "support_owner": support,
        "data": {
            "0.0": {"st": status, "mode": mode, "incoterm": "CIF",
                    "pol": pol, "pod": pod},
            "1.2": {"pol": pol, "pod": pod, "booking_no": booking,
                    "carrier": "Cosco", "vessel": "EVER GIVEN", "container_no": container,
                    "etd": _D(-4), "eta": _D(eta_days)},
            "2.6": {"arrival_date": _D(eta_days), "free_time_days": 7,
                    "mode": mode},
            "2.7": {"is_delivered": status == "done",
                    "delivery_date": _D(eta_days + 1) if status == "done" else None},
            "3.4": {"details": [], "status": "waiting", "agency": {"name": "Đại lý nội địa HN"}},
            "factories": [
                {"factory": "Nhà máy " + customer.split()[-1] if customer else "Nhà máy",
                 "product": "Hàng may mặc" if "Textile" in customer else "Linh kiện điện tử",
                 "quantity": 120, "packages": 120, "weight": 1500.0, "cbm": 24.0,
                 "ready_date": _D(-2), "contact": "Anh Tài", "phone": "0900000111",
                 "required_information_complete": True, "lot": "LOT-01",
                 "pickup_contact": "Anh Tài", "pickup_address": "KCN Thăng Long, Hà Nội"},
            ],
            "documents": [
                {"name": "Commercial Invoice", "ok": True, "status": "ok"},
                {"name": "Packing List", "ok": True, "status": "ok"},
                {"name": "Bill of Lading", "ok": False, "status": "missing",
                 "note": "Chờ hãng tàu phát hành"},
            ],
        },
        "customer_required_date": _D(eta_days + 3),
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "version": 1,
        "notes": owner_note,
    }


def _build_shipments() -> dict:
    ships = [
        _ship("SHP-2026-0001", "CUS-0001", "Công ty TNHH Minh Phát Textile",
              "Export", "Hà Nội", "Hamburg", "wait", "owner01", "support01",
              "MSKU1234567", "COSU-98812", 3,
              "Chờ nhà máy đóng hàng & bổ sung Bill of Lading."),
        _ship("SHP-2026-0002", "CUS-0001", "Công ty TNHH Minh Phát Textile",
              "Import", "Thượng Hải", "Hải Phòng", "pending", "owner01", "support01",
              "MSKU7654321", "OOLU-20331", -1,
              "Lô đang thông quan; sắp hết free time — cần theo dõi."),
        _ship("SHP-2026-0003", "CUS-0002", "Công ty CP An Lộc Electronics",
              "Import", "Shenzhen", "Hà Nội", "done", "owner02", "support02",
              "MSKU0011223", "COSU-51288", -6,
              "Đã giao đủ kiện. Chờ thu nốt công nợ & xuất PXK."),
        _ship("SHP-2026-0004", "CUS-0002", "Công ty CP An Lộc Electronics",
              "Export", "Hải Phòng", "Los Angeles", "wait", "owner02", "support02",
              "MSKU4455667", "OOLU-77190", 9,
              "Đang lập phương án; cần báo giá phụ trội."),
    ]
    return {s["id"]: s for s in ships}


def _contracts(ship_ids) -> dict:
    return {
        "HDMB-2026-001": {
            "id": "HDMB-2026-001", "contract_no": "HDMB-2026-001",
            "customer_id": "CUS-0001", "customer": "Công ty TNHH Minh Phát Textile",
            "type": "HDMB", "status": "active", "value_vnd": 185_000_000.0,
            "created_at": utc_now(), "updated_at": utc_now(), "shipment_ids": ship_ids[:2],
            "sale_owner": "owner01",
        }
    }


def _users() -> dict:
    from core.users import hash_password  # noqa: PLC0415

    admin_hash = hash_password("Admin@123")
    return {
        "admin": {"id": "admin", "username": "admin", "display_name": "Quản trị viên",
                  "role": "ADMIN", "password_hash": admin_hash, "active": True},
        "sale": {"id": "sale", "username": "sale", "display_name": "Sale 01",
                 "role": "SALE", "password_hash": hash_password("Sale@123"), "active": True},
    }


def seed_dev_mongo() -> bool:
    """Install (idempotent) the in-memory stand-in and return True if seeded."""
    try:
        import mongomock  # noqa: PLC0415
    except Exception:  # noqa: BLE001
        return False

    current = _db_get_db()
    if current is not None:
        return False  # a live DB is present; do not seed

    client = mongomock.MongoClient()
    db_name = "logistics_workdesk_dev"
    db = client[db_name]
    ships = _build_shipments()
    ctr = _contracts(list(ships)[:2])

    if db.shipments.count_documents({}) == 0:
        db.shipments.insert_many(list(ships.values()))
    if db.customers.count_documents({}) == 0:
        db.customers.insert_many(list(DEMO_CUSTOMERS))
    if db.contracts.count_documents({}) == 0:
        db.contracts.insert_many(list(ctr.values()))
    if db.users.count_documents({}) == 0:
        db.users.insert_many(list(_users().values()))

    # Route the canonical DB layer to this stand-in for this process.
    import core.database as cdb

    cdb.get_db = lambda: db  # type: ignore[assignment]
    return True


def _db_get_db():
    import core.database as cdb

    return cdb.get_db()
