# R3 — Production Compatibility Rehearsal (LOG-LG02)

Date: 2026-08-18 (UTC)

## 1. Rehearsal environment design

Per contract Section 18 (preferred order), a **schema/index reconstruction based on the read-only production inventory** was chosen as the safest feasible method: production data is not copied (values are synthetic), credentials never enter the rehearsal environment, and no production mutation occurs.

| Property | Rehearsal environment |
|---|---|
| location | Local mongod 8.0 on sandbox (`mongodb://localhost:27017`), fully isolated |
| database | `logistics_workdesk_LG01_E2E` (approved TEST identity; cannot be production) |
| shape source | R1 production inventory of `logistics_db` (20 collections, 52 indexes) |
| data | 819 synthetic documents; **counts match production exactly** (customers 362, shipments 78, audit_logs 54, legacy staging 289, legacy review actions 27, contracts 6, proxy_payments 2, quick_notes 1, all finance canonical collections 0) |
| secrets | none — URI set via env var to localhost |

Tooling persisted in the repo: `docs/goals/LOG-LG02/tools/seed_rehearsal_db.py` (deterministic rebuild, random seed 20260818, verifies every collection count against production) and `docs/goals/LOG-LG02/tools/run_rehearsal_load.py` (compatibility loader).

## 2. Rehearsal questions answered (Section 18)

| Question | Result |
|---|---|
| Can candidate load existing customers? | PASS — read all 362 |
| Can candidate load existing shipments? | PASS — read all 78 with required keys |
| Can current finance model read existing canonical finance collections? | PASS — all 4 collections readable, all empty as in production |
| Do quotes/agreements coexist with legacy data? | PASS — legacy staging/review + contracts all loadable alongside |
| Are indexes compatible? | PASS — unique index lookup (customers.code) resolves; no key-pattern conflict |
| Can user collections/bootstrap work? | No `users` collection exists in production; bootstrap flow creates it on first-admin setup (documented, R9) |
| Does environment identity remain fail-closed? | PASS — rehearsal DB accepted; `logistics_db` rejected with PRODUCTION guard error |
| Required migrations discovered? | **MIGRATION_REQUIRED = NO** — all collections load with current candidate schema |

## 3. Baseline test results on candidate branch (for R6 preflight)

With `MONGO_DB_NAME=logistics_workdesk_LG01_E2E` (rehearsal TEST identity), the full candidate test suite:

| Suite | Result |
|---|---|
| Full pytest (36 files, skipping 3 UI-playwright files that need browser tooling) | **200 passed, 28 skipped (playwright UI), 6 subtests passed, 0 failed** |
| `test_lg01_env_security.py` (fail-closed guards, actor identity, RBAC denials) | 7 passed (requires configured secrets; placeholder stub used, never committed) |
| `test_financial_write_safety`, `test_dashboard_financial_write_oracle`, finance oracle tests | passed |
| `test_lg01_auth_rbac`, quotations, contracts, finance logic, ledger, payment | passed |

The 28 skipped tests are the same Playwright UI E2E tests skipped in LOG-LG01 (browser-automation dependent, not regression-relevant for this rehearsal); all logic, safety-oracle, guard, and RBAC tests pass on the candidate branch against production-shaped data.

## 4. Verdict

**REHEARSAL = PASS.** Candidate loads production-shaped data correctly, finance canonical collections coexist empty as in production, indexes are compatible, the fail-closed environment guard holds both directions, and no migration is required.
