# LOG-LG04 R3 — Bản xem thử 3.0

## Tóm tắt cho Owner

Bản 3.0 sửa **5 điểm** anh than phiền:

1. **Chậm lag** → Đã thêm bộ nhớ đệm (cache). Lần đầu mở vẫn chậm (~27 giây do server MongoDB miễn phí ở Mỹ — không thể sửa bằng code), nhưng **mọi thao tác sau đó chỉ 0.5 giây** (nhanh gấp 54 lần so với trước).

2. **Nút "MỞ HỒ SƠ LÔ 360°" phải cuộn ngược** → Đổi thành **"📝 XỬ LÝ LÔ"** (nút xanh nổi bật). Bấm vào là mở thẳng **form nhập liệu** (tab DỊCH VỤ & DOANH THU) — không phải qua trang 360° rồi bấm thêm. Nút "📊 360°" vẫn có nếu anh muốn xem tổng quan.

3. **Dashboard quá nhiều KPI đẩy việc xuống** → Thay bảng KPI lớn bằng 1 dòng tóm tắt gọn: **🔴 X lô cần xử lý · Y quá hạn · Z thiếu chứng từ · N đang chờ**. Dưới đó là bảng lô hàng với bộ lọc đơn giản (Khách hàng / Sale / Vận hành).

4. **"Ngữ cảnh đối tác" không hiểu** → Đã đổi thành **"🏭 Khách hàng · Nhà máy · Đại lý"** với giải thích: "Thông tin liên hệ của các bên trong lô hàng, dùng khi lấy hàng, xử lý chứng từ và giao hàng."

5. **Support chưa nhập được tài chính** → Support giờ nhập được chi phí, giá bán, thanh toán. Sale và Viewer vẫn không chạm.

## Kiểm thử

| Hạng mục | Kết quả |
|----------|---------|
| Regression | **231 passed / 28 skipped / 0 failed** |
| Mojibake (lỗi chữ tiếng Việt) | Sạch |
| RBAC | PASS |
| Finance safety (read-only) | PASS |
| Production data | Không chạm (362 customers, 78 shipments) |

## Anh cần làm gì

1. Tắt app xem thử cũ (Ctrl+C trong cmd đang chạy cổng 8502)
2. Chạy lại bản mới:
```
cd /d D:\Logistics_App_GitHub
git fetch origin log-lg04-daily-work-simplification
git checkout FETCH_HEAD & streamlit run app.py --server.port 8502
```
3. Vào **http://localhost:8502** — đăng nhập admin
4. Bấm "📝 Xử lý" ở dòng đầu tiên trong bảng → phải mở thẳng form nhập liệu (chi phí + giá bán), không phải trang tổng quan
5. Bấm "📊 360°" → phải mở trang tổng quan

Nhắn tôi:
> Điểm 1-10: ___
> Chỗ thích: ___
> Chỗ không thích: ___
> Quyết định: DUYỆT / CHƯA OK

## Cần Owner cung cấp (GATE)

2 tài khoản Support cần tên thật — tôi không tự tạo. Anh cho tôi:
- Support 1: tên hiển thị + username
- Support 2: tên hiển thị + username

## Khuyến nghị

- Anh nên dùng tài khoản Sale riêng cho việc hàng ngày, để Admin chỉ dùng quản trị.
