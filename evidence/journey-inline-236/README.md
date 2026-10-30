# Issue #236 — trao đổi trong Journey Map tại node đang xem

Ngày QA: 30/10/2026. Nhánh: `arena/385e4a4d-logistics-work-desk-arena`, nền staging `a570383`
(`a570383b1cf1d97f80f2144689e489195beaef35`).

## Điều đã thay đổi (một hệ thống, không backend thứ hai)

- `views/journey_inline.py` (mới): adapter có biên. Đọc **đúng một** lô + **đúng một** công đoạn
  qua `core/journey_notes.py`; nhận `journey_note_create` / `journey_note_download` một lần
  (chống replay theo `seq` + `requestId`), tái xác minh khách/lô/công đoạn/quyền ở server.
- `core/journey_notes.py`: thêm `reply_to_id` (một cấp; trả lời của trả lời gộp về gốc).
  `build_thread` **bỏ** phản hồi có cha không nhìn thấy (không lộ cha INTERNAL, không có
  "phản hồi mồ côi" đội lốt bình luận gốc).
- `component/src/components/JourneyDiscussionPanel.tsx` (mới) + `JourneyMap.tsx`: panel gắn vào
  node, nằm trong viewport của bản đồ (không bị cắt), bottom sheet < 640px, mặc định INTERNAL
  với nhân viên, hiện đúng một cấp trả lời.
- `assets/customer_portal/hexa-portal.js|css`: danh sách bình luận + trả lời + ô nhập + đính kèm +
  tải nằm **trong bubble của node**; refresh giữ lô + node + pan/zoom (`fit:false`).
- `views/customer_dashboard.py`, `views/logi_view_model.py`, `views/web_app.py`: bỏ hẳn pane
  Streamlit phía trên bản đồ; chỉ còn `journeyDiscussion` trong payload component.

## Bằng chứng đã chạy

| Kiểm chứng | Kết quả | Đường dẫn |
| --- | --- | --- |
| Toàn bộ suite Python | `34 failed / 2266 passed / 44 skipped` — **trùng đúng tập FAILED nền 34** của `a570383` (baseline `2247 passed`) | `/tmp/final_7ffd232_suite.txt` (so với `/tmp/baseline_suite.txt`) |
| `tests/test_journey_notes.py` | **63 PASS** (thêm reply/orphan/replay/revoked/no-progress-change/inline UI + 5 test bind phạm vi tải + 2 test stale/repeat download + 2 ca kiểm lại file đã queue trước khi giao) | `tests/test_journey_notes.py` |
| `tests/test_journey_map_focus.py` | 54 PASS (payload đúng node, không form Streamlit, từ chối focus lạ) | `tests/test_journey_map_focus.py` |
| Nhóm phụ thuộc (portal/journey/inbox) | 181 PASS | lệnh trong log phiên |
| jsdom — khách | `PASS … focus + reply + file + download inside the node bubble, scope separated` | `tests/component/dom_acceptance_journey_focus_customer.mjs` |
| jsdom — shell nội bộ | `PASS … thread inside the map, reply→root, backend-authoritative clear, bounded download` | `tests/component/dom_acceptance_journey_inline_shell.mjs` |
| jsdom — focus cũ (không hồi quy) | `PASS Journey Map node action (shell)` | `tests/component/dom_acceptance_journey_focus_shell.mjs` |
| Build + scan | `dist/logi-shell.js` 1.576,33 kB (gzip 338,27 kB); `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0` | `component/dist/*` |

Các test jsdom chứng minh: payload focus chỉ có `{shipment_id, stage_id}` (không khách/quyền);
`journey_note_create` mang `replyToId` đúng gốc, `visibility=CUSTOMER` ở cổng khách và
`INTERNAL` mặc định ở shell, không có `customer_id`/email/role; tệp đi base64 có giới hạn;
`journey_note_download` chỉ mang mã; ô nhập chỉ được xóa khi server trả outcome đúng
`requestId`; chữ người dùng là text (không thành DOM); chạm vào hội thoại không pan/zoom;
refresh không reset pan/zoom và không gửi lại intent.

