# LOGI_CONTRACT_AND_SHIPMENT_CORE_GAPS_01 — contract facts and lot-header facts become editable, persisted and read back

Closing CORE data gaps that were **displayed but not changeable** in the contract and
lot workspaces. **Not** a new page, **not** a new collection, **not** a second
contract/shipment engine, **not** an auth change: every write here goes through a
canonical writer the repository already owns, and every value is verified by a fresh
backend read rather than by the component's own local state.

## Decision gate

`CONTRACT_SHIPMENT_CORE_CLASSIFICATION = GLUE_ONLY`

| Needed fact | Already owned by (reused unchanged) | What was missing here |
| --- | --- | --- |
| "Công ty bên mua" (`company_id` → `legal_name`) | `core.database.save_contract_to_cloud`, `contract_projection` (`views/logi_c1.py:533`), vocabulary of `views/docgen.py:216/265/769` | a label and a searchable selector — it was a bare `<select>` of ids |
| counterparty (`client` / `customer_id`) | same writer; `_handle_contract_create` resolution | post-create editability + search |
| contract date (`date`) | same writer; `_normalize_date` | reachable field on the overview form |
| `pl_required` — the operator's PL decision | NEW field on the contract document, `_pl_required_decision` refuses anything but `Có PL` / `Không cần PL` / blank | — |
| GetFly extraction on the contract flow | `core.getfly_reader` column keywords + `_handle_customer_import` (canonical `save_customer_to_cloud`) | a bounded entry point on `/hop-dong/moi` |
| lot creation date (`data.0.0.created_at`) | `shipment_field_save → save_shipment_atomic`; legacy editor in `views/shipment.py`; reader already projects `createdAt` | the key was absent from `FIELD_PATHS` |
| customer half of a lot's name | `core.database.update_shipment_customer` (own `shipment_edit` gate, `customer_updated` audit, `$inc: version`) | a bounded dispatcher event that calls it |

## Rules this slice preserves

- **UNKNOWN ≠ ZERO / no invented defaults.** A blank `pl_required` stays `""` and is
  never rendered as "Không cần PL"; a blank lot date stays blank and is never today or
  an epoch; an unknown query in a picker says "no match" instead of selecting option 0;
  `customerId` travels **only** when the operator actually re-picked it, so a legacy
  contract with no `customer_id` stays saveable while an explicit unknown/blank re-pick
  is refused (`Không có khách hàng <id> trong danh bạ.` / `Chọn khách hàng trong danh bạ
  hoặc gõ đúng tên khách.`).
- **GetFly honesty.** A DSDH sheet carries `Tên KH` / `Mã KH` / order rows — nothing
  about a contract number, a buyer legal entity or an MST — so `customer_getfly_import`
  imports exactly customer identity, dedupes against the master, reports lines it
  skipped for a missing code, and fails closed with the backend's own message when the
  header is unrecognizable. `.xlsx` upload is not possible on this bridge (the transport
  carries typed JSON), hence paste, like `/khach-hang`.
- **Lot code is an identifier, not a name.** `core.database.rename_shipment_id`
  re-points proxy payments and entrustments but **not** `contracts.shipment_ids`, so no
  rename surface is exposed from the component (asserted in
  `test_rename_of_the_lot_code_is_deliberately_not_exposed`).
- **50-triệu docgen rule untouched.** `core/docgen/*.py` never learns about
  `pl_required`; a test asserts that at source level so the two notions cannot be merged
  later by accident.
- **RBAC, audit, one event per intent.** `sales_write` for contracts, `shipment_edit`
  for lots; viewer refusals are tested on every new surface; each click emits exactly one
  typed event and the page updates only when the fresh view-model arrives
  ("sent ≠ saved").
- **`/nguoi-dung` was not re-implemented.** The admin user-management UI exists
  (`views/user_management.py`, `UserAccess.tsx`, shipped bundle) and is hidden by
  `views/user_access.py::_can_manage` unless `role == "admin"` (local mode injects
  `local-admin`). Reported "missing button" = role/deploy condition, proven by
  `dom_acceptance_user_management.mjs` + `dom_acceptance_user_access.mjs`.

## Verification

```
.venv/bin/python -m pytest tests/test_logi_contract_core_gaps_01.py \
                          tests/test_logi_shipment_core_gaps_01.py -q   # 48 passed
.venv/bin/python scripts/gen_contract_shipment_edit_fixture.py         # real staging writes
node tests/component/dom_acceptance_contract_core_edit.mjs             # 8 checks
node tests/component/dom_acceptance_shipment_header_edit.mjs           # 7 checks
cd component && npx tsc --noEmit && npm run build                      # 890.62 kB
python3 scripts/scan_process.py component/dist                         # FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0
```

Full suite `pytest tests -q --continue-on-collection-errors` → `13 failed, 902 passed,
38 skipped, 8 errors` — the failure set is **identical to main `4c798e9`** (all
pre-existing and unrelated: `test_deepl_route_rbac.py` / `test_partner_reconciliation_desk_write_oracle.py`
collection import errors, `test_lg05_excel_roundtrip_gnt.py`, `test_all_tabs_smoke.py`,
dashboard/financial oracle tests, `test_logc15_auth_rbac.py::test_unknown_role_falls_back_to_viewer`, …).

Known pre-existing DOM-harness drift, **not** caused by this slice (reproduced against a
worktree built from main's own source): `dom_acceptance_create_shipment.mjs` still asserts
the label `ĐANG CHỜ BACKEND XÁC NHẬN…` while `CreateShipment.tsx` (untouched here) renders
`ĐANG TẠO LÔ…`. `dom_acceptance_user_access.mjs` flakes when run back-to-back in a loop and
passes standalone.
