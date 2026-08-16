# P2P Execution Ledger Actual Status

Title: P2P Execution Ledger
Date: 2026-08-10
Status: PASS for approved hardening scope. Core implementation, lifecycle integration, release-gate enforcement, final runtime proof, and supervisor review complete; no release/deployment performed.
Companion plan: `docs/plans/2026-08-10-p2p-execution-ledger/2026-08-10-p2p-execution-ledger-plan.md`
Companion evidence: `docs/plans/2026-08-10-p2p-execution-ledger/2026-08-10-p2p-execution-ledger-evidence.md`
Companion benchmark: `docs/plans/2026-08-10-p2p-execution-ledger/2026-08-10-p2p-execution-ledger-benchmark.md`

## Purpose

This is the current-state classification before and during implementation. It does not replace the evidence ledger.

## Scope

Target scope:

- Persistent ledger schema, validator, immutable writer, governed-run adapter, and project evals under `.p2p/execution-ledger` and `.p2p/evals`.

Out of scope:

- Application code, business data, credentials, custom-agent profiles, FACT_LEDGER, Live Specs, and release/deployment execution. The explicitly approved quorum skill, project policy, existing `p2p_gate`, and runtime lock were in scope for P1-D/P1-E.

## Relationship / Impact Evidence

Anvien is unavailable for this repository because it is not indexed (`E0-P0A-SRC4`). Direct source/topology inspection is used instead.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `.p2p/execution-ledger/` | E0-P0A-SRC1 | 0 existing | missing package; new local boundary | low outside protected runtime |
| `.p2p/evals/build_eval.py` | E0-P0A-SRC1 | direct eval consumer | existing synthetic harness and 18 cases | medium; preserve prior evidence |
| `.p2p/evals/fixtures/quorum-runtime.json` | E0-P0A-SRC1 | consumed by quorum checks | synthetic/previous runtime summary | medium; preserve as historical fixture |
| `.codex/agents/*.toml` | E0-P0A-SRC2 | eight profiles | host-resolved custom profiles | preserve-only; protected |
| `.p2p/system/governance/*` | E0-P0A-SRC3 | protected governance tree | FACT_LEDGER/Live Specs/locks/policies | do-not-touch |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already satisfies the requirement. | Preserve and verify. |
| `partial` | Some behavior exists but required pieces are missing. | Add only missing pieces. |
| `missing` | Required surface does not exist. | Implement within approved boundary. |
| `unbound` | Surface exists but is not wired to the real source. | Bind through adapter or record blocker. |
| `blocked` | Required authority or host evidence is unavailable. | Stop or preserve UNKNOWN. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Ledger schema/validator | `.p2p/execution-ledger/schema.json` + `ledger.py` | versioned schema and fail-closed validator | correct | new package | E1-P1A-SRC1, E1-P1A-TEST1..TEST4 | preserve and verify |
| Immutable persistence | `.p2p/execution-ledger/runs/` exclusive writer and SHA-256 | one immutable record per run, tamper detection | correct | one real pending record plus temp eval records | E1-P1A-TEST2..TEST3, E1-P1B-RUNTIME2 | preserve and verify |
| Governed-run adapter | `adapter.py` plus skill lifecycle boundary | every governed quorum completion records/finalizes the same run id | correct | lifecycle is bound at the approved skill boundary | E1-P1B-SRC1, E1-P1D-SRC1..RUNTIME2 | preserve and verify |
| Quorum lifecycle boundary | `quorum_runtime.py` start/record/finalize/verify | same run id starts, records agents, and finalizes after supervisor | correct | append-only journal plus immutable record | E1-P1D-SRC1..RUNTIME2 | preserve and verify |
| Pre-release ledger gate | `p2p_gate.py` execution-ledger gate | missing/failing ledger blocks technical PASS | correct | existing gate now binds final record hash | E1-P1E-SRC1..TEST3 | preserve and verify |
| Existing quorum fixture | eight exact names and prior thread paths | preserved as historical synthetic evidence | correct for fixture | 8 entries | E0-P0A-SRC1, E0-P0A-SRC2 | preserve-only |
| Ledger eval coverage | 18 general cases plus new 12-case ledger suite | twelve explicit ledger cases | correct | secondary suite + 4 trials/case | E1-P1C-EVAL1..12 | preserve and re-run when code changes |
| Protected governance baseline | installed, approved runtime lock updated, and drift-clean | no unapproved drift | correct | protected tree | E0-P0A-SRC3, E2-P2A-DRIFT1 | preserve-only |
| Anvien impact graph | repository not indexed | impact evidence if available | blocked/unavailable | N/A | E0-P0A-SRC4 | direct inspection fallback; do not block local ledger |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-10 | baseline before implementation | ledger, adapter, eval, protected boundaries | initial classification | E0-P0A-SRC1..SRC4 | proceed with P1-A; keep host hook as explicit risk |
| R1 | 2026-08-10 | after core/eval implementation and fresh runtime | ledger, adapter, eval, host evidence | missing -> correct; partial -> correct; adapter remains unbound/blocked | E1-P1A-TEST1..TEST4, E1-P1B-RUNTIME1..RUNTIME2, E1-P1C-EVAL1..12, E1-P1B-BLOCK1 | stop before protected skill change; request approval |
| R2 | 2026-08-10 | explicit user approval in current goal | lifecycle boundary and release gate | adapter remains partial; lifecycle/release gate missing -> scheduled edit | current goal approval; E1-P1B-BLOCK1 | proceed with P1-D then P1-E only |
| R3 | 2026-08-10 | after approved integration and final verification | lifecycle, release gate, final runtime, supervisor | missing/unbound -> correct; final hardening verdict PASS | E1-P1D-SRC1..RUNTIME2, E1-P1E-SRC1..TEST3, E2-P2A-SUPERVISOR1, E2-P2A-FINAL1 | close approved hardening; preserve; no release |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `.p2p/execution-ledger/*` | none | source of truth | P1-A/P1-B | edit | E0-P0A-SRC1 | no secrets/transcripts |
| `.p2p/evals/build_eval.py` | `.p2p/evals/suite.json` | test/eval consumer | P1-C | edit | E0-P0A-SRC1 | preserve old evidence hashes |
| `.p2p/evals/fixtures/*` | `.p2p/evals/evidence/*` | safe fixtures/evidence | P1-C | edit/generate | E0-P0A-SRC1 | isolated/quarantined |
| `.codex/agents/*.toml` | `.agents/skills/p2p-quorum/*` | runtime profiles/contract | P1-B/P1-D/P2-A | inspect-only/preserve profiles; approved contract edit | E0-P0A-SRC2, E1-P1D-SRC2 | no profile edits |
| `.p2p/system/governance/*` | `.p2p/system/scripts/*` | protected runtime | P1-E/P2-A | approved gate/lock edit; validate-only otherwise | E0-P0A-SRC3, E1-P1E-SRC1, E2-P2A-DRIFT1 | no promotion or release |

