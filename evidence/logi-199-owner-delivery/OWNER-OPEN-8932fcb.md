# Mở đúng bản LOGI #199 — 8932fcb

**Trạng thái: CHƯA NGHIỆM THU. Independent Review INCOMPLETE; Windows chưa chạy thử thật.**
Đây là snapshot nguồn đúng commit để chuẩn bị chạy thử, không phải bản release
đã được reviewer phê duyệt. Chưa bắt đầu Owner UAT chính thức trước review PASS.

File: **logi199-8932fcb-source-candidate.zip** (75,236,991 bytes).
App commit: **8932fcb4aa2e7705b1e0963a830758bd3d9849ae**.
SHA-256 ZIP: `04bade45872e4793a231e7f2fc53c19c8aa5ade1679f2885f9947143a9e54a0f`.
Không dùng ZIP/tag cũ `logi199-owner-trial` (3533144).

## Windows — ba bước sau khi reviewer PASS

1. Chuẩn bị **Python 3.11 x64**, chọn **Add python.exe to PATH**, có Internet
   để cài thư viện. Không cần Node/npm hoặc MongoDB. Đây là điều kiện cần,
   **không phải xác nhận Windows đã PASS**.
2. Tải ZIP trên và giải nén vào **thư mục mới có quyền ghi**. Không chép `.env`,
   `secrets.toml`, config hoặc credential production vào đó; không chạy trong ZIP.
3. Trong thư mục giải nén, bấm đúp **`scripts\logi199_uat.cmd`**. Giữ cửa sổ
   lệnh mở; khi server khởi động, mở **http://localhost:9501** bằng trình duyệt.
   Phải thấy log `STAGING_ISOLATION_PROOF=PASS ... client=Mongomock ...
   real_uri=NO production_client=NO`. Nếu lỗi/thiếu proof, dừng và giữ log,
   không bỏ guard. Ctrl+C tắt server; dữ liệu mẫu tự mất khi tắt.

**Bấm đâu?** File khởi động là `scripts\logi199_uat.cmd`; URL sau đó là
http://localhost:9501 trên **chính máy Windows Owner**, không phải sandbox/e2b.
Port 9501 phải trống. Launcher chỉ bind 127.0.0.1, không chia sẻ/tunnel ra Internet.
Không dùng dữ liệu thật hoặc thông tin đăng nhập production.

ZIP này bảo toàn toàn bộ 1,564 file của commit gốc, kể cả tài liệu UAT cũ trong
snapshot. **Không theo link commit cũ trong docs/UAT bên trong ZIP**; dùng tờ
hướng dẫn này và UAT guide mới tại nhánh bàn giao. Source/dist không bị sửa để
đóng gói; manifest riêng ghi hash chính xác.

## Đã kiểm thật gì?

- Đã giải nén chính ZIP này và chạy app thật trên **Linux x86_64, Python 3.11.2,
  Streamlit, Chromium**, Mongomock và loopback.
- A PASS: mobile 390×844 bắt đầu BOOKING → PICKUP → CUSTOMS EXPORT; pan/zoom/Fit,
  focus và 11 node/20 cạnh giữ nguyên.
- B PASS trong lần kiểm ZIP: OLD **2026-10-04** → NEW **2026-10-11** → Lưu →
  reload → đọc lại **2026-10-11**. Không phải lưu cùng giá trị.
- Đã kiểm tĩnh launcher Windows và tải được wheels cho các dependency trực tiếp
  với target CPython 3.11 / win_amd64. Chưa cài dependency đầy đủ trên Windows,
  chưa chạy `.cmd`, chưa mở app trên Windows. **Windows/Mac PASS không được tuyên bố.**

## Blocker còn lại

Independent Reviewer chưa được giao thành công: phiên không có công cụ gọi
reviewer độc lập; đăng handoff lên issue #199 bị từ chối quyền
`Resource not accessible by integration`. Không có independent PASS.
Owner/Control Tower cần chuyển file `INDEPENDENT_REVIEW_REQUEST.md` cho reviewer
riêng. Không tự ký PASS thay reviewer.

Chưa có link web riêng tư/an toàn được kiểm từ ngoài sandbox. Không phát sinh
hosting/chi phí, không public app bỏ auth, không merge main/deploy production.
Gói này chỉ là **candidate**, không phải thông báo DONE hay cam kết Owner đã mở được.
