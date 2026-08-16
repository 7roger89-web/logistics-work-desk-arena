# LOG-C02 B2 Financial Ledger Foundation + A Bò Golden Financial Case Actual Status

Title: LOG-C02 B2 Financial Ledger Foundation + A Bò Golden Financial Case
Date: 2026-08-14
Status: P0 Complete / P1-A Complete / P1-B Complete / P1-C Blocked / Overall PARTIAL
Companion plan: `docs/plans/2026-08-14-log-c02-b2-financial-ledger-foundation/2026-08-14-log-c02-b2-financial-ledger-foundation-plan.md`
Companion evidence: `docs/plans/2026-08-14-log-c02-b2-financial-ledger-foundation/2026-08-14-log-c02-financial-ledger-foundation-evidence.md`
Companion benchmark: `docs/plans/2026-08-14-log-c02-b2-financial-ledger-foundation/2026-08-14-log-c02-b2-financial-ledger-foundation-benchmark.md`

## Purpose

This file records the real current state after B2 implementation and review.
B1 remains bounded PASS by its prior accepted scope, while the latest opt-in
regression attempt hit an external Atlas timeout. The overall worktree remains
dirty and legacy financial sources remain separate. The status below is the
gate for the new B2 ledger only; it does not authorize Quick Entry, migration,
or real-money writes.

## Freshness / Refresh Rules

P0 is the baseline before B2 code edits. After each B2 slice, affected rows
must be refreshed with an appended log entry and exact evidence IDs. Existing
dirty changes are user-owned unless proven B2-owned and must remain outside
the B2 commit boundary.

## Scope

Target scope:

- canonical optional-shipment Mongo ledger;
- derived allocation/outstanding/partner position;
- B1-compatible request/reversal safety;
- bounded read-only A Bò / Sale Thành projection;
- fixture-only proof and regressions.

Out of scope:

- real business data, live Mongo mutation, migration/import, deployment,
  credentials, P2P, Quick Entry, AI, workflow/progress redesign, full FX,
  accounting GL, period close, debit generator, and broad reconciliation.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `core/database.py` | `E0-P0A-IMP1` | 1 direct affected file in file impact; 64 linked flows | B1 repository, indexes, transactions, audit/outbox, legacy stores | high containing-file risk; additive index-only edit |
