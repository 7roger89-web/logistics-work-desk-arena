# Journey Map → trao đổi / chứng từ đúng lô, đúng công đoạn

Session: `LOGI-JOURNEY-NODE-DISCUSSION` — nhánh `arena/d46744d8-logistics-work-desk-arena`.
Ngày đo: 2026-10-30.

## 0. Trạng thái đo được trước khi sửa

| Mục | Giá trị đo |
|---|---|
| Nhánh gốc khi nhận việc | `arena/d46744d8-logistics-work-desk-arena` @ `9e4190b278dd2ced8771c5249582753d34e561db` (`main`) |
| Staging tham chiếu | `arena/ae5f9f47-logistics-work-desk-arena` @ `7ac441b23407a6f337d08cf923cbda28c8c7f197` (**có thật**, commit “PR234 merged staging”) |
| Vì sao base khác | `main` không chứa `views/journey_discussion.py`, `core/journey_notes.py`, `assets/customer_portal/hexa-portal.js`. Nhánh làm việc được fast-forward lên `7ac441b` (827 commit) để mục tiêu có code thật; **không** sửa `main`. |
| Full suite baseline (đo tại `7ac441b`, có `component/node_modules`) | **35 failed / 2196 passed / 44 skipped / 0 error** |
| `tests/test_journey_notes.py` baseline | 48 passed |
| Môi trường | Python 3.11.2, streamlit 1.66.1, pytest 9.2.0, mongomock, node 22.22.3 (jsdom 30) |

## 1. Cơ chế component ↔ Streamlit đã kiểm tra trước khi sửa

* Cổng khách (`assets/customer_portal/hexa-portal.js` + `views/customer_portal_component.py`) là
  **một chiều**: `st.components.v2.component(..., html/css/js)` nhận `component.data` và **không**
  gọi `setTriggerValue` ở bất kỳ đâu. Vì vậy `selectJourneyNode()` chỉ đổi state cục bộ; pane
  Streamlit bên dưới **không biết** node/lô nào đang được chọn.
* Shell nội bộ (`component/dist/logi-shell.js`, `views/logi_shell.py`) đã có sẵn transport hai
  chiều `setTriggerValue` → `on_<event>_change` → `views.logi_view_model.dispatch` (callback
  prefix + post-mount fallback, chống dispatch đôi bằng `_logi_callback_dispatched` và `seq`).
