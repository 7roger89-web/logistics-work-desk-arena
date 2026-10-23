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

## Trial Pilot — Shared-Truck ROAD Connection (TT → Lục Giác, Isolated Sandbox)

- **Modules**:
  - `core/hexa_trial_portal.py`: Isolated trial adapter + server-side opaque session table + customer HTTP endpoints + customer-only HEXA V0 trial portal UI over `SANDBOX_STAGING` (`mongomock` + `mongomock.gridfs`), reusing `core/hexa_customer_publication.py`, `core/quotations.py`, `core/shipment_attachments.py` (`upload_attachment`, `fetch_attachment_bytes`), and `core/database.py`.
  - `scripts/run_hexa_trial_portal.py`: Standalone trial HTTP server runner (`0.0.0.0:8787`, `internal_qa_mode=False` by default).
  - `tests/test_hexa_trial_http_e2e.py`: End-to-end TCP HTTP + GridFS integration test suite (7 HTTP E2E tests on top of the 19 unit tests in `tests/test_hexa_customer_publication_v0.py`).
- **Trial Portal Security Boundary Hardening**:
  - **Tách biệt hoàn toàn dữ liệu kiểm tra nội bộ TT khỏi giao diện/API khách**: Giao diện khách (`GET /`, `GET /hexa`) chỉ hiển thị màn hình tra cứu công bố khách hàng (không chứa giá vốn, lợi nhuận, nhà cung cấp, ETA chưa xác minh hay thông tin khách cùng chuyến xe). Mọi truy cập từ Khách A, Khách B, `viewer` hoặc người ẩn danh tới `/api/hexa/v0/trial-inspector` hoặc `/internal/qa/inspector` đều bị chặn ngay phía server (`HTTP 403 CUSTOMER_RESOURCE_UNAVAILABLE`).
  - **Cấm token mẫu và cấm tự đổi phiên trên đường khách**: Các token mẫu dự đoán được (`sess-customer-lg`, `sess-customer-md`, `sess-internal-viewer`, `sess-anonymous`, mã khách) bị từ chối hoàn toàn. Phiên hợp lệ chỉ dùng token ngẫu nhiên sinh mỗi lần khởi tạo phía server (`secrets.token_urlsafe(24)`). `GET /` không tự cấp cookie phiên khách; `GET /api/hexa/v0/session` không trả danh sách `available_sessions` hay chuỗi token; `POST /api/hexa/v0/session` luôn bị từ chối `HTTP 403 CUSTOMER_RESOURCE_UNAVAILABLE`.
  - **Cơ chế đổi phiên/kiểm tra dành riêng cho QA nội bộ (cách ly khỏi đường truy cập khách)**: Mặc định tắt (`internal_qa_mode=False`). Khi bật tường minh cho harness kiểm thử nội bộ (`internal_qa_mode=True`), các route `/internal/qa/session` và `/internal/qa/inspector` nằm ngoài đường khách và bắt buộc phải có khóa nội bộ phía server `X-Hexa-Internal-QA-Key` (`env.internal_qa_key`); đây **chỉ là quyền của môi trường thử nghiệm nội bộ**, không bao giờ cấp cho khách hàng.
