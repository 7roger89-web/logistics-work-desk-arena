# LOG-RBAC-SUPPORT-01 — Full operational access for Support Actual Status

Title: LOG-RBAC-SUPPORT-01 — Full operational access for Support
Date: 2026-09-03
Status: P1-A complete; P1-B/P1-C implementation pending
Companion plan: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/2026-09-03-log-rbac-support-01-full-operational-access-plan.md`
Companion evidence: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/2026-09-03-log-rbac-support-01-full-operational-access-evidence.md`
Companion benchmark: `docs/plans/2026-09-03-log-rbac-support-01-full-operational-access/2026-09-03-log-rbac-support-01-full-operational-access-benchmark.md`

## Purpose

This file records the current repo reality before implementation. It is based on a fresh fetch and isolated worktree at `origin/main` `c1c9468a814a2c0e56cefcf2851a2cadf46df436`; it does not treat old SHA claims or the dirty Owner checkout as authority.

## Freshness / Refresh Rules

P0 records the baseline before implementation. After each implementation slice, only affected rows and the refresh log are updated with fresh evidence. Detailed command output remains in the companion evidence ledger.

## Scope

Target scope:

- Support employee-facing operational authorization and Contract create/edit/save/reopen persistence.
- Existing route/control/service/repository writer family, actor/audit traceability, and security boundaries.

Out of scope:

