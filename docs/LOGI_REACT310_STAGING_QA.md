# React #310 staging QA — Issue #229

Supervisor verdict: **PASS for bounded shipment-editor acceptance**.
`VERDICT=PROVEN`. This is not full release certification; the Python suite remains known-red.

## Provenance and preflight

- Executor: local Codex, 29 October 2026, Asia/Saigon. Arena-specific new-session canary was not applicable.
- Target: `7roger89-web/logistics-work-desk-arena`, `arena/ae5f9f47-logistics-work-desk-arena`.
- Baseline verified twice, including before repair: `00901511759882cd25039ac97de990e0c332687e`; no HEAD_MOVED.
- Tested repair commit: `9fbff3b86bc06be9ee6ad11f200ddfab500efb8a`. Subsequent report-only commit does not change tested code or dist.
- `P2P_LAW_SOURCE=LOCAL_PORTABLE`; `LAW_CHECK=PASS` after this executor read the target AGENTS and portable notebook. Recorded canonical source-content SHA-256: `11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`. No cross-repository canonical read claimed.
- `EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE`, ID `shared-exp-b2611df4c9393f0017f07dcb`; advisory only.
- OE question: **Không bị over engineering chứ?** SIMPLER_PATH=YES, MATERIAL_PROGRESS=YES, NECESSITY=YES, CORE_BEFORE_SUPPORT=YES, SMALLER_VERIFIABLE_SLICE=YES. `OE_VERDICT=DO_IT`: test the existing hotfix, repair only the reproduced false-success outcome.

```json
{"schema":"p2p-skill-consumption-receipt/1","status":"CONSUMED","skills":[{"id":"scope-reality-check","path":".agents/skills/scope-reality-check/SKILL.md","sha256":"e2b894509e4c8987d5d509edb98a06ee85ad98ebae088b88edde6efe40bd7688","read":true,"hash_match":true,"application":"Existing-hotfix QA first; causal repair only after reproduction."},{"id":"p2p-uiux","path":".agents/skills/p2p-uiux/SKILL.md","sha256":"98f26873e48cc87e34d132478f73672a80d20b3a8e1a2256bdcdab4d6107e7b2","read":true,"hash_match":true,"application":"Real rendered Streamlit/Chromium workflow with isolated data and backend readback; no static-runtime substitution."}]}
```

## Runtime result

`RUNTIME_REVIEWED=YES`; `BROWSER_QA=PASS`; `REACT_310=NOT_REPRODUCED_ON_TESTED_PATH`; `SAVE_READBACK=PASS`.

Environment: real Streamlit 1.60.0 / Python 3.12 / Playwright Chromium, desktop viewport 1440x900, `http://127.0.0.1:9501/?portal=internal`. The test host calls the unchanged `views.web_app.main`, real password authentication, component trigger dispatcher and canonical writers. Before seeding/writes it asserts PREVIEW identity, `mongomock` client, `logistics_staging` database and no real Mongo URI. QA-only controls inject transient VM states and downgrade the disposable test user. These controls are confined to the test host, not app.py.

Passed: Admin password login; shipment list → LO-0306; edit open/close/reopen; save date 2026-10-21; verify canonical `data.0.0.created_at` in DB; reload, log in again and verify displayed date; shipment absent/present; Journey empty/ready/empty; repeated disclosure changes; downgrade account to viewer and attempt 2026-10-22. The final write returns correlated `ok=false`, shows RBAC error and retains 2026-10-21 in DB. No false success toast, React #310, Hook-order error or shell crash. Final browser exit code 0, console errors `[]`.

Baseline reproduction found **false date-save success**, not another React #310: `saveHeaderDate` called `afterSave` immediately after dispatch even when backend RBAC refused. Repair adds one pending intent, duplicate-send protection, request-correlated outcomes and matching canonical readback before success. Header customer save already uses correlated outcomes and its regression remains green. The existing route/Journey hotfix is preserved.

## Validation and exact Python comparison

- `node tests/component/dom_acceptance_react310_shipment_route.mjs`: PASS, including pending, stale success, RBAC denial, mismatched readback, confirmed date and blank date.
- `node tests/component/dom_acceptance_shipment_header_edit.mjs`: 7 checks PASS. Updated the stale immediate-save assertion and existing harness waits/Windows module URL.
- Backend correlation cases: 6 passed, exercising saved/denied/missing/empty/unknown-field/write-failed outcomes.
- `npm run typecheck`: PASS. `npm run build`: PASS; dist rebuilt.
- `npm run scan`: attempted, failed because this Windows host lacks `python3`. Identical `py -3.12 scripts/scan_process.py component/dist`: PASS, 0 executable process references.
- Before, untouched baseline clone: `78 failed, 2061 passed, 23 skipped, 2 errors, 16 subtests passed`, 863.11s.
- After, separate repair worktree: `77 failed, 2068 passed, 23 skipped, 2 errors, 16 subtests passed`, 841.91s.
- Exact unique FAILED/ERROR node sets: before 70, after 69; **added: none**. Removed in the full run: `tests/test_gnt_and_docgen_reality_check.py::test_gnt_revision_comes_from_durable_docgen_metadata_after_session_clear`.
- This removed node is **not claimed fixed**: an isolated rerun passed on baseline and failed on repair at the same existing `attachmentDuplicate is True` assertion; the full-run outcomes were the reverse. It remains known-red/nondeterministic and is outside this repair. No tests were skipped or weakened to hide it. Failure counts also include subtest outcomes and are not unique-node counts.

## Changed files and evidence

Production: `component/src/pages/ShipmentDetail.tsx`, `views/logi_view_model.py`; generated `component/dist/logi-shell.js` and `.css`.
Tests: `tests/test_logi_shipment_core_gaps_01.py`, the two DOM regressions above, `tests/component/react310_streamlit_host.py`, `tests/component/browser_react310_shipment_route.mjs`. This report is the only additional documentation file.

Local durable evidence: `D:/logi-react310-repair/.tmp/evidence/manifest.json`, screenshots `01-edit-save.png`, `02-transitions.png`, `03-viewer-denied.png`, `before-false-success.png`; correlated save/viewer readbacks and console/browser logs. The manifest binds source and evidence hashes to the tested commit/environment. Exact suite comparison: `.tmp/python-suite-comparison.json` with preserved failed/error node lists; full logs remain in each clone's `.tmp`. No credentials or production customer records were published.

Test host/runner use existing dependencies; no new QA framework/service/dependency. Native Anvien capability was unavailable; bounded direct source/diff and runtime evidence were used. Port 9501 was confirmed stopped; in-memory test DB lifetime ended. Production instances, databases, secrets and OAuth were untouched. No merge or deployment.

Draft PR: https://github.com/7roger89-web/logistics-work-desk-arena/pull/231

`LEARNING_RECONCILIATION=CANDIDATE`: when a UI reports a write outcome, dispatch success is not persistence evidence. Trigger: denied backend write paired with a green toast. Evidence: baseline screenshot/readback, repaired runtime RBAC result and stale/denied/mismatch regressions. No experience was promoted to ACTIVE or law.