- **Simulated Shared-Truck Scenario (`TRIP-ROAD-2026-01`, xe `29H-886.68`)**:
  - **Khách A (Lục Giác — `CUST-LUCGIAC`, lô `ROAD-LG-001`)**:
    - Dữ liệu nội bộ TT giữ lại: giá vốn `42.000.000 VND`, lợi nhuận dự kiến `11.000.000 VND`, nhà cung cấp `Foshan Hexa Furniture Factory`, nhà xe `Nhà xe Việt Trung An Bình`, chứng từ giá vốn `DOC-LG-COST` (`kind=COST`), chứng từ cũ `DOC-LG-PL` (`v1`), và ETA chưa xác minh `2026-10-25`.
    - Dữ liệu công bố sang Lục Giác: 2 mốc tiến độ đã xác minh (`EVT-LG-02-BORDER@v2`, `EVT-LG-01-PICKUP@v1`), 2 chứng từ đúng phiên bản (`DOC-LG-PL@v2`, `DOC-LG-PI@v1`), và tổng báo giá bán đã gửi (`Q-LG-ROAD-001` `v3`, `status=SENT`, `selling_total_vnd=57240000.0`).
  - **Khách B cùng chuyến xe (Minh Đức — `CUST-MINHDUC`, lô `ROAD-MD-002`)**:
    - Có chứng từ riêng (`DOC-MD-PL@v1`) và báo giá riêng (`Q-MD-ROAD-002` `v3`, `selling_total_vnd=38880000.0`) trên cùng chuyến xe `29H-886.68`.
    - Mọi nỗ lực của Khách A đoán URL/mã lô của Khách B (`/api/hexa/v0/shipments/ROAD-MD-002`, `/api/hexa/v0/shipments/ROAD-LG-001/documents/DOC-MD-PL/download?version=v1`, hoặc giả mạo `?customer_id=CUST-MINHDUC` / header `X-Customer-Id`) đều bị chặn `HTTP 403 CUSTOMER_RESOURCE_UNAVAILABLE` với `0` lần đọc GridFS.

## Exact Missing Fields in Current Internal Schema (Acceptance Criterion #7)

Nguồn dữ liệu nội bộ hiện tại trong repo **chưa có sẵn** các trường bắt buộc sau của `core/hexa_customer_publication.py` (không được giả định hoặc chế vào DB thật):

1. **Danh tính phiên khách hàng (`principal`) — `core/users.py` & `core/auth.py`**:
   - Đã có: `user_id`, `username`, `role` (`admin` | `sale` | `support` | `viewer`), `active`.
   - **Thiếu**: `principal.kind == "customer"` và `principal.customer_id` gắn từ phiên xác thực phía server (lưu ý: `role="viewer"` nội bộ có quyền `finance_view`, tuyệt đối không dùng cho khách).
2. **Manifest duyệt công bố của TT (`publication`) — `core/database.py`**:
   - **Thiếu toàn bộ collection manifest công bố**: `state="PUBLISHED"`, `customer_id`, `shipment_id`, `approved_by`, `approved_at`, `event_versions: {event_id: version}`, `document_versions: {document_id: version}`, `quote: {id, version}`.
3. **Lô hàng ghép xe ROAD (`shipment`) — `core/database.py` & `views/logi_staging_seed.py`**:
   - Đã có: `id`, `customer_id` (1 khách/lô), `data["0.0"]["mode"]` (`"Truck"`), `data["1.2"]["eta"]`.
   - **Thiếu**: `transport_mode` chuẩn hoá ở top-level (`"ROAD"`), `quote_id` ở top-level trên bản ghi `shipments`, và khóa gom chuyến xe ghép (`trip_id`) tách khỏi `shipment_id` từng khách.
4. **Mốc tiến độ & xác minh ETA (`events`) — `core/shipment_journey.py`**:
   - Đã có: các node hiển thị suy diễn trực tiếp từ `data["1.2"]`, `data["2.4"]`, `data["2.7"]`.
   - **Thiếu**: `id` sự kiện công bố ổn định, `version`, `customer_id`, `verified` (`bool`), `verified_at` (ISO timestamp), `visibility` (`"CUSTOMER"` vs `"TT"`), `public_title`, `occurred_at`.
5. **Chứng từ đính kèm (`documents`) — `core/shipment_attachments.py` & `core/database.py`**:
   - Đã có: `id` (`ATT-...`), `shipment_id`, `storage_backend`, `storage_file_id`, `original_name`, `mime`, `category`, `status="AVAILABLE"`.
   - **Thiếu**: `customer_id`, `version` phát hành (`v1`, `v2`), `kind` thuộc `ALLOWED_DOCUMENT_KINDS` (`PL`, `PI`, `BOOKING`, `SI`, `BL`, `AWB`, `POD`, `CUSTOMS`, `CUSTOMER_INVOICE`, `CUSTOMER_CONTRACT`, `PAYMENT_REQUEST`), `visibility` (`"CUSTOMER"` vs `"TT"`), `verified` (`bool`), `public_title`.
