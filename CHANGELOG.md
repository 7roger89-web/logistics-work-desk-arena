# Changelog

## LOGI_TRADE_DOCUMENT_SHIPMENT_REVIEW_RUN3_01

### Reconciled against current main — My Drive OAuth backend (PR #133)

- Rebased the Run 3 work onto `main` at `185e6ee`, which merged PR #133's
  **My Drive OAuth** attachment backend. Current main offers three storage
  backends (`gridfs`, `drive_shared`, `drive_oauth`); Run 3 now proves itself
  against all of them rather than against the pre-PR133 reader.
- The one material overlap was `core/shipment_attachments.py`. Main's change
  added `STORAGE_BACKEND_DRIVE_OAUTH`, `DRIVE_STORAGE_BACKENDS`,
  `_drive_auth_mode()`, the auth-mode-aware `build_drive_client(...)` /
  `load_drive_settings(...)` calls and the drive_oauth branches inside
  `fetch_attachment_bytes(...)`. Run 3's change was confined to
  `project_attachment()` (`reviewSelectable` / `reviewNote`). The two touch
  disjoint functions, so **both lanes are preserved verbatim** — no drive_oauth
  line was reverted and no review field was lost.
- **The storage reader was NOT forked.** The review still reaches bytes only
  through `core.shipment_attachments.fetch_attachment_bytes(...)`, which now
  selects the user-OAuth credential family for `drive_oauth` by itself. There
  is no `fetch_review_attachment_bytes`, no second Drive or OAuth reader and no
  second attachment abstraction.
- Added `TestReconcileDriveOAuth` (9 tests) as the current-main integration
  proof on test seams only — no real Google credential and no Drive integration
  framework. The real `_drive_auth_mode` → `load_drive_settings` →
  `build_drive_client` chain executes; only the HTTP client class and the
  settings source are stubbed. It explicitly covers all three storage backends (`gridfs`, `drive_shared`,
  `drive_oauth`) through the one reader, and proves: dashboard RBAC still applies on the
  OAuth backend; ownership is proven before any byte read; the drive_oauth byte
  path is reusable by the review (`auth_mode=user_oauth`, 3 reads, full canary
  19 facts unchanged); zero writes and zero Drive deletes; no OAuth client id,
  client secret, refresh token, Drive file id or raw SHA-256 reaches the
  browser; and no provider/OCR fallback is reached from that path.
