# Issue #186 — Journey Cockpit V3 terminal product readiness · final runtime evidence

**Purpose.** Final, exact-head runtime evidence for PR #187 after the Control Tower
bounded source repairs B7 (no fake whole-shipment `COMPLETED` terminal) and
B8 (truthful finance Completion Goal semantics). This supersedes the historical
`a06ff69` runtime evidence, which is retained in the PR body for provenance only.

**Actor self-law preflight.**
`LAW_CHECK=PASS | SOURCE=.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md (LOCAL_PORTABLE) | SOURCE_SHA256=316936bc951a466c89cc8efb9291f9425571cf886199c8f4f4372be5d7c25ae4`
The portable projection's recorded `SOURCE_CONTENT_SHA256` equals the sha256 of the
projected source body (verified in-repo). Canonical cross-repo law was not probed
per the repo-scoped portable rule. `P2P_LAW_SOURCE=LOCAL_PORTABLE`.
`EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-b2611df4c9393f0017f07dcb`

**Transport.** Isolated in-process mongomock staging only
(`scripts/verify_visual_shipment_workspace.py` → `SANDBOX_STAGING`). No real
`MONGO_URI`, no `.env`, no production DB, no deploy, no secrets, no `tienthanhlog`.

**Browser.** Real Chromium `HeadlessChrome/153.0.8010.0` (Sparticuz build), driven by
puppeteer-core. NSS/NSPR were built from source (NSS_3_131_RTM / NSPR_4_40_RTM) to
satisfy the sandbox's missing system libs; this affects only the throwaway browser
harness, not the repository or the product. The rendered bytes are the EXACT committed
`component/dist` produced from this head.

## 1. Rebuild from source (dist generated, never hand-edited)

| Check | Command | Result |
| --- | --- | --- |
| typecheck | `npm run typecheck` (component) | PASS (`tsc --noEmit`, exit 0) |
| build | `npm run build` (component) | PASS — Vite 8.2.2, 1914 modules |
| scan | `npm run scan` (`scripts/scan_process.py dist`) | `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0` |

Rebuilt dist hashes (differ from the stale `a06ff69` dist, proving regeneration):
- `component/dist/logi-shell.js`  sha256 `940cc11bc4998ae57537865a0b3796eacd1fd2197fe26a35575b50233bc56296` (was `4f80bf58…`)
- `component/dist/logi-shell.css` sha256 `6c9581d39f42ef5c04c092007ec426f9dab07a101fbc9caa377dca534d088569` (was `e5c92ea8…`)

Dist contains the repaired semantics and no fake terminal:
- `RÀ SOÁT HOÀN TẤT` present (1); `không phải % hoàn thành hay trạng thái CLOSED` present (1);
  `UNKNOWN được giữ nguyên, không đổi thành 0/đã trả` present (1); `>COMPLETED<` occurrences 0.

## 2. Focused regressions + Prototype B oracle

| Check | Command | Result |
| --- | --- | --- |
| #186 + #184 | `python -m unittest tests.test_journey_super_goal_186 tests.test_journey_v3_customs_import_184 -q` | `Ran 25 tests … OK` |
| Prototype B | `node tests/component/dom_acceptance_journey_demo_fidelity.mjs <fixture>` | PASS — 11 exact positions, parallel group/routes, fit/zoom/reset/pan, drag guard, all node selections, right-side workspace, collapse/expand, global process, zero navigation writes |

## 3. Real browser · desktop 1440×1000 — `DESKTOP_186 PASS (18/18)`

- Attention visible (1 item) and rendered ABOVE Completion Goals ABOVE Journey.
- Completion Goals visible; summary `2 mục có bằng chứng · 3 mục cần xử lý · 1 mục chưa xác định`.
- Six phase strip visible and labelled `HỒ SƠ … HOÀN TẤT` (1/6..6/6).
- Detailed map visible with all 11 factual nodes; parallel SI/VGM + Gate-in group shown.
- Neutral `RÀ SOÁT HOÀN TẤT` terminal visible with dashed slate styling; NO green/emerald
  whole-shipment completion; NO `COMPLETED` text; NO numeric `%` or health score.
- Customs Import specialized panel opens; exactly ONE dominant CTA (`XỬ LÝ NGAY`);
  registration≠clearance surfaces present; suggested partner stays qualified.
- Stage Workspace opens on the right (single Quick Panel, no duplicate).
- B8 finance goal renders `UNKNOWN` for this fixture (never zero/paid, never fake EVIDENCED).
- No page-level horizontal overflow (scrollWidth=1440). No application console errors
  (only the sandbox-blocked external Google Fonts stylesheet).

## 4. Real browser · mobile 390×844 — `MOBILE_186 PASS (12/12)`

- No page-level horizontal overflow (scrollWidth=390) before and after internal map pan.
- Attention, Completion Goals, and Journey all usable; goal title font 15.5px.
- Six phase buttons present, labelled, within viewport, touchable height (≥71px).
- Tapping `NHẬP KHẨU` opens a readable Customs panel (font 15.5px, single CTA).
- Map internal pan/scroll allowed: transform follows the pointer gesture without page overflow.

## 5. B8 finance truth table (exact dist, jsdom) — `B8_TRUTH_TABLE PASS`

| Fixture finance state | Rendered state |
| --- | --- |
| outstanding unknown, partner suggested | `UNKNOWN` |
| known non-zero customer outstanding | `ACTION` |
| authoritative zero closeout (outstanding 0 + partner remaining 0) | `EVIDENCED` |
| relevant partner without authoritative remaining | `UNKNOWN` |

## 6. Screenshot sha256

```
03023744702f9dee044a79b0792832cdff18541b74f80b39c53731fcc95b5fea  desktop-1-attention-and-completion-goals.png
14dad1541f0c3133806827916b7d7b54f00f0d0f7b3c1b9b32e52f5539e15500  desktop-2-journey-six-phases-and-map.png
28ea23441cf1c29999ab9764023ec2558f31be12bd7bc097369aae3768a188d3  desktop-3-customs-import-panel.png
ab33998f2fc804a5567a67cb44c7ce9d1162757c9d5b15bf0debd7b279741ee8  desktop-4-stage-workspace.png
d3af4fd6c5bcca838659d72158814697333092a605e77acc160d5aadadaefc32  mobile-1-phase-strip-and-map.png
8581972d48584996e382d8780a6445a4f58ad8241fc4f81d6cc96457799d9b8b  mobile-2-customs-panel.png
27a0c2a9b86a8086dd2f06a511c2bba7acff99ad75a29332cd9488d42c920d05  mobile-3-completion-goals.png
```

Exact `FINAL_HEAD` / `FINAL_TREE` and branch ahead/behind are bound in the PR #187
comment (and git log) at the commit that adds this evidence. Not merged, not deployed,
Human UAT not claimed.
