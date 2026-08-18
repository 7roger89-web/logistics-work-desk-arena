# R4 — Permission Policy Reconciliation (LOG-LG02)

Date: 2026-08-18 (UTC)

Approved policy (from the Owner-approved LOG-LG01 release record): **ADMIN = full access; SALE = commercial access without finance write; SUPPORT = operational read-only on finance; no role holds destructive hard-delete as a normal correction path.**

## 1. Reconciliation matrix (candidate branch `ba4142c`; re-verified unchanged on tip `a96ad86` after LG02 hardening)

Full live matrix as of `a96ad86` (7 roles): admin `{*}`; sale 14 perms incl. `commercial_write`, `sales_write`, `sales`; support 12 perms incl. `operations_write`, `finance_view` (no writes anywhere); accounting 10 perms (legacy, `proxy_payment`, `receivables` — no finance/admin writes); operations 9 perms; sales 10 perms; viewer 6 read-only perms.

Boundary re-checks executed live on tip `a96ad86` (all TRUE): admin holds only `*`; sale lacks `finance_write`, `admin_write`, `receivables`, `finance_review_write`, `proxy_payment_delete`, `user_create/update/deactivate`; sale holds `commercial_write`, `sales_write`, `sales`, `commercial_view`; support lacks `finance_write`, `commercial_write`, `sales_write`, `shipment_create`, `admin_write`, `receivables`; support holds `operations_write` and `finance_view`; viewer holds no `*_write`; **no role (incl. legacy accounting/operations/sales) holds any `*_delete` permission**; admin is the only full-access role.

| Boundary | Evidence | Verdict |
|---|---|---|
| `admin` holds `{"*"}` (full access) | `core/auth.py` ROLE_PERMISSIONS | COMPLIANT |
| `sale` has no `finance_write`, `receivables`, `admin_write`, `finance_review_write`, `proxy_payment_delete`, `user_*` | Matrix enumeration + `tests/test_logc15_auth_rbac.py` (explicit assertions pass on candidate: 200/0) | COMPLIANT |
| `sale` holds `commercial_write`, `sales_write` (commercial authority) | views/agreements.py gates all agreement mutation behind `commercial_write`; views/finance.py gates finance actual writes behind `finance_write` | COMPLIANT — SALE can commercial-write but finance-write paths are a different permission SALE does not hold |
| `support` holds `operations_write` (operational corrections) but has no `finance_write`, `commercial_write`, `sales_write`, `shipment_create`, `admin_write`, `receivables` | `test_logc15_auth_rbac.py::test_support_is_read_only_on_finance_and_admin` passes; support lacks shipment creation | COMPLIANT |
| `support` can read finance (`finance_view`) but never write actuals | `views/finance.py` lines 95-97: finance actual write disabled and blocked by `has_write_permission("finance_write")` which support lacks | COMPLIANT |
| Shipment deletion is NOT a normal correction path | `core/database.py::delete_shipment` performs **soft delete** (`is_deleted=True`, `deleted_at`, `deleted_by`, `delete_reason`, audit entry `_audit(..., "soft_delete")`); hard delete does not exist anywhere in `core/` or `views/` | COMPLIANT |
| No role grants `shipment_delete`/`user_delete`/`proxy_payment_delete` except admin `*` | Enumeration: no role (incl. legacy) holds any `*_delete` perm; `shipment_delete` only hides/shows the UI button in `views/dashboard.py:619` | NOTE — see item 2 |
| AGREED agreement cannot be silently overwritten | `core/commercial_agreements.py` bounded transition table: `AGREED -> {REVISED}` only; revision opens a new DRAFT keeping the AGREED document | COMPLIANT |
| User deactivation writes provenance | `core/users.py`: `deactivated_by`/`reactivated_by` actor fields + audit note | COMPLIANT |
| Bootstrap creates first admin only when users collection empty | `core/auth.py::require_login` — `_render_bootstrap_setup` shown iff `user_count == 0` | COMPLIANT (R9) |
| Anonymous fall-back to viewer | `_role_permissions` falls back to viewer; viewer has no write perms | COMPLIANT |

## 2. Bounded correction identified (Section 21 allows tightening before release)

The `shipment_delete` permission exists only in the UI layer (`views/dashboard.py` hides the delete button), but `delete_shipment()` itself has **no backend permission gate** — any authenticated session that retains an active session could theoretically reach it if the UI changed. The contract permits hardening the enforcement point without redesign:

**Tightening applied (minimal, behavior-preserving):** `core/database.py::delete_shipment` now asserts `has_write_permission("shipment_delete")` before executing the soft delete; callers in `views/dashboard.py` unchanged. No role grants `shipment_delete` today, so the effective behavior is identical for all approved roles while eliminating the class of UI-only authorization defect permanently.

RBAC regression re-run after tightening: full suite **200 passed / 0 failed**, `test_logc15_auth_rbac` passes including `assert_permission` denial cases.

## 3. Verdict

**RBAC_RECONCILIATION = PASS** (one bounded backend-gate tightening applied and regression-verified). The candidate role matrix exactly matches the approved policy: ADMIN full; SALE commercial without finance write; SUPPORT operational with finance read-only; no role performs hard-delete as a correction path.
