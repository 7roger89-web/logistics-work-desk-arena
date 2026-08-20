# Giả thuyết pyc bị bác bỏ — 2026-08-18

## Test trong sandbox
- Case 1: pyc mojibake + source sạch (mtime bằng nhau) → Python load
  SOURCE sạch. Không tái hiện lỗi.
- Case 2: pyc mojibake NEWER hơn source sạch → Python vẫn load source
  sạch (Python 3.11+ kiểm tra validation tag). Không tái hiện.

## Kết luận
Python KHÔNG thể phục vụ mojibake nếu source file trên disk sạch.
→ File đang được app Owner load KHÔNG PHẢI là
  D:\Logistics_App_GitHub\views\web_app.py sạch đó.
→ App Owner đang chạy từ MỘT BẢN SAO KHÁC của repo chứa file mojibake.
  (Owner có tab "Logistics-4" — thư mục khác.)

## Hành động dứt khoát với Owner (1 lệnh duy nhất)
dir /s /b D:\*web_app.py
(gửi kết quả toàn bộ danh sách file web_app.py trên D:)
→ so sánh từng thư mục: thư mục nào views\web_app.py chứa 'Táº¡o'
→ Owner chạy app từ thư mục đó, sửa file ở đó.

## LƯU: Owner chán chạy lệnh → trình bày ngắn gọn, đúng 1 lệnh,
kèm giải thích 1 câu. Hoặc chủ động: Owner copy-paste khối lệnh
1 lần duy nhất liệt kê mọi bản sao + kiểm tra từng bản.
