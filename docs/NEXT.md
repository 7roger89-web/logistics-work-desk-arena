# NEXT — Logistics Work Desk | checkpoint mục tiêu đang hoạt động

> SNAPSHOT, KHÔNG PHẢI LUẬT. Cập nhật: **2026-10-30 (Asia/Bangkok)**. Repository bắt buộc: `7roger89-web/logistics-work-desk-arena`.
> Đọc `AGENTS.md` và Supreme Law trước. GoalPlan/TaskPlan đang được duyệt, yêu cầu Owner mới nhất và GitHub refs/bằng chứng mới hơn luôn thắng snapshot này. **Không suy SHA đang chạy trên Streamlit Cloud từ Git branch.**

## GOAL — kết quả Owner muốn

Xây **Logistics Work Desk có thể sử dụng thật**, tập trung giao diện Journey Map đơn giản: Trường Thành (Support/Sale) nhìn một lô là biết **đang ở đâu, đang vướng gì, làm gì tiếp, chứng từ nào cần xử lý**; Lục Giác đăng nhập để xem **đúng lô, mốc và chứng từ Trường Thành đã duyệt công bố**. Không biến QA, review prompt, báo cáo hoặc bổ sung framework thành mục tiêu thay thế cho phát triển sản phẩm.

## PROGRESS — đã xác minh tại thời điểm checkpoint

