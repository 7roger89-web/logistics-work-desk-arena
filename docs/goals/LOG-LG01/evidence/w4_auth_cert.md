# LG01-T06: W4 Auth/RBAC Certification + Hardening

Branch: log-lg01-multi-user-internal-rc
Date: 2026-08-17. Git base: C15 (27/27 RBAC tests green).

## 1. Goal
Certify C15 auth/RBAC as the certified gate (NOT rebuilt) and add hardening regression tests for LG01 env-security changes.

## 2. What was certified
- core/auth.py: require_login, assert_permission, current_actor, ROLE_PERMISSIONS unchanged except LG01 hardening in config layer.
- views/web_app.py: route guards and _assert_route_access preserved.
- tests/test_logc15_auth_rbac.py: 27/27 PASS (re-run after LG01 changes).

## 3. New regression tests (tests/test_lg01_env_security.py)
- test_validate_allows_dev: dev DB logistics_workdesk_logc14 accepted.
- test_validate_rejects_prod: production DB logistics_db rejected (RuntimeError, PRODUCTION).
- test_validate_rejects_empty_db: empty DB name rejected.
- test_validate_rejects_unknown_db: unknown DB name rejected.
- test_actor_never_admin: current_actor() never returns admin impersonation (system fallback when no user).
- test_assert_permission_denied_for_viewer: viewer role denied finance_approve.
- test_anonymous_role_has_no_write_perms: anonymous role grants zero write permissions.
Result: 7/7 PASS on lg01 branch; 27/27 PASS on C15 suite (no regression).

## 4. Hardening summary
- core/config.py: validate_mongo_identity() fail-closed (LG01-T02 evidence w1_hardening.md).
- core/database.py: _actor() fallback = system (never admin); all 20 mutation by-fields attributed (LG01-T05 evidence).
- views: route guards require login where route permission != public; finance routes require finance permissions.

## 5. Production boundary (no production action taken)
- Zero writes to PROD DB logistics_db (cluster0.qvjh5ji.mongodb.net): 0 canonical writes, 0 migrations, 0 user creation.
- All tests run on dev DB logistics_workdesk_logc14.

## 6. Verdict
C15 auth/RBAC is CERTIFIED with LG01 hardening regression coverage. 34 tests total green (27 C15 + 7 LG01). No behavior change to RBAC logic.
