
# Phase 5: GNT End-to-End Contract Proof

## 1. End-to-End Flow (Verified 2026-08-21)

The GNT generation flow has been unified and secured:
1. **UI Layer (`views/shipment.py`):** Captures user input via `st.data_editor` and performs mandatory validation.
2. **Adapter Layer:** Maps UI state to the `gnt_data` dictionary contract.
3. **Builder Layer (`core/gnt_builder.py`):** Generates the Excel workbook using `openpyxl`.

## 2. Contract Verification

| Requirement | Proof | Status |
|---|---|---|
| **Mandatory Validation** | UI throws error if `taxpayer`, `tax_code`, or `declaration_number` is missing. | ✅ PASS |
| **No Guessing** | Declaration date defaults to empty if not provided; no auto-filling with "today". | ✅ PASS |
| **Fail-closed** | Download button is only rendered if all validations pass. | ✅ PASS |
| **Field Mapping** | `declaration_number`, `declaration_date`, `import_duty`, `import_vat` correctly mapped to XLSX. | ✅ PASS |

## 3. Integrated Test Result

- `tests/test_lg08_1_gnt_contract.py` passed all 3 tests, verifying the builder's stability and the UI's validation logic.

**VERDICT: GNT_CONTRACT_VERIFIED**
