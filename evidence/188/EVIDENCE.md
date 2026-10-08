# Issue #188 — Journey Cockpit fresh-shipment production parity · runtime evidence

**Purpose.** Prove that the Owner-observed production failure (`journey.nodes=[]`
removed the approved cockpit and exposed the legacy vertical page) is repaired,
that the Independent Supervisor blocker **B1** (profile onboarding action reached the
wrong tab) is closed, and that the populated shipment path did not regress, on ONE
exact final HEAD.

**Round history.**

- **Round 1** (superseded for B1 acceptance by Control Tower `CONTROL_TOWER_BOUNDED_REPAIR_02`,
  2026-10-08T00:20:58Z): started at `START_HEAD=cbd60e200dda3ca7a1d046df4c811de7b4a3f5fb`,
  rebuilt dist + browser evidence, final head of that round `cf3755075faf1bc25fb8b20ac0a76dae3b383a5f`.
  Supervisor verdict REJECT with blocker B1. Its dist/fixture/browser evidence is **superseded**,
  not deleted: the sections below are re-run and re-bound to the Round-2 head.
- **Round 2 (this document, authoritative)**: bounded verification of the Control Tower B1
  correction, started at `START_HEAD=8925b8784462a488a247c1bbeb1219d7b4cdb90b` (verified as the
  exact remote head of `ct/journey-fresh-parity-188` before any edit; ahead of
  `main=a381a8ee9632c13d622d264c4009ac7ddf3e2a9f` by 10, behind by 0).

**Actor self-law preflight (Round-2 executor, own receipt).**
`LAW_CHECK=PASS | SOURCE=.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md (LOCAL_PORTABLE) | SOURCE_SHA256=316936bc951a466c89cc8efb9291f9425571cf886199c8f4f4372be5d7c25ae4`
The portable projection's recorded `SOURCE_CONTENT_SHA256` equals the Control-Tower-supplied
`CANONICAL_LAW_SHA256`/`TARGET_LAW_SHA256` (projection current). Canonical cross-repo law was not
probed, per the repo-scoped portable rule. `P2P_LAW_SOURCE=LOCAL_PORTABLE`.
`EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-b2611df4c9393f0017f07dcb`
(bounded lookup against `.p2p/portable/P2P-EXPERIENCE-CAPSULE.json`; the single ACTIVE record's
triggers — actor receipt / preflight / portable / experience consumption — match this task).

**Scope guard honoured.** No redesign, no router/framework, no new workflow/store/engine,
no dist hand-editing, no merge, no deploy. Product source was NOT touched by this verifier;
the only source change in Round 2 is in **test/verification artifacts** (see §6), made because
the Round-2 run proved those assertions were observing an impossible channel.

**Transport.** Isolated in-process `mongomock` staging only (`SANDBOX_STAGING`), the same
transport `scripts/verify_visual_shipment_workspace.py` already uses. No real `MONGO_URI`,
no `.env`, no production database, no deploy, no secrets, no `tienthanhlog`, no business
write outside the isolated staging transport.

**Browser.** Real headless Chromium `153.0.8010.0` (`@sparticuz/chromium` 153.0.0 x64 build,
same version family as Round 1), driven by Node `playwright` 1.x in this throwaway sandbox.
The sandbox has no browser and no apt/CDN access, so the Chromium binary's three missing
dynamic deps (`libnspr4`, `libnss3`, `libnssutil3`) were satisfied by building Mozilla
NSPR 4.36 + NSS 3.109 **from the official GitHub mirrors** and passing them through the
lane's existing `CHROMIUM_LIB_PATH` (browser-only `LD_LIBRARY_PATH`) contract. Nothing
browser-related is committed. The rendered bytes are the EXACT `component/dist` rebuilt from
this head.

## 1. Typecheck · build · bundle scan (dist rebuilt FROM SOURCE, never hand-edited)

