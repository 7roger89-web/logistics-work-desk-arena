# PR #234 — QA thực chạy trên HEAD (30/10/2026)

Code được kiểm thử: `2e510d50f2ec58284f4e3e8a74b1ea2bb42811e0` (nhánh session
`arena/6db41d2f-logistics-work-desk-arena`, dựa trên PR #234 HEAD
`f80b2bdfe3931a67ca299d3a7b0e425db5486c68`).

Môi trường: Python 3.11.2 · streamlit 1.66.1 · pytest 9.2.0 · mongomock 4.3.0 ·
pymongo 4.19.0 · node v22.22.3. DB là **mongomock**, kho byte là **kho giả lập
được inject** (`FakeStore`), không có Cloud/Mongo/Drive thật, không dữ liệu khách.

## 1. Kết quả test thực tế

```
$ python -m pytest -q tests/test_journey_notes.py
48 passed

$ python -m pytest -q tests/test_customer_dashboard_g1_runtime.py \
    tests/test_customer_portal_core_g1.py tests/test_customer_portal_g15_independent_challenge.py \
    tests/test_customer_portal_publish_g15.py tests/test_customer_portal_sources_g15.py \
    tests/test_customer_portal_tenant_reset_g15.py tests/test_inbox_snippets.py
138 passed   (sau khi cài `jsdom` cho component; trước đó 2 FAIL chỉ vì thiếu node_modules)

$ python -m pytest -q tests --continue-on-collection-errors
34 failed, 2197 passed, 44 skipped, 10 subtests passed
```

Baseline cùng máy, cùng lệnh, tại `f80b2bd`: **34 failed / 2185 passed / 44
skipped**. Tập FAILED **giống hệt từng tên** (agreements_api, all_tabs_smoke,
dashboard_financial_write_oracle, entity_context_ui ×2, handbook, lg08_1_safety
×2, … shipment_slash_route_repair_01). Không phát sinh lỗi mới; +12 test mới đều
PASS. Hai FAIL `test_customer_portal_tenant_reset_g15` và
`test_dom_acceptance_inbox_desktop_and_mobile` ở lần chạy đầu là **thiếu
`node_modules` (jsdom)** trong sandbox, không phải lỗi code; sau `npm install`
trong `component/` cả hai PASS.

## 2. Bằng chứng UI: chọn công đoạn → gửi → lưu → reload → xem lại

Tất cả chạy bằng `streamlit.testing.v1.AppTest` trên **script thật**
(`app.py` cho cổng khách, `views.journey_discussion.render_internal_discussion`
cho màn lô hàng) với widget Streamlit thật, không chỉ gọi hàm backend.

| Bước | Bằng chứng |
| --- | --- |
| Trường Thành chọn công đoạn | `selectbox 'Công đoạn'` = `02 · Gom hàng`; note lưu `stage_id=consolidate`, công đoạn khác rỗng — `test_ui_stage_selection_sends_and_shows_the_note_immediately` |
| Gửi → thấy ngay (không cần reload tay) | sau một lần bấm `Gửi`, nội dung **xuất hiện trong thread cùng lượt chạy** + “Đã lưu trao đổi” (flash sống qua rerun) |
| Gửi nội bộ vs công khai | `radio 'Ai nhìn thấy nội dung này?'` → `INTERNAL` (khách không thấy) hoặc `CUSTOMER`; khách đọc được note công khai nhưng **không** thấy `NỘI BỘ: giá vốn` — `test_ui_staff_public_note_file_and_customer_reply_meet_at_the_same_stage` |
| Đính chứng từ | `file_uploader.upload("to-khai.png")` → lưu qua kho inject, 1 tệp trong kho |
| Reload | AppTest **instance mới** chạy lại script: note + nút `📎 to-khai.png` vẫn còn ở đúng công đoạn Thông quan, công đoạn Lấy hàng rỗng; bấm đính kèm hiện `⬇️ Tải xuống` và `read_note_attachment` trả đúng byte PNG gốc — `test_ui_upload_then_reload_keeps_the_document_and_downloads_it` |
| Lục Giác gửi | cổng khách (OIDC giả lập, `app.py`): chọn `04 · Thông quan`, gửi “Khách đã xác nhận tờ khai”, reload vẫn thấy, công đoạn giữ nguyên; thread nội bộ nhận đúng note `author_kind=customer`, `visibility=CUSTOMER`, công đoạn pickup vẫn rỗng |
| Tải chứng từ phía khách | khách tải được đúng tệp của note công khai; không thấy và không tải được note nội bộ |

