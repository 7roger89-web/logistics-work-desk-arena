# LOGI #199 — final bounded Owner-fidelity fix A/B

Baseline: `abf3c0edca0e0c24e7cba840ca2923623454653e`.
Branch: `arena/d657fb56-logistics-work-desk-arena` (unchanged).
Only A (mobile initial camera) and B (meaningful OLD→NEW test) are in scope.
No G0–G5 rerun, redesign, merge, production deploy, or business/auth/API changes.

## Actor-own receipts

- `P2P_LAW_SOURCE=LOCAL_PORTABLE`
- `LAW_CHECK=PASS | SOURCE=LOCAL_PORTABLE | SOURCE_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`
  (recorded `SOURCE_CONTENT_SHA256`; no installed notebook, no canonical probe).
- `EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-b2611df4c9393f0017f07dcb`
  (portable ACTIVE advisory, no permission/acceptance authority).
- Read root AGENTS.md, portable notebook, ACTIVE capsule, skill and existing Owner visual override.
- `INITIAL_PLANNING_CLASSIFICATION=UIUX`; `FINAL_ROUTING_CLASSIFICATION=UIUX`.

```json
{"schema":"p2p-skill-consumption-receipt/1","skills":[{"id":"p2p-uiux","path":".agents/skills/p2p-uiux/SKILL.md","sha256":"98f26873e48cc87e34d132478f73672a80d20b3a8e1a2256bdcdab4d6107e7b2","consumption":"READ_AND_APPLIED"}]}
```

`Không bị over engineering chứ?`
`SIMPLER_PATH=YES` (existing map, no new camera framework),
`MATERIAL_PROGRESS=YES`, `NECESSITY=YES`, `CORE_BEFORE_SUPPORT=YES`,
`SMALLER_VERIFIABLE_SLICE=YES` (A/B only).
`OE_VERDICT=DO_IT`: change initial camera and challenge a real changed value;
no larger campaign. Evidence level: `RUNTIME_VISUAL_REVIEW`, provider `PLAYWRIGHT`.

## A — mobile initial camera: PASS in Chromium

Root cause: mobile `auto()` called `readable()`, which prioritizes a real
PROBLEM/current node. For T6-FCL that centered ARRIVAL, showing
TRANSIT → ARRIVAL → CUSTOMS IMPORT instead of the route's beginning.

Bounded source fix in `JourneyMap.tsx`:
- Fresh, unselected mobile auto view anchors the first actual node 24px inside
  the canvas (plus 1px canvas border). No artificial node or state.
- Scale remains **100%**, title effective size **11px**, existing vertical
  anchor retained. This is a framing correction, not pixel-identical donor
  geometry: CUSTOMS EXPORT is partially visible at the right edge (69px).
- `Đọc rõ` retains selected/problem/current focus; on this fixture it centers
  the actual PROBLEM node ARRIVAL. Selection after that centers DELIVERY.
- Desktop still fits all 11 nodes (95% displayed scale). All 20 real edges remain.
- Paper texture, grid, palette, node styles, API, auth and business status logic
  are unchanged relative to baseline.

| Evidence at 390×844 | File |
|---|---|
| BEFORE (historical capture preserved from previous packet) | `mobile-before-initial.png` |
| AFTER (fresh real Streamlit capture) | `mobile-after-initial.png` |
| Labeled before/after | `mobile-before-vs-after.png` |
| One tap `Đọc rõ` → actual problem ARRIVAL | `mobile-after-doc-ro-problem.png` |
| Selection focuses DELIVERY | `mobile-after-select-focus-delivery.png` |

`metrics.json`: initial visible IDs = `booking`, `pickup`, `customs-export`;
11 nodes / 20 edges; `translate(-18px,121px) scale(1)`; no page errors.
Real CDP touch pan Δx=240px; zoom tap 1→1.2; Fit scale 0.238356.
`A_VERDICT=PASS` requires initial framing, real problem focus, selected DELIVERY
centered and pan/zoom/Fit checks (not simply a nonempty selected array).
Far-node selection is explicitly a DOM-dispatched click to challenge camera
focus; zoom/Fit, task opening and saving in B use actual touch taps.

