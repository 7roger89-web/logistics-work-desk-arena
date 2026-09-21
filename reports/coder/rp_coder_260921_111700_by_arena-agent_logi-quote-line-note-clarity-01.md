# Coder Report — LOGI_QUOTE_LINE_NOTE_CLARITY_01 (per-service-line note clarity)

Status: PASS for the bounded UI/UX clarity repair + strengthened multi-line verification.
`P2P_LAW_SOURCE=LOCAL_PORTABLE` (repo-root `AGENTS.md` → `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`,
`P2P_PORTABLE_LAW_PROJECTION=YES`, canonical source `7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`,
source SHA-256 `94990826e7f20fa96c6d58edad53d19d99cc8fa0f18a90bcb9b915e165a1391a`).
Canonical was attempted first in this session (`gh api repos/7roger89-web/P2P-upgrade-github-1/contents/...` → `404 Not Found`),
so the valid generated portable projection is the truthful law source — no cross-repo probe was made
solely to trigger fallback (`TARGET_REPO_AUTH != CANONICAL_CROSS_REPO_REACHABILITY`).

## Git reference

- Branch: `arena/01a0c399-logistics-work-desk-arena` (this session is pinned to one branch by the platform;
  that branch IS the one fresh branch for this task, off `main`)
- BASE_SHA: `c088c0da424d25034b237f5a9cb78f1b66ee71cf` (= EXPECTED_MAIN, verified `git rev-parse HEAD` before work)
- Issue: #90 · PR: (see packet)
- TARGET_APP=thu-log · FORBIDDEN_APP=tienthanhlog (not read, not touched)

## OE gate

```
Không bị over engineering chứ?
SIMPLER_PATH            = yes — one page component (SalesQuotes.tsx); no abstraction, no new module
MATERIAL_PROGRESS       = yes — the Owner's actual complaint (ambiguous note ownership) disappears
NECESSITY               = yes — without a visible per-card identity the note reads as quote-level
CORE_BEFORE_SUPPORT     = yes — requested UX first; test lanes were extended, not rebuilt
SMALLER_VERIFIABLE_SLICE= yes — 1 page + its 2 existing evidence lanes
OE_VERDICT=DO_IT (Owner selected DO_IT)
```

Deferred as `DEFERRED_NOT_REQUIRED`: any quote-level note concept, any new design-system file, any
new component/test framework, any change to the persistence model.

## What changed (bounded)

`component/src/pages/SalesQuotes.tsx` — the create/edit quote modal only:

1. **Every service card is now a `<fieldset>` with an explicit visible identity** `Dòng dịch vụ 1`,
   `Dòng dịch vụ 2`, … (badge inside the card, preceding the fields) plus an `sr-only` `<legend>` so the
   same identity is the programmatic group name for screen readers.
2. **Inside EACH card**: the note field is now visibly labelled **`Ghi chú dòng này`**, with a hint
   `Chỉ áp dụng cho dòng dịch vụ N.`, and it lives in its own sub-panel inside the SAME card as that
   line's `Mã dịch vụ · Tên dịch vụ · ĐVT · Số lượng · Giá vốn (unit) · Giá bán (unit) · Thuế % · Tiền tệ`.
3. The form section states the rule once in user language: *“Mỗi dòng dịch vụ có ô ghi chú riêng của
   chính dòng đó — không có ghi chú dùng chung cho cả báo giá.”*
4. `Xóa dòng` moved into that card's header (still hidden when only one line remains) and the
   `Thêm dòng` button got a stable test hook. Behaviour is unchanged: `addLine` appends a **fresh**
   `LineForm` (`note: ""`), `removeLine(i)` filters exactly index `i`.
5. Test hooks added for durable verification: `quote-line-N`, `quote-line-N-title`,
   `quote-line-N-note-block`, `quote-line-N-note`, `quote-line-N-remove`, `quote-add-line`.

No backend, dispatcher, writer, schema, route, navigation, or price/tax/margin/FX code was touched.
The old per-line `aria-label` was replaced by the real visible `<label>` (wrapping label supplies the
accessible name); the one existing DOM harness selector that depended on that private attribute was
updated in place with unchanged assertion strength (see Evidence §5).

Evidence tooling (not shipped app code): `tests/component/specimen_quote_line_note_clarity.html` mounts the
REAL committed bundle with a real fixture so a human can open the Báo Giá desk and see the per-line cards
without running Streamlit/Mongo.

## Evidence

### 1. Owner’s required proof — DOM/runtime lane on the REAL built bundle

`node tests/component/dom_acceptance_quote_line_note_clarity.mjs` → `PASS — 7 checks` (10 s), including
verbatim payload captures:

