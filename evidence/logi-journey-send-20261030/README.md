# LOGI — khách Lục Giác gửi trao đổi trong node Journey Map: tái hiện, sửa, nghiệm thu

- **Ngày thực thi:** `2026-10-30` (UTC), trong Arena (E2B Firecracker microVM, Debian 12, Python 3.11.2, Node v22.22.3).
- **Repository:** `7roger89-web/logistics-work-desk-arena`
- **Nhánh làm việc:** `arena/c78d9bf7-logistics-work-desk-arena` (nhánh của phiên Arena này).
- **Base đo lại:** yêu cầu ghi `4dd3cb9aceaedf66a2128b8612a38012f3e13e50`; nhánh phiên được tạo từ `main@9e4190b` (cũ hơn 81 commit và **chưa có** `views/customer_dashboard.py`). Đã fetch `arena/ae5f9f47-logistics-work-desk-arena` (nhánh tích hợp nhận PR #234–#241, không có ref tên `staging`) và đưa nhánh phiên lên đúng `4dd3cb9` trước khi sửa. `main`/production không bị chạm.
- **Trình duyệt:** Chromium thật `153.0.8010.0` (`@sparticuz/chromium@153.0.0` + `@playwright/cli@0.1.22`, cài trong `/tmp`, đúng công thức đã chạy ở PR #241).

## 1. Kết quả

| Hạng mục | Kết quả | Bằng chứng |
|---|---|---|
| `CUSTOMER_SEND` | `VERIFIED` | Khách Lục Giác gửi bình luận trong bubble node `01 LẤY HÀNG`; thread `0 → 1`; không còn alert lỗi (`01-before-fix-customer-send-fails-1440x900.png` là trạng thái TRƯỚC khi sửa). |
| `RELOAD_PERSISTENCE` | `VERIFIED` | Reload cứng (phiên Streamlit mới) → mở lại `QA-LOT` / `01 LẤY HÀNG` → đúng bình luận `QA-SEND-…` còn nguyên, thread vẫn `4`. |
| `STAFF_REPLY_CUSTOMER_READBACK` | `VERIFIED` | Trường Thành đăng nhập thật (`AUTH_REQUIRED=true`, tài khoản fixture trong `users` store), mở cùng lô/công đoạn, đọc câu hỏi của khách, trả lời với phạm vi `👁 Khách xem`; khách reload và đọc được câu trả lời (`06/07-customer-read-staff-reply-*`). |
| `TENANT_ISOLATION` | `PASS` | Khách khác: không thấy `QA-LOT`, 0 node, 0 khung trao đổi; payload crafted sang lô khác bị từ chối (`INVALID_SCOPE`) và không ghi byte nào (test mới + browser `08-other-customer-isolation-1440x900.png`). |
| `BROWSER_QA` | `VERIFIED` | Desktop `1440x900` + mobile `390x844`; hội thoại nằm trong bubble, 4/4 nút `hitOk`/in-viewport, `horizontalOverflow=false` (`geometry-checks.json`). |

## 2. Điểm đứt thực tế (tái hiện trước khi sửa)

Chạy đúng fixture QA khách hàng đã dùng ở PR #241 (`tests/component/g15_isolated_runtime.py`, port 9502, `mongomock` cô lập), bấm `Gửi` trong node:

- Giao diện: `alert` **“Không gửi được trao đổi.”**, thread vẫn `💬 Trao đổi (0)` → `01-before-fix-customer-send-fails-1440x900.png`.
- Log server: `JOURNEY_NOTE_DB_UNAVAILABLE reason=None`.

Nguyên nhân: `views/customer_dashboard.py::render_customer_dashboard` **đọc** bằng handle `db` được truyền vào
(`journey_inline.build_customer_discussion(..., db=db)`) nhưng **ghi** qua `handle_portal_events` /
`on_portal_event` **không truyền `db`**; `core.journey_notes._resolve_db(None)` rơi về
`core.database.get_db()` — một handle thứ hai, độc lập. Khi runtime truyền handle (QA/staging fixture, mọi host
mà cổng khách dùng DB được inject), write không tới được DB mà read đang đọc → từ chối ghi hoặc ghi vào nơi
reload không bao giờ đọc lại. Test cũ che lỗi này vì `_portal_stack()` patch `core.journey_notes._resolve_db`
(`tests/test_journey_notes.py:730`).

Đã kiểm chứng thêm bằng mutation: bỏ `db=db` (giữ nguyên chữ ký) → test mới fail; đổi `on_portal_event` truyền
`db=None` → test callback fail. Không có test nào cũ bị đổi trạng thái.

## 3. Thay đổi

`views/customer_dashboard.py` (chỉ tệp này):

- `handle_portal_events(..., *, db=None)` → `journey_inline.consume_customer_triggers(..., db=db)`.
- `_portal_context(db=None)` → `build_customer_principal(..., db=db)` + `load_customer_dashboard(..., db=db)`.
- `on_portal_event(*, db=None)`; đăng ký callback bằng `functools.partial(on_portal_event, db=db)`.
- Fallback consumer: `handle_portal_events(component_result, principal, view.cards, db=db)`.

Không đổi: OIDC, tenant/principal, `customer_id + shipment_id + stage_id` phía server, RBAC, visibility
(khách luôn bị ép `CUSTOMER`), backend `core.journey_notes`, không thêm form Streamlit, không thêm kho file,
không đụng `views/logi_view_model.py` (đường nội bộ resolve `get_db()` qua `logi_sandbox.ensure_backend()`,
tức vẫn là database mà shell đọc — đã chứng minh bằng browser).

Regression tests (`tests/test_journey_notes.py`, +4):

1. `test_customer_portal_comment_is_written_to_the_db_the_portal_rendered` — ghi + reload qua seam thật, đồng thời chứng minh **không** ghi vào handle thứ hai.
2. `test_customer_portal_prefix_callback_writes_through_the_same_db` — đường callback prefix (production OIDC path).
3. `test_customer_portal_event_seam_refuses_another_tenant_lot` — payload crafted sang tenant khác bị từ chối, không ghi, không lộ.
4. `test_customer_portal_event_seam_passes_its_db_handle` — chốt call-site (read/callback/write) cùng một handle.

QA harness mới (QA-only, không phải production code): `tests/component/g15_lg_tt_discussion_runtime.py`
— một database `mongomock` cô lập cho **cả hai** cổng; khách là fixture, Trường Thành đăng nhập bằng mật khẩu
thật vào `users` store của fixture (không nhét `current_user` giả — chính cổng `fresh_session_identity_for_action`
đã chặn cách đó và ghi nhận là bài học).

## 4. Test

| Lần chạy | Kết quả |
|---|---|
| Baseline tại `4dd3cb9` (worktree sạch) | **2259 passed, 40 failed, 45 skipped** (`/tmp/base`) |
| Nhánh này (sau sửa) | **2263 passed, 40 failed, 45 skipped** |
| So sánh tập FAILED | **giống hệt** (`diff` rỗng) — 40 lỗi đỏ sẵn có, không thêm, không mất |
| `tests/test_journey_notes.py` | 67 passed (4 test mới) |

Lệnh: `/tmp/venv/bin/python -m pytest tests -q --continue-on-collection-errors -p no:randomly --tb=no`

## 5. Ảnh và dữ liệu đo (thực tế, cùng commit)

| Tệp | Nội dung |
|---|---|
| `01-before-fix-customer-send-fails-1440x900.png` | TRƯỚC khi sửa: bấm `Gửi` → “Không gửi được trao đổi.” |
| `02-customer-discussion-desktop-1440x900.png` | Cổng khách: bình luận nằm trong bubble node (desktop). |
| `03-customer-discussion-mobile-390x844.png` | Cổng khách: bubble + composer + `Gửi` trên mobile, không tràn ngang. |
| `04-staff-reply-desktop-1440x900.png` | Trường Thành trong Journey Map nội bộ: đọc câu hỏi, trả lời `👁 Khách xem`, `2 trao đổi`. |
| `05-staff-reply-mobile-390x844.png` | Cùng màn hình ở `390x844`. |
| `06-customer-read-staff-reply-desktop-1440x900.png` | Khách reload, đọc được câu trả lời của Trường Thành. |
| `07-customer-read-staff-reply-mobile-390x844.png` | Như trên ở `390x844`. |
| `08-other-customer-isolation-1440x900.png` | Khách khác: không có `QA-LOT`, không có node, không có khung trao đổi. |
| `geometry-checks.json` | `getBoundingClientRect`, `scrollWidth/clientWidth`, `elementFromPoint().hitOk` đo thật. |
| `flows/*.js` | Đúng script đã chạy qua `playwright-cli run-code` (tái lập được). |

## 6. Giới hạn trung thực

- Danh tính khách là **fixture QA**, không phải Google OIDC thật; luồng OIDC không được chứng minh trong phiên này. Mọi kiểm tra tenant/quyền/visibility phía server vẫn chạy thật.
- Database là `mongomock` trong tiến trình (sống theo tiến trình, không phải MongoDB/Drive production). “Reload” được chứng minh ở tầng server (dữ liệu đọc lại từ DB chứ không phải session state), không chứng minh độ bền của MongoDB thật.
- Tệp đính kèm (bytes) không phải trọng tâm phiên này: đường ghi chứng từ dùng kho bytes riêng (`core.inbox_attachments`), không nằm trong thay đổi này.
