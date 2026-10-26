# Logistics Work Desk

Ứng dụng điều hành logistics nội bộ: lô hàng, hợp đồng, báo giá, tài chính, chứng từ,
phân quyền, biểu thuế, đối soát.

- **Stack:** Python 3.10+ / Streamlit (shell + toàn bộ nghiệp vụ) + một React 19 / Vite
  component là UI vỏ (`component/`).
- **Dữ liệu:** MongoDB là nguồn sự thật. `st.session_state` chỉ là cache theo phiên.
- **Entry point:** `app.py`.

**Đây là tài liệu cài đặt DUY NHẤT.** `README_HOTFIX.md`, `README_UPGRADE.md`,
`ROUTER_HOTFIX.md`, `BUILD_REPORT.md` là hồ sơ lịch sử — đọc khi cần truy vết, không
dùng để cài. Muốn hiểu kiến trúc và policy: `docs/ARCHITECTURE-PRINCIPLES.md`.

---

## 1. Yêu cầu môi trường

| Thành phần | Bắt buộc | Ghi chú |
|---|---|---|
| Python | 3.10+ | 3.11+ khuyến nghị |
| MongoDB | Khuyến nghị | Atlas hoặc replica set. Replica set cần cho transaction tài chính |
| Node.js | Chỉ khi build component | >= 18. `component/dist/` đã commit nên chạy app không cần Node |

Không có `MONGO_URI` thì app chạy trên transport staging in-memory (`mongomock`).
Tiện cho dev, nhưng xem mục 7 để tránh nhầm dữ liệu giả với dữ liệu thật.

---

## 2. Cài đặt

```bash
git clone https://github.com/7roger89-web/logistics-work-desk-arena.git
cd logistics-work-desk-arena
python -m pip install -r requirements.txt
```

Khuyến nghị: tạo virtualenv trước khi cài (`python -m venv .venv` rồi kích hoạt)
để không lẫn thư viện với các dự án khác trên cùng máy.

---

## 3. Cấu hình

App đọc cấu hình theo thứ tự ưu tiên (nguồn đầu tiên có giá trị thắng — xem
`core/config.py`):

1. **Biến môi trường** — mẫu: `.env.example` (copy thành `.env`, không commit).
2. **`st.secrets`** khi chạy bằng `streamlit run`.
3. **File `.streamlit/secrets.toml`** khi chạy script CLI bằng `python` —
   mẫu: `.streamlit/secrets.toml.example` (copy thành `.streamlit/secrets.toml`,
   không commit).

Chỉ cần chọn **một** kênh. Cả hai file mẫu đã liệt kê đúng tên biến/section mà
code thực tế đọc; khi thêm biến mới vào `core/config.py`, cập nhật cả hai file mẫu.

> **Cảnh báo — `secrets.toml` viết theo tên cũ:** ai đang giữ
> `.streamlit/secrets.toml` dùng tên cũ (`[mongodb]`, `[google]`, `MONGODB_URI`)
> thì phải đổi sang tên hiện hành `[mongo]`, `[gemini]`, `MONGO_URI` — nếu không
> app sẽ báo thiếu cấu hình dù file secrets vẫn tồn tại (code chỉ đọc tên mới;
> xem `.streamlit/secrets.toml.example`).

| Việc cần cấu hình | Biến môi trường | `secrets.toml` | Ghi chú |
|---|---|---|---|
| MongoDB URI | `MONGO_URI` | `[mongo].uri` | Không đặt → staging `mongomock` (mục 7) |
| Tên database | `MONGO_DB_NAME` | `[mongo].database` | **Bắt buộc tường minh** khi dùng DB thật; không có mặc định |
| Danh sách DB được phép | `MONGO_ALLOWED_DB_NAMES` | `[mongo].allowed_databases` | Để trống = dùng allowlist mặc định trong code |
| Danh tính môi trường | `ENV_IDENTITY` | `[env].identity` | `DEV` (mặc định) \| `STAGING` \| `PREVIEW` \| `PRODUCTION` |
| Cổng phát hành production | `MONGO_RELEASE_MODE` | `[mongo].release_mode` | Mặc định tắt. Chỉ Owner bật; xem cảnh báo ở mục 7 |
| Bắt buộc đăng nhập | `AUTH_REQUIRED` | `[auth].required` | Fail-closed: thiếu cấu hình vẫn bắt đăng nhập. Chỉ tắt cho phiên dev local cố ý |
| Tên thương hiệu hiển thị | `DISPLAY_COMPANY_NAME` | `[display].company_name` | Chỉ là tên hiển thị; pháp danh trên chứng từ luôn lấy từ dữ liệu gốc trong MongoDB |
| Gemini | `GEMINI_API_KEY` (hoặc danh sách `GEMINI_KEYS`) | `[gemini].api_key` | `[gemini].model` tùy chọn (đã có mặc định trong code) |
| DeepL | `DEEPL_API_KEYS` / `DEEPL_API_KEY` | `[deepl].api_keys` / `[deepl].api_key` | Thứ tự ưu tiên ghi trong file mẫu; khóa chỉ ở server |
| Telegram bot | `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` | `[telegram].token`, `[telegram].chat_id` | Chỉ cần khi dùng thông báo/bot |
| File biểu thuế SQLite | `TARIFF_DB_PATH` | `[paths].tariff_db` | Tạo file rỗng tương thích: `python scripts/initialize_tariff_db.py --database data/tariff.db` |
| Backend lưu chứng từ đính kèm | `ATTACHMENT_STORAGE_BACKEND` | `[attachments].storage_backend` | Mặc định `gridfs`. `drive_shared`/`drive_oauth` là tùy chọn tường minh, không tự fallback |

