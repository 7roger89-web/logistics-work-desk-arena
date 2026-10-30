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
- **`main` tham chiếu:** `9e4190b278dd2ced8771c5249582753d34e561db`. **Không được tự merge/deploy production**; đây chỉ là ref tại thời điểm quan sát.

## CURRENT — phạm vi phát triển đang mở

**G1.5 / PR #226 — hoàn thiện một luồng Trường Thành → Lục Giác**, tái sử dụng nguồn và giao diện đang có. Phân biệt ba lớp nghiệm thu: (1) code/test với fixture; (2) tính đầy đủ, tính đúng của manifest/provenance nghiệp vụ được duyệt; (3) trải nghiệm khách hàng tại runtime thật. PASS lớp này không đồng nghĩa PASS lớp khác.

## NEXT — bước có giá trị lớn nhất (một lát chức năng)

1. Đo lại PR #226 và staging; **khảo sát những bước công bố đã tồn tại** trước khi viết thêm. Hoàn thiện phần còn thiếu cho luồng: Trường Thành chọn đúng lô + sự kiện/chứng từ → người có quyền duyệt và công bố phiên bản cụ thể → Lục Giác chỉ xem những mục đã công bố trên Journey.
2. Dùng dữ liệu giả cô lập, kiểm tra tối thiểu **một lô đúng khách, một lô khác khách, một bản chưa công bố và một bản sai version**; kiểm chứng qua source/backend/UI thích hợp. Không seed, duyệt hoặc thay đổi dữ liệu khách thật.
3. Khi lát chức năng này chạy được và có bằng chứng, mới chuyển sang **trao đổi/comment + đính chứng từ theo công đoạn** cho hai bên. Kế hoạch, thanh toán tiền hàng và công nợ lô là các lát tiếp theo; không trộn vào PR #226 lúc này.

## BLOCKERS / GATES — đừng biến thành vòng lặp

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

**Hướng dẫn duy trì:** Trước khi chọn task, so mục tiêu Owner + GoalPlan/TaskPlan với GitHub thực tế và checkpoint này. Chỉ cập nhật GOAL/CURRENT/NEXT/BLOCKERS và append **một dòng mốc có PR/SHA/bằng chứng** khi kết quả hoặc ưu tiên thực sự đổi. Không ghi nhật ký mỗi lệnh; không tự nhận đã cập nhật nếu chưa commit thành công.
