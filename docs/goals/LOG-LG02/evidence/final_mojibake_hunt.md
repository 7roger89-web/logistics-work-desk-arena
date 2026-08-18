# Săn mojibake cuối — 2026-08-18 11:20 (trước compaction)

## Sự thật mới
1. ChatGPT (qua Owner) đề xuất chẩn đoán đúng: nghi process khác /
   import path khác. ChatGPT bảo KHÔNG cho cutover tiếp tới khi fix xong.
2. Owner chạy port mới 8601 với `python -m streamlit run web_app.py`
   từ D:\Logistics_App_GitHub → trang 8601 hiện MÀN HÌNH ĐĂNG NHẬP
   (đúng UI sạch, auth hoạt động). → D:\Logistics_App_GitHub\views\web_app.py
   + app.py chạy ĐÚNG trên máy anh.
3. `dir /s /b D:\ web_app.py` chỉ trả về 2 file, CẢ 2 TRONG
   D:\Logistics_App_GitHub: web_app.py (root) và views\web_app.py.
   → KHÔNG có bản sao repo khác trên D:.
4. File trên GitHub sạch (đã xác nhận nhiều lần).
5. App 8501 (tab cũ Owner thấy lỗi) vẫn đang chạy process khác
   (process giữ 8501) — chính Owner từng chạy `streamlit run web_app.py`
   nhiều lần; có thể app 8501 = process chạy từ ROOT web_app.py trước
   khi bị sửa (màn hình trắng), giờ là process của tab cũ.
6. Câu hỏi đang chờ Owner: findstr /c:"Táº¡o" web_app.py (file root)
   — nếu có chữ lạ → root web_app.py = thủ phạm (launcher root cũ là
   bản mojibake, chưa được git checkout lại).
   LƯU Ý: Owner từng del web_app.py rồi git checkout launcher 4 dòng
   → root hiện giờ là launcher sạch. Nhưng trước đó từng copy
   views/web_app.py mojibake lên root! Nếu checkout launcher rồi mà
   8501 vẫn mojibake... 

## Suy luận tổng hợp
- App hiện 8501 có thể là process CŨ chạy từ web_app.py root mojibake
  (trước khi Owner del+checkout) chưa bị kill (Ctrl+C ở cửa sổ KHÁC
  hoặc cửa sổ bị đóng mà process vẫn sống).
- Hoặc: Owner chưa pull root web_app.py (untracked trước đó) —
  Owner đã del + checkout launcher rồi mà tôi nghĩ...
  Actually Owner nói "xong" sau khi del+checkout+rd+app.py → nhưng app
  8501 tab cũ mở TRƯỚC khi process mới → trang trắng (do module cache
  của process đó load views.web_app cũ).
- Process 8501 hiện đang phục vụ mojibake = process của app.py cũ
  (views\web_app.py mojibake lúc đó) HOẶC process root web_app.py
  mojibake chưa bị kill.

## Kế hoạch dứt khoát (không cần Owner nhiều)
1. Owner phải KILL process 8501: trong CMD:
   for /f "tokens=5" %a in ('netstat -ano ^| findstr :8501') do @taskkill /PID %a /F
   (1 lệnh duy nhất, in ra trước PID để an toàn)
2. Rồi: cd /d D:\Logistics_App_GitHub & streamlit run app.py (hoặc dùng 8601)
3. Tôi kiểm tra qua My Browser (extension hay 504 — Owner's extension
   thỉnh thoảng treo; nếu 504 tiếp → nhờ Owner xác nhận bằng mắt).
4. Sau khi sạch: commit trạng thái LG02, báo Owner. LG02 đã đạt
   INTERNAL_RELEASE_VERIFIED; cutover production DB an toàn; KHÔNG bắt
   đầu LG03.

## Ghi chú kỹ thuật
- My Browser = Chrome extension trên máy Owner, URL my browser actions
  chạy trên localhost máy anh.
- Lệnh taskkill: cần tìm PID giữ 8501 bằng netstat -ano | findstr 8501.
- Repo: 7roger89-web/logistics-work-desk, main + rc branch, PAT file.
- Sandbox: app cổng 8501 trong sandbox vẫn chạy (riêng biệt).
