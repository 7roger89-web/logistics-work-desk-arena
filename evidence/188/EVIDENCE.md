# Issue #188 — Journey Cockpit fresh-shipment production parity · runtime evidence

**Purpose.** Prove that the Owner-observed production failure (`journey.nodes=[]`
removed the approved cockpit and exposed the legacy vertical page) is repaired,
and that the populated shipment path did not regress, on ONE exact final HEAD.

**Actor self-law preflight (this executor, own receipt).**
`LAW_CHECK=PASS | SOURCE=.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md (LOCAL_PORTABLE) | SOURCE_SHA256=316936bc951a466c89cc8efb9291f9425571cf886199c8f4f4372be5d7c25ae4`
The portable projection's recorded `SOURCE_CONTENT_SHA256` equals the sha256 recorded
in its header block (projection verified in-repo). Canonical cross-repo law was not
probed, per the repo-scoped portable rule (`.p2p/system` carries no installed notebook).
`P2P_LAW_SOURCE=LOCAL_PORTABLE`.
`EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-b2611df4c9393f0017f07dcb`
(bounded lookup against `.p2p/portable/P2P-EXPERIENCE-CAPSULE.json`; the ACTIVE record's
triggers — actor receipt / preflight / portable / experience consumption — match this task).

**Start state.** `START_HEAD=cbd60e200dda3ca7a1d046df4c811de7b4a3f5fb` verified as the real
remote head of `ct/journey-fresh-parity-188` (`gh api .../git/refs/heads/ct/journey-fresh-parity-188`)
before any edit, and an ancestor of `main` = `a381a8ee9632c13d622d264c4009ac7ddf3e2a9f`.
Control Tower source changes were inspected as a diff before touching anything — no redesign,
no new workflow/store/state engine; the bounded repair is:

- `component/src/components/ShipmentJourney.tsx` — the zero-node early return now renders
  `FreshShipmentCockpit` (six universal phases, HỒ SƠ actionable, downstream UNKNOWN, no
  fabricated mode-specific nodes) instead of the legacy tiny fallback;
- `component/src/pages/ShipmentDetail.tsx` — `ShipmentCompletionGoals` moved AFTER
  `<ShipmentJourney>` so the approved cockpit is the primary surface;
- `tests/test_journey_fresh_parity_188.py` + the #186 composition assertion.

**Transport.** Isolated in-process `mongomock` staging only (`SANDBOX_STAGING`), the same
transport `scripts/verify_visual_shipment_workspace.py` already uses. No real `MONGO_URI`,
no `.env`, no production database, no deploy, no secrets, no `tienthanhlog`, no business
write outside the isolated staging transport.

