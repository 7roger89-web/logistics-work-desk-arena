# LOGI_EXCEL_QUOTE_IMPORT_V1 — implementation & evidence

## Contract / preflight (2026-10-16)
- Repository `7roger89-web/logistics-work-desk-arena`; branch `arena/63b3ec32-logistics-work-desk-arena`; baseline/main `5c6642a339ec53fe4cc300b15f665e2cd5384bca`; initially clean.
- Actor read AGENTS.md, portable notebook (body SHA256 verified against header: `11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`), skill and ACTIVE experience. `P2P_LAW_SOURCE=LOCAL_PORTABLE`, `LAW_CHECK=PASS`. Prompt's malformed hash is not authority.
- `p2p-skill-consumption-receipt/1`: selected set `[p2p-uiux]`; `.agents/skills/p2p-uiux/SKILL.md`; SHA256 `98f26873e48cc87e34d132478f73672a80d20b3a8e1a2256bdcdab4d6107e7b2`; matches current portable manifest; read/applied; `SKILL_CONSUMPTION=PASS`.
- `EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE`, `shared-exp-b2611df4c9393f0017f07dcb`: own receipt, bounded verification, honest reconciliation. No installed law runtime or native Arena `/goal` execution capability; normal execution path, no substitute control plane.
- Goal #199 and all open PR file lists checked. #204 overlaps SalesQuotes/viewmodel/bundle, #198/#203 overlap Python viewmodel. Do not overwrite/cherry-pick those branches or modify Journey. Main merge triggers production: **no merge, no deploy, no production DB access**.

## Bounded design contract
`INITIAL_PLANNING_CLASSIFICATION=UIUX`; `FINAL_ROUTING_CLASSIFICATION=UIUX`, secondary quotation truth/persistence.
Product: existing Streamlit Components v2 + React logistics work desk. User: Sale receiving a furniture workbook. Need: inspect source, select reference costs without treating them as selling prices, save an incomplete draft, disclose only approved customer information.

USER NEED → transparent review → three steps within existing Báo Giá route → reuse existing UI primitives, customer master, Cost Intelligence matcher, typed C1 dispatcher, quote writer and openpyxl exporter. No new route/server/database/framework/price engine/design system. Keep quick-text quoting available.

Reference URL fetched successfully as text: https://01a13f14-6767-7e2c-9ee3-9043533ca20d.arena.site/ (title Fable–Sonnet V2.1). Text is a UI/behavior reference, not calculation authority. Runtime comparison is a separate evidence gate. Optional specialist profile not available (`PROFILE_UNAVAILABLE`); skill-only fallback.

Use existing navy/blue/slate tokens and Be Vietnam Pro stack; scoped workspace styling only. Three numbered steps, internal-vs-customer distinction, warnings not color-only, editable source rows, labeled inputs, keyboard focus, 44px actions, dense desktop table / stacked mobile cards. Source declarations stay stored when deselected. No localStorage authority.

OE_GATE: **Không bị over engineering chứ?**
- SIMPLER_PATH=YES: extend the existing quote document/dispatcher/exporter and GridFS adapter.
- MATERIAL_PROGRESS=YES: one Excel → reference cost → customer quote → save → export slice.
- NECESSITY=YES: nullable selling prices, source provenance and sent snapshots protect explicit acceptance locks.
- CORE_BEFORE_SUPPORT=YES: implementation and focused tests before supporting artifacts.
- SMALLER_VERIFIABLE_SLICE=YES: Lục Giác table layout only, no universal workbook mapper.
`OE_VERDICT=DO_IT`: use this bounded path; defer unrelated Journey, design-system and dependency upgrades.

## Acceptance boundaries
- Synthetic three-sheet fixture only, generated from the Owner's prompt. **Not the original Lục Giác workbook**.
- Decimal arithmetic stays in `core/quotations.py`; browser renders correlated server previews, never maintains a second quote calculator.
- Keep UNKNOWN distinct from zero, goods and fee currencies separate, customs basis independent of selling prices, A/B lines separate, expiry/conditional warnings visible, calendar dates strict.
- Existing Mongo quote collection stores business state; existing GridFS adapter stores original XLSX bytes + metadata. No customer bytes in Git. Preview/Staging uses existing in-memory mongomock transport: refresh readback is not proof of production durability.
- Customer output uses an allowlist; sent customer snapshots remain immutable while the current quote returns to DRAFT for revision.

## Implemented slice

