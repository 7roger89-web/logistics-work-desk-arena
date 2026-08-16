# BUILD REPORT — LOGISTICS PRO v3.1.3 Router Hotfix

Build date: 2026-07-29

## Root cause

`app.py` và `web_app.py` trước đó chỉ thực hiện:

```python
from views.web_app import *
```

Ở lần chạy đầu, import thực thi phần render. Khi người dùng tương tác, Streamlit
rerun launcher nhưng Python tái sử dụng module `views.web_app` trong
`sys.modules`; top-level render không được thực thi lại nên trang trống.

## Fixes

- Launcher gọi `main()` trong mọi lần rerun.
- `views/web_app.py` không còn render ở import-time.
- Thay `streamlit-option-menu` bằng `st.radio` native.
- Lazy-import view đang được mở.
- Error boundary cho từng route, có traceback trên UI.
- Thêm `scripts/check_router.py`.

## Verification

- Python compileall: PASS
- Route registry: 12/12 module và entry function tồn tại
- Launcher `app.py`: PASS, gọi `main()`
- Launcher `web_app.py`: PASS, gọi `main()`
- Launcher import-star: không còn
- `.streamlit/secrets.toml`: được giữ trong full-config package
