# LOGISTICS DeepL Translation V1 Plan

## Metadata

- Date: `2026-09-03`
- Status: `ready_for_owner_gate`
- Plan: `docs/plans/2026-09-03-logistics-deepl-translation-v1/2026-09-03-logistics-deepl-translation-v1-plan.md`
- Evidence: `docs/plans/2026-09-03-logistics-deepl-translation-v1/2026-09-03-logistics-deepl-translation-v1-evidence.md`
- Benchmark: `docs/plans/2026-09-03-logistics-deepl-translation-v1/2026-09-03-logistics-deepl-translation-v1-benchmark.md`
- Actual status: `docs/plans/2026-09-03-logistics-deepl-translation-v1/2026-09-03-logistics-deepl-translation-v1-actual-status.md`

## Goal

Add a bounded, server-side DeepL text translation tool to the Logistics
Streamlit app with deterministic authorized-key failover, explicit usage
checks, minimum RBAC access for sale/support users, and a local Owner visual
acceptance gate. Keep all credentials local and never use a silent provider
fallback.

## Rules

- The user-provided DeepL decisions are closed authority; do not redo broad
  research or add unsupported provider behavior.
- Use the fresh `origin/main` commit containing PR #8 as the branch base.
- Preserve the dirty detached checkout and all unrelated worktrees; do not
  reset, clean, merge, push, open a PR, deploy, or touch production.
- Keep DeepL credentials server-side, masked/index-only in results, and absent
  from source, tests, reports, logs, UI, and exception text.
- Use the existing `core/config.py`, `requests`, Streamlit routing, and the
  single `core/auth.py` permission matrix.
- Add only text translation and explicit usage inspection in V1. Do not add a
  database, queue, worker, generic router, document pipeline, OCR, or fallback
  to Gemini/another provider.
- Complete P0 actual status before implementation work.
- Update each checklist item immediately when it is completed.
- Record evidence as work completes and benchmark only measured counts.
- Run Anvien detect-changes before every implementation-slice commit.
- For this Python Streamlit repository there is no Dockerfile/build target;
  local runtime evidence uses the native Streamlit runtime and focused
  Streamlit/AppTest plus browser-visible checks. No production runtime is
  started.

## Problem

The current app has no DeepL client, no translation route, and no translation
permission. Owner needs a practical Chinese/Vietnamese/English text workflow
that can fail over across authorized DeepL keys when one key is exhausted or
unusable, while keeping API credentials completely outside the user-visible
surface.

## Scope

- Add DeepL key-list configuration through existing list-setting conventions.
- Add a small requests-based DeepL service with endpoint inference, bounded
  retry/backoff, deterministic per-session key state, safe translation results,
  and explicit usage rows.
- Add focused mocked tests for translation, 456 rotation, 401/403 failover,
  bounded 429 retry, exhaustion, endpoint inference, no-key fail-closed
  behavior, secret non-disclosure, and usage masking/indexing.
- Add a `translation` permission for the existing sale/support operational
  roles and register one route under `CÔNG CỤ & THAM KHẢO`.
- Add a compact mobile-friendly Streamlit view for the accepted languages,
  editable/disable-able logistics context, translation, result metadata, API
  index, and explicit usage check.
- Run focused local validation, launch a non-production local preview only if
  the environment is safe, and stop at Owner visual acceptance.

## Non-Goals

- No document/PDF/DOCX/XLSX translation, OCR, glossary, translation memory,
  history database, bulk pipeline, async jobs, voice, browser extension, or
  public API.
- No Gemini or other-provider fallback, quota circumvention, account creation,
  subscription pooling claims, or credential manager subsystem.
- No production database mutation, production app modification, deployment,
  promotion, merge, push, or PR.
- No automatic usage calls on Streamlit rerun; usage runs only after the
  explicit user click.

## Requirements