Google Drive (chỉ khi chọn backend `drive_shared`/`drive_oauth`) dùng
`GOOGLE_DRIVE_ROOT_FOLDER_ID` + `GOOGLE_SERVICE_ACCOUNT_JSON` (hoặc bộ ba
`GOOGLE_DRIVE_OAUTH_*` cho `drive_oauth`). Service account **không có quota Drive
riêng** nên thư mục gốc phải là thư mục ghi được **trong Google Workspace Shared
Drive** đã cấp quyền ghi cho `client_email` của service account; thư mục My Drive
chia sẻ cho service account không được hỗ trợ. Chi tiết: comment trong hai file mẫu.

Kiểm tra cấu hình đã nạp đúng mà không lộ giá trị bí mật:

```bash
python scripts/check_config.py
```

---

## File nghiệp vụ ngoài repo (KHÔNG có trong git)

Các file nghiệp vụ sau **không nằm trong git** (dữ liệu thật / template pháp lý
local-only). Thiếu file nào thì tính năng tương ứng **không chạy được**:

| File | Biến đường dẫn | Cách tạo / khôi phục |
|---|---|---|
| `tariff.db` (biểu thuế SQLite) | `TARIFF_DB_PATH` / `[paths].tariff_db` | `python scripts/initialize_tariff_db.py` (tạo file rỗng tương thích) hoặc upload qua màn hình Admin |
| `GNT_MAU.xlsx` (template GNT) | `GNT_TEMPLATE_PATH` | File local trên máy Owner — không bao giờ commit bản đã điền dữ liệu |
| `MA_NGAN_SACH.xlsx` (mã ngân sách) | `TREASURY_FILE_PATH` | File local trên máy Owner — không bao giờ commit bản đã điền dữ liệu |
| `entrustment_database.json`, `knowledge_base.json`, `cbpg_saved_data.json` (dữ liệu JSON cũ ở gốc repo) | đường dẫn gốc repo, đọc bởi script | `python scripts/migrate_local_data.py` — idempotent (upsert theo id, chạy lại nhiều lần an toàn) |
| Template DOCX/XLSX cho docgen (`HDMB` / `pl` / `pxk`...) | `DOCGEN_TEMPLATE_DIR` | Thư mục template local của Owner; thiếu thì luồng docgen fail-closed và báo **Owner gate**, không tự chế template |

---

## 4. Chạy app

```bash
streamlit run app.py
```

- `web_app.py` ở gốc repo là launcher tương thích, gọi cùng một `main()` như
  `app.py`; `start.sh` (môi trường deploy) chạy thêm bot Telegram nền rồi mới mở app.
- Lần đầu chạy khi database chưa có người dùng, app hiển thị form tạo tài khoản
  Admin đầu tiên — không có tài khoản/mật khẩu mặc định nào. Cách CLI tương đương:
  `python scripts/setup_first_user.py` (tương tác, mật khẩu không truyền qua args).
- Trên máy Owner đang có instance production ở port `8501`/`8510`: khi chạy dev/test
  UI, mở port khác, ví dụ `streamlit run app.py --server.port 9501`, và tắt khi xong.

---

## 5. Build component (chỉ khi sửa UI vỏ)

`component/dist/` đã được commit, nên chạy app thường **không** cần bước này.
Chỉ build lại khi có thay đổi trong `component/src/`:

```bash
cd component
npm install
npm run build
```

---

## 6. Cấu trúc repo (rút gọn)

| Đường dẫn | Vai trò |
|---|---|
| `app.py` / `web_app.py` | Launcher — đều gọi `views.web_app.main()` |
| `core/` | Nghiệp vụ, `config.py` (cấu hình tập trung), truy cập MongoDB, phân quyền (`auth.py`) |
| `views/` | Tầng UI Streamlit + transport staging (`logi_sandbox.py`) |
| `component/` | UI vỏ React 19 / Vite (một Streamlit custom component) |
| `scripts/` | Công cụ CLI: khởi tạo tariff DB, tạo user đầu tiên, kiểm tra cấu hình... |
| `tests/` | Test tự động (mục 8) |
| `docs/` | Kiến trúc, policy, hồ sơ/handoff các đợt việc |
| `data/` | Dữ liệu tham chiếu local (vd `tariff.db`) — file DB đã có dữ liệu **không** commit |

