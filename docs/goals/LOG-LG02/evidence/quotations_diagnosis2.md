# quotations.py — chẩn đoán 2 — 2026-08-18

## Phát hiện
Blob 83a567c của views/quotations.py KHÔNG phải mojibake kiểu "byte→glyph".
Nó là DẠNG ĐÃ BỊ CHUẨN HÓA NFD (tách tone): ví dụ 'Để đế' = 'Để đế' với
dấu tách rời (ký tự tone dạng decomposed như U+0300..U+0328 đi cùng chữ gốc,
hoặc dấu tách thành ký tự riêng như 'ệ' → 'e' + U+0323?). Khi decode() xử
lý, các char tone > 0xFF encode utf-8 bình thường, nhưng NBSP-loss heuristic
trên byte suspect phá cấu trúc, và kết quả cuối có '→' (U+2192) gây
SyntaxError ở string trong code? Không — '→' trong string thì OK, nhưng
dấu '–'... SyntaxError reported at line 1: '→' character INSIDE the file
content after BOM strip produced garbled line-1 that Python complains.

## Kết luận
quotation.py blob: tone-vowel đã bị tách NFD hoặc mất hoàn toàn ('Để đ' +
tone rời). Không thể tự động khôi phục hoàn chỉnh bằng decoder.

## Giải pháp thực dụng
1. Kiểm tra git log —refs của views/quotations.py: có thể có commit trước đó
   chứa bản sạch (Owner đẩy mojibake trong 1 commit riêng của PR).
2. Nếu không có bản sạch nào: khôi phục tone bằng NFC normalize + heuristic
   tone-repair cho các ký tự tone rời (U+0300..U+0328 → gộp lại bằng
   unicodedata NFC).
3. Nếu vẫn hỏng: Owner có bản local sạch (máy anh trước khi push) — yêu cầu
   anh kiểm tra file gốc; hoặc tôi rebuild thủ công từ các chuỗi hiển thị
   trong các file khác (không khả thi vì quotations.py là module mới).
