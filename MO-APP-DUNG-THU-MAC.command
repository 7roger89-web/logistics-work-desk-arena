#!/bin/bash
# ==========================================================================
# LOGI #199 — Trình mở bản DÙNG THỬ trên máy Mac.
#
# Cách dùng: nhấp đúp vào tệp này. Không cần gõ lệnh.
#
# An toàn:
#   * Chỉ chạy với DỮ LIỆU MẪU trong bộ nhớ tạm (Mongomock) — launcher
#     scripts/logi199_t6_staging_app.py tự chặn nếu thấy cấu hình thật.
#   * Không đọc/không ghi cơ sở dữ liệu thật; không cần tài khoản thật.
#   * Chỉ mở trên máy này (127.0.0.1), không mở ra Internet.
#   * Tắt bằng cách đóng cửa sổ này hoặc bấm Control + C.
#
# Không thay đổi ứng dụng production: app.py, web_app.py, auth, dữ liệu thật
# đều không bị sửa.
# ==========================================================================
set -u
cd "$(dirname "$0")" || exit 1

PORT=9501
fail() { printf '\n%s\n' "DỪNG: $1"; printf '%s\n' "Cửa sổ này giữ nguyên để người hỗ trợ đọc thông báo. Bấm Control + C để đóng."; read -r _; exit 1; }

printf '%s\n' "=== Logistics Work Desk — bản dùng thử (dữ liệu mẫu) ==="

# 1. Không bao giờ chạy trong thư mục có cấu hình thật.
if [ -f .streamlit/secrets.toml ]; then
  fail "Thư mục này có .streamlit/secrets.toml (cấu hình thật). Hãy giải nén gói dùng thử vào một thư mục MỚI rồi mở lại."
fi

# 2. Ép trống mọi thông tin kết nối thật + chế độ dùng thử một người dùng.
unset MONGO_URI MONGO_DB_NAME LOGISTICS_PRO_SECRETS_FILE 2>/dev/null || true
export MONGO_URI="" MONGO_DB_NAME="" LOGISTICS_PRO_SECRETS_FILE=""
export AUTH_REQUIRED="false"
export STREAMLIT_BROWSER_GATHER_USAGE_STATS="false"

# 3. Cần Python 3.11 trở lên.
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' "Máy chưa có Python 3. Đang mở trang tải Python để cài (miễn phí)..."
  open "https://www.python.org/downloads/macos/" 2>/dev/null || true
  fail "Hãy cài Python 3.11 trở lên, rồi nhấp đúp lại tệp này."
fi
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
  printf '%s\n' "Python trên máy cũ hơn 3.11. Đang mở trang tải Python mới..."
  open "https://www.python.org/downloads/macos/" 2>/dev/null || true
  fail "Hãy cài Python 3.11 trở lên, rồi nhấp đúp lại tệp này."
fi

# 4. Gói dùng thử phải có sẵn giao diện đã đóng gói.
[ -f component/dist/logi-shell.js ] || fail "Thiếu tệp giao diện component/dist/logi-shell.js. Hãy giải nén LẠI gói ZIP đầy đủ."

# 5. Môi trường riêng cho bản dùng thử (không đụng Python của máy).
if [ ! -x .venv/bin/python ]; then
  printf '%s\n' "Lần đầu chạy: đang tạo môi trường riêng (mất khoảng 1 phút)..."
  python3 -m venv .venv || fail "Không tạo được môi trường riêng (.venv)."
fi
if [ ! -f .venv/.ready ] || [ requirements.txt -nt .venv/.ready ]; then
  printf '%s\n' "Đang chuẩn bị thư viện cần thiết (lần đầu có thể mất vài phút)..."
  .venv/bin/python -m pip install --quiet --upgrade pip || true
  .venv/bin/python -m pip install --quiet -r requirements.txt pytest || fail "Chưa cài được thư viện. Cần Internet cho lần chạy đầu tiên."
  touch .venv/.ready
fi
printf '%s\n' "Thư viện đã sẵn sàng."

# 6. Chọn cổng trống, rồi mở ứng dụng.
PORT=$(.venv/bin/python - <<'PY'
import socket
for port in range(9501, 9510):
    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", port)) != 0:
            print(port); break
else:
    print(9501)
PY
)
printf '\n%s\n' "Đang mở ứng dụng tại http://localhost:${PORT}"
printf '%s\n\n' "Dữ liệu là MẪU trong bộ nhớ tạm. Tắt: đóng cửa sổ này hoặc bấm Control + C."
( sleep 8; open "http://localhost:${PORT}" >/dev/null 2>&1 || true ) &

.venv/bin/python -m streamlit run scripts/logi199_t6_staging_app.py \
  --server.port "${PORT}" \
  --server.address 127.0.0.1 \
  --server.headless true \
  --browser.gatherUsageStats false

printf '\n%s\n' "Ứng dụng đã dừng. Các lô dữ liệu mẫu đã biến mất khỏi bộ nhớ."
read -r _ 2>/dev/null || true