| `core/financial_ledger.py` | `E0-P0A-DEC1` | new file; no baseline relationships | new canonical service boundary | low initially; validate callers/tests |
| `views/finance.py` | `E0-P0A-IMP2` | 0 downstream files in graph impact | existing Finance route and receipt form | high file-detail risk; minimal read-only append |
| `views/partner_finance.py` | `E0-P0A-DEC1` | new file; no baseline relationships | new read-only renderer | low initially; source-scan and runtime check |
| `core/shipment_360.py` | `E0-P0A-IMP3` | 1 direct affected file; 7 linked flows | existing read-only Shipment 360 projection | preserve-only in B2 |
| `tests/test_financial_write_safety.py` | `E0-P0A-SRC4` | existing B1 fixture consumer | direct/entrustment/proxy/lump-sum regressions | preserve-only; do not rewrite B1 tests |
| `tests/test_financial_ledger.py` | `E0-P0A-CAP1` | new file | B2 fixture and optional Mongo proof | editable B2-only test boundary |
| P2P checkout/source | `E0-P0A-SRC1` | protected external path | unrelated P2P governance/runtime | do-not-touch |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve and add only needed evidence. |
| `partial` | Some required behavior exists, but gaps remain. | Change only the missing bounded part. |
| `wrong` | Current behavior conflicts with requirement. | Replace only the exact conflicting behavior. |
| `missing` | Required behavior does not exist. | Implement the missing piece only. |
| `unbound` | Surface exists but is not wired to required source/flow. | Bind only to the canonical source. |
| `fake-or-stub` | Demo/placeholder behavior is treated as real. | Remove or mark UNKNOWN. |
| `blocked` | Required authority/evidence/dependency is unclear. | Stop and record blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| B1 request identity/transaction/correction primitives | Stable request registry, transaction guard, audit, correction/reversal, and B1 fixture proof exist | Reuse for ledger writes | correct for B1 boundary | 64 linked DB flows | `E0-P0A-SRC2`, `E0-P0A-SRC4` | preserve; reuse P1-A |
| Existing shipment/customer payment | Embedded shipment payment history and derived `core.logic` balance | Canonical transaction/allocation without breaking legacy path | partial | inspect-only legacy siblings | `E0-P0A-SRC3` | preserve; no migration |
| Existing lump-sum payment | Existing transaction/idempotency path is B1 regression surface | Remain regression-safe | correct for existing bounded route | existing tests | `E0-P0A-SRC4` | preserve; regression P1-C |
| Contract proxy pair | B1 bounded atomic helper exists in dirty current source | Remain regression-safe | correct for B1 boundary | `core/database.py` high-risk | `E0-P0A-SRC2`, `E0-P0A-SRC4` | preserve; regression P1-C |
| Entrustment wallet | Existing wallet/legs are separate and legacy-shaped | Canonical held/received-on-behalf projection | partial | `views/entrustment.py` consumer | `E0-P0A-SRC3` | inspect-only; new ledger fixture only |
| Obligation | No canonical collection/service | Durable optional-shipment obligation | missing | new service boundary | `E0-P0A-CAP1` | implement P1-A |
| Transaction/money event | Legacy payment/proxy/entrustment events are duplicated across stores | Durable source/holder/beneficial-owner money event | partial/missing canonical | new service boundary | `E0-P0A-SRC3`, `E0-P0A-CAP1` | implement P1-A |
| Allocation | No canonical allocation source; legacy FIFO/lump-sum is shipment-bound | Derived effective allocation supporting 1↔many | missing | new service boundary | `E0-P0A-SRC3` | implement P1-A |
| Adjustment/reversal for ledger | B1 correction exists for direct shipment payment only | Reuse traceable correction semantics for allocation reversal | partial | B1 correction collection | `E0-P0A-SRC2` | implement bounded P1-A |
| Evidence/provenance | Audit/note/source fields are scattered | Structured evidence refs/raw provenance on canonical rows | partial/missing | legacy stores inspect-only | `E0-P0A-SRC3` | implement bounded P1-A |
| Shipment linkage | Existing legacy financial paths require shipment in some writes | Optional empty linkage and later attach | wrong for B2 if generalized | new service boundary | `E0-P0A-SRC3`, `E0-P0A-CAP1` | implement P1-A; do not alter B1 API |
| Ownership/holder/restriction | No canonical separated buckets | Source, holder, beneficial owner, allowed use, restriction | missing | new service boundary | `E0-P0A-CAP1` | implement P1-A |
| A Bò partner position | Existing entrustment/proxy relations do not form a derived position | Explicit currency buckets and formulas | missing | `core/shipment_360.py` preserve-only | `E0-P0A-SRC3` | implement P1-A/B |
| Sale Thành dimension | No canonical ledger filter dimension | `internal_sale_owner` filtering without party semantics | missing | new service boundary | `E0-P0A-CAP1` | implement P1-A/B |
| UNKNOWN/restricted review | Legacy unknown fields are not canonical ledger buckets | Visible, searchable, excluded from confirmed position | missing | new service boundary | `E0-P0A-CAP1` | implement P1-A/B |
| Existing Finance UI | Customer receipt form exists and writes legacy path | Add bounded read-only projection only | partial | `views/finance.py` file risk high | `E0-P0A-IMP2` | minimal P1-B edit |
| Docker runtime | No Dockerfile/compose found in current repo | Required only if public UI acceptance claims Docker evidence | blocked for Docker-specific validation | repo-level | plan risk note | record limitation; do not install/build new infra |
| Real data/migration/P2P | Explicitly forbidden | unchanged | preserve-only | protected paths | `E0-P0A-SRC1`, `E0-P0A-WT1` | do-not-touch |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-14 | B2 attachment, current source, refreshed Anvien graph, worktree | B2 ledger/projection boundary | baseline classifications above | `E0-P0A-SRC1..E0-P0A-DEC1` | P1-A/B/C may proceed in order; Quick Entry remains closed |
| R1 | 2026-08-14 | P1-A implementation, 10 memory tests, 1 disposable Mongo fresh-client test, exact cleanup | canonical obligation/transaction/allocation, optional linkage, derived position, reversal | `missing/blocked -> correct for bounded new-ledger writes`; UI projection remains missing/in progress | `E1-P1A-SVC1..E1-P1A-RUN4` | proceed to P1-B; legacy sources remain partial and no Quick Entry |
| R2 | 2026-08-14 | P1-B projection, over-allocation hardening, 11 memory tests, B2 fresh-client 1/1, full suite 48/48, fresh integrity/edge reviews | canonical B2 ledger and bounded A Bo/Sale Thanh read-only projection | `correct for bounded B2; P1-C remains in progress pending supervisor and explicit runtime/dirty-boundary closure` | `E2-P1C-TEST1-R2..E2-P1C-REVIEW6-R2` | run supervisor; keep Docker/browser, B1 Atlas timeout, legacy migration, and general adjustment risks explicit |
| R3 | 2026-08-14 | fresh Supervisor review after source/diff inspection, Anvien refresh, 48-test suite, B2 1/1 Mongo proof | B2 closure claim and P1-C evidence | `REJECT for closure; overall PARTIAL` because Docker/browser proof, complete B1 Atlas regression, and isolated shared-file boundary are unresolved | `E2-P1C-REVIEW4-R3`, `reports/supervisor/rp_supervisor_260814_165706_by_gpt-5-codex_log_c02_b2_ledger.md` | do not enable production writes; resolve/re-scope blockers before closure |

