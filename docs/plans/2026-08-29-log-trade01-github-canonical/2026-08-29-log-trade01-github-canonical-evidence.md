# LOG-TRADE01 evidence ledger

## Fresh authority

- `git fetch --no-tags origin main`: PASS — remote `main` resolved to `bddcf24e10285dbc82a52a2e3640bf0bf63a5a23`.
- Fresh tree: `91f8d31bb52f042b93ba17328ddfeef5a0ad9c6e`.
- Old local base: `9e93379c836b41116d727a35d9bec18295915da7` object unavailable in canonical checkout; no old commit or uncommitted delta was recovered.
- Existing canonical checkout was mid-revert and was not mutated; implementation uses one isolated Git worktree sharing the existing object store.

## Evidence to record after implementation

| Evidence ID | Claim | Command / artifact | Status |
|---|---|---|---|
| E1 | Product identity normalization and field-state semantics | `tests/test_log_trade01_trade_compliance.py` | PASS — 16/16 focused tests |
| E2 | HS candidate-only and insufficient/ambiguous fail-closed behavior | focused unittest module | PASS — candidate/insufficient/ambiguous cases |
| E3 | Conditional evidence requests, chemical SDS/MSDS, ISO 13485 negative sufficiency | focused unittest module | PASS — conditional/chemical/ISO cases |
| E4 | Regulatory measure representation and unavailable/stale/conflict handling | focused unittest module | PASS — measures plus unavailable/stale/conflict cases |
| E5 | Tariff source validation and no invented rate | focused unittest module | PASS — scope/source/HS fail-closed cases |
| E6 | VAT/duty calculation trace and incomplete-input behavior | focused unittest module | PASS — trace and invalid-input cases |
| E7 | Official-source registry and provenance parsing | `core/trade_compliance/source_registry.json` + unittest | PASS — 3 official discovery entries and parser checks |
| E8 | Compile and diff hygiene | in-memory compile + `git diff --check` | PASS — 9/9 Python files compile in memory; compileall cache write separately hit WinError 5 |
| E9 | Independent supervisor review | `reports/supervisor/rp_supervisor_260829_193240_by_gpt-5-codex_log-trade01_github_canonical.md` | PASS — source/diff review, fresh Anvien, and focused rerun |
