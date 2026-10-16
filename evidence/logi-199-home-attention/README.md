# LOGI-199 — Home urgent-work panel sizing

**Scope:** one UI layout repair on the existing Home work desk. At desktop width, CSS Grid was stretching the short urgent-work panel to the height of the adjacent running-shipment list; the alert-tinted panel therefore looked like a much larger alert than its actual content. The Home grid now uses the existing responsive `xl:items-start` utility. Content, actions, routes, Journey, business rules, and the approved visual tokens are unchanged.

## Durable identity

- Goal / issue: `LOGI-APP-RENEWAL-01` / [#199](https://github.com/7roger89-web/logistics-work-desk-arena/issues/199)
- Previous verified checkpoint: `arena/d657fb56-logistics-work-desk-arena` @ `1fe2ff56c9214293d5318f1eb33798ddb3d81f93`
- Session branch: `arena/18ef00cf-logistics-work-desk-arena`
- Product source commit: `6391b1d78a376df9117afe7876c9e2c8f5c4736d`
- Reviewed Journey source (unchanged by this slice): `8932fcb4aa2e7705b1e0963a830758bd3d9849ae`
- Draft incremental PR: [#207](https://github.com/7roger89-web/logistics-work-desk-arena/pull/207), based on the verified checkpoint branch—not `main`.

## Changed files

- `component/src/pages/Home.tsx` — adds `xl:items-start` to the existing two-column Home grid.
- `component/dist/logi-shell.js` and `component/dist/logi-shell.css` — rebuilt from the source with the official Vite build.
- `tests/component/dom_home_attention_layout.mjs` — focused regression over the existing compiled React bundle and canonical Home fixture.

## Open-PR overlap audit (#198, #200–206)

Compared the full changed-path lists and submitted reviews/conversation findings for open drafts #198 and #200–206 before treating #207 as an incremental slice:

- No PR in that set changes `component/src/pages/Home.tsx` or the focused Home layout test. #198 is Journey/ShipmentDetail work; #201–203 are shipment-mode/Journey truth; #205–206 are quotation/workbook flows.
- #200 and #204 do change the child `AttentionNow.tsx` used by Home (mobile text behavior/typography); this slice only adjusts the parent Home grid alignment. They are adjacent, composable scopes, not a duplicate. Their broader reviews still reject the respective whole-runtime/integration claims; this PR does not claim to close those findings.
- The generated `component/dist/logi-shell.js` and `.css` paths are shared build outputs across #198/#200/#202–206. This PR was built from its stated checkpoint; when branches are integrated, regenerate dist from the selected combined sources and rerun the relevant checks rather than taking one branch's compiled bundle as authoritative.
- No files or branches from #198–206 were changed. #207 remains a draft on the verified checkpoint base.

## Verification

- `cd component && npm run typecheck` — **PASS**.
- `cd component && npm run build` — **PASS**, Vite 8.2.2, 1,936 modules; committed dist rebuilt from source.
- `cd component && npm run scan` — **PASS**, `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`.
- `node tests/component/dom_home_attention_layout.mjs` — **PASS**; confirms the Home worklist remains alongside the running-shipment list, the wide breakpoint has `xl:items-start`, and the production CSS emits `align-items:flex-start`.
- Isolated `Streamlit AppTest` on `scripts/logi199_t6_staging_app.py` — **PASS**, zero app exceptions; its isolation proof confirms in-process Mongomock only, no real URI and no production client. See `app-test.txt`. AppTest does not render Streamlit Components v2 in a real browser.
- Local loopback Streamlit server — startup and `/_stcore/health` / `/` both returned HTTP 200 while bound only to `127.0.0.1`; server stopped after the smoke.

## Browser / visual evidence boundary

`RUNTIME_REVIEWED=NO`; `VISUAL_VERDICT=NEEDS_EVIDENCE`. No screenshot or runtime visual PASS is claimed. The sandbox had no system Chromium. A temporary Chromium/Playwright probe (installed outside the repository; no app dependency added) could not launch because the host lacks `libnspr4.so`. This is an environment limitation, not an observed product defect. A real rendered desktop/mobile comparison remains open.

## Existing unrelated test gaps observed

These were observed before the Home-only diff was applied; they are not introduced or altered by it and are retained rather than hidden:

- `dom_acceptance_home_hierarchy.mjs` stopped at its old expected label `Quá hạn và sắp tới hạn`, which is absent from the current Home projection.
- `dom_acceptance_support_attention_166.mjs` stopped at its stale expectation that Journey is present in that test's current route/context.
- `.venv/bin/python -m pytest tests/test_logi_shipment_primary_action_unify_01.py -q`: 26 passed, 5 failed on old route-tab expectations (`lay-hang`) versus the current canonical `van-tai` route for profile actions. No route/business source was changed; the existing #199 reconciliation records the same stale anchor-target issue.

The new focused Home layout regression passes. No broad test cleanup or Journey redesign was included.

## Gates and status

- `OE_VERDICT=DO_IT` — one existing responsive utility is the smallest useful correction; no new framework, library, component system, data layer, or workflow was added.
- `FULL_GOAL_199=IN_PROGRESS`; this single Home improvement is not whole-app completion.
- `OWNER_UAT=NOT_RUN` and remains deferred per the 16-Oct Owner direction; no Windows/ZIP/Python trial requested.
- `PRODUCTION_READY=NO`; production data/configuration untouched; no main merge, deployment, public host, or auth bypass.
- `UPLOAD_REQUIRED=NO` — source, dist and this evidence are in the GitHub branch/PR; no separate artifact upload is needed.
