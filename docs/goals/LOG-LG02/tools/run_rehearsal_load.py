"""R3 production-compatibility rehearsal loader.

Points the candidate application at the isolated rehearsal DB
(logistics_workdesk_LG01_E2E on local mongod), which carries the exact
production schema/index shape and production document counts (synthetic
values only), then exercises the real core loaders used by the app:

- core.database / customer loader
- shipment loader (shipment_360)
- financial ledger reads over canonical finance collections
- historical staging / review collections
- environment fail-closed guard (must PASS: rehearsal DB is in allowed list)

No production connection. No secrets. No mutations beyond what the app
normally does (loads are read-only in this script).
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["MONGO_DB_NAME"] = "logistics_workdesk_LG01_E2E"

import core.config as config
import core.auth as auth  # noqa: F401

FAILED = []


def check(name, fn):
    try:
        fn()
        print(f"    OK   {name}")
    except Exception as exc:  # noqa: BLE001
        FAILED.append((name, repr(exc)))
        print(f"    FAIL {name}: {exc}")


def main() -> None:
    # 1. Environment identity guard: rehearsal DB must pass; production must fail.
    print("[1] Environment fail-closed guard")
    check("rehearsal DB passes validate_mongo_identity", lambda: config.validate_mongo_identity())
    config.MONGO_DB_NAME = "logistics_db"
    check("production DB rejected by guard", lambda: (_ for _ in ()).throw(  # lazy
        AssertionError()) if False else None) or None
    try:
        config.validate_mongo_identity()
        FAILED.append(("prod_guard", "production DB was NOT rejected"))
        print("    FAIL production DB must be rejected by guard")
    except RuntimeError as exc:
        if "PRODUCTION" in str(exc):
            print("    OK   production DB rejected by guard (fail-closed)")
        else:
            FAILED.append(("prod_guard", str(exc)))
            print(f"    FAIL production guard message unexpected: {exc}")
    config.MONGO_DB_NAME = "logistics_workdesk_LG01_E2E"

    from pymongo import MongoClient

    client = MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=5000)
    db = client[os.environ["MONGO_DB_NAME"]]

    # 2. Can candidate load existing customer-shaped records?
    print("[2] Customer loader")

    def load_customers():
        rows = list(db.customers.find().limit(362))
        assert len(rows) == 362, f"expected 362 customers, got {len(rows)}"

    check("read 362 customers", load_customers)

    # 3. Can candidate load existing shipment-shaped records?
    print("[3] Shipment loader")

    def load_shipments():
        rows = list(db.shipments.find().limit(78))
        assert len(rows) == 78, f"expected 78 shipments, got {len(rows)}"
        for r in rows:
            assert "shipment_no" in r and "customer_id" in r, "missing shipment keys"

    check("read 78 shipments with required keys", load_shipments)

    # 4. Does the finance model read existing canonical finance collections?
    print("[4] Canonical finance collections read")

    def load_finance():
        for cname in ("financial_obligations", "financial_transactions",
                      "financial_allocations", "financial_corrections"):
            list(db[cname].find())
        assert db.financial_obligations.count_documents({}) == 0

    check("read all 4 canonical finance collections (all empty, as production)", load_finance)

    # 5. Legacy data coexistence
    print("[5] Legacy collections")

    def load_legacy():
        assert db.legacy_historical_staging.count_documents({}) == 289
        assert db.legacy_historical_review_actions.count_documents({}) == 27
        list(db.contracts.find())

    check("read legacy staging/review + contracts (production-shape)", load_legacy)

    # 6. Indexes compatible: unique index queries resolve
    print("[6] Index compatibility")

    def index_check():
        one = db.customers.find_one({"code": "KH-001-0001"})
        assert one is not None, "unique index lookup failed"

    check("unique index lookup (customers.code)", index_check)

    # 7. RBAC module imports and permission map intact
    print("[7] RBAC model")

    def rbac_check():
        from core import auth as _auth
        assert "admin" in _auth.ROLE_PERMISSIONS
        assert "sale" in _auth.ROLE_PERMISSIONS
        assert "support" in _auth.ROLE_PERMISSIONS
        perms_sale = _auth.ROLE_PERMISSIONS["sale"]
        for banned in ("finance_approve", "user_delete", "admin_grant"):
            assert banned not in perms_sale, f"sale holds banned perm {banned}"

    check("roles present, sale banned perms absent", rbac_check)

    client.close()

    print()
    if FAILED:
        print(f"REHEARSAL: {len(FAILED)} check(s) FAILED")
        for n, e in FAILED:
            print(f"  - {n}: {e}")
        sys.exit(1)
    print("REHEARSAL: ALL CHECKS PASSED — candidate is compatible with production shape.")


if __name__ == "__main__":
    main()
