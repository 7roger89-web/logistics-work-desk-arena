# LOG-C06 Owner Review and Reconciliation Phase Plan

## Metadata

- Date: `2026-08-15`
- Status: `PRODUCT_PASS` — LOG-C06 terminal product closure
- Plan: `docs/plans/2026-08-15-log-c06-owner-review-reconciliation/2026-08-15-log-c06-owner-review-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-15-log-c06-owner-review-reconciliation/2026-08-15-log-c06-owner-review-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-15-log-c06-owner-review-reconciliation/2026-08-15-log-c06-owner-review-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-15-log-c06-owner-review-reconciliation/2026-08-15-log-c06-owner-review-reconciliation-actual-status.md`

Final P4 status: complete for staging/review reconciliation; cutover remains `DRAFT / NOT_APPROVED / NOT_LIVE`.

Current P5 status: complete for staging/review sufficiency; cutover remains
`DRAFT / NOT_READY / NOT_APPROVED / NOT_LIVE` pending opening-material Owner
decisions and temporal-scope clarification.

## Goal

Continue LOG-C06 inside the existing staging/review boundary after the Owner authorized
review/correct/reconcile work. Reconstruct the six golden items from the real workbook,
derive a deterministic checkpoint component candidate set, cluster the remaining
`REVIEW_REQUIRED` workload, expose business-language evidence and an Owner Decision Pack,
and regenerate a truthful non-live opening draft. No new P2P Goal Contract is created.

## Rules

- The Owner decision authorizes staging/review analysis only.
- Source workbook remains read-only and its SHA-256 must remain unchanged.
- `READY_FOR_OWNER_CONFIRMATION` is a derived review-readiness state, never `CONFIRMED`.
- No material financial meaning may be auto-confirmed from arithmetic or free text.
- Checkpoint rows and their candidate components may not both enter an opening draft.
- CNY, USD, VND, and UNKNOWN remain separate; no cross-currency total is produced.
- Canonical ledger, payment writes, migration, publication, approval/live cutover, AI, and Quick Entry remain forbidden.
- Use deterministic/reversible evidence and grouping only; no external inference.
- Run Anvien impact/file-detail before editing existing production functions or shared contracts.
- Run full build/validation and visible browser evidence for the UI change; Docker absence remains an explicit limitation.
- Update evidence/benchmarks/status after each slice and commit each verified slice separately.

## Problem

The first LOG-C06 phase safely staged 289 items but left 185 amount-bearing rows in
`REVIEW_REQUIRED`. The existing screen exposes raw/proposal fields and a draft, but does
not yet show the Owner the business meaning, deterministic review clusters, checkpoint
arithmetic, or a compact set of business decisions. The six golden values also need
source-row reconstruction before any Owner confirmation is requested.

## Scope

- Pure deterministic analysis of staged items and their source provenance.
- Six golden-item business summaries in Vietnamese-friendly wording.
- Exact candidate reconstruction for the 134,973 CNY checkpoint.
- Review cluster counts and known-currency amounts.
- Derived `READY_FOR_OWNER_CONFIRMATION`, `REVIEW_REQUIRED`, `UNKNOWN`, and
  `NOT_APPLICABLE` review-readiness labels without changing raw or confirmed state.
- Business-language Owner Decision Pack rendered in Historical Review.
- Opening draft regeneration that still excludes all non-`CONFIRMED` items.
- Focused tests, full tests, build, visible browser QA, source hash, and sibling regression.

## Non-Goals

- No new Goal Contract.
- No canonical financial mutation or payment write.
- No workbook edit or live migration.
- No AI or free-text SALE Thành inference.
- No Quick Entry, Dashboard redesign, deployment, Docker setup, or production acceptance.
- No automatic `CONFIRMED` transition for any golden item or cluster.

## Requirements

1. Read the actual workbook and preserve exact source sheet/row/cell references.
2. Reconstruct 24,576, 62,464, 1,687, 1,572, 25,025, and 134,973 from source evidence.
3. For 134,973, search the bounded preceding source context for candidate components,
   calculate an exact sum/difference, and record excluded candidate rows and reasons.
4. Group all 185 review rows into deterministic clusters with count, known-currency
   totals, representative evidence, and a rule-resolution recommendation.
5. Keep the Owner-facing language about money source, holder/location, business meaning,
   shipment/customer linkage, certainty, and remaining business decision.
6. Keep the canonical opening model confirmed-only and checkpoint-safe.

## Acceptance Criteria

- Every golden item has a source trace and a business-language recommendation.
- The 134,973 candidate component set sums exactly to 134,973 CNY, while the checkpoint
  remains excluded from the opening draft and no double count is possible.
- All 185 review items appear in exactly one deterministic cluster.
- Derived readiness does not change `review_status` or create `CONFIRMED` rows.
- Historical Review visibly renders the golden evidence, clusters, and decision pack.
- Opening draft remains `DRAFT / NOT_APPROVED / NOT_LIVE` and has zero canonical mutations.
- Focused tests, full regression, compile/build, source hash, and visible browser evidence
  are recorded; Docker limitation is explicit.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: establish current source/model/UI reality after Owner authorization.
  - Work Steps: inspect current plan, source workbook, staging/opening/view modules, and Anvien file-detail/impact; record statuses and next-slice gates.
  - Implementation Gate: actual status has evidence IDs and a final P0 decision.
  - Acceptance: current parser/opening model are marked preserve/partial precisely and the missing analysis/decision-pack surface is bounded.