- Regression at the reconciled HEAD: Run 3 backend 49 passed; targeted 11-file
  set 208 passed (includes PR #133's own Drive suite, untouched); Run 3 DOM
  `PASSED checks=17`; attachments DOM `PASSED checks=13`; TypeScript typecheck
  clean; Vite build clean; executable-reference scan 0. Full suite 1541 passed
  / 24 failed against a current-main baseline of 1492 passed / 24 failed — the
  delta is exactly the 49 new tests and the failure lists are byte-identical.

### Read-only trade-document review on existing shipment attachments (Issue #132)

- Connects the two capabilities already on `main` to the EXISTING shipment
  **Chứng từ / Tệp đính kèm** surface: the operator selects existing PDF/XLSX
  attachments and presses **KIỂM TRA CHỨNG TỪ** to get an honest read-only
  review. No re-upload, no local download+upload loop, no business-field write,
  no automatic winner, no OCR/provider fallback.
- Reuses every authoritative seam instead of rebuilding one:
  `core.shipment_attachments.fetch_attachment_bytes` (server-side byte read
  with shipment ownership proven first), `core.located_text_reader.
  read_document_text` (Run 2 located text), `LocatedTextDocument.
  to_document_artifact`, and `core.trade_document_crosscheck.
  run_trade_document_crosscheck` (Run 1, 19 canonical facts, unchanged).
- ONE typed READ-ONLY event, `shipment_document_review`, deliberately NOT in
  `PHASE_B_EVENTS`. The browser payload carries only
  `{ shipmentId, attachmentIds, requestId }` — never bytes, base64, storage /
  GridFS / Drive ids, a raw SHA or a credential. Read RBAC is the existing
  `can_operate_business("dashboard")` boundary, so a role that may see the lot
  may inspect its documents without `sales_write`.
- Server order is enforced so every request-level refusal costs
  `STORAGE_BYTE_READS=0`: shape → RBAC → fresh shipment existence → 1..6 unique
  ids → canonical metadata → per-attachment ownership proof → supported
  extension → per-file + aggregate byte budgets → only then sequential byte
  reads → Run 2 → Run 1 → bounded projection.
- Bounds: `MAX_REVIEW_FILES = 6`, `MAX_REVIEW_TOTAL_BYTES = 30 MB`, plus the
  unchanged Run 2 `TextReaderLimits.max_file_bytes` (10 MB) per file. Documents
  are read SEQUENTIALLY; Run 2 limits and the attachment upload limit are
  untouched.
- Five honest document states — `READABLE`, `NEEDS_OCR_NOT_RUN`,
  `UNSUPPORTED_FORMAT`, `TOO_LARGE_FOR_REVIEW`, `READ_FAILED`. Unreadable files
  stay visible with their state, contribute ZERO fabricated trade facts, and a
  corrupt file never fails the whole request (per-document containment after the
  security/identity preflight). JPG/JPEG/PNG show
  *"Cần OCR — bước này chưa chạy OCR"*; DOC/DOCX/XLS show *"Chưa hỗ trợ kiểm
  tra tự động ở bước này"* — never implying the file is damaged.
- Partial-review honesty: 1 readable document is reviewed as incomplete, 2
  compare only the available evidence, 3+ use the existing Run 1 independence
  rules, and duplicate copies of ONE document type never become independent
  confirmation. ZERO readable documents returns document states only, with no
  fabricated cross-check.
- Vietnamese operator surface: count chips (Lệch / Chưa xác định / Thiếu / Chỉ
  một nguồn / Khớp), then **CẦN XEM** (CONFLICT → UNKNOWN → MISSING), then
  **THAM KHẢO** (SINGLE_SOURCE), then **ĐÃ KHỚP** (SAME), with Vietnamese labels
  for all 19 canonical field keys (canonical keys kept in code). A CONFLICT
  shows EVERY source side with page OR sheet/cell provenance and states
  *"Chưa chọn giá trị đúng — cần người kiểm tra."* No score, percentage or
  quality metric is invented.
- Session-only result in ONE bounded Streamlit slot
  (`SHIPMENT_DOCUMENT_REVIEW_KEY`). A new review replaces the previous one;
  nothing is persisted to shipments, `shipment_attachments`, audit, GridFS,
  Drive or any review collection. The stored review carries its own
  `shipmentId`, so a review belonging to another lot can never project into the
  current one. `requestId` correlation means only the matching outcome settles
  the pending UI, and the pending button blocks a double submit.
- Privacy projection: no PDF/XLSX bytes, no base64, no storage/GridFS/Drive id,
  no raw SHA-256, no full extracted text, and never the whole
  `LocatedTextDocument` — only bounded per-fact evidence, document states and
  status counts. The UI always states
  *"Kết quả chỉ để kiểm tra — chưa ghi vào hồ sơ lô hàng."*
- Hard read-only acceptance proven by test: `DB_WRITES=0`, `AUDIT_WRITES=0`,
  `ATTACHMENT_WRITES=0`, `SHIPMENT_WRITES=0`, `NETWORK_PROVIDER_CALLS=0`,
  `OCR_CALLS=0`; storage byte reads only for selected, ownership-proven files.
- Synthetic end-to-end canary over the real Run 2 fixtures
  (`commercial_invoice.xlsx`, `packing_list.xlsx`, `bill_of_lading.pdf`)
  uploaded as real attachments onto the app's own GridFS store:
  metadata → server-side byte read → Run 2 → Run 1 → Run 3 projection → React
  UI, giving `TOTAL FACTS=19` with `SAME=7 CONFLICT=1 MISSING=2 UNKNOWN=1
  SINGLE_SOURCE=8` and 3/3 classification.
- Regression preserved: attachment upload, attachment download, GridFS /
  `drive_shared` ownership checks, Run 1, Run 2, the shipment view-model and the
  existing document tab. No delete event, no new storage.

## LOGI_LOGIN_RESPONSIVE_BACKGROUND_FIT_01

### Login artwork fits portrait / tall viewports (no more cropped background)

- One geometry-based rule added to the login CSS:
  `@media (orientation: portrait)` switches
  `[data-testid="stAppViewContainer"]` from `background-size: cover` to
  `contain` (with `no-repeat`, `background-position: center 85%` and the
  existing neutral `#071019`), so the whole 16:9 artwork stays visible and
  undistorted on phone portrait, tablet portrait, and a phone in
  "Desktop site" mode (whose CSS width stays above the 768px breakpoint, so
  the old width-only rule never matched it).
- Orientation/aspect geometry only — no device names, no user-agent sniffing,
  no JS, no responsive framework, no new artwork assets.
- Landscape / laptop / desktop keep `cover` (unchanged).
- One portrait-specific login-card offset (`margin-top: 6vh`) keeps the
  transparent card clear of the artwork band; the card stays transparent and
  no dark veil, blur or gradient is reintroduced.
- Rotation, authentication flow, database and secrets are untouched.

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
