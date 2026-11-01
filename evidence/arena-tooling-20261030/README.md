# Bằng chứng nghiệm thu Serena MCP & Playwright CLI trong môi trường Arena

- **Ngày thực thi:** `2026-10-30` (UTC)
- **Repository:** `7roger89-web/logistics-work-desk-arena`
- **Nhánh staging mục tiêu:** `arena/ae5f9f47-logistics-work-desk-arena`
- **HEAD staging đo lại:** `aa5df4bc13fb92f36f39f6ec40d8df5f479f08a1` (`main` giữ nguyên tại `9e4190b278dd2ced8771c5249582753d34e561db`)
- **Môi trường Arena:** E2B Firecracker microVM (`E2B_SANDBOX_ID=is4fwfdjwuk863hguikxj`, `E2B_TEMPLATE_ID=mn0k6lgvyo6q8utbj8jh`), Debian 12 (`6.1.158+`), `Python 3.11.2`, `Node.js v22.22.3` (`npm 10.9.8`), outbound allowlist chỉ mở `github.com`, `codeload.github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`.

## Tóm tắt kết quả

| Hạng mục | Kết quả | Ghi chú ngắn |
|---|---|---|
| `SERENA_INSTALL` | `PASS` | Cài cô lập tại `/tmp/serena-venv` (`serena-agent==2.1.0`) + `/tmp/serena-pyright` (`pyright@1.1.403`). Server khởi chạy với `--context codex --mode no-memories --agent-interface tools --transport stdio --enable-web-dashboard false --open-web-dashboard false`. |
| `SERENA_ARENA_MCP` | `UNAVAILABLE` | Host agent của Arena chạy ngoài E2B VM, không hỗ trợ đăng ký custom stdio/HTTP MCP server; `list_connector_tools(service="serena")` trả `{"status": "unsupported"}`. Không dùng Python MCP client độc lập để tuyên bố tích hợp Arena. |
| `PLAYWRIGHT_CLI` | `PASS` | Cài cô lập tại `/tmp/pw-cli` (`@playwright/cli@0.1.22` + `@sparticuz/chromium@153.0.0` từ `registry.npmjs.org`, giải nén `al2023.tar.br` NSS `.so` libs vào `/tmp/al2023/lib`, `ldd /tmp/chromium` 0 thiếu thư viện). |
| `ARENA_BROWSER` | `VERIFIED` | Điều khiển thật `Chromium 153.0.8010.0` qua `playwright-cli` mở Streamlit `1.66.1` chạy cục bộ trên dữ liệu giả cô lập `mongomock-4.3.0`, mở Journey Map, chọn node, mở hội thoại trong node, gửi bình luận thử, kiểm tra hình học & `elementFromPoint` trên Desktop `1440x900` và Mobile `390x844`. |
| `PERSISTENCE` | `SESSION_ONLY` | Mọi package trong `/tmp` (và cả `.venv`/`node_modules` bị loại khỏi workspace snapshot) chỉ tồn tại trong phiên VM hiện hành; mở phiên Arena mới (`NEW_CHAT`) cần cài lại. |
| `FINAL` | `INCOMPLETE` | Browser/Playwright CLI đạt `VERIFIED`, nhưng Serena MCP không thể kết nối vào native tool surface của agent Arena (`SERENA_ARENA_MCP=UNAVAILABLE`). |

## 1. Bằng chứng Serena MCP trong Arena

1. **Cài đặt cô lập ngoài dependency ứng dụng:**
   - `/tmp/serena-venv`: `serena-agent==2.1.0` (`Serena 2.1.0`).
   - Phát hiện khác biệt thực tế giữa GitHub Actions và Arena E2B: `solidlsp` mặc định chạy `uvx -p 3.13 --from pyright==1.1.403 pyright-langserver`, khiến `uv` tải CPython 3.13 từ `github.com/astral-sh/python-build-standalone/releases/download/...` (redirect sang `objects.githubusercontent.com` bị chặn bởi E2B firewall). Khắc phục gọn bằng `npm install --prefix /tmp/serena-pyright pyright@1.1.403` (từ `registry.npmjs.org`) và cấu hình `ls_specific_settings.python.ls_path: /tmp/serena-pyright/node_modules/.bin/pyright-langserver` trong `/home/user/.serena/serena_config.yml`.
2. **Kiểm tra tích hợp MCP của Arena:**
   - Gọi trực tiếp tool Arena `list_connector_tools(service="serena")` -> `{"status": "unsupported"}`.
   - Agent loop của Arena không đọc `.claude/.mcp.json` / `.mcp.json` và không cho đăng ký stdio MCP server tùy chỉnh, nên Arena **không** tự phát hiện hay gọi trực tiếp `get_symbols_overview`, `find_symbol`, `find_referencing_symbols` như native Arena tools (`SERENA_ARENA_MCP=UNAVAILABLE`).
3. **Vị trí mã nguồn tham chiếu trên HEAD `aa5df4bc13fb92f36f39f6ec40d8df5f479f08a1` (đối chiếu trực tiếp, không mạo nhận native MCP call của Arena):**
   - Định nghĩa: `core/journey_notes.py`, hàm `read_note_attachment` (dòng `526–609`).
   - Nơi gọi: `views/journey_inline.py`, hàm `_handle_download` (dòng `538–591`, lệnh gọi `notes.read_note_attachment(...)` tại dòng `561`).