## B — genuine OLD→NEW save/reload/readback: PASS in Chromium

Final authoritative capture (not the earlier same-value test):

| Step | Observed value | Screenshot |
|---|---|---|
| Read current persisted OLD in ON BOARD editor | **2026-10-11** | `mobile-save-before-old.png` |
| Fill a valid, different NEW | **2026-10-04** | `mobile-save-filled-new.png` |
| Tap Save → reload app/lot → reopen editor | **2026-10-04** | `mobile-save-readback-new.png` |

Visual comparison: `save-old-to-new.png`.
`changed=true`; `seeded_old_first=false` in the final capture;
`B_VERDICT=PASS` only if readback == NEW **and** readback != OLD.
The harness chooses a different valid date based on the actual current field,
refuses same-value saves as PASS, and exits nonzero for either failed A or B.
Previous runs used the alternate direction; only the final metrics and final
screenshots listed here are authoritative for this packet.

Environment: **real Streamlit app, official source-built dist, Chromium
153.0.8010.0**, 390×844 and desktop 1440×900, isolated in-process Mongomock.
Launcher `scripts/logi199_t6_staging_app.py` emitted:

```text
STAGING_ISOLATION_PROOF=PASS transport=SANDBOX_STAGING client=Mongomock db=logistics_staging real_uri=NO production_client=NO
```

No real DB/payment write. The final run uses Fit → touch-tap ON BOARD →
Đọc rõ → touch-tap task → fill → touch-tap Save, then full page navigation
and canonical readback, not a local form-state assertion.

## Build, regression and provenance

- `npm run typecheck`, official `npm run build`, `npm run scan`: PASS.
- Verification rebuild byte-identical to browser-captured dist.
- JS SHA-256: `121bbc3c6090b4cdd0aa576a6e9b29a0976f0bf6f6c35360512b5ee6cac5ca9b`.
- CSS SHA-256: `cd690366fbc18ed63db3b4af8ffe0b75b971e0bcfffac3c03cc0729cfa43a4ab`
  (unchanged from baseline).
- Focused existing Journey / LOGI199 regressions + new initial-camera pin:
  **106 passed**. Not a full-suite/release claim.
- Official-dist zero-node DOM variants (`nodes=[]`, absent Journey): PASS.
- Same-instance hook transitions (zero→populated / populated→zero): PASS.
- Runtime capture: `capture_fix_ab.py`; exact tested source, dist and harness
  SHA-256s recorded at capture time in `metrics.json`.
  `capture_base_head` is baseline `abf3c0e…`; the tested working files were
  uncommitted at capture time. File hashes, rather than a false capture-HEAD
  equivalence claim, bind them to the delivered commit.
- Before image provenance: previous packet `evidence/logi-199-restore/`;
  final AFTER and OLD→NEW images were freshly captured in this slice.

Some harness-only probes needed correction: a zoom tap immediately following
CDP touch-pan did not increase the scale in the first added challenge. Zoom/Fit
was then independently exercised before CDP pan; the final record has actual
1→1.2 zoom and 240px pan. No product logic was changed to bypass this probe.

## Original Owner HTML — unchanged, offline

[Download the original HTML](../../reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html)
(Save/open locally in Chromium; no server needed).
SHA-256 `26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f`.
JPEG asset SHA-256 remains
`e3cb46df825b3a9d5427aa734113f2975ca7c25cd52a2ff1eeb780008d040627`.
Neither the HTML nor the paper/grid implementation was modified in this slice.

## Boundary / reconciliation

A/B implementation + runtime evidence: **PROVEN within isolated staging**.
Owner-device testing, independent review, full release certification: **not
claimed**. No G0–G5 recertification. No merge main or production deploy.
`LEARNING_RECONCILIATION=CANDIDATE`: trigger = persistence acceptance tests;
require OLD != NEW and authoritative reload/readback == NEW before PASS.
Evidence = the prior same-value test rejection and this packet's real state
transition. Advisory candidate only, no self-promotion into shared law/skills.
