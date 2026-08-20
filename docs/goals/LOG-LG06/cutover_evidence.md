# LOG-LG06 — CUTOVER READINESS EVIDENCE

## Phase 0-1: Git Truth + Runtime Identity

### Git
- Branch: `main` (HEAD = `c6c0afe`)
- PR #4: MERGED (merge SHA `5189ddf`)
- Worktree: clean
- Remote: `origin/main` = `c6c0afe` (matches local)

### Runtime
| Port | PID | Code path | SHA | DB | Purpose |
|------|-----|-----------|-----|----|---------|
| 8501 | 71110 | /home/ubuntu/logistics_repo | c6c0afe (current main) | logistics_db | PRODUCTION |
| 8502 | 52481 | /home/ubuntu/logistics_repo | c6c0afe (current main) | logistics_db | PREVIEW (same code) |
| 8601 | 19381 | /tmp/repro_root/web_app.py | stub (95 bytes) | unknown | REPRO (ignore) |

**KEY FINDING:** Port 8501 (production) is ALREADY running current main (c6c0afe) which includes all LG05 fixes. The code-level cutover has already happened.

### DB
- Cluster: cluster0.qvjh5ji.mongodb.net (Atlas)
- Database: `logistics_db`
- Config: `identity=PROD_INTERNAL`, `release_mode=true`

## Phase 2: Production Data Safety (READ-ONLY)

### Collections
| Collection | Count |
|------------|-------|
| customers | 362 |
| shipments | 91 |
| users | 4 |
| contracts | 6 |
| agreements | 1 |
| proxy_payments | 2 |
| tasks | 8 |
| legacy_historical_staging | 289 |
| legacy_historical_review_actions | 27 |
| audit_logs | 60 |
| counters | 2 |
| quick_notes | 1 |
| quotes | 1 |
| All others | 0 |

### Shipments Structure
- ID field: `id` (e.g., "T12-LÔ QUANG MINH - HT35240/HT35241, HT47042/HT47043")
- Also: `shipment_id` (same value)
- Data stored in `data` dict (keyed by service line index like "0.0")
- Top-level: `client`, `customer`, `status`, `is_deleted`, `is_archived`, `updated_at`, `version`

### Indexes
- `_id_` (unique, MongoDB default)
- `uq_shipment_id` (unique on `id`, partial filter `id: {type: string}`)
- `ix_shipment_worklist` (compound: is_deleted, is_archived, status, updated_at)
- `ix_shipment_customer` (customer_id, updated_at)
- `ix_shipment_contract` (contract_id, updated_at)

### Duplicate Check
- **0 duplicates** on `id` field (unique index enforces)

### Conflict Status
- Shipments with conflict_status: **0** (all resolved)
- Held for review: **0**