| Surface | Actual files / behavior |
|---|---|
| Existing Báo Giá route | `component/src/pages/SalesQuotes.tsx`: additive Excel entry and imported-quote editing; quick-paste quoting kept. No standalone demo or new route. |
| Three-step form | `component/src/components/ExcelQuoteWorkspace.tsx`, scoped `excelQuote.css`, `lib/excelQuote.ts`: existing customer picker → upload/review/apply → internal costing → customer disclosure/preview/save/export. Responsive goods cards, labeled fields and visible source warnings. |
| Same component channel | `component/src/lib/dispatcher.ts`, `lib/viewmodel.ts`, `views/logi_c1.py`: typed import/preview/source-download events through the existing Streamlit v2 dispatcher; request-correlated server calculations/readback. No JS arithmetic engine or localStorage authority. |
| Bounded Python import | `core/quote_excel_import.py`: openpyxl Lục Giác layout reader; 5 MB input / 25 MB expanded / 300 ZIP entries / 8 sheets / 2500 rows / 40 columns / 200 goods. Macros/unsupported paths/formats refused; formulas never executed. Source bytes and metadata use existing `GridFSAttachmentStore`, customer ownership and SHA256 readback. |
| Canonical quotation truth | `core/quotations.py`, `views/logi_quote_import.py`: nullable Excel DRAFT selling, explicit Sale confirmation, independent A/B, EXW/FOB/CIF/DAP, SEA FCL/LCL/AIR/ROAD, route/ports/delivery/equipment, Decimal calculations, strict dates, independent customs basis, immutable sent customer snapshots. Missing FX remains UNKNOWN. Direct and cross FX cannot silently overwrite one another. |
| Existing cost repository | `component/src/lib/costHistory.ts`: reference IDs, validity and conditional notes carried from existing matcher. Backend rehydrates selected `rate_cards` amount/unit/currency/expiry; these are reference cost only, never selling. Unselected fees and option B are not auto-populated. |
| Existing persistence | `core/database.py`: optional expected-version CAS on the existing quote writer; stale edits refused. Create validates a fresh customer rather than the 30-second render cache; a writer acknowledgment without fresh quote readback is not a saved-success result. No second database or API service. |
| Customer XLSX | `core/excel_utils.py`: existing exporter uses the public allowlist: reviewed goods, selected scope/option/route, confirmed selling, independently justified tax estimate, selected disclosures and multiline public notes. No cost/profit/internal source/notes/Sale audit. Formula-looking text is literal. Historical sent exports use the immutable snapshot. |
| Build / regression | Tracked `component/dist/logi-shell.js/css`; synthetic generator; new Python/browser tests; screenshots and logs under `evidence/excel-quote-import-v1/`. No original/customer workbook or downloaded XLSX committed. |

Read-only selected-rate cost/unit/currency are visually distinct from editable selling fields. Border styling is explicit **only in this workspace** to survive the existing Components-v2 shadow root. The footer is in normal flow rather than clipping actions under the nested shell scrollport. Shared `Layout`, `shell.css`, `index.css`, `core/auth.py` and Journey are unchanged.

## Verification results — 2026-10-16

**Verdict: PROVEN for the bounded sandbox vertical slice; INCOMPLETE for production release / exact donor visual certification. Draft review only. No main merge, deployment, email sending, production database access or ledger posting.**

