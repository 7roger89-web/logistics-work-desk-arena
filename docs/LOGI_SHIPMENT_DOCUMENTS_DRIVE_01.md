# LOGI_SHIPMENT_DOCUMENTS_DRIVE_01 — real shipment attachments (Google Drive bytes, Mongo metadata)

ONE production-shaped vertical slice:

    shipment attachment upload → safe preprocessing → Google Drive adapter →
    metadata persistence → shipment document UI/readback

**Not** a DMS platform, **not** a queue/worker/file microservice, **not** an
S3/cloud-storage abstraction, **not** a new API server. One adapter, one
metadata collection, one uploadable surface, one bounded pair of events.

## Decision gate

`EXISTING_ATTACHMENT_MODEL = NONE (checklist of derived facts only)`

| Surface audited | Finding |
| --- | --- |
| `ShipmentDetail` tab `chung-tu` (component/src/pages/ShipmentDetail.tsx) | Derived checklist ("Chứng từ lô hàng — hiện trạng & bổ sung") + PXK block. No attachment object, no writer, no bytes. |
| `views/logi_real_data.document_checklist()` | Four rows derived from shipment facts (`tk_no`, customs status, delivery plate, delivered flag). Not attachments. |
| `docgen_documents` (`core.database.load_docgen_documents` / `save_docgen_document`) | Real metadata-only precedent for generated Office documents. No binary, immutable content fields. |
| PXK/GNT bytes | Session-scoped store (`views/logi_c1.store_output`) projected as base64 for download; bytes are never persisted. |
| GetFly DSDH import | Browser→Python bounded base64 transport precedent (`getfly_preview`) with server-side decode. |
| Google Drive | **No integration of any kind existed** (`requirements.txt` had no Drive/google-auth dependency, no adapter, no credential convention). |
| Reference repo `7roger89-web/logistics-work-desk` | Not reachable from this session (authenticated 404) — nothing to reuse, nothing claimed. |

So this slice creates the attachment model it needs, reusing the EXISTING
dispatcher, RBAC matrix, audit writer, `_save_document` writer family and the
EXISTING bounded-base64 transport pattern.

## Binary authority

`Google Drive = BYTES` · `MongoDB = bounded METADATA`.

- `core/database.save_shipment_attachment()` is the boundary: it REFUSES any
  document carrying `bytes` / `data` / `base64` / `content` / `blob` keys, any
  binary value, and any missing identity field.
- Stored metadata: `id`, `shipment_id`, `original_name`, `stored_name`, `mime`,
  `category`, `original_size`, `stored_size`, `sha256`, `drive_file_id`,
  `drive_folder_id`, `uploaded_at`, `uploaded_by`, `compression_mode`,
  `compression_note`, `status` + the standard audit stamps from `_save_document`.
- `RAW_BINARY_IN_MONGO = NO`, `BASE64_IN_MONGO = NO` — asserted twice (writer
  guard test + a test that reads the raw collection document back and checks
  every value).
- Credentials are never persisted anywhere: nothing in the record identifies the
  service account.

## Google Drive auth model

    Google Service Account (deployment secrets/env)
      + ONE Owner-controlled Drive folder shared with that service account

- `GOOGLE_DRIVE_ROOT_FOLDER_ID` — the shared folder's id.
- `GOOGLE_SERVICE_ACCOUNT_JSON` — the service-account JSON (JSON string, or a
  `[google_drive]` TOML table). Read through the EXISTING `core.config` chain
  (env → `st.secrets` → `.streamlit/secrets.toml`) via the new
  `core.config.get_raw_setting()` (raw, non-stringified, so a JSON/table value
  cannot be corrupted).
- Not implemented, on purpose: browser OAuth, per-user Google login, public
  links, credential in React, credential in Mongo, credential in logs, asking
  the Owner to paste a secret into chat.
- Unconfigured deployment = honest refusal
  (`gate=DRIVE_NOT_CONFIGURED`, naming the missing setting), zero Drive calls,
  zero Mongo writes. The UI shows the same state.

`DRIVE_CLIENT_PATH = google-auth (AuthorizedSession) + existing requests → Drive REST v3`

- Chosen over `google-api-python-client`: the SDK adds a large dependency tree
  for four endpoints, while `requests` and the service-account auth helper
  already cover exactly what this slice does.
- `NEW_DEPENDENCIES = google-auth, Pillow` (see §Dependencies).
- Operations implemented (`core/drive_client.GoogleDriveClient`): `ensure_folder`
  (find-or-create, memoised per instance), `upload_file` (multipart/related,
  exact bytes), `file_metadata`, `download_file` (`alt=media`), `delete_file`
  (used ONLY by the compensation path). No delete surface is exposed to the UI,
  no sync daemon, no folder migration, no watcher.
- Folder/file names go through ONE sanitizer (`sanitize_drive_name` /
  `is_unsafe_drive_name`): path separators, control characters, `.`/`..` and
  over-long names are refused rather than guessed at.