- Production, `logistics_workdesk_logc14`, `logistics_db`, deployment, promotion, merge, auth rewrite, schema migration, unrelated LG09/Getfly/GNT/historical/trade work.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `core/auth.py` | `E0-P0A-ANV1` | 13 local / 3 inbound | Single permission matrix, permission helpers, actor identity | medium/high; shared auth boundary |
| `core/database.py` | `E0-P0A-ANV1` | 144 local / 44 inbound | Contract, shipment, customer, finance, task, proxy, entrustment writers and audit | critical; central persistence fan-in |
| `views/contracts.py` | `E0-P0A-ANV1` | 18 local | Contract route/forms, shipment links, contract finance, terms | high; direct user-visible path |
| `views/quotations.py` | `E0-P0A-ANV1` | 12 local | Quote create/transition/shipment draft controls | medium; Support operational sibling |
| `views/customers.py` | `E0-P0A-ANV1` | 0 local | Customer import/create/edit/delete controls | medium; writer boundary is imported |
| `views/shipment.py` | `E0-P0A-ANV1` | 0 local | Pickup/export, import/delivery, GNT, finance and shipment save | high; writer boundary is imported |
| `core/payment_logic.py` | `E0-P0A-ANV1` | 3 local | Lump-sum receipt and allocation | high; financial writer sibling |
| `core/financial_ledger.py` | P0 Anvien impact | 78 local / 34 outbound | Canonical ledger writer family, not mounted in the primary current route | inspect-only unless fresh impact proves required |
| `views/dashboard.py` | P0 Anvien impact | 18 local / 3 outbound | Tasks, GetFly import/export, shipment launch/detail, admin-only delete | medium; mounted operational sibling |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve; add proof if needed. |
| `partial` | Some required behavior exists, but gaps remain. | Change only missing parts. |
| `wrong` | Current source/contract conflicts with requirement. | Replace required behavior. |
| `missing` | Required surface does not exist or is not wired. | Implement only if in scope. |
| `unbound` | Surface exists but is not bound to real source/flow. | Bind to existing source. |
| `fake-or-stub` | Demo/mock/fallback is acting as real behavior. | Remove/replace truthfully. |
| `blocked` | Authority/evidence/dependency is unavailable. | Stop and report blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| `ROLE_PERMISSIONS` / Support | Current matrix grants employee-facing operational permissions but not Admin wildcard/destructive tokens | one canonical Support operational policy | partial | 13 local auth relationships | E0-P0A-SRC2 | preserve policy; reconcile tests/helpers in P1-A |
| Route visibility | `views/web_app.py` derives visible routes from `has_permission`; Support receives Contract, Shipment, Customer, Sales, Finance, reports, tariff, tracking, knowledge routes; User route requires `admin` | all current employee workflows visible to Support; User/security admin hidden | partial | route consumer in web app | E0-P0A-SRC2, E0-P0A-SRC4 | verify in P1-B |
| Contract UI | Contract forms and tabs now use `can_edit_contract()` over the existing matrix; mounted Support form has enabled save and no exception | Support controls enabled; validation and Vietnamese success/error are clear | correct for mounted control path | 18 local Contract relationships | E1-P1A-SRC1, E1-P1A-UI1 | preserve; continue sibling sweep |
| Contract service/repository | `save_contract_to_cloud`, `save_contract_transaction`, and atomic proxy Contract writer now reject unauthorized calls before mutation | authorized Support writes succeed; unauthorized direct calls fail before mutation | correct for covered writers | 146 central DB relationships | E1-P1A-SRC1, E1-P1A-DB1 | preserve; verify other writers P1-B |
| Contract reopen/readback | `load_contracts` reads persisted documents; fixture test proves Support create/update/fresh-readback | values survive fresh read after create and edit | correct | Contract + database | E1-P1A-TEST1, E1-P1A-DB1 | preserve |
| Customer operations | Support route is visible; import/create/edit buttons are not explicitly write-gated; repository save is not centrally gated | Support can perform ordinary customer operations; unauthorized direct writer fails | partial | customer surface + DB writer | E0-P0A-SRC4 | edit P1-B |
| Shipment/Pickup/Export/Import/Delivery | Support has `shipment_create`/`shipment_edit`; detail controls and import paths reach existing writers, with incomplete control/service guard coverage | Support can operate; protected delete remains Admin-only | partial | shipment surface + DB writer | E0-P0A-SRC2, E0-P0A-SRC4 | edit P1-B |
| Quotations/Agreements/factory data | Support matrix has `sales`, `sales_write`, `commercial_write`; some quote create/persist controls are UI-only | Support can use current operational quote/agreement workflow; Sale effective access unchanged | partial | quote/agreement surfaces | E0-P0A-SRC2, E0-P0A-SRC4 | edit P1-B |
| Documents/GNT/evidence | Existing current routes expose review/GNT/export/read flows; no new document-management route is needed | Support can use existing operational evidence/document flows without new authority | partial | shipment/review/dashboard surfaces | E0-P0A-SRC4 | inspect and verify P1-B |
| Tasks/quick work handling | Support has `operations_write`; dashboard task/note writes exist but are not all explicitly gated/audited | Support can create/complete ordinary tasks; admin/security boundaries remain separate | partial | dashboard + DB task writers | E0-P0A-SRC4 | edit P1-B/P1-C |
| Finance Actual | Support has `finance_write`; shipment direct payment already has a backend gate; lump-sum and some sibling writers are UI-only | actual cost/payment/AR/AP/reconciliation operations allowed with financial safety | partial | finance/payment/database | E0-P0A-SRC2, E0-P0A-SRC4 | edit P1-B/P1-C |
| Payment/reconciliation | Support has `receivables`, `proxy_payment`, `entrustment`; current finance route and contract finance exist, but legacy writer controls are uneven | Support payment/reconciliation succeeds; idempotency and protected history remain | partial | payment logic + DB + routes | E0-P0A-SRC2, E0-P0A-SRC4 | edit P1-B/P1-C |
| Audit/actor identity | `_audit` now stores actor string, canonical user ID, username, role, and timestamp; central document writers also stamp actor metadata | every Support mutation retains user ID, username, role, time, audit/provenance | partial (Contract covered; sibling regression pending) | `_audit` CRITICAL fan-in | E1-P1A-DB1, E1-P1A-IMPACT1 | continue P1-C |
| Admin-only boundaries | `Người Dùng` route requires `admin`; Support lacks `*`, delete tokens, and admin route permission | user/role/secrets/config/deployment/database/security/destructive functions remain unavailable | correct at matrix/route level; service audit pending | auth/web app/database | E0-P0A-SRC2, E0-P0A-SRC4 | preserve; prove negative paths P1-C |
| Sale permission | Immediate predecessor changed only Support; Sale set was not changed by that commit | exact previous Sale effective access, zero drift | correct by current diff; test coverage stale | auth + tests | E0-P0A-SRC1, E0-P0A-TEST1 | snapshot and prove P1-C |
| Test contract | LOG-C15 tests still assert old Support denial; finance fixture tests call a gated writer without an authenticated fixture | affected tests express the Owner decision and prove behavior | wrong/stale | auth + finance tests | E0-P0A-TEST1 | update only affected tests after code P1-A/P1-C |
| Runtime/Preview | No safe Preview credential was supplied; no Production runtime will be used | mounted evidence if available, otherwise honest pending status | blocked for browser-only proof | app/runtime | E0-P0A-SRC1 | use fixture/AppTest; report pending browser gate |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-09-03 | fresh `origin/main` fetch and isolated worktree at `c1c9468` before implementation | full Support RBAC/Contract operational family | initial matrix/route partial; Contract service/readback partial/missing; admin boundary correct; tests stale; browser blocked | E0-P0A-SRC1..E0-P0A-BUILD1 | proceed to P1-A; retain P1-B/P1-C sibling sweep |
| R1 | 2026-09-03 | P1-A implementation checkpoint in isolated worktree | Contract helper, UI guards, Contract writers, central actor/audit fields, focused tests | Contract UI/service/readback `partial/missing -> correct`; actor family remains partial pending sibling sweep | E1-P1A-SRC1..E1-P1A-UI1 | proceed to P1-B; preserve Contract behavior and test remaining writers |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `core/auth.py` | `views/web_app.py`, `views/contracts.py`, `core/database.py` | source-of-truth permission/actor consumer | P1-A/P1-C | edit | E0-P0A-ANV1 | preserve Admin wildcard and Sale effective set |
| `views/contracts.py` | `core/database.py`, `tests/test_contracts.py` | Contract UI writer/test | P1-A | edit | E0-P0A-SRC3 | no UI redesign; use semantic helper |
| `core/database.py` | Contract/customer/shipment/payment/task callers | central repository/audit writer | P1-A/P1-B/P1-C | edit narrowly | E0-P0A-ANV1 | CRITICAL fan-in; no unrelated refactor |
| `views/customers.py` | `core/database.py` | customer operation consumer | P1-B | edit narrowly | E0-P0A-SRC4 | no schema/route addition |
| `views/shipment.py` | `core/database.py` | shipment operation consumer | P1-B | edit narrowly | E0-P0A-SRC4 | preserve GNT/export and financial history rules |
| `views/quotations.py` / `views/agreements.py` | `core/database.py` | quote/agreement operation consumers | P1-B | edit narrowly | E0-P0A-SRC4 | no quote/agreement redesign |
| `views/dashboard.py` | `core/database.py` | task/import/detail consumer | P1-B | edit narrowly | E0-P0A-SRC4 | preserve admin-only delete and task identity |
| `core/payment_logic.py` | `core/database.py`, `views/finance.py` | receipt/allocation writer | P1-B/P1-C | edit narrowly | E0-P0A-ANV1 | preserve transaction/idempotency |
| `tests/*` | affected production modules | behavior/security evidence | P1-A/P1-B/P1-C | edit tests after code | E0-P0A-TEST1 | no stale contradictory assertions |
| `docs/plans/...` | source/evidence only | plan/evidence/benchmark status | P0/P1/Pn | edit | P0 records | no production source changes in docs |
| Production config/data | none | forbidden external target | all | do-not-touch | E0-P0A-SRC1 | zero Production mutations |

