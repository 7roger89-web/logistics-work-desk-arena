# Coder Report — LOGI_COST_RATE_VIETNAMESE_PARSER_01 (Kho giá vốn Vietnamese rate parser)

Status: PASS for the bounded parser + review-UI repair on the existing canonical cost-rate parser.
`P2P_LAW_SOURCE` = repo-root `AGENTS.md` → `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`, which is a
generated projection: `P2P_PORTABLE_LAW_PROJECTION=YES`, `PACKAGE_VERSION=8.4.7-C-codex.74`,
`CANONICAL_SOURCE=7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`,
`SOURCE_CONTENT_SHA256=4e7239101063ac43e26a0fc784d48dc212eea640bdbc583395bc2d930c78876d`,
`CANONICAL_WINS_WHEN_REACHABLE=YES`, status `CANONICAL_IN_DEVELOPMENT_SOURCE` (candidate, `UNPROMOTED`).
Reported as the actual portable projection, not the stale `LOCAL_PORTABLE` shorthand.

## Git reference

- Branch: `arena/01a0d2a3-logistics-work-desk-arena` (session-pinned; the single task branch off `main`)
- BASE_SHA: `7ce2d656a3cf1ae862d2dfd86707b43bb85b49f4` (= EXPECTED_MAIN, verified before work)
- PR: open, DO NOT MERGE (see PR link in session return)
- TARGET_APP=logistics-work-desk · no other app touched

## OE gate

```
Không bị over engineering chứ?
SIMPLER_PATH            = yes — extends the existing deterministic regex parser in core/cost_intelligence.py
MATERIAL_PROGRESS       = yes — production defect (0 rows on real Vietnamese rate text) is fixed
NECESSITY               = yes — Owner fixture is the required contract; 8/10 tests failed pre-fix
CORE_BEFORE_SUPPORT     = yes — parser first, review-UI second; no new service
SMALLER_VERIFIABLE_SLICE= yes — 1 parser module + 1 page view-model + 1 component view + 1 test file
OE_VERDICT=DO_IT
```

FORBIDDEN and honored: no LLM/API parsing, no NLP framework, no second parser, no rules engine, no
external service, no new database; same canonical store/parser.

## Root cause (verified with failing tests BEFORE implementation)

`core/cost_intelligence.py` → `_money_matches` only recognized currency-BEFORE-amount legacy forms
(`USD 750`, `$130`, `USD1425/40HQ`) and fixed unit tokens (`20GP/40HQ/SET/RT`). Real Vietnamese rate
text uses (a) amount-before-currency (`950 usd/cont`), (b) k/tr/triệu multipliers (`9.5 triệu`,
`250k`, `6 tr`), (c) the `cont 20'`/`cont 40'` container phrase, and (d) unit-less amounts
(`2 triệu/cont`, `KHOẢNG 10 triệu`). Pre-fix: 8 failed / 2 passed on the new contract tests →
`ValueError: Không bóc được dòng giá nào` → **zero rows** in production.

## What changed (bounded)

1. `core/cost_intelligence.py` (`PARSER_VERSION="cost-rate-parser/2"`), same deterministic parser:
   - amount-before-currency with currency list `USD|CNY|RMB|VND|$` (e.g. `950 usd/ cont 20'` → 950 USD);
   - `k`/`tr`/`triệu` multipliers (250k → 250,000; 6 tr / 9.5 triệu / 10 triệu → ×1,000,000);
   - `cont 20'` → `20GP`, `cont 40'` → `40` (deliberately NOT mapped to `40HQ` — ambiguous, stays
     `NEEDS_REVIEW`); `container`/`cont` → `CONT` generic; unit may be absent (stays blank, never invented);
   - currency inferred `USD` for bare `usd` mentions, `VND` for `tr/trieu/k`-denominated Vietnamese
     amounts; `KHOẢNG`/`~` sets `approximate=True` (never presented as an exact confirmed price);
   - primary-vs-conditional: a line with 2+ amounts (e.g. `950 usd/cont 20' ... +80 usd/cont`) keeps the
     PRIMARY amount and exposes the conditional remainder in `conditionalAmounts` with a
     `NEEDS_REVIEW` warning — never replaced, summed, or silently promoted; `rawLine` always preserved;
   - a line whose ONLY amounts are conditional produces no row; non-price sentences
     (`Nếu có phát sinh...`) produce no row and no zero-price row (UNKNOWN != ZERO);
   - service labels preserved verbatim (Cước biển, Phụ phí hãng tàu, nâng cont hạ vỏ, Hạ tầng, thủ tục
     hải quan, vận tải về Sơn Tây Hà Nội, kiểm hóa mở cont, Kiểm hóa soi chiếu, công bố hợp quy...);
     catalog canonicalization only on a real alias match — never a blanket DVK/"Dịch vụ khác" mapping;
   - line-start `-` treated as a bullet (not a negative sign); legacy forms unchanged.