6. **Báo giá (`quote`) — `core/quotations.py`**:
   - Đã có đầy đủ `id`, `version`, `customer_id`, `status` (`SENT`/`ACCEPTED`), `calculation.selling_price_total_vnd` (và `estimated_cost_vnd`, `estimated_margin_vnd` nội bộ).
   - **Thiếu**: trường liên kết `shipment.quote_id` trên lô hàng để đối chiếu 1-1 với `publication.quote.id`.

## End-to-End Trial Loop V1 — TT Approve/Revoke → Customer Login & Download (`HEXA-TT-LG-APPROVE-LOGIN-V1`)

- **Phạm vi**: Hoàn thiện 1 vòng nghiệp vụ khép kín trong môi trường thử nghiệm `SANDBOX_STAGING` (`mongomock` + `GridFS`; dữ liệu lưu trong tiến trình thử nghiệm, không tuyên bố bền vững qua khởi động lại tiến trình và không kết nối DB production).
- **1. Nhân sự Trường Thành duyệt & thu hồi công bố (`/api/hexa/v0/tt/*`)**:
  - Xác thực qua `POST /api/hexa/v0/tt/auth/login` bằng tài khoản nội bộ thử nghiệm `tt.ops.truongthanh` (kiểm tra băm PBKDF2-SHA256 qua `core.users.authenticate` / `core.auth.verify_password` và bắt buộc có quyền `operations_write` trong `core.auth.ROLE_PERMISSIONS`). Tài khoản `viewer` (`tt.viewer`) và tài khoản khách hàng đều bị từ chối `HTTP 403`.
  - Mở hồ sơ nội bộ lô `ROAD-LG-001` (`GET /api/hexa/v0/tt/shipments/ROAD-LG-001`), tích chọn các mốc tiến độ đã xác minh (`event_versions`), chứng từ kèm phiên bản (`document_versions`) và phiên bản báo giá bán (`quote`), rồi bấm **Công bố cho khách** (`POST /api/hexa/v0/tt/shipments/ROAD-LG-001/publish`).
  - Có thể thu hồi từng chứng từ/mục hoặc thu hồi toàn bộ công bố bất kỳ lúc nào (`POST /api/hexa/v0/tt/shipments/ROAD-LG-001/revoke`); hệ thống lưu vết kiểm toán tại `hexa_trial_publications` (`approved_by`, `approved_at`, `revoked_by`, `revoked_at`, `event_versions`, `document_versions`, `quote`, `history`).
- **2. Khách hàng Lục Giác & Minh Đức đăng nhập tài khoản thử nghiệm riêng (`/api/hexa/v0/auth/*`)**:
  - Đăng nhập qua `POST /api/hexa/v0/auth/login` kiểm tra PBKDF2-SHA256 trên server (`db["hexa_trial_customer_accounts"]`):
    - Khách A (Lục Giác): tài khoản `lucgiac.trial` → gắn cứng `customer_id="CUST-LUCGIAC"` vào phiên ngẫu nhiên phía server (`hexa_trial_session`).
    - Khách B (Minh Đức, đi ghép cùng xe): tài khoản `minhduc.trial` → gắn cứng `customer_id="CUST-MINHDUC"` vào phiên ngẫu nhiên phía server.
  - Mọi `customer_id` do client gửi kèm đều bị bỏ qua; tài khoản `viewer` của Logistics và mật khẩu sai đều bị chặn `HTTP 403`.
- **3. Hai màn hình rõ ràng cho Owner trên Live Preview (`GET /`, `GET /hexa`)**:
  - **Màn hình 1 — Nội bộ Trường Thành**: Đăng nhập TT → Chọn mục chia sẻ → Công bố cho khách → Thu hồi chứng từ / Thu hồi toàn bộ.
  - **Màn hình 2 — Cổng Khách hàng (Lục Giác / Minh Đức)**: Đăng nhập tài khoản khách riêng → Xem hành trình & báo giá bán → Tải chứng từ PDF đúng phiên bản (`DOC-LG-PL@v2`).
