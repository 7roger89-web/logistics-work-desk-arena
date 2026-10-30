# Trao đổi + chứng từ theo công đoạn lô hàng — bằng chứng

Lát phát triển tiếp theo sau G1.5 (PR #232). Repository:
`7roger89-web/logistics-work-desk-arena`. Nhánh làm việc:
`arena/85dbc833-logistics-work-desk-arena` (phụ thuộc PR #232, **chưa merge**).

## Phạm vi đã làm

- `core/journey_notes.py` — một luồng trao đổi gắn **khách hàng + lô hàng +
  công đoạn** (7 công đoạn `plan → finance`), lưu trong **collection
  `quick_notes` đang có** với `kind="journey_note"`. Không tạo kho lưu trữ mới.
- `views/journey_discussion.py` — cùng một composer/thread cho hai phía:
  `render_internal_discussion` (màn lô hàng Trường Thành) và
  `render_customer_discussion` (cổng khách hàng, dưới Journey Map).
- Tệp đính kèm đi qua **`core/inbox_attachments`** → đúng adapter kho chứng từ
  đang cấu hình (`ATTACHMENT_STORAGE_BACKEND`, mặc định **GridFS**;
  `drive_shared`/`drive_oauth` khi được cấu hình). **Không giả định Google
  Drive**: nếu kho chưa sẵn sàng, ghi bị từ chối và không lưu nửa vời.

## Phân quyền

| Hành động | Trường Thành | Lục Giác |
| --- | --- | --- |
| Đọc nội bộ (`INTERNAL`) | có (quyền `shipment_edit`) | **không bao giờ** |
| Đọc nội dung `CUSTOMER` | có | chỉ lô của chính mình |
| Ghi `INTERNAL` | có | bị ép thành `CUSTOMER` |
| Ghi `CUSTOMER` | có | có, chỉ lô của mình (đối chiếu `shipments.customer_id`) |
| Tải tệp đính kèm | có | chỉ tệp của note `CUSTOMER` trên lô của mình |

Danh tính khách hàng do server quyết định (`portal_access_email` → `customers.id`);
không có tham số `customer_id`/`shipment_id` từ trình duyệt ở phía cổng khách.

## Kiểm thử (`tests/test_journey_notes.py`, 31 PASS)

Runtime: Python 3.11.2, pytest 9.2.0, streamlit 1.66.1, mongomock 4.3.0. Kho
bytes giả lập được inject, không chạm Cloud/production/dữ liệu thật.

- lưu → đọc lại → reload nhiều lần vẫn đúng nội dung; đúng công đoạn, đúng lô;
- note nội bộ không xuất hiện ở phía khách (cả khung nhìn lẫn AppTest thật);
- khách ghi `INTERNAL` bị ép thành `CUSTOMER`; viewer/unknown/robot bị từ chối;
- khách không ghi được vào lô khách khác; công đoạn sai/nội dung rỗng bị từ chối;
- tệp: lưu qua kho giả lập, metadata trả về **không** lộ `storage_file_id`/`sha256`;
  khách tải được tệp của note `CUSTOMER`, bị từ chối với note nội bộ và lô người khác;
- kho chứng từ lỗi → **không** lưu note và bù xoá byte đã ghi; tệp sai định dạng/rỗng bị từ chối;
- UI: pane nội bộ chạy trong **Streamlit thật** (`AppTest.from_string`) gửi được
  note; cổng khách (app.py + OIDC giả lập) gửi, reload và hiển thị đúng;
- thoát HTML: nội dung note chứa `<script>` được escape trước khi render.

**Đột biến (chứng minh test không rỗng)** — mỗi đột biến làm đúng test tương ứng FAIL:
1. bỏ lọc `visibility` khi khách đọc → 2 FAIL;
2. không ép `CUSTOMER` khi khách ghi + bỏ chặn đọc khác khách → 2 FAIL;
3. bỏ chặn ghi/tải chéo khách và tải nội bộ → 2 FAIL.

## Full suite (cùng lệnh, cùng môi trường)

`python -m pytest tests -q --continue-on-collection-errors -p no:cacheprovider`

| HEAD | Kết quả |
| --- | --- |
| PR #232 gốc `968e7cf` | 38 failed / 2115 passed / 45 skipped |
| + review G1.5 | 35 failed / 2148 passed / 44 skipped |
| + trao đổi công đoạn | **34 failed / 2178 passed / 44 skipped** |

Không có lỗi mới so với baseline; tập lỗi nền (34) không đổi.

## Giới hạn trung thực

- Chưa chạy trên Cloud/Streamlit thật với Google OIDC và Mongo thật:
  `CLOUD_QA=BLOCKED` (deployed SHA và DB identity chưa xác minh).
- Chưa nối vào `stage_comments`/`stage_documents` của Journey Map trong
  component React: phần trao đổi hiển thị bằng widget Streamlit ngay dưới bản đồ.
- Chưa có nguồn sự kiện/chứng từ thật được nghiệp vụ duyệt: dữ liệu thử là giả lập.

## Hậu kiểm khi tích hợp nhánh PR #234 (30/10/2026)

- PR #232 G1.5 **đã merge staging** tại `e75a239277573f0d470607818e40b8d11f775e44` trước khi mở PR #234; câu “chờ PR #232” phía trên là bối cảnh lịch sử của patch gốc.
- **7/7 blob sha** của patch gốc trong `7roger89-web/CHUNLI@arena/5bc30481-chunli/logi/journey-notes` khớp khi áp dụng lên đúng staging SHA. Thay đổi sau patch: đọc/tải phải xác minh chủ lô còn hiệu lực, tệp bị REVOKED phải ẩn, key ô soạn thảo tách customer/lot, tối đa 200 comment mới nhất, báo lỗi khi chọn >4 tệp.
- **31 PASS và 3 mutation proofs chỉ áp dụng cho patch gốc**, **không phải** cho HEAD cuối chứa các guard mới. Các regression test mới `test_shipment_reassignment_revokes_old_tenant_notes_and_bytes`, `test_removed_shipment_denies_old_stage_notes_and_download`, `test_streamlit_customer_composer_keys_are_scoped_per_tenant_and_lot`, `test_revoked_attachment_status_blocks_download_and_listing`, `test_latest_notes_remain_visible_after_read_limit` **NOT_RUN trên runtime với PyMongo/Streamlit**. PR #234 giữ trạng thái Draft, chưa đủ điều kiện merge staging.
- Chưa có bằng chứng Cloud deployed SHA/DB identity, Google OIDC thực hoặc dữ liệu thật; không ghi production.