2. `component/src/lib/viewmodel.ts` — `CostRateLine` gains `reviewNote`, `approximate`,
   `conditionalAmounts` (smallest truthful representation of the new parser warnings in the existing model;
   no schema change).
3. `component/src/components/CostIntelligence.tsx` — review rows render the amber review notes
   (conditional surcharge not structurally separated; approximate price not yet confirmed), keep the
   original `Gốc:` line, and expose stable testids `cost-rate-raw` / `cost-rate-parse` /
   `cost-rate-review` / `cost-rate-row`.
4. `component/dist/logi-shell.js` — rebuilt production bundle (1,117.68 kB, gzip 239.72 kB);
   CSS unchanged.
5. `tests/test_cost_intelligence_vietnamese_rates.py` (new) — 10 contract tests A–J incl. the exact
   Owner fixture (9 rows, 3 NEEDS_REVIEW, 2 conditional-surcharge warnings) and all legacy regression
   forms (USD 750/20GP, MCC USD 675/20GP, O/F:USD1425/40HQ, USD1200/40HQ, THC $130/20GP $205/40HQ,
   REFUND 21$/RT, BUY EXPORT:100$/SET + TAX, COSCO USD 1300/40HQ, SNL 没仓位, 电放费 RMB500/SET).

## Evidence

- Parser contract: `tests/test_cost_intelligence_vietnamese_rates.py` 10/10 PASS; legacy
  `tests/test_cost_intelligence.py` 15/15 PASS (25 passed combined).
- Owner fixture final output: 9 rows — Cước biển 950 USD/20GP (NEEDS_REVIEW, cond `+80 usd/cont`);
  Phụ phí hãng tàu 9,500,000 VND/20GP; nâng cont, hạ vỏ 2,600,000 VND/20GP; Hạ tầng 250,000 VND/20GP;
  thủ tục hải quan 2,000,000 VND (unit CONT, generic); vận tải về Sơn Tây, Hà Nội 6,000,000 VND/20GP
  (NEEDS_REVIEW, cond `+500k/cont`); kiểm hóa mở cont (nếu có) 4,000,000 VND; Kiểm hóa soi chiếu
  (nếu có) 2,000,000 VND; công bố hợp quy hàng thuộc Bộ Công An 10,000,000 VND, unit blank,
  approximate, NEEDS_REVIEW. Route Ningbo→Hải Phòng. Non-price sentence → no row.
- Full suite (`--ignore` pre-existing broken `tests/test_partner_reconciliation_desk_write_oracle.py`
  collection error present on clean main): **24 failed / 1414 passed / 44 skipped — FAILED set
  identical to clean main** → zero regressions.
- `npm run typecheck` clean; `npm run build` clean.
- Streamlit AppTest of the real app script: clean run, no exceptions.
- REAL built UI (isolated staging port 9501, `AUTH_REQUIRED=false` → local-admin preview, staging data,
  NO save action performed): Chrome 153 headless CDP. Navigated Báo Giá → **KHO GIÁ VỐN**, pasted the
  exact 719-char Owner fixture, pressed **PHÂN TÍCH** → toast "Đã bóc dữ liệu giá — 9 dòng · 3 dòng cần
  xem lại."; review section rendered all 9 rows with correct VND amounts, 20GP/CONT units, route
  NINGBO → HAI PHONG, verbatim raw lines, the 2 conditional-surcharge amber warnings and the
  KHOẢNG approximate warning; the 3 NEEDS_REVIEW rows show the confirm form (Cước biển: 950 / USD /
  20GP) instead of being silently accepted. Screenshots (not committed; repo `reports/` is text-only):
  `/tmp/ui-review-evidence/desktop_1440x900_review.png`, `/tmp/ui-review-evidence/mobile_390x844_review.png`,
  `/tmp/ui-review-evidence/desktop_review_rows.png`, structured `/tmp/ui-review-evidence/ui_evidence.json`.
  Desktop 1440×900 and mobile 390×844 both render without overflow.