### R1 Current Status Overrides

The baseline rows above remain historical context. The following rows are the
current classifications after P1-A and are authoritative for the next slice.

| Unit | Current State | Required State | Status | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|----------|--------------------|
| Canonical obligation | `financial_obligations` persists a shipment-optional obligation and derives outstanding from allocations | One durable canonical obligation source | correct for bounded new ledger | `E1-P1A-SVC1`, `E1-P1A-RUN2` | preserve; no migration |
| Canonical transaction | `financial_transactions` preserves source, holder, beneficial owner, restriction, provenance, and optional shipment | One durable canonical money-event source | correct for bounded new ledger; legacy sources remain partial | `E1-P1A-SVC2`, `E1-P1A-RUN2` | preserve; no legacy replacement |
| Canonical allocation | `financial_allocations` supports partial, one-to-many, many-to-one and derived remainder | Effective allocation history | correct for bounded new ledger | `E1-P1A-SVC3`, `E1-P1A-SVC4`, `E1-P1A-RUN1` | preserve; no stored balance |
| Allocation reversal | B1-shaped correction preserves original allocation and changes only effective status | Traceable correction/reversal | correct for bounded reversal | `E1-P1A-SVC8` | preserve; positive adjustment types remain out |
| Ownership/restriction/UNKNOWN | Guards block restricted, unknown, and incompatible-currency allocations; projection excludes them from confirmed totals | No unsafe auto-net | correct for bounded new ledger | `E1-P1A-SVC7`, `E2-P1C-REVIEW1-R2` | expose read-only buckets; no auto-net |
| Optional shipment link | Later link updates linkage only and keeps one transaction/history row | Attach without duplication | correct for bounded new ledger | `E1-P1A-SVC6`, `E2-P1C-TEST2-R2` | expose source IDs in read-only projection |
| A Bo / Sale Thanh projection | Domain projection and Finance renderer expose explicit currency buckets, formulas, and internal owner filter without mutation controls | Bounded read-only UI | correct for bounded B2; runtime closure partial | `E1-P1B-UI1..E1-P1B-UI6`, `E2-P1C-TEST7-R2` | no write UI; Docker/browser unavailable |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `core/financial_ledger.py` | `core/database.py` | repository/transaction helper dependency | P1-A | edit | `E0-P0A-DEC1` | new canonical service; no legacy migration |
| `core/database.py` | `core/financial_ledger.py` | index bootstrap/source repository | P1-A | edit | `E0-P0A-IMP1` | additive ledger indexes only |
| `core/financial_ledger.py` | `tests/test_financial_ledger.py` | service/test contract | P1-A/P1-C | edit | `E0-P0A-CAP1` | fixture-only; fresh read-back |
| `views/partner_finance.py` | `core/financial_ledger.py` | read-only projection consumer | P1-B | edit | `E0-P0A-DEC1` | no mutation helper import |
| `views/finance.py` | `views/partner_finance.py` | existing Finance route consumer | P1-B | edit | `E0-P0A-IMP2` | minimal append; preserve receipt flow |
| `core/shipment_360.py` | legacy finance/proxy/entrustment sources | existing projection sibling | P1-A/P1-B | preserve-only | `E0-P0A-IMP3` | no source replacement in B2 |
| `tests/test_financial_write_safety.py` | B1 production paths | regression consumer | P1-C | validate-only | `E0-P0A-SRC4` | do not rewrite B1 tests |
| `views/partner_finance.py` | `core/financial_ledger.py` | read-only projection consumer | P1-B | edit | `E1-P1A-SVC1..E1-P1A-SVC9` | no mutation controls |
| `.p2p/`, `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4` | P2P governance/runtime | protected external boundary | all | do-not-touch | `E0-P0A-SRC1` | no P2P change |

## Detailed Findings

### Canonical ledger and optional shipment linkage

Current state:

