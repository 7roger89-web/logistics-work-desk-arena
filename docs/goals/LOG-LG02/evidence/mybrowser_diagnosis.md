# Chẩn đoán qua My Browser — 2026-08-18

## Quan sát tận mắt (localhost:8501 trên MÁY OWNER)
- Sidebar: vẫn mojibake toàn bộ — 'Táº¡o LÃ´ Má»›i', 'KhÃ¡ch HÃ',
  'Thá»a Thuáº­n & BÃ n Giao', 'Äang cháº¡y Local Admin...', 'Há»£p Äá»“ng',
  'Äáº·t lÆ°u trá»¯'(?), 'Báº£o CÃ¡o CEO'.
- Panel phải phần lớn SẠCH (Giao Việc Nhanh, Sổ Tay Nháp, Lưu Trữ,
  BỘ LỌC DỮ LIỆU & THỜI GIAN — đúng tiếng Việt).
- Banner app version: 'LOG-C07 · 3.1.3-router-hotfix'.

## Suy luận
- String sạch ở panel phải = các file views khác (dashboard.py,...) ĐÃ sạch.
- Sidebar = views/web_app.py — đang phục vụ bản MOJIBAKE.
- Câu hỏi: web_app.py trên origin/rc hiện có mojibake không?
  → Phải kiểm tra: git show origin/log-lg01-multi-user-internal-rc:views/web_app.py
  → Nếu repository SẠCH nhưng app phục vụ mojibake → app Owner đang chạy
    từ thư mục/file KHÁC (ví dụ: tab "Logistics-4" chạy từ thư mục khác
    và Owner kill tab "logistics-1" nhưng tab kia đang chạy), hoặc Python
    cache (views/__pycache__), hoặc web_app.py ở thư mục gốc repo
    (D:\Logistics_App_GitHub\web_app.py) trong khi pull cập nhật views/web_app.py.
- LƯU Ý: Owner chạy `streamlit run web_app.py` → Streamlit chạy file
  `web_app.py` trong CWD. Nếu CWD = D:\Logistics_App_GitHub và file
  `web_app.py` gốc tồn tại ở đó (copy cũ của views/web_app.py?) →
  đó là nguồn mojibake!
- Trước đây có file /home/ubuntu/logistics_repo/web_app.py (repo root)?
  Cần kiểm tra git ls-tree origin/rc -- để xem cấu trúc repo.

## Hành động
1. Kiểm tra tree của origin/rc: views/web_app.py có mojibake?
2. Kiểm tra repo root có web_app.py không.
3. Nếu repo sạch: hướng dẫn Owner xác định file nào streamlit đang load.
