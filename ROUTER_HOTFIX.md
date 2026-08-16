# LOGISTICS PRO v3.1.3 Router Hotfix

## Lỗi đã sửa

Launcher cũ dùng:

```python
from views.web_app import *
```

Python chỉ thực thi module import ở lần đầu. Khi người dùng bấm menu, Streamlit
rerun `app.py`, nhưng `views.web_app` đã nằm trong module cache nên mã render
không chạy lại và trình duyệt chỉ còn trang trắng.

Launcher mới luôn gọi hàm render:

```python
from views.web_app import main
main()
```

Ngoài ra:

- Menu `streamlit-option-menu` được thay bằng `st.radio` native để giảm lỗi
  component ở lần rerun.
- View được import theo route đang chọn thay vì import toàn bộ ngay khi mở app.
- Mỗi route có error boundary; exception sẽ hiện rõ trên trang thay vì trắng.
- Có script `python scripts/check_router.py` để kiểm tra toàn bộ route.

## Cài đặt

Giải nén ZIP vào thư mục gốc, chọn ghi đè, sau đó chạy:

```bat
python scripts/check_router.py
streamlit run app.py
```

Nên dừng cửa sổ Streamlit cũ bằng `Ctrl+C` trước khi chạy lại.
