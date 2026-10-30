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
- **PR [#232](https://github.com/7roger89-web/logistics-work-desk-arena/pull/232):** đã chuyển từ `main` sang staging, tích hợp lịch sử staging không force. HEAD `1a16b4d7d40922af8b4ab7fef63766090523f11b`, Draft; đã thêm backend Admin công bố phiên bản và UI chọn nguồn, test mới **chưa chạy**. 12 file thay đổi so với staging. PR #226 vẫn Draft, giữ nguyên và đang chồng lấn logic reader.
- **`main` tham chiếu:** `9e4190b278dd2ced8771c5249582753d34e561db`. **Không được tự merge/deploy production**; đây chỉ là ref tại thời điểm quan sát.

## QA follow-up — bản sửa đã fast-forward vào PR #232

- 2026-10-30: bản PR #232 trước sửa `b67f306d44650c4f039e2b1275941e0e7e597c48` có lỗi hiển thị modal khách trước khi đổi model trong cùng trang. Chromium và kiểm thử hồi quy tái hiện; bằng chứng tại `evidence/g15-followup-qa/README.md`.
- **Đã tháo chặn quyền nhánh:** nhánh QA là hậu duệ trực tiếp của PR #232 (`ahead 3, behind 0`); Control Tower fast-forward **không force** PR #232 lên `dd1c63d94024caeff76fef0699179c3cc38d7f6e`. Bản sửa `c2ba70b` và test/ảnh đã **nằm trong PR #232**. PR vẫn Draft; chưa merge staging.
- QA cục bộ trên nhánh QA: pytest G1/G1.5 **143 PASS** ở cây ứng dụng trước commit định dạng test; Chromium với dữ liệu/danh tính giả kiểm chứng công bố/reload/Journey/đổi khách; Viewer gọi backend bị từ chối và không đổi dữ liệu. Full suite còn các lỗi nền và một test thay đổi tập FAIL, cần đối chiếu log từng lần chạy (`README.md` ghi 2110 PASS/35 FAIL, báo cáo phiên nêu 2111 PASS/34 FAIL). Đây không phải PASS toàn bộ. Chưa có test thực thi trong môi trường Cloud/Google OIDC/Mongo thật.
- `CLOUD_QA=BLOCKED`: chưa chứng minh deployed SHA và DB identity an toàn; không ghi Cloud, production hay dữ liệu thật.

## CURRENT — phạm vi phát triển đang mở

**G1.5 / PR #232 — tiếp tục kiểm chứng độc lập luồng Admin Trường Thành → Lục Giác trên staging**, tái sử dụng nguồn và giao diện đang có. Phân biệt ba lớp nghiệm thu: (1) code/test với fixture; (2) tính đầy đủ, tính đúng của manifest/provenance nghiệp vụ được duyệt; (3) trải nghiệm khách hàng tại runtime thật. PASS lớp này không đồng nghĩa PASS lớp khác.

## NEXT — bước có giá trị lớn nhất (một lát chức năng)

1. **PR #232 đã có bản sửa chống lộ dữ liệu khi đổi principal.** Đo lại HEAD hiện tại, kiểm chứng độc lập chính **diff 3 commit QA** và chạy/đối chiếu focused pytest + DOM regression trên HEAD PR sau fast-forward (đặc biệt `tests/component/dom_acceptance_g15_tenant_reset.mjs`). Fix lỗi trong cùng PR, không mở PR khác.
2. Kiểm tra dữ liệu giả cô lập: đúng khách, khác khách, chưa công bố, sai version, người xem gửi lệnh ghi bị backend từ chối. Kiểm chứng nguồn nghiệp vụ được xác minh, không biến fixture PASS thành chứng nhận dữ liệu thật. Chỉ tích hợp staging sau review độc lập/QA đầy đủ. Nếu Cloud thiếu SHA hoặc DB identity thì Cloud QA BLOCKED, không chặn test cô lập.
3. Khi luồng công bố G1.5 có bằng chứng và đã tích hợp staging, chuyển sang **trao đổi/comment + đính chứng từ theo công đoạn**. Nguồn sự kiện/chứng từ thật cần nhập/xác minh và duyệt bởi nghiệp vụ trước khi công bố; không giả định có sẵn. Kế hoạch/thanh toán/công nợ là các lát sau, không trộn vào PR #232.

## BLOCKERS / GATES — đừng biến thành vòng lặp

- **Đã có QA thực thi trên nhánh QA ancestor của PR #232:** focused pytest 143 PASS và Chromium/Streamlit với **mongomock, OIDC giả lập**; đã fast-forward nguyên ancestry QA vào PR. Chưa có QA độc lập trên exact HEAD PR sau cập nhật tài liệu; full-suite baseline còn lỗi, business provenance/Google OIDC/Cloud QA chưa nghiệm thu. Kết quả 27/27 trên fake DB tối giản là mốc lịch sử, **không thay thế** kiểm thử repo.
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

**Hướng dẫn duy trì:** Trước khi chọn task, so mục tiêu Owner + GoalPlan/TaskPlan với GitHub thực tế và checkpoint này. Chỉ cập nhật GOAL/CURRENT/NEXT/BLOCKERS và append **một dòng mốc có PR/SHA/bằng chứng** khi kết quả hoặc ưu tiên thực sự đổi. Không ghi nhật ký mỗi lệnh; không tự nhận đã cập nhật nếu chưa commit thành công.