`DRIVE_VISIBILITY_MODEL = RESTRICTED_SERVICE_ACCOUNT_UPLOAD + SERVER_PROXIED_DOWNLOAD`

- Files are uploaded into the Owner-controlled folder; the app never calls
  `permissions.create`, never sets `anyoneWithLink`, never makes a file public.
- No Drive URL is rendered. Opening an attachment is ONE `attachment_download`
  event; the server reads the bytes and hands them to the browser, so no Drive
  file id, folder id, bearer token or signed URL ever enters DOM/state.
- The Drive ids stay backend metadata for repair/ops.

### Folder structure

    <ROOT_FOLDER_ID>/
      shipments/
        <shipment-id>/          (sanitized)
          attachments/

Category is metadata (`category`), not a folder tree: no decorative folders.
Each level is resolved at most once per upload (three find-or-create calls).

## Files, limits, compression

`MAX_UPLOAD_BYTES = 20 MB` (enforced on the declared size, on the base64 body
length BEFORE decoding, and on the decoded bytes). Oversize ⇒ honest refusal,
no Drive call, no Mongo metadata.

`ALLOWED_FILE_TYPES = pdf, jpg, jpeg, png, doc, docx, xls, xlsx`
(extension allowlist + MIME allowlist + magic-byte sanity: `%PDF-`, JPEG SOI,
PNG signature, `PK\x03\x04` (docx/xlsx), OLE header (doc/xls)). Executables,
scripts, HTML/SVG and unknown content are refused.

| Input | Policy |
| --- | --- |
| JPEG/PNG | Pillow: EXIF orientation applied, no upscaling, longest edge capped at 2200 px, JPEG q82, `optimize=True`; the optimized bytes are kept ONLY when at least 5 % smaller. |
| PDF | kept byte-identical (no Ghostscript, no system daemon) |
| DOC/DOCX/XLS/XLSX | kept byte-identical |
| Optimizer failure | upload proceeds with the ORIGINAL bytes (`KEPT_ORIGINAL`), never blocked |

`COMPRESSION_POLICY = REAL_REDUCTION_OR_NOTHING`
`IMAGE_COMPRESSION = PILLOW_OPTIMIZE_WHEN_MATERIALLY_SMALLER`
`PDF_COMPRESSION = NONE (byte-identical)`
`OFFICE_COMPRESSION = NONE (byte-identical)`

Original-file safety: `sha256` is computed from the ORIGINAL upload; the
original filename is preserved; `original_size` / `stored_size` /
`compression_mode` record exactly what happened, and the UI only claims
"Ảnh đã tối ưu" for a real reduction ("Giữ nguyên" otherwise).

## Duplicate guard

`sha256` of the original bytes, scoped to the SAME shipment:
a duplicate returns the EXISTING attachment (`gate=DUPLICATE`, message
"không tải lên bản sao") with zero Drive calls. Durable half of the guard:
a unique compound index on `(shipment_id, sha256)`. Cross-shipment dedupe is
explicitly out of scope.

## Events, RBAC, ordering

`UPLOAD_EVENT = shipment_attachment_upload` (bounded payload:
`shipmentId, category, fileName, mime, size, base64, requestId`)
`DOWNLOAD_EVENT = attachment_download` (bounded payload:
`shipmentId, attachmentId, requestId`) — no delete event exists.

Server ownership: permission → size/type validation → decode → SHA-256 →
duplicate guard → compression → Drive auth → Drive upload → metadata write →
fresh readback. The browser's role is a picker and a renderer.

`SERVER_RBAC`: upload = EXISTING `core.auth.can_generate_documents()`
(`sales_write`, the same boundary document generation already uses);
download = EXISTING `can_operate_business("dashboard")`, so every role that may
read a shipment may open its files. No new `ROLE_PERMISSIONS` entry was added.
Unauthorized ⇒ refused before decode, zero Drive calls (asserted).

Ordering and failure policy:

    validate → hash → (duplicate?) → Drive upload → Mongo metadata
    Drive fails                  ⇒ no Mongo attachment (nothing to compensate)
    Mongo write fails            ⇒ ONE compensating delete of the exact file id
                                   just created; if that cannot be proven,
                                   result says orphan_risk=true and logs
                                   non-secret evidence (shipment id, file id,
                                   name, size) for repair

No transaction coordinator, no cleanup daemon, no retry worker.

## UI

`ShipmentDetail → tab "Chứng từ & PXK" → section "TỆP ĐÍNH KÈM"`:
category picker, file picker (accept-list from the server policy), one upload
button with a real pending state, the backend's own outcome text, and the
attachment list (name, category, honest size `original → stored`,
"Ảnh đã tối ưu"/"Giữ nguyên", upload date, uploader, TẢI). The list always comes
from the backend projection — `lastWrites` only carries the outcome, never the
canonical rows. A viewer sees the read-only note instead of the form (server
refuses regardless). Nothing in the DOM exposes a Drive id, folder id, public
link, credential or the raw SHA-256.