## Sửa blocker review `6519682460` — tải chứng từ phải đúng lô + công đoạn đang mở

**Lỗi:** `_handle_download` gọi `read_note_attachment(note_id, attachment_id, actor, db)` mà không buộc
ghi chú phải thuộc **đúng** `customer_id + shipment_id + stage_id` mà server đã resolve cho panel.
Biết mã note/tệp của lô khác (hoặc công đoạn khác, hoặc lô ngoài projection của nhân viên) là có thể
lấy được byte, rồi `_store_download` gắn nhầm phạm vi.

**Sửa (nhỏ nhất, giữ nguyên backend/quyền/UI):**

- `core/journey_notes.py::read_note_attachment` nhận thêm `expected_scope` (tùy chọn, tương thích
  ngược). Khi có, nó so `customer_id`, `shipment_id`, `stage_id` **của chính row** với phạm vi server
  vừa resolve, **trước khi** tra attachment và **trước khi** gọi kho byte. Lệch → trả cùng một thông
  báo "Không tìm thấy chứng từ." (không tạo oracle), log `reason=focus_scope_mismatch`.
  Thiếu bất kỳ thành phần nào của `expected_scope` → fail closed (không khớp).
- `views/journey_inline.py::_handle_download` luôn truyền `expected_scope` từ focus đã xác minh
  (`customer_id` lấy từ projection/RBAC của chính danh tính, không phải từ trình duyệt).
- Không đổi `create`, không đổi visibility/RBAC, không thêm collection/kênh tải thứ hai.

**Chứng minh (test mới trong `tests/test_journey_notes.py`):**

| Ca | Kỳ vọng | Test |
| --- | --- | --- |
| Tệp đúng lô + đúng công đoạn | tải được, byte khớp `PNG_1PX` | `test_attachment_read_is_bound_to_the_expected_lot_and_stage`, `test_staff_inline_download_matches_a_note_in_the_same_open_scope`, `test_ui_staff_public_note_file_and_customer_reply_meet_at_the_same_stage` |
| Cùng khách, **lô khác**, biết mã tệp | từ chối, `download=None`, không đọc kho | `test_inline_download_refuses_a_note_from_another_lot_even_with_its_ids` |
| Cùng lô, **công đoạn khác**, biết mã tệp | từ chối, không đọc kho | `test_inline_download_refuses_a_note_from_another_stage_of_the_same_lot` |
| **Lô ngoài projection** của nhân viên (cả focus giả lẫn mã tệp) | `INVALID_SCOPE` / `NOT_FOUND`, không byte nào vào slot | `test_staff_inline_download_refuses_a_lot_outside_the_projection` |
| `expected_scope` sai/thiếu thành phần | fail closed, kho không bị đọc | `test_attachment_read_is_bound_to_the_expected_lot_and_stage` |
| Khách khác, tệp thu hồi | vẫn từ chối như trước | các test cũ giữ nguyên |

"Không có byte nào" được đo bằng `FakeStore.reads` (số lần gọi kho) **không tăng** và
`discussion["download"] is None`; với nhân viên, slot `STAFF_DOWNLOAD_KEY` rỗng (`slot=False`,
`slot_len=0`).

**Mutation proof:** bỏ đúng dòng `expected_scope=…` trong `_handle_download` → 3 test tấn công
(`another_lot`, `another_stage`, `projection`) FAIL; khôi phục → 8/8 PASS. Vì vậy test bắt đúng lỗi
reviewer mô tả, không phải test trang trí.

## Chưa xác minh (không tự nhận)

- **`VISUAL_PASS=NOT_VERIFIED`**: sandbox không có trình duyệt thật. Đã thử: không có
  `chromium`/`google-chrome`/`firefox` trong PATH, `playwright` không được cài, và CDN tải browser bị
  chặn (`cdn.playwright.dev` và `storage.googleapis.com` đều không kết nối được — chỉ npm/pypi/github
  mở). Vì vậy không có ảnh chụp 1280px/390px, không kiểm chứng trực quan clipping, bottom sheet thật,
  hay độ mượt pan/zoom; không có roundtrip tệp trên trình duyệt thật.