## 2. Bằng chứng Playwright CLI & trình duyệt thực tế trên ứng dụng Logistics

### Công thức cài đặt cô lập trong phiên Arena (`/tmp/pw-cli`)

Do `cdn.playwright.dev`, `storage.googleapis.com` và `deb.debian.org` đều bị chặn trong E2B sandbox, `playwright-cli install-browser chromium` trả `ECONNRESET`. Thay vào đó, dùng trực tiếp gói npm `@sparticuz/chromium@153.0.0` (chứa sẵn `Chromium 153.0.8010.0` + thư viện NSS `al2023.tar.br`):

```bash
mkdir -p /tmp/pw-cli && cd /tmp/pw-cli
npm install --prefix /tmp/pw-cli --no-audit --no-fund "@playwright/cli@0.1.22" "@sparticuz/chromium@153.0.0"
AWS_EXECUTION_ENV=AWS_Lambda_nodejs20.x node --input-type=module -e 'import c from "@sparticuz/chromium"; console.log(await c.executablePath());'
LD_LIBRARY_PATH=/tmp/al2023/lib:/tmp /tmp/chromium --version
# -> Chromium 153.0.8010.0 (ldd: 0 missing shared libraries)
```

### Luồng nghiệm thu thực tế đã chạy bằng `playwright-cli`

1. **Shell nội bộ Trường Thành (`app.py` trên `http://127.0.0.1:9501/?portal=internal`, `AUTH_REQUIRED=false`, `ENV_IDENTITY=PREVIEW`, `MONGO_URI` rỗng -> `mongomock`):**
   - `playwright-cli open` -> click `Mở LO-0306` -> click `🗺 Bản đồ chi tiết` (`journey-detail-map-toggle`) -> click node `1 Chặng chính` (`journey-node-MAIN_CARRIAGE`) -> click `💬 Trao đổi / Chứng từ công đoạn Chặng chính` (`journey-node-discussion-MAIN_CARRIAGE`).
   - Mở `dialog "Trao đổi công đoạn Vận chuyển"` ngay trong Journey Map -> `fill` bình luận thử -> `click` nút `Gửi` -> bình luận hiển thị ngay trong thread (`1 trao đổi`) kèm nút `Trả lời` -> thử `click` `Trả lời` (`Đang trả lời local-admin`) và `Đóng trao đổi` trên Mobile `390x844`.
   - Kiểm tra hình học & che khuất (`geometry-checks.json`):
     - Desktop `1440x900`: `horizontalOverflow=false` (`scrollWidth=1440`), `dialogRect=540x540`, `6/6` điều khiển (`Đóng trao đổi`, `Trả lời`, `Viết bình luận…`, `Đính kèm`, `Ai xem?`, `Gửi`) đều `inViewportX=true`, `inDialog=true`, `hitOk=true` (`elementFromPoint` trúng đích, các nút cao `44px`).
     - Mobile `390x844`: `outerHorizontalOverflow=false` (`scrollWidth=390`), `dialogRect=316x602` (`bottom=723`, nằm trên thanh điều hướng dưới), `6/6` điều khiển đều `inViewportX=true`, `inViewportY=true`, `inDialog=true`, `hitOk=true`.

2. **Cổng khách hàng Lục Giác (`tests/component/g15_isolated_runtime.py` trên `http://127.0.0.1:9502/`, `mongomock` cô lập):**
   - Duyệt công bố mốc `pickup` cho `QA-LOT` -> chuyển sang `Lục Giác` -> mở hải đồ Journey Map -> click node `01 LẤY HÀNG` (`journey-node-pickup`) -> kiểm tra vùng hội thoại trong bubble của node trên cả Desktop `1440x900` và Mobile `390x844` (`horizontalOverflow=false`, `hitOk=true` cho mọi nút `Xem chi tiết chỉ-đọc →`, `Viết bình luận…`, `📎 Đính kèm`, `Gửi`).

## Tệp đính kèm trong thư mục này

- `staff-desktop-1440x900-node-discussion.png` — Ảnh chụp thật Chromium 153 màn Journey Map nội bộ (Trường Thành) ở `1440x900` khi mở hội thoại node `Chặng chính` và đã gửi 1 trao đổi thử.
- `staff-mobile-390x844-node-discussion.png` — Ảnh chụp thật Chromium 153 màn Journey Map nội bộ ở `390x844` (không tràn ngang, không bị thanh điều hướng dưới che nút `Gửi`/`Đính kèm`).
- `customer-desktop-1440x900-node-discussion.png` — Ảnh chụp thật Chromium 153 cổng khách hàng Lục Giác ở `1440x900` khi mở bubble hội thoại node `01 LẤY HÀNG`.
- `customer-mobile-390x844-node-discussion.png` — Ảnh chụp thật Chromium 153 cổng khách hàng Lục Giác ở `390x844` khi mở bubble hội thoại node `01 LẤY HÀNG`.
- `geometry-checks.json` — Dữ liệu `getBoundingClientRect()`, `scrollWidth` và `elementFromPoint()` (`hitOk`) thực đo từ Chromium cho cả 4 khung nhìn.
