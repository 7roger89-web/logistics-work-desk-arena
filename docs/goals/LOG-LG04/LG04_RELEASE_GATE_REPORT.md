# LOG-LG04 — Báo cáo chờ anh duyệt (chưa áp dụng gì vào app anh đang dùng)

Anh chỉ cần đọc mục "ANH CẦN LÀM GÌ" ở cuối. Tất cả còn lại là bằng chứng để anh yên tâm.

## LOG-LG04 TRẠNG THÁI

**Chưa áp dụng.** Bản cải tiến đã làm xong và đang chờ anh duyệt. Anh duyệt xong tôi mới gộp vào app, chưa gộp gì cả.

## ANH ĐÃ NÓI GÌ (từ file "Trải nghiệm app.docx" anh gửi)

| Anh than phiền | Tôi đã sửa thế nào |
|---|---|
| Mở lô hàng phải cuộn ngược tìm chỗ nhập, Pickup/Export, Import/Delivery, Tài chính nằm tít dưới | 3 khối việc chính đưa lên đầu màn hình: 🚛 Lấy hàng & Xuất khẩu, 🛃 Nhập khẩu & Giao hàng, 💰 Chi phí & Công nợ — bấm nút là nhảy thẳng đến chỗ nhập |
| Cảnh báo "Quá free time" và "Việc tiếp theo" mờ nhạt, dễ bỏ qua | Card "VIỆC TIẾP THEO" to rõ ở trên cùng, viền màu theo mức gấp (đỏ = rất gấp), có nút "Xử lý ngay" |
| Bảng chứng từ 5 cột, bảng phí rườm rà | Các bảng tham khảo thu gọn vào mục phụ có thể đóng mở, không chiếm chỗ nữa |
| Khối "Mã vận động chủ", "Sổ tay đối chứng", "Ngữ cảnh đối tác" không hiểu là gì | Gộp vào một mục "Ai tham gia lô hàng này" có giải thích tiếng Việt thường, khối kỹ thuật tự ẩn khi chưa có dữ liệu |
| Tab Tài chính mở ra chỉ thấy số tổng hợp, muốn nhập chi phí ngay | Tab Tài chính giờ mở ngay tại phần nhập chi phí + giá bán; bảng kê số tổng vẫn ở cuối để đối chiếu |
| Form báo giá nhiều trường quá, ô nhập không kẻ khung | Chỉ còn trường thiết yếu trên màn hình, cài đặt nâng cao gom vào mục phụ; mỗi dòng dịch vụ kẻ khung riêng |
| Không hiểu "tạo thỏa thuận từ báo giá" → "chi tiết bàn giao" để làm gì | Thêm sơ đồ 4 bước: Báo giá → Thỏa thuận → Bàn giao → Tạo lô hàng, giải thích mỗi bước bằng tiếng Việt thường |

## ĐÃ KIỂM TRA GÌ

1. **Toàn bộ 226 kiểm thử tự động ĐẠT, 0 lỗi** (tăng từ 217 lên 226 nhờ 9 kiểm thử mới riêng cho các thay đổi này).
2. **Quét lỗi chữ tiếng Việt: sạch** — 5 file mới/thay đổi, không có ký tự lỗi.
3. **Quyền truy cập (ai được thấy gì) và an toàn số liệu tài chính: ĐẠT** — 50 kiểm thử liên quan, không thay đổi quyền nào cả.
4. **Dữ liệu thật của anh: không chạm gì.** Trong quá trình làm tôi chỉ đọc, không tạo/sửa khách hàng hay lô hàng nào.

## CÓ GÌ KHÔNG ĐỔI

- Phân quyền, mật khẩu, cách tạo tài khoản: giữ nguyên.
- Số liệu khách hàng (362), lô hàng (78): giữ nguyên.
- Cơ sở dữ liệu: giữ nguyên, không đổi cấu trúc gì.

## LOG-LG05

Chưa bắt đầu, đúng yêu cầu.

## ANH CẦN LÀM GÌ

1. Mở xem bản cải tiến: https://github.com/7roger89-web/logistics-work-desk/pull/3 (bản nháp, chưa gộp).
2. Nếu OK: nhắn tôi **"DUYỆT LOG-LG04"** — tôi sẽ gộp vào và cập nhật app trên máy anh.
3. Nếu muốn chỉnh gì: nhắn tôi điều muốn đổi, tôi sửa rồi cho xem lại trước khi gộp.
