# LOG-TRADE01 — GitHub canonical implementation plan

## Authority and re-anchor

- Canonical source: `https://github.com/7roger89-web/logistics-work-desk`
- Default branch: `main`
- Fresh base: `bddcf24e10285dbc82a52a2e3640bf0bf63a5a23`
- Fresh base tree: `91f8d31bb52f042b93ba17328ddfeef5a0ad9c6e`
- Task workspace: `D:\Logistics_App_GitHub\.tmp\log-trade01-github-canonical`
- Historical local base `9e93379c836b41116d727a35d9bec18295915da7` is not available in this checkout and is not treated as authority.

The user request is the active authority. `AGENTS.md` supplies repository safety rules. No approved `docs/SPEC` family exists in this canonical HEAD, so this tranche uses the user-supplied contracts directly and does not invent a new SPEC framework.

## Invariant Family Map

| Family | Authority / SSOT | Same-family surfaces checked | Forbidden fallback | Verify matrix |
|---|---|---|---|---|
| Product identity, evidence, HS candidates | LOG-TRADE01 product/evidence/HS contracts in the user request | Existing `views/tariff.py` and `tests/test_tariff.py` are legacy tariff UI and remain untouched; no LOG-SKILL01 module exists in canonical HEAD | Customer text cannot become verified identity; missing facts cannot become a guessed HS code; HS candidate cannot become final classification | A–F fixtures, missing facts, conditional documents, ambiguous candidates, compile |
| Regulatory measures and provenance | LOG-TRADE01 authority model and Vietnam official-source priority | Existing tariff surfaces are not legal-source authority; new source registry and typed source records are the only new compliance boundary | Third-party/discovery data cannot silently become legal truth; stale/conflicting sources cannot pass | registry parse, measure enum/serialization, unavailable/stale/conflicting source cases |
| Tariff snapshot and tax trace | LOG-TRADE01 tariff/calculation contracts | Existing tariff UI remains preservation-only; no database or production tariff data is modified | No rate without jurisdiction + HS + origin + date + current authoritative source; no preferential eligibility inference; no hidden tax arithmetic | missing source, candidate HS, verified source, preference separation, incomplete input, trace |
| Repository / release boundary | User request and `AGENTS.md` | `P2P core`, production configuration/data, current owner checkout, and other worktrees | No restore of deleted checkout, no push/deploy/production access, no broad regression | path-limited diff, `git diff --check`, clean candidate, supervisor review |

## Bounded execution slices

1. Add `core/trade_compliance` typed contracts, provenance/source registry, identity normalization, evidence requests, and HS candidate generation.
2. Add regulatory assessment and tariff/tax snapshot/calculation with fail-closed statuses and explicit traces.
3. Add focused fixtures/tests and plan/evidence/report artifacts. Run only affected compile and the focused test module.

The slices are implementation checkpoints only; the user explicitly requires one clean candidate commit, so no intermediate implementation commits will be created.

## Non-goals

- No crawler, tariff database, vector/graph database, OCR/document AI, translation, UI, route optimization, CRM, autonomous declaration, deployment, or production data access.
- No Vietnamese regulatory conclusion is invented from product category alone.
- No final HS classification is emitted by this module.
- No P2P core or legacy tariff UI changes.

## Acceptance criteria

- Product identity exposes field state as `PROVIDED`, `REQUIRED_FOR_THIS_PRODUCT`, `NOT_RELEVANT`, or `UNKNOWN` and remains unverified customer input.
- HS output is candidate-only; insufficient and ambiguous inputs fail closed.
- Document requests are category-conditional; chemical data requests SDS/composition/CAS and never imply non-dangerous status; ISO 13485 is evidence only.
- Regulatory measures are representable and unresolved authority produces review/source-verification status.
- Source registry preserves official URL, jurisdiction, authority, retrieval/effective metadata, scope, conclusion, confidence, and evidence status.
- Tariff rates require destination jurisdiction, HS, origin, assessment date, and a current authoritative source; MFN/preferential/VAT stay separate.
- Tax arithmetic is gated by explicit verified inputs and returns a formula/value trace.
- Focused validation passes; broad regression is not run.
