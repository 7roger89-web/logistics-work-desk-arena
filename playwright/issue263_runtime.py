"""Issue #263 QA runtime — the REAL app on isolated staging data.

This is a browser-QA launcher, not application code. It seeds the existing
``mongomock`` staging transport with two isolated customers/lots and runs the
UNCHANGED ``app.py`` for the internal shell. The customer view uses the same
process/database and the same ``views.customer_dashboard.render_customer_dashboard``
path with a staging-granted verified email (the OIDC provider is NOT exercised).

Nothing here proves authentication: Google OIDC / Cloud stay NOT_VERIFIED.

URLs:
  /                     → internal app (password login, real RBAC)
  /?as=khach-a          → customer A portal (its own allowlisted email)
  /?as=khach-b          → customer B portal

Run:
  AUTH_REQUIRED=true ISSUE263_TEST_PASSWORD=... \
  streamlit run playwright/issue263_runtime.py --server.port 9513
"""
from __future__ import annotations

import copy
import json
import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PASSWORD = os.environ["ISSUE263_TEST_PASSWORD"]
assert len(PASSWORD) >= 8
assert not os.environ.get("MONGO_URI"), "Issue #263 QA runtime refuses a real Mongo URI"
assert os.environ.get("AUTH_REQUIRED", "").lower() == "true"

import streamlit as st

from core import config, database
from core import customer_portal as portal
from core.users import build_user_document
from views import logi_sandbox

assert config.AUTH_REQUIRED is True
assert config.MONGO_URI in ("", logi_sandbox.STAGING_URI_PLACEHOLDER)
assert logi_sandbox.ensure_backend() == logi_sandbox.SANDBOX_TRANSPORT
DB = database.get_db()
assert DB.name == "logistics_staging"
assert type(DB.client).__module__.startswith("mongomock")

LOT_A, LOT_B = "LO-263-A", "LO-263-B"
CUST_A, CUST_B = "CUST-263-A", "CUST-263-B"
EMAIL_A, EMAIL_B = "khach-a-263@example.test", "khach-b-263@example.test"
INTERNAL_SECRET = "SECRET_263_INTERNAL_MARGIN"
FINANCE_SECRET = 987654321
EVIDENCE_DIR = Path(os.environ["ISSUE263_EVIDENCE_DIR"]).resolve()
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def _write(name: str, payload: object) -> None:
    tmp = EVIDENCE_DIR / (name + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, default=str, indent=2) + "\n",
                   encoding="utf-8")
    tmp.replace(EVIDENCE_DIR / name)


def _seed() -> None:
    for username, role in (("qa.263.support", "support"), ("qa.263.admin", "admin")):
        if DB.users.find_one({"username": username}) is None:
            DB.users.insert_one(build_user_document(
                username, PASSWORD, f"G15 {role}", role, created_by="issue263.fixture",
            ))
    DB.customers.replace_one(
        {"id": CUST_A},
        {"id": CUST_A, "name": "An Phát JSC (G15-A)", "portal_access_email": EMAIL_A,
         "is_deleted": False},
        upsert=True,
    )
    DB.customers.replace_one(
        {"id": CUST_B},
        {"id": CUST_B, "name": "Khách B (G15-B)", "portal_access_email": EMAIL_B,
         "is_deleted": False},
        upsert=True,
    )
    base = copy.deepcopy(DB.shipments.find_one({"id": "LO-0306"}, {"_id": 0}))
    assert base is not None
    for lot, cust, name in ((LOT_A, CUST_A, "An Phát JSC (G15-A)"),
                            (LOT_B, CUST_B, "Khách B (G15-B)")):
        doc = copy.deepcopy(base)
        doc.update({
            "id": lot, "shipment_id": lot, "customer_id": cust, "customer": name,
            "client": name, "internal_notes": INTERNAL_SECRET, "version": 0,
            "is_deleted": False, "is_archived": False,
        })
        doc.pop("customer_publication_version", None)
        doc["data"]["1.2"] = {
            "transport_legs": [{
                "id": f"leg-pickup-{lot}", "sequence": 1, "mode": "Truck",
                "origin": "Nam Ninh", "destination": "Hữu Nghị",
                "carrier": "CN Road Partner", "etd": "2026-11-01", "eta": "2026-11-02",
                "atd": "", "ata": "",
                "units": [{
                    "id": f"truck-{lot}", "kind": "truck", "number": "桂A-26399",
                    "type_size": "Container 40", "driver_name": INTERNAL_SECRET,
                    "driver_phone": "0900263999",
                }],
            }],
        }
        doc["data"]["3.4"] = {
            "details": [{"id": f"ACT-{lot}", "name": "Cước nội bộ",
                         "qty": 1, "price": FINANCE_SECRET, "cost": 700000000}],
            "payments": [], "commission": {"list": [], "total": 0, "note": INTERNAL_SECRET},
        }
        DB.shipments.replace_one({"id": lot}, doc, upsert=True)
        # A clean slate for THIS process: the QA run must not start from a
        # fixture-made public source.
        DB.public_events.delete_many({"shipment_id": lot})
        DB.public_documents.delete_many({"shipment_id": lot})
    _write("seed-truth.json", {
        "lots": {LOT_A: CUST_A, LOT_B: CUST_B},
        "public_events_at_start": DB.public_events.count_documents({"shipment_id": LOT_A}),
        "pickup_leg_atd_at_start": [
            (row.get("data") or {}).get("1.2", {}).get("transport_legs", [{}])[0].get("atd", "")
            for row in DB.shipments.find({"id": {"$in": [LOT_A, LOT_B]}}, {"_id": 0, "data": 1})
        ],
    })


