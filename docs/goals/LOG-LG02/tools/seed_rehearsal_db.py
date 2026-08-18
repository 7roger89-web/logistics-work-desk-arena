"""Rehearsal environment builder for LOG-LG02 (R3).

Builds an ISOLATED rehearsal DB with production SHAPE (schema + index
structure reconstructed from the read-only production inventory R1) and
non-sensitive/synthetic-but-quantity-accurate data:

- document counts match production counts exactly (so load tests reflect
  real cardinality),
- field names and types match the production schema samples,
- all values are synthetic (no production record values are copied),
- no secrets are present anywhere.

Usage (from the repo root, local mongod required):
    python3 docs/goals/LOG-LG02/tools/seed_rehearsal_db.py

Target: logistics_workdesk_LG01_E2E on mongodb://localhost:27017
(cannot be production: DB name not authorized as release DB and URI is local).
"""
import json
import os
import random
import uuid
from datetime import date, timedelta

from pymongo import MongoClient

LOCAL_URI = "mongodb://localhost:27017"
REHEARSAL_DB = "logistics_workdesk_LG01_E2E"

# Production shape reconstructed from R1 inventory (logistics_db on Cluster0).
# Each entry: (collection, prod_count, sample key shape, list of indexes to create)
PROD_SHAPE = [
    ("audit_logs", 54, {
        "actor": "system", "action": "login", "entity_type": "user", "entity_id": "u-1",
        "details": {"ok": True}, "created_at": "2026-01-01T00:00:00Z"},
        [{"keys": [("created_at", 1)], "name": "idx_created_at"}]),
    ("contract_transactions", 0, {"contract_id": "CO-1", "amount": 100.0, "currency": "USD",
                                  "type": "invoice", "created_at": "2026-01-01T00:00:00Z"},
        []),
    ("contracts", 6, {"contract_no": "HD-001", "customer_id": "C-1", "status": "AGREED",
                       "currency": "USD", "amount": 1000.0, "terms": {"note": "synthetic"}},
        [{"keys": [("customer_id", 1)], "name": "idx_customer"}]),
    ("customers", 362, {"name": "Customer", "code": "KH-001", "type": "retail",
                        "phone": "0900000001", "city": "Ho Chi Minh"},
        [{"keys": [("code", 1)], "name": "idx_code", "unique": True}]),
    ("entrustments", 0, {"customer_id": "C-1", "status": "pending"}, []),
    ("financial_action_requests", 0, {"request_id": "FR-1", "type": "payment",
                                      "status": "open"}, []),
    ("financial_allocations", 0, {"obligation_id": "OB-1", "amount": 50.0,
                                  "currency": "USD", "transaction_id": "TX-1"}, []),
    ("financial_corrections", 0, {"obligation_id": "OB-1", "delta": -10.0,
                                  "reason": "adjustment"}, []),
    ("financial_obligations", 0, {"id": "OB-1", "from_party": {"party_type": "customer",
        "party_id": "C-1", "name": "Customer"}, "to_party": {"party_type": "partner",
        "party_id": "P-1", "name": "Partner"}, "amount": 500.0, "currency": "USD",
        "due_date": "2026-09-01", "shipment_ids": ["SH-1"],
        "classification_status": "UNALLOCATED"}, []),
    ("financial_transactions", 0, {"id": "TX-1", "amount": 500.0, "currency": "USD",
                                   "direction": "in", "evidence_refs": []}, []),
    ("knowledge_base", 0, {"topic": "note", "body": "synthetic note"}, []),
    ("legacy_historical_review_actions", 27, {"item_id": "HS-1", "action": "review",
        "status": "done", "created_at": "2025-12-01T00:00:00Z"},
        [{"keys": [("item_id", 1)], "name": "idx_item"}]),
    ("legacy_historical_staging", 289, {"batch_id": "B-1", "stage": "imported",
        "row": {"col_a": "x"}}, [{"keys": [("batch_id", 1)], "name": "idx_batch"}]),
    ("notification_outbox", 0, {"target": "user", "message": "note", "sent": False}, []),
    ("payment_receipts", 0, {"reference": "PR-1", "amount": 100.0, "currency": "USD"}, []),
    ("proxy_payments", 2, {"proxy_id": "PP-1", "customer_id": "C-1",
        "amount": 200.0, "currency": "VND", "status": "processed"}, []),
    ("quick_notes", 1, {"note": "synthetic quick note", "created_at": "2026-07-01T00:00:00Z"}, []),
    ("rate_cards", 0, {"route": "HCM-SGN", "price": 100.0, "currency": "USD"}, []),
    ("shipments", 78, {"shipment_no": "SH-001", "customer_id": "C-1",
        "status": "in_transit", "origin": "Ho Chi Minh", "destination": "Ha Noi",
        "created_at": "2026-05-01T00:00:00Z"}, [
        {"keys": [("shipment_no", 1)], "name": "idx_no", "unique": True},
        {"keys": [("customer_id", 1)], "name": "idx_customer"}]),
    ("tasks", 0, {"title": "task", "status": "open", "assignee": "anon"}, []),
]

random.seed(20260818)

def main() -> None:
    client = MongoClient(LOCAL_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[REHEARSAL_DB]
    # Drop any previous rehearsal remnants to keep rehearsal deterministic.
    for name in db.list_collection_names():
        db[name].drop()

    created = 0
    for cname, count, sample, indexes in PROD_SHAPE:
        coll = db[cname]
        for i in range(1, count + 1):
            doc = dict(sample)
            doc["_id"] = f"{cname[:-1] if cname.endswith('s') and cname not in ('proxy_payments', 'financial_transactions') else cname}-{i:04d}"
            # Per-document variation so unique indexes can be built and queries
            # exercise realistic cardinality; all values remain synthetic.
            for key in ("code", "shipment_no", "contract_no", "proxy_id", "note"):
                if key in doc:
                    doc[key] = f"{doc[key]}-{i:04d}"
            for key in ("phone",):
                if key in doc:
                    doc[key] = f"09{i:08d}"
            for key in ("amount",):
                if key in doc:
                    doc[key] = round(doc[key] * (1 + 0.01 * i), 2)
            created += 1
            coll.insert_one(doc)
        for idx in indexes:
            coll.create_index(idx["keys"], name=idx["name"], unique=idx.get("unique", False))

    # Verify counts vs production
    ok = True
    print(f"Rehearsal DB {REHEARSAL_DB} seeded with {created} synthetic documents (shape = production logistics_db).")
    for cname, count, _sample, _idx in PROD_SHAPE:
        n = db[cname].count_documents({})
        flag = "OK" if n == count else "MISMATCH"
        if n != count:
            ok = False
        print(f"    {flag} {cname}: {n}/{count}")
    client.close()
    if not ok:
        raise SystemExit("Rehearsal counts do not match production inventory.")
    print("OK: rehearsal environment ready; indexes restored.")


if __name__ == "__main__":
    main()