## 3. Sáu kịch bản bắt buộc

| Kịch bản | Test | Kết quả |
| --- | --- | --- |
| Trường Thành gửi comment nội bộ hoặc công khai | `test_internal_ui_posts_a_note`, `test_internal_ui_can_publish_a_customer_visible_note`, `test_ui_staff_public_note_file_and_customer_reply_meet_at_the_same_stage` | PASS |
| Lục Giác chỉ xem/gửi trong lô của mình | `test_ui_customer_cannot_see_or_write_another_lots_thread`, `test_ui_customer_with_two_lots_posts_into_the_lot_it_selected`, `test_customer_cannot_write_to_another_customers_lot` | PASS |
| Đính chứng từ, reload còn dữ liệu | `test_ui_upload_then_reload_keeps_the_document_and_downloads_it` | PASS |
| Chuyển chủ lô / xoá lô không đọc–tải dữ liệu cũ | `test_ui_reassigned_lot_hides_previous_notes_and_files`, `test_ui_deleted_lot_hides_previous_notes_and_files`, `test_shipment_reassignment_revokes_old_tenant_notes_and_bytes`, `test_removed_shipment_denies_old_stage_notes_and_download` | PASS |
| Chứng từ bị thu hồi không tải được | `test_ui_revoked_document_is_not_listed_or_downloadable`, `test_revoked_attachment_status_blocks_download_and_listing` | PASS |
| Đổi khách không lộ comment/file/bản nháp | `test_ui_switching_customer_clears_thread_draft_and_staged_file` (AppTest thật: đổi session → thread trống, ô soạn thảo rỗng, tệp đang chọn rỗng, không còn nút `📎`) | PASS |
| (thêm) quá 4 tệp | `test_ui_more_than_four_files_is_refused_without_writing` | PASS |
| (thêm) pane được mount ở trang thật | `test_real_pages_are_wired_to_the_discussion_panes` | PASS |

## 4. Lỗi phát hiện & đã sửa trong phiên này

1. **Nháp bị gửi nhầm công đoạn.** Ô soạn thảo khoá theo `customer+lot` nhưng
   **không theo công đoạn**: gõ ở “Lấy hàng”, chuyển sang “Thông quan” rồi bấm Gửi
   là note rơi vào công đoạn mới; tệp đã chọn cũng còn treo và có thể bị gửi lại.
   Sửa: khoá `body/visibility/file_uploader/send` theo `customer+lot+stage`,
   uploader reset sau mỗi lần gửi thành công.
2. **Gửi xong không thấy bình luận.** Thread được render *trước* composer nên note
   vừa lưu chỉ hiện ở lần tương tác kế tiếp (dễ khiến người dùng bấm Gửi lần 2).
   Sửa: flash một lần + `st.rerun()`; xác nhận “Đã lưu trao đổi” vẫn hiển thị.
3. **Nhãn nút đính kèm không escape.** Tên tệp là markdown trong `st.button`;
   đã escape như phần còn lại của thread.

Ba đột biến chứng minh test mới có hiệu lực (mỗi đột biến làm đúng test FAIL, sau
đó khôi phục):

| Đột biến | Test FAIL |
| --- | --- |
| bỏ `stage` khỏi khoá composer | `test_ui_draft_is_scoped_to_its_stage…`, `test_ui_stage_selection_sends…` |
| bỏ flash + `st.rerun()` | `test_ui_stage_selection_sends…`, `test_ui_staff_public_note_file…` |
| bỏ recheck chủ lô trong `read_note_attachment` | `test_shipment_reassignment_revokes…`, `test_removed_shipment_denies…` |

## 5. Giới hạn trung thực

- **CLOUD_QA=BLOCKED**: chưa có SHA deploy và danh tính DB của
  `thu-log-g1-test.streamlit.app` được chứng minh; không ghi Cloud/production.
- Không có PyMongo/GridFS/Drive thật: byte đi qua `core.inbox_attachments` với
  kho giả lập inject; hợp đồng adapter là của code sẵn có, không phải bằng chứng
  hạ tầng.
- Không có ảnh DOM/CSS: pane là widget Streamlit, AppTest chạy runtime Streamlit
  thật nhưng không render pixel. Comment **chưa** nhúng vào node/modal React
  `stage_comments`; vẫn là pane ngay dưới Journey Map.
- Dữ liệu là giả lập; chưa có nguồn chứng từ/sự kiện thật do nghiệp vụ duyệt.
