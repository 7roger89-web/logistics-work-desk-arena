# LG01-T10: W7 Release Operations Package

Branch: `log-lg01-multi-user-internal-rc`. Candidate SHA: `23d17e5c7099725bfd1b29b5f6f7f869a8ba91ae`. Baseline: `05fa777` (LOG-C15 verified root). Date: 2026-08-17.

## 1. Candidate identity

The release candidate lives on branch `log-lg01-multi-user-internal-rc` of `7roger89-web/logistics-work-desk`, at commit `23d17e5`. A Draft PR will be opened against `main` as part of T11 (not merged by this Goal). Provenance chain: `05fa777` (LOG-C15) → `5e4d919` (T01 recovery) → `db1219f` (T02) → `a13fc40` (T03) → `1e920a4` (T04) → `efcb100` (T05) → `cb371a5` (T06) → `b41e5a9` (T07) → `23d17e5` (T09).

## 2. Supported user roles and permission matrix

Three official roles plus four legacy-compatibility roles (no material widening performed this Goal; see `docs/goals/LOG-LG01/evidence/w2_permission_audit.md`).

| Role | Key permissions | Notes |
|---|---|---|
| admin | `*` (all) | Can create users, manage roles, review queue |
| sale | dashboard, shipment_create, shipment_edit, customers, sales, sales_write, contracts, tariff, tracking, knowledge, shipment_360_read, entity_context, commercial_view, commercial_write | Commercial lifecycle owner |
| support | dashboard, shipment_edit, customers, shipment_360_read, entity_context, contracts, tariff, tracking, knowledge, commercial_view, finance_view, operations_write | Operations + read-only finance |
| accounting (legacy) | dashboard, shipment_edit, customers, contracts, proxy_payment, receivables, entrustment, reports, knowledge, finance_view | Unchanged, kept compatible |
| operations (legacy) | dashboard, shipment_create, shipment_edit, customers, contracts, tariff, tracking, knowledge, commercial_view, sales_write | Unchanged |
| sales (legacy) | dashboard, shipment_create, shipment_edit, customers, contracts, tracking, knowledge | Unchanged |
| viewer (legacy/default) | dashboard, reports, tracking, knowledge, commercial_view, finance_view | Unknown role falls back to viewer (fail-closed) |

**Unresolved Owner Gates tied to permissions:** none opened this Goal — the audit confirmed all permission keys are pre-existing, no material widening, no destructive-permission gap found. Policy decisions remain the Owner's: who may hard-delete users, who may destructively mutate agreements, who may approve payments. These are business-policy choices, not code defects.

## 3. Environment matrix DEV/TEST/PROD

| Environment | DB | URI source | Status this Goal |
|---|---|---|---|
| DEV | `logistics_workdesk_logc14` | local `.env` / `.streamlit/secrets.toml` (untracked) | Default identity, fail-closed when identity missing (`docs/goals/LOG-LG01/evidence/w1_hardening.md`) |
| TEST | `logistics_workdesk_LG01_E2E` | isolated secrets file (LG01-only evidence DB) | Created fresh this Goal for E2E; contains only synthetic LG01 test records; no production data |
| PROD | any DB named `logistics_db` is blocklisted | `core/config._PRODUCTION_DB_NAMES` | `validate_mongo_identity()` raises `RuntimeError` at startup if identity is empty or production — app refuses to run rather than risk prod writes |

**Production DB decision: NOT MADE.** Choosing a production database, switching to it, or migrating data are all Owner Gates (Section 36.B). The candidate refuses to start against a production-named DB, so no accidental promotion is possible without an explicit Owner decision.

## 4. Secret / config checklist

Configuration flows through `MONGODB_URI`, `GEMINI_API_KEY`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `TARIFF_DB_PATH` (from `.env.example`) or `.streamlit/secrets.toml`. Checklist before any deployment: `.env` exists and contains real values; `MONGO_DB_NAME` explicitly set to a non-production, non-empty name inside `MONGO_ALLOWED_DB_NAMES`; `.streamlit/secrets.toml` never committed (gitignored, example-only template in repo); `tariff.db` never re-introduced into Git; `.env.example` / `secrets.toml.example` contain only placeholders (`YOUR_VALUE_HERE`). Secret scan result: PASS (see `docs/goals/LOG-LG01/evidence/w6b_responsive_tariff_secrets.md`).

