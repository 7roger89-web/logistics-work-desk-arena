# Issue #190 — visual-fidelity evidence vs the OWNER SAMPLE (final loop)

Branch: `arena/12974a76-logistics-work-desk-arena` (product head `944ddae` + evidence/fix commits)
PR under review: #191 (`ct/journey-visual-fidelity-190`)
Runtime: real Chromium 110.0.5478.0 (`/tmp/chr110`, sandbox-only), mongomock SANDBOX_STAGING host
(`scripts/verify_visual_shipment_workspace.py`, SEA-160, 11 journey nodes), viewport 1536×1466.
NO real MongoDB, NO production writes, NO secrets, NO merge, NO deploy.

## 1. The Owner sample (source of truth for visible composition)

- Fetched from PR #191 head `6f6c655c07c7a5960b7344768a05f9ebb29b8037` ("Issue #190: add owner
  visual reference to task branch"), blob `26bf1ee2d08ddf1ca966d92207782af7dc993b5c`,
  saved as `evidence/190/reference-original.png` (sha256 `62b0f7f4…dbb9a`, 1536×1466 RGB).
- NOTE on that commit: its TREE contains ONLY the PNG (parent = 944ddae). It is a transport
  commit for the sample, not a product tree; the session branch therefore did NOT rebase onto
  it (doing so would delete ~1158 product files). The sample was extracted by blob only.
- The banner inside the sample identifies it as the PR177 RECONSTRUCT HARNESS, case UY-THAC,
  map geometry per 70fd361, demo state in-memory only — i.e. the approved visual oracle.

### Reference geometry (pixel-segmentation measurement, `scripts/measure_reference_190.py`)

| block | page coords (px) | note |
|---|---|---|
| identity/header bar | y 28..109 (h 81) | ONE white bar: brand+lot+chip, route line, right controls |
| attention band | y ≈124..188 (h ≈64) | ONE tinted row: [CẦN XỬ LÝ (n)] title+reason · [XỬ LÝ →] · other-attention chips |
| journey row | y 205..922 (h 718) | map card x 17..1055 (w 1039) · gap 12 · right panel x 1068..1519 (w ≈451) |
| five summary cards | y 937..1420 (h ≈484) | 5 equal columns w ≈289, gaps 12, full fact rows, tall whitespace |
| footer note | y ≈1446..1462 | harness caption line |
| node cards | ≈153×122 rendered | = logical 164×136 at the sample's 91 % fit zoom |

## 2. Candidate after the fix loop (`candidate-populated-desktop.png`, same viewport)

`geometry-190.json` (30 harness checks PASS, all lanes):

| block | candidate value | reference value | verdict |
|---|---|---|---|
| attention | ONE tinted band h≈50, badge+title+reason+XỬ LÝ+chips | band h≈64 same anatomy | MATCH (composition) |
| journey split height | 718 px | 718 px | MATCH |
| right Quick Panel | 450 px | ≈451 px | MATCH |
| map width | 772 px | 1039 px | shell-derived (production sidebar+toolbar own ≈284 px; oracle allows production shell) |
| map/panel ratio | 1.716 | 2.30 | shell-derived (panel width matches; total width does not) |
| node logical size | 164×136 ×11/11 oracle-exact | 164×136 | MATCH |
| five cards | 5 columns, gaps 12, full fact rows + footer link, END inside 1466 | 5 columns, gaps 12, tall | MATCH (height content-driven, see §4) |
| first screen order | attention → journey(map+panel) → cards (fully visible) → Completion Goals below fold | same order, all inside 1466 | MATCH |

## 3. Product changes made ONLY because the rendered mismatch proved them

