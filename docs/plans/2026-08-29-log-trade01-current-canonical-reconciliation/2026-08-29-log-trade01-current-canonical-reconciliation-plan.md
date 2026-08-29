# LOG-TRADE01 current GitHub canonical reconciliation Plan

## Metadata

- Date: `2026-08-29`
- Status: `draft`
- Plan: `docs/plans/2026-08-29-log-trade01-current-canonical-reconciliation/2026-08-29-log-trade01-current-canonical-reconciliation-plan.md`
- Evidence: `docs/plans/2026-08-29-log-trade01-current-canonical-reconciliation/2026-08-29-log-trade01-current-canonical-reconciliation-evidence.md`
- Benchmark: `docs/plans/2026-08-29-log-trade01-current-canonical-reconciliation/2026-08-29-log-trade01-current-canonical-reconciliation-benchmark.md`
- Actual status: `docs/plans/2026-08-29-log-trade01-current-canonical-reconciliation/2026-08-29-log-trade01-current-canonical-reconciliation-actual-status.md`

## Goal

Reconcile the Supervisor-reviewed LOG-TRADE01 candidate onto the freshly
verified GitHub `main` that now contains LOG-SKILL01. Preserve current
LOG-SKILL01 canonical work, preserve the verified trade-compliance domain and
its focused tests, resolve the single documentation overlap, and stop at a
fresh Owner Gate candidate.

## Rules

- Fresh remote `main` is the authority before every mutation.
- The current canonical base is first parent; no reset, rebase, squash, or
  destructive cleanup.
- The old trade candidate is a source snapshot, not a promotion authority.
- Keep `core/trade_compliance` independent unless a direct low-risk compatible
  contract reuse is proven; do not force coupling to LOG-SKILL01.
- Preserve all trade fail-closed/provenance/tax semantics and all LOG-SKILL01
  contracts.
- Do not touch P2P core, production, secrets, deployment, push, or merge to
  the canonical branch.
- Validation is focused only; no broad regression.

## Problem

The old trade candidate was based on `bddcf24e...`, while current GitHub
`main` advanced to `f99bec21...` with LOG-SKILL01. The two deltas overlap only
at the daily notes file. The trade implementation and focused tests must be
carried forward without replacing newer canonical skill files.

## Scope

- Freshly resolve remote `main` and bind the reconciliation base.
- Compare exact old-trade and current-main path/blob deltas.
- Preserve current `skills/logistics/**` and its focused tests.
- Bring the old `core/trade_compliance/**`, trade fixtures/tests, and bounded
  evidence into a branch whose first parent is current `main`.
- Reconcile the overlapping daily notes without dropping either workstream.
- Inspect LOG-SKILL01 contracts for reuse; record `NONE` when independent
  trade identity needs make direct reuse non-clean.
- Run only trade and directly relevant LOG-SKILL01 focused validation, affected
  non-writing compile, diff hygiene, and one exact-subject Supervisor review.

## Non-Goals

- No global tariff/legal database, crawler, live source adapter, UI wiring,
  database, OCR, document AI, country adapters, framework, or P2P work.
- No automatic legal conclusion, final HS classification, promotion, push,
  deployment, production change, or canonical-branch merge.

## Requirements

- `CURRENT_MAIN_SHA/TREE` must be freshly verified before mutation.
- Overlap must be mechanically enumerated and classified.
- LOG-SKILL01 source/test blobs must remain unchanged.
- Trade source/test blobs must remain identical to the reviewed candidate
  unless a directly required compatibility fix is evidenced.
- The official registry remains discovery-only and provenance-preserving.
- Candidate must have current `main` as its first-parent base, exact SHA/tree,
  clean index/worktree, and an independent review over that exact object.

## Acceptance Criteria

- Current main is fresh and preserved; overlap is `DOCUMENTATION_ONLY`.
- `LOG_SKILL01_REUSE_AFTER_RECONCILIATION=NONE` is justified by the clean
  independent boundary, or a minimal reuse is proven without coupling drift.
- Focused trade evidence remains PASS, including ambiguity, ISO 13485,
  regulatory measures, tariff fail-closed, tax trace, and provenance.
- No source/test change occurs after the final Supervisor review.
- Candidate is local-only, clean, exact-subject reviewed, and Owner Gate ready.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: bind current GitHub authority and classify the old/current deltas.
  - Work Steps: verify remote SHA/tree; compare path sets; compare old
    post-review source/test blobs; inspect LOG-SKILL01 contracts; record the
    independent-boundary decision in actual status.
  - Implementation Gate: current remote is known and not beyond the recorded
    authority; no code mutation has started.
  - Acceptance: actual status records the one overlapping notes path,
    documentation-only classification, and preserve/edit touch map.

### P1: Reconcile canonical main and trade foundation

- Phase Goal: produce a current-main-first branch containing both canonical
  workstreams with no semantic source/test drift.
- Phase Boundary:
  - In scope: one task worktree, old trade candidate delta, one notes merge,
    reconciliation evidence.
  - Out of scope: new trade behavior, LOG-SKILL01 refactor, UI/runtime,
    P2P, production, push, deployment.
  - Dependencies: P0-A authority and overlap classification.
- Phase Implementation Rule: implement `P1-A`, verify and record it, then
  implement `P1-B`; do not implement the phase directly.
- Ordered Slice List:
  - P1-A: Preserve current-main LOG-SKILL01 and import old trade snapshot.
  - P1-B: Resolve the shared notes file and update reconciliation evidence.

