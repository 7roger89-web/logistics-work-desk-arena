# Changelog

## 3.1.1-core

### CLI configuration hotfix
- Added direct TOML loading for scripts started with `python scripts/...`.
- Removed dependency on `st.secrets` and Streamlit session context in bare CLI mode.
- Added compatibility with legacy flat keys: `MONGO_URI`, `MONGO_DB_NAME`, `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, and `GEMINI_KEYS`.
- Added compatibility with nested `[mongo]`, `[telegram]`, and `[gemini]` tables.
- Added multiple Gemini key fallback support.
- Added sanitized MongoDB connection diagnostics through `get_last_db_error()`.
- Added `scripts/check_config.py`.
- Added tests for both legacy and nested secrets formats.
- Added `SECRETS_MIGRATION.md` and mandatory credential-rotation guidance.

## 3.1.0-core

### Security
- Removed hard-coded MongoDB credentials.
- Added optional PBKDF2 authentication.
- Added HTML escaping for task content.

### Data integrity
- Added financial canonical calculation.
- Added validation pipeline, versioning, audit logs, soft delete and soft archive.
- Added unique indexes and data-quality tooling.
- Added idempotent FIFO payment allocation.

### Integrations
- Added Telegram outbox worker.
- Added Google GenAI structured HS output.
- Added MongoDB migration for local JSON modules.

### Fixes
- Fixed GNT DataFrame row iteration.
- Fixed GetFly export list/dict mismatch.
- Fixed GetFly imported status behavior.
- Fixed customer lookup by name in GNT.
- Added missing tracking configuration and routes.

### Additional hardening
- Fixed GNT float parsing that could multiply VND amounts.
- Added robust GetFly parsing for Vietnamese thousand separators.
- Added customer/contract audit trails and normalized contract identifiers.
- Added stale notification lock recovery.
- Added evidence requirement and human-review language for CBPG screening.
- Added customer soft-delete UI and safer fixed-row customer editing.

## 3.1.3 — Router hotfix

- Sửa trang trắng sau khi bấm menu do launcher import-star và Python module cache.
- Refactor giao diện chính thành hàm `main()` được gọi ở mọi Streamlit rerun.
- Thay `streamlit-option-menu` bằng điều hướng native `st.radio`.
- Lazy-import view và thêm error boundary để lỗi hiển thị trên trang.
- Thêm `scripts/check_router.py`.
