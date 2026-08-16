# LOGISTICS PRO Core Consolidation v3.1.1

Gói này được thiết kế để **giải nén trực tiếp vào thư mục gốc của dự án** và ghi đè các file cùng tên.

## Hotfix cấu hình CLI 3.1.1

- Script chạy bằng `python scripts/...` tự đọc `.streamlit/secrets.toml`, không phụ thuộc `st.secrets`.
- Không còn cảnh báo `missing ScriptRunContext` từ lớp database/config khi chạy CLI.
- Hỗ trợ secrets mới dạng `[mongo]`, `[telegram]`, `[gemini]` và secrets cũ dạng `MONGO_URI`, `TELEGRAM_TOKEN`, `GEMINI_KEYS`.
- Bổ sung `python scripts/check_config.py` để kiểm tra file cấu hình và ping MongoDB mà không in secret.
- Secrets cũ không có MongoDB URI vì URI từng nằm trong source; phải thêm URI mới đã rotate.
- Xem hướng dẫn chi tiết tại `SECRETS_MIGRATION.md`.

## Nội dung đã triển khai

- Loại bỏ MongoDB URI/mật khẩu khỏi source code.
- Kết nối MongoDB qua `.streamlit/secrets.toml` hoặc biến môi trường.
- Một nguồn tính toán tài chính duy nhất tại `core/logic.py`.
- Tách doanh thu trước VAT, VAT đầu ra, tổng phải thu, chi phí, hoa hồng, lợi nhuận và công nợ.
- Chuẩn hóa dữ liệu cũ nhưng vẫn giữ các key `0.0`, `1.2`, `2.4`, `2.6`, `2.7`, `3.4` để tương thích.
- Validation có `errors` và `warnings`.
- Optimistic locking bằng `version` để hạn chế ghi đè khi nhiều người cùng sửa.
- Audit log, soft delete và soft archive.
- Notification outbox cho Telegram.
- MongoDB storage cho Knowledge Base, CBPG workspace và Ví ký quỹ.
- Sửa lỗi xuất GNT từ `st.data_editor` và lỗi số tiền dạng float có thể bị nhân sai khi xử lý dấu chấm.
- Sửa lỗi xuất GetFly nhận sai kiểu dữ liệu.
- Mapping trạng thái GetFly thay vì tự động đánh dấu mọi lô là hoàn thành.
- Customer liên kết bằng `customer_id`, vẫn fallback theo tên cho dữ liệu cũ.
- Màn Thu Tiền & Công Nợ với phân bổ FIFO và idempotency key.
- Tracking URL đầy đủ.
- Gemini HS dùng `google-genai` và structured JSON output; kết quả luôn gắn cờ chuyên viên duyệt.
- CBPG yêu cầu bằng chứng khi chọn tiêu chí ngoại trừ và không còn kết luận tuyệt đối “an toàn”.
- Archiver không còn di chuyển/xóa document; chỉ đánh dấu `is_archived`.

## Yêu cầu môi trường

- Python 3.10 trở lên.
- MongoDB Atlas hoặc MongoDB replica set nếu sử dụng transaction phân bổ công nợ.

## Cài đặt

### 1. Sao lưu

Sao lưu thư mục dự án và MongoDB trước khi ghi đè.

### 2. Giải nén

Giải nén nội dung ZIP vào **thư mục gốc dự án**, chọn ghi đè file trùng tên.

Cấu trúc sau khi giải nén:

```text
app.py
web_app.py
core/
views/
scripts/
tests/
.streamlit/
requirements.txt
```

### 3. Cài thư viện

```bash
python -m pip install -r requirements.txt
```

### 4. Cấu hình secrets

Sao chép:

```bash
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
```

Trên Linux/macOS:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Điền MongoDB URI mới vào `.streamlit/secrets.toml`. **Phải đổi mật khẩu MongoDB cũ đã xuất hiện trong source code trước đây.**

Các tích hợp Gemini và Telegram là tùy chọn. App vẫn chạy khi chưa cấu hình hai tích hợp này; riêng nút AI/worker Telegram sẽ thông báo thiếu khóa.

### 5. Kiểm tra cấu hình và dữ liệu

```bash
python scripts/check_config.py
python scripts/check_data_quality.py
```

### 6. Chuyển JSON cũ sang MongoDB

Script có tính idempotent, có thể chạy lại:

```bash
python scripts/migrate_local_data.py
```

Script tự tìm tại thư mục gốc:

- `entrustment_database.json`
- `knowledge_base.json`
- `cbpg_saved_data.json`

### 7. Tạo index

```bash
python scripts/bootstrap_indexes.py
```

Nếu unique index báo lỗi, chạy `check_data_quality.py` và xử lý các ID trùng được liệt kê trước.

### 8. Khởi chạy

```bash
streamlit run app.py
```

Hoặc tương thích lệnh cũ:

```bash
streamlit run web_app.py
```

## Bật đăng nhập

Mặc định `auth.required = false` để không khóa ứng dụng ngay sau khi ghi đè.

Sinh password hash:

```bash
python scripts/generate_password_hash.py
```

Dán hash vào `.streamlit/secrets.toml`, sau đó đặt:

```toml
[auth]
required = true
```

Mỗi tài khoản có `display_name` và `role`. Gói đã có phân quyền menu theo các vai trò `admin`, `accounting`, `operations`, `sales`, `viewer`; thao tác xóa Shipment/Thanh toán hộ/Sổ tay chỉ dành cho `admin`.

## Telegram worker

Có thể chạy mỗi phút hoặc mỗi 5 phút bằng Task Scheduler/Cron:

```bash
python scripts/process_notifications.py
```

Worker có retry theo cấp số nhân và lưu trạng thái trong `notification_outbox`.

## Soft archive

Chạy thủ công hoặc theo lịch:

```bash
python scripts/archiver.py
```

Chỉ các lô `done` và công nợ nằm trong dung sai 1.000 VNĐ mới được đánh dấu archive. Dữ liệu vẫn nằm trong `shipments`, nên báo cáo lịch sử không bị mất.

## Kiểm thử

```bash
python -m unittest discover -s tests -v
```

Bộ test đi kèm kiểm tra:

- VAT không bị tính thành lợi nhuận.
- Tương thích các field tài chính cũ.
- Financial snapshot.
- Parse tiền theo định dạng Việt Nam/quốc tế.
- Parse ngày.
- Validation khách hàng, ngày và thanh toán.
- Parse file GetFly với dấu phân cách tiền Việt Nam.
- Số tiền GNT từ Streamlit không bị biến đổi sai.

## File nghiệp vụ bên ngoài

Gói không tạo thay các dữ liệu nghiệp vụ riêng của doanh nghiệp. Đặt các file hiện có tại thư mục gốc hoặc cấu hình đường dẫn trong secrets:

- `tariff.db`
- `GNT_MAU.xlsx`
- `MA_NGAN_SACH.xlsx`
- `GNT_MAU.docx` nếu còn xuất GNT Word

## Lưu ý triển khai

- MongoDB là nguồn sự thật; `st.session_state` chỉ là cache theo phiên.
- Không chạy lại script archiver cũ có thao tác insert sang collection khác rồi delete Shipment.
- Không đưa `.streamlit/secrets.toml` vào Git.
- Thu hồi mọi key/token/private key từng xuất hiện trong source hoặc hội thoại; không tái sử dụng credential cũ.
- Sau khi đổi credential, thu hồi MongoDB user cũ hoặc đổi mật khẩu ngay.
