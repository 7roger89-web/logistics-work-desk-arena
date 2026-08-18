# R5 — Production Configuration Preparation (LOG-LG02)

Date: 2026-08-18 (UTC)

## 1. Production release gate added (Section 23-24, fail-closed by default)

`logistics_db` remains **fail-closed** in the candidate even after this workstream completes. Two independent gates must now BOTH pass before the candidate can open the production database, and only the Owner can satisfy them:

| Gate | Mechanism | Default |
|---|---|---|
| Release-mode switch | New setting `MONGO_RELEASE_MODE` (`[mongo].release_mode` in `.streamlit/secrets.toml`, or env var `MONGO_RELEASE_MODE=true`); `validate_mongo_identity()` rejects `logistics_db` unless the switch is truthy | **OFF** |
| Allowed-database list | Existing LG01 guard: `logistics_db` must additionally be present in `MONGO_ALLOWED_DB_NAMES` (or `[mongo].allowed_databases`) | **Absent by default** |

Verified behavior (recorded at gate implementation time): `logistics_db` with `release_mode=False` → rejected with release-mode message; `logistics_db` with `release_mode=True` but not in allowed list → rejected by the allowed-list guard; only with both set does the guard pass. Development TEST identities (`logistics_workdesk_logc14`, `logistics_workdesk_LG01_E2E`) remain permitted without any change.

No credentials of any kind were written, committed, or generated during this workstream. The production config (`[mongo].uri` pointing at Atlas Cluster0, `[mongo].database = logistics_db`, `allowed_databases` including `logistics_db`, `release_mode = true`) is documented below for the Owner's manual application, never stored in the repository:

```toml
# Apply ONLY at Owner's manual cutover, after pre-release export:
[mongo]
uri = "<Atlas Cluster0 connection string>"
database = "logistics_db"
allowed_databases = ["logistics_workdesk_logc14", "logistics_workdesk_LG01_E2E", "logistics_db"]
release_mode = true
```

## 2. Cutover sequence (Owner executed, Section 26)

The cutover sequence is: (1) stop the running app; (2) run `docs/goals/LOG-LG02/tools/export_production.py` once to create the pre-release snapshot; (3) update `.streamlit/secrets.toml` per the config above; (4) start the app — the fail-closed guards verify environment identity at startup before any page logic runs, and with zero users in `logistics_db` the first-admin bootstrap form appears; (5) create the Owner's admin account (R9); (6) verify sanity checklist (Section 27). Rollback restores the pre-cutover secrets file and runs `restore_production.py` with the token after stopping the candidate.

## 3. Rollback contract record update

The rollback record (Section 17) is amended: production config **before** cutover is the Owner's current secrets file (TEST identity); **after** planned cutover it is the release-mode config above; on rollback the Owner restores the pre-cutover file, which re-arms the fail-closed guard automatically.

## 4. Verdict

**PROD_CONFIG_PREPARED = YES** — gate implemented default-OFF, dual-guard verified, no credential material enters the repository, cutover and rollback sequences documented.
