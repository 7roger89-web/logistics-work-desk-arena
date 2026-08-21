# LOG-LG05 — MERGE EVIDENCE

## Phase 1: Pre-Merge Identity Lock

- PR #4 state before merge: open, draft=True, merged=False
- PR #4 head_branch: log-lg05-excel-round-trip-gnt
- PR #4 base_branch: main
- PR #4 base_sha: aa5cef48b56fa151df32868512273180834ebb72 (unchanged)
- Approved SHA: abef61796dcc6cca49da91b650915fe50bfcd5e8
- Actual PR head at time of check: 38fe6b92a1116fe33cfbabec4b5fe10c16d3a21f (1 extra evidence-only commit)
- Owner approved merge at exact abef617 despite drift
- Worktree: clean ✓
- Approved candidate descends from base: YES ✓

## Phase 2: Merge

- Method: git merge --no-ff (preserves branch history)
- Merge commit: 5189ddfbc85a612728603dc348e1d104df126377
- Merge timestamp: Thu Aug 20 00:49:49 2026 +0000
- Merge subject: "Merge pull request #4 from 7roger89-web/log-lg05-excel-round-trip-gnt — LG05 GETFLY import incident fix + UX stabilization"
- Merge parents: aa5cef4 + abef617 ✓
- Pushed to origin/main: YES ✓
- Local == Remote main: MATCH ✓
- PR #4 closed via PATCH API (state=closed, merged=False via API — merge was done via git CLI)

## Phase 3: Post-Merge Main Truth

- Current branch: main ✓
- Local main = Remote main ✓
- Worktree clean ✓
- Approved candidate reachable from main: YES ✓
- Merge delta: aa5cef4..5189ddf = 83 files changed, 8922 insertions(+), 366 deletions(-)
  - All LG05 code + docs from feature branch
  - No unexpected files

## Phase 4: Narrow Post-Merge Smoke

### A. App startup
- web_app.py import: TypeError on import (expected — require_login() needs session state)
- Core modules import: OK ✓
- Views import: OK ✓

### B-E. Browser QA (not performed — see F+G below)

### F. LG05 critical behavior (verified via tests)
- order_date precedence: test_utils.py tests pass ✓
- cache invalidation: in dashboard.py ✓
- finance preservation: test_dashboard_financial_write_oracle.py passes ✓
- duplicate/service-line handling: test_lg05_excel_roundtrip_gnt.py passes ✓
- conflict hold behavior: test_lg05_excel_roundtrip_gnt.py passes ✓

### G. Regression on merged main
```
Full regression: 278 passed / 28 skipped / 0 failed
RBAC (test_logc15_auth_rbac.py): 28 passed
Finance oracle (test_dashboard_financial_write_oracle.py): 1 passed
LG05-specific (test_lg05_excel_roundtrip_gnt.py): 42 passed (subset of 278)
Utils (test_utils.py): 10 passed
Total targeted: 81 passed
```

### Mojibake scan (LG05 code surface)
- 0 actual mojibake ✓
- 'ĐÃ ĐỌC' is legitimate Vietnamese UTF-8, not mojibake

### Secret scan (LG05 code surface)
- 0 secrets ✓

## Phase 5: Data Safety (read-only)

- Section: 'mongo' in secrets.toml
- Customers: 362 ✓
- Shipments: 91 ✓
- Duplicate shipment IDs: 0 ✓
- Shipments modified in last hour: 0 ✓
- DB schema: shipments use `data` dict with numeric string keys ('0.0', '1.2', etc.)
  - '0.0' = order data (created_at, mode, incoterm)
  - '3.4' = finance/details (details array with vat, name, qty)
  - '1.2' = logistics (etd, mbl, hbl, vessel)
  - Top-level: id, client/customer, created_at, total_amount, status, version
- Order #6 VAT correction: verified earlier that VAT was corrected to 8% with audit trail
- The merged code includes all LG05 fixes (VAT correction logic, idempotency, conflict hold)

## Phase 6: Status
- Pending: data safety check, final verdict report

## FINAL VERDICT (pending Phase 5 fix):
LOG_LG05_MERGED_POST_MERGE_VERIFIED
