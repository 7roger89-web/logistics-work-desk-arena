# LOGISTICS DeepL Translation V1 Benchmark Ledger

## Metadata

- Date: `2026-09-03`
- Plan: `docs/plans/2026-09-03-logistics-deepl-translation-v1/2026-09-03-logistics-deepl-translation-v1-plan.md`
- Evidence: `docs/plans/2026-09-03-logistics-deepl-translation-v1/2026-09-03-logistics-deepl-translation-v1-evidence.md`
- Benchmark: `docs/plans/2026-09-03-logistics-deepl-translation-v1/2026-09-03-logistics-deepl-translation-v1-benchmark.md`
- Actual status: `docs/plans/2026-09-03-logistics-deepl-translation-v1/2026-09-03-logistics-deepl-translation-v1-actual-status.md`

## Benchmark Rules

- Record measured counts only; pass/fail narrative belongs in evidence.
- Never record API keys, key fragments, customer text, or secret-bearing URLs.
- Baselines are from the fresh branch before implementation.

## B0 - P0 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P0 | Anvien scanned files | files | 473 | 473 | 473 | known baseline | 0 | E0-P0A-ANV1 |
| P0 | Anvien parsed code files | files | 227 | 227 | 227 | 0 parse failures | 0 | E0-P0A-ANV1 |
| P0 | Anvien parse failures | files | 0 | 0 | 0 | 0 | 0 | E0-P0A-ANV1 |
| P0 | Target DeepL source/view/test files | files | 0 | 0 | 0 | implementation starts from missing | 0 | E0-P0A-MISSING1 |
| P0 | Related files: core/config.py | files | 3 | 3 | 3 | inspect before edit | 0 | E0-P0A-REL1 |
| P0 | Related files: core/auth.py | files | 4 | 4 | 4 | inspect before edit | 0 | E0-P0A-REL1 |
| P0 | Related files: views/web_app.py | files | 1 | 1 | 1 | inspect before edit | 0 | E0-P0A-REL1 |

## B1 - P1 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P1 | Focused service tests | tests | 0 | 14 | 14 | all requested cases pass | +14 | E1-P1A-TEST1 |
| P1 | Automatic usage calls during import/translation | calls | 0 | 0 | 0 | 0 | E1-P1C-BOUNDARY1 |
| P1 | Maximum same-key retries observed | retries | 0 | 2 | 2 | <=2 per status budget | +2 | E1-P1B-ROTATE1 |

## B2 - P2 Benchmarks

| Phase | Metric | Unit | Baseline | Latest | Final | Target | Delta | Evidence |
|-------|--------|------|----------|--------|-------|--------|-------|----------|
| P2 | Translation route entries added | routes | 0 | pending | pending | 1 | pending | pending |
| P2 | Focused RBAC/UI tests | tests | 0 | pending | pending | all pass | pending | pending |
| P2 | Production DB mutations | mutations | 0 | pending | pending | 0 | 0 | pending |
| P2 | Real API smoke calls | calls | 0 | pending | pending | small single smoke or NOT_RUN | pending | pending |

## Non-Benchmarkable Notes

- Visual readability, Owner acceptance, and secret non-disclosure are evidenced
  through test/browser observations and are not reduced to invented scores.
- Docker is not benchmarkable for this repository because no Dockerfile or
  container runtime is part of the local Streamlit project.
