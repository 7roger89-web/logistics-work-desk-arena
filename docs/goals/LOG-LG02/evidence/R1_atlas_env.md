# R1 Evidence: Atlas Environment Discovery (read-only)
Date: 2026-08-18 (user timezone GMT+7)
Method: User's own browser session (My Browser), logged into cloud.mongodb.com.
Read-only. No mutations performed.

## Findings so far
- Organization: "truong thanh logistics"
- Project: "Project 0"
- Cluster: **Cluster0** (free/shared tier indicator: "Data Size: 119.06 MB / 512 MB" — 512 MB shared M0 tier)
- Tag: application: logistics
- Backup menu exists in sidebar (Backup feature visibility)
- PyMongo v4.17.0 driver suggestion shown

## Important constraints for later
- Free/shared M0 tier: continuous backup may NOT be available; snapshots on M0 are limited. Must verify Backup page.
- Connection string available from Connect button (not recorded; credentials must not be committed).

## Collection inventory: TO BE COMPLETED (browse collections on logistics_db)

## Cluster0 Data Explorer snapshot (2026-08-18, read-only)
Organization: truong thanh logistics | Project: Project 0 | Cluster: Cluster0 (replicaSet id 6951608339cbf36bd2f11270)

| Database | Storage size | Data size | Collections | Indexes |
|---|---|---|---|---|
| admin | 0 B | 0 B | 0 | 0 |
| local | - | - | 0 | - |
| **logistics_db** (PROD authority) | 827.39 kB | 1.23 MB | **20** | **52** |
| logistics_workdesk_LG01_E2E (TEST) | 258.05 kB | 4.53 kB | 7 | 7 |
| logistics_workdesk_logc14 (DEV) | 192.51 kB | 38.81 kB | 19 | 50 |
| sample_mflix (sample data) | 99.66 MB | 101.11 MB | 6 | 10 |

Note: All 3 logistics DBs exist on the SAME cluster (cluster0.qvjh5ji.mongodb.net per LG01 evidence). sample_mflix is leftover sample data. Free shared tier (512 MB pool).

## logistics_db collection inventory (Atlas Data Explorer, 2026-08-18, read-only)
Total: 20 collections, 52 indexes. Data size 1.23 MB / storage 827.39 kB.

| Collection | Storage | Data | Docs | Avg size | Indexes |
|---|---|---|---|---|---|
| audit_logs | 106.50 kB | 207.43 kB | 54 | 3.84 kB | 2 |
| contract_transactions | 4.10 kB | 0 B | 0 | - | 2 |
| contracts | 36.86 kB | 4.14 kB | 6 | 690 B | 3 |
| customers | 102.40 kB | 122.01 kB | 362 | 337 B | 2 |
| entrustments | 4.10 kB | 0 B | 0 | - | 2 |
| financial_action_requests | 4.10 kB | 0 B | 0 | - | 2 |
| financial_allocations | 4.10 kB | 0 B | 0 | - | 4 |
| financial_corrections | 4.10 kB | 0 B | 0 | - | 3 |
| financial_obligations | 4.10 kB | 0 B | 0 | - | 4 |
| financial_transactions | 4.10 kB | 0 B | 0 | - | 4 |
| knowledge_base | 4.10 kB | 0 B | 0 | - | 2 |
| legacy_historical_review_actions | 53.25 kB | 52.31 kB | 27 | 1.94 kB | 3 |
| legacy_historical_staging | 270.34 kB | 698.22 kB | 289 | 2.42 kB | 3 |
| notification_outbox | 4.10 kB | 0 B | 0 | - | 3 |
| payment_receipts | 4.10 kB | 0 B | 0 | - | 2 |
| proxy_payments | 36.86 kB | 960 B | 2 | 480 B | 2 |
| quick_notes | 36.86 kB | 280 B | 1 | 280 B | 1 |
| rate_cards | 4.10 kB | 0 B | 0 | - | 2 |
| shipments | 102.40 kB | 147.76 kB | 78 | 1.89 kB | 5 |
| users* | not visible in partial list (20 collections counted; need scroll check; NOTE users collection may exist in DEV db logistics_workdesk_logc14 19 coll; check) | - | - | - | - |

Notable: Many finance-related collections are EMPTY (0 docs) in PROD — production is light on finance data. Real business data: customers 362, shipments 78, audit_logs 54, contracts 6, legacy_historical_staging 289, legacy_historical_review_actions 27, proxy_payments 2.
Total docs ~ 825 in logistics_db.

## Verification of collection list completeness
Markdown extraction of logistics_db shows exactly 19 named collections (audit_logs ... shipments). Header said 20 collections. Need to check bottom of list for a possible 20th (possibly users, tariffs, or _id hidden). Also need to expand shipments detail for schema check later (via document view, read-only).

## Complete collection list — 20 confirmed
The 20th collection is `tasks`: storage 36.86 kB, data 1.10 kB, 8 docs, 1 index (36.86 kB total index size). Full list: audit_logs, contract_transactions, contracts, customers, entrustments, financial_action_requests, financial_allocations, financial_corrections, financial_obligations, financial_transactions, knowledge_base, legacy_historical_review_actions, legacy_historical_staging, notification_outbox, payment_receipts, proxy_payments, quick_notes, rate_cards, shipments, tasks. NOTE: `users` collection does NOT exist in logistics_db — admin bootstrap creates users in whichever DB the app connects to; PROD users must be bootstrapped at cutover time (this is a known LG01 gate: bootstrap procedure required at PROD first boot).

## R2 backup evidence (Atlas Backup page, 2026-08-18)
The project Backup page shows the "Introducing Backups" upsell with two buttons only: "Upgrade cluster for continuous backups" and "Upgrade cluster for daily backups". There is no schedule page, no snapshot list, and no backup retention configuration for Cluster0 — confirming that Atlas Cloud Backup is NOT enabled and CANNOT be enabled on the current free shared tier (M0). This is the critical R2 finding: production cutover cannot rely on Atlas-managed backup/restore. The fallback mechanisms are (a) manual export of logistics_db via Data Explorer collection-by-collection JSON export, (b) mongodump/mongoexport against the cluster using the existing application connection string (requires user-provided read/write-capable or admin credentials), or (c) upgrading the Atlas tier. The 1.23 MB data size makes a manual export fast and low-risk.
