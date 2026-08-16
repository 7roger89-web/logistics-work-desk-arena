# P2P Execution Ledger Plan

## Metadata

- Date: `2026-08-10`
- Status: `in_progress`
- Plan: `docs/plans/2026-08-10-p2p-execution-ledger/2026-08-10-p2p-execution-ledger-plan.md`
- Evidence: `docs/plans/2026-08-10-p2p-execution-ledger/2026-08-10-p2p-execution-ledger-evidence.md`
- Benchmark: `docs/plans/2026-08-10-p2p-execution-ledger/2026-08-10-p2p-execution-ledger-benchmark.md`
- Actual status: `docs/plans/2026-08-10-p2p-execution-ledger/2026-08-10-p2p-execution-ledger-actual-status.md`

## Goal

Implement a persistent, append-only, tamper-evident P2P execution ledger for Logistics_App_Copy that records governed quorum runtime evidence and fails closed when identity, distinctness, evidence, or gate requirements are not met.

## Rules

- Complete P0 actual status before implementation work.
- Do not modify business logic, database code, credentials, FACT_LEDGER, Live Specs, governance policies, role definitions, or protected runtime scripts.
- Never fabricate a runtime/session identifier; preserve `UNKNOWN` or `UNAVAILABLE` when host evidence is absent.
- A coordinator summary is not independent runtime proof; real host subagent evidence remains authoritative.
- Ledger records are immutable: a duplicate run id is rejected and tampering is detectable by hash verification.
- Generated fixtures contain no customer data, secrets, or raw transcripts.
- Update evidence and actual-status after each implementation slice.
- Run Anvien when available; this repository is not currently indexed, so direct source inspection is the documented fallback.

## Problem

The installed P2P workflow describes an execution ledger but currently persists only a synthetic quorum fixture. There is no reusable record schema, immutable persistence boundary, automatic validation API, or project eval coverage for duplicate threads, substitutions, simulation, missing evidence, tampering, supervisor disagreement, and small-quorum correctness.

## Scope

- New `.p2p/execution-ledger/` package and schema.
- A coordinator-facing governed-run adapter that validates runtime evidence and writes exactly one immutable record.
- Safe synthetic fixtures and twelve focused ledger evals, while preserving existing eval cases and governance hashes.
- Fresh real-agent runtime proof for the eight named custom profiles and one small real quorum proof.
- Doctor, drift, eval, tamper, baseline, and supervisor verification evidence.

## Non-Goals

- No changes to application behavior, app database, authentication, credentials, network, hooks, proxying, cloud memory, or deployment.
- No changes to protected agent profiles, P2P skill text, governance policies, FACT_LEDGER, Live Specs, or installed governance scripts.
- No storage of raw agent transcripts or sensitive prompt content.

## Requirements

- Schema includes schema version, run id, timestamps, project/root, task/invocation, required and actual agents, profile names, thread ids, per-agent status/timing/scope/evidence references, missing/substitution/simulation flags, identity validation, quorum count/verdict, eval/gate/approval/drift fields, missing evidence, UNKNOWN values, supervisor verdict, provenance, and record hash.
- Runtime identity is verified only when the host supplies a distinct thread id and exact returned identity for the configured custom profile.
- Required-agent equality, unique thread ids, evidence presence/hash, and gate status are enforced before PASS.
- Small quorums use the declared required set; they are never silently upgraded to eight.
- Records are written beneath `.p2p/execution-ledger/runs/` with exclusive creation and deterministic canonical hashing.
- Validation detects changed bytes, duplicate identities, generic/renamed substitutes, simulation-only output, missing evidence, and supervisor claims that contradict the ledger.

## Acceptance Criteria

- A valid governed run automatically writes one persistent ledger record and returns PASS only when all declared checks pass.
- Twelve ledger evals pass for valid cases and fail closed for each negative case listed in the user brief.
- Fresh real runtime evidence contains eight distinct resolved custom threads with exact identities and a persisted PASS record.
- Existing project eval, RAG, doctor, drift, and protected baseline hashes remain passing/unchanged.
- Supervisor review finds no residual same-invariant unverified surface; otherwise the final status is NOT READY/blocked, not PASS.