Existing payment, proxy, entrustment, and shipment stores are separate. Some
legacy writes require shipment context, and no canonical obligation,
transaction, or allocation collections exist. B2 must add a new optional-
shipment source without changing legacy source documents.

Required state:

```text
obligation / transaction / allocation are durable canonical records;
shipment linkage is optional and can be added later without duplicating money;
all balances are derived from effective history.
```

Evidence:

- `E0-P0A-SRC1`: user-defined B2 boundary.
- `E0-P0A-SRC3`: current code has no canonical ledger.
- `E0-P0A-IMP1`: database touch risk is high/medium and must remain narrow.

Relationship and impact:

- Related file count: one direct affected file in Anvien file impact for the
  existing database source; new service has no baseline consumers.
- Relationship summary: B1 helpers can be reused through the current Mongo
  transaction boundary; legacy sources remain siblings.
- Impact note: additive index registration and a new module limit blast radius;
  fresh tests must cover new consumers.

Classification:

`correct` for the bounded new-ledger write/read service after P1-A fixture
proof; `partial` legacy context.

Allowed next action:

Proceed to P1-B read-only projection; keep legacy source migration out.

Forbidden next action:

Do not import real legacy rows, replace Shipment 360 sources, or make shipment
mandatory for canonical money.

### A Bò / Sale Thành projection

Current state:

There is no derived A Bò partner position or internal Sale Thành dimension in
the current Finance route. Existing customer receipt UI is a mutation surface.

Required state:

```text
read-only A Bò buckets by currency, deterministic why-number rows,
Sale Thành filtering by internal dimension, no editable balance or write UI.
```

Evidence:

- `E0-P0A-SRC3`: existing Finance and Shipment 360 are separate projections.
- `E0-P0A-IMP2`: Finance file is high-detail-risk but low graph impact.
- `E0-P0A-CAP1`: projection is missing.

Relationship and impact:

- Related file count: no downstream files in file impact for current Finance
  file; new renderer requires direct tests and runtime check.
- Relationship summary: new renderer consumes only canonical projection.
- Impact note: keep existing receipt controls unchanged and add read-only
  section only.

Classification:

`missing` bounded projection.

Allowed next action:

P1-B implementation is complete for the bounded read-only projection; keep
all rendering read-only and do not infer reconciliation closure.

Forbidden next action:

Do not add Quick Entry, auto-netting, AI, manager reconciliation, or fake
accounting party for Thành.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | canonical ledger is missing but B1 transaction/request/correction boundary is reusable | implement new service with optional shipment; keep `core/database.py` index-only |
| P1-B | A Bò/Sale Thành read-only projection is missing; Finance route exists | add bounded read-only renderer after service tests; preserve receipt flow |
| P1-C | fixtures, compile, full suite, fresh reviews, and B2 Mongo proof ran; Supervisor rejected closure because Docker/browser, B1 Atlas timeout, and dirty-boundary evidence remain | do not claim production-wide safety; resolve or explicitly re-scope blockers |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship/impact evidence when applicable.
- [x] Phase Touch Map lists plan-relevant relationship files.
- [x] Phase Touch Map defines touch mode for every affected unit.
- [x] Correct parts are preserve-only where required.
- [x] Partial/missing/unsafe/unknown parts have exact next actions.
- [x] Blockers are recorded, including Docker-specific validation limitation.
- [x] Next phase assumptions and work steps were updated from this status.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Affected rows were refreshed after P1-A and P1-B; P1-C is blocked by the Supervisor findings.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase can proceed unchanged.
- [ ] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 PASS for bounded B2 implementation. The new canonical ledger may be built
with synthetic fixture data and optional isolated Mongo proof. The existing
dirty worktree, legacy source duplication, missing migration/import path, and
Docker-specific runtime requirement remain explicit constraints. Quick Entry,
AI, real business writes, and P2P remain closed.

## Final B2 Review Decision

- Implementation result: `PARTIAL` — bounded canonical ledger and read-only
  projection are implemented and fixture-proven.
- Supervisor result: `REJECT` for plan closure; see
  `reports/supervisor/rp_supervisor_260814_165706_by_gpt-5-codex_log_c02_b2_ledger.md`.
- Blocking evidence: no Docker/browser proof for the changed Finance route;
  one B1 Atlas regression/teardown timed out; shared `core/database.py` and
  `views/finance.py` remain too dirty for an isolated B2 checkpoint.
- Safety boundary: no production write enablement, migration, deployment,
  credential/permission change, real business data mutation, Quick Entry, or
  P2P work is authorized by this result.