## Detailed Findings

### Ledger package

Current state: persistent schema, validator, exclusive writer, adapter, and twelve-case eval suite are implemented and verified.

Required state: a reusable local component must accept coordinator-captured runtime evidence, validate exact profile/thread identity and gate evidence, and persist an immutable hash-checked record.

Evidence:

- E0-P0A-SRC1: repository search and directory inspection.

Classification: `correct`.

Allowed next action: preserve and independently re-verify; no application or governance edits are needed.

Forbidden next action: edit protected governance or application paths.

### Host integration

Current state: the installed skill requires a coordinator execution ledger; the approved lifecycle boundary starts, records, finalizes, and verifies governed runs, while the adapter persists coordinator-captured evidence.

Required state: adapter-driven persistence with honest `UNKNOWN`/`UNAVAILABLE` when host evidence is absent.

Evidence:

- E0-P0A-SRC1, E0-P0A-SRC2, E0-P0A-SRC3.

Classification: `correct` for the approved boundary, with no hook required.

Allowed next action: preserve the final proof and keep release/deployment behind its existing user-approval gate.

Forbidden next action: claim that hardening completion is release/deployment approval.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | core ledger is verified | preserve and verify |
| P1-B | adapter works; protected host hook absent | superseded by approved P1-D lifecycle integration |
| P1-D | lifecycle journal and skill wiring verified | preserve and verify |
| P1-E | p2p_gate ledger gate positive/negative paths verified | preserve and verify |
| P1-C | twelve-case coverage and gate PASS | preserve and re-run if code changes |
| P2-A | gates, final eight-thread proof, supervisor PASS, and drift pass | close approved hardening; no release/deploy |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Protected preserve-only surfaces are listed.
- [x] Missing/unbound/blocked parts have exact next actions.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Anvien unavailability and direct-inspection fallback are recorded.
- [x] P0 decision is complete before implementation.
- [x] R1 status refresh records completed core/eval work and the protected integration blocker.
- [x] R2 status refresh records explicit approval for the protected integration.
- [x] R3 status refresh records the final PASS evidence and closure.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase can proceed with explicit host-integration risk.
- [ ] P0 complete. Target scope is preserve-only.

Decision note:

The current goal explicitly approved the minimum protected quorum/runtime and existing release-gate changes. P1-D, P1-E, and P2-A pass; hooks remain disabled because the boundary is sufficient. No release/deployment was performed.