### P1: Deterministic review analysis

- Phase Goal: create a pure, reversible analysis contract for golden items, checkpoint candidates, readiness, and clusters.
- Phase Boundary:
  - In scope: new `core/historical_review_analysis.py` and direct tests.
  - Out of scope: canonical store, raw parser mutation, approval, live cutover.
  - Dependencies: existing staging item schema and preserved source workbook.
- Phase Implementation Rule: implement `P1-A`, verify and commit; then implement `P1-B`, verify and commit.
- Ordered Slice List:
  - P1-A: six golden-item business evidence and checkpoint reconstruction
  - P1-B: 185-row deterministic clusters and owner-readiness classification

- [x] P1-A: six golden-item business evidence and checkpoint reconstruction
  - Goal: prove the six requested values from actual source rows and identify the exact candidate component set for 134,973.
  - Scope Boundary:
    - Editable: new pure analysis module and its tests.
    - Inspect-only: workbook, `core/historical_staging.py`, `core/historical_opening.py`.
    - Preserve-only: raw staging fields, canonical ledger, existing store.
    - Out of scope: any confirmation or database mutation.
  - Non-Goals: no automatic business ownership decision; no live amount.
  - Pre-flight Questions:
    - Data source: staged items produced from `D:\Copy of TOYS-2025 - Copy.xls`.
    - Display permission: Owner-authorized staging review only.
    - DB read flow: N/A for pure module; caller supplies staged items.
    - DB write flow: none.
    - Render location: later Historical Review business evidence panel.
    - UI behavior flow: N/A in this slice; unit contract first.
    - Docker runtime: record repository Docker target absence.
    - Playwright target: N/A for pure model slice.
    - Behavior test: golden rows, exact checkpoint sum, exclusions, and no double count.
    - Cleanup/quarantine: no persistent writes; fixture/source remains read-only.
    - External side effects: none.
    - N/A notes: UI is implemented in P2-A.
  - Work Steps:
    1. Add pure golden-item and checkpoint reconstruction functions using source traces and Decimal arithmetic.
       - UI flow check: N/A; result must be renderable without technical fields.
       - DB/data flow check: input copies only; no mutation.
       - Render location check: return source reference, meaning, money source/location, certainty, and Owner question.
       - Mini QA for each completed implementation slice (MUST): focused unit tests and compileall.
       - Evidence target: `E1-P1A-GOLD1`, `E1-P1A-CHECKPOINT1`.
    2. Verify the exact 134,973 candidate set and explicit excluded rows.
       - UI flow check: N/A.
       - DB/data flow check: checkpoint and components remain excluded from canonical opening.
       - Render location check: component table and arithmetic explanation.
       - Mini QA for each completed implementation slice (MUST): exact-sum and double-count tests.
       - Evidence target: `E1-P1A-ORACLE1`.
  - Implementation Gate:
    - Anvien impact/file-detail evidence confirms only a new pure module is edited in this slice.
    - `views/historical_review.py`, staging parser, opening model, and canonical ledger remain untouched.
  - Acceptance:
    - Source: all six values resolve to Sheet2 rows/cells.
    - Runtime/UI: N/A in this slice.
    - DB/data: no writes; checkpoint candidate IDs are separate from checkpoint ID.
    - Behavior test: focused tests pass.
    - Cleanup/quarantine: no persistent artifact other than code/tests/plan evidence.
    - Evidence IDs: `E1-P1A-GOLD1`, `E1-P1A-CHECKPOINT1`, `E1-P1A-ORACLE1`.
    - Actual-status rows refreshed: analysis module and checkpoint state.
  - Evidence Targets: source row dump, focused test log, hash check.
  - Actual-status Update: mark golden reconstruction correct; keep checkpoint opening inclusion blocked pending Owner decision.
  - Commit Boundary: commit after acceptance passes.
  - Actual result: `core/historical_review_analysis.py` reconstructs all six rows and finds one exact 11-row candidate set for 134,973 CNY; focused tests pass.

