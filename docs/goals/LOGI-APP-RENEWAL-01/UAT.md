# LOGI-199 — UAT local đơn giản (chưa phải nghiệm thu/cho phép release)

Chỉ dùng bản tích hợp trên nhánh hiện tại `arena/818a2d0a-logistics-work-desk-arena`.
Independent review và Owner UAT vẫn **PENDING**. Không tự động merge `main` hay deploy production.

## Khi reviewer cho phép bắt đầu UAT

1. [Tải ZIP nhánh thử nghiệm](https://github.com/7roger89-web/logistics-work-desk-arena/archive/refs/heads/arena/818a2d0a-logistics-work-desk-arena.zip), giải nén vào **thư mục mới**, không dùng thư mục app production. Không cần Git hay sửa code (gói giao diện `component/dist` đã được biên dịch sẵn trong nhánh).
2. Trên Windows có Python 3.11+, mở thư mục `scripts`, nhấp đúp **`logi199_uat.cmd`**. Lần đầu chờ tải thư viện. Nếu báo lỗi, giữ nguyên cửa sổ gửi người hỗ trợ; không tự sửa cấu hình DB. *(Lưu ý: `scripts/logi199_uat.cmd` là batch launcher cho Windows; trên môi trường Linux sandbox chỉ kiểm tra tĩnh và kiểm chứng trực tiếp lệnh `streamlit run scripts/logi199_t6_staging_app.py`, trạng thái chạy thực tế trên máy Windows là `NOT_RUN` cho tới khi chạy trên Windows thật).*
3. Mở **http://localhost:9501**. App chạy dữ liệu mẫu trong bộ nhớ (`mongomock` cô lập); port 8501/8510 của production không đổi. Không copy `secrets.toml`, `.env` hoặc URI production vào thư mục này. Nếu launcher từ chối cấu hình, dừng, không bỏ guard.
4. Xong thì Ctrl+C trong cửa sổ chạy. Dữ liệu thử sẽ mất khi dừng server (đúng thiết kế staging trong bộ nhớ). Ghi PASS/FAIL và ảnh, không cần lập trình.

Không cài app public, không đăng nhập bằng tài khoản production. Chưa tạo staging cloud/deploy mới.

## Checklist ngắn

| Màn hình / lô mẫu | Thao tác | Kỳ vọng |
|---|---|---|
| T6-FCL / bản đồ Journey map-first | Xem mặc định; kéo (pan); +/−; `⤢ Fit Journey`; `↺ Đọc rõ`; nút nổi `▤ Hồ sơ & Tài chính` | Desktop (`1440×900`): mặc định `95%` (Fit) hiển thị trọn vẹn 11 node căn giữa theo chiều dọc trên nền hải đồ Việt Nam / Biển Đông / Hoàng Sa / Trường Sa (`vietnam-east-sea-chart.webp`); góc trái dưới có `CHÚ GIẢI TRẠNG THÁI`; góc phải trên có nút nổi `▤ Hồ sơ & Tài chính`. Mobile (`390×844`): phần thông tin đầu trang gọn, nửa trên khung bản đồ hiển thị rõ hải đồ Việt Nam / Hoàng Sa / Trường Sa không bị cắt ngang hay méo tỷ lệ, nửa dưới hiển thị các node công đoạn, không tràn ngang (`0px`). |
| T6-FCL / ON BOARD | Chọn node `07 ON BOARD / ATD` (trên mobile: kéo bản đồ sang phải tới node `ON BOARD` rồi chạm chọn) → bubble công việc → mở công đoạn → tab `Công việc`; nhập ngày `2026-10-03` rồi nhấn Lưu; tải lại hoặc chuyển lô rồi quay lại | Hiện `Hoàn thành` (`CÓ BẰNG CHỨNG`) và giữ nguyên ngày đã lưu sau khi đọc lại từ backend; ATD đơn thuần không tự chứng minh on-board. Trên mobile trình sửa mở dạng bottom sheet, nút Lưu bấm được bằng thao tác chạm. |
| T6-FCL / DELIVERY | Nhập POD khi chưa xác nhận giao | Bị từ chối; không tự hoàn thành toàn lô. |
| T6-LCL | Xem CFS / GHÉP HÀNG; mở Công việc và `Xem thêm chi tiết` | Không bắt buộc GATE-IN/VGM; hiển thị tối đa 2–5 trường chính, các trường phụ nằm trong `Xem thêm chi tiết` và vẫn chỉnh sửa được. |
| T6-AIR và T6-AIR-CONSOLIDATED | Xem AWB/chuyến, kho, uplift, đến | Không có SI/VGM/GATE-IN tàu. Chọn loại consolidated không tự chứng minh đã bay. |
| T6-ROAD-LTL và T6-ROAD-FTL | Xem nhận/ghép hàng hoặc xe/tài xế | Không áp maritime; fixture nội địa không cửa khẩu/hải quan. |
| Công đoạn bất kỳ / Chứng từ | Mở và đối chiếu phạm vi | Chỉ chứng từ thuộc công đoạn; không hỏi lại khách đã biết. UNKNOWN không biến thành hoàn thành. |
| Báo giá 390px | Xem tab/bộ lọc | Đọc được, không cắt ngang (`overflowPx = 0`). |
| Tra cứu chính sách 390px | Xem tên nguồn | Đọc đủ “Bộ Thông Tin Truyền Thông”, biểu tượng mở vẫn trong thẻ. |

Ảnh bằng chứng theo từng cổng:
- Oracle tham chiếu Owner HTML: `evidence/logi-199-g0/reference-html/`
- G1 (Hệ màu & font Mimo–Sonnet): `evidence/logi-199-g1/`
- G2 (Journey map-first, nền Việt Nam / Hoàng Sa / Trường Sa, touch save/readback): `evidence/logi-199-g2/` và `evidence/logi-199-g2/metrics.json`
- G3 (Các màn hình Nghiệp vụ & Điều hành desktop/mobile): `evidence/logi-199-g3/`
- G4 (Các màn hình Công cụ & Quản trị desktop/mobile): `evidence/logi-199-g4/`
- G5 & T5/T6 tổng hợp: `evidence/logi-199-g5/`, `evidence/logi-199-t5/route_audit.json`, `evidence/logi-199-t6/browser_metrics.json`

Ảnh/CI không thay thế Independent review, Owner UAT hoặc quyền merge production.