| Check | Command | Result |
| --- | --- | --- |
| typecheck | `npm run typecheck` (component) | PASS — `tsc --noEmit`, exit 0. The B1 patch had no compile/type defect. |
| build | `npm run build` (component) | PASS — Vite 8.2.2, 1914 modules |
| rebuild determinism | second `npm run build`, byte compare | **byte-identical** (`cmp` equal) ⇒ committed dist provably comes from this source |
| scan | `python3 scripts/scan_process.py dist` | `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0` (js 1 327 872 chars, css 79 873 chars, 0 executable hits) |

`DIST_REBUILT=YES`. Round-1 committed bundle at `8925b878` was **stale** (it pre-dated the B1
source change); after rebuild:

```
9d8f10e23d258dcb64063fa20361a75fd2a349eeecdd2a3ee96ca150f421c406  component/dist/logi-shell.js   (was 563a690f… = Round-1 dist)
b6e06731f36a5c394a05a3451413f992fa5d3d307d486555f2ba0843e0dce151  component/dist/logi-shell.css  (unchanged: B1 touched no styles)
```

Bundle truth markers (count in `logi-shell.js`): `data-empty-journey` 1, `journey-empty-canvas` 1,
`journey-empty-primary-cta` 1, `BỔ SUNG HỒ SƠ` 1, `RÀ SOÁT HOÀN TẤT` 1,
`Chưa có công đoạn phù hợp` **0**.

## 2. Focused regressions + Prototype-B oracle

| Check | Command | Result |
| --- | --- | --- |
| #188 + #186 + #184 | `python -m pytest tests/test_journey_fresh_parity_188.py tests/test_journey_super_goal_186.py tests/test_journey_v3_customs_import_184.py -q` | **32 passed** (was "31 tests" in Round 1; +1 = the Round-2 fixture-route pin) |
| fresh zero-node DOM lane | `node tests/component/dom_acceptance_journey_fresh_188.mjs` | PASS — shell kept, 6 phases (HỒ SƠ ACTION, 5 UNKNOWN), 0 fabricated nodes, CTA reaches the Execution Profile on `tab=van-tai` inside the Global Workspace with a post-mount reveal, zero writes |
| Prototype-B geometry/oracle | `python scripts/verify_visual_shipment_workspace.py --fixture /tmp/sea160.json` then `node tests/component/dom_acceptance_journey_demo_fidelity.mjs /tmp/sea160.json component/dist/logi-shell.js` | **PASS demo B** — 11 exact approved positions, parallel group/routes, fit/zoom/reset/pan, drag guard, every node selection, right-side workspace, collapse/expand, global process, zero navigation writes |

`PROTOTYPE_B_ORACLE=PASS` against the REBUILT bundle.

## 3. Fresh-shipment acceptance fixture (regenerated through the canonical handler)

`scripts/verify_journey_fresh_parity_188.py` creates SEA-188 through the SAME canonical handler
the Create Shipment screen uses (`vm.consume_phase_b_triggers` → `shipment_create`) with no first
mode, no Incoterm, no service scope, and then FAILS CLOSED unless the persisted shipment is
truthfully fresh. Regenerated on this head (`--dump-fixture`, raw copy committed as
`fixture-truth-188.json`; `--dump-model` refreshes the DOM-lane fixture):

```json
{"fixture":"FRESH_SHIPMENT_188","shipmentId":"SEA-188","persisted":true,"version":1,
 "journeyNodes":0,"profileState":"PROFILE_INCOMPLETE","profileStateLabel":"Hồ sơ lô còn thiếu",
 "serviceScope":[],"serviceScopeConfirmed":false,"firstMode":"","incoterm":"","transportLegs":0,
 "attentionItems":1,"primaryAction":"Bổ sung hồ sơ thực hiện lô",
 "projectedPrimaryRoute":"/lo-hang/SEA-188?tab=van-tai#shipment-execution-profile",
 "nextRoute":"/lo-hang/SEA-188?tab=van-tai#shipment-execution-profile",
 "nextAction":"Bổ sung hồ sơ thực hiện lô","nextActionDetail":"Chưa có điều kiện giao hàng (Incoterm)."}
```

