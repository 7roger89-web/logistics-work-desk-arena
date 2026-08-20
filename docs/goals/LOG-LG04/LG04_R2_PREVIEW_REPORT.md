# LOG-LG04 R2 — Bản xem thử 2.0

## 1. LOG-LG04 R2 STATUS: XONG CODE — CẦN ANH XEM THỬ LẠI

Anh phản hồi rằng bản 1.0 có 3 vấn đề: (a) thẻ "Mở..." làm anh phải cuộn ngược lên xuống, (b) Support không nhập được tài chính, (c) Dashboard chưa lọc theo tháng. Tôi đã sửa cả 3 — bản 2.0 sẵn sàng cho anh xem thử.

## 2. 5 ĐIỂM ANH PHẢN HỒI → ĐÃ SỬA GÌ

| # | Anh nói | Tôi sửa |
|---|---------|---------|
| 1 | "Mở Xuất khẩu", "Mở Nhập khẩu", "Mở Chi phí" làm phải cuộn ngược | **Bỏ hoàn toàn 3 thẻ này.** Thay bằng 3 khối việc chính hiển thị trực tiếp ngay đầu màn hình — mỗi khối có tiêu đề, tóm tắt trạng thái, và nút "Cập nhật" nhỏ bên phải. Không phải cuộn ngược nữa. |
| 2 | Support không nhập được chi phí/giá bán | **Cấp quyền `finance_write` cho Support.** Support giờ nhập được chi phí, giá bán, thanh toán trực tiếp trên lô hàng (vẫn bị cấm xóa/thay đổi tổng hợp, chỉ được nhập trên lô). |
| 3 | Dashboard hiển thị tất cả lô, không tập trung | **Bộ lọc thời gian mặc định = "Tháng này".** App mở ra chỉ hiện lô hàng tháng này. Lô quá hạn vẫn hiện trong mục "Việc cần xử lý" (cơ chế carry-over tự động). |
| 4 | Nhãn mức độ việc tiếp theo khó hiểu | **Đổi nhãn:** "NGHIÊM TRỌNG" → "KHẨN CẤP / QUÁ HẠN", "CẦN XỬ LÝ SỚM" → "CẦN XỬ LÝ", "CÔNG VIỆC TIẾP THEO" → "BÌNH THƯỜNG", "GỢI Ý KIỂM TRA" giữ nguyên. |
| 5 | "👥 Ai tham gia lô hàng này" → đổi tên | **Đổi thành "📞 Liên hệ nhanh".** Ý nghĩa: số điện thoại, địa chỉ lấy/giao hàng — dùng để gọi và đi giao hàng. |

## 3. CẤU TRÚC MÀN HÌNH MỚI (1 màn hình lô hàng)

```
┌─────────────────────────────────────────┐
│ LO-0306 · Khách ABC                     │  ← Header gọn 2 dòng
│ Cát Lái → Port Klang · Sea · FOB       │
├─────────────────────────────────────────┤
│ 🚨 VIỆC TIẾP THEO · KHẨN CẤP/QUÁ HẠN   │  ← Card nổi bật
│ Free time sắp hết...                    │
│ [⬇ Xử lý ngay]                          │
├─────────────────────────────────────────┤
│ 🚛 Lấy hàng & Xuất khẩu                 │  ← Khối việc 1
│ Mode: Sea · Booking: BK-001 · ...       │  ← Tóm tắt trạng thái
│ ⚠️ Thiếu: MBL, ETD                     │  ← Cảnh báo thiếu
│                     [Cập nhật]          │  ← Nút nhỏ, 1 click
├─────────────────────────────────────────┤
│ 🛃 Nhập khẩu & Giao hàng                │  ← Khối việc 2
│ ETA: ... · Free time: ... · TK HQ: ...  │
│                     [Cập nhật]          │
├─────────────────────────────────────────┤
│ 💰 Chi phí & Công nợ                    │  ← Khối việc 3
│ Phải thu: 5M · Phải trả: 3M · ...      │
│                     [Cập nhật]          │
├─────────────────────────────────────────┤
│ [5 ô tín hiệu: Vận hành / Tài chính /   │  ← Tóm tắt nhanh
│  Chủ sở hữu / Hạn khách / Free time]    │
├─────────────────────────────────────────┤
│ 📞 Liên hệ nhanh                        │  ← Đóng/mở
├─────────────────────────────────────────┤
│ ❌ Thiếu 2 chứng từ: House BL, Invoice  │  ← Tín hiệu ngắn
│ [Xem chứng từ]                          │
├─────────────────────────────────────────┤
│ 🏭 Hàng từ nhà máy (nếu có)             │  ← Đóng/mở
├─────────────────────────────────────────┤
│ 🕒 Lịch sử / audit                      │  ← Đóng/mở
└─────────────────────────────────────────┘
```