## Detailed Findings

### Contract authorization and persistence

Current state:

The predecessor matrix denied Support the `sales_write` token used by every Contract mutation control. The fresh current `main` merge adds that token and broadens the Support set, so the visible denial is no longer present in the current source. However, the view still expresses Contract authority as a repeated Sales-specific check, the service writers accept direct calls without a permission gate, and no Support create/edit/fresh-readback test proves the full loop.

Required state:

```text
Support opens Hợp Đồng, edits normal fields, creates a Contract, saves it, links supported shipment data, receives clear validation/success feedback, and reopens the persisted values. The same service boundary rejects unauthorized direct writes before mutation.
```

Evidence:

- `E0-P0A-SRC3`: direct source path and missing service gate.
- `E0-P0A-TEST1`: stale policy tests and no focused persistence proof.

Relationship and impact:

- Related file count: `views/contracts.py` 18 local; `core/database.py` 144 local / 44 inbound.
- Relationship summary: route → forms → Contract writers → `_audit`/Mongo collections.
- Impact note: high/critical shared writer family; slice narrowly and test rollback/idempotency.

Classification:

`partial` (UI matrix repaired in current baseline; semantic/service/readback closure missing).

Allowed next action:

Implement P1-A only after preserving current fields, validation, legacy read projections, and Sale/admin boundaries.

