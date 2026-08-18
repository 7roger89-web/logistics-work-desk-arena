# ĐỊNH HƯỚNG KHÔI PHỤC — 2026-08-18

## Phát hiện quyết định
- Commit 83a567c (PR #1 merge) chứa TOÀN BỘ file .py SẠCH tiếng Việt
  (0 FFFD, 0 mojibake) cho hầu hết file.
- My first "mojibake fix" (fix_repo_mojibake.py) + rebuild_from_mojibake.py
  đã GHI ĐÈ file SẠCH thành file HỎNG (U+FFFD, 0xA0 mất) vì decoder
  hiểu nhầm byte lành thành mojibake.
- views/web_app.py trên máy Owner có mojibake vì file của anh bị hỏng
  ở CẤP MÁY (sau khi pull/merge — có thể do editor/tool của anh encode
  lại UTF-8->latin-1->UTF-8).

## Kế hoạch khôi phục
1. Khôi phục TOÀN BỘ file .py (trừ docs) về trạng thái commit 83a567c:
   git checkout 83a567c -- *.py (làm từng thư mục)
2. Re-apply cổng R4 vào core/database.py (delete_shipment gate).
3. Verify: 0 FFFD, 0 mojibake artifact, compile toàn bộ, UI strings OK.
4. Commit + push. Hướng dẫn Owner pull bản này.

## Vì sao máy Owner vẫn mojibake khi pull bản sạch
Nếu Owner pull 83a567c mà chữ vẫn lỗi, thì corruption nằm ở tool trên máy
anh đang encode lại file khi git checkout (vd: .gitattributes text=auto +
CRLF? không — encoding không đổi với CRLF). Khả năng còn lại: anh dùng
công cụ mở/convert file (vd: Notepad++ convert) hoặc git của anh có
filter smudge. Cần kiểm tra sau khi Owner pull.