## Checklist

- [x] P0-A: Complete actual status before implementation work.
  - Goal: classify the current runtime, persistence, eval, and protected-boundary surfaces.
  - Work Steps: inspect `.p2p/evals`, `.agents/skills/p2p-quorum`, `.codex/agents`, governance locks, and Anvien availability; record missing/partial/correct surfaces and downstream decisions.
  - Implementation Gate: actual-status records evidence IDs and confirms the editable boundary.
  - Acceptance: ledger absence and protected-path constraints are explicitly documented.

### P1: Ledger implementation

- Phase Goal: create and exercise the reusable immutable ledger without changing protected runtime artifacts.
- Phase Boundary:
  - In scope: `.p2p/execution-ledger/`, its schema, adapter, direct tests, and eval fixtures.
  - Out of scope: application code, governance tree, role profiles, and external services.
  - Dependencies: P0 status, Python standard library, existing eval harness conventions.
- Phase Implementation Rule: implement P1-A, verify it, refresh status, then P1-B and P1-C.
- Ordered Slice List:
  - P1-A: immutable schema, canonical hashing, validation, and CLI/API.
  - P1-B: governed-run adapter and runtime evidence contract.
  - P1-C: twelve fail-closed ledger evals and report generation.
  - P1-D: append-only quorum lifecycle and protected skill-boundary integration.
  - P1-E: existing pre-release gate enforcement for final ledger evidence.

- [x] P1-A: Immutable schema, hashing, validation, and CLI/API
  - Goal: provide one source of truth for records and deterministic validation.
  - Scope Boundary:
    - Editable: `.p2p/execution-ledger/schema.json`, `ledger.py`, focused tests.
    - Inspect-only: protected governance and agent profile paths.
    - Preserve-only: existing application and eval artifacts.
    - Out of scope: host thread spawning and external writes.
  - Non-Goals: no database migration, no network service, no transcript persistence.
  - Pre-flight Questions: Can the module validate both full and small quorums? Can it distinguish missing host evidence from a failed agent? Can exclusive creation and hash verification be proven without touching protected paths?
  - Work Steps:
    1. Define the versioned record contract and canonical serialization; test required fields, enum states, exact required-agent matching, uniqueness, evidence references, and supervisor/gate consistency.
    2. Add exclusive immutable persistence, record hash verification, CLI commands, and direct positive/negative tests; use only temporary eval directories for test writes.
  - Implementation Gate: target files are new and outside installed protected paths; Anvien limitation is recorded.
  - Acceptance:
    - Source: schema and validator enforce every required invariant.
    - Runtime/UI: N/A; this is a local CLI/library boundary.
    - DB/data: immutable file creation and tamper detection pass in a temporary quarantine.
    - Behavior test: valid, duplicate, malformed, and tampered records produce the specified verdicts.
    - Cleanup/quarantine: tests use isolated temp roots and remove them after verification.
    - Evidence IDs: E1-P1A-SRC1..E1-P1A-TEST4.
    - Actual-status rows refreshed: ledger core `missing -> correct`.
  - Evidence Targets: schema, source inspection, unit/CLI test output, and hash checks.
  - Actual-status Update: refresh ledger core and persistence boundary rows.
  - Commit Boundary: commit after acceptance if repository commit is authorized; otherwise retain a clean evidence boundary.