- **4. Chốt trạng thái công bố mặc định `UNPUBLISHED` / Default-Deny (`HEXA-TT-LG-V1-DEFAULT-DENY-CLOSURE`)**:
  - Khi khởi tạo môi trường thử nghiệm mới (`ensure_seeded`), cả Lục Giác (`ROAD-LG-001`) và Minh Đức (`ROAD-MD-002`) đều ở trạng thái chưa công bố (`hexa_trial_publications` rỗng / `UNPUBLISHED`), không có `approved_by` / `approved_at` giả trước khi nhân sự TT có thẩm quyền thao tác duyệt thực tế, và không có mốc tiến độ, chứng từ hay báo giá nào được chia sẻ sẵn.
  - Trước khi TT duyệt công bố, khách hàng đăng nhập gọi xem lô hoặc tải chứng từ đều bị chặn `HTTP 403 CUSTOMER_RESOURCE_UNAVAILABLE` với `0` lần đọc byte từ GridFS.
  - Các bài kiểm thử cần dữ liệu ở trạng thái `PUBLISHED` phải thiết lập bước đăng nhập TT + duyệt công bố tường minh trong fixture/test setup (tổng cộng `29 passed`: 19 unit tests + 10 HTTP E2E tests).
  - Các thông tin đăng nhập thử nghiệm (`tt.ops.truongthanh`, `lucgiac.trial`, `minhduc.trial`) chỉ phục vụ `SANDBOX_STAGING`, tuyệt đối không chuyển nguyên tài khoản/mật khẩu demo sang hệ thống thật.

## Customer Dashboard V1 — Map/Journey-First Dùng Chung Nền Tảng Logistics (`HEXA-CUSTOMER-DASHBOARD-V1`)

- **Tái sử dụng trực tiếp core hiện có (không copy source, không hardcode tên khách)**:
  - `core/shipment_dashboard.py` (`build_shipment_dashboard_view`): giải quyết đầu mối phụ trách (`owner` / `sale_owner`) và trạng thái lô.
  - `core/shipment_journey.py` (`build_journey`) + `core/shipment_execution_profile.py` (`build_execution_profile`) + `core/shipment_operations.py` (`compatibility_facts`, `transport_legs_for_read`): dựng khung các chặng hành trình (`pickup` → `road-ltl` → `road-border` → `customs-import` → `delivery`).
  - `core/hexa_customer_publication.py` (`build_customer_publication`, `authorize_document_download`): lọc fail-closed theo `principal["customer_id"]` của phiên server và manifest `PUBLISHED` do nhân sự TT duyệt.