- `component/src/index.css` — split 760→718, rail 420→450 (sample-measured constants).
- `component/src/pages/ShipmentDetail.tsx` — compact identity bar (row 1: back·lot·state·dense
  #86 quick-facts·journey controls; row 2: customer·route·update·disclosure toggle), slim tabs,
  compact AttentionNow, journey controls forwarded as counters; NOTHING deleted (facts stay
  visible per #86, secondary facts stay behind the collapsed disclosure).
- `component/src/components/AttentionNow.tsx` — new single-row compact band (card list kept for
  Home); sr-only band/action labels keep the #166 link contracts machine-readable.
- `component/src/components/ShipmentJourney.tsx` — populated view starts at the map+panel split
  (section header row removed; empty modules row removed; zero-module attach entry moved to the
  identity bar via `attachRequest`); summary cards project the sample's fact rows from real
  view-model fields only (booking/cut-off/ETD/carrier/vessel·voyage, ETA/ATA, declaration/
  clearance/tax/VAT, 8 delivery rows, customer/form/incoterm/scope) + delivery footer link.
- `component/src/components/JourneyQuickPanel.tsx` — white header, action CTA INSIDE the red
  "CẦN LÀM NGAY" box, "THÔNG TIN CHÍNH" factual rows (importer, declaration, clearance, tax,
  VAT, GNT, China-agent CNY payable/paid from the canonical C2B block; UNKNOWN stays red text,
  never 0).
- Acceptance scripts updated for the moved controls (documented in-file): Prototype-B oracle,
  #160 dom, #162 dom+browser (zero-module attach entry), 190 harness constants (450/718,
  cards-inside-first-screen, #86 facts visibility).

## 4. Residual deltas — classified, NOT "looks close"

1. Shell chrome (left nav + top toolbar) exists; the sample is a standalone harness page.
   Oracle rule: "app shell may remain the production shell".
2. Map width / ratio differ because the sidebar owns horizontal space (panel width matches).
3. Identity bar = 2 rows + slim tab row (production navigation) vs the harness' single bar.
4. Card height ≈400 vs ≈484: the sample's extra height is demo-only delivery-note copy
   ("Xe >2.5T tránh khung… (gợi ý demo — GAP G05)"); we render no invented notes.
5. Fit zoom 67 % vs 91 % (smaller canvas); node logical geometry unchanged and oracle-exact.
6. Quick Panel opens ARRIVAL (first factual PROBLEM node of SEA-160) vs the sample's NHẬP KHẨU
   (first PROBLEM node of its demo case) — same selection rule, different data.
No intentional layout/styling difference remains inside the Journey content region.

## 5. Regression matrix (this branch)

| suite | result |
|---|---|
| TEST_190 / 188 / 186 / 184 (pytest) | 7/7 · 7/7 · 9/9 · 16/16 = 39 passed |
| 190 harness, all lanes (real Chromium) | 30 checks PASS (donor reconstruction, populated, list alerts, fresh, 390px, completion collapsed/expanded, global workspace) |
| 188 browser parity | 31/31 PASS |
| Prototype-B DOM geometry oracle | PASS (11 exact positions, zero business writes) |
| #160 dom, #166 dom | PASS |
| typecheck / build / executable-process scan | PASS / PASS / 0 hits |
| PRE-EXISTING at base 944ddae (verified via `git worktree` build): glanceable #86 dom (`clickable "LO-0308"`), #162 dom (`/Next Action/`), browser-162 (guidance waitFor timeout) | identical failures on base and here — not regressions of this loop |

## 6. Artifacts

`reference-original.png` · `candidate-populated-desktop/-journey/-fullpage/-390.png` ·
`fresh-desktop.png`, `fresh-390.png` · `completion-collapsed/expanded.png` ·
`global-workspace-expanded.png` · `shipment-list-alerts.png` ·
`reference-donor-reconstruction*.png` · `side-by-side-populated-ref.png` ·
`overlay-populated-ref.png` · `diff-populated-ref.png/.json` · `geometry-190.json` ·
`reference-measure.json` · `scripts/measure_reference_190.py` ·
`scripts/compare_journey_visual_190.py` · `tests/component/browser_journey_visual_fidelity_190.mjs`
