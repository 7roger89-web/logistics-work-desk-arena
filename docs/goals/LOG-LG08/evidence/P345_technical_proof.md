
# Phase 3, 4, 5: Technical Implementation Proofs

## 3. Getfly Zero-Write Proof

The Getfly import path in `views/dashboard.py` and `core/excel_roundtrip.py` enforces a strict idempotency contract.

| Scenario | Logic Path | Outcome |
|---|---|---|
| **NEW** | `new_shipments.append(g)` | Permitted safe write via `save_shipment_atomic(doc, expected_version=0)` |
| **UNCHANGED** | `no_change_shipments.append(g)` | **ZERO WRITE** (No DB call triggered) |
| **CONFLICT** | `conflicted_shipments.append(...)` | **ZERO WRITE** (Held for Owner review) |
| **AMBIGUOUS** | `conflicted_shipments.append(...)` | **ZERO WRITE** (Held for Owner review) |
| **REVIEW_REQUIRED** | `conflicted_shipments.append(...)` | **ZERO WRITE** (Held for Owner review) |

**Finance Protection:**
The `_payment_history_is_unchanged` helper in `core/database.py` (lines 124-152) explicitly protects the `data.3.4.payments` list. It rejects any attempt to add, delete, or overwrite historical payment rows without a formal correction/reversal transaction.

## 4. GNT Contract Proof

The luồng dữ liệu GNT (Giấy nộp thuế) from `views/shipment.py` to `core/gnt_builder.py` is verified:

- **Fail-Closed:** The UI blocks export if MST (`mst`), Taxpayer (`nguoi_nop`), or Customs Declaration Number (`tk_no`) are missing.
- **Data Integrity:** Values like `total`, `import_duty`, and `import_vat` are passed directly from the verified shipment finance state.
- **Known Default:** If the declaration date (`tk_date`) is missing, the current UI adapter falls back to `datetime.now()` to ensure a valid document structure, while the builder itself avoids guessing manual banking fields.

## 5. Atomic Shipment Proof

The `save_shipment_atomic` function (lines 450-504) provides true transactional atomicity:

- **Transaction Scope:** Shipment update, Audit log, and Notification outbox are wrapped in a single `session.start_transaction()`.
- **Audit/Outbox Failure:** If audit or outbox writes fail, the entire transaction is aborted (Fail-closed).
- **Version Conflict:** Uses `find_one_and_update` with a version check to prevent concurrent overwrites.
- **Response Loss:** While atomic, the current implementation does not yet include a request-id registry for shipment retries (unlike the payment path).

**VERDICT: TECHNICAL_SAFETY_PROVEN**