- **Đúng repo:** `7roger89-web/logistics-work-desk-arena`; checkout `logistics-work-desk` khác là sai đích.
- **Staging branch:** `arena/ae5f9f47-logistics-work-desk-arena` tại `b02c6db50180a7f811189cb101c575defdee6652` (GitHub branch, **không phải bằng chứng deployed SHA**).
- **PR [#231](https://github.com/7roger89-web/logistics-work-desk-arena/pull/231):** đã merged vào nhánh staging; sửa luồng lưu/readback thông tin lô. Nghiệm thu thao tác trên Cloud còn thiếu bằng chứng.
- **PR [#226](https://github.com/7roger89-web/logistics-work-desk-arena/pull/226):** Draft, HEAD `9978e0a6ee120e8de2ea4838aa2c8e23746663f9`; phần *đọc* event/document theo customer_id và manifest PUBLISHED, pinned ID/version đã có trong source. Chưa chứng minh test runtime tại HEAD này và chưa tích hợp staging.
- **PR [#232](https://github.com/7roger89-web/logistics-work-desk-arena/pull/232):** nhắm staging, đã nhận bản sửa bảo mật và các test từ nhánh Arena QA bằng fast-forward không force; **Draft sau phát hiện lỗi toàn vẹn nội dung**, chưa merge staging. SHA code QA mốc `dd1c63d94024caeff76fef0699179c3cc38d7f6e`; HEAD cuối phải đo lại. Đã có focused pytest 143 PASS trên môi trường mongomock + browser giả lập, không chứng minh đăng nhập Google/Cloud thật. PR #226 vẫn Draft, chưa thay đổi.
- **PR [#232] reviewed độc lập (2026-10-30, actor khác tác giả fix):** reviewer khác chạy focused G1/G1.5 tại HEAD `968e7cf` trên pymongo/mongomock + Streamlit thật: **186 PASS**, gồm 29 test challenge mới (`tests/test_customer_portal_g15_independent_challenge.py`) và đột biến tắt kiểm tra hash nội dung làm **25 test FAIL** (bằng chứng test không rỗng). Sửa 1 test hồi quy thật tại HEAD: `test_owner_granted_publication_fields_reach_the_ui_without_scope_change` giờ tạo bản công bố qua Admin publisher thật. Full suite cùng lệnh: 38F/2115P (trước) → **35F/2148P** (sau), không có lỗi mới. Bằng chứng: `evidence/g15-independent-review/README.md`. `CLOUD_QA=BLOCKED` vẫn đứng.
- **`main` tham chiếu:** `9e4190b278dd2ced8771c5249582753d34e561db`. **Không được tự merge/deploy production**; đây chỉ là ref tại thời điểm quan sát.

## QA follow-up — bản sửa đã fast-forward vào PR #232

- 2026-10-30: bản PR #232 trước sửa `b67f306d44650c4f039e2b1275941e0e7e597c48` có lỗi hiển thị modal khách trước khi đổi model trong cùng trang. Chromium và kiểm thử hồi quy tái hiện; bằng chứng tại `evidence/g15-followup-qa/README.md`.
- **Đã tháo chặn quyền nhánh:** nhánh QA là hậu duệ trực tiếp của PR #232 (`ahead 3, behind 0`); Control Tower fast-forward **không force** PR #232 lên `dd1c63d94024caeff76fef0699179c3cc38d7f6e`. Bản sửa `c2ba70b` và test/ảnh đã **nằm trong PR #232**. PR đã **trở lại Draft** để sửa và nghiệm thu lỗi mới; chưa merge staging.
- QA cục bộ trên nhánh QA: pytest G1/G1.5 **143 PASS** ở cây ứng dụng trước commit định dạng test; Chromium với dữ liệu/danh tính giả kiểm chứng công bố/reload/Journey/đổi khách; Viewer gọi backend bị từ chối và không đổi dữ liệu. Full suite còn các lỗi nền và một test thay đổi tập FAIL, cần đối chiếu log từng lần chạy (`README.md` ghi 2110 PASS/35 FAIL, báo cáo phiên nêu 2111 PASS/34 FAIL). Đây không phải PASS toàn bộ. Chưa có test thực thi trong môi trường Cloud/Google OIDC/Mongo thật.
- `CLOUD_QA=BLOCKED`: chưa chứng minh deployed SHA và DB identity an toàn; không ghi Cloud, production hay dữ liệu thật.

## CURRENT — phạm vi phát triển đang mở

**G1.5 / PR #232 — kiểm chứng bản sửa chống thay đổi nội dung sau công bố, rồi review độc lập trên staging**, tái sử dụng nguồn và giao diện đang có. Phân biệt ba lớp nghiệm thu: (1) code/test với fixture; (2) tính đầy đủ, tính đúng của manifest/provenance nghiệp vụ được duyệt; (3) trải nghiệm khách hàng tại runtime thật. PASS lớp này không đồng nghĩa PASS lớp khác.

## NEXT — bước có giá trị lớn nhất (một lát chức năng)

1. **PR #232 đang Draft với fix hash nội dung công khai** (mốc code `db9015e60b2621fb5aae154caa20bf2bb42930c4`). Chạy focused pytest gốc (PyMongo/mongomock), thử lại tình huống `E/v1` sửa tiêu đề sau duyệt vẫn giữ version và chứng từ sửa metadata, xác nhận card bị ẩn; test DOM 0/1/2 lô và luồng Admin → khách vẫn PASS. Reviewer **khác tác giả bản sửa** đánh giá chính HEAD sau QA, không vòng prompt review khác.
2. Kiểm tra dữ liệu giả cô lập: đúng khách, khác khách, chưa công bố, sai version, người xem gửi lệnh ghi bị backend từ chối. Kiểm chứng nguồn nghiệp vụ được xác minh, không biến fixture PASS thành chứng nhận dữ liệu thật. Chỉ tích hợp staging sau review độc lập/QA đầy đủ. Nếu Cloud thiếu SHA hoặc DB identity thì Cloud QA BLOCKED, không chặn test cô lập.
3. Khi luồng công bố G1.5 có bằng chứng và đã tích hợp staging, chuyển sang **trao đổi/comment + đính chứng từ theo công đoạn**. Nguồn sự kiện/chứng từ thật cần nhập/xác minh và duyệt bởi nghiệp vụ trước khi công bố; không giả định có sẵn. Kế hoạch/thanh toán/công nợ là các lát sau, không trộn vào PR #232.

- **2026-10-30 (security fix mới):** Review thực thi phát hiện cùng ID/version nhưng sửa `public_title` nguồn làm khách thấy nội dung chưa duyệt; tái hiện với mongomock (bằng chứng từ reviewer, chưa có independent verdict). PR #232 bổ sung `approved_content_sha256` của **allowlist công khai** khi Admin công bố; reader so lại trên từng lượt tải và từ chối nếu thiếu hash ở manifest có pin hoặc nội dung khác. Commit code `db9015e60b2621fb5aae154caa20bf2bb42930c4`. Hai module hash/publisher byte-exact đã qua **37/37 phép thử backend cô lập fake Mongo**, chưa chạy pytest repo mới/Google/Cloud. PR chuyển lại Draft chờ kiểm chứng/challenge độc lập.

## BLOCKERS / GATES — đừng biến thành vòng lặp

- **Lịch sử trước security fix:** focused pytest 143 PASS và Chromium/Streamlit với **mongomock, OIDC giả lập**; không bao gồm kiểm tra cùng version bị sửa nội dung. **PR hiện Draft** sau fix `db9015e`. Pytest gốc cho HEAD mới, independent reviewer và Cloud/browser thực tế chưa nghiệm thu; full suite còn baseline failures. 27/27 và 37/37 fake DB không thay thế focused pytest repo.
- Chưa có chứng cứ `CLOUD_DEPLOYED_HEAD` và DB identity của ứng dụng `thu-log-g1-test.streamlit.app`: **cấm ghi Cloud để thử QA** khi chưa xác thực runtime an toàn. Nếu bị chặn, ghi `BLOCKED` cho riêng Cloud QA và tiếp tục công việc phát triển/test cô lập.
- Dữ liệu công bố thật cho Lục Giác chưa được xác minh; **không tự tạo manifest PUBLISHED thật hoặc coi fixture là nghiệm thu nghiệp vụ**.
- Chính sách Owner 5C: không lộ báo giá tiền, chi phí, margin, ghi chú nội bộ, GridFS bytes/download; báo giá khách chỉ là metadata tệp được duyệt; công nợ thiếu đối soát = UNKNOWN.
- **Main merge có thể kích hoạt production**; không merge main, deploy hay động dữ liệu production khi không có Owner Gate.
- Cấm tự biến yêu cầu phát triển thành một vòng độc lập chỉ viết prompt/QA/review hoặc cải tổ kiến trúc, trừ khi đó là blocker thật của lát đang làm.

## SUCCESS CHECKS

- Trường Thành có thể tạo/chọn, duyệt và công bố *đúng* event/document phiên bản được phép trên dữ liệu thử.
- Lục Giác chỉ xem lô/phiên bản của mình; unpublished, foreign tenant, dữ liệu nội bộ không lộ. Journey UNKNOWN khi thiếu chứng cứ đã duyệt.
- Có code, test và bằng chứng đúng commit; PR tiến về trạng thái sẵn sàng review/tích hợp staging. `main`/production vẫn nguyên vẹn.

## Nhật ký mốc (chỉ ghi khi có tiến độ hay blocker làm thay đổi bước kế tiếp)

- **2026-10-26 (lịch sử):** `main/docs/NEXT.md` từng ghi baseline 18 test đỏ và hướng điều tra; **không còn là ưu tiên sản phẩm hiện hành**. Số test trong đó là số đo lịch sử, không phải baseline hôm nay.
- **2026-10-29:** #231 merged staging tại `b02c6db`; #226 vẫn Draft `9978e0a`; Cloud/browser và nghiệp vụ thật chưa được chứng minh.
- **2026-10-30:** Owner xác nhận phải ưu tiên phát triển sản phẩm, không tiếp tục vòng QA/review prompt lặp lại. Tạo checkpoint này để các AI khác tiếp tục đúng việc.
- **2026-10-30 (mốc phát triển):** PR #232 chuyển khỏi `main` sang staging, tích hợp base `b02c6db` và thu gọn còn 12 file; bổ sung Admin publisher/Streamlit UI/test tại `1a16b4d`. Source-bound guards có; QA runtime của HEAD mới chưa có, không merge/deploy.

- **2026-10-30 (QA cô lập):** các bản sao ba module GitHub được đối chiếu Git blob SHA chính xác; 27/27 kiểm thử logic publisher trên fake DB nội bộ đã PASS. Giới hạn: không chứng minh PyMongo/mongomock thật, UI, OIDC hoặc Cloud; PR #232 vẫn Draft, chưa merge.

- **2026-10-30 (integration):** Control Tower fast-forward `b67f306d` → `dd1c63d` (không force) để nhận sửa bảo mật/test từ Arena QA; chuyển PR #232 sang **Ready for independent review**. Chưa có independent PASS, chưa merge staging, main và production giữ nguyên.

- **2026-10-30 (integrity):** Reviewer giả lập phát hiện same-version mutation, kết luận REJECT. Fix hash content tại `db9015e60b2621fb5aae154caa20bf2bb42930c4` trên PR #232; offline 37/37 PASS, pytest repo và review độc lập sau fix chưa có. **Không merge staging/main**.

- **2026-10-30 (independent review PASS):** actor khác tác giả fix nghiệm thu HEAD `968e7cf` bằng focused suite + rerender Streamlit + đột biến; sửa 1 test hồi quy và thêm 29 challenge test. PR #232 đủ điều kiện tích hợp **staging**; `main`/production giữ nguyên, `CLOUD_QA=BLOCKED` (deployed SHA + DB identity chưa xác minh). Bắt đầu lát tiếp theo: **comment + chứng từ theo công đoạn Journey** trên nhánh phụ thuộc #232.

**Hướng dẫn duy trì:** Trước khi chọn task, so mục tiêu Owner + GoalPlan/TaskPlan với GitHub thực tế và checkpoint này. Chỉ cập nhật GOAL/CURRENT/NEXT/BLOCKERS và append **một dòng mốc có PR/SHA/bằng chứng** khi kết quả hoặc ưu tiên thực sự đổi. Không ghi nhật ký mỗi lệnh; không tự nhận đã cập nhật nếu chưa commit thành công.