## Safety / scope

- No production DB mutation, no schema change, no secrets touched, no deploy, PR not merged.
- UI verification ran on isolated port 9501 (production = 8501/8510) with preview/staging data only;
  the save path was never invoked.
- Minimum sufficient repair: parser + one view-model type + one component view + rebuilt dist + tests.

## Restack (LOGI_COST_RATE_VIETNAMESE_PARSER_01_RESTACK, 2026-09-24)

Control Tower blocker (comment 5812359151): current main advanced 6 commits
(PR #110 "move international payment to standalone Tools calculator") and
**rewrote history — `4a4efe815202626e5a0fc6d709598307fb87a202` is now an
orphan root with no common ancestor with the original PR112 base
`7ce2d65`** (verified: `git merge-base` → none; `--is-ancestor` → NO).
`git rebase` is therefore impossible; the restack was done as:

1. `git reset --hard origin/main` (4a4efe8) on the SAME branch.
2. Re-applied exactly the PR112 source intent (5 files; content-verified:
   main snapshot is identical to the old base for all three source files,
   so the re-applied diff is byte-identical to the original commit's
   source changes): `core/cost_intelligence.py`,
   `component/src/components/CostIntelligence.tsx`,
   `component/src/lib/viewmodel.ts`,
   `tests/test_cost_intelligence_vietnamese_rates.py`, this report.
3. Rebuilt `component/dist/logi-shell.js` FROM THE RESTACKED SOURCE
   (`npm ci` + `npm run typecheck` + `npm run build`) — did NOT copy the old
   PR112 bundle; did NOT touch current-main Intl Payment work.
   `dist/logi-shell.css` rebuild is byte-identical to main's committed css.

Preservation proof (source + artifact):
- PR112 family: 10/10 new + 15/15 legacy parser tests PASS on the restacked
  tree; dist contains `cost-rate-raw`, `cost-rate-review`, `KHO GIÁ VỐN`,
  "Đã bóc dữ liệu giá", `GẦN ĐÚNG`, "Phụ phí có điều kiện", "XÁC NHẬN LẠI",
  `KHOẢNG`; parser warning strings ("chưa tách được thành cấu trúc",
  "chưa phải giá chốt") live in `core/cost_intelligence.py` (runtime data).
- Current-main Intl Payment family: `IntlPaymentTool.tsx`,
  `IntlPaymentComparator.tsx`, App.tsx route `/thanh-toan-quoc-te`
  (standalone CÔNG CỤ page) and main's ContractDetail state (tab removed by
  PR #110) all present; rebuilt dist contains "Thanh toán quốc tế",
  `intl-payment-tool`, `thanh-toan-quoc-te`, `intl-tool`, `intl-gross-usd`,
  `intl-manual-toggle`.
- Rebuild determinism: two consecutive builds → identical
  sha256 `df32e841b48409209292ea3b69743a7118032fd3f271c1afa5bde0e0f07071f5`;
  differs from main's pre-restack dist `ce6a5da52a95743b998a10213ff2dbedaae214ee7e7dc899e1e9435509cf778b`
  → the pushed bundle IS the build of the restacked source.
- Focused checks: 25/25 parser tests, `tsc --noEmit` clean, build clean
  (dist 1,102.46 kB / gzip 238.73 kB; css 67.15 kB, identical to main's).

Safety: no DB/schema/secrets changes, no deploy, no merge; SAME branch
`arena/01a0d2a3-logistics-work-desk-arena`, SAME PR #112 (force-updated).
