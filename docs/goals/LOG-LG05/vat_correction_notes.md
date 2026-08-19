# LG05 — VAT Correction Notes

## Current Status (before fix)
- VAT correction for order #6 NOT yet applied successfully
- The `data.3.4` dot-notation `$set` is NOT working — values remain unchanged
- Only `_conflict_status` and `_conflict_resolution` were updated
- The financial fields (vat, vat_line, out, in, out_net, output_vat, debt) remain at OLD values

## Order #6 Details
- ID: `T7.2026 - LÔ ÔNG DẪN MỀM BẰNG SILICONE + KEO`
- Service line: qty=1, price=941,849,572, vat=0% → 8%
- New values needed:
  - vat: 8.0
  - vat_line: 75,347,966
  - out: 1,017,197,538
  - in: 1,017,197,538
  - out_net: 1,017,197,538
  - output_vat: 75,347,966
  - debt: 1,017,197,538

## Why update failed
- The `data.3.4` key uses a string `"3.4"` as dict key
- Dot notation `data.3.4` might be interpreted as `data["3"]["4"]` (nested) instead of `data["3.4"]`
- Need to use `replace_one` with the full document instead

## Correct approach
Use `db.shipments.replace_one({"id": sid}, doc)` after modifying the full doc object.

## Remaining phases
3. Post-correction verification (pending — need to re-run after fix)
4. Re-run GETFLY dry-run (expected: NEW=0, TRUE_NEW_SERVICE=0, CONFLICT=0, AMBIGUOUS=0)
5. Regression, commit, push, return GETFLY_IMPORT_VERIFIED_COMPLETE

## Current SHA
446226f (before VAT correction commit)