- [x] P1-B: 185-row deterministic clusters and owner-readiness classification
  - Goal: reduce Owner workload to cluster-level business decisions without auto-confirming material semantics.
  - Scope Boundary:
    - Editable: same pure analysis module and direct tests.
    - Inspect-only: staged item schema and parser rules.
    - Preserve-only: `review_status`, raw evidence, review store, canonical opening.
    - Out of scope: applying review actions.
  - Non-Goals: no hidden fallback and no AI classification.
  - Pre-flight Questions:
    - Data source: all 289 staged items.
    - Display permission: Owner review phase.
    - DB read flow: caller supplies loaded staging items.
    - DB write flow: none.
    - Render location: cluster table and decision pack in Historical Review.
    - UI behavior flow: N/A until P2-A.
    - Docker runtime: record limitation.
    - Playwright target: N/A until P2-A.
    - Behavior test: every review row belongs to exactly one cluster.
    - Cleanup/quarantine: no writes.
    - External side effects: none.
    - N/A notes: no Owner action is executed by this slice.
  - Work Steps:
    1. Derive cluster, readiness, business meaning, common ambiguity, and rule-resolution recommendation.
       - UI flow check: N/A; result must be JSON-serializable.
       - DB/data flow check: derived fields do not alter source/status.
       - Render location check: cluster counts and currency totals are business-readable.
       - Mini QA for each completed implementation slice (MUST): focused cluster coverage tests.
       - Evidence target: `E1-P1B-CLUSTER1`.
    2. Verify golden rows map to the intended Owner decision categories.
       - UI flow check: N/A.
       - DB/data flow check: `READY_FOR_OWNER_CONFIRMATION` never enters opening position.
       - Render location check: decision-pack candidates are concise.
       - Mini QA for each completed implementation slice (MUST): readiness immutability tests.
       - Evidence target: `E1-P1B-READY1`.
  - Implementation Gate:
    - P1-A exact arithmetic tests pass; no existing production function needs editing.
  - Acceptance:
    - Source: 185/185 rows are assigned once; known-currency totals are deterministic.
    - Runtime/UI: N/A in this slice.
    - DB/data: no review action, confirmation, or canonical write.
    - Behavior test: cluster and readiness tests pass.
    - Cleanup/quarantine: no persistent writes.
    - Evidence IDs: `E1-P1B-CLUSTER1`, `E1-P1B-READY1`.
    - Actual-status rows refreshed: cluster workload and Owner decision count.
  - Evidence Targets: cluster JSON summary, focused tests, raw/status immutability assertion.
  - Actual-status Update: record deterministic workload reduction while retaining unresolved business decisions.
  - Commit Boundary: commit after acceptance passes.
  - Actual result: all 185 `REVIEW_REQUIRED` rows map to one of 10 deterministic clusters; derived readiness is read-only and the bounded Owner Decision Pack contains six decisions.

### P2: Business review surface and draft explanation

- Phase Goal: expose the deterministic analysis in Historical Review and keep the opening draft truthful.
- Phase Boundary:
  - In scope: minimal `views/historical_review.py` seam, UI tests, browser flow/evidence.
  - Out of scope: existing C04/C05 desk redesign and any canonical writer.
  - Dependencies: P1 pure analysis contract.
- Phase Implementation Rule: implement `P2-A`, verify and commit; then run `P2-B` validation and closure.
- Ordered Slice List:
  - P2-A: render business evidence, cluster workload, and Owner Decision Pack
  - P2-B: browser/regression/build/source-fingerprint closure

- [x] P2-A: render business evidence, cluster workload, and Owner Decision Pack
  - Goal: let Owner review meaning instead of technical accounting fields.
  - Scope Boundary:
    - Editable: `views/historical_review.py` and its direct UI tests.
    - Inspect-only: new pure analysis module.
    - Preserve-only: existing review actions and opening model semantics.
    - Out of scope: approve/live controls, new routes, canonical data.
  - Non-Goals: no automatic action on READY rows.
  - Pre-flight Questions:
    - Data source: loaded staging items plus pure analysis output.
    - Display permission: local Owner review session.
    - DB read flow: existing staging DB/session fallback.
    - DB write flow: review buttons remain reason-gated and staging-only.
    - Render location: Historical Review before review inbox/draft.
    - UI behavior flow: open review -> inspect golden item -> inspect cluster -> inspect decision pack -> draft remains NOT_READY.
    - Docker runtime: no target found; record bounded local runtime only.
    - Playwright target: visible local Streamlit runtime for bounded UI evidence.
    - Behavior test: UI recorder + visible browser.
    - Cleanup/quarantine: browser profile and screenshots under repo-local `.tmp`/QA paths; no screenshots committed.
    - External side effects: none beyond existing staging action controls.
    - N/A notes: no production runtime acceptance.
  - Work Steps:
    1. Render six business cards, clusters, and Owner Decision Pack with source trace and certainty.
       - UI flow check: all requested sections visible from Historical Review.
       - DB/data flow check: no derived readiness changes `review_status`.
       - Render location check: no debit/credit/journal/GL/database fields in the Owner-facing pack.
       - Mini QA for each completed implementation slice (MUST): UI recorder and focused tests.
       - Evidence target: `E2-P2A-UI1`, `E2-P2A-ORACLE1`.
    2. Verify the existing review action and draft remain reachable and safe.
       - UI flow check: no-reason action remains blocked; draft remains DRAFT/NOT_READY.
       - DB/data flow check: canonical access remains zero.
       - Render location check: checkpoint warning and no-double-count explanation visible.
       - Mini QA for each completed implementation slice (MUST): visible browser flow.
       - Evidence target: `E2-P2A-BROWSER1`.
  - Implementation Gate:
    - Before editing the high-risk view, current file-detail/impact evidence is recorded; edit stays a minimal import/render seam.
  - Acceptance:
    - Source: UI consumes only pure analysis output and staged evidence.
    - Runtime/UI: business panels render in the real Historical Review route.
    - DB/data: no confirmation or canonical mutation.
    - Behavior test: focused UI tests and browser flow pass.
    - Cleanup/quarantine: screenshots remain uncommitted; reports are scoped.
    - Evidence IDs: `E2-P2A-UI1`, `E2-P2A-ORACLE1`, `E2-P2A-BROWSER1`.
    - Actual-status rows refreshed: Historical Review bound-correct for owner review.
  - Evidence Targets: official QA JSON/Markdown, screenshots, UI tests, source hash.
  - Actual-status Update: mark business review surface implemented; retain cutover locked.
  - Commit Boundary: commit after acceptance passes.
  - Actual result: Historical Review now renders the six golden business cards, all 10
    deterministic clusters, the six-decision Owner Decision Pack, and the 134,973 CNY
    checkpoint reconstruction. The derived READY label is visibly separated from
    CONFIRMED; existing no-reason review guard and non-live draft remain reachable.
    The implementation slice is committed as `05ebe65`.

