# LOG-LG02 progress notes (2026-08-18)

## Status summary
- R0 DONE: CANDIDATE_PROVENANCE = VERIFIED (main 82c8134, candidate ba4142c on log-lg01-multi-user-internal-rc, PR#1 head matches, chain 3434339 -> ba4142c clean, no rebase). Evidence: state.json + earlier evidence file.
- R1 DONE: logistics_db on Cluster0 (Atlas M0 free), 20 collections/52 indexes/~1.23MB. customers 362, shipments 78, audit_logs 54, legacy_historical_staging 289, legacy_historical_review_actions 27, contracts 6, proxy_payments 2, quick_notes 1, finance canonical 0 docs, NO users collection. Evidence: evidence/R1_atlas_env.md.
- R2 DONE: BACKUP_READY=YES controlled export (Atlas M0 has no managed backup, contract-allowed). Tools: tools/export_production.py (read-only, uses app secrets.toml), tools/restore_production.py (ROLLBACK CONFIRM token, whitelist, --dry-run). Synthetic dry-run verified. Evidence: evidence/R2_backup_rollback.md.
- R3 DONE: REHEARSAL PASS, MIGRATION_REQUIRED=NO. Local mongod 8.0, DB logistics_workdesk_LG01_E2E seeded with prod shape 819 docs (counts match prod). Tools: tools/seed_rehearsal_db.py, tools/run_rehearsal_load.py (all 7 checks pass incl fail-closed both directions). Full pytest baseline on candidate: 200 passed, 28 skipped (playwright UI), 0 failed. Evidence: evidence/R3_rehearsal.md.
- R4 IN PROGRESS: auditing core/auth.py. Findings so far (see below).
- R5/R6 TODO: production config prep (MONGO_DB_NAME=logistics_db + release mode), secret scan (gitleaks/tfsec/grep), full preflight, terminal report, push to candidate branch, update PR #1 description (allowed by Section 45), stop at Owner Release Gate.

## Auth.py audit findings (R4)
core/auth.py ROLE_PERMISSIONS:
- admin: {"*"} — full admin, matches policy.
- sale: dashboard, shipment_create, shipment_edit, customers, sales, sales_write, contracts, tariff, tracking, knowledge, shipment_360_read, entity_context, commercial_view, commercial_write.
  - Check needed: does commercial_write or any sale view allow finance actual write? Need to grep where finance_write/finance_approve actions are enforced (core/finance*.py, views/finance.py) and whether sale has finance_view — sale does NOT have finance_view in ROLE_PERMISSIONS (policy: Finance Review may be read-only where needed — sale lacks finance_view; support has it). SALE lacks: user_* perms, admin perms — good. sale has no "finance_write"/"finance_approve" perm listed — check action perms in code: e.g. core.financial_ledger checks action perms.
- support: dashboard, shipment_edit, customers, shipment_360_read, entity_context, contracts, tariff, tracking, knowledge, commercial_view, finance_view, operations_write.
  - support has NO shipment_create (policy: no commercial mutation), no sales_write, no commercial_write — good. support has shipment_edit but must NOT destructively delete shipment — check if shipment_edit covers delete (views/shipment.py) and whether delete is a separate perm "shipment_delete".
- viewer: dashboard, reports, tracking, knowledge, commercial_view, finance_view.
- legacy roles kept: accounting, operations, sales.
- Key risk to audit: "commercial_write" on sale — does it allow mutating AGREED agreements (Section 21: Support must not destructively modify commercial agreement authority; agreements AGREED must use revision/amendment path)? Check core/commercial_agreements.py + views/agreements.py for amendment path and perm checks.
- Audit: audit_logs collection + audit trail functions exist (core.database? state.py?) — verify material destructive actions (user deactivation, sensitive) write audit_logs with actor identity.
- current_actor() fallback to "system" only when AUTH_REQUIRED off — ok.
- Bootstrap: when users collection empty, render _render_bootstrap_setup (first admin) — matches R9; must be disabled after first admin (user_count == 0 guard) — ok.
- PermissionDeniedError generic message — ok.

## Important file inventory
- Contract: /home/ubuntu/upload/pasted_content.txt
- Repo: /home/ubuntu/logistics_repo (branch main 82c8134; working tree currently on main? verify — git status showed on main; candidate on origin branch).
- PAT token: /home/ubuntu/upload/pasted_file_vZOrYO_token-manus-new.txt (repo access 7roger89-web/logistics-work-desk; user thanhfle). API helper earlier used TOKEN=$(cat ...) pattern.
- state.json: docs/goals/LOG-LG02/state.json — keep updated each phase.
- Local mongod running in sandbox (systemctl start mongod; URI mongodb://localhost:27017).
- Evidence dir: docs/goals/LOG-LG02/evidence/ (R1_atlas_env.md, R2_backup_rollback.md, R3_rehearsal.md).
- Git push must go to candidate branch log-lg01-multi-user-internal-rc (do not touch main).

## Remaining work
1. R4: finish audit (grep finance actions + agreement amendment path + audit trail), write evidence/R4_rbac.md; only bounded minimal corrections if needed (contract authorizes tightening pre-release).
2. R5: production config prep — check core/config.py release mode; ensure logistics_db NOT in MONGO_ALLOWED_DB_NAMES default; add production release mode flag (env/secret) per Section 23-24; write config plan doc; NEVER commit secrets.
3. R6: secret scan (grep + gitleaks if available; check history for secrets with git log -S), full preflight = rerun all tests on candidate with rehearsal DB + env tests + RBAC matrix + oracle + fail-closed; write preflight checklist report; checkpoint READY_FOR_CONTROLLED_CUTOVER.
4. Push docs/goals/LOG-LG02/* to candidate branch; update Draft PR #1 description with preflight evidence; stop at Owner Release Gate (Vietnamese explanation + "Anh có phê duyệt INTERNAL RELEASE không?").
5. Terminal report sections per contract 49-50.
