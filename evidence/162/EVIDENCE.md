# Issue #162 — Work Module Library V1 · evidence index

**Candidate SHA (round 1, superseded):** `3939e00d5d04b248ee533c7b47a420ebd9ed2e96`
**Independent review:** `CHANGES_REQUIRED` at `c74dfc400090522ccc88fbd19bc32f314823d733` (3 blockers)
**Repair candidate SHA (round 2, superseded):** `2a29a7688c0e0f6417f320ae7f7ca697591cce6d`
**Final candidate SHA:** `96d96979d200e4af35a1ba6e850353da641d061e` (section 8 is new; sections 1–7 keep their provenance)
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
[desktop 1 base journey](https://github.com/7roger89-web/logistics-work-desk-arena/blob/2a29a7688c0e0f6417f320ae7f7ca697591cce6d/evidence/162/desktop-1-base-journey.png) ·
[desktop 2 attach panel](https://github.com/7roger89-web/logistics-work-desk-arena/blob/2a29a7688c0e0f6417f320ae7f7ca697591cce6d/evidence/162/desktop-2-attach-panel.png) ·
[desktop 3 rollup attached](https://github.com/7roger89-web/logistics-work-desk-arena/blob/2a29a7688c0e0f6417f320ae7f7ca697591cce6d/evidence/162/desktop-3-rollup-attached.png) ·
[desktop 4 steps + guidance](https://github.com/7roger89-web/logistics-work-desk-arena/blob/2a29a7688c0e0f6417f320ae7f7ca697591cce6d/evidence/162/desktop-4-steps-and-guidance.png) ·
[desktop 5 step workspace](https://github.com/7roger89-web/logistics-work-desk-arena/blob/2a29a7688c0e0f6417f320ae7f7ca697591cce6d/evidence/162/desktop-5-step-workspace.png) ·
[desktop 6 completion readback](https://github.com/7roger89-web/logistics-work-desk-arena/blob/2a29a7688c0e0f6417f320ae7f7ca697591cce6d/evidence/162/desktop-6-completion-readback.png) ·
[desktop 7 gate cleared](https://github.com/7roger89-web/logistics-work-desk-arena/blob/2a29a7688c0e0f6417f320ae7f7ca697591cce6d/evidence/162/desktop-7-gate-cleared.png) ·
[desktop 8 template library](https://github.com/7roger89-web/logistics-work-desk-arena/blob/2a29a7688c0e0f6417f320ae7f7ca697591cce6d/evidence/162/desktop-8-template-library.png) ·
[mobile 1 journey](https://github.com/7roger89-web/logistics-work-desk-arena/blob/2a29a7688c0e0f6417f320ae7f7ca697591cce6d/evidence/162/mobile-1-journey.png) ·
[mobile 2 rollup](https://github.com/7roger89-web/logistics-work-desk-arena/blob/2a29a7688c0e0f6417f320ae7f7ca697591cce6d/evidence/162/mobile-2-rollup.png)

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

---

## 7. Independent-review blocker repair (round 2)

Reviewed head `c74dfc400090522ccc88fbd19bc32f314823d733` → `CHANGES_REQUIRED`, exactly
three blockers. Each was repaired at its smallest safe point and each has a
regression that fails without the repair. Repair candidate:
`2a29a7688c0e0f6417f320ae7f7ca697591cce6d`.

### BLOCKER 1 — the template lifecycle never reached its transition (`FIXED`)

Two halves, both needed:

1. `core/database.py::save_work_module_template()` normalized the caller's body
   **before** looking up the immutable version, so the bounded library UI's
   status-only payload — `{template_id, name, version, status, anchor_stage}`,
   with no `nodes` at all — died on `Quy trình phải có danh sách bước` for both
   `DRAFT → ACTIVE` and `ACTIVE → RETIRED`. The writer now recognises an existing
   `(template_id, version)` first, loads the **stored** body and validates only
   the requested transition.
2. `views/logi_view_model.py::_handle_work_module_template_save()` re-normalized
   the request body to build its success summary — the same crash, *after* the
   write had already persisted (the exact "failed write that landed" shape). It
   now reads the saved version back from the store, and refuses to report success
   if that readback is missing.

Invariants held and asserted: a status step changes **only** `status` (plus the
write's own audit metadata); nodes, guidance, anchor, gate and join are
byte-for-byte identical before/after; a body smuggled into a status call is
discarded, never applied; `RETIRED → ACTIVE` fails; a same-status re-save is still
refused as an immutable-version edit.

### BLOCKER 2 — the common exception path dropped `requestId` (`FIXED`)

`consume_phase_b_triggers()` kept `requestId` only for
`shipment_sea_facts_save`. The repair is the generic bounded rule: **if the
payload carries a `requestId`, the failure result echoes it** — no per-event
hard-coding, no change to event authority. The regression challenges the hard
case the reviewer named: an exception raised *after* the durable write but
*before* the fresh readback. Asserts: `ok=false`, correct event, exact
`requestId`, the landed fact still on record with the bumped version (no
rollback, no invented failure), recovery visible on the next read, and an
idempotent retry (`noop`). A negative control proves an uncorrelated payload gets
no invented id.

### BLOCKER 3 — dependency readiness was UI-only (`FIXED`)

`_handle_work_module_step_complete()` persisted completion without checking
required dependencies. Before appending, the writer now derives readiness from the
persisted facts of the **exact bound version** through the existing pure
`module_execution()`: `BLOCKING`/`PARALLEL_REQUIRED` hold, `INFORMATIONAL` never
does, and a refusal leaves the shipment version and the history untouched.
Regression: direct dispatcher challenge on `prepare → result (BLOCKING)` —
completing `result` first is refused with `còn thiếu bước bắt buộc (Prepare)`, no
version bump, no history mutation, gate still blocked; after `prepare`, `result`
succeeds and the gate clears; a second module with an `INFORMATIONAL` dependency
completes out of order without being blocked.

### Gates re-measured at the repair candidate

| Gate | Result |
| --- | --- |
| `tests/test_work_module_library_162.py` | **26 passed** (21 round-1 + 5 blocker regressions) |
| Regression lanes (workspace, execution profile, primary action, documents drive/review, scope-aware missing info, slash-route repair, document workflow) | **364 passed** |
| Full suite | **23 failed / 1628 passed / 44 skipped / 25 errors** |
| Pinned untouched `main@36d4cd4` | **23 failed / 1602 passed / 44 skipped / 25 errors** |
| Failure-set diff | sorted FAILED+ERROR ids **identical** → zero regressions |
| `typecheck` / `build` / `scan` | PASS / PASS / PASS (`FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`) |
| Dist rebuild | byte-identical to the reviewed bundle — `logi-shell.js` `311e5b7e…`, `logi-shell.css` `947b1ff8…` (Python-only repair; `dist` untouched and never hand-edited) |
| DOM acceptance #162 | PASS (stable 3/3 runs) |
| Real browser #162 | PASS — lifecycle clicked through: DRAFT → ACTIVE → RETIRED with authoritative readback, version body unchanged, zero page errors |

New screenshots (this candidate):
[desktop 9 lifecycle ACTIVE](https://github.com/7roger89-web/logistics-work-desk-arena/blob/96d96979d200e4af35a1ba6e850353da641d061e/evidence/162/desktop-9-lifecycle-active.png) ·
[desktop 10 lifecycle RETIRED](https://github.com/7roger89-web/logistics-work-desk-arena/blob/96d96979d200e4af35a1ba6e850353da641d061e/evidence/162/desktop-10-lifecycle-retired.png)

### Pre-existing issues observed, NOT fixed (out of the reviewed scope)

* **`#160` harness flakiness, reproduced on the reviewed head.** In an untouched
  `c74dfc4` worktree, `dom_acceptance_visual_shipment_workspace.mjs` passed 1/3
  runs (failing at *different* assertions) and
  `browser_visual_shipment_workspace.mjs` passed 1/3 runs (cold start). In the
  repair tree: jsdom 1/5 runs, browser 1/3 runs. Untouched by this repair; #162's
  own DOM suite is stable (3/3) and its browser suite passed 3/3.
* ~~A gate-less template is stored but hidden from the library list.~~ **Fixed in
  section 8** — the re-review correctly ruled this a real V1 blocker, not an
  out-of-scope observation.

---

## 8. Final blocker repair — gate-less modules (round 3)

Reviewed head `ae6ff2cf7e740e86eb763994fdd1463d2576293d` → one remaining blocker:
a **gate-less** Work Module was written, reported as saved, and then silently lost
on the fresh read. Final candidate: `96d96979d200e4af35a1ba6e850353da641d061e`.

### Root cause

`normalize_template()` emits `join={}` for a version with `gate_stage=""`. Because
`{}` is still a `Mapping`, the **next** normalization re-entered the join branch,
read an empty source node and raised `Điểm nối phải là một bước của quy trình:
(trống).` Every reader skips rows that raise — `index_templates()`,
`attachable_templates()` and `_work_module_library()` — so the stored version
vanished from the library **and** from the attach list while the write had
reported success. A write/readback inconsistency, exactly as reported.

### Repair — canonical model, not a projection patch

`core/work_modules.py` only:

* `gate_stage == ""` accepts a missing join, an explicit `join=None` **and** the
  persisted `join={}` as the same canonical `{}` → idempotent:
  `normalize_template(normalize_template(x)) == normalize_template(x)`;
* no gate, no join node and no `BLOCKING` semantics are invented;
* a **declared** gate is not loosened — an explicit in-template join node with a
  valid dependency type stays mandatory;
* a half-declared join (`{type}` or `{to}` with no source) is still refused rather
  than guessed.

### Regressions (each verified to FAIL against the reviewed normalizer)

| # | Required check | Result |
| --- | --- | --- |
| 1 | pure idempotence for `{}` / `None` / missing join + the negative gated cases (`gate_stage` set with missing, empty, ghost or bad-type join) | PASS |
| 2 | real write → fresh `build_view_model()`: version still in `workModules.all` **and** `workModules.templates` | PASS |
| 3 | real attach: exact id + version pinned, provenance/actor/time normal, rollup present, base journey untouched | PASS |
| 4 | gate-less completion: internal `BLOCKING` still enforced, `INFORMATIONAL` still free, no base gate sentence | PASS |
| 5 | round-2 UI lifecycle still holds for a gate-less version (RETIRED not re-activatable) | PASS |

Reverting only the normalizer hunk makes all five fail (`5 failed, 26 passed`),
then restoring it returns `31 passed` — the tests genuinely bind the bug.

### Gates at the final candidate

| Gate | Result |
| --- | --- |
| `tests/test_work_module_library_162.py` | **31 passed** (26 prior + 5 gate-less) |
| Regression lanes (workspace, execution profile, primary action, documents drive/review, scope-aware missing info, slash-route repair, document workflow) | **369 passed** |
| Full suite | **23F / 1633P / 44S / 25E** vs pinned `main@36d4cd4` **23F / 1602P / 44S / 25E** — sorted FAILED+ERROR ids **identical** |
| typecheck / build / scan | PASS / PASS / PASS (`FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`) |
| Dist rebuild | byte-identical (`logi-shell.js` `311e5b7e…`, `logi-shell.css` `947b1ff8…`) — Python-only repair, `dist` untouched |
| DOM acceptance #162 | PASS, stable 3/3 |

### Real-runtime gate-less flow (browser, shipped bundle)

The form was submitted with the gate left at its default *"Không chặn cổng nào"*
(`inputValue() == ""` asserted), status ACTIVE, anchor `customs-import`, two steps
with an `INFORMATIONAL` dependency. Proven by authoritative readback:

* the fresh library shows the version (`workModules.all` **and** `.templates`),
  `status=ACTIVE`, `gateStage=""` — it did **not** disappear;
* attaching pins the exact version and renders a rollup reading **`Chờ 0/2 bước`**
  with **no** `Chặn …` sentence and **no** gate object, while the gated demo module
  keeps its own `Hoàn thành 3/3` rollup;
* base truth is byte-identical before/after that attach: same 7 nodes, same
  dependencies, same blockers, and no base stage acquired a dependency on the
  gate-less module.

Screenshots: [`desktop-11-gateless-library-readback.png`](https://github.com/7roger89-web/logistics-work-desk-arena/blob/96d96979d200e4af35a1ba6e850353da641d061e/evidence/162/desktop-11-gateless-library-readback.png) ·
[`desktop-12-gateless-attached.png`](https://github.com/7roger89-web/logistics-work-desk-arena/blob/96d96979d200e4af35a1ba6e850353da641d061e/evidence/162/desktop-12-gateless-attached.png)