- [x] P2-B: browser/regression/build/source-fingerprint closure
  - Goal: independently validate the complete continuation slice and preserve C02-C05.
  - Scope Boundary:
    - Editable: plan/evidence/benchmark/status/report artifacts only.
    - Inspect-only: production behavior after P2-A.
    - Preserve-only: unrelated dirty worktree files.
    - Out of scope: Docker deployment and live cutover.
  - Non-Goals: no code repair during QA review.
  - Pre-flight Questions:
    - Data source: real workbook and local staging DB/session.
    - Display permission: visible local runtime.
    - DB read flow: existing staging path.
    - DB write flow: no action with material reason is executed.
    - Render location: Historical Review and Dashboard return path.
    - UI behavior flow: real visible browser journey.
    - Docker runtime: unavailable if no repository target exists.
    - Playwright target: visible Chrome.
    - Behavior test: focused/full/regression suites and browser action ledger.
    - Cleanup/quarantine: `.tmp` logs and uncommitted screenshots.
    - External side effects: none.
    - N/A notes: production acceptance not claimed.
  - Work Steps:
    1. Run compile/build, focused tests, sibling regressions, source hash, and browser evidence.
       - UI flow check: golden evidence, cluster/decision pack, draft and dashboard return.
       - DB/data flow check: canonical write oracle zero.
       - Render location check: no live controls.
       - Mini QA for each completed implementation slice (MUST): official JSON/Markdown report.
       - Evidence target: `E2-P2B-REGRESSION1`, `E2-P2B-BUILD1`.
    2. Refresh Anvien, run detect-changes, write coder/supervisor reports, and close the continuation plan.
       - UI flow check: N/A.
       - DB/data flow check: source hash unchanged and no canonical mutation.
       - Render location check: final status states owner decisions and cutover lock.
       - Mini QA for each completed implementation slice (MUST): supervisor review.
       - Evidence target: `E3-CLOSE1`.
  - Implementation Gate:
    - P2-A runtime evidence passes or records a concrete blocker; no live action is pending.
  - Acceptance:
    - Source: final diff and reports match the implemented scope.
    - Runtime/UI: browser artifact is current and visible.
    - DB/data: canonical oracle remains zero.
    - Behavior test: regressions and build pass or are explicitly bounded.
    - Cleanup/quarantine: unrelated worktree changes preserved.
    - Evidence IDs: `E2-P2B-REGRESSION1`, `E2-P2B-BUILD1`, `E3-CLOSE1`.
    - Actual-status rows refreshed: final continuation status.
  - Evidence Targets: final graph/detect output, hash, test logs, supervisor report, commit.
  - Actual-status Update: mark continuation complete only for staging/review scope.
  - Commit Boundary: commit after acceptance passes.
  - Actual result: official visible-browser evidence passed 6/6 actions on a clean local
    runtime; focused tests passed 27/27, full regression passed 113 with 2 existing
    environment-guarded skips, compileall and browser-script syntax checks passed, the
    source workbook hash remained unchanged, and the local health endpoint returned 200.
    Docker/production acceptance is intentionally not claimed.

- [x] Pn-A: Call supervisor for the implemented-plan acceptance loop.
  - Goal: verify the continuation scope against the Owner decision, source evidence, plan, diff, UI, and safety boundary.
  - Work Steps: inspect source/diff, re-run required evidence, write PASS/REJECT report, and return only to the failed slice if rejected.
  - Implementation Gate: P2-A and P2-B complete or explicitly blocked.
  - Acceptance: supervisor gives one bounded verdict with no false live claim.
  - Actual result: `reports/supervisor/rp_supervisor_260815_log_c06_owner-review-reconciliation.md`
    gives `PASS` for the bounded staging/review scope and explicitly keeps cutover locked.