| Gate | Result | Scope / recoverable evidence |
|---|---|---|
| Source | **PASS** | Repository/base/branch verified; additive existing-authority integration reviewed; `git diff --check` and Python compilation pass; product hashes in [verified-source-sha256.json](../evidence/excel-quote-import-v1/verified-source-sha256.json). This is a bounded source review, not an independent human approval. |
| Unit / focused regression | **PASS (separate batches)** | **102** quotation/import/C1/export regressions = 31 new + 71 existing; **61** further quotation/cost/RBAC tests in another process. New fixture + RBAC isolation: **59** pass (overlapping, not added to total). Cost matcher, 20 quick-parser/calculator checks and 7 legacy line-note DOM checks pass. [Logs](../evidence/excel-quote-import-v1/README.md). Not a clean full-suite claim; see known baseline failures below. |
| Typecheck / build / scan | **PASS** | `npm run typecheck && npm run build && npm run scan`: 1918 modules; `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`. [Log](../evidence/excel-quote-import-v1/component-build.txt). |
| Browser | **PASS** | Actual `app.py` → Streamlit Components v2 → React → C1 → writers/readers, **18 checks**, Chromium 153 / Playwright, 1440×900 and 390×844. No route mocks, injected VM, fake API or second server. No horizontal document/shell overflow; no JS `pageerror` events. [Results](../evidence/excel-quote-import-v1/browser-results.json), [run](../evidence/excel-quote-import-v1/browser-run.txt), [screenshots](../evidence/excel-quote-import-v1/README.md). Not Owner-device certification. |
| Backend persistence | **PASS — sandbox only** | Saved incomplete draft, refreshed browser/reopened through existing readers, read back customer/disclosure flags/notes/A/B/history, verified source-download SHA256. Existing **mongomock/GridFS** transport; no real MongoDB, transaction/replica/disk-restart durability certification. Real production persistence: **NOT_RUN**. |
| XLSX | **PASS** | Actual browser downloads opened with openpyxl: current draft, historical sent v4 and byte-identical source workbook. Customer-workbook checks confirm public multiline notes/disclosures/routes/tax basis; exclude 31800000 reference cost, PRIVATE marker, supplier source, profit/cost headings, deselected production clause and formulas. Source workbook is intentionally unchanged, including its original formula text. Sent v4 still contains PUBLIC-BROWSER-V1 after next-draft edits. Excel desktop application: **NOT_RUN**; actual XLSX ZIP/workbook open/read/assert: PASS. |

### Actual representative case

- Generator `scripts/make_luc_giac_quote_fixture.py` creates three clearly marked **SYNTHETIC** sheets; it is not the absent original workbook.
- Existing-customer selection after customer creation through the real directory UI; file upload does not auto-create a quotation.
- **5 rows / 27 units / 607180 RMB**; only first row has confirmed model/material. Editing first quantity 16 → 15 gives **26 / 594125 RMB**, then restore.
- Existing Cost Intelligence UI parses/reviews/saves a synthetic historical rate. Picking its **31800000 VND reference cost leaves selling blank** and can save a DRAFT. Sale independently enters/confirms **35000000 VND**, explicit fixture service VAT 0%; B starts empty, then separately entered 50000000 remains independent of A.
- Missing FX / unconfirmed customs yield no determined VND grand total. Direct CNY and cross FX together are explicitly rejected, not silently resolved.
- Using explicitly entered **26500 VND/USD / 6.78 CNY/USD** yields **2373196165 VND** goods. Independently confirmed customs basis **2400000000 VND**, duty 5%, import VAT 8% gives **321600000 VND** tax; raising service sell to 36000000 does not increase it. These figures are test assumptions, NOT current rates or legal advice.
- With restored 35000000 service sell and confirmed fixture VAT, grand estimate is **2729796165 VND**. `31/02/2027` is rejected.
- Production disclosure deselected; multiline public notes saved/read back/exported. Source disclosure text remains in backend, not deleted.
- Explicit DRAFT → READY_FOR_REVIEW → SENT creates immutable sent v4; subsequent edit becomes draft v5 without changing historical export. “Đánh dấu đã gửi” records a state; it does not send email.
- Last complete browser run's synthetic quote ID is in `browser-results.json`. Sandbox app on port 9501 is stopped after acceptance; in-memory staging records are disposable.

### Known baseline failures — not hidden or repaired out of scope

1. `node tests/component/dom_acceptance_quote_cost_workflow_ux_01.mjs` passes quote/cost steps through 8c, then **FAILS at step 9**: `clickable "Quay lại" not found` in the Journey/list return test. Same error was reproduced using the **exact original baseline bundle** (`git show 5c6642a:component/dist/logi-shell.js`), without modifying the worktree bundle. Journey is outside this task and remains untouched. This script is **not reported PASS**.
2. Combining existing C1 staging tests and RBAC tests in one Python process leaves the existing `STAGING_ACTOR` authenticated. `test_unknown_role_falls_back_to_viewer` then **FAILS**. Reproduced on a **complete clean `git archive 5c6642a` baseline checkout**: **42 passed / 1 failed**, same assertion. The exploratory combined current batch had 161 passed / 1 failed. Separate relevant batches pass; our new fixture restores its prior user, and its mixed run with RBAC is **59 PASS**. See [baseline proof](../evidence/excel-quote-import-v1/baseline-python-isolation.txt) and [exploratory combined failure](../evidence/excel-quote-import-v1/combined-python-isolation-failure.txt).
3. Existing `npm audit` high transitive `source-map-js` advisory `GHSA-68fv-2mgg-jv7q` remains. No unrelated lockfile/dependency upgrade was made.

