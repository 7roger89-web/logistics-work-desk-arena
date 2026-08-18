# LOG-LG04 — Bằng chứng phản hồi của Owner (Trải nghiệm app.docx)

Nguồn: /home/ubuntu/upload/Trảinghiệmapp.docx (3 trang, đính kèm ảnh màn hình).

## Ý 1 — Vị trí việc chính khi mở lô hàng (quan trọng nhất)
Khi mở 1 lô hàng, phải cuộn ngược lên đầu trang mới thấy. Thông tin cần nhập hàng ngày của Support là: **Pickup & Xuất khẩu — Import & Giao hàng — Finance (công nợ)**. Khi ấn vào 1 lô hàng, 3 khu vực này phải hiện ngay ở trên đầu.

## Ý 2 — Khối cần làm gọn (rườm rà)
Khối gồm nhiều dòng "Vận chuyển / Phí kiểm chứng / Chi phí giữ lô / Mã M/B/L / Phí giữ lô" dạng bảng nhiều cột (xem trang 1, ảnh bảng 5 cột). Đánh giá của Owner: "làm gọn lại, rườm rà".

## Ý 3 — Cảnh báo quá mờ nhạt
Cảnh báo "Quá free time" + "Việc tiếp theo" chỉ là dòng chữ nhỏ mờ, không nổi bật, không gây chú ý. Ảnh trang 1: "⚠ Cần báo và xử lý khi hơn để có ... Quá free time ... Việc tiếp theo: ... Nguồn: Shipment financial projection".

## Ý 4 — Khối "Mã vận động chủ này: pickup delivery" không rõ, tốn diện tích
Khối có: Khách hàng, Customer ID, Nhà cung cấp, Agent/partner + bên phải Pickup contact/address/delivery address/Receiver (trang 1-2). Owner: "Thông tin này là gì, chưa rõ và tốn diện tích". → NGỮ CẢNH ĐỐI TÁC cần giải thích/đổi tên/thu gọn.

## Ý 5 — "Sổ tay đối chứng/thể" không hiểu
Khối "ⓘ Sổ tay đối chứng/thể" với 1 UNKNOWN — ... support: Check out collection/settle for factory_inspection_terms_house (trang 2 trên): "Không rõ thông tin này".

## Ý 6 — "Cẩn số: xem trị" không rõ mục đích
Khối "ⓘ Cẩn số: xem trị" (dạng table: Tự cũ/1009638/shipper.../UNKNOWN) — "mục đích cái này để làm gì" (trang 2 giữa).

## Ý 7 — Tab FINANCE (CÔNG NỢ): mở ra chỉ là tổng hợp số, không có chỗ nhập chi phí
Mở tab là các thẻ: TỔNG PHẢI THU 49,180,000 VND / ĐÃ THU 0 / CÒN PHẢI THU 49,180,000 / ... CHI PHÍ ĐÃ NHẬP 35,000,000 / CHI LÀ KHÔNG UNKNOWN / CHI TIẾT ĐÓNG UNKNOWN / THU ĐI TỪNG LỆ UNKNOWN / ... trạng thái wait / trạng thái CHỜ THU / ... LỢI NHUẬN DỰ KIẾN 11,500,000 VND.
Trong khi cái cần là **nhập các thông tin chi phí** ngay đó. → Input-first finance ở mức lô hàng.

## Ý 8 — "Ngữ cảnh đối tác là cái gì?"
Câu hỏi trực tiếp — cần đổi tên + giải thích hoặc thu gọn.

## Ý 9 — Form tạo báo giá
"tạo báo giá có quá nhiều trường dữ liệu, và các ô nhập chưa có kẻ khung" (form nhập dòng dịch vụ & doanh thu trang 3 không có viền ô).

## Ý 10 — Luồng Báo giá → Thỏa thuận
"chưa rõ từ tạo báo giá chốt: tạo thỏa thuận từ báo giá này -> chi tiết bàn giao để làm gì?" → Làm rõ 4 giai đoạn: Báo giá → Khách chốt → Thỏa thuận → Bàn giao cho Support → Lô hàng vận hành. Đổi tên/ghichú "chi tiết bàn giao" nếu kỹ thuật quá.

## GHI CHÚ ÁNH XẠ UI (từ ảnh, nhận diện khối)
1. Bảng 5 cột (Vận chuyển/Phí kiểm chứng/Chi phí giữ lô/Mã M/B/L/Phí giữ lô) = khối "document/status" kiểu bảng chi tiết — thu gọn.
2. "Mã vận động chủ này: pickup delivery" = khối entity context (Khách hàng/Pickup contact/Receiver...).
3. "Sổ tay đối chứng/thể" = khối knowledge/reference liên quan collection/settle terms (UNKNOWN).
4. "Cẩn số: xem trị" = khối chứa các field dạng shipper/factory/status UNKNOWN — cần tra source code xác định.
5. Tab Finance = views.finance hoặc tab trong shipment workspace — hiện chỉ read-only summary cards.
6. Form báo giá = views.quotations ui_sales_module, bảng "1. Dịch Vụ & Doanh Thu" (Tên dịch vụ, SL, Đơn vị, Đơn giá, VAT, Thành tiền) ô input không kẻ viền.