- [x] Pn-B: Remove dead work created during this continuation.
  - Goal: retain only useful analysis, UI, tests, reports, and plan artifacts.
  - Work Steps: review generated output and remove only continuation-created dead files; preserve prior worktree changes; review cleanup.
  - Implementation Gate: only continuation-created artifacts are candidates.
  - Acceptance: no stale placeholder or rejected approach remains in the scoped diff.
  - Actual result: no debug marker or rejected implementation remains in the scoped
    files; official screenshots are not staged, and unrelated worktree content remains
    preserved outside the LOG-C06 path list.
- [x] Pn-C: Close the continuation plan.
  - Goal: finish evidence, benchmark, detect-changes, commit, and final status.
  - Work Steps: final build/QA/hash, Anvien detect-changes, reports, scoped commit, worktree check.
  - Implementation Gate: Pn-A and Pn-B pass or record blockers.
  - Acceptance: final report says staging/review PASS or bounded blocker; cutover remains locked.
  - Actual result: source hash, Anvien refresh/file-detail/impact/detect evidence,
    focused/full tests, compile/build, visible browser QA, coder report, supervisor
    report, and scoped commits are recorded. Final state is staging/review PASS with
    no Owner confirmation or canonical mutation.

## Continuation Slice P3: apply the confirmed Owner decisions in staging only

The previous P2 closure remains the baseline.  This P3 slice continues the
same LOG-C06 task after the Owner supplied six explicit business decisions;
it does not open a new Goal and does not authorize cutover.

- [x] P3-A: source evidence and impact gate
  - Confirmed the six CNY source values from the read-only workbook, including
    the C102/C109/C115/C190/C197/C198 received-group cells.
  - Refreshed Anvien and ran file-detail/impact for the review analysis,
    staging store, and opening model.  The affected LOG-C06 flows are bounded
    to those surfaces; canonical writers remain outside the change.
- [x] P3-B: deterministic Owner batch and lineage graph
  - Added a pure component/checkpoint graph for the 24,576 embedded credit,
    134,973 checkpoint, 159,998 derived paid-on-behalf group, and the
    416,482.2426005565 received-group expectation.
  - Added an audited, deterministic, retry-safe staging batch.  It applied 20
    source-row metadata actions representing the six Owner decisions and left
    row 96 (1,572 CNY) REVIEW_REQUIRED.
  - Raw workbook fields remain immutable; the batch reports zero canonical
    writes and keeps DRAFT / NOT_APPROVED / NOT_LIVE.
- [x] P3-C: draft opening and UI evidence seam
  - Opening draft now excludes embedded snapshot credit and checkpoint summary
    rows explicitly, while retaining BASE / SOURCE COMPONENTS + POST-BASE
    EVENTS lineage.
  - Historical checkpoint reconciliation retains the 67,033.84966649559 CNY
    source-vs-expectation difference as a visible material difference; it is
    not auto-filled.
  - Historical Review renders the Owner-confirmed reconciliation and its
    double-count protections.
- [x] P3-D: full build, visible browser QA, Anvien detect-changes, and supervisor
  - Must complete after the P3 code/tests settle.  Final acceptance is bounded
    to staging/review only; no live opening publication is allowed.
  - Actual result: full compile/build, focused tests, full regression, visible
    browser QA, source hash, Anvien refresh/detect-changes, and supervisor
    review completed.  The Owner batch is idempotent on replay; the six-row
    business decisions are applied to staging only; one material received-group
    difference remains explicit; cutover stays locked.

- [x] P3-E: final staging/review handoff
  - Result: `CONFIRMED=20`, `REVIEW_REQUIRED=170`, `RAW=39`,
    `NOT_APPLICABLE=60`; derived Owner-review states are
    `CONFIRMED=20`, `REVIEW_REQUIRED=77`, `UNKNOWN=132`,
    `NOT_APPLICABLE=60`.  Draft opening buckets are traceable and do not
    publish a current opening balance.
  - Remaining Owner pack is reduced to the `67,033.84966649559 CNY`
    received-group reconciliation difference plus the unresolved legacy
    checkpoint/source-lineage items.  No per-row manual processing is needed
    for the six confirmed decisions.

## Risk Notes

- `views/historical_review.py` has high Anvien risk and must receive only a small render/import seam.
- Arithmetic exactness does not prove ownership or allocation; the decision pack must keep that distinction visible.
- Source rows with inherited dates and unknown currency remain review/unknown even if arithmetic is clear.
- The formal P2P helper may remain limited by the prior locked cache; do not modify cache/P2P source.
- Docker is not a valid substitute for the local runtime when no repository Docker target exists; report the limitation.

## Continuation Slice P4: technical source-lineage reconciliation

The Owner's latest instruction corrects the prior handoff: the
`67,033.84966649559 CNY` difference is not yet an Owner question. This slice must
compare the six verified historical source rows against current staging records
cell-by-cell, then trace the separate row-86/E86 parser mismatch. It remains
strictly staging/review-only and must not create a balancing event.

