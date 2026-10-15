# LOGI-199 — Owner UAT (staging, không production)

Bản UAT này chạy **app thật** (`views.web_app.main`, React build `component/dist`) trên
**sandbox mongomock trong bộ nhớ**. Không có `MONGO_URI`, không đọc `.streamlit/secrets.toml`, không ghi DB thật.
Launcher `scripts/logi199_t6_staging_app.py` tự từ chối chạy nếu có `MONGO_URI`.

## Phương án A — chạy trên máy Owner (khuyến nghị, không cần cấp quyền mới)

Máy Owner đang có 2 instance production (8501, 8510). Dùng **port riêng 9501**, thư mục clone riêng:

```powershell
git clone https://github.com/7roger89-web/logistics-work-desk-arena.git logi-uat
cd logi-uat
git checkout ct/logi199-t6-integration        # hoặc ct/logi199-int198-preview (có #198)
python -m venv .venv; .venv\Scripts\activate
pip install -r requirements.txt pytest
$env:MONGO_URI=""; $env:AUTH_REQUIRED="false"
python -m streamlit run scripts/logi199_t6_staging_app.py --server.port 9501
```

Mở `http://localhost:9501`. Dữ liệu là bộ staging seed + 4 lô thử: `T6-FCL`, `T6-LCL`, `T6-AIR`, `T6-ROAD-LTL`.
Tắt bằng Ctrl+C khi xong. Không copy `secrets.toml` vào thư mục này.

## Phương án B — preview công khai (Streamlit Cloud từ nhánh) — **OWNER GATE**

Cần Owner tự quyết: tạo app preview riêng từ nhánh, **không** gắn secrets production,
`AUTH_REQUIRED` phải bật (hoặc app private) vì link công khai. Executor không tự tạo.

## Checklist UAT (đánh dấu PASS/FAIL)

| # | Màn hình | Thao tác | Kỳ vọng |
|---|---|---|---|
| 1 | Lô hàng → `T6-FCL` → bản đồ | Xem node | Booking chưa xong dù có số BK-160; ON BOARD chưa xong khi chỉ có ATD |
| 2 | `T6-FCL` → ON BOARD → mở bàn làm việc → Thông tin/Công việc | Nhập `2026-10-03`, Lưu | Node chuyển Hoàn thành sau khi đọc lại |
| 3 | `T6-FCL` → GATE-IN | Nhập cấp rỗng/đóng hàng/EIR | Node **vẫn chưa** hoàn thành cho tới khi nhập gate-in thực tế |
| 4 | `T6-FCL` → DELIVERY | Nhập POD khi chưa giao | Bị từ chối "POD chỉ ghi sau khi lô đã xác nhận giao" |
| 5 | `T6-LCL` | Xem node | Có "CFS / GHÉP HÀNG", **không** có GATE-IN; SI không có VGM |
| 6 | `T6-AIR` | Xem node | AWB/chuyến bay, kho/soi chiếu, uplift, hạ cánh; không có booking tàu/SI/VGM |
| 7 | `T6-ROAD-LTL` | Xem node | Nhận & ghép hàng (LTL); không có hải quan/cửa khẩu |
| 8 | Báo giá (điện thoại 390px) | Xem 3 tab + bộ lọc | Đọc được hết, không bị cắt |
| 9 | Tra cứu chính sách (390px) | Xem danh sách | Biểu tượng mở nằm trong thẻ |
| 10 | (bản `int198-preview`) lô bất kỳ | Journey 5 bước | Chứng từ đúng bước; chi phí chỉ ở bước cuối; không bắt chọn lại khách |

## Ảnh trước / sau
- Trước: `evidence/logi-199-uat/before/` (chụp tại `cbdb10f`/`d0a1b55`).
- Sau: `evidence/logi-199-t5/` và `evidence/logi-199-t6/` (do CI chụp lại trên SHA mới nhất của nhánh).