- **Endpoint & Cấu trúc hiển thị (`GET /api/hexa/v0/dashboard`)**:
  - **Tổng quan (`summary`) — Chốt tính đúng nghiệp vụ (`HEXA-DASHBOARD-V1-TRUTH-CLOSURE`)**:
    - `active_tracking` (**Đang theo dõi**): số lô đã công bố chưa hoàn tất giao hàng.
    - `verified_warehouse_eta_count` / `arriving_soon` (**Có ETA kho đã xác minh**, `arriving_soon_label="Có ETA kho đã xác minh"`): **chỉ đếm lô có `verified_warehouse_eta` đã được TT xác minh và công bố**; tuyệt đối không tự suy từ chặng cửa khẩu (`road-border`) hay trạng thái Journey. Lô `ROAD-LG-001` có mốc cửa khẩu nhưng thiếu ETA kho đã xác minh phải có giá trị `0`.
    - `customer_action_needed` (**Cần khách xử lý**, `customer_action_status_label="Chưa có yêu cầu được xác nhận"` khi bằng `0` — `HEXA-DASHBOARD-CUSTOMER-ACTION-BOUNDARY`): **không suy diễn từ việc có chứng từ hay báo giá**, **không tính công việc của nhân viên Trường Thành (`tasks` nội bộ / `responsible_side != "CUSTOMER"`)**, và **không hiển thị `customer_actions` chưa được TT duyệt công bố riêng**. Vì V1 chưa có cơ chế duyệt công bố riêng cho yêu cầu khách xử lý trong manifest (`build_customer_publication` chỉ duyệt `event_versions`, `document_versions`, `quote`), hệ thống giữ chặt `customer_action=None`, `needs_customer_action=False`, KPI `customer_action_needed=0` và nhãn `"Chưa có yêu cầu được xác nhận"`; không xây thêm hệ thống task management.
    - `total_published`: tổng số lô đang được công bố của khách hàng hiện tại.
  - **An toàn hiển thị DOM (`HEXA-DASHBOARD-V1-TRUTH-CLOSURE`)**:
    - Toàn bộ dữ liệu động trên giao diện (`cargo_summary`, `route_summary`, `next_step`, `contact_point`, `shipment_id`, `verified_stage_label`, `verified_stage_title`, `last_updated_label`, `verified_warehouse_eta_label`, các node của `journey`, `timeline`, `documents`, `quote`) đều được dựng bằng `document.createElement` và gán qua `.textContent` (`0` lần sử dụng `.innerHTML` trong `core/hexa_trial_portal.py`), đảm bảo mọi chuỗi dạng HTML/script chỉ hiển thị như văn bản thuần.
  - **Mỗi lô đã công bố (`shipments[*]`)**:
    - `shipment_id`, `transport_mode`, `cargo_summary`, `route_summary`
    - `verified_stage_id`, `verified_stage_label`, `verified_stage_title` (chặng/vị trí được xác minh gần nhất)
    - `last_updated_at`, `last_updated_label` (thời điểm cập nhật xác minh)
    - `verified_warehouse_eta`, `verified_warehouse_eta_label` (chỉ hiện khi có mốc ETA kho được TT xác minh & duyệt công bố; khi thiếu xác minh như `ROAD-LG-001` thì giữ `None` / `"Chưa xác minh"`, tuyệt đối không lộ ETA nội bộ chưa xác minh `2026-10-25`)
    - `is_complete` (không mặc định hoàn thành khi chưa có sự kiện `delivery` đã xác minh & công bố)
    - `next_step` (việc tiếp theo) & `contact_point` (đầu mối CSKH/Sale TT)
    - `journey` (bản đồ các chặng Journey-first chỉ đánh dấu hoàn thành các chặng có sự kiện đã xác minh trong `timeline`), `documents` (đúng phiên bản được TT công bố), và `quote` (tổng giá bán đã gửi).
- **Chứng minh tái sử dụng cho 3 khách hàng thử nghiệm mà không sửa/copy source**:
  1. **Khách A (`CUST-LUCGIAC` — `lucgiac.trial`)**: lô `ROAD-LG-001` (đi ghép xe `29H-886.68`).
  2. **Khách B (`CUST-MINHDUC` — `minhduc.trial`)**: lô `ROAD-MD-002` (đi ghép cùng xe `29H-886.68` với Khách A).
  3. **Khách C (`CUST-ANPHAT` — `anphat.trial`)**: lô `ROAD-AP-003` (chuyến `15H-339.12`, kiểm chứng trường hợp có mốc `EVT-AP-02-CUSTOMS@v1` kèm `verified_warehouse_eta="2026-10-23"`).
- **Giới hạn môi trường thử nghiệm & những gì chưa sẵn sàng vận hành thực tế**:
  - Dữ liệu của 3 khách (`Lục Giác`, `Minh Đức`, `An Phát`) và nhân sự TT (`tt.ops.truongthanh`) là dữ liệu giả lập trong `SANDBOX_STAGING`.
  - Toàn bộ trạng thái lưu trong RAM (`mongomock` + `GridFS`); khởi động lại tiến trình sẽ quay về mặc định `UNPUBLISHED`.
  - Chưa nối MongoDB Atlas production, chưa tạo collection manifest/account khách trên DB thật, và `BROWSER_QA=NOT_RUN / BLOCKED` trong sandbox Arena (không có Chromium).

## 7. Đồng bộ Dashboard khách hàng với Journey Map đã duyệt (`HEXA-CUSTOMER-JOURNEY-UI-FIDELITY`)