- **Transport byte của component v2 trong runtime Streamlit thật** chưa chạy end-to-end ở đây.
  Cơ sở an toàn: dùng đúng đường đã có của `views/logi_inbox.py` (`files[]` base64 →
  `decode_upload_payload` / `validate_upload`, tối đa 4 tệp × 20 MB, `MAX_BASE64_CHARS` chặn
  trước khi decode). Không thêm backend/kênh thứ hai; không có byte nào trong view-model.
- Chưa UAT Cloud (không ghi Cloud khi chưa xác minh deployed SHA + quyền dataset).

## Điều kiện FAIL của issue

UI trao đổi **không** còn nằm trong expander Streamlit phía trên bản đồ: `views/web_app.py`
không còn `_render_journey_focus_pane`, `views/customer_dashboard.py` không còn
`render_customer_discussion`, và test khẳng định app thật không render `expander`/`text_area`/
`file_uploader` nào cho trao đổi. Pane Streamlit còn lại chỉ ở trang chi tiết lô
(`views/shipment.py`), một màn khác — không thuộc đường đi của Journey Map.

## Bổ sung kiểm tra session download trong cùng PR #237

Kiểm tra nguồn sau commit `9354a9da` phát hiện byte đã queue có thể còn trong session nếu lần tải sau bị từ chối; đồng thời `seq` của tệp lặp bị trả về 1 sau mỗi lần consume, khiến React bỏ qua lần tải thứ hai cùng tệp. Adapter nay clear slot ở mọi download intent mới (kể cả invalid scope), consume-and-drop dù scope không khớp, buộc slot với customer hiện tại, và dùng counter tuần tự riêng. Thêm 2 regression test trong `tests/test_journey_notes.py` để bắt stale bytes, đổi chủ, tải lặp. Cần chạy test trên môi trường có Streamlit/mongomock; chưa có browser roundtrip thật thì `VISUAL_PASS=NOT_VERIFIED`.

## Chạy lại toàn bộ trên HEAD cuối (sau `7ffd232` + `2096dff`)

Review `6519969047` yêu cầu chạy lại đúng tại HEAD sau commit `7ffd232` (sửa stale queued bytes + cho
phép tải lặp). Trong lúc kiểm, nhánh có thêm `2096dff` (kiểm lại file đã queue trước khi giao, huỷ byte
nếu note/tệp không còn hiển thị). Toàn bộ được chạy lại trên HEAD cuối gồm cả hai commit; không sửa gì
thêm ở lớp code:

| Lệnh | Kết quả |
| --- | --- |
| `pytest tests/test_journey_notes.py -k "one_shot_tenant_bound_and_repeatable or clears_previously_queued_bytes"` | **2 passed** (đúng hai regression test được yêu cầu) |
| `pytest tests/test_journey_notes.py -k "queued_file_is_rechecked"` | **2 passed** (ca dương + ca thu hồi/đổi chủ của `2096dff`) |
| `pytest tests/test_journey_notes.py` | **61 passed** |
| `pytest tests/test_journey_map_focus.py` | **54 passed** |
| `node tests/component/dom_acceptance_journey_focus_customer.mjs` | PASS (focus + reply + file + download trong bubble) |
| `node tests/component/dom_acceptance_journey_inline_shell.mjs` | PASS (thread trong map, reply→root, bounded download) |
| `node tests/component/dom_acceptance_journey_focus_shell.mjs` | PASS (mỗi node gửi đúng một intent) |
| `pytest -q` (full suite) | **34 failed / 2266 passed / 44 skipped** — tập FAILED **trùng đúng** 34 lỗi nền của `a570383` |

`VISUAL_PASS=NOT_VERIFIED` giữ nguyên: không có trình duyệt trong sandbox (CDN tải browser bị chặn),
nên chưa có roundtrip tệp thật trên trình duyệt, chưa có ảnh desktop/mobile và transport byte
component v2 chưa chạy end-to-end. Không tự nhận UX PASS.