- Secrets: support `[deepl].api_keys = [...]` and `DEEPL_API_KEYS` JSON/list or
  comma-separated environment form through `get_list_setting`.
- Endpoint: keys ending `:fx` use `https://api-free.deepl.com`; all other keys
  use `https://api.deepl.com`.
- Translation: `POST /v2/translate` with accepted source/target codes, optional
  context, preserve-formatting request, and billed-character request when
  supported; reject oversized input clearly.
- Rotation: 456 marks the key exhausted and advances; 401/403 skips the key;
  429 retries with bounded backoff before reasonable failover; 5xx/network
  errors retry finitely and then may fail over; each key is tried at most once
  per translation attempt after its bounded retry budget.
- Terminal error: exhausted/unavailable pool returns exactly
  `Tất cả API DeepL hiện đã hết hạn mức hoặc không khả dụng.`
- UI: visible translation result, detected source language, billed characters
  when returned, and `Đang dùng API X/N`; no key fragment.
- RBAC: admin wildcard remains; sale and support receive only the new
  translation route permission needed for this feature.
- Tests: use fake keys only and assert no fake or real key appears in logs,
  errors, or rendered UI.

## Acceptance Criteria

- Branch is `feature/logistics-deepl-translation-v1`, based on fresh
  `origin/main` at the recorded SHA/tree, with the original dirty checkout
  unchanged.
- Focused service tests pass for all ten requested behavior classes.
- Focused route/RBAC/AppTest evidence proves support can see and mount the
  translation page and unauthorized users cannot use the route.
- Source compilation and focused runtime checks pass without production DB
  access or writes.
- If no key is configured in the clean branch, real smoke remains `NOT_RUN` and
  the Owner receives the exact local-secret instruction.
- Local preview, when launched, uses a non-production port and is left at the
  DeepL page for Owner review; no push/PR/deploy occurs.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish exact Git authority, current route/config/RBAC surfaces,
    missing DeepL surfaces, and safe touch boundaries.
  - Work Steps: fetch origin; compare detached checkout/local main/origin main;
    verify PR #8; create clean branch worktree from origin/main; inspect
    config/auth/router/tests; run Anvien index and file-detail/impact checks;
    record status and update phase assumptions.
  - Implementation Gate: actual-status file has complete current-state rows,
    evidence IDs, relationship counts, touch map, and a P0 decision.
  - Acceptance: implementation may begin only from the clean branch worktree
    and only inside the listed family.

### P1: DeepL service and safe key pool

- Phase Goal: implement the pure server-side DeepL client contract and prove
  translation, rotation, retry, endpoint, usage, size, and secret-safety rules.
- Phase Boundary:
  - In scope: `core/config.py`, new `core/deepl_translation.py`, focused service/config tests.
  - Out of scope: Streamlit route/UI wiring, database, production, real API calls.
  - Dependencies: P0 complete; `requests` remains the existing dependency.
- Phase Implementation Rule: implement and verify P1-A, refresh status and
  commit; then P1-B; then P1-C. Do not implement P1 as one broad batch.
- Ordered Slice List:
  - P1-A: Add DeepL secret loading and safe service data contracts.
  - P1-B: Add deterministic translation rotation and bounded retries.
  - P1-C: Add explicit usage inspection and terminal-safe status mapping.

