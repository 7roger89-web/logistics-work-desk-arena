# Coder report: LOG-TRADE01 GitHub canonical foundation

## Scope

Rebuilt the minimum LOG-TRADE01 trade-compliance foundation from fresh GitHub `main` in the isolated task worktree. The scope is a pure-Python domain boundary for foreign-origin/China to Vietnam import assistance: identity normalization, conditional evidence requests, HS candidates, source provenance, regulatory measures, tariff snapshots, and traceable duty/VAT arithmetic.

## Authority and git reference

- Canonical remote: `https://github.com/7roger89-web/logistics-work-desk`
- Fresh base SHA: `bddcf24e10285dbc82a52a2e3640bf0bf63a5a23`
- Fresh base tree: `91f8d31bb52f042b93ba17328ddfeef5a0ad9c6e`
- Branch: `log-trade01-github-canonical`
- Implementation candidate reviewed before report-only closure amendment: `dd470fa2be27b4cd1df0bd40e7da47b0a05740ed` / tree `dab3ce133aa7528edaed94d881802be5f5e016ed`.
- Historical `9e93379c836b41116d727a35d9bec18295915da7` was not found in the canonical object database and was not reconstructed.

## Invariant Family Map

### Product identity, evidence, and HS

- Authority: LOG-TRADE01 user contract.
- Production surfaces: `core/trade_compliance/identity.py`, `evidence.py`, `hs.py`, `models.py`.
- Siblings checked: existing `views/tariff.py` and `tests/test_tariff.py`; they are legacy tariff UI/SQL and were not modified. Canonical HEAD has no LOG-SKILL01 package or compatible trade contract.
- Forbidden fallback: customer description is never verified identity; missing facts never produce a forced HS code; candidates never become final classification.
- Verify matrix: fixtures A, B, D, E; conditional document requests; chemical/ISO negative cases; ambiguous and insufficient HS cases.

### Regulatory measures and provenance

- Authority: LOG-TRADE01 authority/source-priority contract.
- Production surfaces: `models.py`, `sources.py`, `source_registry.json`, `assessment.py`.
- Siblings checked: legacy tariff source is not reused as legal authority; no other compliance registry exists.
- Forbidden fallback: discovery, third-party, stale, conflicting, or unscoped evidence cannot silently become current legal truth.
- Verify matrix: official discovery registry parse; HTTPS/provenance validation; measure serialization; unavailable/stale/conflicting/scoped-out source cases.

### Tariff and tax trace

- Authority: LOG-TRADE01 tariff/calculation contract.
- Production surfaces: `tax.py`, `models.py`; legacy `views/tariff.py` remains untouched.
- Forbidden fallback: no rate without jurisdiction + HS + origin + date + scoped official source; MFN/preferential/VAT remain separate; omitted tax inputs are not assumed zero.
- Verify matrix: known HS/no source, candidate HS with source, verified source, preference eligibility, incomplete/invalid arithmetic, and trace output.

### Repository boundary

- One task-scoped Git worktree shares the canonical object store; no second full clone was created.
- No UI wiring, database, crawler, production configuration/data, P2P core, push, merge, deploy, or secret access.

## Output files created

- `core/trade_compliance/__init__.py`
- `core/trade_compliance/models.py`
- `core/trade_compliance/sources.py`
- `core/trade_compliance/source_registry.json`
- `core/trade_compliance/identity.py`
- `core/trade_compliance/evidence.py`
- `core/trade_compliance/hs.py`
- `core/trade_compliance/assessment.py`
- `core/trade_compliance/tax.py`
- `core/trade_compliance/README.md`
- `tests/test_log_trade01_trade_compliance.py`
- `tests/fixtures/log_trade01/fixture_{a,b,c,d,e,f}_*.json`
- bounded plan/evidence/benchmark/status docs under `docs/plans/2026-08-29-log-trade01-github-canonical/`
- `docs/notes_decisions_log/notes_decisions_log_20260829.md`

## Verification

### E2E Verification

  [PASS] Compiled: in-memory `compile()` over 9 affected Python files -> 9/9 compiled; no source writes.
  [PASS] Runtime: direct module boundary -> imports and pure-domain calls execute through focused unittest.
  [PASS] Happy path: fixture A -> normalized machine -> candidate HS 8422 -> conditional evidence -> verified-source fixture -> tax trace.
  [PASS] Edge case: fixtures B/D/E/C/F plus conflicting/stale/unscoped source and invalid tax inputs -> explicit customer-input/review/source-verification/incomplete outcomes.