**Browser.** Real Chromium `Chromium 153.0.8010.0` (`@sparticuz/chromium` 153.0.0 binary,
the same build family the #186 evidence used: `HeadlessChrome/153.0.8010.0`), driven by
`playwright-core` 1.63.0 in this throwaway sandbox harness. The rendered bytes are the EXACT
committed `component/dist` produced from this head. `chrome`/`playwright` binaries are not
committed to the repository — only the runner script and its screenshots are.

## 1. Typecheck · build · bundle scan (dist rebuilt FROM SOURCE, never hand-edited)

| Check | Command | Result |
| --- | --- | --- |
| typecheck | `npm run typecheck` (component) | PASS — `tsc --noEmit`, exit 0. **No compile/type defect needed repair**; the Control Tower patch compiles as-is. |
| build | `npm run build` (component) | PASS — Vite 8.2.2, 1914 modules |
| scan | `python3 scripts/scan_process.py component/dist` | `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0` |
| rebuild determinism | second `npm run build` | byte-identical output (same sha256), so the committed dist provably comes from this source |

`DIST_REBUILT=YES` from source. Hashes of the committed bundle:

```
563a690f11e414237e6346c028df02a6fbf2b751a562355f44ff067c5ef9be00  component/dist/logi-shell.js   (was 940cc11b… = #186 dist)
b6e06731f36a5c394a05a3451413f992fa5d3d307d486555f2ba0843e0dce151  component/dist/logi-shell.css  (was 6c9581d3… = #186 dist)
```

Bundle truth markers (count in `logi-shell.js`): `data-empty-journey` 1, `journey-empty-canvas` 1,
`journey-empty-primary-cta` 1, `BỔ SUNG HỒ SƠ` 1, `RÀ SOÁT HOÀN TẤT` 1,
`Chưa có công đoạn phù hợp` **0**.

## 2. Focused regressions + Prototype-B oracle

| Check | Command | Result |
| --- | --- | --- |
| #188 + #186 + #184 | `python3 -m unittest tests.test_journey_fresh_parity_188 tests.test_journey_super_goal_186 tests.test_journey_v3_customs_import_184` | `Ran 31 tests … OK` |
| Prototype-B geometry/oracle | `python3 scripts/verify_visual_shipment_workspace.py --fixture /tmp/sea160_fixture.json` then `node tests/component/dom_acceptance_journey_demo_fidelity.mjs /tmp/sea160_fixture.json component/dist/logi-shell.js` | **PASS demo B** — 11 exact approved positions, parallel group/routes, fit/zoom/reset/pan, drag guard, every node selection, right-side workspace, collapse/expand, global process, zero navigation writes |

`PROTOTYPE_B_ORACLE=PASS` against the REBUILT bundle (not the stale one).

## 3. Fresh-shipment acceptance fixture (production-shaped, no invention)

`scripts/verify_journey_fresh_parity_188.py` creates a NEW shipment through the SAME
canonical handler the Create Shipment screen uses (`vm.consume_phase_b_triggers` →
`shipment_create`) with no first mode, no Incoterm, no service scope, and then FAILS CLOSED
unless the persisted shipment is truthfully fresh. Served truth (`/fixture`):

```json
{"fixture":"FRESH_SHIPMENT_188","shipmentId":"SEA-188","persisted":true,"version":1,
 "journeyNodes":0,"profileState":"PROFILE_INCOMPLETE","profileStateLabel":"Hồ sơ lô còn thiếu",
 "serviceScope":[],"serviceScopeConfirmed":false,"firstMode":"","incoterm":"","transportLegs":0,
 "attentionItems":1,"primaryAction":"Bổ sung hồ sơ thực hiện lô",
 "nextActionDetail":"Chưa có điều kiện giao hàng (Incoterm)."}
```

So the DOM below belongs to a genuinely zero-node, scope-unconfirmed, mode-less shipment —
the DOM is not trusted on its own (`ZERO_NODE_COCKPIT`, `NO_FAKE_NODES` are asserted against
this server-side truth).

## 4. Real browser · fresh shipment desktop 1440×1000 — PASS (17 checks)

`FRESH_DESKTOP=PASS`

- Attention (**1 mục**, the same primary action) renders ABOVE the cockpit;
- cockpit visible with `data-empty-journey="true"`, 1128×972px, dominant on the first screen;
- **six phases** visible in order `HỒ SƠ · ĐẦU ĐI · CHẶNG CHÍNH · NHẬP KHẨU · GIAO HÀNG · HOÀN TẤT`;
- `HỒ SƠ` is `data-state="ACTION"` and enabled; the other five stay `UNKNOWN` **and disabled**;
- zero `journey-node-*` elements: no BOOKING / SI-VGM / GATE-IN / customs / delivery fabrication;
- empty/onboarding Journey canvas (START rail + "1/6 · HỒ SƠ" card + 5 dashed `Chưa xác định` chips) visible;
- right-side onboarding Quick Panel visible (`journey-side-panel` is provably to the RIGHT of the canvas);
- exactly ONE dominant CTA `BỔ SUNG HỒ SƠ →` (`journey-empty-primary-cta`), bound to the
  Execution Profile next action `Bổ sung hồ sơ thực hiện lô`;
- the old tiny `Chưa có công đoạn phù hợp…` fallback is absent from the DOM;
- legacy vertical page does NOT spill open: first screen contains Attention + Cockpit only,
  `journey-global-workspace` and `shipment-execution-profile` are not rendered by default;
- **Completion Goals comes AFTER the cockpit** (Attention y=501 → Cockpit y=687 → Goals y=1675 in the app scrollport);
- no horizontal overflow (page 0px, app scrollport 0px, body 1440px).

## 5. Real browser · fresh shipment 390×844 — PASS (4 checks)

`FRESH_390=PASS`

- same semantics: six phases, `HỒ SƠ` actionable, five `UNKNOWN` + disabled;
- dominant CTA inside the 390px viewport, canvas + Quick Panel still visible;
- zero fabricated nodes; Attention → Cockpit → Goals order preserved;
- **no horizontal overflow** (page 0px, app scrollport 0px, body 390px ≤ viewport 390px);
- cockpit remains understandable: onboarding card, "Tại sao chưa có node chi tiết?", `MỞ THÔNG TIN LÔ →`.

## 6. Real browser · populated shipment (entrusted-import / Prototype-B SEA-160) — PASS (11 checks)

`POPULATED_DESKTOP=PASS`, `POPULATED_390=PASS`

- approved **large horizontal map** with 11 factual detailed nodes — DOM count equals the
  server projection count (11), not a DOM marker claim;
- **parallel SI/VGM + Gate-in** branch present (`journey-parallel-branch`);
- right **Quick Panel → Stage Workspace**: exactly one panel column, workspace replaces the
  Quick Panel inside `journey-side-panel`, no duplicate Quick Panel;
- **Customs Import truthful panel**: registration and clearance are separate rows, the real
  blocker (`Bổ sung số tờ khai nhập khẩu.`) is surfaced verbatim, "Tạo GNT không đồng nghĩa đã
  nộp thuế.", suggested partner stays an unconfirmed suggestion, **ONE dominant CTA**
  (`XỬ LÝ NGAY` = the canonical primary-action label for this shipment);
- **B7 stays neutral**: exactly one `RÀ SOÁT HOÀN TẤT` terminal, dashed border, no
  emerald/green/red/amber colour class, no coloured fill, no `COMPLETED` text; the only `%`
  in the cockpit is the map zoom readout (61%);
- **B8 finance truth**: `finance.outstanding=null` and `partner.suggested=true` ⇒
  `completion-goal-finance[data-state=UNKNOWN]` with "UNKNOWN được giữ nguyên, không đổi
  thành 0/đã trả" — never fabricated as zero/paid/EVIDENCED;
- composition preserved: Attention → Cockpit → Completion Goals;
- 390px: 11 nodes, map usable, customs panel readable, **no horizontal overflow**;
- **zero application page errors** in both lanes.

## 7. Mutation control — the new deterministic lane actually detects the bug

`tests/component/dom_acceptance_journey_fresh_188.mjs` mounts the committed dist over a real
fresh-shipment projection (fixture committed at
`tests/component/fixtures/view_model_journey_fresh_188.json`, regenerable with
`python scripts/verify_journey_fresh_parity_188.py --dump-model <path>`).

| Bundle | Result |
| --- | --- |
| pre-patch `main` dist `940cc11b…` | **FAILS** — `AssertionError: cockpit shell must exist for journey.nodes=[]` (the Owner's production failure, reproduced) |
| this head dist `563a690f…` | **PASS** — shell kept, 6 phases (HỒ SƠ ACTION, 5 UNKNOWN), 0 fabricated nodes, 1 CTA, Attention → Cockpit → Goals, zero business writes |

The lane also executes inside the normal Python suite
(`tests/test_journey_fresh_parity_188.py::ZeroNodeRenderLane`, skipping only where node/jsdom
are unavailable), closing Issue #188 root cause C (coverage that proved labels existed but
never executed the zero-node render path).

## 8. Whole-suite DOM acceptance sweep — no regression

Full `tests/component/dom_acceptance_*.mjs` sweep, run twice with ONLY the bundle swapped:

| Bundle | lanes rc=0 |
| --- | --- |
| pre-patch `main` dist `940cc11b…` | 24 / 46 |
| this head dist `563a690f…` | **25 / 46** |

`diff` of the per-lane results shows exactly ONE difference: `dom_acceptance_journey_fresh_188.mjs`
rc=1 → rc=0. The other 45 lanes have identical outcomes on both bundles, so this patch
introduces no regression in the existing committed DOM lanes (the lanes that fail here fail
identically on the pre-patch baseline bundle — a pre-existing sandbox/baseline condition, not
this change; raw logs: `dom-sweep-baseline.txt`, `dom-sweep-head.txt`).

## 9. Screenshot sha256

```
44e62a6b3acad9aec37be39e2350d9377012fa1704da0cfa9023f77bf4782733  fresh-desktop-1-first-screen.png
30f66cb9dd6c107d38b4b1de12aed9c8aedee52d29bedb0c71b95f21292222d2  fresh-desktop-2-cockpit.png
bca0e35d06d089a12196e091f08f56d37bca001bdd7b7949e156c437ba7943da  fresh-desktop-3-onboarding-canvas.png
616f6a7f078af52a0535a028259ac44b17e69ac8834c640443bb1dbfd57dfb39  fresh-desktop-4-completion-goals-after-cockpit.png
194c3a973233f96773c56ec3569bc259f759fd1028abc26b53abeba77a0c8b49  fresh-mobile-390-1-first-screen.png
b3f59da156f67b310e204134e8d6a6e07ea1eaaa2f7685097787665644cc320f  fresh-mobile-390-2-cockpit.png
5f65708c0f4f00d89ce2feec53804101eaf47c88346e5bef8abb14797493ced0  fresh-mobile-390-3-onboarding-quick-panel.png
82f88fcb78476e54ed7b772e57aaa99a0db6b1bdb77517ca53e844a486c39007  fresh-mobile-390-4-completion-goals-after-cockpit.png
7ecde18402b408b9ed8253145a125f1047d27a58847b87fe547ff3ece4ffba90  populated-desktop-1-map-and-quick-panel.png
3af5c4070605f8140f4d70421efecae8d061e54735598d27d59e7d9d212a4438  populated-desktop-2-cockpit.png
794ca68ef6fd63154ca716b47ad2b0a8b9fdf470886f03dd2591a5bb0af4abf5  populated-desktop-3-customs-import-panel.png
8b1e8ac0453c2602eda55a28a5dcaca2c562403177e22390ee213a6eb2529d9a  populated-desktop-4-completion-goals.png
cc0e161a805ee3a939bf57e954fa898a15452485e7c57a3018d05e327c094c45  populated-mobile-390-1-map.png
ad52c024ddf097a34e0874c91a0fdd43d8c4a7fe6a10a4b5b3b02b24d85cd1a6  populated-mobile-390-2-customs-panel.png
```

## 10. Reproduce

```bash
# 0. toolchain
pip install -r requirements.txt                       # pymongo + mongomock (staging transport)
cd component && npm ci && npm run typecheck && npm run build && python3 ../scripts/scan_process.py dist && cd ..

# 1. deterministic lanes
python3 -m unittest tests.test_journey_fresh_parity_188 tests.test_journey_super_goal_186 tests.test_journey_v3_customs_import_184
node tests/component/dom_acceptance_journey_fresh_188.mjs
python3 scripts/verify_visual_shipment_workspace.py --fixture /tmp/sea160.json
node tests/component/dom_acceptance_journey_demo_fidelity.mjs /tmp/sea160.json component/dist/logi-shell.js

# 2. real browser (any browser-capable machine; binaries are NOT committed)
PLAYWRIGHT_MODULE=/path/playwright-core/index.mjs \
CHROMIUM_EXECUTABLE=/path/chromium CHROMIUM_LIB_PATH=/path/chromium/libs \
node tests/component/browser_journey_fresh_parity_188.mjs ./evidence/188 all
```

## 11. Boundary

`MERGE_TO_MAIN => STREAMLIT_PRODUCTION_DEPLOY_TRIGGER`. Not merged, not deployed, no
production business writes, no secrets, `tienthanhlog` untouched, **no Human UAT claimed**.
`FINAL_HEAD` / `FINAL_TREE` and the branch position are bound in the PR #189 comment and in
the commit that adds this evidence. Independent read-only Supervisor is still required
before any merge decision.