## Evidence

Backend (`tests/test_logi_shipment_documents_drive.py`, staging mongomock +
deterministic fake Drive — never the Owner's account/folder):

- provider contract: three folder levels resolved/created once; upload receives
  the EXACT post-processing bytes and MIME/name; returned `drive_file_id`
  persisted; no binary/base64 in Mongo; duplicate SHA refuses the second upload
  and performs zero Drive calls; Drive failure ⇒ no Mongo attachment; metadata
  failure ⇒ exactly ONE compensating delete; unprovable cleanup ⇒
  `orphanRisk` + warning log without secrets; unauthorized/oversized/unknown
  shipment/lying declared size ⇒ ZERO Drive calls;
- Drive REST adapter itself (stub session): folder query + create, multipart
  `multipart/related` body byte-for-byte, `alt=media` download, bounded delete,
  HTTP failure → credential-free `DriveError`;
- compression: large photo materially smaller (and still decodable, capped, never
  upscaled), EXIF orientation applied, PNG path, PDF/DOCX/XLSX byte-identical,
  corrupt-image fallback keeps the original and still uploads;
- writer guard: binary/base64 payloads refused, immutability, audit row;
- projection/policy: no Drive id, no SHA, no credential; `allowUpload` reflects
  the server session role; every shipment row always carries `attachments`.

Commands:

```
.venv/bin/python -m pytest tests/test_logi_shipment_documents_drive.py -q      # 44 passed
.venv/bin/python scripts/gen_shipment_attachments_fixture.py                    # real staging fixture
cd component && npm run typecheck && npm run build                              # 944.47 kB / 63.36 kB
python3 scripts/scan_process.py component/dist                                  # FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0
node tests/component/dom_acceptance_shipment_attachments.mjs                    # PASSED checks=11
```

DOM acceptance (real bundle in jsdom, 11 checks): section visible in the
`chung-tu` tab; list rendered from the backend projection with honest sizes and
compression labels; selectors mirror the server policy; ONE
`shipment_attachment_upload` event with the bounded payload + visible pending
state; fresh readback replaces the pending state and shows the new attachment;
duplicate and Drive-not-configured refusals displayed honestly; viewer gets no
upload control but keeps download; no Drive id/URL/credential/SHA in the DOM;
ONE `attachment_download` event whose bytes are saved locally; no forced
horizontal overflow and thumb-sized controls.

Full suite: `14 failed, 1001 passed, 44 skipped, 1 error` — the failure set is
IDENTICAL to `main c53ef4f` (958 passed there), i.e. this slice adds 43 passing
tests and no new failure. The DOM harness has four pre-existing failures on
main's own build (`dom_acceptance_handbook`, `dom_acceptance_consolidation`,
`dom_acceptance_create_shipment`, `dom_acceptance_user_access`); every other DOM
suite passes, including the new one.

## Adversarial check (one, decision-useful)

Mutation: `record["bytes"] = data` added to the upload path so raw upload bytes
would be written into MongoDB metadata. Result: the focused guard failed as
required — `TestProviderContract::test_no_binary_or_base64_is_ever_persisted`
and `test_upload_creates_three_folder_levels_once_and_persists_metadata` failed
(the writer refused the document, so the compensation path ran),
`10 failed, 33 passed`. Mutation reverted; `44 passed` again.

## Data safety

`PRODUCTION_MUTATIONS = 0` · `PILOT_MUTATIONS = 0` · `LIVE_DRIVE_MUTATIONS = 0`
· `SECRETS_CHANGED = NO`. Tests run on isolated mongomock staging plus a fake
Drive adapter; the fixture generator uses the same fake adapter.

`MALWARE_SCANNING = NOT_AVAILABLE` — allowlist + magic-byte validation only, no
ClamAV daemon, and the feature never claims a file is malware-free.

`LIVE_DRIVE_VERIFICATION = OWNER_RUNTIME_REQUIRED` — this environment has no
deployed Drive credential, and no live Drive write was attempted or needed.

## Owner runtime runbook (the only remaining step)

1. Create (or choose) ONE folder in the Owner's Drive to hold shipment files.
2. Create a Google Cloud service account, download its JSON key, share the
   folder with the service account's `client_email` (Editor).
3. Put the two values in the deployment's own secrets — never in chat, never in
   git: `.streamlit/secrets.toml → [google_drive] root_folder_id`,
   `service_account_json` (or the env vars
   `GOOGLE_DRIVE_ROOT_FOLDER_ID` / `GOOGLE_SERVICE_ACCOUNT_JSON`).
4. Restart the app; the shipment tab then uploads into
   `<ROOT>/shipments/<shipment-id>/attachments/` and the same screen lists and
   re-opens the file.

If a step fails, the app says exactly which setting is missing — it never fakes
a successful upload.