- [x] P4-A: reproduce and document the six-source and E86 discrepancies
  - Goal: produce a deterministic side-by-side source/staging reconciliation for C102, C109, C115, C190, C197, and C198, and identify exactly where 7,683 CNY is sourced for row 86.
  - Work Steps:
    1. Read the read-only workbook source cells, raw values, notes, formula/cached values, merged/inherited context, and physical Excel rows for all six received items and E86.
    2. Load current staging records by source row/item ID and capture staged raw amount, normalized amount, confirmed amount, inclusion flag, classification, and exclusion reason.
    3. Calculate per-row deltas with Decimal arithmetic and prove whether their sum equals `67,033.84966649559 CNY`.
    4. Compare C115 against the historical `100,000,000 VND / 3,953 = 25,297.24260055654 CNY` reference without using current FX.
  - Implementation Gate: source hash is unchanged; Anvien graph is current; no production code has been edited; the diagnostic table identifies exact cells and staging IDs.
  - Acceptance: the six-source table and E86 trace are reproducible from source/staging evidence, including any residual unresolved row.
  - Actual result: physical source cells show the legacy oracle mapping `C190 -> Sheet2!C192`, `C197 -> Sheet2!C199`, and `C198 -> Sheet2!C200`; the pre-fix row deltas were `+105,549`, `-102,643.15033350437`, and `+64,128` CNY, summing to `67,033.84966649563` by Decimal arithmetic (the Owner display rounds this to `67,033.84966649559`). Row 86 selected `D86` text and parsed `7,683`; the authoritative numeric cell is `E86 = 99,824.43`.

- [x] P4-B: correct only deterministic parser/normalization defects
  - Goal: fix a proven wrong cell mapping, formula handling, row offset, or normalization defect without changing Owner-confirmed business meaning.
  - Work Steps:
    1. Trace the parser's selected amount cell and normalized proposal for row 86 back to the physical source row/cell and preserve any legitimate 7,683 component separately.
    2. If a deterministic defect is proven, patch the source parser/staging normalization at its owner, preserving raw workbook fields and prior review/audit history.
    3. Add direct regression tests for the six source rows, C115 FX handling, E86 formula/cached value handling, and no-balancing/no-canonical-write guards.
  - Implementation Gate: root cause is reproduced and file-detail/impact evidence covers every edited function or contract; no business reinterpretation is required.
  - Acceptance: corrected staging reproduces verified source amounts exactly where the source is authoritative, and all prior Owner classifications/lineage remain intact.
  - Actual result: parser v2 fixes the off-by-one cell provenance and rejects non-numeric formula/reference prose as amount text. Audited staging repair returns the three legacy aliases to `REVIEW_REQUIRED`, confirms the three correct late rows, and records row-86 E86 lineage without overwriting immutable raw evidence. Focused regression tests cover parser, store, mapping, FX context, and no-canonical-write behavior.

- [x] P4-C: regenerate checkpoints and non-live draft
  - Goal: rebuild the received group and historical checkpoint from the corrected lineage while retaining draft/cutover locks.
  - Work Steps:
    1. Recompute `C102+C109+C115+C190+C197+C198 = 416,482.2426005565 CNY` and classify the checkpoint as `RECONCILED` only if all six source rows match.
    2. Recompute `418,060.79 + 159,998 - received_group` and preserve the old M89 checkpoint as a superseded older snapshot, not an independent event.
    3. Run focused tests, full build/regression, visible browser QA if the rendered surface changes, source hash, Anvien detect-changes, and supervisor review.
  - Implementation Gate: P4-B tests pass and no canonical writer is in the diff or runtime path.
  - Acceptance: final report contains the six-row table, exact gap source or exact residual defect, E86 lineage, checkpoint relationships, draft position, and any genuinely remaining business ambiguity only.
  - Actual result: six-source received group is `RECONCILED` at `416,482.2426005565 CNY`; derived paid-on-behalf group is `159,998 CNY`; historical position reconstructs to `161,576.5473994435 CNY`; draft buckets and locks are regenerated with zero canonical mutation. Remaining Owner questions are limited to genuine unresolved review rows, not the former technical gap.

### P4 non-goals and safety locks

- No balancing transaction, guessed adjustment, current-FX recalculation, or business-meaning reinterpretation.
- No Owner request about the 67,033.8497 difference until the six source cells are fully compared.
- No source workbook mutation, canonical ledger mutation, migration, publication, approval/live cutover, Quick Entry, payment, or AI.

### P4 acceptance criteria

- The six-source reconciliation table reports source cell, row, raw value, note/context, staging item, staged/normalized/confirmed amounts, included amount, delta, classification, and reason.
- `SUM(DELTA)` either equals `67,033.84966649559 CNY` with row-level proof or the exact remaining discrepancy is identified.
- C190/C197/C198 total exactly `327,034 CNY` in source/staging comparison.
- C115 preserves the historical VND-to-CNY reference without current FX.
- E86 is proven as `99,824.43 CNY` or the source contradiction is explicitly documented; 7,683 cannot masquerade as E86.
- Old M89 and updated historical checkpoints have explicit supersession lineage.
- Corrected staging remains staging-only, raw provenance and audit history remain preserved, and regression tests prevent reintroduction.
- Final state remains `DRAFT / NOT_APPROVED / NOT_LIVE` with canonical mutation oracle zero.

## Continuation Slice P5: final cutover sufficiency and opening-impact review

