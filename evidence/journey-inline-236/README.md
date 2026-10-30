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
| Toàn bộ suite Python | `34 failed / 2255 passed / 44 skipped` — **trùng đúng tập FAILED nền 34** của `a570383` (baseline `2247 passed`) | `/tmp/after2.txt` (so với `/tmp/baseline_suite.txt`) |
| `tests/test_journey_notes.py` | 54 PASS (thêm reply/orphan/replay/revoked/no-progress-change/inline UI) | `tests/test_journey_notes.py` |
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

## Chưa xác minh (không tự nhận)

- **`VISUAL_PASS=NOT_VERIFIED`**: sandbox không có trình duyệt thật. Không có ảnh chụp 1280px /
  390px, không kiểm chứng trực quan clipping, bottom sheet thật, hay độ mượt pan/zoom.
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
