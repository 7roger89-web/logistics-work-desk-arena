# quotations.py — chẩn đoán 3 (CUỐI) — 2026-08-18

## Sự thật
MỌI commit của views/quotations.py trong lịch sử git đều chứa mojibake
(e518cae cũng vậy). 'KhÃ¡ch' = C3 A1 bytes = 'á' đọc sai kiểu latin-1.
Nguyên nhân gốc: Owner push file đã bị hỏng encoding từ máy anh (LOG-LG01).

## Giải pháp đúng
Decode đơn thuần: mỗi char 0x80-0xFF → emit byte; sau đó toàn bộ buffer
byte → .decode('utf-8'). KHÔNG cần NBSP heuristic, KHÔNG cần artifact map
(cho file này). BOM U+FEFF giữ nguyên (file gốc có BOM, Python đọc được).

## Trạng thái hiện tại của repo (sau git checkout 83a567c -- .)
- views/web_app.py: SẠCH (đã decode trước đó, working tree giữ nguyên)
- core/database.py: SẠCH (82c8134 + R4 gate)
- views/quotations.py: CẦN decode từ blob 83a567c (mọi history mojibake)
- Các file khác: SẠCH
