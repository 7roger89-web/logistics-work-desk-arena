# Màn hình trắng sau khi copy — 2026-08-18

## Quan sát
- Trang http://localhost:8501 trên máy Owner: trống, chỉ còn nút Deploy +
  menu (khung Streamlit shell render được nhưng script không chạy được
  nội dung) → app BỊ CRASH lúc boot.

## Giả thuyết
- `copy views\web_app.py web_app.py`: root web_app.py giờ trùng tên với
  module views.web_app → khi Python import 'views.web_app' từ code bên
  trong, có thể xung đột module; hoặc web_app.py root chạy với
  sys.path[0] khác → import 'views.dashboard' OK nhưng...
- Khả năng cao: views/web_app.py gọi `from views.xxx import ...` và có
  code chạy ở module level phụ thuộc vị trí file; chạy từ root làm
  main: tên module '__main__' — import views.web_app (bên trong?)
  tạo module 2 lần, không crash thường.
- Crash khả dĩ hơn: trong views/web_app.py có dòng tìm file config
  dựa on __file__ (ví dụ .streamlit ở thư mục cha?) — chạy từ root thì
  thư mục cha khác → secrets.toml không tìm thấy → MONGO_RELEASE_MODE
  OFF → connect localhost → fail? Không, secrets vẫn load.
- HOẶC: file views/web_app.py trên rc bị sửa bởi git merge/fix và chứa
  lỗi runtime mới (my hotfix). Cần kiểm tra: chạy file gốc (từ repo
  clone) từ ROOT directory trong sandbox và xem có crash không.

## Hành động
1. Trong sandbox: cd repo, `cp views/web_app.py .`, chạy
   `streamlit run web_app.py --server.headless true` và xem log crash.
2. Nếu crash → fix tại nguồn repo, push, Owner pull + copy lại.
3. Nếu không crash → crash ở máy Owner là do cache __pycache__ root
   có bytecode cũ của web_app.py (root copy) với cấu trúc khác →
   Owner phải xóa __pycache__ root (rd /s /q __pycache__).
