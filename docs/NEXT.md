# NEXT — Logistics Work Desk | checkpoint mục tiêu

> Cập nhật **30/10/2026**. Đây là snapshot để tiếp tục làm sản phẩm, không phải luật. Đọc `AGENTS.md` + Supreme Law trước; đo lại GitHub PR/HEAD trước khi dùng SHA lịch sử. Yêu cầu Owner mới nhất và GoalPlan/TaskPlan hiệu lực có ưu tiên cao hơn bản này.

## GOAL

Hoàn thiện **Logistics Work Desk thực sự dùng được**: Trường Thành nhìn Journey của một lô biết đang ở đâu, vướng gì, cần làm gì, chứng từ nào; Lục Giác xem duy nhất tiến độ/chứng từ đã được Trường Thành duyệt và trao đổi theo **đúng công đoạn**. Đơn giản, map-first; không thay phát triển chức năng bằng vòng viết prompt, QA hình thức hay framework mới.

## PROGRESS — mốc đã xác minh

- Repo đúng: `7roger89-web/logistics-work-desk-arena`.
- [PR #233](https://github.com/7roger89-web/logistics-work-desk-arena/pull/233): **MERGED** vào staging; `AGENTS.md` bắt buộc đọc checkpoint hiện tại.
- [PR #232](https://github.com/7roger89-web/logistics-work-desk-arena/pull/232): **MERGED vào staging** ở `e75a239277573f0d470607818e40b8d11f775e44`. Có Admin duyệt công bố event/document theo ID, version và hash nội dung, customer-only reader; fix modal giữ dữ liệu khi đổi khách. Bằng chứng review độc lập 29 challenge tests và focused suite ghi tại `evidence/g15-independent-review/README.md`. **G1.5 đạt code-level staging, chưa chứng minh Google OIDC và dữ liệu nghiệp vụ Lục Giác thật**.
- **Đã tích hợp:** [PR #234](https://github.com/7roger89-web/logistics-work-desk-arena/pull/234) **MERGED staging** ở `0e20a93c48f95b76839c093c9cb56bfcb1472e5f`. Comment + chứng từ gắn `customer_id + shipment_id + stage_id` của 7 mốc; cùng backend `quick_notes`, adapter `core/inbox_attachments` và pane Streamlit tại màn lô Trường Thành / dưới Journey Lục Giác. Tái kiểm tra quyền tải, khách đổi chủ, note INTERNAL, thu hồi file, ô nháp và rerun. GridFS/Drive chỉ theo cấu hình runtime, **không mặc định Drive**.
- Bản gốc PR #234 là patch `7roger89-web/CHUNLI@arena/5bc30481-chunli/logi/journey-notes/` với **7/7 Git blob SHA khớp byte-exact**; `31 PASS` của bản gốc chỉ là bối cảnh lịch sử.
- **QA trên HEAD mới (30/10):** `arena/6db41d2f-logistics-work-desk-arena` commit `2e510d50f2ec58284f4e3e8a74b1ea2bb42811e0` chạy thật: `tests/test_journey_notes.py` **48 PASS** (36 cũ + 12 mới), tập G1/G1.5 phụ thuộc **138 PASS**, full suite **34 failed / 2197 passed / 44 skipped** — trùng đúng tập FAILED nền 34 của `f80b2bd`, +12 test mới đều PASS. Ba mutation proof (stage draft, flash/rerun, recheck chủ lô) đều FAIL đúng chỗ. Bằng chứng: `evidence/journey-notes/session-qa-20261030.md`.

## CURRENT

**Chốt xong PR #234 ở mức code staging.** Việc nghiệp vụ tiếp theo là khiến Journey Map thực sự dễ dùng: chọn trực tiếp mốc hành trình → mở trao đổi/chứng từ **đúng lô và mốc đó**, tái dùng backend đã có, không viết lại persistence. Hiện comment là pane Streamlit **bên dưới bản đồ** chứ chưa tích hợp vào modal/node React. Cloud deployed SHA, DB identity và Google OIDC thật vẫn chưa xác minh; merge code không đồng nghĩa app đang chạy đã có chức năng.

## NEXT — công việc kế tiếp có giá trị

1. **Map-first nhỏ nhất:** điều khiển chọn 1 node Journey Map phải định vị/mở đúng pane trao đổi/chứng từ của **chính lô và công đoạn đó** (reuse `core/journey_notes.py` + `views/journey_discussion.py`). Không tạo hệ thống comment thứ hai; không hiển thị note `INTERNAL` cho khách. Test desktop/mobile, đổi khách, 0/1/2 lô và reset nháp; chỉ phát triển sau khi đo lại staging HEAD và xác minh binding thật giữa component và Streamlit.
2. **UAT staging an toàn:** trước bất kỳ thao tác ghi Cloud, đọc/kiểm chứng deployed SHA và danh tính DB của `thu-log-g1-test.streamlit.app` bằng cách không tiết lộ secret. Nếu chưa xác minh, giữ `CLOUD_QA=BLOCKED`, tiếp tục QA với dữ liệu giả cô lập. Test Trường Thành gửi → Lục Giác xem/trả lời → reload/download, nguồn đã duyệt và Google OIDC thật khi điều kiện cho phép.
3. Sau UAT, mới quyết định mở tính năng kế hoạch/thanh toán/công nợ; tránh lặp lại G1.5/#232/#234 và không đưa `main`/production vào luồng này khi chưa có Owner Gate.

## BLOCKERS / GATES

- PR #234 đã **MERGED staging**. Bằng chứng code: QA Arena `48 PASS` stage notes, `138 PASS` tests phụ thuộc; full suite còn **34 lỗi nền** theo cùng máy/baseline. Control Tower đọc lại code/test trên HEAD QA và không thấy blocker mới; các test không được chạy lại trong container hiện tại (thiếu Streamlit/mongomock).
- `thu-log-g1-test.streamlit.app`: deployed SHA và danh tính DB runtime chưa được chứng minh; **không ghi Cloud/production** chỉ để test.
- Nguồn chứng từ/sự kiện Lục Giác thật chưa được nghiệp vụ xác nhận; hash/fixture chỉ chứng minh contract phần mềm. Thông tin chi phí, margin, báo giá nội bộ và công nợ thiếu đối soát tuyệt đối không công bố.
- `main` trước công việc này: `9e4190b278dd2ced8771c5249582753d34e561db`; không merge `main` hoặc deploy production nếu thiếu Owner Gate. PR #226 lịch sử Draft, không phải workstream tiếp theo.

## SUCCESS CHECKS

- Staff có `shipment_edit` ghi/xem INTERNAL và CUSTOMER; khách chỉ ghi/xem CUSTOMER đúng lô và công đoạn.
- Upload file qua kho đang có; download xác minh lại note, khách, quyền, lô **hiện tại**, tệp và trạng thái AVAILABLE. Không lộ GridFS ID/hash/link nội bộ.
- Sau reload/đổi khách, không còn dữ liệu hay bản nháp của khách trước; test trên code commit `2e510d5` được QA báo PASS và cùng code blob đã merge staging. Cần UAT Cloud riêng trước phát hành.
- Mọi phát hành/live UAT tách biệt việc merge code; không tự nhận app production đã có chức năng.

## Nhật ký mốc quan trọng

- **30/10:** PR #233 merged staging; PR #232 có independent challenge và merged staging tại `e75a239`.
- **30/10:** Patch comment/chứng từ từ CHUNLI áp dụng byte-exact lên nhánh cô lập; thêm bảo vệ đọc/tải lô đã chuyển chủ, tệp thu hồi và bản nháp đổi khách; PR #234 Draft chờ chạy test sau sửa.
- **30/10 (QA thực chạy):** 48 PASS `test_journey_notes.py`, 138 PASS tập G1.5 phụ thuộc, full suite 34F/2197P/44S trùng baseline; sửa 3 lỗi UI (nháp lẫn công đoạn, gửi xong chưa thấy note, nhãn tệp chưa escape) tại `2e510d5`; Cloud QA vẫn `BLOCKED`.

- **30/10 (staging integration):** Control Tower fast-forward patch QA Arena vào PR #234 HEAD `cc9f9a7ae50abe9244ae2a457e5e3dbcb31bcc5a`, kiểm tra nguồn/test/20 điều kiện an toàn, merge **staging** ở `0e20a93c48f95b76839c093c9cb56bfcb1472e5f`; `main` giữ nguyên. Cloud UAT vẫn BLOCKED vì runtime SHA/DB chưa xác minh.

**Duy trì:** chỉ cập nhật CURRENT/NEXT/BLOCKERS và một mốc PR/SHA khi việc thực sự đổi. Không log từng thao tác, không dựng bảng roadmap khác.