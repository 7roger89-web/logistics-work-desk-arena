# LOG-LG04 — Audit phân loại khối thông tin trên màn hình lô hàng (read-only)

## Sơ đồ hiện tại của `views.shipment.ui_shipment_detail_tabs` (thứ tự thực tế khi mở 1 lô)

1. `render_shipment_workspace` (read-only 360, toàn màn hình trên cùng):
   - Header: SHIPMENT 360 · OPERATIONAL WORKSPACE / shipment_id · customer / route / Incoterm
   - Note: "Đọc nhanh để xử lý lô · UNKNOWN · writer nằm bên dưới"
   - NEXT ACTION alert (severity → st.error/warning/success/info) + caption "Nguồn bước tiếp theo"  ← Ý 3: MỜ NHẠT — chủ yếu chữ, st.warning/st.error chỉ dùng cho warning/critical
   - 5 cột signal: Vận hành / Tài chính / Chủ sở hữu / Hạn khách / Free time
   - Expander "⚠️ Cảnh báo và việc cần theo dõi" (chứa "Quá free time") ← Ý 3
   - Expander "👥 Khách hàng · nhà máy · pickup · delivery" (Khách hàng/Customer ID/Nhà cung cấp/Agent-partner/Pickup contact/address/Delivery address/Receiver + 3 nút 360) ← Ý 4, Ý 8 ("Ngữ cảnh đối tác")
   - Expander "🏭 Factory lots" ← Ý 5/6 ("không rõ thông tin này")
   - Expander "📄 Chứng từ" ← Ý 6 (khối bảng 5 cột từ doc: document/status/step/source/required — bảng fallback)
   - Expander "🕒 Lịch sử / audit"
   - Caption "Chi tiết chỉnh sửa... nằm bên dưới"
2. HEADER chỉnh sửa (border container): Mã Lô, Ngày tạo, Khách hàng, Trạng thái, nút 💾 LƯU, Hợp đồng liên kết
3. 3 tabs: 🚛 PICKUP & XUẤT KHẨU / 🛃 IMPORT & GIAO HÀNG / 💰 FINANCE (CÔNG NỢ)
   - t1: thông tin vận đơn (mode, incoterm, booking, carrier, mbl, hbl, vessel, etd, pol, pod, cont, qty)
   - t2: Nhập khẩu (ETA, free time, TK HQ, GNT expander, thông quan, luồng) + Giao hàng (xe, tài xế, ngày giao, SĐT, Đ/C, đã giao) + Ủy thác & Hợp đồng + COPY NHANH
   - t3: render_shipment_360_summary (16 thẻ metric) + "1. Dịch Vụ & Doanh Thu" (bảng dịch vụ) + "2. Chi Hoa Hồng" + "3. Lịch sử Thu tiền" + "📊 BẢNG KÊ TÀI CHÍNH" + audit expander
4. Save flow cuối trang

## Ánh xạ complaint → khối → phân loại

| # | Complaint Owner | Khối code | Phân loại | Xử lý đề xuất |
|---|---|---|---|---|
| 1 | Việc chính phải ở trên đầu, không phải cuộn ngược | Workspace render trên cùng nhưng chỉ READ-ONLY; việc nhập nằm ở 3 tabs bên dưới + phải LƯU | PRIMARY_WORK bị đẩy xuống | Đưa "Việc tiếp theo" lớn + 3 card việc chính (Pickup/Export, Import/Delivery, Chi phí) vào trên cùng, mỗi card dẫn thẳng đến input |
| 2 | Bảng 5 cột rườm rà | `_document_rows` fallback bảng Chứng từ (doc/ status/step/source/required) | REFERENCE (fallback audit tech) | Thu gọn thành 1 dòng trạng thái + link, hoặc expander nhỏ "Chứng từ nhanh" |
| 3 | "Quá free time" / Việc tiếp theo mờ nhạt | NEXT ACTION alert + expander Cảnh báo | PRIMARY_WORK attention | Card NEXT ACTION lớn (màu + viền + icon + vì sao + ai làm + việc tiếp), không phải 1 dòng caption |
| 4 | "Khách hàng · nhà máy · pickup · delivery" không rõ, tốn diện tích | `view["context"]` expander + 3 nút 360 | REFERENCE | Đổi tên "Ai tham gia lô hàng này" + 1 câu giải thích + nút Xem chi tiết thay vì hiện 8 dòng + 3 nút ngang hàng |
| 5 | "Sổ tay đối chứng/thể" UNKNOWN | alerts entry source "collection/settle terms" | REFERENCE/EXCEPTION | Nhóm vào expander "Điều cần xác nhận" với ngôn ngữ thường: "Thỏa thuận với khách về đối soát/điều khoản chưa có — cần Sale bổ sung" |
| 6 | "Cẩn số: xem trị" | factory_lots UNKNOWN "shipment chưa có collection factories/factory_lots/factory_items chuẩn" | AUDIT_TECHNICAL | Ẩn khi UNKNOWN hoặc đổi thành "Hàng từ nhà máy: chưa nhập" + giải thích |
| 7 | "Ngữ cảnh đối tác là cái gì?" | entity_context views | REFERENCE (hồ sơ đối tác tổng hợp) | Đổi tên "Hồ sơ đối tác" + subtitle 1 câu |
| 8 | Tab FINANCE mở ra toàn số tổng hợp, cần nhập chi phí | t3: render_shipment_360_summary trước, form dịch vụ sau | INPUT FIRST mong muốn | Thứ tự: A) Nhập chi phí & doanh thu (form chính, có kẻ khung) → B) Tóm tắt công nợ → C) Đối soát/đóng |
| 9 | Form báo giá quá nhiều trường, ô không kẻ khung | views.quotations "1. Dịch Vụ & Doanh Thu" selectbox không khung + nhiều trường | INPUT UX | Kẻ khung ô (border container per row), tách Essential/Frequent/Conditional/Advanced |
| 10 | "tạo thỏa thuận từ báo giá → chi tiết bàn giao để làm gì?" | agreements: tạo từ quote + 6 tabs + Bàn giao 16 câu hỏi | COMMERCIAL HANDOFF | Hành trình 4 bước có giải thích bằng tiếng Việt thường; đổi "Bàn giao vận hành" → "Danh mục cần có trước khi Support vận hành"; tooltip/văn bản "Khách chốt báo giá → Thỏa thuận chốt điều khoản → Bàn giao = kiểm tra đủ thông tin Support cần" |

## Khối KHÔNG xóa (và lý do)
- Audit/history: bằng chứng kiểm toán, pháp lý — chỉ thu gọn (expander đóng mặc định)
- Factory lots: cần khi Support lấy hàng nhiều nhà máy — giữ nhưng ẩn khi UNKNOWN
- Documents: Support cần biết chứng từ nào đã có — giữ dạng "chứng từ nhanh" 1 dòng mỗi chứng từ
- Free time: nghiệp vụ thực (tránh phí lưu cont) — giữ nhưng làm NỔI BẬT khi sắp hết
- Commission / payments: nghiệp vụ tài chính thực — giữ trong input-first

## Bảo toàn bắt buộc (không được phá)
- UNKNOWN != ZERO; ESTIMATE != ACTUAL; currency separation; finance write permission; audit/provenance; 0 financial mutation từ commercial flow.
