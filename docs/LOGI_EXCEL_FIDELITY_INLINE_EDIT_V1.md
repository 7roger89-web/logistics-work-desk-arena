# LOGI_EXCEL_FIDELITY_INLINE_EDIT_V1

**Status: implemented on a stacked draft branch, verified on a SYNTHETIC fixture; real-workbook and real-MongoDB gates stay open. Not merged, not deployed.**

## What the Owner asked for, and what was built

1. **Keep the customer's original workbook visible, per sheet.** `core/quote_workbook_view.py` re-reads the bytes already stored in GridFS (verifying their SHA256) and returns a bounded, read-only view: sheet names in file order, cell values at their real row/column, merged ranges, column widths/row heights, font/fill/border/alignment/wrap, number formats, and source formulas together with their cached results. `ExcelSourceWorkbook.tsx` renders it inside Step 1 with tabs per sheet and an explicit "this is not 100% fidelity" statement. Nothing in this path writes: it is a cross-check, and the file the customer owns is never rewritten (SHA256 identical before/after).
2. **Click any text on the Step-3 customer preview and type the new wording.** `InlineText.tsx` turns the clicked piece into an input (or a textarea for a multi-line region) exactly where it is; Enter applies, Ctrl/⌘+Enter applies a multi-line region, Escape cancels, clicking away applies. A region that differs from its default shows its own restore control, and the toolbar offers "hoàn tác nội dung chưa lưu".
3. **One controlled customer snapshot.** `core/quote_customer_text.py` builds a single resolved text map (`quote-customer-text/1`) from the quote + the Sale's presentation overrides. `customer_quote_snapshot()` embeds it, the Step-3 paper renders it, and `core/excel_utils.generate_quote_excel` prints the same map — so a sentence cannot be visible on screen while the file prints something else.
4. **Money stays authoritative.** Amounts, FX rates, tax percentages and totals are not text regions at all: they are computed by the backend and rendered read-only.
5. **Identity data is never silently changed.** Customer name and customer code are guarded regions: restyling them is allowed, but the paper and the sale-side UI warn that the displayed wording diverges from confirmed data, and the directory record is untouched.

## Where the edits live (stable, not row-order dependent)

Region ids are derived from content and canonical keys — never from array position:

- document wording: `doc.title`, `doc.greeting`, `doc.customer_name`, `doc.goods_description`, `doc.route`, `doc.option_line`, `scope`, `doc.closing`, `doc.addendum`
- labels: `col.goods.*` and `col.service.*` (table headers), `sec.*` (section headings)
- bound rows: `goods.<key>.name|model|material|note`, `service.<key>.name|public_note`
- published disclosures: `note.<disclosure-id>`, plus `notes.additional`
- every region carries `source` = `SOURCE` | `SYSTEM_DEFAULT` | `SALE_EDITED` | `UNKNOWN`, its `binding`, and a `mismatch` flag for guarded regions

Bound regions write the ONE canonical field they belong to (goods description, service name, public note, option scope, header fields). Presentation regions write a small override block on the existing draft (`excel_quote.customer_text.overrides`). Values are stored as plain text only: control characters stripped, a leading `=` prefixed so it can never become a formula, unknown/unbound ids dropped, length bounded (2,000 short / 6,000 long).

## Unsupported / not rendered — declared, never claimed as 100%

| Supported | Explicitly NOT rendered |
|---|---|
| cell values at their real position (text, number, date) | images / logos inside a sheet |
| source formulas shown as text, never executed | charts |
| a formula's cached result when the file stored one | conditional formatting |
| merged cells | data validation dropdowns |
| column widths, row heights | cell comments |
| font, size, bold/italic, colour | rich text inside one cell |
| fill, borders, alignment, wrap | pivot tables, sparklines |
| common number/date formats (unknown format codes shown raw) | named ranges / external links (listed, not rendered) |
| hidden row/column/sheet flags | print settings, repeated headers, page breaks |

