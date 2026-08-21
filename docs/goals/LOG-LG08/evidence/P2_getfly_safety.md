
# Phase 2: Getfly Write & Idempotency Proof

## 1. Code Analysis (Verified 2026-08-21)

- **Writer Implementation:** `views/dashboard.py` has been updated to use `save_shipment_atomic` instead of raw `update_one` for Getfly imports.
- **Idempotency Engine:** `core/excel_roundtrip.py` uses `merge_details_idempotent` which classifies service lines into `SAME`, `NEW`, `CONFLICT`, and `AMBIGUOUS`.
- **Financial Protection:** Only `NEW` lines are appended. Existing lines (which may contain `payment_status`, `paid_amount`) are preserved byte-for-byte if they match the incoming basic identity.

## 2. Deterministic Test Results

| Test Case | Status | Result |
|---|---|---|
| **NEW Shipment** | ✅ PASS | Permitted safe write via `save_shipment_atomic`. |
| **UNCHANGED Shipment** | ✅ PASS | Zero write detected (`stats["same"]` matches incoming count). |
| **CONFLICT (Identity match, value diff)** | ✅ PASS | Zero write to database; flagged for manual review. |
| **AMBIGUOUS (Multiple matches)** | ✅ PASS | Zero write to database; flagged for manual review. |
| **FINANCE Protection** | ✅ PASS | `payment_status` and `paid_amount` preserved during re-import. |
| **Idempotency** | ✅ PASS | Second import of same workbook results in `new=0` and no duplicates. |

## 3. Boundary Verification

- **Dashboard Bypass Check:** No `db.shipments.update_one` calls remain in the Getfly import path in `views/dashboard.py`.
- **Protected Fields:** `payment_status`, `paid_amount`, `bank_account`, `payment_date`, `audit_log`, `version`.

**VERDICT: GETFLY_WRITE_PATHS_CLOSED**
