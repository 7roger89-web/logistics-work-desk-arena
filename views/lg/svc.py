"""Repository + DEV demo-seed bootstrap for the Logi-good donor view layer.

Data access goes through the real core readers (``core.database.load_*``) and
the real deterministic builders (``core.shipment_dashboard`` /
``core.shipment_workspace`` / ``core.shipment_360`` / ``core.financial_ledger``).

When no live Mongo is reachable and the environment is not PRODUCTION, a
DEV-only in-memory Mongo stand-in (mongomock) is seeded once so the donor UI
renders. It is clearly surfaced as demo data and never touches a real DB.
"""
from __future__ import annotations

import logging
from typing import Any

import core.database as _db

from core.shipment_dashboard import (
    build_dashboard_summary,
    build_shipment_dashboard_view,
)
from core.shipment_workspace import build_shipment_workspace_view

LOGGER = logging.getLogger("lg_v4.svc")
_DEMO_ENABLED = False


# --------------------------------------------------------------------------- data load
def _collections():
    db = _db.get_db()
    return db if db is not None else None


def shipments_db() -> dict[str, dict[str, Any]]:
    try:
        data = _db.load_data(include_archived=False, include_deleted=False)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("load_data failed")
        data = {}
    return data or {}


def dashboard_rows():
    rows = []
    for sid, doc in shipments_db().items():
        try:
            rows.append(build_shipment_dashboard_view(doc))
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("dashboard row failed for %s: %s", sid, exc)
    return rows


def build_summary() -> dict[str, int]:
    return build_dashboard_summary(dashboard_rows())


def customers() -> dict[str, dict[str, Any]]:
    try:
        return _db.load_customers() or {}
    except Exception:  # noqa: BLE001
        return {}


def contracts() -> dict[str, dict[str, Any]]:
    try:
        return _db.load_contracts() or {}
    except Exception:  # noqa: BLE001
        return {}


def agreements() -> dict[str, dict[str, Any]]:
    try:
        return _db.load_agreements() or {}
    except Exception:  # noqa: BLE001
        return {}


def quotes() -> dict[str, dict[str, Any]]:
    try:
        return _db.load_quotes() or {}
    except Exception:  # noqa: BLE001
        return {}


def users() -> dict[str, dict[str, Any]]:
    try:
        return _db.load_users() or {}
    except Exception:  # noqa: BLE001
        return {}


def workspace_view(doc: dict[str, Any]):
    return build_shipment_workspace_view(doc)


def demo_mode() -> bool:
    return _DEMO_ENABLED


def ensure_ready() -> None:
    """Bootstrap DEV demo data only when no live Mongo is available."""
    global _DEMO_ENABLED
    try:
        live = _db.get_db() is not None
    except Exception:  # noqa: BLE001
        live = False
    if live:
        return
    try:
        from core.config import ENV_IDENTITY
    except Exception:  # noqa: BLE001
        ENV_IDENTITY = "DEV"
    if str(ENV_IDENTITY).upper() in {"PRODUCTION", "STAGING", "PREVIEW"}:
        return
    from .seed import seed_dev_mongo

    seeded = seed_dev_mongo()
    _DEMO_ENABLED = bool(seeded)


def save_shipment(ship: dict[str, Any]) -> tuple[bool, str]:
    """Persist a shipment. Real Mongo -> core writer; DEV stand-in -> direct op."""
    sid = str(ship.get("id") or ship.get("shipment_id") or "")
    db = _db.get_db()
    client = getattr(db, "client", None) if db is not None else None
    if client is not None and hasattr(client, "start_session"):
        ok = _db.save_shipment_atomic(ship)
        return ok, _db.get_last_db_error() or ""
    # DEV mongomock stand-in: single-document upsert (no sessions).
    if db is None:
        return False, "MongoDB chưa sẵn sàng."
    try:
        doc = dict(ship)
        doc.pop("_id", None)
        doc.pop("version", None)
        doc["id"] = sid
        doc["shipment_id"] = sid
        from core.utils import utc_now

        doc.setdefault("created_at", utc_now())
        doc["updated_at"] = utc_now()
        existing = db.shipments.find_one({"id": sid})
        db.shipments.update_one({"id": sid}, {"$set": doc}, upsert=True)
        return True, ("" if existing else "Đã tạo mới")
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("dev save failed")
        return False, str(exc)
