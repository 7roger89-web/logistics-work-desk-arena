# Issue #162 — Work Module Library V1 · evidence index

**Candidate SHA:** `3939e00d5d04b248ee533c7b47a420ebd9ed2e96`
**Branch:** `arena/01a0fafa-logistics-work-desk-arena` (branched from `main@36d4cd4370426a752c3ec0d3c1f205c38f2f6c86`)
**Status:** candidate ready — **not merged, not deployed.**

Every number below was produced on this exact tree. Nothing here is a projection
of intent; each line names the command that produced it.

---

## 1. Product truth (backend, through the real dispatcher)

`core/work_modules.py` adds one small template model, one shipment instance
block, and pure projection composition. Attach, step completion and template
save all flow through the **existing** path:
dispatcher → handler → `ROLE_PERMISSIONS` → versioned atomic save →
fresh readback (`readback` + `audit` in the same result as the write).

| Fact | Observed |
| --- | --- |
| Attach (ACTIVE only) | rollup `BLOCKING`, `0/3 bước`; provenance echoed `MANUAL_ADDITION`; actor `staging.support`; timestamp present |
| Human gate sentence | `Chặn DELIVERY — còn thiếu Prepare specialist file, Submit / process, Result received` |
| After 1 persisted step | `1/3 bước`, status still `BLOCKING` (gate not cleared by unrelated completion) |
| After 3 persisted steps | `DONE`, `3/3 bước`, `gateText == ''`; `delivery` deps gained the module's terminal node |
| Repeat completion | `ok:true, noop:true` — no version churn, no false history |
| Stale write | `expectedVersion` mismatch → `Lô đã thay đổi — đọc lại dữ liệu trước khi ghi nhận.` |
| Zero-module shipment | payload byte-identical to pre-#162 (no `modules` key) — #160/#161 compatibility |
| V2 published | attached V1 instances keep V1 steps; V2 is selectable for **new** attach only |
| DRAFT / RETIRED | attach refused |
| Viewer (`VIEWER`) | attach refused (`shipment_edit`), authoring refused (`operations_write`), library still readable |

Command: `/home/user/.venv/bin/python -m pytest tests/test_work_module_library_162.py -q`
→ **21 passed** (V2 retro-mutation, retired attach, viewer write, PROBLEM
overlay cannot erase completion, unrelated completion cannot clear a blocking
gate, an uploaded document never auto-completes a step, zero-module base
behaviour).

## 2. Regression set

* Focused lanes: `tests/test_work_module_library_162.py`,
  `tests/test_visual_shipment_workspace.py` → **42 passed**.
* Module + 6 related suites (execution profile, primary action, documents,
  scope-aware missing info, slash-route repair) → **253 passed**.
* Full suite: **23 failed / 1623 passed / 44 skipped / 25 errors**.
* Pinned untouched `main` (`git archive 36d4cd4` → `/tmp/main-baseline`):
  **23 failed / 1602 passed / 44 skipped / 25 errors**.
* `diff` of the sorted FAILED+ERROR id lists: **empty** → the candidate adds
  exactly the 21 new passes and changes no existing outcome. The 23 failures and
  25 errors are pre-existing on main (they are collection/setup failures in
  `partner_reconciliation_desk_write_oracle`, `logi_interaction_latency_finalize_02`,
  `logi_render_performance_01`) and are **not** regressions.

## 3. Frontend

| Gate | Result |
| --- | --- |
| `npm run typecheck` | PASS (`tsc --noEmit`) |
| `npm run build` | PASS — `dist/logi-shell.css` 71.32 kB (gz 14.60), `dist/logi-shell.js` 1,216.52 kB (gz 263.54) |
| `npm run scan` | PASS — `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0` |
| Rebuild byte-identity | `dist/logi-shell.js` sha256 `311e5b7e3f759646dce202aa33e70b129b6cade62fda559c829e300110c0fdc8`, `dist/logi-shell.css` sha256 `947b1ff8ff6d7a9b797b4159e33c038137979136347596b6cb6767a6d60f1ef7` — **unchanged by a clean rebuild**, so the committed bundle (and every screenshot below) is exactly this source. `dist` is never hand-edited. |

DOM acceptance on the **shipped bundle** (jsdom, real transport):
`node tests/component/dom_acceptance_work_module_library_162.mjs /tmp/log162-dom.json`
→ PASS — 7 base nodes unchanged after attach, rollup BLOCKING→DONE with the
gate wording, internal steps hidden until the rollup toggle, selection is
view-state only, exactly ONE bounded `work_module_step_complete` event with the
correct `instanceId/nodeId/expectedVersion`, optimistic UI suppressed until
readback, refusal banner honest, `1/3 → 3/3` gated by readback, Viewer
read-only, bounded `/quy-trinh` library.

