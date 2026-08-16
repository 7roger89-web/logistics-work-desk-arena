# Contracts, shipment filters, and CBPG redesign Plan

## Metadata

- Date: `2026-08-06`
- Status: `draft`
- Plan: `docs/plans/2026-08-06-contracts-filter-cbpg-redesign/2026-08-06-contracts-filter-cbpg-redesign-plan.md`
- Evidence: `docs/plans/2026-08-06-contracts-filter-cbpg-redesign/2026-08-06-contracts-filter-cbpg-redesign-evidence.md`
- Benchmark: `docs/plans/2026-08-06-contracts-filter-cbpg-redesign/2026-08-06-contracts-filter-cbpg-redesign-benchmark.md`
- Actual status: `docs/plans/2026-08-06-contracts-filter-cbpg-redesign/2026-08-06-contracts-filter-cbpg-redesign-actual-status.md`

## Goal

Make the shipment history filter deterministic, keep a selected shipment detail open across Streamlit reruns, and make the contract the single business home for linked shipments and contract-level financial activity. Correct the CBPG workbench so row numbers and exception criteria are data-safe and category-specific.

## Problem

The dashboard filters by the Mongo insert timestamp before the shipment's business/document date. Missing or malformed dates fall back to today. A selected detail is rendered from the unfiltered map and several expensive database reads run during every rerun. Contracts currently find shipments only through a legacy active entrustment contract number, while bank payments, proxy payments, and entrustment/wallet activity live in separate surfaces. The tariff editor uses one exception list for chairs and tables and does not persist sequential STT reliably after dynamic row edits.

## Scope

- Dashboard date source, filter state, selected-detail state, and related regression tests.
- Mongo connection timeout hardening and indexes required for contract links/ledger rows.
- Backward-compatible contract-to-many-shipment relation (`contract_id` on shipment with legacy contract-number read fallback).
- A unified Contract financial workspace with sub-sections for bank transfer, proxy payment, and entrustment wallet; legacy routes remain compatible during transition.
- CBPG row normalization, sequential STT, and category-specific exception options for `Ghế` and `Bàn`.
- Evidence, benchmarks, runtime validation, and supervisor review.

## Non-Goals

- Rewriting the receivables engine or merging customer receivables into contract accounting. They are different bounded contexts and remain separate, with cross-links where useful.
- Changing customs law or asserting a legal CBPG classification. Existing rule output remains an internal screening result.
- Destructive migration or deletion of existing proxy-payment, entrustment, or shipment records.

## Requirements

1. Business date is read from `data["0.0"]["created_at"]` first, then a valid top-level date; missing dates are excluded from bounded date filters.
2. Selecting `Tháng trước` then opening a shipment keeps the selection and filter after every rerun/save; an intentionally out-of-filter selection is clearly marked and closable.
3. A contract can link many shipments. Existing `entrustment.contract_no` and proxy `linked_id` data remain readable.
4. Contract finance is one tab with three explicit sections: bank transfer, proxy payment, and entrustment wallet. Each row has a type/source and contract id.
5. `Thu tiền & Công nợ` remains a separate receivables context; the contract workspace links to it rather than duplicating allocation logic.
6. CBPG STT is regenerated from persisted row order on every edit/save/add/remove. Exception choices are constrained by category and invalid legacy values are cleared with a visible note.

## Acceptance Criteria

- Unit tests prove month-boundary date precedence, invalid-date exclusion, filter/detail state, contract link normalization, and CBPG row normalization/exception rules.
- Source checks show the contract tab can read/write links and all three finance types without dropping legacy fields.
- Real app runtime starts, dashboard filter and detail flow are exercised, and contract/CBPG screens render without exceptions. If Docker is unavailable, the limitation is recorded explicitly; no fake runtime evidence is substituted.
- `Thu tiền & Công nợ` remains a distinct route and its existing payment-allocation tests still pass.

## Checklist