- [x] P1-A: Add DeepL secret loading and safe service data contracts
  - Goal: expose only a list of configured keys to the backend and define safe
    result/error/status data without persistence or key rendering.
  - Scope Boundary:
    - Editable: `core/config.py`, new `core/deepl_translation.py`, focused config/service tests.
    - Inspect-only: existing Gemini configuration and database modules.
    - Preserve-only: existing Mongo/Gemini/Telegram settings and production secrets.
    - Out of scope: route registration, UI rendering, network calls in tests.
  - Non-Goals: generic provider abstraction or credential manager.
  - Pre-flight Questions:
    - Data source: `[deepl].api_keys` and `DEEPL_API_KEYS` through `get_list_setting`.
    - Display permission: N/A for pure service; UI is P2.
    - DB read flow: N/A; no database read.
    - DB write flow: N/A; no database write.
    - Render location: N/A; data contracts only.
    - UI behavior flow: N/A.
    - Docker runtime: N/A; no Dockerfile exists.
    - Playwright target: N/A; pure service slice.
    - Behavior test: config list loading, no-key fail-closed, safe dataclass fields.
    - Cleanup/quarantine: temporary fake TOML/env only; no persistent app data.
    - External side effects: none; HTTP is not called in this slice.
    - N/A notes: real secrets are never loaded by tests.
  - Work Steps:
    1. Add the DeepL list setting and service constants/models with explicit
       safe-string boundaries.
       - UI flow check: N/A.
       - DB/data flow check: config only; no DB access or writes.
       - Render location check: N/A.
       - Mini QA: run focused import/config tests.
       - Evidence target: `E1-P1A-CONFIG1`, `E1-P1A-TEST1`.
    2. Add fake-key redaction assertions and input-size/language validation
       helpers without making an HTTP request.
       - UI flow check: N/A.
       - DB/data flow check: in-memory only.
       - Render location check: N/A.
       - Mini QA: verify errors contain no fake key value.
       - Evidence target: `E1-P1A-SEC1`.
  - Implementation Gate:
    - Relevant Anvien file-detail/impact evidence is recorded before edits.
    - P0 rows classify config/service/test surfaces and no real key is read.
  - Acceptance:
    - Source: list setting and safe models compile.
    - Runtime/UI: N/A.
    - DB/data: no DB import/write path.
    - Behavior test: config/no-key/validation tests pass.
    - Cleanup/quarantine: temporary fake config is isolated and removed by its context.
    - Evidence IDs: `E1-P1A-CONFIG1`, `E1-P1A-TEST1`, `E1-P1A-SEC1`.
    - Actual-status rows refreshed: service/config rows transition missing -> partial/correct as proven.
  - Evidence Targets: config loader output, file-detail refresh, focused test result.
  - Actual-status Update: record exact source/test states and next slice assumptions.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P1-B: Add deterministic translation rotation and bounded retries
  - Goal: translate text through DeepL with endpoint inference, 456/401/403
    failover, bounded 429/transient retry, and safe terminal errors.
  - Scope Boundary:
    - Editable: `core/deepl_translation.py`, focused service tests.
    - Inspect-only: existing `core/utils.py` Gemini fallback implementation.
    - Preserve-only: all non-DeepL providers and DB-backed views.
    - Out of scope: UI and usage table.
  - Non-Goals: fallback to Gemini or any silent provider substitution.
  - Pre-flight Questions:
    - Data source: in-memory text/options and configured key list.
    - Display permission: N/A for pure service.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: caller -> service -> safe `TranslationResult`.
    - Docker runtime: N/A; no Dockerfile exists.
    - Playwright target: N/A; mocked service slice.
    - Behavior test: mocked HTTP responses for success, 456, 401/403, 429, 5xx/network, exhaustion, and endpoint.
    - Cleanup/quarantine: mocked requests and injected sleeper only.
    - External side effects: mocked HTTP only; no real API key or customer data.
    - N/A notes: retries are finite and test sleep is injected.
  - Work Steps:
    1. Implement the key pool state machine and safe request wrapper with
       bounded per-status retry budgets.
       - UI flow check: N/A.
       - DB/data flow check: no persistence.
       - Render location check: N/A.
       - Mini QA: run all service rotation tests.
       - Evidence target: `E1-P1B-ROTATE1`, `E1-P1B-TEST1`.
    2. Verify no-key, oversized-input, invalid response, network, and terminal
       failure messages remain key-free and provider-fallback-free.
       - UI flow check: N/A.
       - DB/data flow check: in-memory only.
       - Render location check: N/A.
       - Mini QA: fake-key scan over logs/errors/test result.
       - Evidence target: `E1-P1B-SEC1`.
  - Implementation Gate:
    - Anvien impact for the new service/config boundary is captured.
    - P1-A tests pass and the request wrapper has a finite retry contract.
  - Acceptance:
    - Source: translation service compiles and uses only `requests`.
    - Runtime/UI: N/A.
    - DB/data: no persistent writes.
    - Behavior test: success, 456 rotation, invalid failover, bounded 429, exhaustion, and endpoint tests pass.
    - Cleanup/quarantine: no real calls; fake keys remain test-local.
    - Evidence IDs: `E1-P1B-ROTATE1`, `E1-P1B-TEST1`, `E1-P1B-SEC1`.
    - Actual-status rows refreshed: service behavior transitions partial -> correct.
  - Evidence Targets: mocked HTTP call sequence, sleep count, safe error assertions, focused test output.
  - Actual-status Update: refresh service and security rows before P1-C.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P1-C: Add explicit usage inspection and terminal-safe status mapping
  - Goal: query usage only when called, produce index-only status rows, and
    preserve safe statuses for 456/401/403/429/provider failures.
  - Scope Boundary:
    - Editable: `core/deepl_translation.py`, focused service tests.
    - Inspect-only: existing Streamlit rerun behavior.
    - Preserve-only: translation key-pool semantics and all production data.
    - Out of scope: automatic polling, UI table layout, database persistence.
  - Non-Goals: quota aggregation claims across subscriptions.
  - Pre-flight Questions:
    - Data source: explicit service call over configured keys.
    - Display permission: N/A; UI caller gates the action.
    - DB read flow: N/A.
    - DB write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: explicit click -> one bounded usage request per configured key -> safe rows.
    - Docker runtime: N/A.
    - Playwright target: N/A; service slice.
    - Behavior test: usage payload mapping and index-only rows.
    - Cleanup/quarantine: mocked responses only.
    - External side effects: no real calls in automated tests.
    - N/A notes: UI click wiring is P2.
  - Work Steps:
    1. Implement usage response normalization and per-key safe status rows.
       - UI flow check: N/A.
       - DB/data flow check: no persistence.
       - Render location check: N/A.
       - Mini QA: run usage tests with key scan.
       - Evidence target: `E1-P1C-USAGE1`, `E1-P1C-TEST1`.
    2. Verify configured-key order and no automatic call at service import or
       ordinary translation rerun.
       - UI flow check: caller contract documented for P2.
       - DB/data flow check: no DB calls.
       - Render location check: N/A.
       - Mini QA: mock call count assertions.
       - Evidence target: `E1-P1C-BOUNDARY1`.
  - Implementation Gate:
    - P1-B translation tests pass and no automatic usage path exists.
  - Acceptance:
    - Source: usage rows contain index/status/count/limit/remaining only.
    - Runtime/UI: N/A.
    - DB/data: no persistent writes.
    - Behavior test: usage mapping and no-auto-query tests pass.
    - Cleanup/quarantine: all HTTP is mocked.
    - Evidence IDs: `E1-P1C-USAGE1`, `E1-P1C-TEST1`, `E1-P1C-BOUNDARY1`.
    - Actual-status rows refreshed: service family correct/bound.
  - Evidence Targets: usage mock sequence, row shape, call-count proof.
  - Actual-status Update: mark P1 service family correct before P2.
  - Commit Boundary: commit after this slice when acceptance passes.