- [ ] P1-B: Governed-run adapter and runtime evidence contract (blocked at protected host hook)
  - Goal: make the normal coordinator handoff write a record from host-provided runtime evidence rather than model memory.
  - Scope Boundary:
    - Editable: adapter and documented evidence input under `.p2p/execution-ledger/`.
    - Inspect-only: collaboration host and installed quorum skill.
    - Preserve-only: existing synthetic fixture.
    - Out of scope: changing protected skill text or host tooling.
  - Non-Goals: the adapter cannot invent thread ids or spawn agents from Python.
  - Pre-flight Questions: Is host evidence available? If not, does the adapter return UNKNOWN/FAIL rather than synthesize proof? Does the persisted path and hash appear in the result?
  - Work Steps:
    1. Implement an adapter that accepts a coordinator-captured runtime evidence JSON, validates exact profiles/threads/identities/evidence/gates, and persists a new record with provenance.
    2. Exercise the adapter first with a real small quorum and then with the exact eight-agent runtime; retain host thread ids and returned identities without raw transcripts.
  - Implementation Gate: no changes to `.agents`, `.codex`, `.p2p/system`, or role definitions are needed.
  - Acceptance:
    - Source: adapter calls the immutable writer on every governed run completion.
    - Runtime/UI: N/A; host subagent UI is the runtime evidence source.
    - DB/data: one record per run, no overwrite, persisted path and hash returned.
    - Behavior test: missing/duplicate/substituted/simulated evidence cannot PASS.
    - Cleanup/quarantine: synthetic inputs stay under `.p2p/evals`; real proof uses the project ledger only.
    - Evidence IDs: E1-P1B-SRC1..E1-P1B-RUNTIME2.
    - Actual-status rows refreshed: adapter `unbound -> bound-correct` or `blocked` if host evidence is unavailable.
  - Evidence Targets: adapter result, real host thread list, persisted record, and validation output.
  - Actual-status Update: document whether protected host integration is available or remains a boundary limitation.
  - Commit Boundary: commit after acceptance if authorized.

- [x] P1-C: Twelve ledger evals and report
  - Goal: prove valid behavior and every specified fail-closed path with safe fixtures.
  - Scope Boundary:
    - Editable: `.p2p/evals/` ledger test runner, fixtures, reports, and suite additions.
    - Inspect-only: existing project code and governance baseline.
    - Preserve-only: previous 18-case eval evidence and hashes.
    - Out of scope: application behavior and external deployment.
  - Non-Goals: no real customer data or raw agent transcript capture.
  - Pre-flight Questions: Do negative cases assert the ledger verdict, not merely an exception? Are record files unique and tamper checks independent of the writer?
  - Work Steps:
    1. Add the twelve safe synthetic cases: valid 8, missing one, duplicate, generic, renamed, simulated, missing evidence, supervisor conflict, no overwrite, tamper, small quorum, and valid final PASS.
    2. Run them in isolated trials, emit hashes/reports, extend the project eval suite without rewriting prior baseline evidence, and validate the suite.
  - Implementation Gate: all fixtures are deterministic, local, and outside protected governance paths.
  - Acceptance:
    - Source: all twelve cases map to concrete validator behavior.
    - Runtime/UI: N/A.
    - DB/data: no application data touched; temporary ledger roots are quarantined.
    - Behavior test: 12/12 expected outcomes.
    - Cleanup/quarantine: temp runs are removed; durable eval evidence is immutable and hashed.
    - Evidence IDs: E1-P1C-EVAL1..E1-P1C-EVAL12.
    - Actual-status rows refreshed: eval coverage `partial -> correct`.
  - Evidence Targets: ledger eval report, suite validation, baseline hash comparison.
  - Actual-status Update: record final coverage and any blocked integration claims.
  - Commit Boundary: commit after acceptance if authorized.

