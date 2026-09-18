# Changelog

## LOGI_SHIPMENT_DOCUMENTS_GRIDFS_RUNTIME_01

### GridFS attachment runtime (Issue #66)

- Keeps `shipment_attachments` as the canonical bounded metadata collection,
  but stores new attachment bytes in the existing MongoDB/PyMongo GridFS
  bucket `shipment_attachment_files` by default.
- Adds the smallest fail-closed selector: `ATTACHMENT_STORAGE_BACKEND=gridfs`
  (default) or explicit `drive_shared`; the Drive path remains Shared Drive
  only and is never a fallback.
- New metadata uses `storage_backend` + `storage_file_id`; the browser
  receives neither storage identity nor Mongo/provider implementation details.
  Legacy `drive_file_id` rows remain readable when their existence cannot be
  disproven.
- Preserves validation, original-byte SHA dedupe, image policy, RBAC,
  server-proxied download, fresh readback, and exactly-one compensation with
  explicit orphan-risk reporting.
- Focused evidence uses isolated fake/mongomock/GridFS storage only;
  `PRODUCTION_MUTATIONS=0`, `PILOT_MUTATIONS=0`, `NEW_PROVIDER_DEPENDENCIES=0`.

## LOGI_SHIPMENT_DOCUMENTS_DRIVE_REINTEGRATE_02

### Shipment attachments reintegrated (Google Drive bytes, MongoDB metadata)

- ONE vertical slice on the CURRENT shipment "Chứng từ" tab (donor PR #49 used
  as reference only, never merged): real document/photo upload → bounded server
  validation → real image optimization → Google Drive upload → metadata
  persistence → authoritative readback, with server-authoritative download.
- Binary authority: Google Drive owns the bytes; MongoDB stores bounded metadata
  only. `core.database.save_shipment_attachment` REFUSES any document carrying
  bytes/base64 values (`RAW_BINARY_IN_MONGO=NO`).
- NEW `core/drive_client.py`: the smallest Drive adapter — service account via
  `google-auth` on top of the EXISTING `requests`, talking to Drive REST v3
  directly (no `google-api-python-client`). Folders, upload, metadata, download
  and the ONE bounded compensating delete. No public links, no browser OAuth,
  no credential in the payload. Missing config fails closed as
  `DRIVE_NOT_CONFIGURED`. `SERVICE_ACCOUNT_STORAGE_MODE=SHARED_DRIVE_ONLY`:
  the root folder must be a writable folder inside a Google Workspace Shared
  Drive (service account needs write permission there); a normal My Drive
  folder shared with the service account is unsupported, and without an
  available Shared Drive `LIVE_DRIVE_VERIFICATION=BLOCKED`. OAuth-on-behalf-of-user
  is a separate future decision, not part of this PR.
- NEW `core/shipment_attachments.py`: 20 MB ceiling, extension + MIME +
  magic-byte validation, same-shipment SHA-256 duplicate guard, Pillow JPEG/PNG
  optimization kept ONLY when ≥5% smaller (PDF/DOCX/XLSX stay byte-identical),
  and the validate → Drive → Mongo order with exactly-one compensation and
  explicit `orphanRisk` evidence.
- Two bounded events in the ONE dispatcher: `shipment_attachment_upload`
  (EXISTING `sales_write` boundary via `can_generate_documents`) and
  `attachment_download` (EXISTING `dashboard` read boundary). No delete event,
  no queue, no worker, no new RBAC role. Viewer may download but may not upload.
- UI: "Tệp đính kèm lô hàng" section in ShipmentDetail rendering the backend
  projection, honest `original → stored` sizes, "Ảnh đã tối ưu"/"Giữ nguyên",
  real pending state and honest refusals; `component/dist` rebuilt from the
  current source tree (never copied from the donor).
- Evidence: `tests/test_logi_shipment_documents_drive_02.py` (45 focused
  tests, fake Drive only, `LIVE_DRIVE_MUTATIONS=0`) and
  `tests/component/dom_acceptance_shipment_attachments.mjs` (12 checks on the
  real rebuilt bundle).

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
