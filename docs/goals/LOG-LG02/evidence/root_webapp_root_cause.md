# NGUYÊN NHÂN GỐC THẬT SỰ — 2026-08-18

## Phát hiện qua My Browser + kiểm tra repo
1. Repo root chứa 2 entry point: `app.py` VÀ `web_app.py`.
2. Trên origin/rc, `views/web_app.py` hiện đã SẠCH (mojibake check False,
   'Tạo Lô Mới' True).
3. Nhưng app đang CHẠY trên máy Owner phục vụ sidebar MOJIBAKE → file mà
   Streamlit đang load là `D:\Logistics_App_GitHub\web_app.py` (bản root
   cũ, mojibake, KHÔNG được git quản lý/cập nhật).
4. Owner chạy `streamlit run web_app.py` trong thư mục root → load root
   file, KHÔNG phải views/web_app.py.

## Fix cho Owner (thực hiện qua My Browser/CMD):
- Sao chép file sạch đè lên root: `copy views\web_app.py web_app.py`
- Xóa cache: `rd /s /q __pycache__ views\__pycache__`
- Kill app cũ (Ctrl+C) rồi `streamlit run web_app.py`

## Kiểm chứng: sau khi Owner chạy, mở lại http://localhost:8501 bằng
My Browser để xác nhận sạch.

## Ghi chú
- Logo.png, data/, .streamlit/, app.py tồn tại ở root — cấu trúc repo
  hỗ trợ cả 2 cách chạy: `streamlit run app.py` (có thể là bản chuẩn?)
  và `streamlit run web_app.py`. Cần giữ nguyên: đè root web_app.py
  bằng views/web_app.py là hợp lệ vì views/web_app.py là bản chuẩn mới.
- Kiểm tra xem app.py trên rc có clean không (để Owner có thể dùng app.py).