Forbidden next action:

Do not add a new RBAC framework, wildcard Support, schema migration, Production test, or session-only fake persistence.

### Operational siblings and actor traceability

Current state:

Support has all current employee-facing permission tokens in the fresh matrix, but multiple sibling writers rely on UI gates or have no central gate, and `_audit` does not retain canonical actor user ID/role fields consistently. Existing protected delete guards must remain Admin-only.

Required state:

```text
Every mounted ordinary business operation is usable by Support through the existing matrix, unauthorized direct writer calls fail closed, and each Support mutation has user_id, username, role, timestamp, and audit/provenance without weakening idempotency or protected-history rules.
```

Evidence:

- `E0-P0A-SRC2`: current permission tokens and Admin exclusion.
- `E0-P0A-SRC4`: sibling UI/service guard inventory.
- `E0-P0A-ANV1`: central writer/audit impact counts.

Relationship and impact:

- Related file count: central database high fan-in; dashboard/finance/payment siblings.
- Relationship summary: routes and legacy views converge on central writers, while some writers bypass `_audit`.
- Impact note: P1-B/P1-C must be narrow and prove unchanged finance safety.

Classification:

`partial`.

Allowed next action:

Audit and patch only the existing mounted operational family; add focused role/security/readback tests.

Forbidden next action:

Do not broaden Sale, permit Support user/security administration, rewrite financial semantics, or delete historical truth.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Current Support matrix contains the missing Contract write token, but Contract semantic/service/readback proof is partial/missing | keep P1-A; use helper and close UI→service→repository loop |
| P1-B | Support route/action tokens cover current employee operations, but sibling UI-only/backend gaps remain | keep P1-B; patch only existing writer/control gaps after P1-A refresh |
| P1-C | Admin route boundary is correct; actor metadata and stale tests are incomplete | keep P1-C; centralize metadata with focused high-fan-in regression |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence from `file-detail` when applicable.
- [x] Phase Touch Map lists plan-relevant relationship files that can affect the current phase/slice.
- [x] Phase Touch Map defines touch mode for every plan-relevant relationship unit that may be affected.
- [x] Correct parts are marked preserve-only.
- [x] Partial, missing, wrong, unbound, and fake-or-stub parts have exact next actions.
- [x] Blockers are recorded, if any.
- [x] Next phase status assumptions, next action, and work steps have been updated from this status file when needed.
- [x] Status Refresh Log has an R0 baseline row.
- [x] If implementation has started, affected Current Status Matrix rows have been refreshed from latest evidence.
- [x] If refreshed statuses changed next work, only the stale next-phase status assumptions, next action, or work steps have been updated before the next phase.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete. Current `origin/main` already contains a matrix-only Support expansion, so the candidate must not claim that a matrix edit alone is the fix. Proceed with the smallest semantic Contract helper, service-side authorization, mounted sibling sweep, actor/audit metadata, and focused persistence/security tests. Browser Preview remains pending if safe staging identity is unavailable; no Production mutation is allowed.