* Pane trao đổi thật sự đang chạy: `views/journey_discussion.py` + `core/journey_notes.py`
  (`quick_notes kind=journey_note`, kho tệp `core/inbox_attachments`). `views/shipment.py`
  (chỗ gắn pane nội bộ của PR #234) **không được route** — `views/web_app.py` chỉ render
  `views/logi_shell`. Đây là phát hiện, không phải giả định: `grep -rn "views.shipment"` không có
  điểm gọi nào ngoài test/tool.

## 2. Thay đổi (một intent đọc, không backend thứ hai)

| File | Việc |
|---|---|
| `views/journey_focus.py` (mới) | Chuẩn hoá + lưu **một** ý định UI đã xác minh; `seq` one-shot; `for_customer` / `for_staff` tái xác minh lô + công đoạn theo projection của server |
| `assets/customer_portal/hexa-portal.js` | Nút “💬 Trao đổi / Chứng từ” trong bubble của node → `setTriggerValue('journey_focus', {seq, event, payload:{shipment_id, stage_id}})`; nút tự vô hiệu hoá khi không có transport |
| `views/customer_portal_component.py` | Đăng ký **một** callback `on_journey_focus_change`; trả về `ComponentResult` để có fallback |
| `views/customer_dashboard.py` | Resolve intent → render **pane hiện có** ở trên bản đồ (`focus=...`); fallback capture + 1 rerun khi runtime không chạy prefix callback; nút “Đóng” |
| `views/journey_discussion.py` | `focus_stage` / `focus` mở đúng expander + đúng công đoạn (widget key theo stage, không tái dùng lựa chọn cũ); caption “Đang mở từ Journey Map…”; không đổi backend/kho tệp |
| `component/src/components/JourneyMap.tsx` | Chip 💬 là **sibling** của nút node (không lồng button), phát `journey_focus` read-only |
| `component/src/lib/dispatcher.ts` + `component/dist/*` | Thêm `journey_focus` vào allowlist typed event; rebuild bundle (`vite build`, `scan_process.py` = 0 executable hit) |
| `views/logi_view_model.py` | `JOURNEY_FOCUS_EVENTS` + `consume_journey_focus_triggers` (read-only, `seq` dùng chung) + `journey_focus_pane()`; thêm 1 rerun để pane lên trên shell |
| `views/web_app.py` | Render pane nội bộ đang có phía trên shell khi có intent hợp lệ; gate `shipment_edit` |

Không tạo collection/collection-index/upload/API mới. Tệp vẫn đi qua `core.inbox_attachments`
đang cấu hình; comment vẫn là `quick_notes`.

## 3. Mô hình tin cậy

* Trình duyệt chỉ gửi `{shipment_id, stage_id}`. **Không** gửi `customer_id`, email, quyền,
  nội dung, tệp.
* `stage_id` phải nằm trong `core.journey_notes.STAGE_IDS` (00..06), nếu không = đóng pane.
* `shipment_id` phải khớp **projection của server cho chính danh tính hiện tại**:
  khách → `view.cards` của `CustomerPrincipal` đã xác thực; nội bộ → `vm["shipments"]` đã qua RBAC.
* `customer_id` cho pane nội bộ lấy từ **row projection** (`row["customerId"]`), không từ browser;
  `core.journey_notes._scope` vẫn kiểm tra lại `shipments.customer_id` trên DB trước mỗi lần đọc/ghi.
* `seq` one-shot: trigger phát lại không mở lại pane đã đóng; dispatch đôi bị chặn như mọi event khác.
* Quyền: pane nội bộ cần `shipment_edit` (ma trận duy nhất `core/auth.ROLE_PERMISSIONS`);
  khách chỉ `CUSTOMER`, `INTERNAL` vẫn bị lọc ở `core.journey_notes.list_stage_notes`.

## 4. Bằng chứng thực thi

### 4.1 Suite

```
python -m pytest tests -q --continue-on-collection-errors
```
| Lần đo | Kết quả |
|---|---|
| Baseline `7ac441b` | 35 failed / 2196 passed / 44 skipped |
| Sau thay đổi | **35 failed / 2216 passed / 44 skipped** |
| Tập FAILED | **giống hệt baseline** (so sánh theo id) — không có failure mới |
| +20 test mới | `tests/test_journey_map_focus.py` (20 PASS) |

Test mới: `python -m pytest tests/test_journey_map_focus.py -q` → **20 passed**.

### 4.2 Front-end thật (jsdom, không cần browser)

```
node tests/component/dom_acceptance_journey_focus_customer.mjs
  PASS Journey Map node → discussion intent (desktop/mobile, 0/1/2 lots, no transport)
node tests/component/dom_acceptance_journey_focus_shell.mjs
  PASS Journey Map node action (shell): 2 nodes, one read-only intent {LO-0307, MAIN_CARRIAGE},
       node interaction intact, zero-node lot inert
```

Phủ: desktop + mobile 390px; 0/1/2 lô; đổi lô thứ hai; `seq` tăng; payload không chứa
`customer_id`/`customerId`/`@`/`INTERNAL`/`body`/`attachment`; không transport → nút disabled và
không gửi; node vẫn mở đúng panel cũ; lô 0 node không có action.

### 4.3 Đường ứng dụng thật (AppTest trên `app.py`)

`tests/test_journey_map_focus.py::test_real_app_opens_the_existing_internal_pane_above_the_shell`
chạy `views.web_app.main` (AUTH_REQUIRED=False, DB mongomock) và đo được expander
`💬 Trao đổi / Chứng từ · lô G1-LG-001 · công đoạn Thông quan`, selectbox `04 · Thông quan`,
caption “Đang mở từ Journey Map”, và note `INTERNAL` **hiện** cho người nội bộ.
Hai test âm: lô ngoài projection → không pane; thiếu `shipment_edit` → không pane.

### 4.4 Mutation proof (5/5 bị giết)

| Mutation | Kết quả |
|---|---|
| Bỏ `index=` của công đoạn focus | FAIL đúng chỗ |
| `for_customer` nhận mọi lô (bỏ kiểm cards) | FAIL đúng chỗ |
| Bỏ lọc `visibility=CUSTOMER` (INTERNAL lộ cho khách) | FAIL đúng chỗ |
| JS luôn gửi `stage_id='plan'` | FAIL đúng chỗ |
| Bỏ `journey_focus` khỏi allowlist trong **dist** | FAIL đúng chỗ (0 trigger) |

## 5. Chưa chứng minh / blocker còn lại

* **Không có browser thật** trong sandbox (Playwright/browser binary không có; chỉ jsdom +
  Streamlit AppTest). Desktop/mobile là mô phỏng DOM, **không** phải ảnh chụp thiết bị thật.
* **Cloud UAT vẫn BLOCKED**: deployed SHA của `thu-log-g1-test.streamlit.app`, danh tính DB runtime
  và Google OIDC thật chưa xác minh. Không ghi dữ liệu Cloud trong phiên này.
* `views/shipment.py` (pane nội bộ của PR #234) vẫn **chết** — không route. Pane nội bộ nay chạy
  qua `views/web_app.py` + `views.logi_discussion`, nhưng vẫn là **Streamlit pane đặt phía trên
  shell**, không nằm trong React; muốn “in-map” thật cho Trường Thành cần một lane riêng (đọc
  notes vào view-model + composer trong React) — chưa làm, chưa được duyệt.
* Pane nội bộ chỉ mở cho role có `shipment_edit` (viewer không đọc được trao đổi — đúng theo
  `core.journey_notes._actor`, nhưng là hạn chế sản phẩm cần Owner quyết).
* Chưa có test nào chứng minh Google OIDC → principal thật; phần khách chỉ được chứng minh ở lớp
  principal giả lập + server-built cards.