- **Tái sử dụng UI (`REUSE_ACTUAL_COMPONENT=PARTIAL_CSS_ASSETS_AND_PORTED_JOURNEYMAP_DOM`)**:
  - Phục vụ trực tiếp file CSS biên dịch `component/dist/logi-shell.css` (`/assets/journey/logi-shell.css`) và 2 tài sản hải đồ thật `component/src/assets/journey/vietnam-east-sea-chart.webp` (`/assets/journey/vietnam-east-sea-chart.webp`), `component/src/assets/journey/chart-paper.jpg` (`/assets/journey/chart-paper.jpg`) mà không chỉnh sửa `component/src/*` hay `component/dist/*` của PR #211.
  - Vì `component/dist/logi-shell.js` chỉ export hàm mount toàn bộ `<App />` nội bộ (gồm sidebar nội bộ TT và các form nhập liệu nghiệp vụ TT), cổng khách hàng tái sử dụng nguyên trạng hệ class CSS `.journey-demo`, `.journey-toolbar`, `.journey-split.journey-map-first`, `.journey-canvas`, `.journey-sea-chart`, `.journey-edge`, `.journey-node`, `.journey-bubble`, `.journey-modal-layer`, `.journey-side.journey-modal-card`, `.journey-zoom-bar` và công thức tọa độ/đường cong Bézier (`JOURNEY_NODE_W=116`, `JOURNEY_NODE_H=66`, `PITCH=140`, `PX=42`, `journeyEdgePath`) của `JourneyMap.tsx` + `JourneyBubble.tsx` + `ShipmentJourney.tsx` trên lớp JS chỉ-đọc dành riêng cho khách.
- **Tách biệt tuyệt đối màn hình khách hàng (`GET /`, `GET /hexa`) và bàn duyệt nội bộ TT (`GET /tt`, `GET /tt/login`)**:
  - HTML khách hàng tuyệt đối không chứa: Màn hình 1 — Nội bộ Trường Thành, tab đổi vai trò, nút chọn nhanh Khách A/B/C hay mật khẩu mẫu, debug JSON / schema kỹ thuật / cảnh báo `HTTP 403`, hay công việc nội bộ/giá vốn/NCC/lợi nhuận của TT.
  - Bàn duyệt công bố dành cho nhân sự TT được tách sang `/tt` (kiểm quyền `_require_authorized_tt_staff` phía server trước khi trả HTML; khách hoặc người dùng ẩn danh truy cập `/tt` bị chặn `HTTP 403`).
- **Hành trình khách hàng Map-First & tính đúng của các công đoạn**:
  - Khách có 1 lô đã công bố (`ROAD-LG-001`) sẽ mở thẳng Journey Map làm màn hình chính; khi có nhiều lô mới hiện thanh danh sách lô gọn (`customer-shipment-selector`).
  - Bấm node mở `.journey-bubble` gắn theo node → bấm mục trong bubble mở popup chỉ-đọc (`.journey-modal-layer` / `.journey-side.journey-modal-card`) hiển thị trạng thái đã xác minh, thời điểm, nội dung công bố và bảng tải chứng từ PDF đúng phiên bản (không có form nhập liệu nội bộ TT).
  - **Không tự động đánh dấu hoàn thành công đoạn sau từ công đoạn trước**: đã xóa nhánh suy diễn `pickup` → `road-ltl`; sự kiện `pickup` (`Lấy hàng`) không tự đánh dấu `road-ltl` (`Nhận & ghép hàng (LTL)`) hoàn thành khi chưa có sự kiện `road-ltl` được xác minh & công bố.
  - Khi chưa đăng nhập: hiển thị màn đăng nhập gọn (`customer-login-screen`); khi lô chưa công bố hoặc đã thu hồi: hiển thị `"Trường Thành chưa công bố thông tin cho lô này"` trên nền hải đồ (`journey-zero-notice`).

## 8. Điều hướng hai tầng Dashboard nhiều lô → Journey Map từng lô (`HEXA-MULTI-SHIPMENT-DASHBOARD-NAVIGATION`)

