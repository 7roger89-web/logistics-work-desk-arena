# TRẠNG THÁI CUỐI CÙNG — sửa mojibake máy Owner — 2026-08-18

## Sự thật đã xác nhận nhiều lần
1. GitHub (origin/rc = a77c675, origin/main) `views/web_app.py` SẠCH
   (mojibake hits = 0, 'Tạo Lô Mới' = True). Đã commit + push từ sandbox.
2. Trên máy Owner, file disk `D:\Logistics_App_GitHub\views\web_app.py`
   sạch (findstr 'Táº¡o' = trống).
3. App live trên máy Owner (localhost:8501 qua My Browser) VẪN phục vụ
   sidebar mojibake: 'Táº¡o LÃ´ Má»›i', 'KhÃ¡ch HÃ', 'Äang cháº¡y Local
   Admin...', 'Thá»a Thuáº­n & BÃ n Giao', 'Há»£p Äá»“ng', 'Báº£o CÃ¡o CEO',
   'Tra Cá»©u Thuáº¿', 'NgÆ°á»i DÃ¹ng', 'Náº¡p kho lÆ°u trá»¯'...
4. Panel phải sạch (đến từ các view file khác).
5. Owner đã chạy app.py sau khi del+checkout launcher root web_app.py,
   kill app cũ, Ctrl+Shift+R — vẫn lỗi.
6. Owner chán, không muốn chạy lệnh nữa.

## Suy luận còn lại
- File .py sạch + app phục vụ mojibake → bytecode .pyc cũ trong
  `views/__pycache__/web_app.cpython-312.pyc` VẪN ĐƯỢC load, HOẶC
  app chạy từ THƯ MỤC KHÁC có web_app.py mojibake (thư mục của tab
  "Logistics-4"?).
- Python __pycache__ nằm trong mỗi thư mục views/. Nếu Owner không xóa
  đúng (lệnh rd bị gõ sai * thay _ nhiều lần), bytecode cũ tồn tại →
  Python load bytecode thay vì source? Streamlit KHÔNG load pyc của
  script chính — nó dùng source. NHƯNG module IMPORT views.web_app từ
  app.py? app.py gọi `from views.web_app import main` — import này
  CÓ THỂ dùng bytecode cũ nếu .pyc timestamp >= .py! Nếu Owner trước đó
  đã copy views/web_app.py mojibake làm root rồi copy ngược lại, hoặc
  .pyc cũ timestamp mới hơn .py hiện tại → import dùng pyc mojibake.
- Đây là nguyên nhân hợp lý nhất và KHÔNG cần thư mục khác.
- Streamlit cũng có module cache riêng: rerun reuse imported modules;
  Kill process là đủ nhưng nếu Python đã load views.web_app từ pyc...

## KẾ HOẠCH DỨT KHOÁT (không bắt Owner chạy lệnh nhiều)
Chủ động hướng dẫn Owner 1 lần duy nhất, rõ ràng:
1. Đóng cửa sổ CMD đang chạy app (hoặc Ctrl+C).
2. Mở CMD mới, gõ 1 khối lệnh (copy-paste 1 lần):
   cd /d D:\Logistics_App_GitHub
   del /q views\__pycache__\*.pyc 2>nul & rd /s /q views\__pycache__
   del /q __pycache__\*.pyc 2>nul & rd /s /q __pycache__
   dir /b views\web_app.py
   python -c "open('views/web_app.py',encoding='utf-8').read()"
   streamlit run app.py
3. Sau đó tôi kiểm tra qua My Browser. Nếu vẫn mojibake → chắc chắn
   có thư mục thứ 2: bắt Owner tìm `dir /s /b web_app.py` trong
   D:\ để liệt kê mọi bản sao, rồi gửi kết quả.
- Alternative chủ động hơn: yêu cầu Owner mở 2 tab file explorer
  chỉ thư mục đang chạy app? Không cần.

## Ghi chú repo/sandbox
- Sandbox repo: /home/ubuntu/logistics_repo, branch main, commit
  0d6ce55+, state.json = INTERNAL_RELEASE_VERIFIED. LG02 hoàn tất,
  không bắt đầu LG03.
- My Browser = Chrome của Owner, kết nối localhost:8501 máy anh.
- Repo GitHub: 7roger89-web/logistics-work-desk
- PAT ở /home/ubuntu/upload/pasted_file_vZOrYO_token-manus-new.txt
- App sandbox (port 8501 trong sandbox) chạy ổn, chữ Việt sạch.