- [x] P0: baseline actual status recorded before implementation.
- [ ] P1-A: canonical shipment business date and dashboard filter/detail state.
- [ ] P1-B: CBPG row normalization and category-specific exception choices.
- [ ] P2-A: contract link/ledger data contract, indexes, and backward-compatible persistence.
- [ ] P2-B: unified Hợp đồng UI with shipment links and three finance sections.
- [ ] P2-C: shipment detail and legacy payment surfaces write/read the canonical contract id.
- [ ] P3-A: verify receivables remains separate and add cross-links/copy only where needed.
- [ ] Pn-A: supervisor acceptance review.
- [ ] Pn-B: dead-work cleanup review.
- [ ] Pn-C: final validation, evidence, benchmark, and commit state.

## Implementation Slices

### P1-A — Filter and detail state

- Goal: make `Tháng trước` use the correct business date and keep detail open.
- Scope boundary: edit `core/utils.py`, `views/dashboard.py`, `core/database.py`, and focused tests; preserve existing status/search semantics.
- Pre-flight questions: Mongo reads remain the source of truth; dashboard remains permission-gated; detail is rendered from the selected shipment map; no destructive writes.
- Work steps: add a canonical helper; replace date fallback; give widgets stable keys; distinguish selected-in-filter vs selected-outside-filter; avoid unnecessary audit DB work on every render; add tests.
- Gate: run impact/source checks before edit; run unit tests and a real dashboard smoke check after edit.
- Acceptance: month boundary and selected detail behavior pass from a fresh session.
- Commit boundary: one commit after slice evidence is captured.

### P1-B — CBPG editor correctness

- Goal: normalize row ids and category-specific exception values.
- Scope boundary: edit `views/tariff.py`, add pure helpers/tests; preserve existing CBPG tax formulas.
- Work steps: define option maps, normalize dynamic editor output, clear incompatible legacy values, persist normalized rows, show the user what was corrected.
- Acceptance: adding/removing rows yields STT 1..n; chair/table rows cannot retain each other's exception values.

### P2-A — Contract relation and ledger contract

- Goal: persist one contract linked to many shipments and a typed contract transaction ledger without deleting legacy data.
- Scope boundary: edit `core/database.py` and contract-focused tests; add indexes and helpers; dual-read legacy fields.
- Work steps: add `contract_id`/`contract_ids` compatibility normalization, add `contract_transactions` collection helpers/index, derive legacy proxy/entrustment rows as read-only ledger rows, preserve audit/version behavior.
- Acceptance: write then reload proves the relationship and ledger rows survive a new request.

### P2-B — Unified contract UI

- Goal: make Hợp đồng the canonical surface for linked shipments and the three finance types.
- Scope boundary: edit `views/contracts.py` and route presentation; legacy modules remain importable and data-compatible.
- Work steps: add shipment link/unlink controls; add one financial workspace with bank/proxy/wallet sections; show balances by type and source; link to existing receivables route without duplicating allocation.
- Acceptance: one contract page shows all related shipments and typed financial activity.

### P2-C — Link write paths

- Goal: ensure creating/editing a shipment or legacy payment can populate canonical `contract_id` while preserving old fields.
- Scope boundary: edit `views/shipment.py`, `views/proxy_payment.py`, `views/entrustment.py` only where the existing write path is touched; preserve permissions.
- Acceptance: a link made from either side is visible from the contract page after reload.

### P3-A — Receivables boundary

- Goal: keep Thu tiền & Công nợ as customer-level allocation and avoid a duplicated contract debt engine.
- Scope boundary: inspect/test `views/finance.py` and `core/payment_logic.py`; add only explanatory links or contract filters.
- Acceptance: existing receivables behavior/tests remain unchanged; contract payments do not silently alter customer allocation.

## Risk Notes

- Existing records may have inconsistent date fields or contract number spellings; normalization must be explicit and reversible.
- Streamlit executes every tab body on rerun, so all new writes must use stable widget keys and avoid relying on tab visibility.
- Mongo indexes may already exist with incompatible options; index creation must be non-destructive and log failures.
- Contract finance is a bounded context; do not infer customer receivables from a contract transaction without an explicit allocation.
