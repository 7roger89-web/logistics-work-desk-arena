# Contracts, shipment filters, and CBPG redesign Actual Status

Title: Contracts, shipment filters, and CBPG redesign
Date: 2026-08-06
Status: Implementation complete; DB-backed E2E pending external MongoDB availability
Companion plan: `docs/plans/2026-08-06-contracts-filter-cbpg-redesign/2026-08-06-contracts-filter-cbpg-redesign-plan.md`
Companion evidence: `docs/plans/2026-08-06-contracts-filter-cbpg-redesign/2026-08-06-contracts-filter-cbpg-redesign-evidence.md`
Companion benchmark: `docs/plans/2026-08-06-contracts-filter-cbpg-redesign/2026-08-06-contracts-filter-cbpg-redesign-benchmark.md`

## Scope

- Dashboard filter/detail behavior, shipment business-date canonicalization, Mongo connection bounds.
- Contract relation and financial workspace.
- CBPG tariff editor.
- Receivables boundary and regression/runtime validation.

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| `views/dashboard.py` filter | top-level timestamp wins; missing dates can become today | business date first; bounded missing-date behavior | implemented | n/a | E1-P1A-TEST,E1-Pn-UI |
| Dashboard selected detail | rendered from all shipments and widget state has no stable filter key | selection survives rerun and is explicit when outside filter | implemented; DB record not available in smoke env | n/a | E1-P1A-SRC,E1-Pn-UI |
| `core/database.py` Mongo client | connection timeout is bounded but socket wait is not | bounded connect/server/socket/wait behavior | implemented | n/a | E1-P2A-SRC,E1-Pn-DB |
| Contract-to-shipment link | active legacy entrustment number only | canonical one-contract-to-many-shipments relation + legacy fallback | implemented; write/reload pending DB | n/a | E1-P2C-TEST,E1-Pn-SRC |
| Contract financial model | bank and proxy are separate; wallet not in contract page | typed unified contract ledger | implemented; write/reload pending DB | n/a | E1-P2B-TEST,E1-Pn-UI |
| CBPG row STT | display resets ID but persisted output has no invariant helper | sequential STT after every dynamic edit | implemented | n/a | E1-P1B-TEST,E1-Pn-UI |
| CBPG exception criteria | one static list for all categories | category-specific option sets and invalid-value repair | implemented | n/a | E1-P1B-TEST,E1-Pn-UI |
| `views/finance.py` receivables | customer-level allocation engine exists | remain separate from contract transaction ledger | correct boundary | n/a | E0-P0A-TEST1 | preserve P3-A |
| Regression tests | no tests for reported flows | behavior tests for source and runtime | 24 passing; detail persistence smoke blocked by DB | n/a | E1-P1A-TEST,E1-P1B-TEST,E1-P2B-TEST,E1-P2C-TEST,E1-Pn-UI |

## Phase Touch Map

| Unit / File | Relationship | Plan Item | Touch Mode | Evidence | Constraint |
|-------------|--------------|-----------|------------|----------|------------|
| `core/utils.py` | source helper | P1-A | edit | E0-P0A-SRC2 | preserve existing `parse_date` callers |
| `views/dashboard.py` | UI consumer | P1-A | edit | E0-P0A-SRC1 | stable widget keys; no hidden fallback |
| `views/tariff.py` | UI/data consumer | P1-B | edit | E0-P0A-SRC4 | preserve CBPG formulas |
| `core/database.py` | persistence source | P2-A | edit | E0-P0A-SRC5 | no destructive migration |
| `views/contracts.py` | canonical render/write surface | P2-B | edit | E0-P0A-SRC3 | keep legacy fields readable |
| `views/shipment.py` | link write path | P2-C | edit | E0-P0A-SRC3 | keep shipment validation and versioning |
| `views/proxy_payment.py`,`views/entrustment.py` | legacy writers | P2-C | inspect/edit only where needed | E0-P0A-SRC3 | dual-write, no deletion |
| `views/finance.py`,`core/payment_logic.py` | receivables consumer | P3-A | preserve/test | E0-P0A-TEST1 | do not duplicate allocation |

## Detailed Findings

### Filter/date source

Current status is `wrong`: `created_at` is selected with system timestamp precedence and `parse_date` can silently default to today. The next action is a pure helper plus focused dashboard change.

### Contract boundary

Current status is `partial`: the domain exists but its relation and payment surfaces are split. The next action is a backward-compatible canonical id/ledger, not a destructive rewrite.

### CBPG

Current status is `wrong/partial`: the existing formulas are preserved, while row identity and category-specific exception selection need explicit normalization.

## Final implementation decision

- [x] P0 baseline complete.
- [x] P1/P2 implementation and regression tests complete.
- [ ] Mongo-backed write -> reload -> render verification remains blocked until `MONGO_URI` resolves.

Decision note: the implementation preserves legacy fields/collections while writing canonical `contract_id` and typed `contract_transactions`. The app fails visibly and quickly when MongoDB is unavailable; no fabricated shipment dates are included in bounded filters.
