# Supervisor Report: LOG-TRADE01 GitHub canonical candidate

Verdict: PASS

## Metadata

- Review lane: one independent Supervisor review after source inspection and fresh focused validation.
- Canonical remote: `https://github.com/7roger89-web/logistics-work-desk`
- Fresh base: `bddcf24e10285dbc82a52a2e3640bf0bf63a5a23` / tree `91f8d31bb52f042b93ba17328ddfeef5a0ad9c6e`
- Reviewed implementation commit: `dd470fa2be27b4cd1df0bd40e7da47b0a05740ed`
- Reviewed implementation tree: `dab3ce133aa7528edaed94d881802be5f5e016ed`
- Branch: `log-trade01-github-canonical`
- Review boundary: pure LOG-TRADE01 domain contracts, fixtures, focused tests, provenance, and arithmetic; no push, merge, deploy, production, or P2P action.

## Executive Summary

The candidate is technically ready for Owner review within the requested bounded tranche. The fresh GitHub `main` was revalidated as the base, the implementation is isolated in one Git worktree, and the changed production surface is a new standard-library-only `core/trade_compliance` boundary. Existing tariff UI/SQL and P2P surfaces are unchanged.

The implementation preserves the required uncertainty boundaries: customer input remains normalized but unverified, HS output remains candidate-only, discovery URLs do not become legal conclusions, unscoped/stale/conflicting sources fail closed, and arithmetic requires an explicitly final HS plus a current scoped official source. The arithmetic guard also rechecks the source scope at calculation time, so a manually forged verified snapshot or stale source cannot drive a result.

## Source-Level Clearance Notes

- `models.py` carries explicit field state, source authority, evidence status, effective dates, scope, confidence, and serialized contract values. `DocumentEvidence` prevents `sufficient=true` unless present, valid, and relevant.
- `identity.py` deterministically normalizes nested/customer input and marks product-specific required, not-relevant, and unknown fields. The generic factory-machine description does not force an HS code.
- `hs.py` emits only numeric hypotheses with reasoning and facts used. Missing facts produce `NEEDS_MORE_PRODUCT_DATA`; multiple headings produce `HUMAN_CLASSIFICATION_REQUIRED`.
- `evidence.py` requests catalogue, SDS/MSDS, composition, CAS, medical-device evidence, and related documents conditionally by product category. ISO 13485 is explicitly evidence-only and never import approval.
- `sources.py` and `source_registry.json` enforce HTTPS/provenance parsing. The bundled Vietnam registry is discovery-only (`NOT_RETRIEVED`) and contains no tariff rate or legal conclusion.
- `assessment.py` maps source-backed measures to the typed categories and downgrades unproven, stale, conflicting, or out-of-scope conclusions to review/source-verification states. Sensitive chemical and medical-device categories remain review-required without inventing a requirement.
- `tax.py` keeps MFN, preferential duty, FTA/potential eligibility, origin evidence, VAT, and other tax separate. `calculate_import_taxes()` refuses incomplete, non-final-HS, non-official, stale, conflicting, or scope-mismatched inputs and returns a formula/value trace.

## Evidence Checked

- Fresh remote check: `origin` normalized to the requested GitHub URL; remote `HEAD` and `refs/heads/main` both resolved to `bddcf24e10285dbc82a52a2e3640bf0bf63a5a23`.
- `git merge-base` binds the reviewed branch to the fresh base. Historical `9e93379c836b41116d727a35d9bec18295915da7` is unavailable in the canonical object database and was not reconstructed.
- Fresh focused run: `py -X utf8 -m unittest tests.test_log_trade01_trade_compliance -v` -> 16 tests passed.
- Non-writing compile check: 9 affected Python files compiled in memory. `ruff`, `flake8`, and `pylint` are not installed/configured in this checkout; no lint claim is made. A prior `compileall` attempt was blocked only by a locked bytecode-cache replacement; no source or cache cleanup was performed.
- `git diff --check` passed.
- Anvien fresh analyze: 440 files scanned, 215 code files parsed, 0 failed, graph 35,336 nodes / 40,504 relationships. All eight production module file-detail records were `parse=parsed`, `stale=false`. Reported high/critical fan-out is confined to the new shared contract and is a scope warning, not an existing application-route mutation.
- Changed-path review: 23 files, all under the new compliance boundary, focused fixtures/tests, bounded plan/evidence/report artifacts, and no legacy tariff/P2P/production files.

## Invariant Closure

- Product identity and missing-data fail-closed: PASS.
- HS candidate-only and ambiguity fail-closed: PASS.
- Conditional document semantics and ISO 13485 negative sufficiency: PASS.
- Chemical SDS/composition/CAS request behavior and no non-dangerous inference: PASS.
- Regulatory measure representation with unavailable/stale/conflict/source-scope review: PASS.
- Tariff source and effective-period validation: PASS.
- VAT/duty trace with explicit customs value and non-guessed other tax: PASS.
- Provenance, HTTPS, retrieval, authority, scope, confidence, and date contract: PASS.
- Residual same-invariant unverified surfaces in this bounded pure-domain tranche: none identified.

## Overall Evaluation

PASS for the LOG-TRADE01 GitHub-canonical candidate as a review-ready foundation. This is not a live legal/tariff authority, a production operator UI, an autonomous classifier, or a country-wide source adapter; those are explicitly outside this tranche and remain future authorized work. Owner approval is still required before any promotion, merge, push, deployment, or live use.
