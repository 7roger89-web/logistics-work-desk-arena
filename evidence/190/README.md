# LOGI #190 — B1/B2/B3 blocker-closure evidence

This directory is the durable real-browser packet for Issue #190 / PR #191.

- Fixed session branch: `arena/fae8f805-logistics-work-desk-arena`
- Product/test/dist commit under capture: `f604d71547dea9a8b6f7cba2607bca555a5adb3d`
- Integrated parent: `92f012d1f726b1a6db02462c2e57046f8da96ccb`
- Owner reference: `reference-original.png`, 1536×1466, SHA-256
  `62b0f7f4960334ed0880a5908f7138b2f4f0296ccf7ea76ea9421251bd6fbb9a`
- Runtime: real Chromium `110.0.5478.0`; visible layout scrollbars enabled.
- Data: canonical isolated mongomock staging hosts only. No production database,
  production write, deploy, merge, secret exposure, or human-UAT claim.

`EVIDENCE.md` is the exact hash manifest and product-head binding.
`geometry.json` is the standardized machine-readable record for all populated,
list, fresh, desktop, and 390px lanes (33 passing runtime checks).

## B1 — Customs Import Quick Panel

The specialized panel now follows the existing `JourneyQuickPanel.tsx` pattern:
fixed header and declaration lead, one bounded scrolling middle, and one fixed
bottom workspace footer. No panel framework was added.

Measured in real Chromium against canonical SEA-160:

| Contract | Runtime result |
|---|---|
| source/visual order | `ci-next-action` y=272.44 before `ci-registration-clearance` y=488.47 |
| action counts | 1 `ci-next-action`; 1 `ci-primary-cta`; 1 `ci-open-workspace` |
| dominant action styling | red surface `rgb(254,242,242)`; red border `rgb(228,0,20)` |
| bounded middle | `clientHeight=551`, `scrollHeight=685`, scrolled 134px |
| pinned footer | y=811.86 before and after the 134px internal scroll |
| navigation | `ci-open-workspace` opened the existing Stage Workspace |
| write safety | opening the panel/workspace and scrolling emitted 0 `/event` writes |

Evidence:

- `quick-panel-action-order.png` — complete top hierarchy, including the one
  dominant action before declaration/clearance facts.
- `quick-panel-pinned-footer.png` — middle scrolled to the supplementary facts
  while the sole bottom workspace action remains pinned.

Truth boundaries remain explicit: declaration registration is not customs
clearance; generated GNT is not tax payment; catalog suggestion is not payable;
unknown money is not converted to zero and no FX total is fabricated.

## B2 — accidental first-screen overflow and exact desktop geometry

### Identified scrollport and cause

The overflowing element was `.logi-shell`, the app's actual scrollport. Before
this repair it measured `clientHeight=1409`, `scrollHeight=1476`: 67px of
accidental vertical overflow. DOM bboxes showed the zero-module setup row below
the five summary cards extending the Journey, while `.focus-shell` inherited a
nested `min-h-screen` minimum. Chromium's visible vertical scrollbar then
consumed layout width and reduced the map.

### Bounded repair

- Desktop `.focus-shell` overrides the nested minimum with `min-height:100%`.
- The empty optional-module strip is absent by default, but its same canonical
  setup remains reachable through `HỒ SƠ & PHẠM VI → Thông tin thêm`; revealing
  it is navigation-only and emitted zero writes. Existing attached modules still
  render normally.
- Desktop focus gutters are 17px and the Quick Panel is 451px.
- No global scrollbar hiding, clipping, mobile-scroll disabling, logical-node
  change, `DEMO_POS` change, business schema, or workflow engine was introduced.

### Post-fix real-Chromium measurement, 1536×1466

| Metric | Result | Target |
|---|---:|---:|
| `.logi-shell` client / scroll | 1536×1409 / 1536×1409 | no accidental overflow |
| vertical / horizontal overflow | 0px / 0px | 0px / 0px |
| map | 1039×718px | ≈1039×718px |
| Quick Panel | 451×718px | ≈451×718px |
| gap | 12px | 12px |
| map/panel ratio | 2.304 | ≈2.304 |
| fit scale | 0.90704 (91%) | ≈91% |
| node logical geometry | 164×136, all 11 oracle positions exact | unchanged |
| node rendered bbox | 148.8×123.4px | sample-segmentation ≈153×122px |
| five-card gaps | 12/12/12/12px | 12px |