### P2: RBAC route and Owner-facing UI

- Phase Goal: expose one translation route with minimum access and a readable
  text-only workflow without changing existing route behavior.
- Phase Boundary:
  - In scope: `core/auth.py`, `views/web_app.py`, new `views/translation.py`, focused mounted tests.
  - Out of scope: other views, DB, production, live customer text.
  - Dependencies: P1 service contract is correct.
- Phase Implementation Rule: implement P2-A, verify/commit, then P2-B,
  verify/commit, then P2-C mounted/security checks.
- Ordered Slice List:
  - P2-A: Register minimum translation permission and route.
  - P2-B: Build translation form/result/usage UI.
  - P2-C: Prove route visibility and UI behavior with focused AppTest.

- [x] P2-A: Register minimum translation permission and route
  - Goal: let authenticated sale/support users reach exactly the new route while
    retaining admin wildcard and route-boundary enforcement.
  - Scope Boundary:
    - Editable: `core/auth.py`, `views/web_app.py`, focused RBAC/router tests.
    - Inspect-only: existing route modules and permission tests.
    - Preserve-only: all existing route labels and permissions.
    - Out of scope: granting admin/system privileges or changing other roles.
  - Non-Goals: authentication redesign.
  - Pre-flight Questions:
    - Data source: `ROLE_PERMISSIONS` and existing `ROUTES` tuple.
    - Display permission: explicit `translation` route permission.
    - DB read flow: N/A for route table.
    - DB write flow: N/A.
    - Render location: sidebar group `CÔNG CỤ & THAM KHẢO`.
    - UI behavior flow: authenticated user -> visible route -> `_assert_route_access`.
    - Docker runtime: N/A.
    - Playwright target: mounted UI in P2-C.
    - Behavior test: support/sale visible, viewer denied, admin allowed, route grouping.
    - Cleanup/quarantine: pure mocks/fixtures.
    - External side effects: none.
    - N/A notes: no database login in focused test.
  - Work Steps:
    1. Add only `translation` to modern sale/support permission sets and add
       the route/group entry.
       - UI flow check: route appears only for authorized roles.
       - DB/data flow check: no DB access.
       - Render location check: existing sidebar group.
       - Mini QA: run route/RBAC assertions.
       - Evidence target: `E2-P2A-RBAC1`, `E2-P2A-TEST1`.
    2. Verify the existing route list remains stable except for the one new
       label and no admin privilege leaks.
       - UI flow check: viewer cannot select/access the route.
       - DB/data flow check: no writes.
       - Render location check: group membership is exact.
       - Mini QA: focused router inspection.
       - Evidence target: `E2-P2A-BOUNDARY1`.
  - Implementation Gate:
    - P1 service tests pass and Anvien impact for `ROLE_PERMISSIONS`/`ROUTES` is recorded.
  - Acceptance:
    - Source: route points to `views.translation.ui_translation` and permission is `translation`.
    - Runtime/UI: authorized route is visible; unauthorized route is filtered/blocked.
    - DB/data: no DB mutations.
    - Behavior test: RBAC/router tests pass.
    - Cleanup/quarantine: fixture-only.
    - Evidence IDs: `E2-P2A-RBAC1`, `E2-P2A-TEST1`, `E2-P2A-BOUNDARY1`.
    - Actual-status rows refreshed: route/RBAC missing -> bound-correct.
  - Evidence Targets: route tuple, visible-route results, permission tests.
  - Actual-status Update: refresh route/RBAC rows before P2-B.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P2-B: Build translation form/result/usage UI
  - Goal: provide the Owner-facing Vietnamese UI for text translation, swap,
    editable context, safe result metadata, and explicit usage checking.
  - Scope Boundary:
    - Editable: new `views/translation.py`, focused UI tests.
    - Inspect-only: existing visual conventions in `views/knowledge_base.py` and `views/tariff.py`.
    - Preserve-only: all existing views and data refresh behavior.
    - Out of scope: history, persistence, bulk text, document uploads.
  - Non-Goals: customer-data integration or automatic context injection.
  - Pre-flight Questions:
    - Data source: user-entered text/options and in-memory session key pool.
    - Display permission: route already checks `translation`.
    - DB read flow: N/A; translation is external API only.
    - DB write flow: N/A; no history/storage.
    - Render location: `views.translation.ui_translation`.
    - UI behavior flow: input -> DỊCH -> service -> result; explicit usage click -> table.
    - Docker runtime: N/A; local Streamlit runtime only.
    - Playwright target: localhost:9501 DeepL page if keys are configured; otherwise no-key fail-closed page.
    - Behavior test: AppTest with mocked service result/error and support identity.
    - Cleanup/quarantine: no DB writes; no real customer text in tests.
    - External side effects: optional real DeepL smoke only after Owner adds local keys.
    - N/A notes: no document upload controls.
  - Work Steps:
    1. Add the compact form with accepted language codes, swap action, context
       toggle/text, input size guidance, and result area.
       - UI flow check: Chinese -> Vietnamese and Vietnamese -> Chinese controls are present.
       - DB/data flow check: no persistence.
       - Render location check: translation route only.
       - Mini QA: AppTest renders support page without exception.
       - Evidence target: `E2-P2B-UI1`, `E2-P2B-TEST1`.
    2. Wire DỊCH and explicit usage actions with safe error/status rendering,
       API index, detected language, and billed characters.
       - UI flow check: mocked success/error/usage paths are observable.
       - DB/data flow check: no Mongo calls.
       - Render location check: no key material in visible text.
       - Mini QA: rendered-text secret scan.
       - Evidence target: `E2-P2B-FLOW1`, `E2-P2B-SEC1`.
  - Implementation Gate:
    - P2-A route/RBAC checks pass; service API is stable.
  - Acceptance:
    - Source: view imports only the approved service/config/auth surfaces.
    - Runtime/UI: form/result/usage affordances render and error states are clear.
    - DB/data: no database reads/writes from the translation view.
    - Behavior test: AppTest mocked translation/usage flows pass.
    - Cleanup/quarantine: no persistent test data.
    - Evidence IDs: `E2-P2B-UI1`, `E2-P2B-TEST1`, `E2-P2B-FLOW1`, `E2-P2B-SEC1`.
    - Actual-status rows refreshed: UI missing -> bound-correct after mounted proof.
  - Evidence Targets: AppTest element labels/results and no-key scan.
  - Actual-status Update: refresh UI row before P2-C.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] P2-C: Prove route visibility and UI behavior with focused AppTest
  - Goal: close the support-access and mounted-flow family with no production
    access and fake service responses only.
  - Scope Boundary:
    - Editable: new/updated focused tests only.
    - Inspect-only: implementation from P1/P2-A/P2-B.
    - Preserve-only: unrelated route tests and production data.
    - Out of scope: broad regression suite and real customer text.
  - Non-Goals: claiming real DeepL readiness from mocked evidence.
  - Pre-flight Questions:
    - Data source: fake key config and mocked service methods.
    - Display permission: support and sale fixtures; viewer negative case.
    - DB read flow: patched `refresh_core_data`, no DB.
    - DB write flow: none.
    - Render location: mounted `Dịch Thuật DeepL` route.
    - UI behavior flow: support fixture -> route -> input -> mocked translate -> result; usage click -> table.
    - Docker runtime: N/A; repository has no Dockerfile.
    - Playwright target: if local preview starts, browser-visible localhost:9501 check; AppTest remains deterministic gate.
    - Behavior test: focused `unittest`/AppTest.
    - Cleanup/quarantine: patch contexts and terminated local process.
    - External side effects: no real API unless Owner explicitly adds keys after mock gate.
    - N/A notes: local browser gate may be `NOT_RUN` if no key is configured.
  - Work Steps:
    1. Add support-access, viewer-denial, mounted-success, usage-click, and
       key-free error tests with no real key values.
       - UI flow check: visible labels/results prove trigger -> service -> render.
       - DB/data flow check: assert no database mutation/call.
       - Render location check: route label/group/result metadata.
       - Mini QA: run the focused UI suite.
       - Evidence target: `E2-P2C-UI1`, `E2-P2C-TEST1`.
    2. Run compile, diff hygiene, Anvien detect-changes, and a local preview
       on port 9501 only when safe; stop with exact Owner gate instruction if
       DeepL keys are absent.
       - UI flow check: browser-visible route/no-key state or real smoke only after Owner configures keys.
       - DB/data flow check: production DB untouched.
       - Render location check: preview left on DeepL page for Owner if launched.
       - Mini QA: browser screenshot/visible-text check or explicit NOT_RUN evidence.
       - Evidence target: `E2-P2C-BUILD1`, `E2-P2C-ANV1`, `E2-P2C-LOCAL1`.
  - Implementation Gate:
    - P2-B AppTest behavior passes; no unresolved secret-safety issue remains.
  - Acceptance:
    - Source: focused UI tests exist for each new trigger and failure path.
    - Runtime/UI: support can use the page; viewer cannot; no key appears.
    - DB/data: `PRODUCTION_DB_MUTATIONS=0` with no DB write path.
    - Behavior test: focused UI suite passes.
    - Cleanup/quarantine: local process stopped unless explicitly left ready for Owner review.
    - Evidence IDs: `E2-P2C-UI1`, `E2-P2C-TEST1`, `E2-P2C-BUILD1`, `E2-P2C-ANV1`, `E2-P2C-LOCAL1`.
    - Actual-status rows refreshed: all in-scope rows correct/bound-correct or explicitly blocked at Owner gate.
  - Evidence Targets: test output, compile output, browser/AppTest evidence, git/anvien state.
  - Actual-status Update: final status matrix and Owner gate readiness.
  - Commit Boundary: commit after this slice when acceptance passes.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the completed plan work against the exact branch, evidence,
    tests, security boundary, and local-only stop contract.
  - Work Steps:
    1. Read the supervisor skill and review the exact changed commit/worktree.
    2. If rejected, fix only the rejected scope, rerun focused evidence, and
       perform a separate traceable commit.
    3. Repeat until pass or an evidenced external blocker is recorded.
  - Implementation Gate: all implementation slices are complete or explicitly
    blocked; no source changes occur after the reviewed identity.
  - Acceptance: supervisor passes or records a blocker; no promotion is inferred.