Every mission-required fixture fact is proven: `persisted=true`, `PROFILE_INCOMPLETE`,
`serviceScopeConfirmed=false`, `serviceScope=[]`, `firstMode=""`, `journeyNodes=0`, and the
projected primary route uses `tab=van-tai` + `#shipment-execution-profile` — the tab that owns
`ShipmentExecutionProfile` (`ShipmentDetail.tsx` mounts it only for `tab === "van-tai"`).

**Stale-fixture finding (why regeneration was mandatory).** The fixture committed at `8925b878`
still carried the pre-B1 route `/lo-hang/SEA-188?tab=lay-hang#shipment-execution-profile`
(plus a 07/10 timestamp). With that fixture the corrected bundle selects `lay-hang` and the
profile editor never mounts — i.e. the committed evidence input contradicted the committed
correction. `tests/test_journey_fresh_parity_188.py::ZeroNodeRenderLane` now pins
`row["nextRoute"]`/`primaryAction.route`/`meta.projectedPrimaryRoute` so a stale fixture fails
closed instead of silently passing.

## 4. Real browser · Supervisor B1 runtime challenge — PASS

`FRESH_DESKTOP=PASS`, `FRESH_390=PASS` (raw lane log: `browser-lane-run.txt`, machine-readable
summary: `acceptance-188.json`; 20 fresh-lane checks).

Before the click (fresh default, both viewports):
- cockpit visible (`data-empty-journey="true"`, 1128×972px at 1440), Attention above it;
- profile editor **NOT** auto-opened: `journey-global-workspace` and
  `shipment-execution-profile` absent; first screen = Attention + Cockpit only;
- zero business writes on load; zero page errors.

Desktop 1440×1000, click **`BỔ SUNG HỒ SƠ`** (`journey-empty-primary-cta`):
- selected query tab = `van-tai` — observed as the single `aria-pressed="true"` tab inside the
  Cockpit Global Workspace (6 tabs, exactly 1 pressed);
- Journey Global Workspace opens;
- `shipment-execution-profile` mounted **inside** `journey-global-workspace`;
- anchored reveal lands on the mounted editor (`scrollIntoView` recorder: last target =
  `shipment-execution-profile`, not the `workspace-tabs` fallback) ⇒ the reveal happens after
  the selected tab mounted;
- no business write from navigation; no page error; no horizontal overflow.

390×844, fresh default again, click the **`HỒ SƠ` phase** (`journey-phase-profile`):
- same four truths: `tab=van-tai`, Global Workspace visible, `shipment-execution-profile`
  mounted and readable inside it, reveal after mount;
- no horizontal page overflow (page 0px, app scrollport 0px, body 390px); no business write;
  no page error.

## 5. Real browser · populated regression (entrusted-import / Prototype-B SEA-160) — PASS

`POPULATED_DESKTOP=PASS`, `POPULATED_390=PASS` (11 populated-lane checks).

- approved **large horizontal map** with **11 factual detailed nodes** — DOM count equals the
  server projection count;
- **parallel SI/VGM + Gate-in** branch present (`journey-parallel-branch`);
- right **Quick Panel → Stage Workspace**: exactly one panel column;
- **Customs Import truthful panel**: registration ≠ clearance rows, real blocker verbatim,
  "Tạo GNT không đồng nghĩa đã nộp thuế.", qualified suggested partner, ONE dominant CTA
  (`XỬ LÝ NGAY`);
- **B7 stays neutral**: one dashed slate `RÀ SOÁT HOÀN TẤT`, no completion colour class/fill,
  no `COMPLETED`; the only `%` in the cockpit is the map zoom readout (61%);
- **B8 finance truth**: `finance.outstanding=null` + `partner.suggested=true` ⇒
  `completion-goal-finance[data-state=UNKNOWN]`, never 0/CLOSED/EVIDENCED;
- composition preserved (Attention → Cockpit → Completion Goals);
- 390px: 11 nodes, map usable, customs panel readable, **no horizontal overflow**;
- **zero application page errors** in both lanes.

## 6. Why test artifacts changed (and product source did not)