- **3 trạng thái hiển thị theo số lô đã được TT công bố cho `customer_id` của phiên server**:
  1. **Khi khách chưa có lô công bố (`0` lô — ví dụ `anphat.trial`)**: hiển thị trạng thái trống thân thiện (`"Trường Thành chưa công bố thông tin cho lô này"`), ẩn bảng danh sách nhiều lô và ẩn nút quay lại.
  2. **Khi khách chỉ có `1` lô công bố (ví dụ `minhduc.trial` với `ROAD-MD-002`, hoặc Lục Giác khi chỉ công bố 1 lô)**: giữ nguyên hành vi vào thẳng hải đồ Journey Map của lô đó, ẩn danh sách nhiều lô và ẩn nút `"← Quay lại Dashboard"`.
  3. **Khi khách có từ `2` lô được công bố trở lên (ví dụ `lucgiac.trial` với 2 lô thuộc cùng `CUST-LUCGIAC`: `ROAD-LG-001` và `ROAD-LG-002`)**:
     - Mở **Dashboard tổng quan** (`#customer-shipment-selector`) làm màn hình đầu tiên; **ẩn hải đồ** (`#shipment-journey-view`) cho đến khi khách chọn một lô.
     - Danh sách hiển thị đầy đủ 6 thông tin cần thiết: **mã lô** (`shipment_id`), **hàng hóa & tuyến** (`cargo_summary`, `route_summary`), **phương thức vận chuyển** (`transport_mode`), **chặng xác minh** (`verified_stage_label`, `verified_stage_title`), **ETA được xác minh** (`verified_warehouse_eta_label`), **cập nhật cuối** (`last_updated_label`).
     - Desktop (`> 720px`) hiển thị bảng `.dash-table-desktop`; Mobile (`<= 720px`) tự động chuyển sang danh sách thẻ gọn `.dash-cards-mobile` (`#dash-shipments-cards`) không gây cuộn ngang.
     - Bấm dòng lô/thẻ lô hoặc nút **"Xem hành trình"** → ẩn Dashboard tổng quan, mở **Journey Map toàn màn hình** của lô đó kèm nút **"← Quay lại Dashboard"** (`#btn-back-to-dashboard`) trên thanh công cụ để quay lại danh sách tổng quan bất kỳ lúc nào.
     - Khi TT thu hồi công bố 1 lô (`POST /api/hexa/v0/tt/shipments/ROAD-LG-002/revoke`), lô đó biến mất ngay khỏi Dashboard của khách.
- **Khóa bảo mật token phiên khi chạy trong iframe**:
  - Đã gỡ bỏ hoàn toàn việc truyền `_hx_token` trên URL tải PDF và gỡ bỏ cơ chế đọc `_hx_token` từ query string trên server (`GET ...?_hx_token=...` trả `HTTP 403`) để tuyệt đối không làm lộ token phiên qua access log / lịch sử trình duyệt / Referer.
  - Việc gọi API và tải chứng từ PDF trong chế độ iframe chặn cookie dùng header `Authorization: Bearer <token>` trong `apiFetch()` kết hợp `res.blob()` + `URL.createObjectURL(blob)`.

## 9. Bổ sung Kế hoạch (`00`), Công nợ (`06` + Dashboard) và Trao đổi Chứng từ theo Công đoạn (`HEXA-JOURNEY-PLAN-FINANCE-COLLAB-V1`)

- **Hành trình 7 công đoạn (`00`..`06`) cho cổng khách hàng ROAD LTL**:
  - Giữ nguyên 5 công đoạn vận chuyển đang có (`01` `pickup` — Lấy hàng, `02` `road-ltl` — Nhận & ghép hàng (LTL), `03` `road-border` — Vận chuyển đường bộ & qua biên, `04` `customs-import` — Khai báo & thông quan, `05` `delivery` — Giao hàng), bổ sung 2 công đoạn thương mại/tài chính ở hai đầu mà không gộp bớt chặng vận chuyển và không làm sai lệch trạng thái các chặng `01`..`05`:
    - **Node `00` — `KẾ HOẠCH` (`plan`, trước Lấy hàng)**: hiển thị báo giá & tình trạng xác nhận báo giá (`quote_no`, `quote_confirmation_status`), hợp đồng & tình trạng ký kết (`contract_no`, `contract_status`), điều kiện thanh toán (`payment_terms`). Chỉ khi lô hàng thuộc diện **ủy thác nhập khẩu** (`entrusted_import=True`, ví dụ `ROAD-LG-002`) mới hiển thị điều kiện tiền hàng ứng trước (`goods_advance_required=200.000.000 VND`, `goods_advance_received=150.000.000 VND`, `goods_advance_remaining=50.000.000 VND`); các lô dịch vụ thông thường (`ROAD-LG-001`) không bị áp điều kiện tiền hàng ứng trước.
    - **Node `06` — `THANH TOÁN & ĐỐI SOÁT` (`finance-reconciliation`, sau Giao hàng)**: hiển thị tổng phải thanh toán đã đối soát, tổng đã thanh toán & phân bổ đúng lô, số dư còn phải thanh toán, ngày cập nhật, trạng thái đối soát, cùng trao đổi & chứng từ thanh toán liên quan. Việc giao hàng xong không tự động có nghĩa đã thanh toán đủ; khách thanh toán trước khi giao hàng vẫn ghi nhận đúng ngày thực tế.
