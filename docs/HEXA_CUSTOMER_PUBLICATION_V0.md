# HEXA Customer Publication V0 — backend-only sidecar

BASE=767eabd23aac1188770a857acaa1c645d3402e05
BRANCH=hexa/tt-lg-publication-v0-20261022
TASK=TT_TO_LG_READ_ONLY_PUBLICATION
STATUS=LOCAL_PROJECTION_ONLY; NOT_LIVE_API
OWNER_GATE=NO_MERGE | NO_PR211_UPDATE | NO_DEPLOY | NO_PRODUCTION_DATA

## Goal

Trường Thành xử lý toàn bộ nghiệp vụ và dữ liệu riêng (giá vốn, lịch sử giá, nhà cung cấp, Finance, bảng tính gốc) trong Logistics Work Desk. HEXA chỉ nhìn thấy một bản công bố hẹp của lô đã được TT duyệt: tiến độ có bằng chứng, chứng từ đúng phiên bản và tổng giá BÁN đã gửi khách.

V0 thực hiện bằng core/hexa_customer_publication.py, thuần Python, KHÔNG mở HTTP endpoint. Tài khoản Logistics role viewer hiện có finance_view, tuyệt đối không dùng làm tài khoản khách.

## Trusted inputs, never customer-controlled

- shipment: server-loaded source with shipment ID, customer_id and optionally quote_id.
- principal: external customer identity obtained from a VERIFIED SERVER AUTH SESSION, kind=customer and authenticated=true, with customer_id resolved by the server. It MUST NOT be built from a caller-provided customer_id or query/header.
- publication: TT-approved, SERVER-LOADED manifest for exact same shipment/customer. Requires state=PUBLISHED, approved_by, approved_at ISO string, event_versions (event_id -> version), document_versions (document_id -> version), and optional quote {id,version}. Any unapproved/missing manifest denies all.
- events, documents, quote: server-loaded records; each candidate is filtered by owner scope, explicit approval, actual validation and version.

No original supplier workbook, margin, internal cost, cost history, raw GridFS IDs, file URLs, raw shipment workflow, or private chat enters this payload.

## Key rules

1. Event must be verified=true with verified_at and visibility=CUSTOMER AND pinned version in manifest. Neither ETD nor a Journey done flag auto-publishes completion.
2. Document must belong to current customer/shipment, kind on explicit safe list, verified=true, status=AVAILABLE, visibility=CUSTOMER and released version match.
3. Before reading document bytes, the future server route must re-run authorize_document_download against the actual storage metadata and trusted session. The list response contains NO download URL or GridFS locator.
4. Quote uses the existing backend quote ID/status/calculation: linked to shipment, same customer, status SENT or ACCEPTED, version pinned. Publish ONLY the selling_price_total_vnd summary, not workbook/FX/cost or full quote object. Missing selling total stays null, not 0.
5. Unknown, unpublished or cross-customer references all raise the SAME PublicationDenied exception. Customer ID itself need not be exposed in JSON.
6. Status is NEVER inferred from upload, comment, customer checkmark or unsigned ETA.

## Evidence and limitations

19 isolated unit tests PASS against the exact core module, including wrong customer, guessed shipment, unpublished event, unverified ETA, stale document version, internal COST document, foreign document download, draft/wrong-version quote and internal sentinel leakage.

This is NOT an HTTP, GridFS, RBAC, browser, real-account or production test. No TT approval UI or manifest persistence implemented. The current internal schema is not asserted to have all these metadata fields; a separate trusted adapter is needed to resolve/store them before a real portal can consume this projection.

NEXT: pilot with two test customers and one shared-load shipment. Implement the smallest trusted adapter + nonproduction authenticated read-only GET and exact download authorization; test guessing a foreign shipment ID, wrong tenant, stale document version, and an unpublished TT ETA. Require Owner approval before live customer access.