def _seed_once() -> None:
    """Seed exactly ONCE per process.

    Streamlit re-runs this whole script on every interaction; re-seeding would
    delete the source that the staff action under test just produced.
    """
    marker = DB["qa263_runtime_marker"]
    if marker.find_one({"id": "seeded"}) is not None:
        return
    _seed()
    marker.insert_one({"id": "seeded"})


_seed_once()

def _dump_state() -> dict:
    """Authoritative DB snapshot (QA-only) for the browser runner."""
    return {
        "public_events": [
            {k: row.get(k) for k in ("id", "version", "customer_id", "shipment_id",
                                     "stage_id", "occurred_at", "public_title", "verified",
                                     "verified_at", "verified_by", "state", "recorded_by")}
            for row in DB.public_events.find({}, {"_id": 0})
        ],
        "publications": [
            {k: row.get(k) for k in ("version", "customer_id", "shipment_id", "state",
                                     "approved_by", "event_versions")}
            for row in DB.customer_publications.find({}, {"_id": 0})
        ],
        "shipments": [
            {"id": row.get("id"), "customer_id": row.get("customer_id"),
             "published": row.get("customer_publication_version", ""),
             "pickup_atd": (((row.get("data") or {}).get("1.2") or {}).get("transport_legs") or [{}])[0].get("atd", "")}
            for row in DB.shipments.find({"id": {"$in": [LOT_A, LOT_B]}}, {"_id": 0})
        ],
    }


def _reset_milestone_state() -> None:
    """QA-only: return both lots to "no milestone yet" between viewport runs."""
    DB.public_events.delete_many({"shipment_id": {"$in": [LOT_A, LOT_B]}})
    DB.public_documents.delete_many({"shipment_id": {"$in": [LOT_A, LOT_B]}})
    DB.customer_publications.delete_many({"shipment_id": {"$in": [LOT_A, LOT_B]}})
    for lot in (LOT_A, LOT_B):
        row = DB.shipments.find_one({"id": lot})
        if not row:
            continue
        data = copy.deepcopy(row.get("data") or {})
        legs = ((data.get("1.2") or {}).get("transport_legs") or [])
        for leg in legs:
            if isinstance(leg, dict):
                leg["atd"] = ""
        DB.shipments.update_one(
            {"id": lot},
            {"$set": {"data": data}, "$unset": {"customer_publication_version": ""}},
        )


customer_mode = str(st.query_params.get("as") or "").strip().lower()
if customer_mode == "reset":
    st.set_page_config(page_title="QA reset", layout="wide")
    _reset_milestone_state()
    state = _dump_state()
    _write("state-readback.json", state)
    st.json(state)
elif customer_mode == "state":
    st.set_page_config(page_title="QA state", layout="wide")
    state = _dump_state()
    _write("state-readback.json", state)
    st.json(state)
elif customer_mode in {"khach-a", "khach-b"}:
    from views import customer_dashboard

    st.set_page_config(page_title="Cổng khách hàng · QA", layout="wide")
    st.caption(
        "QA cô lập: danh tính khách được cấp trong TEST, dữ liệu mongomock. "
        "Không chứng minh Google OIDC."
    )
    email = EMAIL_A if customer_mode == "khach-a" else EMAIL_B
    principal = portal.build_customer_principal(verified_email=email, db=DB)
    view = portal.load_customer_dashboard(principal, db=DB)
    _write(f"customer-readback-{customer_mode}.json", {
        "email": email,
        "customer_id": principal.customer_id,
        "cards": [
            {"reference": card.reference, "version": card.publication_version,
             "timeline": [dict(e) for e in card.timeline]}
            for card in view.cards
        ],
        "denied_lots": view.denied_lots, "data_issues": view.data_issues,
    })
    customer_dashboard.render_customer_dashboard(principal, db=DB)
else:
    # QA-only observer: record every dispatcher outcome so a browser step can be
    # traced to the exact backend answer instead of trusting an optimistic toast.
    from views import logi_view_model as _vm

    if not hasattr(_vm, "_issue263_observed_dispatch"):
        _original_dispatch = _vm.dispatch

        def _observed_dispatch(result, **kwargs):
            outcomes = _original_dispatch(result, **kwargs)
            try:
                _write("dispatch-log.json", {
                    "at": str(__import__("datetime").datetime.now()),
                    "events": list(result.keys()) if isinstance(result, dict) else str(type(result)),
                    "raw": json.loads(json.dumps(result, default=str)) if result else None,
                    "outcomes": [
                        {k: o.get(k) for k in ("event", "shipmentId", "ok", "error",
                                               "pendingSource", "sourceError")}
                        for o in (outcomes or [])
                    ],
                })
            except Exception as exc:  # noqa: BLE001 - never break the app for a log
                print(f"ISSUE263 dispatch log failed: {exc}", file=sys.stderr)
            return outcomes

        _vm.dispatch = _observed_dispatch
        _vm._issue263_observed_dispatch = _observed_dispatch

    _write("internal-readback.json", {
        "public_events": [
            {k: row.get(k) for k in ("id", "version", "customer_id", "shipment_id",
                                     "stage_id", "occurred_at", "verified", "verified_at",
                                     "verified_by", "state")}
            for row in DB.public_events.find({}, {"_id": 0})
        ],
        "shipments": [
            {"id": row["id"], "published": row.get("customer_publication_version", "")}
            for row in DB.shipments.find({"id": {"$in": [LOT_A, LOT_B]}}, {"_id": 0, "id": 1})
        ],
    })
    runpy.run_path(str(ROOT / "app.py"), run_name="__main__")
