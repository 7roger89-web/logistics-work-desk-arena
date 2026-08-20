# Màn hình trắng — nguyên nhân chính xác — 2026-08-18

## Sự thật về cấu trúc repo
- `web_app.py` (root) = launcher 4 dòng:
  """Launcher tương thích: streamlit run web_app.py"""
  from views.web_app import main
  main()
- `views/web_app.py` = toàn bộ UI, module-level code (không có if __main__).
- views/web_app.py chứa chú thích: không dùng `from views.web_app import *`
  và không chạy trực tiếp làm main vì Python module cache → TRANG TRẮNG
  sau lần tương tác đầu tiên.

## Chuỗi lỗi của Owner
1. Trước đây: root web_app.py là BẢN CHÉP CŨ của views/web_app.py (mojibake)
   do một ai đó (hoặc Owner) tạo ra — đây chính là nguồn chữ lỗi.
2. Lệnh copy của tôi đè file root bằng views/web_app.py sạch → khi
   `streamlit run web_app.py` (root), Python chạy UI code với
   __name__='__main__' nhưng views.web_app cũng được import (bởi các
   import nội bộ từ core/views khác) → 2 module object khác nhau, cache
   → trang trắng.
3. Reproducer sandbox KHÔNG crash nhưng cũng không gặp white page vì
   không ai import views.web_app trong repro (không có core/). Trên máy
   Owner, toàn bộ repo có → đúng triệu chứng trắng.

## SỬA ĐÚNG (cho Owner)
Phương án A (đơn giản nhất — dùng app.py chuẩn):
   streamlit run app.py
Phương án B (khôi phục launcher):
   del web_app.py
   git checkout origin/log-lg01-multi-user-internal-rc -- web_app.py
   rd /s /q __pycache__ views\__pycache__
   streamlit run web_app.py

## Tại sao pull không cập nhật root web_app.py từ trước
- Root web_app.py trên rc đã là launcher sạch từ lâu; bản mojibake trên
  máy Owner là file không được git theo dõi (untracked) → pull bỏ qua.
