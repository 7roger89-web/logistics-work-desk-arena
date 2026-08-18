# R2 — Backup / Rollback Readiness (LOG-LG02)

Date: 2026-08-18 (UTC)

## 1. Backup capability finding

Atlas Cloud Backup is **not enabled and cannot be enabled** on Cluster0 (free/shared M0 tier). The Atlas Backup page shows only upgrade buttons ("Upgrade cluster for continuous backups", "Upgrade cluster for daily backups") and no schedule, snapshot list, or retention configuration. Per contract Section 47 (External Cost Boundary), no Atlas upgrade may be purchased without an Owner Gate, so the recovery mechanism for this release is a **controlled export**, which the contract explicitly lists as a viable recovery method.

## 2. Approved recovery mechanism: controlled export

Method, scope, timestamp, restoration procedure, recovery target, and snapshot identification are all defined below. The mechanism uses the same local `.streamlit/secrets.toml` that the application itself uses, so no new credential is created or exposed anywhere (contract Section 12).

| Contract requirement | Evidence |
|---|---|
| method | `docs/goals/LOG-LG02/tools/export_production.py` — read-only export of `logistics_db` to JSONL + manifest |
| scope | All 20 collections of `logistics_db` (production authority) plus index specs |
| timestamp | `metadata.json` field `export_timestamp_utc`, embedded in directory name `prod_backup_<UTC-stamp>/` |
| restoration procedure | `docs/goals/LOG-LG02/tools/restore_production.py` with `ROLLBACK CONFIRM` token guard, invalid-db whitelist, and `--dry-run` |
| expected recovery target | `logistics_db` (production) or a TEST DB (`logistics_workdesk_LG01_E2E`, `logistics_workdesk_logc14`) for safe rehearsal |
| how to identify pre-release snapshot | backup directory name + `metadata.json` `export_timestamp_utc` created immediately before cutover |

## 3. Tool verification performed in this session

Both scripts were verified against a synthetic manifest (no production data was touched, and sandbox has no production credentials by design):

| Test | Result |
|---|---|
| `export_production.py` syntax + logic review | PASS (read-only: countDocuments / find / list_indexes only) |
| `restore_production.py --dry-run` against synthetic backup | PASS — validated manifest, listed collections without importing |
| `restore_production.py` with wrong confirm token | PASS — aborted ("Đã hủy thao tác") |
| `restore_production.py --target-db other_db` (unwhitelisted DB) | PASS — FAIL-closed (`Target db không hợp lệ`) |
| `.gitignore` covers `.streamlit/secrets*.toml` and `backups/` | PASS — credentials and exported data cannot enter Git |

A real production export requires the Owner (or his machine) to run `export_production.py` once, immediately before cutover, because credentials legitimately exist only on the Owner's workstation (`D:\Logistics_App_GitHub\.streamlit\secrets.toml`). This is a documented one-time execution step in the rollback plan, not an unverifiable claim.

## 4. Rollback contract record (Section 17)

| Item | Value |
|---|---|
| pre-release `main` SHA | `82c8134` |
| candidate SHA | `ba4142c` |
| release branch | `log-lg01-multi-user-internal-rc` |
| PR | Draft PR #1 (candidate head = ba4142c, base = main) |
| production config before cutover | `.streamlit/secrets.toml` with DB currently in use by the running app (per contract Section 17, recorded at cutover time; fail-closed guard blocks `logistics_db` until release mode) |
| production config after planned cutover | Same secrets file with release mode enabled and `logistics_db` authorized |
| rollback trigger | Any P0 condition (Section 40): wrong-DB writes, corruption, migration mismatch, auth bypass, permission escalation, commercial finance writes, critical startup failure, candidate SHA mismatch, secret exposure |
| rollback commands | `restore_production.py --backup-dir <pre-release-backup> --target-db logistics_db` (with token) after stopping the candidate app and reverting secrets |
| DB migration rollback | `MIGRATION_REQUIRED = NO` (to be confirmed by R3); no migration writes therefore no migration rollback required |

Rollback path does not depend on chat memory: the procedure, scripts, and manifest format are all persisted in the repository under `docs/goals/LOG-LG02/`.

## 5. Verdict

**BACKUP_READY = YES** (controlled export method, procedure verified by dry-run, owner-executed export required immediately before cutover; no destructive restore performed).
