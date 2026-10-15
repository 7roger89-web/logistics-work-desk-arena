# LOGI-199 — UAT local đơn giản (chưa phải nghiệm thu/cho phép release)

Chỉ dùng bản tích hợp có #198 trên `arena/d8927583-logistics-work-desk-arena`.
Independent review và Owner UAT vẫn **PENDING**. Không cần chọn phương án hay cấp quyền deploy.

## Khi reviewer cho phép bắt đầu UAT

1. [Tải ZIP nhánh thử nghiệm](https://github.com/7roger89-web/logistics-work-desk-arena/archive/refs/heads/arena/d8927583-logistics-work-desk-arena.zip), giải nén vào **thư mục mới**, không dùng thư mục app production. Không cần Git hay sửa code.
2. Trên Windows có Python 3.11+, mở thư mục `scripts`, nhấp đúp **`logi199_uat.cmd`**. Lần đầu chờ tải thư viện. Nếu báo lỗi, giữ nguyên cửa sổ gửi người hỗ trợ; không tự sửa cấu hình DB.
3. Mở **http://localhost:9501**. App chạy dữ liệu mẫu trong bộ nhớ; port 8501/8510 không đổi. Không copy `secrets.toml`, `.env` hoặc URI production vào thư mục này. Nếu launcher từ chối cấu hình, dừng, không bỏ guard.
4. Xong thì Ctrl+C trong cửa sổ chạy. Dữ liệu thử sẽ mất khi dừng server (đúng thiết kế staging). Ghi PASS/FAIL và ảnh, không cần lập trình.

Không cài app public, không đăng nhập bằng tài khoản production. Chưa tạo staging cloud/deploy mới.

## Checklist ngắn

| Màn hình / lô mẫu | Thao tác | Kỳ vọng |
|---|---|---|
| T6-FCL / bản đồ | Xem mặc định; kéo; +/−; Fit Journey; Đọc rõ | Mặc định 100%, đọc tên node rõ. Fit chỉ để xem toàn cảnh. Desktop: map trái / việc phải; mobile: xếp dọc, không tràn. |
| T6-FCL / ON BOARD | Fit → chọn node → Mở công đoạn → Công việc; nhập 2026-10-03 rồi Lưu; sang lô khác, quay lại | Hiện Hoàn thành và ngày đã lưu sau backend readback; ATD đơn thuần không tự chứng minh on-board. |
| T6-FCL / DELIVERY | Nhập POD khi chưa xác nhận giao | Bị từ chối; không tự hoàn thành toàn lô. |
| T6-LCL | Xem CFS / GHÉP HÀNG; mở Công việc và Chi tiết phụ | Không GATE-IN/VGM bắt buộc; trường phụ còn sửa được, không bị xóa. |
| T6-AIR và T6-AIR-CONSOLIDATED | Xem AWB/chuyến, kho, uplift, đến | Không có SI/VGM/GATE-IN tàu. Chọn loại consolidated không tự chứng minh đã bay. |
| T6-ROAD-LTL và T6-ROAD-FTL | Xem nhận/ghép hàng hoặc xe/tài xế | Không áp maritime; fixture nội địa không cửa khẩu/hải quan. |
| Công đoạn bất kỳ / Chứng từ | Mở và đối chiếu phạm vi | Chỉ chứng từ thuộc công đoạn; không hỏi lại khách đã biết. UNKNOWN không biến thành hoàn thành. |
| Báo giá 390px | Xem tab/bộ lọc | Giữ kết quả sửa mobile: đọc được, không cắt ngang. |
| Tra cứu chính sách 390px | Xem tên nguồn | Đọc đủ “Bộ Thông Tin Truyền Thông”, biểu tượng mở vẫn trong thẻ. |

Ảnh so sánh: `evidence/logi-199-t6/{desktop,mobile}-map-A-fit.png` và `*-map-B-readable.png`.
Audit 21 màn hình độc lập: `evidence/logi-199-t5/route_audit.json`; 3 redirect legacy được kiểm tra đích riêng, không tính là màn hình.
Ảnh/CI không thay thế Independent review, Owner UAT hoặc quyền merge production.
