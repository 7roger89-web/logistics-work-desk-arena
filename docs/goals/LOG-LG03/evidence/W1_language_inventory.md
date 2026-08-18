# LOG-LG03 W1 — Language Inventory (Kiểm kê ngôn ngữ UI)

Ngày: 2026-08-18. Nguồn dữ liệu gốc: `docs/goals/LOG-LG03/evidence/W1_raw_strings.json` (kết quả quét AST toàn bộ `views/*.py` + `core/*.py`).

## 1. Tổng quan định lượng

Quét bằng AST (bước đi literal string) trên 55 file Python. Kết quả toàn repo (kể cả cả docstring/lỗi kỹ thuật, chưa lọc UI thực tế):

| Phân loại | Số lượng (toàn repo) | Trong views/*.py (chuỗi 2–120 ký tự) |
|---|---|---|
| VIETNAMESE_OK | 2.858 | 1.871 |
| ENGLISH_USER_VISIBLE | 12.920 | 3.585 |
| MOJIBAKE | 48 | 8 |
| TECHNICAL_INTERNAL | (bị lọc) | — |

Con số 3.585 "ENGLISH" trong views chưa phân biệt nhãn người dùng thật với chuỗi kỹ thuật (ID, status code, message log). Inventory UI thực tế được lọc thủ công ở mục 2–4. Nhiều chuỗi trong `core/*.py` là thông báo lỗi nội bộ/trợ giúp debug cho admin — thuộc diện "technical jargon cần che/ẩn" (Section 26) chứ không cần dịch sạch.

## 2. Hàng điều hướng (ROUTES + NAVIGATION_GROUPS, views/web_app.py dòng 37–82)

Đây là "source of truth" UI. 6/16 nhãn tuyến đã tiếng Việt; 10 nhãn còn lại ENGLISH/mixed. Các nhóm điều hướng hoàn toàn ENGLISH (`OPERATIONS`, `COMMERCIAL CONTEXT`, `FINANCE & REVIEW`, `TOOLS & REFERENCE`, `ADMINISTRATION`).

| Nhãn hiện tại | Phân loại | Đề xuất tiếng Việt (glossary) |
|---|---|---|
| Dashboard | ENGLISH | Tổng quan công việc |
| Review Queue | ENGLISH | Việc cần xử lý |
| Tạo Lô Mới | VIETNAMESE_OK | giữ nguyên |
| Khách Hàng | VIETNAMESE_OK | giữ nguyên |
| Entity Context | ENGLISH | Ngữ cảnh đối tác |
| Sales & Báo Giá | MIXED | Kinh doanh & Báo giá |
| Thỏa Thuận & Bàn Giao | VIETNAMESE_OK | giữ nguyên |
| Hợp Đồng | VIETNAMESE_OK | giữ nguyên |
| Thu Tiền & Công Nợ | VIETNAMESE_OK | giữ nguyên |
| Finance Review | ENGLISH | Đối soát tài chính |
| Công nợ A Bò | VIETNAMESE_OK (tên nghiệp vụ) | giữ nguyên — nghĩa nghiệp vụ cần Owner xác nhận nếu đổi |
| Báo Cáo CEO | VIETNAMESE_OK | giữ nguyên |
| Tra Cứu Thuế | VIETNAMESE_OK | giữ nguyên |
| Tracking | ENGLISH | Theo dõi vận chuyển |
| Sổ Tay Kinh Nghiệm | VIETNAMESE_OK | giữ nguyên |
| Người Dùng | VIETNAMESE_OK | giữ nguyên |

Nhóm điều hướng đề xuất: `VẬN HÀNH` (Tổng quan, Việc cần xử lý, Tạo Lô Mới, Theo dõi vận chuyển), `KINH DOANH` (Khách Hàng, Ngữ cảnh đối tác, Kinh doanh & Báo giá, Thỏa Thuận & Bàn Giao, Hợp Đồng), `TÀI CHÍNH & ĐỐI SOÁT` (Đối soát tài chính, Thu Tiền & Công Nợ, Công nợ A Bò, Báo Cáo CEO), `CÔNG CỤ & THAM KHẢO` (Tra Cứu Thuế, Sổ Tay Kinh Nghiệm), `QUẢN TRỊ` (Người Dùng).

**Phân tích ràng buộc ổn định:** các tuyến khác tham chiếu nhãn bằng `st.session_state.active_page = "Dashboard"/"Review Queue"/"Entity Context"/"Finance Review"/"Tracking"/"Sales & Báo Giá"` (dashboard.py, entity_context.py, finance_review.py, review_queue.py) và test `test_entity_context_ui.py` assert key. web_app lookup theo `route.label` → đổi nhãn tuyến sẽ **phải** đổi đồng bộ toàn bộ điểm tham chiếu active_page (cả views + tests). Đây là thay đổi có kiểm soát, không phá RBAC vì permission lookup theo `route.permission` (không đổi).

## 3. Các page title chính (st.title) trong views/ — phân loại nhanh

| Màn hình | Title hiện tại | Phân loại |
|---|---|---|
| Dashboard | (kicker tiếng Anh: "PRIMARY WORK SURFACE · SHIPMENT QUEUE", "FINANCE ATTENTION", "Shipment control room") | MIXED — nhiều tiếng Anh rải rác |
| Review Queue | "Documents & Review Queue" + label "Search & filter", "Category", "Status", "Severity", "work items" | MIXED/ENGLISH |
| Entity Context | "Customer / Factory / Partner 360", "← Back to Dashboard/Review Queue" | ENGLISH |
| Sales/Quotations | "Sales & Báo giá Logistics", "🤝 QUẢN LÝ SALES & BÁO GIÁ KHUNG (RATE CARD)" | MIXED |
| Agreements | "Thỏa Thuận & Bàn Giao" | OK (body còn label EN) |
| Contracts | "📜 QUẢN LÝ HỢP ĐỒNG & TÀI CHÍNH HỢP ĐỒNG" | OK (body còn label EN) |
| Finance Review | "Finance Review", "Investigation queue", "Reason", "Next action", "Bucket", "Record", "Payer", "Payee", "Holder", "Beneficial owner", "Outstanding / remainder", "Formula" | ENGLISH đậm |
| Partner Reconciliation | "BÁO CÁO CÔNG NỢ A BÒ — SALE THÀNH", "DEBIT DRAFT — A BÒ / SALE THÀNH" | MIXED (title ALLCAPS + EN) |
| Tracking | "🌐 TRA CỨU HÀNH TRÌNH (TRACKING)" | MIXED |
| Entity labels trong UI | "Customer 360", "Factory / Supplier 360", "Partner / Agent 360" | ENGLISH → "Hồ sơ Khách hàng 360" / "Hồ sơ Nhà máy/Cung cấp 360" / "Hồ sơ Đối tác 360" |

## 4. Mojibake tìm thấy (bước đọc ghi — chưa sửa ở W1; sửa trong W4/W6 + encoding scan)

1. views/review_queue.py dòng 85: `Táº¥t cáº£` (đúng ra "Tất cả")
2. views/shipment.py dòng 496: `Lá»‹ch sá»­ thanh toÃ¡n khÃ´ng Ä‘Æ°á»£c xoÃ¡...` (đúng ra "Lịch sử thanh toán không được xóa...")
3. views/entrustment.py dòng 307: ký tự `🗑️ XÓA TOÀN BỘ SỐ LIỆU MÃ NÀY` — chuỗi cảnh báo có ký tự lạ trong chuỗi tiếng Việt đúng → kiểm tra byte
4. views/proxy_payment.py dòng 149: `💰 TỔNG VNĐ ĐÃ THU` (chủ yếu OK, chỉ emoji) — đánh dấu kiểm tra
5. views/shipment_360.py dòng 275/281/287: "ĐÃ THU", "ĐÃ TRẢ / CẤN TRỪ", "CHI PHÍ ĐÃ BIẾT" — hiển thị dấu hỏi/emoji lạ → kiểm tra byte
6. core/database.py các dòng 82, 136, 148, 479, 482, 491, 501: chuỗi lỗi tiếng Việt bị mojibake (log/admin debug — cần sửa vì admin thấy)

Xác minh byte (đọc nhị phân): views/review_queue.py dòng 85 chứa bytes `\xc3\xa1\xc2\xba\xc2\xa5t c\xc3\xa1\xc2\xba\xc2\xa3` ("Tất cả" bị double-encode UTF-8); views/shipment.py dòng 496 bytes `L\xc3\xa1\xc2\xbb\xe2\x80\xb9ch s\xc3\xa1\xc2\xbb\xc2\xad thanh to\xc3\x83\xc2\xa1n...`; views/shipment_360.py dòng 274/280/286: `\xc4\x90\xc3\x83 THU` ("ĐÃ THU"), `CHI PH\xc3\x8d \xc4\x90\xc3\x83 BI\xc3\x8aT` ("CHI PHÍ ĐÃ BIẾT"). Toàn bộ xác nhận là UTF-8 mojibake dạng double-encoding (đúng như LG02 đã chẩn đoán dạng Ã\xba/Ã\xb5).
Lưu ý: LG02 đã làm sạch mojibake trên máy Owner nhưng một số file vẫn còn sót (các chuỗi ở trên có thể chưa được quét hết ở LG02 hoặc tái xuất). Việc sửa bắt buộc trước khi ship: UTF-8 sạch (Section 25).

## 5. International-term whitelist (Section 11) — giữ nguyên, không dịch

USD, VND, CNY, EUR (tiền tệ); Incoterms (EXW, FOB, CIF); HS code; SWIFT/IBAN; Booking No, ETA, ETD, SO; container/reference codes; VAT; FX; rate card. Với các term này khi hữu ích sẽ thêm giải thích tiếng Việt kế bên (vd: `Incoterms: EXW — Nhận hàng tại xưởng`).

## 6. Internal key policy (Section 12) — không đổi

customer_id, shipment_id, agreement_id, status enum (READY_FOR_REVIEW...), key form Streamlit (key=...) giữ nguyên. Chỉ đổi label hiển thị.

## 7. Kết luận W1

Nguồn gốc chuỗi người dùng chủ yếu nằm ở: (1) navigation authority web_app.py (16 routes + 5 nhóm), (2) page shell trong từng views/*.py (title/kicker/filter/button), (3) một phần message trong core/*.py (lỗi/help cho admin). Kế hoạch: W3 glossary → W4 pilot trên 5 màn hình (Tổng quan công việc/Dashboard, Việc cần xử lý, Tạo Lô Mới, Ngữ cảnh đối tác/Khách Hàng, Đối soát tài chính) đồng thời sửa mojibake trong phạm vi pilot → W6 scale phần còn lại với pattern nhất quán.
