# Cài LOGISTICS PRO v3.1.3

1. Tắt tiến trình Streamlit cũ bằng `Ctrl+C`.
2. Giải nén ZIP vào thư mục gốc dự án và chọn ghi đè toàn bộ.
3. Chạy:

```bat
python scripts/check_router.py
streamlit run app.py
```

Kết quả `check_router.py` phải kết thúc bằng:

```text
ROUTER CHECK PASSED
```

Nếu một view phát sinh lỗi nghiệp vụ, bản này sẽ hiển thị exception ngay trong
màn hình thay vì để trang trắng.
