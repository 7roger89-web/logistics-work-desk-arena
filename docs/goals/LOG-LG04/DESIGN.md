# LOG-LG04 DESIGN — Daily Work Simplification & Input-First UX

Nguyên tắc: **HÀNH ĐỘNG TRƯỚC — THAM KHẢO SAU — KIỂM TOÁN CUỐI**. Không rebuild kiến trúc; sửa UI layer và read-model nhẹ; mọi nghiệp vụ, quyền, audit, UNKNOWN giữ nguyên.

## Pilot scope (T2/T3/T4/T5/T6 trong 1 pilot màn hình lô hàng)

### W1 — Next Action nổi bật (Ý 3 complaint)
File: `views/shipment_360.py` + helper mới `core/next_action_card.py`.
- Thay dòng `st.warning/success/info NEXT ACTION` + caption bằng **CARD VIỆC TIẾP THEO**: viền màu theo mức độ (đỏ/cam/xanh dương/xám), icon, tiêu đề "Việc tiếp theo", 3 dòng: Việc gì — Vì sao — Ai làm, nút "Xử lý ngay" cuộn thẳng đến khối nhập liên quan.
- KHÔNG dùng màu duy nhất: kèm viền dày + icon + chữ in đậm + mũi tên chỉ khối.

### W2 — 3 thẻ việc chính ở trên đầu màn hình lô (Ý 1)
Ngay sau card Việc tiếp theo, 3 thẻ border lớn:
1. "🚛 Lấy hàng & Xuất khẩu" → anchor nhảy đến tab PICKUP & XUẤT KHẨU (cuộn tới tab + mở tab).
2. "🛃 Nhập khẩu & Giao hàng" → anchor tab IMPORT & GIAO HÀNG.
3. "💰 Chi phí & Công nợ" → anchor tab FINANCE.
Mỗi thẻ kèm trạng thái rút gọn (vd: "ETD 25/08 · chưa có MBL" từ dữ liệu shipment) lấy từ `build_shipment_workspace_view` (không tạo nguồn dữ liệu mới — chỉ đọc field hiện có).

### W3 — Thu gọn khối đọc (Ý 2, 4, 5, 6, 8)
- "👥 Khách hàng · nhà máy · pickup · delivery" → đổi tên "👥 Ai tham gia lô hàng này" + 1 câu giải thích "Thông tin liên hệ các bên để lấy hàng/giao hàng" + rút còn 1 bảng 2 cột gọn + 1 nút "Xem hồ sơ đối tác" (expander phụ chứa 3 nút 360 cũ).
- Factory lots: khi UNKNOWN → không hiện (tránh "Cẩn số xem trị" khó hiểu). Khi có → giữ như cũ nhưng đổi tên "🏭 Hàng từ nhà máy".
- Documents fallback 5 cột → rút thành danh sách 1 dòng mỗi chứng từ: "Tờ khai hải quan · CÓ/KHÔNG" + nút mở chi tiết khi cần.
- Alert "Quá free time" → đưa vào card Việc tiếp theo (free-time sắp hết = việc tiếp theo) thay vì dòng caption nhỏ.
- Lịch sử/audit: giữ nguyên (expander đóng mặc định).

### W4 — Tài chính input-first (Ý 7)
Tab FINANCE thứ tự mới:
1. "Nhập chi phí & doanh thu" (form dịch vụ đang có — kẻ khung border cho mỗi dòng) trên cùng.
2. Tóm tắt công nợ (thẻ metric) sau đó.
3. "Chi tiết đối soát & lịch sử" (bảng kê tài chính + lịch sử thu tiền) cuối.
Không tạo nguồn chân lý mới — cùng field `d['3.4']`, cùng `apply_financial_snapshot`.

### W5 — Form báo giá dễ đọc (Ý 9)
File: `views/quotations.py`:
- Mỗi dòng dịch vụ: border container, nhãn đầy đủ thay vì "S/Q/In/Out/V", các ô kẻ rõ.
- Phân tầng: nhóm "Thông tin chính" (khách, ngày, dịch vụ, giá vốn, giá bán, thuế) hiện ngay; nhóm "Nâng cao" (tỷ giá USD/CNY, nguồn FX, giá trị hàng, phí ngân hàng, SWIFT, ủy thác) đưa vào 1 expander "📐 Cài đặt nâng cao (tỷ giá & thanh toán)".
- Không bỏ trường bắt buộc nghiệp vụ.

### W6 — Luồng Báo giá → Thỏa thuận → Bàn giao rõ nghĩa (Ý 10)
File: `views/agreements.py`:
- Tab thứ tự: "1. Danh sách thỏa thuận" / "2. Tạo từ báo giá khách chốt" / "3. Chi tiết & Bàn giao".
- Thêm thanh tiến trình 4 bước bằng tiếng Việt thường: Báo giá → Khách chốt → Thỏa thuận → Support vận hành, với chú thích mỗi bước 1 câu.
- Đổi "Bàn giao vận hành — 16 câu hỏi" → "Kiểm tra đủ thông tin cho Support" + câu giải thích "Đây là danh mục thông tin Support cần có để vận hành lô hàng. Chấm dứt khi đủ."
- "Tạo thỏa thuận DRAFT giữ nguyên snapshot" → giải thích 1 câu: "Tạo bản thỏa thuận chốt lại điều khoản tại thời điểm chốt; sau này sửa sẽ tạo bản mới, không làm mất bản đã đồng ý."

## Bảo toàn (kiểm tra T10)
- Permission: chỉ Support/admin vào input lô hàng; Sale vào báo giá — không thay permission nào.
- Finance: KHÔNG thêm write path mới; 0 financial mutation từ commercial flow.
- UNKNOWN != ZERO giữ nguyên trong mọi card (card chỉ hiển thị "chưa có").
- RBAC oracle + finance write oracle + full suite 217/0/28.

## Đo trước-sau (T11 evidence)
Lấy 1 lô hàng thật (read-only, lô có đủ dữ liệu trong production): đếm số lần cuộn/màn hình/thao tác trước-sau cho 2 kịch bản Support & Sale beginner.

## Data
- Production: CHỈ ĐỌC (`logistics_db`), snapshot read-only để lấy 1 lô pilot hiển thị.
- Writes chỉ trong session app chạy local với dữ liệu test hoặc không persist.