- [x] Pn-B: Remove dead work created during this plan.
  - Goal: ensure only accepted source/tests/evidence remain in the final diff.
  - Work Steps:
    1. Inspect plan-created files and remove only obsolete artifacts from this plan.
    2. Verify no temporary logs, fake fallback, placeholder, or rejected helper
       remains in the candidate; rerun supervisor review if cleanup changes state.
  - Implementation Gate: do not remove unrelated Owner files or worktrees.
  - Acceptance: clean final status contains no dead plan-created artifacts.

- [x] Pn-C: Close the plan.
  - Goal: record final validation, benchmark, detect-changes, commit, and exact
    local Owner gate status.
  - Work Steps:
    1. Run final focused validation and compile.
    2. Record branch/base/tree, changed files, test results, key count without
       values, real smoke status, and non-production boundary.
    3. Verify the candidate worktree and original dirty checkout are known.
  - Implementation Gate: supervisor verdict and cleanup status are recorded.
  - Acceptance: return packet truthfully states READY_FOR_OWNER_LOCAL_VISUAL_GATE,
    NOT_RUN, or a precise blocker; push/PR/deploy remain NO.

## Risk Notes

- Root checkout/local `main` divergence is preserved as a baseline blocker to
  local-main fast-forward; the implementation branch is safely based on fresh
  `origin/main` instead.
- DeepL response/error formats can be incomplete; map only known fields and
  keep generic safe statuses rather than exposing raw provider bodies.
- Multiple keys from one subscription do not create extra quota; the UI reports
  API index only and makes no quota aggregation claim.
- The Owner's existing root secrets file is not inspected or copied into the
  clean worktree. Real API smoke is therefore conditional on Owner adding keys
  locally to the branch worktree.