```
STEP 3 — LINE 1 NOTE=A + LINE 2 NOTE=B travels on the right line
    quote_create.serviceLines = [{"code":"DV-VC-TQ","costUnit":26000000,"sellUnit":28500000,"note":"Giá đã gồm bốc xếp"},
                                 {"code":"DV-TQ","costUnit":2500000,"sellUnit":3000000,"note":"Chưa gồm kiểm hóa"}]
STEP 4 — fresh readback restores each note to its own line
  ✓ fresh readback: line 1 = A, line 2 = B, each inside its own card
STEP 5 — edit line 2 only: line 1 keeps A in DOM + payload + readback
    quote_edit.serviceLines   = [{"code":"DV-VC-TQ","note":"Giá đã gồm bốc xếp"},
                                 {"code":"DV-TQ","note":"Chưa gồm kiểm hóa — khách tự làm"}]
  ✓ line 1 STILL="Giá đã gồm bốc xếp", line 2="Chưa gồm kiểm hóa — khách tự làm" in DOM, payload and readback
STEP 6 — removing line 1 removes only that line and its own note
    after delete line 1       = [{"code":"DV-TQ","note":"Chưa gồm kiểm hóa — khách tự làm"}]
```

So: `LINE 1 NOTE=A, LINE 2 NOTE=B → create → fresh readback → line1=A, line2=B` and
`edit line2=B2 → fresh readback → line1 STILL=A, line2=B2` hold on the shipped bundle.

### 2. Structural ownership (same lane, STEP 1/2/7)

- one line → exactly one card (`quote-line-1`), exactly one note input, `line_count == note_count`;
- the note block, its input, the identity badge and every money/qty/tax/currency field of that line are
  descendants of the SAME card element; no note exists outside a line card;
- `Thêm dòng` → card 2 with its own `Dòng dịch vụ 2` badge and its **own blank** note (line 1 untouched);
- badge is visible (not `sr-only`), precedes that line's note; field grid stays `grid-cols-2 md:grid-cols-4`
  (mobile 2-col / desktop 4-col) and the note input keeps the 48 px touch target in both viewport classes.

### 3. Backend authority lane (fresh Mongo readback, mongomock staging, canonical writers unchanged)

`tests/test_logi_quote_line_note_clarity_01.py` → **6 passed**:

| Test | Proves |
| --- | --- |
| `..._two_lines_keep_distinct_notes_through_create_and_fresh_readback` | A/B land on `service_lines[0]/[1]`, `line_no` 1/2, code+name aligned |
| `..._one_blank_line_never_inherits_another_line_note` | an untouched line stays blank (no quote-level sharing) |
| `..._edit_second_line_note_preserves_first_line_note_and_money` | B→B2 leaves line 1 note + every line-1 money field + `calculation` byte-identical |
| `..._delete_first_line_does_not_migrate_its_note_to_the_survivor` | surviving line keeps ITS OWN note, `line_no`=1, deleted note absent from the stored doc |
| `..._note_count_tracks_line_count_across_add_and_remove` | 3 lines → 3 notes; removing the middle leaves `[n1, n3]` on lines 1/2 |
| `..._note_is_not_a_new_persisted_field` | noted vs plain line persist the SAME key set (NEW_PERSISTED_FIELDS=0) |

### 4. Issue #88 regression lanes

- `python -m pytest tests/test_logi_internal_ux_simplify_01.py -q` → **5 passed** (H–K quote-note contract intact).
- `node tests/component/dom_acceptance_internal_ux_simplify.mjs` → **PASS — 8 checks** (nav, customer search,
  `?q=` deep links, searchable picker, per-line note payload, edit readback, dead-route audit, translation parity).
  Only the two note-input selectors moved from the removed private `aria-label` to the stable test id; the
  assertions themselves are unchanged.

### 5. Full-suite regression comparison (HEAD vs BASE, identical command)

```
.venv/bin/python -m pytest tests -q --ignore=tests/test_partner_reconciliation_desk_write_oracle.py
BASE c088c0d: 15 failed, 1279 passed, 44 skipped
HEAD        : 15 failed, 1285 passed, 44 skipped      (+6 = the new tests; 0 new failures)
diff base_fail.txt head_fail.txt → IDENTICAL_PREEXISTING_FAILURE_SET
```

The 15 failures and the `test_partner_reconciliation_desk_write_oracle.py` collection error
(`ImportError: cannot import name 'ROUTES' from 'views.web_app'`, legacy Streamlit router surface) are
**pre-existing at BASE** and unrelated to this task; they are reproduced with the worktree stashed.

### 6. Gates

```
npm run typecheck  → PASS (tsc --noEmit, exit 0)
npm run build      → PASS (dist/logi-shell.js 975.29 kB · logi-shell.css 64.53 kB)
double build       → byte-identical (sha256 bc9c43c2… / f61c9429…) → DETERMINISTIC_BUILD=YES
npm run scan       → FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0
SOURCE_DIST_SYNC   → component/dist rebuilt in the same commit as the source change
```

