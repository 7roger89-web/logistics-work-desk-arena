# LOG-LG04 — HƯỚNG DẪN XEM THỬ BẢN MỚI (bản xem thử an toàn)

Tài liệu này dành cho anh — hướng dẫn xem bản cải tiến LOG-LG04 trực tiếp trên máy anh, trước khi quyết định có áp dụng vào app chính hay không. Không có gì bị thay đổi cả: app anh đang dùng vẫn chạy bình thường, dữ liệu khách hàng và lô hàng không hề bị đụng vào.

## 1. Bản xem thử là gì

Anh đã chạy bản mới ở cửa sổ cmd thứ hai, trên cổng 8502. Bản này chỉ để **xem** — giống như thử đồ trước khi mua: xem thoải mái, thử thoải mái, không ảnh hưởng gì đến app thật đang chạy trên cổng 8501.

| Cửa sổ | Cổng | Nội dung |
|---|---|---|
| App thật anh đang dùng | http://localhost:8501 | App hiện tại, như mọi ngày |
| Bản xem thử LOG-LG04 | http://localhost:8502 | Bản mới với 7 cải tiến bên dưới |

## 2. Tôi đã kiểm tra thay anh những gì

Tôi đã tự đăng nhập vào bản xem thử và mở một lô hàng thật để xem các cải tiến. Kết quả như sau.

| Cải tiến (theo điều anh than phiền) | Kết quả kiểm tra |
|---|---|
| Việc chính (Lấy hàng/Xuất khẩu, Nhập khẩu/Giao hàng, Chi phí) đưa lên đầu màn hình lô hàng | Đạt — 3 thẻ việc hiện ngay dưới tiêu đề, mỗi thẻ có nút "Mở ..." để nhảy thẳng tới chỗ nhập |
| Card "VIỆC TIẾP THEO" to, rõ, viền đỏ khi gấp | Đạt — lô LO-0306 hiện "VIỆC TIẾP THEO · NGHIÊM TRỌNG: Quá free time — Hạn 26/06/2026 đã quá 53 ngày", có nút "Xử lý ngay" |
| Bảng chứng từ / phí rườmrà → thu gọn vào mục đóng mở được | Đạt — các khối phụ như "Việc cần theo dõi khác", "Ai tham gia lô hàng này", "Chứng từ", "Lịch sử" giờ đóng mở được, bảng費 lớn không còn đè lên đầu màn hình |
| Khối khó hiểu ("Mã vận động chủ", "Sổ tay đối chứng"...) | Đạt — gộp thành mục "Ai tham gia lô hàng này" kèm giải thích tiếng Việt thường |
| Tab Tài chính mở tại chỗ nhập chi phí + giá bán | Đạt (đã kiểm tra bằng kiểm thử tự động) — tab Tài chính giờ bắt đầu ngay bằng mục nhập dịch vụ & doanh thu, bảng tổng hợp vẫn ở cuối |
| Form báo giá kẻ khung từng dòng, bớt trường | Đạt (kiểm thử tự động) |
| Luồng Báo giá → Thỏa thuận → Bàn giao có sơ đồ 4 bước | Đạt (kiểm thử tự động) |

## 3. An toàn dữ liệu

Trong toàn bộ quá trình xem thử, tôi không sửa, không xóa, không tạo gì trong dữ liệu của anh. Khách hàng vẫn 362, lô hàng vẫn 78, tài khoản của anh không đổi. Bản xem thử chỉ đọc.

## 4. Anh cần làm gì (3 việc, mất khoảng 10 phút)

**Việc 1 — Mở bản xem thử:** trình duyệt mở địa chỉ http://localhost:8502 rồi đăng nhập bằng tài khoản admin của anh.

**Việc 2 — Xem một lô hàng:** từ bảng tổng, bấm nút "MỞ HỒ SƠ LÔ 360°" của dòng đầu tiên. Nhìn từ trên xuống anh sẽ thấy: (a) card Việc tiếp theo, (b) 3 thẻ việc chính, (c) hàng tín hiệu (Vận hành / Tài chính / Chủ sở hữu / Hạn khách / Free time), (d) các mục phụ đóng mở được, và (e) phần nhập liệu bên dưới qua 3 tab.

**Việc 3 — Chấm điểm:** nhắn tôi kết quả, theo mẫu đơn giản:

> Điểm từ 1 đến 10: ___
> Chỗ thích: ___
> Chỗ không thích hoặc thấy lộn xộn: ___
> Quyết định: DUYỆT áp dụng / CHƯA OK, sửa thêm

Anh chỉ cần nhắn theo mẫu trên, không cần giải thích gì thêm.

## 5. Điều gì xảy ra sau khi anh chấm điểm

Nếu anh **DUYỆT**: tôi gộp bản mới vào app chính, rồi hướng dẫn anh khởi động lại app thật (một lệnh copy-paste duy nhất). Nếu anh **CHƯA OK**: nhắn chỗ không thích, tôi sửa rồi chạy lại bản xem thử mới cho anh xem tiếp. Trong cả hai trường hợp, LOG-LG05 không bắt đầu cho đến khi anh nói tiếp.

## 6. Ghi chú kỹ thuật (lưu trữ, anh không cần đọc)

Bản xem thử chạy bằng `git checkout FETCH_HEAD` của nhánh `log-lg04-daily-work-simplification` (HEAD `8769883`) trên máy Owner, cổng 8502. App production (cổng 8501, SHA `3c1e1c7`) và database production `logistics_db` không bị chạm gì — 0 lệnh ghi. PR #3 vẫn ở trạng thái draft. Trạng thái state.json đã cập nhật thành `UX_PREVIEW_VERIFIED_ON_OWNER_MACHINE`.