### Remaining limits / Owner gates

- Rendered donor URL retry failed `net::ERR_CONNECTION_CLOSED`; only fetched text/spec was available. Actual app screenshots are provided, **not a claimed pixel-perfect Fable–Sonnet comparison**. Existing Be Vietnam Pro stack is reused; external-font delivery is not certified in this network-limited sandbox.
- Original Lục Giác workbook accuracy, current supplier rates, HS/legal determination, Owner physical device, real MongoDB/GridFS disk/replica/restart behavior and production deployment: **NOT_RUN**.
- Before any future main integration, reconcile overlapping open PRs #204/#203/#202/#198 and rebuild the bundle from combined reviewed source. This task has not merged, cherry-picked or overwritten any of them. Final fetch still showed `origin/main` at baseline `5c6642a`.
- **Smallest Owner UAT:** in an isolated test app, choose an existing customer and upload the generated fixture; confirm that the review shows **5 rows / 27 units / 607180 RMB before applying**. No workbook transfer from Battle is needed.

## Reproduce without production access

Python/runtime versions are in [environment.json](../evidence/excel-quote-import-v1/environment.json). Dependencies/browser tooling installed only for this sandbox are not committed.

```bash
# First verify configuration has NO real MONGO_URI; do not print credentials.
.venv/bin/python -c 'from core.config import MONGO_URI; assert not MONGO_URI, "Use an isolated no-real-URI sandbox"'
.venv/bin/python scripts/make_luc_giac_quote_fixture.py .tmp/luc-giac-fixture.xlsx
.venv/bin/python -m pytest -q tests/test_excel_quote_import_v1.py
(cd component && npm ci && npm run typecheck && npm run build && npm run scan)
```

For browser acceptance, start the existing app **only with no real URI** on a spare port (Arena uses its long-running process tool):

```bash
AUTH_REQUIRED=false .venv/bin/python -m streamlit run app.py \
  --server.address 0.0.0.0 --server.port 9501 --server.headless true \
  --server.enableCORS false --server.enableXsrfProtection false --server.fileWatcherType none
```

Authentication/CORS flags above are for isolated acceptance only, not production configuration. The runner additionally refuses writes unless the app's existing UI reports SANDBOX_STAGING. It creates disposable synthetic customer/rate/quote records and does not mock the application transport.

```bash
# Set PLAYWRIGHT_MODULE / CHROMIUM_EXECUTABLE / CHROMIUM_LIB_PATH only if your
# sandbox needs external test tooling. Do not add browser deps to the app.
PLAYWRIGHT_MODULE=file:///home/user/logistics-work-desk-arena/.tmp/browser/node_modules/playwright/index.mjs \
CHROMIUM_EXECUTABLE=/tmp/chromium CHROMIUM_LIB_PATH=/tmp/al2023/lib \
node tests/component/browser_excel_quote_import_v1.mjs http://127.0.0.1:9501
```

Stop port 9501 afterwards. No production connection, `/goal` substitute, second dispatcher, framework, server or price engine is required.

---

## HEXA SIDECAR — PL/PI import for three real workbook layouts

`TASK_ID=HEXA-EXCEL-IMPORT-V0-REAL-LAYOUT-REPAIR` ·
`BRANCH=arena/df8f04ad-logistics-work-desk-arena` ·
`EXACT_BASE_HEAD=83162293036414dcafa01072b93eece8733b8688` · `CHAT_MODE=NEW_CHAT`.

**This is a HEXA SIDECAR checkpoint only.** It is independent of PR #211: it does
not change `NEXT_ACTION`, the Owner UAT status of PR #211, or anything PR #211
contains.

### Base and handoff (corrected)

The first HEXA checkpoint (`ac400977`) was built on `51422c94`, which is 97 commits
behind the task's `EXACT_BASE_HEAD`. Its claim that
`docs/CONTROL-TOWER-HANDOFF.md` is **absent** was an artefact of that wrong base and
is retracted: at `83162293` the Control Tower handoff **exists** and is the handoff
surface for this repository. This checkpoint therefore sits on `83162293` (session
branch fast-forwarded, no force-push, no rebase) and the handoff was updated there —
`HANDOFF_UPDATE=YES | PATH=docs/CONTROL-TOWER-HANDOFF.md | SECTION=HEXA SIDECAR`.

### What changed and what did not

