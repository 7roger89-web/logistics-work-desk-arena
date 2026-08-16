# P2P Execution Ledger Evidence Ledger

## Metadata

- Date: `2026-08-10`
- Plan: `docs/plans/2026-08-10-p2p-execution-ledger/2026-08-10-p2p-execution-ledger-plan.md`
- Evidence: `docs/plans/2026-08-10-p2p-execution-ledger/2026-08-10-p2p-execution-ledger-evidence.md`
- Benchmark: `docs/plans/2026-08-10-p2p-execution-ledger/2026-08-10-p2p-execution-ledger-benchmark.md`
- Actual status: `docs/plans/2026-08-10-p2p-execution-ledger/2026-08-10-p2p-execution-ledger-actual-status.md`

## Evidence Rules

Evidence is current, source-backed, and specific to this plan. Existing reports are context only; fresh commands and fresh runtime records are required for acceptance. No raw transcripts, secrets, or customer data are stored.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-SRC1`: direct inspection found no execution-ledger package; only `.p2p/evals/fixtures/quorum-runtime.json` existed.
- `E0-P0A-SRC2`: `.codex/agents` contains all eight exact custom profiles with read-only sandbox settings.
- `E0-P0A-SRC3`: drift policy protects `.agents/skills`, `.codex/agents`, `.p2p/system/governance`, and `.p2p/system/scripts`; new ledger boundary is outside those paths.
- `E0-P0A-SRC4`: Anvien repository listing did not include Logistics_App_Copy, so direct `rg`/file inspection is the fallback.
- `E0-P0A-BASE1`: pre-change protected hashes were recorded in the task capsule and will be rechecked after implementation.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`, `P1-C`

- `E1-P1A-SRC1`: `.p2p/execution-ledger/schema.json` and `ledger.py` define the versioned record, derived facts, canonical SHA-256, and exclusive writer.
- `E1-P1A-TEST1`: valid full and small quorum records validate with `valid=true` and `verdict=PASS`.
- `E1-P1A-TEST2`: the immutable-no-overwrite case rejects a second write for the same run id.
- `E1-P1A-TEST3`: tamper-detection recomputation reports `record_sha256 mismatch`.
- `E1-P1A-TEST4`: missing, duplicate, generic, renamed, simulated, evidence, and supervisor-negative cases never report PASS.
- `E1-P1B-SRC1`: `.p2p/execution-ledger/adapter.py` is the coordinator completion boundary and delegates to the immutable writer without spawning or inferring threads.
- `E1-P1B-RUNTIME1`: fresh host run spawned all eight resolved custom profiles as distinct threads and returned exact `PROBE_OK` identities.
- `E1-P1B-RUNTIME2`: `.p2p/execution-ledger/runs/ledger-runtime-20260810-1442-pending.json` persisted the host evidence with 8 distinct threads and a truthful `HOLD` while supervisor verdict was `UNKNOWN`.
- `E1-P1B-BLOCK1`: source/runtime inspection found no host post-quorum hook; automatic integration into every ordinary `$p2p-quorum` invocation would require a protected skill/runtime change.
- `E1-P1C-EVAL1..E1-P1C-EVAL12`: `.p2p/evals/reports/execution-ledger-eval-gate.json` reports 12 cases, 2 baseline and 2 P2P trials each, 1.0 P2P pass rate, zero regressions, and zero failures.

- `E1-P1D-SRC1`: `.p2p/execution-ledger/quorum_runtime.py` defines the append-only start/agent/finalize/verify lifecycle, event hash chain, run-id binding, and final-record binding.
- `E1-P1D-SRC2`: `.agents/skills/p2p-quorum/SKILL.md` requires lifecycle calls for every governed invocation and leaves hooks disabled.
- `E1-P1D-RUNTIME1`: targeted lifecycle smoke finalized and verified a sub-quorum PASS; a tampered finalized event was rejected.
- `E1-P1D-RUNTIME2`: fresh final run `p2p-final-cert-20260810-1515` recorded exactly eight distinct custom threads and matching identities, then finalized with `quorum_verdict=PASS`, `final_verdict=PASS`, and record SHA-256 `c47116e27954ef1520c5b286d256d086d4c61d9571b19eea64edd7730115389c`.
- `E1-P1E-SRC1`: `.p2p/system/scripts/p2p_gate.py` requires a boundary-checked, hash-validated finalized PASS ledger record and rechecks the same hash during finalization.
- `E1-P1E-TEST1`: `.p2p/gates/final-ledger-20260810-1515/technical-gate-report.json` reports technical gates PASS with the final ledger record bound.
- `E1-P1E-TEST2`: `.p2p/gates/ledger-missing-final/technical-gate-report.json` blocks without a supplied ledger while drift remains PASS.
- `E1-P1E-TEST3`: p2p_gate positive/negative outputs use isolated gate directories and do not execute approval or release actions.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`

- `E2-P2A-LEDGER1`: fresh ledger module compile and independent `validate_record` checks pass; the real host record is persisted and hash-addressed.
- `E2-P2A-EVAL1`: existing 18-case project eval gate PASS; new execution-ledger 12-case gate PASS.
- `E2-P2A-DOCTOR1`: installed doctor PASS (22 skills, eight profiles, agent limit 8, governance drift, release readiness).
- `E2-P2A-DRIFT1`: installed drift PASS with four preserved-source warnings only.
- `E2-P2A-BASELINE1`: FACT_LEDGER `18033bc4037191865a2ef47e951f5904b41926759a838a39af45db0597bc4510`, Live Specs `452d3cb9a8d3531546b1dede4f32c4415f78976e26eb5630aed22f7825ed6645`, and Live Specs lock `89b159d43178da747dd7fa8c56d98beea09132a3832db458cda732d311fed12d` remain unchanged; the protected runtime-manifest lock was intentionally rebuilt for the approved boundary and is now `47f7f07002371a293e1e45a856d1a4a9715f0cff9af83c8f72c2ae413383e47d`; one governance tree exists.
- `E2-P2A-SUPERVISOR1`: `.p2p/evals/reports/rp_supervisor_260810_1515_by_gpt-5-codex_execution-ledger-runtime.md` is a fresh PASS review covering source, lifecycle, gates, drift, doctor, evals, RAG, and the final eight-thread proof.
- `E2-P2A-FINAL1`: installed doctor, project eval, ledger eval, RAG, and drift checks all PASS after the approved changes.

## Closure Evidence

Implementation and independent review complete for the approved scope. Classification: `correct` for the explicit skill-boundary lifecycle and existing release-gate integration; hooks remain disabled. No release/deployment action was performed.

The final technical-gate report is PASS and remains pending only the existing separate user approval required for any actual release/deployment.

### Closure Checklist

- [x] Same-run lifecycle start → agent evidence → supervisor verdict → final materialization → verify.
- [x] Exactly one fresh full eight-agent custom runtime certification; all identities matched.
- [x] Missing-ledger technical gate blocks; valid final ledger technical gate passes.
- [x] Project eval, ledger eval, RAG, doctor, and drift gates pass.
- [x] Supervisor review PASS; no application code or release/deployment action.
