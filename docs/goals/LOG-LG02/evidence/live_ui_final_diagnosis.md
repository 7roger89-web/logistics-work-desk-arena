# CHẨN ĐOÁN SỐNG QUA MY BROWSER — 2026-08-18 (quyết định)

## Quan sát live trên máy Owner (localhost:8501 qua My Browser)
Sidebar TRÁI vẫn mojibake 100%: 'Táº¡o LÃ´ Má»›i', 'KhÃ¡ch HÃ',
'Äang cháº¡y Local Admin...', 'Thá»a Thuáº­n & BÃ n Giao', 'Há»£p Äá»“ng',
'Báº£o CÃ¡o CEO', 'Tra Cá»©u Thuáº¿', 'Sá»• Tay Kinh Nghiá»‡m',
'NgÆ°á»i DÃ¹ng', 'Náº¡p kho lÆ°u trá»¯', 'Thu Tiá»n & CÃ´ng Ná»£',
'CÃ´ng ná»£ A BÃ²', 'Báº£o CÃ¡o CEO'.
Panel PHẢI sạch 100%: 'Giao Việc Nhanh', 'Sổ Tay Nháp', 'Lưu Trữ',
'BỘ LỌC DỮ LIỆU & THỜI GIAN', 'Bảng Việc Đang Chờ', 'Lịch Sử Đã Xong',
'Lô hàng cần xử lý'...

## Sự thật đã xác nhận
1. `origin/rc:views/web_app.py` = SẠCH (mojibake hits: 0, 'Tạo Lô Mới' = True).
2. `origin/main:views/web_app.py` = SẠCH giống hệt.
3. Owner đã pull đến a77c675 (nhận đủ file sạch), del + checkout launcher,
   chạy app.py → UI vẫn mojibake.
4. Sidebar labels đến từ ROUTES trong views/web_app.py → file sạch trên
   GitHub nhưng app phục vụ mojibake → FILE TRÊN DISK của Owner KHÁC với
   GitHub.

## Kết luận vững chắc
Máy Owner đang phục vụ web_app.py CHƯA SẠCH. Nguyên nhân: git pull đã
cập nhật tracking nhưng `views/web_app.py` trên disk của Owner có thể
KHÔNG đổi vì git thấy local copy bằng remote hash? KHÔNG — pull fast-forward
phải cập nhật. TRỪ KHI: Owner chạy `streamlit run app.py` từ THƯ MỤC KHÁC
D:\Logistics_App_GitHub\... hoặc có 2 thư mục repo (tab Logistics-4 và
logistics-1). Hoặc git pull chỉ fetch rc; nếu app.py trên disk old thì...
app.py import views.web_app — file đó clean trên disk sau pull.

→ Khả năng cao nhất: Owner có 2 bản sao repo (D:\Logistics_App_GitHub và
thư mục khác, tab "Logistics-4" vs "logistics-1"). App đang chạy từ bản
sao cũ chứa web_app.py mojibake. Trước đó Owner từng nói tab "Logistics-4"
và "logistics-1" là 2 tab Chrome.

## Cách xác định dứt khoát (đưa cho Owner 1 lệnh duy nhất)
Trong CMD thư mục anh đang chạy app, gõ:
  findstr /c:"Táº¡o" views\web_app.py
- Hiện chữ lạ → file trên disk chưa sạch → pull chưa chạm được file này
  (file đang bị Git lock/modification?) → del views\web_app.py rồi
  git checkout origin/log-lg01-multi-user-internal-rc -- views\web_app.py
- KHÔNG hiện gì → file sạch → app đang chạy từ thư mục repo KHÁC
  (thư mục nào mà tab Chrome kia mở?) → tìm thư mục: where /r D: web_app.py
  rồi kiểm tra từng thư mục.

## LƯU Ý quan trọng cho Owner
- Anh có 2 tab Chrome ("Logistics-4", "logistics-1") — có thể 2 thư mục
  app khác nhau. Mỗi tab chạy 1 thư mục.
- Lệnh `rd /s /q views\__pycache__` anh gõ sai nhiều lần (* thay _),
  cần nhắc lại chính xác.