- [ ] P1-A: Preserve current-main LOG-SKILL01 and import old trade snapshot.
  - Goal: make current GitHub `main` the first-parent base while carrying the
    old trade implementation without rebuilding it.
  - Scope Boundary:
    - Editable: merge metadata and old trade paths absent from current main.
    - Inspect-only: `skills/logistics/**`, LOG-SKILL01 tests and contracts.
    - Preserve-only: all current-main skill files and test blobs.
    - Out of scope: shared-contract refactor and runtime wiring.
  - Non-Goals: no new trade behavior or direct import of LOG-SKILL01 modules.
  - Pre-flight Questions:
    - Data source: exact old candidate `bd2c2ffd...` and current `main`.
    - Display permission: N/A; pure domain/repository work.
    - DB read flow: N/A; no database.
    - DB write flow: N/A; no runtime writes.
    - Render location: N/A; no UI.
    - UI behavior flow: N/A; no UI.
    - Docker runtime: N/A; no runtime change.
    - Playwright target: N/A; no UI/runtime change.
    - Behavior test: existing trade focused unittest plus LOG-SKILL01 focused tests.
    - Cleanup/quarantine: preserve owner worktrees; no destructive cleanup.
    - External side effects: no push, deploy, or production action.
    - N/A notes: merge is local and uses existing Git history.
  - Work Steps:
    1. Create a branch from freshly verified current `main` in the existing
       task worktree, then merge the old trade candidate as a second parent.
       - UI flow check: N/A.
       - DB/data flow check: verify exact source/test blobs and first-parent base.
       - Render location check: N/A.
       - Evidence target: current-main first-parent and path inventory.
    2. Inspect merged source/tests and the LOG-SKILL01 contracts for accidental
       coupling or semantic drift.
       - UI flow check: N/A.
       - DB/data flow check: compare blobs and focused contract surfaces.
       - Render location check: N/A.
       - Evidence target: source/test preservation and reuse decision.
  - Implementation Gate:
    - P0-A records `DOCUMENTATION_ONLY` overlap and no source/test overlap.
    - Anvien/source checks are run for any changed implementation surface.
  - Acceptance:
    - Source: current `main` skill paths and old trade source/test paths coexist.
    - Runtime/UI: N/A; no runtime wiring claimed.
    - DB/data: N/A; no persistent data.
    - Behavior test: existing focused tests remain applicable.
    - Cleanup/quarantine: worktree remains isolated and owner root untouched.
    - Evidence IDs: `E0-P0A-AUTH1`, `E0-P0A-DIFF1`, `E0-P0A-BLOB1`.
    - Actual-status rows refreshed: LOG-SKILL01 preserve-only and trade bound.
  - Evidence Targets: exact tree/path/blob comparisons and source inspection.
  - Actual-status Update: `missing` trade surfaces become `bound-correct`.
  - Commit Boundary: local reconciliation checkpoint after P1-B passes.

- [ ] P1-B: Resolve the shared notes file and update reconciliation evidence.
  - Goal: preserve both LOG-SKILL01 and LOG-TRADE01 history in the one
    overlapping documentation path without changing code semantics.
  - Scope Boundary:
    - Editable: shared daily notes and new reconciliation plan/evidence docs.
    - Inspect-only: all source/test blobs.
    - Preserve-only: both workstream histories.
    - Out of scope: unrelated notes and old plans.
  - Non-Goals: no source/test edit and no report claims beyond observed facts.
  - Pre-flight Questions:
    - Data source: both exact notes blobs from old candidate and current main.
    - Display permission: N/A.
    - DB read/write flow: N/A.
    - Render location: N/A.
    - UI behavior flow: N/A.
    - Docker/Playwright: N/A.
    - Behavior test: no new behavior; source/test blob proof.
    - Cleanup/quarantine: no deletion of either note history.
    - External side effects: none.
    - N/A notes: documentation-only reconciliation.
  - Work Steps:
    1. Combine the two notes histories and record the reconciliation decision,
       current authority, reuse classification, and validation ceiling.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: notes diff and diff check.
    2. Refresh evidence, benchmark, and actual-status records for the final
       candidate and its exact review boundary.
       - UI flow check: N/A.
       - DB/data flow check: N/A.
       - Render location check: N/A.
       - Evidence target: final SHA/tree and clean-worktree proof.
  - Implementation Gate:
    - Only the known notes overlap is edited; no production/test path changes.
  - Acceptance:
    - Source: no source/test changes beyond the imported unchanged trade blobs.
    - Runtime/UI: N/A.
    - DB/data: N/A.
    - Behavior test: N/A; docs-only slice.
    - Cleanup/quarantine: both notes histories remain represented.
    - Evidence IDs: `E1-P1A-MERGE1`, `E1-P1B-DOC1`.
    - Actual-status rows refreshed: overlap resolved.
  - Evidence Targets: docs-only diff and UTF-8/no-BOM check.
  - Actual-status Update: notes path becomes reconciled documentation.
  - Commit Boundary: include only reconciled implementation/evidence artifacts
    in the final local candidate commit.

- [ ] Pn-A: Call Supervisor for the exact final candidate.
  - Goal: review the frozen final SHA/tree, current-main ancestry, delta, clean
    state, and preservation claims.
  - Work Steps: finish candidate docs; freeze SHA/tree; check clean status;
    run one independent identity/source review; do not mutate afterward.
  - Implementation Gate: focused validation and final commit are complete.
  - Acceptance: exact-subject Supervisor PASS and Owner Gate remains required.

## Risk Notes

- Current main may advance again; if so, rebind to newest official main and do
  not bind this candidate.
- The shared notes file is documentation-only, but both histories must remain.
- LOG-SKILL01 customer intake is a shipment checklist, not a complete product
  identity contract; direct coupling is intentionally not inferred.
- The trade registry remains discovery-only and contains no live tariff rates.