| Surface | Change |
|---|---|
| `core/quote_excel_import.py` | Header-evidence table detection (no file-name or fixed-column matching), per-sheet used data region, layout + GOODS/PALLET/CARTON level roles, review/unknown evidence, hard ceilings relaxed from 40 declared columns to a 2000-column ceiling with a total-cell budget. Header labels are additionally read after dropping an ASCII unit suffix (`NW(KG)`, `VOL(CBM)`, `Size(mm x mm x mm)`). |
| `core/quote_workbook_view.py` | Uses the same hard ceilings, reports the USED region (`column_count`) beside the declared one (`declared_column_count`), renders only used columns. Read-only, grant-gated source cells unchanged. |
| `tests/test_hexa_excel_import_layouts_v1.py`, `scripts/make_hexa_layout_fixtures.py` | SYNTHETIC fixtures + acceptance tests (new files), plus the real-header fixtures A/B and the real multi-level layout C used by the v2 tests. |
| `tests/test_hexa_excel_import_real_headers_v2.py` | New acceptance suite over the REAL header wording/row positions of files A, B and C (new file). |
| React/CSS, `core/quotations.py`, `core/quote_customer_text.py`, customer snapshot allowlist | **Unchanged.** The existing goods table already accepts rows without a price (`None`, never 0). |

### Three levels of a multi-level packing workbook

Only three levels exist, and they are never interchangeable:

| Level | Recognised by | What it may do |
|---|---|---|
| `GOODS` | a goods-table header (identity/description + qty/cartons, price optional) | becomes the single customer goods list |
| `PALLET` | an explicit pallet header (`The pallet number`, `Pallet size`, …) with no qty/price of its own | recorded for review with its row count; never becomes a goods list, never adds qty/CBM/weight |
| `CARTON` | either three explicit `L/W/H` columns or ONE size column plus a `W`/`D`/`H` axis row directly under the header, together with weight/volume evidence | recorded for review with its carton size and numbers; never becomes a goods list, never adds to the shipment totals |

A level is linked to the goods list **only** on an exact, unique reference code.
The code is read from its own source column: on the goods side the model column,
then the source's reference columns, then the product/description cell (in the real
multi-level workbook that cell carries the code); on the level side only an
explicit `contract` / `REF NO` / model — never a free-text description.

A pallet is named **once per group** (`A2` filled, `A3`… blank). The reader carries
that pallet forward as the group's context and clears it when the source repeats
the group header, so a later group can never inherit the previous pallet. A source
`TOTAL` line is a sum of the level, not a level line, and is excluded.

Resulting states: a duplicate code on two goods lines ⇒ `level-link-ambiguous`, no
link, `NEEDS_REVIEW`; a level code matching no goods line ⇒ `level-link-unmatched`,
kept as evidence and never turned into a new goods row; no link at all ⇒
`level-link-needs-review` plus one `level_link_missing` unknown per goods row.

### Three layout families and how they are handled

| Family | Evidence used | Result |
|---|---|---|
| A — packing list with photos, table at row 7, 257 declared columns, no price | header row of bilingual column labels (`Item number`, `Product name`, `Size`, `Quantity`, `CTN`, `NW`, `GW`, `CBM`); used region ends at column T | goods rows with `source_sheet`/`source_row`; `unit_price = None` + `unit_price_missing`; product size kept as review evidence, never as package dims; no CBM invented |
| B — proforma invoice `PI (2)` + duplicate money sheet `File tiền hàng` | priced goods header on the PI sheet (`Model 型号`, `Size尺寸(MM)`, `Qt.数量`, `Unit Price 单价 (CNY)`, `Amount 金额 (CNY)`); the money sheet is classified `INTERNAL_CALC` | one goods table only (no double count), `money-sheet-not-imported`; fees/tax/cost on the money sheet never enter the goods or the customer quotation |
| C — `总清单` (header row 3, goods rows 7–16, 10 codes) → `托盘明细（2托）` (header row 1, repeated at row 9; pallet named once per group, `contract` on every line) → `卫浴` (header row 2 repeated per group, `W`/`D`/`H` axis row, `REF NO` per carton line, source `TOTAL` row) → hidden `打托指令` | GOODS/PALLET/CARTON roles from header evidence; hidden sheets never read; reference codes read from their own columns | one goods list from `总清单` only; 10/10 pallet allocation lines and 36/36 carton lines recorded as separate levels; `level-not-summed`; no link key ⇒ `NEEDS_REVIEW` |

### Standing protection (unchanged by this work)