### Focused tests

- [PASS] `tests/test_log_trade01_trade_compliance.py:77` `test_official_source_registry_preserves_discovery_provenance` — 3 official discovery entries, no live legal data.
- [PASS] `tests/test_log_trade01_trade_compliance.py:88` `test_source_parse_requires_provenance_for_verified_result` — retrieval/HTTPS validation.
- [PASS] `tests/test_log_trade01_trade_compliance.py:108` `test_fixture_a_identity_and_candidate_hs` — identity and candidate-only HS.
- [PASS] `tests/test_log_trade01_trade_compliance.py:120` `test_fixture_d_insufficient_description_fails_closed` — `NEEDS_CUSTOMER_INPUT`, no forced HS.
- [PASS] `tests/test_log_trade01_trade_compliance.py:133` `test_fixture_e_multiple_candidates_are_ambiguous` — multiple candidates and `NEEDS_HS_CONFIRMATION`.
- [PASS] `tests/test_log_trade01_trade_compliance.py:143` and `:151` — conditional and invalid-document behavior.
- [PASS] `tests/test_log_trade01_trade_compliance.py:169` — chemical SDS/composition/CAS requests and no non-dangerous conclusion.
- [PASS] `tests/test_log_trade01_trade_compliance.py:184` — ISO 13485 sufficiency-negative and no automatic import approval.
- [PASS] `tests/test_log_trade01_trade_compliance.py:212` — regulatory measure categories and source-backed measure representation.
- [PASS] `tests/test_log_trade01_trade_compliance.py:258`, `:270`, `:278` — conflicting/stale/unscoped/unavailable source fail-closed behavior.
- [PASS] `tests/test_log_trade01_trade_compliance.py:285`, `:295`, `:341` — tariff source validation, MFN/preferential separation, explicit tax trace, incomplete input, and no forged-source calculation.
- Latest focused command: `py -X utf8 -m unittest tests.test_log_trade01_trade_compliance -v` -> 16 tests, 0.038s, OK.
- `py -X utf8 -m pytest tests/test_log_trade01_trade_compliance.py -q` was not run successfully because `pytest` is not installed in this runtime; the equivalent focused unittest suite passed.
- `git diff --check` -> PASS.
- `py -m compileall -q ...` was attempted but bytecode replacement hit `WinError 5` on a locked cache file; the non-writing compile check above passed and no cache files were changed/deleted.

## Anvien evidence and blast radius

- `anvien analyze <task-worktree> --force` -> 440 files scanned, 215 code files parsed, 0 failed, graph 35,336 nodes / 40,504 relationships.
- Every affected production Python file was inspected with `file-detail`: `parse=parsed`, `stale=False`.
- Downstream impact was isolated to the new compliance boundary and its graph relationships: `__init__.py` LOW/0; `sources.py` MEDIUM/10; `identity.py` MEDIUM/13; `evidence.py` HIGH/23; `hs.py` MEDIUM/12; `assessment.py` CRITICAL/32; `tax.py` CRITICAL/37; `models.py` CRITICAL/214 same-contract relationships. These are blast-radius warnings from a new shared contract, not evidence of an existing application route change.
- Anvien generated local blocks in `AGENTS.md`/`.gitignore` and an untracked `CLAUDE.md`; those tool artifacts were removed from the candidate scope. Existing owner checkout `D:\Logistics_App_GitHub` remained untouched.

## Legacy fallback and sibling status

- Legacy tariff UI/SQL: preserved, not used as Vietnam legal authority, not modified.
- LOG-SKILL01: absent from fresh GitHub canonical HEAD; no duplicate reuse was possible.
- P2P core: no files in scope; unaffected.
- Residual unverified same-invariant surfaces: none for this pure-domain tranche.

## Risks and bounded gaps

- The official registry is discovery-only and contains no live retrieval or tariff rates by design. A future country-specific adapter must supply current, scoped source records before any regulatory/tax conclusion can be verified.
- No Streamlit route/UI was added because this tranche explicitly prioritizes the domain foundation and focused validation; operator UX wiring remains a later bounded slice.

## Handoff

Status: SUPERVISOR PASS; ready for Owner gate. The final candidate may contain a report-only evidence amendment; production code was independently reviewed at the implementation commit above.