A formula with **no** cached value renders as `→ chưa có giá trị cache` and is never coerced to `0`; an unconfirmed customs basis still yields no VND grand total.

Sheet classification comes from evidence, not from a sheet name: a sheet is internal when it matched an internal-cost name marker **or** its rows matched the cost shape of a sheet already classified as internal **or** it duplicates another parse table (recorded in `source.table_sheets`). For the expected Lục Giác file, `Dự kiến Chi phí` is classified internal and never treated as the customer quote.

## Repair of the four findings from the independent source review (2026-10-16)

| # | Finding | Fix |
|---|---|---|
| 1 | `LG nhập - Đại lý TT L Xuất` / `Dự kiến Chi phí` were reachable as raw bytes, and an UNCLASSIFIED sheet was shown as public | One rule — `protected_sheet_names()` = every sheet except the single customer sheet — drives both the read-only viewer's content lock and the raw download, gated on the **existing** `commercial_write` grant no new role. A partial workbook is REFUSED, never trimmed; a SHA256 mismatch is refused; and a ONE-sheet workbook whose cost row sits inside the customer tab is refused as well, because the sheet count is not the test. |
| 2 | the edited `dịch vụ` summary on the preview never reached the file — the option line overwrote it | The exporter now prints the summary at `A15`, the option line at `A16`, the confirmed scope at `A17`, and the service rows from row `19`. |
| 3 | the customer name shown on the paper never reached the `To` cell | The exporter and `CustomerPaper` both read the published `doc.customer_name`; the greeting uses `label.attn` (default `To`, so legacy quotes keep their exact bytes). `customer_id` and the directory record are untouched — asserted, not assumed. |
| 4 | `Kính gửi`, `Cảng / điểm`, `Nơi lấy hàng` … were hardcoded on the paper and absent from the text map | Every label is now a region on BOTH the preview and the XLSX, together with `sec.no_services` and `doc.disclaimer`. Each label is published only when its line is published, and every published region must declare the cell it prints in (`export_rule()`), surfaced in the UI as `eq-text-status[data-unmapped-regions]`. Customs labels print even when the figure is unconfirmed (`Chưa xác định`). |

**No presentational edit moves a number:** the new tests compare numeric cells before and after the label edits, and a forged region id is rejected.

## Verification (see `evidence/excel-fidelity-inline-edit-v1/`)

- 33 real-bundle DOM checks (`dom-acceptance.txt`): click-to-edit title, product name, column label, payment term, multi-line note; the data-backed summary and the 16 label regions; the identity warning; per-region restore; global undo; read-only mode; the save payload; the reload-and-reopen round-trip; both download roles; sheet tabs/order; merged cell span + fill; cached vs uncached formulas; locked internal sheet; no amounts editable; no internal string on the paper.
- 72 Python tests across the new/updated suites (18 in `tests/test_excel_fidelity_repair_v1.py`) and a 198-test quote/Excel/RBAC regression with zero failures in this task's files; the one RBAC failure elsewhere is pre-existing cross-file state pollution, shown to fail with no file from this task loaded.
- Preview ↔ XLSX cross-check: `xlsx-vs-preview.json` plus the exported file, listing every edited sentence and the exact cell it landed in, the export rule per region, and the untouched identity.
- Source immutability: `source-immutability.json`; permissions: `permission-matrix.json`.

## Open gates (honest)

- **Real Lục Giác workbook not tested.** The fixture is SYNTHETIC and proves nothing about that file.
- **Real MongoDB staging not accepted**: staging transport is mongomock + GridFS compatibility only.
- **1440×900 / 390×844 pixel evidence not produced** — this environment has no Chromium/Playwright. A static DOM snapshot (`preview-snapshot.html`) is provided for eyeballing; scroll containers were added but no layout measurement was made.
- **Owner UAT** on the editor's wording/UX not done.
- PR #205 untouched; this branch is stacked on it and nothing is merged or deployed.