The technical six-source reconciliation is complete. This slice determines
whether remaining historical rows can still change the verified opening. It
does not repeat the resolved lineage investigation, does not require every
staged row to become CONFIRMED, and does not authorize live publication.

- [x] P5-A: establish temporal scope and supersession contract
  - Goal: identify the effective date/scope of the verified base and every
    source range used by the snapshot, paid group, received group, and
    shipment-cost checkpoint.
  - Work Steps:
    1. Read workbook dates, section headers, structured SALE columns, source
       rows, and inherited-date context without inventing dates.
    2. Record the latest included physical event for each checkpoint and mark
       any checkpoint whose source cell/date is not provable.
    3. Build a deterministic supersession graph for the embedded credit,
       snapshot, component checkpoint, derived paid group, old M89, received
       group, and verified position.
  - Implementation Gate: source hash remains unchanged; temporal evidence is
    captured from workbook/staging provenance and not from prior reports.
  - Acceptance: output contains CHECKPOINT_AS_OF, latest event/date,
    SOURCE_RANGE, and TEMPORAL_CONFIDENCE with explicit unknowns.

- [x] P5-B: classify all staged rows by opening impact
  - Goal: assign every staged item to exactly one opening-impact category:
    embedded base, post-base confirmed, post-base review, reference-only,
    not-applicable, unresolved non-material, or unresolved material.
  - Work Steps:
    1. Preserve confirmed base lineage and classify snapshot/checkpoint rows
       as non-events.
    2. Scan physical rows after the verified scope, using structured SALE
       columns and section provenance rather than arbitrary free text.
    3. Separate missing shipment linkage and unknown currency from financial
       materiality; only rows capable of changing the CNY opening become
       UNRESOLVED_MATERIAL.
    4. Emit category counts and known-currency totals, plus a material-only
       Owner Decision Pack.
  - Implementation Gate: category precedence and date boundary are pure,
    deterministic, and covered by fixtures for embedded, reference,
    post-base, unknown shipment, unknown currency, and row 96.
  - Acceptance: every input item has one category; category counts sum to the
    input count; UNRESOLVED_MATERIAL_COUNT is independently reproducible.

- [x] P5-C: candidate opening and readiness gates
  - Goal: calculate VERIFIED BASE plus/minus confirmed post-base events and
    return READY_FOR_OWNER_APPROVAL only when no material ambiguity remains.
  - Work Steps:
    1. Keep the verified historical position as the sole base; do not rebuild
       all historical components or add superseded checkpoints.
    2. Apply post-base confirmed events exactly once and leave review events
       excluded from the candidate.
    3. Add readiness fields, proposed cutover-date options only when evidence
       supports them, and preserve NOT_APPROVED / NOT_LIVE / canonical-zero.
  - Implementation Gate: P5-A and P5-B outputs pass their invariants; no
    canonical writer is imported or called.
  - Acceptance: candidate opening formula is reproducible, material blockers
    are exact, and readiness is not derived from total REVIEW_REQUIRED alone.

- [x] P5-D: focused tests, QA, integrity review, and closure
  - Goal: prove the final sufficiency contract and keep LOG-C06 staging-only.
  - Work Steps:
    1. Add the ten requested focused test cases for base/reference,
       post-base, supersession, unknown linkage/currency, and canonical zero.
    2. Run focused/full unittest, compile/build, source hash, independent
       verifier, and visible review smoke if the draft surface changes.
    3. Refresh Anvien, run change detection, write fresh Data-Integrity and
       Supervisor artifacts, and commit only scoped outputs.
  - Implementation Gate: source and pure-analysis tests pass before any final
    verdict is written.
  - Acceptance: final status is either READY_FOR_OWNER_APPROVAL with the
    required locks or NOT_READY with only opening-material blockers listed.

P5 closure result: all 289 staging items classify exactly once. The category
counts are `19 EMBEDDED_IN_VERIFIED_BASE`, `0 POST_BASE_CONFIRMED`, `7
POST_BASE_REVIEW_REQUIRED`, `74 REFERENCE_ONLY`, `122 NOT_APPLICABLE`, `60
UNRESOLVED_NON_MATERIAL`, and `7 UNRESOLVED_MATERIAL`; opening-material blocker
count is 14. The candidate remains `161,576.5473994435 CNY` because no
post-base event is confirmed. Readiness is `NOT_READY` with
`DRAFT / NOT_APPROVED / NOT_LIVE`; focused/full tests, compileall, independent
verifier, smoke QA, fresh Data-Integrity, and Supervisor PASS evidence are
complete. No canonical mutation or live cutover occurred.

## Continuation Slice P6: beginner-first blocker reconstruction and Owner pack

P6 continues LOG-C06 only. It exhausts deterministic workbook/source
investigation for rows 201–205, 213–219, 229–230, the 418,060.79 provenance,
and the 1,572/1,578.5474 audit drift before escalating any genuine business
ambiguity. The verified base remains unchanged and no canonical or live action
is authorized.