## 5. First-admin bootstrap procedure

The app self-bootstraps when no users exist: `_render_bootstrap_setup()` (`core/auth.py`) presents a form requiring a 3–30 character username, display name, email (optional), and a password ≥ 8 characters confirmed twice; `_complete_bootstrap()` creates the first user as role **admin** with `created_by="bootstrap"`. On top of that, the running admin screen (`views/web_app.py`, `_create_user_from_admin`) creates subsequent users with an explicit role selection, and `set_active()` in `core/users.py` can disable any account. Bootstrap requires a running app connected to the target DB, so it must be executed deliberately per environment (DEV, then TEST, and only in PROD after the Owner's environment decision).

## 6. Backup prerequisites

Before any future production work, the Owner should arrange a point-in-time MongoDB Atlas backup or export (`mongodump`) of the production database, stored separately from the application host. This Goal performed no production reads or writes, so no production backup action was taken.

## 7. Rollback procedure

No production change was made, so production rollback is a no-op (`NOT_PERFORMED`). For the application itself: `git checkout main` returns to the pre-LG01 baseline `05fa777` verified lineage; the branch is fully reversible without merge. Secrets are environment-local and unaffected by git operations.

## 8. Smoke-test procedure

After starting the app (`streamlit run app.py`), verify in order: (1) login screen renders and rejects wrong passwords; (2) admin bootstrap or login succeeds; (3) Dashboard loads with real collection counts; (4) a sale user can create a customer and quotation and sees the Review Queue; (5) a support user sees Finance Review read-only; (6) denial message shows user name, screen, and admin contact when permission is missing. Automated coverage: `tests/test_logc15_auth_rbac.py` (27 tests) + `tests/test_lg01_env_security.py` (7 tests) + LG01 E2E suite (29 tests) — all green at this SHA.

## 9. Known limitations

Commercial totals in Finance Review are estimates, not actual payments (explanation now surfaced in the UI). Tariff reference data is local-CSV only (`tariff.db` excluded by policy) — missing data renders empty, never fabricated. No WCAG certification (bounded responsive evidence only). Legacy roles kept for compatibility; their semantics are inherited, not re-verified against current business policy.

## 10. Risk ledger

| ID | Risk | Severity | Mitigation / status |
|---|---|---|---|
| R1 | App starts against wrong DB and writes production | P0 | Fail-closed identity validation — app raises RuntimeError; TEST DB isolated; no prod writes performed |
| R2 | Permission policy mismatch with business intent | P1 | Audit passed; Owner retains policy authority (gate B.A) |
| R3 | User accounts compromised via weak passwords | P2 | pbkdf2_sha256 390k iterations; no default passwords shipped |
| R4 | Multi-user concurrent write conflict | P2 | Optimistic version locking + idempotent upserts (20/20 by-fields, T05) |
| R5 | Tariff data unavailability | P3 | Graceful empty-state handling verified |
| R6 | Legacy role semantics drift | P3 | Documented in w2 audit; no widening performed |

## 11. Recovery instructions (for another executor)

Read `docs/goals/LOG-LG01/state.json` for the durable DAG state (`current_task`, `task_statuses`, `next_safe_task`, `current_git_sha`), then read `docs/goals/LOG-LG01/checkpoint_RECOVERY.md` and the latest evidence files under `docs/goals/LOG-LG01/evidence/`. The execution contract lives with the Owner. Resume from `next_safe_task` on branch `log-lg01-multi-user-internal-rc`. E2E evidence DB `logistics_workdesk_LG01_E2E` may be dropped or preserved; it holds only synthetic test data.

## 12. Release checklist (Owner-visible)

| Item | Status |
|---|---|
| Candidate SHA identified | 23d17e5 |
| Tests green (unit + RBAC + env security + E2E) | 63/63 green |
| Finance mutation oracle (0 canonical finance writes) | Verified |
| Fail-closed production protection | Implemented + tested |
| Secret scan | PASS |
| Draft PR | To be opened T11 |
| Production DB decision | PENDING — Owner Gate |
| Production migration | NOT_PERFORMED |
| Deploy | NOT_DEPLOYED |
| Merge | NOT_MERGED_BY_LOG_LG01 |
| Release status | NOT_RELEASED |