The rendered-node difference is the direct, internally consistent consequence
of immutable 164×136 geometry at a 0.90704 fit scale; it is not described as an
antialiasing delta.

## B3 — durable required states

| Required state | Artifact / proof |
|---|---|
| populated desktop | `candidate-populated-desktop.png` |
| populated Journey crop / full page | `candidate-populated-journey.png`, `candidate-populated-fullpage.png` |
| populated 390, no horizontal overflow | `candidate-populated-390.png` |
| fresh desktop, truthful zero-node | `candidate-fresh-desktop.png`, `candidate-fresh-desktop-cockpit.png` |
| fresh 390 at true scroll top | `candidate-fresh-390-top.png`: `scrollTop=0`, identity, attention, six-phase strip, canvas entrance |
| fresh 390 onboarding action | `candidate-fresh-390-onboarding.png`: visible HỒ SƠ action |
| Completion Goals toggle | `completion-collapsed.png`, `completion-goals-expanded.png`; 703px details only after click |
| Customs Quick Panel order/footer | `quick-panel-action-order.png`, `quick-panel-pinned-footer.png` |
| Global Workspace | `candidate-global-workspace.png`: 208px map rail + 1282px workspace |
| normal non-detail shell | `candidate-other-route-home.png`: topbar and sidebar retained |
| urgent/nonurgent list | `shipment-list-alerts.png`, `shipment-list-alerts-fullpage.png` |
| owner comparison | `side-by-side-populated-ref.png`, `overlay-populated-ref.png`, `diff-populated-ref.png/.json` |
| geometry and reference probes | `geometry.json`, `reference-measure.json` |

The list fixture proves canonical urgent bands on LO-0306, LO-0308, and LO-0295
(all `OVERDUE`) and no band on LO-0299, LO-0307, and SEA-160. LO-0307 contains
free-time wording but remains nonurgent, proving no urgency inference from text.

The raw pixel comparator reports mean absolute RGB difference
`21.77/25.78/23.41` and 16.67% changed pixels at threshold 24. This is retained
as an honest content-sensitive diagnostic, not misrepresented as a visual
acceptance score: the Owner demo and canonical staging fixture contain different
truthful labels/facts. The measured layout geometry above is the acceptance
oracle.

## Gate matrix

| Gate | Result |
|---|---|
| TypeScript | PASS — `tsc --noEmit` |
| committed Vite build | PASS — 1,914 modules; dist rebuilt |
| executable-process scan | PASS — `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0` |
| Issues #190/#188/#186/#184 focused pytest | PASS — 41 passed |
| Prototype-B DOM geometry oracle | PASS — 11 exact positions, routes/interactions, zero navigation writes |
| Issue #190 real Chromium all lanes | PASS — 33 checks |
| Issue #188 real Chromium desktop/mobile | PASS — 31 checks |
| mobile horizontal overflow | PASS — 0px, populated and fresh 390px |
| `git diff --check` / harness syntax | PASS |

The #188 runner's B7 assertion was corrected to recognize the source-contract
`bg-white` terminal as neutral (as well as transparent), while still rejecting
semantic green/red/amber fills. Product B7 remains the dashed slate
`RÀ SOÁT HOÀN TẤT`; B8 finance remains `UNKNOWN`.

## Scope / OE gate

**Không bị over engineering chứ?**

- `SIMPLER_PATH`: used the existing Quick Panel flex/footer pattern and existing
  HỒ SƠ disclosure; no new abstraction.
- `MATERIAL_PROGRESS`: directly closes the rejected hierarchy/footer, overflow,
  geometry, and evidence states.
- `NECESSITY`: every product delta maps to B1 or B2; B3 changes are acceptance
  harness/evidence only.
- `CORE_BEFORE_SUPPORT`: fixed source → rebuilt dist → rendered/measured before
  producing comparator/docs.
- `SMALLER_VERIFIABLE_SLICE`: four product/source files plus focused tests; no
  backend/schema/geometry redesign.

`OE_VERDICT=DO_IT` — this is the smallest measured repair that preserves all
existing capabilities and truth authorities while closing the three blockers.
