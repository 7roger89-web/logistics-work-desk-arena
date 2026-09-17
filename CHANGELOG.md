# Changelog

## LOGI_CUSTOMER_CREATE_TRUTHFULNESS_01 (+ tab/handoff repairs)

### P0-A — Customer create false success (transport failure)
- `/khach-hang` create (and edit) no longer closes the form, clears it, or claims "Đã gửi tạo khách hàng" when the event never crossed the bridge: TRANSPORT_FAILURE now keeps the modal open with the entered data and shows a red failure state.
- TRANSPORT_SUCCESS is no longer treated as persistence: the form waits for the authoritative backend outcome (`lastWrites`, matched by the `requestId` this click sent — the same correlated readback `shipment_create` / `customer_getfly_import` already use) and only closes on ok=True. Refusals (duplicate/RBAC/validation) keep the data and show the real backend error verbatim; the button is locked while the outcome is in flight (one click = one request).
- `views/logi_c1.py`: `customer_create` / `customer_edit` outcomes echo the click's `requestId` (the existing `_res` wrapper pattern; no new event, no second dispatcher, outcome shape backward compatible).
- Archive/import on the same page gained the same transport-failure guard (no success wording when nothing was sent).
- Focused evidence: `tests/component/dom_acceptance_customer_create.mjs` (real bundle in jsdom; transport-failure, duplicate refusal, success readback, double-send lock, adversarial unrelated-change) + `tests/test_logi_customer_create_truthfulness_01.py` (requestId echo on every path, outcome in next view-model, replay writes nothing) + `scripts/gen_customer_create_fixture.py`.

### P1-A — "XỬ LÝ NGAY" truncated tab
- The NextActionBanner's `nextRoute` parser used `/\w+/`, which cut the hyphenated tab id `lay-hang` to the non-existent tab `lay`, so the intended work section never appeared. Now `[\w-]+` (non-hyphenated tabs regression-checked).
- Evidence: `tests/component/dom_acceptance_next_action_handoff.mjs` STEP 1–2 (fails on the old bundle exactly at the truncation).

### P1-B — "MỞ CHỨNG TỪ" handoff
- From a linked contract on the shipment docs tab, the action now routes to the EXISTING contract document workdesk (`/hop-dong/<id>?tab=chung-tu` — HDNT/PL/HDMB generate/issue/download) instead of re-selecting the shipment's own PXK tab with a toast. No new document UI.
- `tests/component/fixtures/view_model_consolidation.json` regenerated with the current backend (the stale fixture predated the `_doc_card_view` `missing` normalization and crashed the contract docs tab).

### Known pre-existing (untouched, recorded)
- `tests/component/dom_acceptance_create_shipment.mjs` expects the old pending label ("ĐANG CHỜ BACKEND XÁC NHẬN…" vs the implementation's "ĐANG TẠO LÔ…") — stale expectation on main.
- `tests/component/dom_acceptance_handbook.mjs` / `dom_acceptance_user_access.mjs` crash on stale fixtures (predate current backend projections).
- 14 pytest failures on main baseline (see PR body) — identical before/after this change.

## LOGI_LOGIN_VISUAL_COMPACT_01

### Login UX
- Added a cinematic login hero: original vector scene (tiny dock worker pulling a tow line toward a gigantic container ship at dusk) at `assets/login_container_ship_hero.svg`, inlined into login CSS as a data URI — no CDN, no external image, no new runtime dependency.
- Compacted the login card to a small frosted panel (max-width 300px; `min(300px, 88vw)` on mobile) placed over the hero's negative space; the first-admin setup screen inherits the hero background.
- Auth semantics unchanged: same keys, `_authenticate`, session + rerun on success, generic error on failure, session revalidation, `ROLE_PERMISSIONS`, hashing and persistence untouched.
- Added focused regression `tests/test_login_visual_compact.py` (asset self-containment, compact scoped responsive CSS, scale-contrast geometry, auth behavior).

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
