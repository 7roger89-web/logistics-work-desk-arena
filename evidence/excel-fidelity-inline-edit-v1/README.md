# Excel fidelity + inline text edit V1 — evidence index

**2026-10-16 · actual repository code paths · SYNTHETIC workbook · isolated SANDBOX_STAGING only.**

[Implementation / scope / verification report](../../docs/LOGI_EXCEL_FIDELITY_INLINE_EDIT_V1.md)

- [33 real-bundle DOM checks](dom-acceptance.txt) ([machine-readable](dom-checks.json)) — acceptance A/B/C/D/E/F/G/I at the UI seam, plus the four findings repaired below.
- [Static DOM snapshot](preview-snapshot.html) — the Step-3 customer paper and the read-only original-workbook viewer, rendered from the real bundle markup + real CSS. **Open it in a browser at any width.** It is *not* a screenshot.
- [Preview ↔ XLSX cross-check](xlsx-vs-preview.json) + [the actual exported file](customer-quote-SYNTHETIC-edited.xlsx) — every edited sentence with the exact cell it landed in (`A5`, `A11`, `B21`, `B33`, `A46`, `A50`), the full region-by-region presence list, internal-string leaks, formula cells.
- [Source immutability](source-immutability.json) — the customer's original file is byte-identical (same SHA256, same GridFS object) after all editing.
- [Declared fidelity](fidelity-declared.json) — what the viewer supports and what it explicitly does NOT render.
- [New suites: 72 passed](python-new-suites.txt); [quote/Excel/RBAC regression: 198 passed, 6 skipped, 0 failures in this task's files](python-quote-regression.txt) — the file also shows the one RBAC failure that is *pre-existing cross-file state pollution* (it fails with no test from this task loaded).
- [Typecheck / build / zero-executable-process scan](component-build.txt).
- [Existing jsdom component lanes](component-dom-regression.txt) and [proof the four failures there are pre-existing](component-dom-preexisting.txt) — the same four lanes fail identically against the pristine `e7ac601` bundle.
- [Permission matrix](permission-matrix.json) — the raw-workbook download refused for a reader-only role, *and* refused for a ONE-sheet workbook whose cost row sits inside the customer tab.
- [Tool versions and open gates](environment.json).

## Repair of the four review findings (2026-10-16)

| # | Finding | Fix | Evidence |
|---|---|---|---|
| 1 | `LG nhập - Đại lý TT L Xuất` / `Dự kiến Chi phí` were reachable as raw bytes, and an UNCLASSIFIED sheet was shown as public | one rule, `protected_sheet_names()` = every sheet except the single customer sheet; both the read-only viewer's content lock and the raw download use the existing `commercial_write` grant; a partial workbook is refused, never trimmed; SHA256 mismatch refused; a ONE-sheet workbook with a cost row on the customer tab is refused too | `tests/test_excel_fidelity_repair_v1.py` (real dispatcher, per-role matrix), `permission-matrix.json`, DOM checks "Finding 1 (UI) …" |
| 2 | the edited `dịch vụ` summary was overwritten by the option line | summary → `A15`, option line → `A16`, scope → `A17`, rows from `19` | `sec.service_summary` → `A15` in `xlsx-vs-preview.json`, DOM "A data-backed label edits through the same in-place seam" |
| 3 | the customer name shown on the paper did not reach the `To` cell | exporter and `CustomerPaper` both read the published `doc.customer_name`; `label.attn` (default `To` for legacy quotes) prints the greeting | `doc.customer_name` → `G7`, `identityUntouched` keeps `customer_id` `CUST-LUCGIAC-EVIDENCE` and the directory record `Công ty Lục Giác` |
| 4 | `Kính gửi`, `Cảng / điểm`, `Nơi lấy hàng` … were hardcoded on the paper and absent from the map | every label is a region on BOTH the preview and the XLSX; `sec.no_services` and `doc.disclaimer` are published regions too; customs labels print even when the figure is unconfirmed (`Chưa xác định`) | `label.attn` → `F7`, `label.ports` → `A19`, `label.pickup` → `A20`; `regionsMissingFromXlsx: []`, `unmappedRegions: []` |

Every published region must name the cell it prints in (`export_rule()`); the contract is visible in the UI as `eq-text-status[data-unmapped-regions]` and surfaces as an alert when non-zero. **No presentational edit moves a number**: the new tests compare numeric cells before/after the label edits.

## What was actually proven where

| Acceptance | Where | Result |
|---|---|---|
| A sheet names/order preserved | DOM (`workbook-tab-*`, `workbook-sheet-order`) + Python | PASS — `BÁO GIÁ` → `LG nhập - Đại lý TT L Xuất` → `Dự kiến Chi phí`, in file order |
| B text/number cells, merged cells, styles | DOM cell `2:1` colspan 8 + fill; Python style/merge assertions | PASS for the supported list; the rest is declared not-rendered |
| C 5 rows / 27 pcs / 607,180 RMB | DOM read-back + Python | PASS, and no VND grand total is invented while the customs basis is unconfirmed |
| D formula without cache → UNKNOWN, never 0 | DOM `workbook-cell-22:2` + Python | PASS |
| E title → `BÁO GIÁ NHẬP KHẨU BÀN HỌP` | DOM click→type→Enter | PASS |
| F product name / column heading / payment term / multi-line note | DOM | PASS (bound regions write the canonical field, wording writes an override) |
| G survives reload | DOM re-mount + reopen; Python fresh reader | PASS |
| H XLSX matches preview | [xlsx-vs-preview.json](xlsx-vs-preview.json) | PASS (`regionsMissingFromXlsx: []`) |
| I no internal cost/source/notes/metadata | DOM paper text + Python (cells, XML package, hidden sheets, defined names) | PASS |
| J SENT stays immutable | Python | PASS |
| K 1440×900 / 390×844 | **NOT RUN** | OPEN GATE — no Chromium in this environment; scroll containers exist but no pixel measurement was made |
| L original file SHA256 unchanged | [source-immutability.json](source-immutability.json) | PASS |

## Honest scope

The fixture is generated by `scripts/make_luc_giac_three_sheet_fixture.py`, is visibly marked SYNTHETIC, and mimics a Lục Giác-shaped workbook (sheet names/order, merges, fills, fonts, borders, number formats, freeze panes, cached formula results plus one deliberately uncached formula). It is **not** the Owner's original workbook and proves nothing about that specific file — the real-workbook gate stays open.

The DOM lane is the repository's existing jsdom lane, driving the real built bundle (`component/dist/logi-shell.js`) with data produced by the real Python modules (`scripts/make_excel_inline_text_dom_fixture.py`). jsdom performs no layout, so **no viewport claim is made**; the static snapshot exists so a human can look at the two layouts in a real browser.

Saving/reading used the existing mongomock/GridFS staging transport. Real MongoDB durability, indexes and GridFS behaviour are not established. No deploy, no merge to `main`, PR #205 untouched.