The Control Tower B1 correction itself is **effective**: `compose_primary_action()` now returns
`/lo-hang/<id>?tab=van-tai#shipment-execution-profile`, and `runPrimaryAction()` reveals the
anchor only after the tab-change render. But the two assertions the Control Tower added observed
the wrong channel:

- the app routes inside a **`MemoryRouter`** (`component/src/App.tsx`: "BrowserRouter →
  MemoryRouter: route state is component-local"), so `?tab=` **never** appears on
  `window.location` (jsdom lane) nor on `page.url()` (browser lane). Both new assertions could
  therefore never pass, on any build, correct or not. Round-2's first run reproduced exactly
  that: `AssertionError: profile CTA must open the tab that owns ShipmentExecutionProfile —
  null !== 'van-tai'`.

Because a **test** proved the defect (and only in the observation channel, not in product
semantics), the bounded fix was test-only:

- `tests/component/dom_acceptance_journey_fresh_188.mjs` — assert the rendered truth instead:
  exactly one pressed Global-Workspace tab and it is `van-tai`; `shipment-execution-profile`
  mounted and contained by the workspace; plus a `scrollIntoView` recorder proving the anchored
  reveal targets the mounted editor (post-mount) rather than the `workspace-tabs` fallback;
- `tests/component/browser_journey_fresh_parity_188.mjs` — same DOM-truth assertions via
  `selectedGlobalTab()` + a `page.addInitScript` reveal recorder, for both the desktop CTA and
  the 390px `HỒ SƠ` phase; server-side route truth (`/fixture.projectedPrimaryRoute`) asserted;
- `scripts/verify_journey_fresh_parity_188.py` — the canonical host now fails closed unless the
  projected profile route is exactly `?tab=van-tai#shipment-execution-profile`, and exposes
  `projectedPrimaryRoute`/`nextRoute` in `/fixture`;
- `tests/test_journey_fresh_parity_188.py` — fixture route pin (see §3).

No product semantics changed. §7 shows the corrected lane is a genuine two-sided challenge.

## 7. Mutation control — the lane detects BOTH halves of B1

| Input under the corrected lane | Result |
| --- | --- |
| pre-B1 bundle (`git archive cf37550`, rebuilt: `cd0feb4d…`) + current fixture | **FAILS** — `anchored reveal must land on the mounted editor … got ["workspace-tabs"]` (the pre-B1 reveal-before-mount defect, isolated) |
| current bundle + pre-B1 (stale) fixture (`tab=lay-hang` route) | **FAILS** — `profile CTA must open the tab that owns ShipmentExecutionProfile: actual 'lay-hang', expected 'van-tai'` (the routing half, isolated) |
| pre-patch `main` dist `940cc11b…` (Round 1) | **FAILS** — `cockpit shell must exist for journey.nodes=[]` (the Owner's production failure) |
| current bundle + current fixture | **PASS** |

## 8. Whole-suite DOM acceptance sweep — no regression, and NOT claimed all-green

Full `tests/component/dom_acceptance_*.mjs` sweep, run twice with ONLY the bundle swapped
(raw logs: `dom-sweep-baseline.txt`, `dom-sweep-head.txt`). 49 lanes + summary line.

| Bundle | lanes rc=0 |
| --- | --- |
| committed dist at `8925b878` (`563a690f…`) | 24 / 49 |
| rebuilt dist on this head (`9d8f10e2…`) | **25 / 49** |

`diff` of the per-lane results shows exactly ONE difference: `dom_acceptance_journey_fresh_188.mjs`
rc=1 → rc=0. The other 48 lanes are identical on both bundles ⇒ no regression from this change.
**The sweep is not green overall and is not claimed to be**: the 24 baseline failures are
pre-existing conditions of this sandbox/baseline (mostly lanes that require fixture arguments,
e.g. `dom_acceptance_journey_demo_fidelity.mjs`, or stale `LO-03xx` fixture data), failing
identically on both bundles.

## 9. Screenshot sha256 (Round 2, real Chromium 153.0.8010.0)

```
e39e95e02b8ae83968f57eac73257f9caacffc7fbed003d1f56be77d0c853d42  fresh-desktop-1-first-screen.png
30f66cb9dd6c107d38b4b1de12aed9c8aedee52d29bedb0c71b95f21292222d2  fresh-desktop-2-cockpit.png
bca0e35d06d089a12196e091f08f56d37bca001bdd7b7949e156c437ba7943da  fresh-desktop-3-onboarding-canvas.png
616f6a7f078af52a0535a028259ac44b17e69ac8834c640443bb1dbfd57dfb39  fresh-desktop-4-completion-goals-after-cockpit.png
e2a02da873bfc3fa0a7830fb370f47dd9d689d89c55cdf362ddd93033b93d79b  fresh-mobile-390-1-first-screen.png
b3f59da156f67b310e204134e8d6a6e07ea1eaaa2f7685097787665644cc320f  fresh-mobile-390-2-cockpit.png
5f65708c0f4f00d89ce2feec53804101eaf47c88346e5bef8abb14797493ced0  fresh-mobile-390-3-onboarding-quick-panel.png
82f88fcb78476e54ed7b772e57aaa99a0db6b1bdb77517ca53e844a486c39007  fresh-mobile-390-4-completion-goals-after-cockpit.png
16e6a138167353bf16f60d9391fe8999710e57dac241692074dcc0271a749c44  populated-desktop-1-map-and-quick-panel.png
e0629e3dc56616a59d8961ff52205ffba4ebf4f28939c49b83d712dadfe836e5  populated-desktop-2-cockpit.png
3730b23accce5f29bb357adba578836b712046775d7b17a1d7e900f15fd94f0f  populated-desktop-3-customs-import-panel.png
8b1e8ac0453c2602eda55a28a5dcaca2c562403177e22390ee213a6eb2529d9a  populated-desktop-4-completion-goals.png
148a12ff569a416fbd6d0fb88319d29de63dbcd2e52b5acaf45f4d6a54120061  populated-mobile-390-1-map.png
ad52c024ddf097a34e0874c91a0fdd43d8c4a7fe6a10a4b5b3b02b24d85cd1a6  populated-mobile-390-2-customs-panel.png
```

## 10. Reproduce

```bash
# 0. toolchain
pip install -r requirements.txt pytest            # mongomock staging transport + tests
cd component && npm ci && npm run typecheck && npm run build && python3 ../scripts/scan_process.py dist && cd ..

# 1. deterministic lanes
python -m pytest tests/test_journey_fresh_parity_188.py tests/test_journey_super_goal_186.py tests/test_journey_v3_customs_import_184.py -q
python scripts/verify_journey_fresh_parity_188.py --dump-model tests/component/fixtures/view_model_journey_fresh_188.json
node tests/component/dom_acceptance_journey_fresh_188.mjs
python scripts/verify_visual_shipment_workspace.py --fixture /tmp/sea160.json
node tests/component/dom_acceptance_journey_demo_fidelity.mjs /tmp/sea160.json component/dist/logi-shell.js

# 2. real browser (browser-capable machine; binaries are NOT committed)
PLAYWRIGHT_MODULE=/path/playwright/index.mjs \
CHROMIUM_EXECUTABLE=/path/chromium CHROMIUM_LIB_PATH=/path/browser-only-libs PYTHON=/path/python \
node tests/component/browser_journey_fresh_parity_188.mjs ./evidence/188 all
```

## 11. Boundary

`MERGE_TO_MAIN => STREAMLIT_PRODUCTION_DEPLOY_TRIGGER`. Not merged, not deployed, no
production business writes, no secrets, `tienthanhlog` untouched, **no Human UAT claimed**.
`START_HEAD=8925b8784462a488a247c1bbeb1219d7b4cdb90b` is bound above; the verified tree is
exactly the tree of the commit that carries this document, and the exact `FINAL_HEAD` /
`FINAL_TREE` of that commit are bound in the PR #189 comment posted immediately after it
(a document cannot contain the hash of the commit that contains it). Independent read-only
Supervisor re-review is still required before any merge decision.