- [x] P6-A: reconstruct blocker source context
  - Goal: produce a source-grounded record for every blocker with physical
    cell, date, shipment/vehicle, description, SALE, amount/freight cells,
    goods fields, direction, event type, neighboring-row relation, and
    embedded status.
  - Work Steps:
    1. Read complete workbook row/column context, merged/header structure,
       formulas, notes, and adjacent rows for each blocker.
    2. Join physical workbook cells to staging source references without
       treating row numbers as Owner-facing questions.
    3. Distinguish freight totals from goods value, weight, CBM, and unit-price
       fields; preserve unknown amount basis explicitly.
  - Implementation Gate: source workbook hash is unchanged and the output is
    read-only/deterministic.
  - Acceptance: all 14 blockers have a complete source-context record or an
    explicit evidence gap.

- [x] P6-B: recover grouped semantics and checkpoint provenance
  - Goal: resolve rows that are subtotals, operational details, grouped
    components, settlements, or already represented checkpoints.
  - Work Steps:
    1. Investigate 201–205 as a received/conversion group rather than assuming
       the aggregate is an A Bò payable.
    2. Investigate 213–219 for nearby freight totals, continuation/settlement
       rows, and section totals without manufacturing an amount.
    3. Investigate 229–230 for exact freight cells, currency, direction,
       ownership, and duplicate/embedded relationships.
    4. Trace 418,060.79 to source cells/formulas/components/date boundary; keep
       it Owner-gated only if deterministic evidence is exhausted.
    5. Reconcile 1,572 versus 1,578.5474 without changing opening.
  - Implementation Gate: prior verified lineage rules remain unchanged.
  - Acceptance: each blocker is either auto-resolved/non-material or remains
    a genuine business ambiguity with a documented reason.

- [x] P6-C: generate beginner-first minimal Owner Decision Pack
  - Goal: group related unresolved events into the fewest independent business
    decisions, using dates, shipment/lots, original descriptions, amounts,
    plain-language meaning, and bounded include/exclude effects.
  - Work Steps:
    1. Group only rows proven to share one shipment/financial event.
    2. Exclude rows fully resolved by source evidence or metadata-only gaps.
    3. Ask plain Vietnamese business questions; do not expose internal
       category names as the primary question.
  - Implementation Gate: deterministic investigation is complete and no
    spreadsheet row number is the sole Owner-facing identifier.
  - Acceptance: `OWNER_DECISION_COUNT` is minimal and every remaining item has
    a bounded scenario effect without cross-currency conversion.

- [x] P6-D: scenario opening, temporal boundary, tests, and closure review
  - Goal: recalculate bounded scenarios, determine the defensible opening date,
    and verify staging/canonical safety.
  - Work Steps:
    1. Keep the verified base as the sole base and apply only proven post-base
       events once.
    2. Return `LAST_EVENT_EMBEDDED_IN_BASE`, `FIRST_EVENT_NOT_EMBEDDED_IN_BASE`,
       `PROPOSED_OPENING_AS_OF_DATE`, and confidence.
    3. Add focused tests for source reconstruction, grouping, amount-basis
       safety, 1,572 audit drift, scenario arithmetic, and canonical zero.
    4. Run full regression, source hash, independent verifier, QA, fresh
       Data-Integrity, and Supervisor review before commit.
  - Implementation Gate: P6-A through P6-C invariants pass; no canonical writer
    is imported or called.
- Acceptance: final report contains only genuine Owner questions, preserves
    `NOT_READY` when needed, and does not start LOG-C07.

P6 closure result: the deterministic blocker sweep reduced the opening-impact
blocker set from 14 row-level records to 7 row-level records and from 7
unresolved-material rows to 0. Rows 213–219 are reference-only goods detail
because their H values sum to the exact H224 subtotal `16,929.56` and no
freight-total cell is present. Rows 201–205 remain one grouped Owner question
about the C conversion column versus the D chuyen-ho column; rows 229–230
remain one grouped Owner question about `5,610 + 1,450 = 7,060`, currency,
and payment direction. The 418,060.79 source-cell scan found no exact source
cell or unique provenance; 1,578.5474 is not a source event. The proposed
opening boundary is `2026-05-28` with LOW overall confidence because the
shipment-cost checkpoint date remains unproven. Candidate remains
`161,576.5473994435 CNY`; readiness remains `NOT_READY` and
`DRAFT / NOT_APPROVED / NOT_LIVE`. No canonical mutation or LOG-C07 work
occurred.

## Terminal closure — 2026-08-15

Owner roadmap decision closes LOG-C06 with `PRODUCT_PASS`. Historical staging,
historical provenance mechanism, Owner review, checkpoint reconstruction,
double-count protection, and cutover sufficiency are all `PASS`. Canonical
financial mutation is `0`; the historical A Bò opening is
`NOT_PUBLISHED`; cutover publication is `DEFERRED_OWNER_GATED`.

The value `161,576.5473994435 CNY` remains historical reconciled
candidate/checkpoint evidence only. Remaining source ambiguity is preserved in
`DEFERRED_HISTORICAL_RECONCILIATION` and is not guessed, deleted, balanced, or
published. LOG-C07 may start only as a new chat and must use whole-Logistics
product scope.