Ma trận phân quyền duy nhất nằm ở `core/auth.py` (`ROLE_PERMISSIONS`), gồm đủ
**7 role**: `admin`, `sale`, `support`, `accounting`, `operations`, `sales`,
`viewer` (fallback chỉ-đọc).

Chỉ có **3 role** tạo/gán được từ UI (`admin`, `sale`, `support` — theo
`core/users.SUPPORTED_ROLES`); 4 role còn lại (`accounting`, `operations`,
`sales`, `viewer`) chỉ tồn tại cho legacy/tương thích ngược và làm fallback,
KHÔNG tạo được user mới với chúng. `views/user_access.py` đã hiển thị đúng
phân biệt này (`roles.assignable` vs `roles.legacy`).

Trong đó `accounting` / `operations` / `sales` là
**tên role cũ được giữ để tương thích ngược** (với entry `secrets.toml` cũ và
test fixture cũ) — không phải nhóm quyền mới; role chưa biết luôn rơi về
`viewer`.

---

## 7. Tránh nhầm dữ liệu giả với dữ liệu thật

- Khi **không có `MONGO_URI`**, tầng UI tự lắp transport staging in-memory bằng
  `mongomock` (database `logistics_staging`, xem `views/logi_sandbox.py`). Dữ liệu
  ở chế độ này chỉ sống trong tiến trình đang chạy, **mất hết khi tắt app**, và
  transaction dùng shim giới hạn — tiện để xem/test giao diện, không phải dữ liệu thật.
- Khi **có `MONGO_URI` thật**, URI thật luôn thắng và app kiểm tra danh tính
  database kiểu fail-closed (`core/config.py::validate_mongo_identity`): phải có
  `MONGO_DB_NAME`, tên DB phải nằm trong allowlist, `STAGING`/`PREVIEW` bị chặn ghi
  vào DB production (`logistics_db`), còn `PRODUCTION` chỉ được chạy khi
  `MONGO_RELEASE_MODE=true` — cổng này chỉ Owner mới bật.
- Trước khi nhập liệu quan trọng, xác nhận môi trường bằng
  `python scripts/check_config.py` thay vì đoán theo giao diện.

---

## 8. Kiểm tra

```bash
python -m pytest tests -q
```

Sự thật hiện trạng của bộ test (đừng tin tài liệu cũ, đừng tin con số hard-code):

- Bộ test có ~130+ file (`test_*.py`, hiện tại là 144 file — con số trôi theo thời
  gian) và suite **ĐANG ĐỎ CÓ CHỦ Ý**: một tập FAILED/ERROR đã biết được giữ
  nguyên như backlog sống. **Không hard-code số test pass vào tài liệu.**
- Quy trình bắt buộc khi sửa bất cứ thứ gì: chạy **full suite 1 lần TRƯỚC** khi
  sửa để lấy baseline danh sách FAILED/ERROR, rồi chạy lại **SAU** khi sửa và so
  sánh — một thay đổi đúng phải **giữ nguyên tập FAILED/ERROR cũ** và chỉ thêm
  test mới (pass). Số pass tăng mà tập fail đổi shape = có regression.
- Lịch sử đã biết để đối chiếu: ~**1492–1541 passed / 24 failed** (xem
  `CHANGELOG.md`); tập failed thực tế có thể đã lớn hơn ở HEAD hiện tại — luôn
  báo con số của lần chạy kèm commit.
- Test cần Streamlit/MongoDB **thật** được **skip theo thiết kế** khi chạy ở chế
  độ thuần (pure) — không cố sửa chúng thành chạy được.
- Một số file test có thể lỗi ngay ở bước collection trên HEAD hiện tại (ví dụ
  import symbol không còn tồn tại); khi lấy baseline dùng
  `--continue-on-collection-errors` để phần còn lại của suite vẫn chạy.

---

## 9. Tài liệu liên quan & quy tắc an toàn

- Kiến trúc và policy: `docs/ARCHITECTURE-PRINCIPLES.md`.
- Luật làm việc cho AI executor/agent trong repo này: `AGENTS.md`.
- Không commit `.env`, `.streamlit/secrets.toml`, khóa service account
  (`google_key.json`, `*.pem`...) hay database đã có dữ liệu — `.gitignore` đã chặn
  sẵn; nếu `git status` vẫn hiện các file này thì dừng lại và kiểm tra trước khi commit.

---

## Khoảng trống đã biết

- LICENSE chưa có (GitHub báo `license: null`).
- Không có repo description và topics.
- `.agents/` bị ignore một phần nên file mới thêm vào đó vô hình với `git add .`.
- 258 branch, 1 tag, 25 open issue.
- Thiếu `pyproject.toml` / `pytest.ini` / `ruff.toml`.
- `requirements.txt` không lock, còn `streamlit-option-menu` nghi đã chết.
- Repo ~189 MB nên clone chậm.
