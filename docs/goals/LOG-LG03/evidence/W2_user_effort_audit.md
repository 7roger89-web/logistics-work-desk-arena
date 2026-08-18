# LOG-LG03 W2 — User-effort / workflow-friction audit

Ngày: 2026-08-18. Dựa trên đọc code views (dashboard.py, shipment.py, review_queue.py, finance_review.py, customers.py, quotations.py, agreements.py, web_app.py) và route map LG01.

## 1. SALE FLOW (Customer → Quotation → Agreement → Shipment)

| Hạng mục | Hiện trạng (code) | Vấn đề |
|---|---|---|
| Số màn hình | 4 màn: Khách Hàng → Sales & Báo Giá → Thỏa Thuận & Bàn Giao → Tạo Lô Mới | Hợp lý, không đổi |
| Khách → Quote | quotations.py phải chọn lại khách hàng đã biết (dropdown độc lập) | Trùng nhập: tên khách đã có trong customers → prefill từ khách đã chọn được (bounded) |
| Quote → Agreement | agreements.py nhập goods/amount lại | Dùng dữ liệu quote đã duyệt làm nguồn (bounded, không mất validation) |
| Agreement → Shipment | ui_create_new_shipment: form 6 trường, Mã Lô tự sinh, ngày chứng từ = hôm nay, mode/incoterm = hardcoded (Sea/EXW ở "0.0") | Trùng nhập tối thiểu; nhưng sau tạo lô người dùng phải nhập lại hàng loạt thông tin vận hành (Mode, Incoterm, Booking, Carrier...) trong Shipment 360 |
| next-action | Dashboard queue đã có "Next action:" per row (tốt) | Label tiếng Anh "Next action:", "PRIMARY WORK SURFACE", "FINANCE ATTENTION" |

## 2. SUPPORT FLOW (Dashboard → Shipment → Documents → Review Queue)

Review Queue đã là trang đích ngoại lệ tốt (cảnh báo + severity + màu + nguồn). Vấn đề:
- Label "Open Shipment 360" / "Open Entity Context" / "Open Finance Review" (tiếng Anh, nút bấm nhảy màn).
- "Documents & Review Queue" title + "Search & filter", "Category", "Status", "Severity", "work items" EN.
- Mojibake tại scope filter "Táº¥t cáº£" (dòng 85) — bug hiển thị khối.
- Chuỗi "Vì sao ra số này?" expander trong dashboard finance: TỐT (progressive disclosure, giữ).

## 3. ADMIN FLOW (Login → User management → Finance Review)

- Login page (core/auth.py) đã tiếng Việt — chỉ thống nhất từ ngữ ("Đăng nhập", "Đăng xuất" đã OK).
- User management (web_app.py) tiếng Việt nhưng lỗi gõ: "Mật khảu" → "Mật khẩu", "kết nốii" → "kết nối".
- Finance Review: "Investigation queue", "Reason", "Next action", "Bucket", "Record", "Payer", "Payee", "Holder", "Beneficial owner", "Outstanding / remainder", "Formula" — cột bảng hoàn toàn EN; label "Scope", placeholders EN. Đây là màn hình đối soát nhạy cảm: dịch label bảng phải giữ nghĩa estimate vs actual, confirmed vs unknown (Section 27).

## 4. Friction chung (nguyên tắc giữ)

- KHÔNG bỏ safety confirmation (xác nhận trước commit tài chính, delete/undo) — Section 15/16: "Safety confirmation is not wasted click".
- Validation, audit, permission giữ nguyên.
- UNKNOWN ≠ ZERO: label "UNKNOWN" giữ nguyên về nghĩa; có thể dịch hiển thị thành "Chưa xác định" KÈM chú thích giá trị UNKNOWN trong tooltip để không nhầm zero. Quyết định: giữ "UNKNOWN" + chú thích VN (international term / technical status) — tránh thay đổi nghĩa tài chính.

## 5. Next-action UX

Dashboard đã có next-action per row (cấu trúc tốt, Section 19). Cần: (a) dịch "Next action:" → "Việc tiếp theo:", (b) giữ cấu trúc; (c) Review Queue → "Việc tiếp theo" nhất quán; (d) không xây workflow engine mới — chỉ dùng state + alert hiện có.

## 6. Progressive disclosure hiện có (không phá)

- Dashboard filter expander "🔎 Lọc & tìm trong queue" (expander kỹ thuật — đổi label "Vì sao ra số này?" và các caption).
- shipment_360 workspace tabs — giữ nguyên cấu trúc, chỉ đổi label tab nếu EN và ngữ nghĩa rõ ràng.

## 7. Quyết định ưu tiên (bounded)

1. Sửa toàn bộ EN label trong 5 màn hình pilot (sidebar 5 mục, Dashboard, Review Queue, Tạo Lô Mới, Entity Context, Finance Review).
2. Sửa mojibake trong phạm vi pilot + shipment_360 (metric labels ĐÃ THU/ĐÃ TRẢ/CHI PHÍ ĐÃ BIẾT) + review_queue scope string.
3. Giảm trùng nhập: (a) dashboard filter label tiếng Việt; (b) Create Shipment: thêm gợi ý chọn customer từ list gần đây (prefill bounded); KHÔNG tự sinh business truth.
4. Sửa lỗi gõ trong user management ("Mật khảu", "kết nốii").
