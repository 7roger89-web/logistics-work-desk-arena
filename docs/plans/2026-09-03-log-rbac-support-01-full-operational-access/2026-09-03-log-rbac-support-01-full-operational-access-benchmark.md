# LOG-RBAC-SUPPORT-01 — Full operational access for Support Benchmark Ledger

## Metadata

- Date: `2026-09-03`
- Plan: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/2026-09-03-log-rbac-support-01-full-operational-access-plan.md`
- Evidence: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/2026-09-03-log-rbac-support-01-full-operational-access-evidence.md`
- Benchmark: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/2026-09-03-log-rbac-support-01-full-operational-access-benchmark.md`
- Actual status: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/2026-09-03-log-rbac-support-01-full-operational-access-actual-status.md`

## Benchmark Rules

This ledger records measured repository/graph inventory and test counts only. Pass/fail narratives belong in the evidence ledger. No Production or application database measurement is permitted.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien scanned files | files | 204 | 478 | 478 | current worktree | +274 in final full refresh (includes plan/evidence/test/tool surfaces) | E0-P0A-ANV1, E1-P1B-IMPACT1 |
| P0 | Anvien parsed code files | files | 178 | 228 | 228 | current worktree | +50 in final full refresh | E0-P0A-ANV1, E1-P1B-IMPACT1 |
| P0 | Anvien graph nodes | nodes | 32049 | 37656 | 37656 | no unexplained loss | +5607 in final full refresh; no graph failure | E0-P0A-ANV1, E1-P1B-IMPACT1 |
| P0 | Anvien graph relationships | relationships | 37412 | 43333 | 43333 | no unexplained loss | +5921 in final full refresh | E0-P0A-ANV1, E1-P1B-IMPACT1 |
| P0 | Focused baseline tests | tests | 30 passed / 2 failed | 37 passed | 37 passed | affected failures resolved | stale Support failures closed | E0-P0A-TEST1, E1-P1B-TEST1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Support operational permission tokens | tokens | 21 | 21 | 21 | all mounted employee operations | 0; policy reused, no wildcard | E0-P0A-SRC2, E1-P1B-SEC1 |
| P1 | Contract persistence readback records | records | 0 in isolated fixture | 2 Contract/transaction records | 2 | create + update visible after reload | +2 | E1-P1A-DB1 |
| P1 | Actor fields on Support mutation audit | fields | actor string only | 4 identity/time fields | 4 | user_id + role + username + timestamp | +4 | E1-P1C-DB1 |
| P1 | Focused Support RBAC/Contract tests | tests | 0 task-specific | 37 passed | 37 passed | no affected failure | +37 | E1-P1B-TEST1 |
| P1 | Finance safety fixture tests | tests | existing suite | 12 passed / 6 skipped | 12 passed / 6 skipped | rollback/idempotency/reversal retained | pass | E1-P1C-TEST1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Candidate commit SHA | SHA | c1c9468 baseline | implementation pending commit | pending | isolated candidate exists | pending | E-CLOSE-1 |

## Non-Benchmarkable Notes

- Browser/Preview availability is a gate/status, not a performance benchmark.
- Production mutation counts are closure safety facts, not product benchmarks.
- Full test pass/fail and compile output are recorded in the evidence ledger.