**1-click tới việc:** Anh mở lô hàng → thấy ngay 3 khối việc → bấm "Cập nhật" → app chuyển sang trang chi tiết với tab đúng đã mở sẵn (Xuất khẩu / Nhập khẩu / Chi phí). Không phải cuộn ngược.

## 4. DASHBOARD MỚI

```
Khoảng thời gian: [Tháng này ▼]     ← Mặc định "Tháng này"
┌─────────────────────────────────────────┐
│ ĐANG HIỂN THỊ: 01/08/2026 đến 31/08/2026│
├─────────────────────────────────────────┤
│ 📋 DASHBOARD │ TOP KHÁCH │ GETFLY │ ... │
├─────────────────────────────────────────┤
│ Lô hàng tháng này (chỉ lô trong tháng)   │
│ + Lô quá hạn chưa xong (carry-over)     │
└─────────────────────────────────────────┘
```

- Mặc định chỉ hiện lô tháng này.
- Lô quá hạn chưa xong vẫn hiện (carry-over tự động).
- Ô tìm kiếm giữ nguyên.

## 5. QUYỀN HẠN MỚI

| Vai trò | Trước R2 | Sau R2 |
|---------|----------|--------|
| Admin | Tất cả | Tất cả |
| Sale | Không chạm tài chính | Không chạm tài chính (giữ nguyên) |
| Support | Chỉ đọc tài chính | **Nhập chi phí, giá bán, thanh toán trên lô hàng** |
| Viewer | Chỉ đọc | Chỉ đọc (giữ nguyên) |

Support vẫn **không thể**: xóa lô, tạo lô mới, tạo báo giá, sửa tổng hợp công nợ khách hàng, quản lý người dùng.

## 6. KIỂM TRA TỰ ĐỘNG

- **Regression:** 231 passed, 28 skipped, 0 failed ✅
- **Mojibake (lỗi chữ):** 0 ✅
- **RBAC:** PASS ✅
- **Finance oracle:** PASS ✅

## 7. PRODUCTION SHA & GIT

- **PR #3 HEAD:** `a7361fd` (đã cập nhật với R2)
- **PR #3 URL:** https://github.com/7roger89-web/logistics-work-desk/pull/3
- **Production (máy anh, chưa merge):** `3c1e1c7` (LG03)

## 8. CÁCH XEM THỬ (trên máy anh)

Trong cmd (cửa sổ mới, không phải cửa sổ đang chạy app):

```
cd /d D:\Logistics_App_GitHub
git fetch origin log-lg04-daily-work-simplification
git checkout FETCH_HEAD
streamlit run app.py --server.port 8502
```

Sau đó vào trình duyệt: **http://localhost:8502**

## 9. LOG-LG04 R2 — 5 TIÊU CHÍ "1-CLICK TỚI VIỆC"

| # | Tiêu chí | Đạt? |
|---|----------|------|
| 1 | Mở lô hàng → thấy ngay việc cần làm (không phải cuộn) | ✅ |
| 2 | Bấm "Cập nhật" → đến đúng tab nhập liệu | ✅ |
| 3 | Support nhập được chi phí/giá bán | ✅ |
| 4 | Dashboard mặc định chỉ hiện tháng này | ✅ |
| 5 | Lô quá hạn vẫn hiện (carry-over) | ✅ |

## 10. ANH CẦN LÀM

1. Chạy bản xem thử trên cổng 8502 (lệnh ở mục 8).
2. Mở 1 lô hàng, nhìn từ trên xuống: card việc tiếp theo → 3 khối việc → nút Cập nhật.
3. Thử bấm "Cập nhật" ở khối Chi phí — phải mở tab Tài chính với form nhập liệu.
4. Thử đăng nhập bằng tài khoản Support (nếu anh có) — phải nhập được chi phí.
5. Nhắn tôi kết quả:

> Điểm từ 1 đến 10: ___
> Chỗ thích: ___
> Chỗ không thích: ___
> Quyết định: DUYỆT / CHƯA OK