### 7. Runtime visual classification (honest)

`RUNTIME_UI_REVIEW_REQUIRED=YES`. Browser capability in THIS session:
`PLAYWRIGHT / CHROME_DEVTOOLS_MCP / HOST_BROWSER = UNAVAILABLE` (Playwright package installed, Chromium
build download blocked by the sandbox network; no system Chromium/`apt` path reachable).
Therefore:

- `RUNTIME_REVIEWED=YES` at the DOM-runtime level (real committed bundle executed in jsdom, real interactions,
  real emitted payloads) — classified `CONFIRMED_RUNTIME_FINDING` for behaviour/ownership;
- `VISUAL_VERDICT=NEEDS_EVIDENCE` for **pixel** desktop/mobile rendering; no screenshot is claimed here.
- Substitute human-verifiable surface: `tests/component/specimen_quote_line_note_clarity.html` served over
  HTTP (`python3 -m http.server 8088` from the repo root, then `/tests/component/specimen_quote_line_note_clarity.html`)
  renders the real bundle + real CSS with a two-line quote (`Q-SPEC-2LINES`, line 1 = A, line 2 = B) and prints
  the emitted `quote_edit`/`quote_create` payload under the app frame. Resize to 390×844 / 1440×900 to see the
  mobile 2-column and desktop 4-column card layout.

## Non-goals — verified untouched

- pricing / tax / margin / FX: `calculation` identical before/after a note-only edit (test §3 row 3);
- customer picker (`SearchPicker`) and the read-only edit customer: unchanged, still asserted by the #88 lane;
- quote workflow/status, navigation, routes: untouched (no diff in `App.tsx`, `Layout.tsx`, dispatcher, `core/…`, `views/…`);
- persistence model: per-line `note` only — `NEW_WRITERS=0`, `NEW_PERSISTED_FIELDS=0` (test §3 row 6);
- `tienthanhlog` untouched; no production/pilot database writes, no deployment, no secrets changed.

## Files changed

```
component/src/pages/SalesQuotes.tsx                              (UI: per-card identity + "Ghi chú dòng này")
component/dist/logi-shell.js, component/dist/logi-shell.css      (rebuilt bundle, committed)
tests/test_logi_quote_line_note_clarity_01.py                    (new backend lane, 6 tests)
tests/component/dom_acceptance_quote_line_note_clarity.mjs        (new DOM lane, 7 checks)
tests/component/dom_acceptance_internal_ux_simplify.mjs           (2 selectors updated, strength unchanged)
tests/component/specimen_quote_line_note_clarity.html             (new runtime specimen, evidence tooling)
reports/coder/rp_coder_260921_111700_by_arena-agent_logi-quote-line-note-clarity-01.md
```

## Return packet

```
TASK_ID=LOGI_QUOTE_LINE_NOTE_CLARITY_01
RESULT=PASS
P2P_LAW_SOURCE=LOCAL_PORTABLE
BASE_SHA=c088c0da424d25034b237f5a9cb78f1b66ee71cf
OE_VERDICT=DO_IT
PER_LINE_NOTE_UI=PASS (each card: visible "Dòng dịch vụ N" + "Ghi chú dòng này" inside the same card)
LINE_COUNT_NOTE_COUNT_MATCH=PASS (1↔1, 2↔2, 3↔3; no quote-level note exists)
TWO_LINE_DISTINCT_NOTES_PAYLOAD=PASS (serviceLines[0].note=A, [1].note=B, code/cost/sell/tax aligned)
TWO_LINE_DISTINCT_NOTES_READBACK=PASS (line1=A, line2=B in DOM, projection and fresh Mongo read)
EDIT_ONE_LINE_PRESERVES_OTHER=PASS (line2 B→B2: line1 STILL=A; line1 money + calculation identical)
DELETE_LINE_NOTE_ASSOCIATION=PASS (removing line 1 deletes only its note; survivor keeps its own note)
MOBILE_VISUAL=DOM-runtime structural PASS (2-col grid, 48 px target, badge+note inside card) / pixel NEEDS_EVIDENCE
DESKTOP_VISUAL=DOM-runtime structural PASS (md:grid-cols-4, badge precedes note inside card) / pixel NEEDS_EVIDENCE
QUOTE_CALC_UNCHANGED=PASS
NEW_WRITERS=0
NEW_PERSISTED_FIELDS=0
TYPECHECK=PASS
BUILD=PASS (deterministic, source-dist in sync)
SOURCE_DIST_SYNC=PASS
PR=(opened, DO NOT MERGE)
DEPLOYED=NO
NEXT_ACTION=RETURN_TO_CONTROL_TOWER
```