- Hidden sheets and cost/money sheets are never the goods source; their rows are not read into the proposal.
- `customer_quote_snapshot` keeps its explicit allowlist; `review` evidence is **not** published.
- A fake `TT_INTERNAL_SENTINEL` in the fixtures (money sheet and hidden sheet) is asserted absent from the snapshot JSON and from the exported customer XLSX (values and package XML), and the pallet/carton sheet names never appear in the exported package.
- Raw source cells still require `commercial_write` on every sheet, customer sheet included; the viewer writes nothing.
- Sheet names only influence which table is *proposed*; publication still requires the operator's reviewed goods.

### Evidence and status

- `RED` (v1, before the first checkpoint's change): `tests/test_hexa_excel_import_layouts_v1.py` → 14 failed / 1 passed.
- `RED` (v2 reproof on the real layout, parser before the header repair): **6 failed / 106 passed** in the focused set. The whole workbook was labelled `PACKING_LIST`, `托盘明细（2托）` was not recognised as a level at all, `卫浴` was read as an extra goods list (`UNCLASSIFIED_TABLE`), the carton W/D/H breakdown was reported as a product size, and `Item number` was not read as a model code.
- `RED` (LINK repair, parser of `451e4e8` against the real-data fixture): **5 failed / 13 passed**. Only **2 of 10** pallet allocation lines survived (the 8 lines with a blank `A` were dropped), **0** reference codes were read (`contract` / `REF NO` were unmapped columns), therefore **0** links, and the source `TOTAL` line / repeated group headers were not excluded by rule.
- `GREEN` (after both repairs): **34 passed** in the two HEXA files (the link-repair suite included); focused 6-file set **115 passed**.
- Whole suite, same environment and same command, EXPECTED_HEAD `451e4e8` parser vs repaired parser with the SAME test files (excluding the pre-existing collection error in `test_partner_reconciliation_desk_write_oracle.py`, which imports a `ROUTES` symbol absent at this base): **639 → 634** failed/error test ids. `NEW=∅`; `GONE` = exactly the 5 link-repair tests. The remaining failures/errors are pre-existing sandbox/Streamlit-runtime issues, not caused by this change.
- Acceptance numbers on the real-data fixture (SYNTHETIC values): pallet **10/10** allocation lines kept, **10/10** `contract` codes read and matched to the summary sheet, pallet context `PLT-01` ×7 / `PLT-02` ×3 with no bleed across the repeated header, carton **36/36** lines linked by `REF NO`, goods table still **10 rows / qty 83** (the pallet `PC`/`Total` counts are kept apart and never added), `shipment.cbm` / `shipment.weight_kg` stay `None`.
- `IMPORT_STATUS=PROVEN_SYNTHETIC`; `REAL_WORKBOOK_TEST=NOT_RUN_IN_ARENA`. The Owner's three original workbooks are **not** in this repository and were **not** uploaded; only the described structures, header wording and data shape are reproduced synthetically.

### Fields that stay UNKNOWN

- `unit_price` for every packing-list / multi-level source (`unit_price_missing`) — never 0.
- `qty` when the source has no quantity column (`qty_missing`).
- Formula cells without a cached value (`formula_no_cache` / `formula-gap`) — never recomputed.
- Level ↔ goods links without an exact, unique reference code (`level_link_missing` / `level-link-ambiguous` / `level-link-unmatched`) — `NEEDS_REVIEW`, never guessed.
- `shipment.cbm` / `shipment.weight_kg`: contradictory or level-only measurements are deliberately left empty instead of being summed.
- Pallet `contract` / `House type` / `Room number` / `Project name` / `PC` / `Total`: kept as level evidence only; `PC` and `Total` are **not** the quantity being sold and are not added to it.

### Owner gates respected

`NO_MAIN_MERGE` · `NO_PR211_UPDATE` · `NO_NEW_PR` · `NO_DEPLOY` · `NO_PRODUCTION_DB` ·
`NO_CUSTOMER_PORTAL` · `NO_DEEPL_INTEGRATION` · `NO_COST_HISTORY_NEW_MODULE` · `NO_FORCE_PUSH`.

### Reproduce

```bash
python scripts/make_hexa_layout_fixtures.py .tmp/hexa-fixtures
python -m pytest -q tests/test_hexa_excel_import_layouts_v1.py \
  tests/test_hexa_excel_import_real_headers_v2.py \
  tests/test_excel_quote_import_v1.py tests/test_quote_workbook_view_v1.py \
  tests/test_excel_fidelity_repair_v1.py tests/test_excel_text_edit_v1.py
```