Fixtures come from the isolated acceptance host
(`scripts/verify_work_module_library_162.py`, mongomock only, loopback:9502 —
never production; production is untouched and no app database is created or
dropped).

## 4. Real-browser runtime (1440px + 390px)

`node tests/component/browser_work_module_library_162.mjs evidence/162`
→ PASS — Chromium 131, root document, the shipped bundle served by the isolated
host:

1. base journey with no modules: 7 nodes, no rollup, attach action present;
2. attach panel → ACTIVE choice → confirm → server version bumped → branch
   appears without disturbing any base node;
3. rollup collapsed/expanded, quick-panel guidance, module step workspace;
4. one persisted step → `1/3` (canonical fact, not a visual flip);
5. three persisted steps → `DONE`, gate sentence gone;
6. mobile 390px: no horizontal page overflow, rollup readable;
7. `/quy-trinh` library bounded, authoring available to an authorised actor;
8. zero page errors for the whole journey.

Screenshots (same SHA):
[desktop 1 base journey](https://github.com/7roger89-web/logistics-work-desk-arena/blob/3939e00d5d04b248ee533c7b47a420ebd9ed2e96/evidence/162/desktop-1-base-journey.png) ·
[desktop 2 attach panel](https://github.com/7roger89-web/logistics-work-desk-arena/blob/3939e00d5d04b248ee533c7b47a420ebd9ed2e96/evidence/162/desktop-2-attach-panel.png) ·
[desktop 3 rollup attached](https://github.com/7roger89-web/logistics-work-desk-arena/blob/3939e00d5d04b248ee533c7b47a420ebd9ed2e96/evidence/162/desktop-3-rollup-attached.png) ·
[desktop 4 steps + guidance](https://github.com/7roger89-web/logistics-work-desk-arena/blob/3939e00d5d04b248ee533c7b47a420ebd9ed2e96/evidence/162/desktop-4-steps-and-guidance.png) ·
[desktop 5 step workspace](https://github.com/7roger89-web/logistics-work-desk-arena/blob/3939e00d5d04b248ee533c7b47a420ebd9ed2e96/evidence/162/desktop-5-step-workspace.png) ·
[desktop 6 completion readback](https://github.com/7roger89-web/logistics-work-desk-arena/blob/3939e00d5d04b248ee533c7b47a420ebd9ed2e96/evidence/162/desktop-6-completion-readback.png) ·
[desktop 7 gate cleared](https://github.com/7roger89-web/logistics-work-desk-arena/blob/3939e00d5d04b248ee533c7b47a420ebd9ed2e96/evidence/162/desktop-7-gate-cleared.png) ·
[desktop 8 template library](https://github.com/7roger89-web/logistics-work-desk-arena/blob/3939e00d5d04b248ee533c7b47a420ebd9ed2e96/evidence/162/desktop-8-template-library.png) ·
[mobile 1 journey](https://github.com/7roger89-web/logistics-work-desk-arena/blob/3939e00d5d04b248ee533c7b47a420ebd9ed2e96/evidence/162/mobile-1-journey.png) ·
[mobile 2 rollup](https://github.com/7roger89-web/logistics-work-desk-arena/blob/3939e00d5d04b248ee533c7b47a420ebd9ed2e96/evidence/162/mobile-2-rollup.png)

The #160 real-browser suite also passes on this bundle
(`node tests/component/browser_visual_shipment_workspace.mjs`, 11 nodes, canonical
write + fresh readback, single primary action, zero page errors) — one cold-start
flake on the first attempt, green on re-run, consistent with the suite's known
`tick=70ms` cold timing.

## 5. One real bug found and fixed

`views/logi_view_model.py::_handle_work_module_template_save` passed
`requestId` both directly and through the shared `out()` result builder, so a
template write that **had** persisted raised `TypeError: _result() got multiple
values for keyword argument 'requestId'` and reported false failure. Caught by
the new adversarial suite; the duplicate kwarg was removed. This is exactly the
"false failed write that landed" class of bug the completion semantics forbid.

## 6. Scope discipline

Not implemented, by design: Support Attention/Now layer (deferred follow-up),
#163 Management Control Tower, Customer Playbook, Assisted Learning, extra
provenance values (`CUSTOMER_PLAYBOOK | REGULATORY_RULE | SYSTEM_RECOMMENDATION_CONFIRMED`),
BPMN/drag-and-drop graph authoring, second workflow/task/document/finance store,
graph DB, rules engine, background worker, scheduler, module-only event bus,
per-module document storage or cost attribution.