- [x] P1-D: Append-only quorum lifecycle and protected skill-boundary integration
  - Goal: start a durable logical ledger run at normal quorum entry, append real agent evidence, and finalize the same run id after supervisor verdict without overwriting history.
  - Scope Boundary:
    - Editable: `.p2p/execution-ledger/quorum_runtime.py`, `.p2p/execution-ledger/ledger.py`, `.p2p/execution-ledger/schema.json`, `.agents/skills/p2p-quorum/SKILL.md`.
    - Inspect-only: host collaboration implementation beyond the skill boundary.
    - Preserve-only: role briefs, application code, FACT_LEDGER, Live Specs, and unrelated skills.
    - Out of scope: hooks, external connectors, deployment, or new release systems.
  - Non-Goals: no hook is added while the skill/runtime boundary can reliably enforce lifecycle calls.
  - Work Steps:
    1. Add a hash-chained append-only lifecycle journal and final materialization that preserves the same run id and rejects missing/duplicate/substituted evidence.
    2. Update the normal quorum skill contract so every mode starts, records, and finalizes the ledger before returning to the user.
  - Implementation Gate: user approval in the current goal explicitly covers these protected runtime/skill changes.
  - Acceptance:
    - Source: lifecycle commands and skill instructions form a complete start → agent → supervisor → final path.
    - Runtime/UI: one small local lifecycle smoke proves start/finalize; one final real eight-agent run proves host evidence.
    - DB/data: append-only journal and immutable final record preserve tamper/overwrite protections.
    - Behavior test: all seven fail-closed negatives and one valid PASS remain green through lifecycle finalization.
    - Cleanup/quarantine: synthetic lifecycle roots are temporary; final proof uses `.p2p/execution-ledger/runs/`.
    - Evidence IDs: E1-P1D-SRC1..E1-P1D-RUNTIME2.
    - Actual-status rows refreshed: adapter `unbound/blocked -> bound-correct`.
  - Evidence Targets: journal verification, skill diff, lifecycle smoke, final proof record.
  - Actual-status Update: record the approved protected boundary and whether hooks remained disabled.
  - Commit Boundary: commit after lifecycle and skill verification.

- [x] P1-E: Existing pre-release gate enforcement for final ledger evidence
  - Goal: make `p2p_gate.py prepare/finalize` block missing or failing execution-ledger evidence while retaining project eval and RAG checks.
  - Scope Boundary:
    - Editable: `.p2p/system/scripts/p2p_gate.py`, `.p2p/project-policy.json`, safe eval helper/fixtures needed to exercise the existing gate.
    - Inspect-only: release approval policy semantics except required ledger binding.
    - Preserve-only: p2p approval workflow and application code.
    - Out of scope: second release system or approval bypass.
  - Non-Goals: no release/deployment is performed; only technical gate behavior is tested.
  - Work Steps:
    1. Require an explicit, hash-validated final PASS ledger record when the project release gate is enabled; bind its hash into the technical report and finalization recheck.
    2. Add missing/failing/valid ledger gate checks to the existing synthetic gate tests and run the existing p2p_gate workflow.
  - Implementation Gate: current project policy and p2p_gate are the only release authority; no new gate framework is introduced.
  - Acceptance:
    - Source: p2p_gate exposes execution-ledger status in its existing technical report.
    - Runtime/UI: N/A; local release technical gate only.
    - DB/data: no application data touched.
    - Behavior test: missing/failing ledger blocks; valid final ledger lets technical gates PASS.
    - Cleanup/quarantine: gate outputs use isolated `.p2p/gates` directories and no approval is self-recorded.
    - Evidence IDs: E1-P1E-SRC1..E1-P1E-TEST3.
    - Actual-status rows refreshed: release enforcement `missing -> correct`.
  - Evidence Targets: technical gate reports, negative/positive gate outputs, final hash recheck.
  - Actual-status Update: record release gate integration without executing a release.
  - Commit Boundary: commit after gate tests pass.

### P2: Verification and handoff

- [x] P2-A: Full verification, supervisor review, and closure evidence
  - Goal: independently verify implementation, real runtime proof, protected baselines, and fail-closed negatives.
  - Work Steps: run ledger tests, doctor, drift, project eval, RAG check, baseline hash comparison, and a fresh supervisor review; record limitations honestly.
  - Implementation Gate: P1 slices are complete or explicitly blocked.
  - Acceptance: overall verdict is PASS only when persistent runtime integration and all evidence requirements are proven; otherwise NOT READY with blocker. **PASS achieved for the approved hardening scope; release/deployment remains unapproved.**

- [ ] Pn-A: Supervisor acceptance loop.
- [ ] Pn-B: Remove dead work created during this plan.
- [ ] Pn-C: Close the plan with final evidence and status.

## Risk Notes

- Host-level collaboration tools may expose thread ids only to the coordinator; if no durable hook exists, the adapter must report the boundary as UNKNOWN rather than claiming automatic host enforcement.
- Existing worktree changes are unrelated user work and must not be reset or folded into this scope.
- Any need to edit protected `.agents`, `.codex`, or `.p2p/system` architecture requires a separate user approval gate and stops this plan.
