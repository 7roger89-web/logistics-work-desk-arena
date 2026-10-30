# Kiểm thử browser có tái lập được bằng bộ Playwright hiện có? — đo thật, 2026-10-30

- **Repository:** `7roger89-web/logistics-work-desk-arena`
- **Nhánh phiên:** `arena/f26588fe-logistics-work-desk-arena` (base `main@9e4190b`, không đổi `main`)
- **Môi trường:** E2B (Debian 12), Python `3.11.2`, Node `22.22.3`, Streamlit `1.66.1`, mongomock `4.3.0`
- **Trình duyệt:** Chromium thật `153.0.8010.0` (bundle `@sparticuz/chromium@153.0.0`) chạy bằng `@playwright/cli@0.1.22`
- **Mục tiêu:** chứng minh (hoặc bác bỏ) rằng bộ script browser sẵn có đủ để nghiệm thu lặp lại lỗi/hotfix của PR #243 — trước khi quyết định có cần thêm `@playwright/test`.

## 1. SHA đo lại (không suy diễn)

| Vai trò | SHA | Ghi chú |
|---|---|---|
| `main` | `9e4190b278dd2ced8771c5249582753d34e561db` | không dùng để tái hiện: thiếu `views/customer_dashboard.py` |
| PRE (baseline lỗi lịch sử) | `4dd3cb9aceaedf66a2128b8612a38012f3e13e50` | cha của PR #243 |
| FIX (PR #243 head) | `6b95af35e94ef331bdf29403d1285bd77fc8c461` | PR `MERGED` |
| Staging hiện tại | `2fcb74ea7fc37890589601c43d5c74a3271ab10e` | `git diff` với `6b95af3` trên `views/customer_dashboard.py` **rỗng** ⇒ đã có bản sửa |

## 2. Làn chạy hiện có (không cài framework mới)

`@playwright/cli` + `@sparticuz/chromium` (đúng công thức đã dùng ở `evidence/arena-tooling-20261030/`), Chromium thật, `PLAYWRIGHT_MCP_EXECUTABLE_PATH=/tmp/chromium`.
`cdn.playwright.dev` / `playwright.download.prss.microsoft.com` trả `000` (bị chặn) ⇒ **không** dùng được `playwright install chromium`; bundle npm là đường duy nhất chạy được trong sandbox này. Không cài gì vào repo, không thêm dependency runtime.

## 3. Ma trận 4 ca chạy thật

| Ca | App | Harness | Script | Exit | Kết quả | Thời gian chạy |
|---|---|---|---|---|---|---|
| `pre_ha_s1` | PRE `4dd3cb9` | `harness/h_split_customer.py` | `evidence/logi-journey-send-20261030/flows/a-customer-send-reload.js` (**nguyên bản, sha256 `1149696…`**) | **1** | **FAIL** — `TimeoutError` chờ marker; server log `JOURNEY_NOTE_DB_UNAVAILABLE reason=None` | 26.9 s (25 s là timeout) |
| `fix_ha_s1` | FIX `6b95af3` | y hệt | y hệt | 0 | **PASS** — gửi OK, `0 → 1`, reload vẫn thấy marker `QA-SEND-…` | 3.8 s |
| `fix_hb_s2` | FIX `6b95af3` | `tests/component/g15_lg_tt_discussion_runtime.py` (harness của PR) | `flows/s2-shared-journey.js` | 0 | **PASS** — khách gửi `(0 → 1)` → reload → Trường Thành đăng nhập thật, đọc, trả lời `👁 Khách xem` `(1 → 2)` → khách đọc lại → **Khách khác: 0 lô, 0 node, 0 khung trao đổi** | 172.5 s |
| `pre_hb_s2` | PRE `4dd3cb9` | y hệt (chép harness sang worktree PRE) | y hệt | 0 | **PASS cả trên bản lỗi** ⇒ harness này **không phát hiện** được defect | 172.7 s |
| `pre_ha_s1b` | PRE `4dd3cb9` | lặp lại `pre_ha_s1` | y hệt | **1** | **FAIL** y hệt (`JOURNEY_NOTE_DB_UNAVAILABLE reason=None`) | 27.0 s |
| `fix_ha_s1b` | FIX `6b95af3` | lặp lại `fix_ha_s1` | y hệt | 0 | **PASS** (`0 → 1`, reload còn marker) | 4.0 s |

Bản sao nguyên trạng script của repo dùng ở ca PRE/FIX: `flows/repo-a-customer-send-reload.js`
(sha256 `114969629d54d83df8c65d527443ecc39d1232ab74c08f694c211c2f3b22a8bc` = blob tại `6b95af3`, không sửa một byte).

Dữ liệu máy đọc: `results.json` (JSON tổng hợp + `db/*.result.json` từng ca), trace: `traces/*.trace.gz` + `*.network.gz` (mở bằng `npx playwright show-trace`), ảnh: `screenshots/*.png`, log server: `logs/*.app.log`.

## 4. Phát hiện quan trọng (định hình quyết định)

1. **Làn `playwright-cli` đủ để nghiệm thu lặp lại một kịch bản**: một lệnh `run-code --filename`, trả JSON, **exit code 1 khi kịch bản lỗi** (đo được ở `pre_ha_s1`), có `tracing-start/stop`, screenshot, console log, network log. Không cần `@playwright/test` để có "chạy được / không chạy được".
2. **Nhưng bộ script hiện có chưa đủ để chứng minh PRE↔FIX**: `flows/a-customer-send-reload.js` hard-code cổng `9502`; harness `g15_isolated_runtime.py` ở `4dd3cb9` **không công bố được lô** (`CUSTOMER_PORTAL_PUBLICATION_DENIED reason=missing_pinned_version`) nên trên baseline không mở được node để bấm `Gửi`.
3. **Harness của PR không phải phép thử phân biệt được**: `g15_lg_tt_discussion_runtime.py` cho cả hai cổng dùng **chung một handle** (`get_db()` = db fixture) nên lỗi "hai handle" bị che; chạy đúng script đó trên `4dd3cb9` vẫn `ok:true`. Muốn FAIL ở bản lỗi phải dùng runtime **inject handle khác `get_db()`** — đúng điều kiện lỗi thật (`harness/h_split_customer.py`, chép nguyên trạng cho cả hai phía, chỉ app code khác nhau).
4. Thiếu so với test runner: không có retry, không nhóm/parallel test, không `expect`/assertion report, không JUnit/HTML summary, không trace tự động theo từng test, không `--repeat-each`/`--grep`, và mỗi kịch bản vẫn là một hàm `page =>` tự viết — người viết phải tự chế `ok` boolean.

## 5. Chi phí đo được

- Cài đặt (pip requirements + pytest): **33.3 s**; npm CLI + Chromium bundle: **5.1 s**; worktree PRE/FIX: **0.66 s** ⇒ **~39 s từ sandbox trống đến browser chạy được**.
- Viết harness split-handle (~130 dòng) + script S2 (~110 dòng) + runner 1 ca: phần lớn thời gian của phiên (~13 phút), không phải phần cài đặt.
- Chạy lại: ca ngắn **3.8 s**, ca FAIL **26.9 s**, ca full journey **172 s**. Không tạo file báo cáo nào ngoài bundle này.

## 6. Thử `@playwright/test` trong môi trường cô lập (điều kiện nghiệm thu #5)

Chỉ thử khi làn cũ **thiếu năng lực**, không đưa vào repo: cài `/tmp/pwtest` (`@playwright/test@1.64.1`, **1.48 s**), config dùng `launchOptions.executablePath=/tmp/chromium`, một spec `specs/customer-send-reload.spec.js` (~1.5 KB) làm đúng ca gửi + reload.

| Ca | Exit | Thời gian | Kết quả |
|---|---|---|---|
| FIX `6b95af3` | 0 | 47.2 s | `1 passed` |
| PRE `4dd3cb9` | **1** | 53.7 s | `1 failed` — `expect(...toBeVisible) element(s) not found`; trace.zip + ảnh lỗi tự động |

Được thêm so với làn cũ: thư viện `expect`, reporter JSON/JUnit/HTML, retries/workers/`--grep`, trace + screenshot tự động theo test.
Phải trả: thêm toolchain Node dev (`package.json` + `node_modules`) vào một repo **hiện không có** `package.json`; vẫn phải tự viết spec và vẫn phải có harness y như làn cũ; **không** nhanh hơn (47 s so với 3.8 s của `playwright-cli` — chênh lệch là do spec có ~10 s sleep thủ công, không phải do runner).

## 7. Kết luận đo được

`KEEP_EXISTING` — làn `playwright-cli` + Chromium bundle đã cho **cùng một phép thử FAIL trên bản lỗi và PASS trên bản sửa, lặp lại được, có exit code, JSON, trace, log**. Cái thiếu không phải framework mà là **hai test asset**: (1) harness inject-handle tách khỏi `get_db()` để chạm đúng seam DB, (2) một script full journey có `ok` boolean. Hai file đó nằm ngay trong bundle này và có thể chuyển vào `tests/component/` khi cần.

## 8. Giới hạn trung thực

- Danh tính khách là fixture QA, **không** chứng minh OIDC Google thật; nhân viên đăng nhập bằng mật khẩu thật vào `users` store của fixture.
- DB là `mongomock` trong tiến trình; "reload" chứng minh ở tầng server (đọc lại từ DB), không chứng minh độ bền MongoDB thật.
- `pre_hb_s2` dùng harness của PR chép sang worktree PRE (chỉ là test asset, không sửa app) — vì `4dd3cb9` chưa có file đó.
- Payload crafted sang tenant khác (`INVALID_SCOPE`) được chứng minh ở tầng pytest (`pre`: 4 failed / `fix`: 67 passed), không phải ở tầng browser; tầng browser chỉ chứng minh "khách khác không thấy lô/node/khung trao đổi".
- Trace chỉ giữ cho 3 ca quyết định (`pre_ha_s1`, `fix_ha_s1`, `fix_hb_s2`), nén `.gz`; `resources/`/`screencast/` dùng chung giữa các ca nên không đưa vào repo ⇒ replay không có video/frame. Ca lặp lại và ca `pre_hb_s2` chỉ giữ JSON + log + ảnh.
