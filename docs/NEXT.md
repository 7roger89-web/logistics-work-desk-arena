# NEXT — Logistics Work Desk | checkpoint mục tiêu

> Cập nhật **30/10/2026**. Đây là snapshot để tiếp tục làm sản phẩm, không phải luật. Đọc `AGENTS.md` + Supreme Law trước; đo lại GitHub PR/HEAD trước khi dùng SHA lịch sử. Yêu cầu Owner mới nhất và GoalPlan/TaskPlan hiệu lực có ưu tiên cao hơn bản này.

## GOAL

Hoàn thiện **Logistics Work Desk thực sự dùng được**: Trường Thành nhìn Journey của một lô biết đang ở đâu, vướng gì, cần làm gì, chứng từ nào; Lục Giác xem duy nhất tiến độ/chứng từ đã được Trường Thành duyệt và trao đổi theo **đúng công đoạn**. Đơn giản, map-first; không thay phát triển chức năng bằng vòng viết prompt, QA hình thức hay framework mới.

## PROGRESS — mốc đã xác minh

- Repo đúng: `7roger89-web/logistics-work-desk-arena`.
- [PR #233](https://github.com/7roger89-web/logistics-work-desk-arena/pull/233): **MERGED** vào staging; `AGENTS.md` bắt buộc đọc checkpoint hiện tại.
- [PR #232](https://github.com/7roger89-web/logistics-work-desk-arena/pull/232): **MERGED vào staging** ở `e75a239277573f0d470607818e40b8d11f775e44`. Có Admin duyệt công bố event/document theo ID, version và hash nội dung, customer-only reader; fix modal giữ dữ liệu khi đổi khách. Bằng chứng review độc lập 29 challenge tests và focused suite ghi tại `evidence/g15-independent-review/README.md`. **G1.5 đạt code-level staging, chưa chứng minh Google OIDC và dữ liệu nghiệp vụ Lục Giác thật**.
- **Đang làm:** [PR #234](https://github.com/7roger89-web/logistics-work-desk-arena/pull/234), nhánh `ct/logi-journey-discussion-20261030`, **Draft**. Tái sử dụng `quick_notes` + adapter `core/inbox_attachments` để ghi comment và chứng từ theo `customer_id + shipment_id + stage_id` (7 node giống `core/customer_journey.STAGE_IDS`). Hai phía có pane Streamlit: chi tiết lô Trường Thành và dưới Journey Map Lục Giác. File lưu theo runtime GridFS/Drive đang cấu hình; **không mặc định Drive**.
- Bản gốc PR #234 là patch `7roger89-web/CHUNLI@arena/5bc30481-chunli/logi/journey-notes/` với **7/7 Git blob SHA khớp byte-exact**; executor báo `31 PASS` mongomock/AppTest cho bản gốc và 3 mutation proofs. Đã bổ sung guard trên nhánh hiện tại: kiểm tra **chủ lô hiện tại** trước khi đọc/tải; thu hồi tệp; widget nhập tách riêng theo khách+lô; mới nhất 200 comment. **Test bổ sung chưa chạy trên HEAD cuối**.

## CURRENT

**Chốt PR #234 trên staging**: làm comment và chứng từ ở một công đoạn bằng hai quyền, không trộn thêm công nợ, kế hoạch hay redesign Journey. UI comment hiện là pane bên dưới bản đồ, **không được khẳng định đã nối vào node/modal React `stage_comments`**.

## NEXT — công việc kế tiếp có giá trị

1. Đo lại HEAD PR #234. Chạy `python -m pytest -q tests/test_journey_notes.py` cùng tập G1/G1.5 phụ thuộc và AppTest. Bắt buộc thử **khách/lô bị chuyển chủ hoặc xóa, note INTERNAL, download sai tệp, tệp REVOKED, thay principal cùng session, >200 comment, quá 4 tệp**. Kiểm thử hành trình gửi → reload → đọc lại. Nếu lỗi thuộc diff, sửa trong **cùng PR** rồi chạy lại; không mở prompt/framework mới.
2. Reviewer độc lập kiểm tra phân quyền/tenant/file và bằng chứng commit cuối. Nếu đạt, merge **staging** theo gate đang có; tuyệt đối không kéo `main`/production theo.
3. Sau khi staging có code, UAT trên môi trường **đã xác minh deployed SHA + DB identity** với dữ liệu được phép. Nếu Cloud chưa xác thực, `CLOUD_QA=BLOCKED`, không ghi dữ liệu thật. Sau đó mới quyết định có cần nhúng comment trực tiếp vào node/modal React thay pane hay không.

## BLOCKERS / GATES

- PR #234 hiện **chưa có pytest/Streamlit QA và review độc lập cho các guard bổ sung trên HEAD cuối**. Chưa đủ điều kiện merge staging; không được mượn 31 PASS của commit gốc làm kết quả của code mới.
- `thu-log-g1-test.streamlit.app`: deployed SHA và danh tính DB runtime chưa được chứng minh; **không ghi Cloud/production** chỉ để test.
- Nguồn chứng từ/sự kiện Lục Giác thật chưa được nghiệp vụ xác nhận; hash/fixture chỉ chứng minh contract phần mềm. Thông tin chi phí, margin, báo giá nội bộ và công nợ thiếu đối soát tuyệt đối không công bố.
- `main` trước công việc này: `9e4190b278dd2ced8771c5249582753d34e561db`; không merge `main` hoặc deploy production nếu thiếu Owner Gate. PR #226 lịch sử Draft, không phải workstream tiếp theo.

## SUCCESS CHECKS

- Staff có `shipment_edit` ghi/xem INTERNAL và CUSTOMER; khách chỉ ghi/xem CUSTOMER đúng lô và công đoạn.
- Upload file qua kho đang có; download xác minh lại note, khách, quyền, lô **hiện tại**, tệp và trạng thái AVAILABLE. Không lộ GridFS ID/hash/link nội bộ.
- Sau reload/đổi khách, không còn dữ liệu hay bản nháp của khách trước. Regression test trên **exact HEAD** pass, có reviewer độc lập, staging tích hợp.
- Mọi phát hành/live UAT tách biệt việc merge code; không tự nhận app production đã có chức năng.

## Nhật ký mốc quan trọng

- **30/10:** PR #233 merged staging; PR #232 có independent challenge và merged staging tại `e75a239`.
- **30/10:** Patch comment/chứng từ từ CHUNLI áp dụng byte-exact lên nhánh cô lập; thêm bảo vệ đọc/tải lô đã chuyển chủ, tệp thu hồi và bản nháp đổi khách; PR #234 Draft chờ chạy test sau sửa.

**Duy trì:** chỉ cập nhật CURRENT/NEXT/BLOCKERS và một mốc PR/SHA khi việc thực sự đổi. Không log từng thao tác, không dựng bảng roadmap khác.