- **Cột `"Công nợ"` trên Dashboard tổng quan (bảng Desktop & thẻ gọn Mobile)**:
  - Hiển thị 3 dòng cho mỗi lô: `Tổng phải thanh toán`, `Đã thanh toán`, `Còn phải thanh toán`.
  - Tái sử dụng trực tiếp `core/financial_ledger.py` (`derive_obligation_position`) trên các nghĩa vụ phải thu dịch vụ của khách với Trường Thành (`direction="RECEIVABLE_FROM_PARTY"`, `party_type="CUSTOMER"`, `purpose="LOGISTICS_SERVICE"`, `status="CONFIRMED"`). Tuyệt đối không dùng `shipment_partner_position()` (dành cho đối tác/NCC), không lấy tổng báo giá làm công nợ thực tế, và tách riêng khoản tiền hàng ủy thác (`purpose="ENTRUSTED_GOODS_ADVANCE"`).
  - Khi chưa có nghĩa vụ phải thu đã xác nhận hoặc chưa đối soát (như `ROAD-LG-002`), hiển thị rõ `UNKNOWN / Chưa đối soát` (không tự hiển thị `0 VND`).
  - **Ranh giới quyền hạn tài chính**: chỉ nhân sự nội bộ có quyền `finance_write` (ví dụ `tt.finance.truongthanh`, `role="support"`) mới được xác nhận bút toán thu tiền/phân bổ qua `POST /api/hexa/v0/tt/shipments/<id>/finance/confirm`; tài khoản chỉ có `operations_write` (`tt.ops.truongthanh`, `role="operations"`) bị chặn `HTTP 403`. Số liệu chỉ hiển thị cho khách khi lô được duyệt công bố và không bị thu hồi (`finance_revoked=False`).
- **Trao đổi (`TRAO ĐỔI`) & Đính kèm chứng từ (`CHỨNG TỪ`) theo từng công đoạn**:
  - Giữ nguyên bố cục `node → bubble → popup`. Bên trong popup mỗi công đoạn có 2 mục gọn:
    1. **TRAO ĐỔI**: danh sách ghi chú gắn với `(shipment_id, stage_id)`, người gửi, thời điểm; chỉ hiển thị các trao đổi `visibility="CUSTOMER"` đã công bố (ghi chú nội bộ `visibility="TT"` của Trường Thành tuyệt đối không hiển thị cho khách).
    2. **CHỨNG TỪ**: đính kèm, xem và tải tệp chứng từ công đoạn qua `core/shipment_attachments.py` + GridFS + kiểm tra loại tệp/dung lượng. Tệp khách tải lên (`source_side="CUSTOMER"`, `verified=False`, `"Hồ sơ khách đã nộp — Chờ TT xác minh"`) chỉ là hồ sơ khách nộp: không tự xác minh, không tự hoàn thành node, và không tự thay đổi số tiền đã thanh toán/còn phải thanh toán cho đến khi nhân sự có `finance_write` xác nhận và TT duyệt công bố. Khi TT thu hồi trao đổi hoặc chứng từ, khách không còn đọc hoặc tải được (`HTTP 403`, `0` lượt đọc GridFS).







