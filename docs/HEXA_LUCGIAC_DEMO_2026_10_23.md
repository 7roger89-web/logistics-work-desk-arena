# HEXA × Lục Giác — DEMO HTML gửi khách (2026-10-23)

Tệp bàn giao: `HEXA_LucGiac_DEMO.html` ở gốc repo — **một tệp duy nhất, mở trực tiếp bằng `file://`**, không cần Python / Streamlit / MongoDB / localhost / CDN.

- Kích thước: **816.578 bytes (~797 KB)**, `sha256 = 646f40ff451de105708c2327d6c82ea7badfbf3d7190930f0c2459eb9c69bd9e`
- Nguồn giao diện: `core/hexa_trial_portal.py` tại commit `4c4600aa52f7b24f8d1eabf9c7df4d248e9fcb52` (nhánh `arena/ecbac12e-logistics-work-desk-arena`) — **giữ nguyên CSS/JS gốc**, chỉ thêm lớp DEMO (badge, ghi chú minh họa) và các bản vá mobile ghi ở §4.
- Ảnh nhúng inline dạng data URI: nền hải đồ `vietnam.webp` (143.967 ký tự base64) + `chart-paper.jpg` (576.711 ký tự base64). Không có `<link>`, `<iframe>`, `<script src>` ngoài.

## 1. Phạm vi đã dựng

| Màn hình | Nội dung |
|---|---|
| Dashboard | 2 lô **ROAD-LG-001** (57.240.000 / 30.000.000 / 27.240.000 VND) và **ROAD-LG-002** (UNKNOWN / Chưa đối soát). Bảng desktop + thẻ mobile, KPI strip. |
| Journey Map | 7 node 00–06 (Kế hoạch → Lấy hàng → Nhận & ghép → Vận chuyển → Thông quan → Giao hàng → Thanh toán), đường nối SVG, trạng thái theo màu (✓ có bằng chứng / ◐ đang xử lý / ◷ chờ thông tin / · chưa bắt đầu). |
| Node | bấm node → **bubble** tóm tắt (bằng chứng, mốc xác minh, chứng từ) → **Xem chi tiết** → **popup chi tiết công đoạn** → **← Quay lại hải đồ** (mở lại đúng bubble của node đó) hoặc **× Đóng**. |
| Popup chi tiết | Bảng chỉ-đọc (trạng thái, thời điểm xác minh, ETA kho, đầu mối, báo giá bán đã duyệt, nội dung công bố), khối riêng cho công đoạn 00 (báo giá/hợp đồng/điều kiện thanh toán/ủy thác) và 06 (công nợ đã đối soát), danh sách chứng từ được phép tải, nhật ký mốc tiến độ, ô trao đổi (demo, không gửi). |
| Khác | Zoom +/−/Fit Journey/Đọc rõ, kéo pan desktop, bubble "Hồ sơ & Chứng từ", quay lại Dashboard, phím **Esc** đóng popup rồi đóng bubble. |

Chỉ có góc nhìn **khách hàng Lục Giác**: không có bàn TT, không giá vốn/lợi nhuận, không nhà cung cấp, không dữ liệu khách khác, không đăng nhập giả.

## 2. Nhãn DEMO bắt buộc

- Dải vàng trên cùng mọi màn hình: **“DEMO — DỮ LIỆU MINH HỌA”** (luôn hiển thị, nằm trong luồng trang nên không che nội dung ở mọi viewport).
- Banner cảnh báo ngay dưới header: toàn bộ số liệu/chứng từ/trao đổi là giả lập, không phải dữ liệu sản xuất, không có giá trị pháp lý.
- 6 ghi chú “Chỉ minh họa” đặt tại: bảng dashboard, bubble, ô trao đổi, danh sách chứng từ, nút gửi trao đổi, footer — mọi nút không có backend đều ghi **“Chỉ minh họa — không lưu dữ liệu thật”**.

## 3. Kiểm chứng trên trình duyệt thật (headless Chromium 153, `file://`)

Chạy bằng `puppeteer-core` + Chromium (không có mạng), viewport **1440×900** và **390×844** (mobile, deviceScaleFactor 2). Log đầy đủ: `docs/evidence/hexa-lucgiac-demo-2026-10-23/browser-test-log.txt`.

| Hạng mục | Desktop 1440×900 | Mobile 390×844 |
|---|---|---|
| Nhãn DEMO hiển thị | PASS | PASS |
| Dashboard đúng 2 lô + 3 dòng công nợ | PASS | PASS (2 thẻ) |
| Mở Journey Map từ hàng/thẻ lô | PASS | PASS |
| 7 node, không node nào tràn viewport | PASS (0) | PASS (0) |
| Node không cắt chữ (`scrollHeight ≤ clientHeight`) | PASS (0) | PASS (0) |
| Bubble trong viewport sau khi bấm node | PASS (290×213) | PASS (250×242) |
| Bubble vẫn nằm trong khung map sau khi zoom | PASS | PASS |
| Popup mở từ bubble (00 và 06) | PASS | PASS |
| “← Quay lại hải đồ” → về map **và mở lại bubble** | PASS | PASS |
| “× Đóng” / Esc / click nền đóng popup | PASS | PASS |
| Chứng từ + trao đổi + công nợ trong popup | PASS (4 chứng từ, 2 ghi chú) | PASS |
| Zoom +/−/Fit/Đọc rõ đổi tỉ lệ đúng | PASS (122→137→107→122→100%) | PASS (99→114→84→99→100%) |
| Thanh zoom không tràn/không chồng nhau | PASS | PASS (340px trong 390px) |
| Trang không cuộn ngang (`scrollWidth == innerWidth`) | PASS | PASS |
| Bubble “Hồ sơ & Chứng từ” trong viewport | PASS | PASS |
| Quay lại Dashboard | PASS | PASS |
| Request ra ngoài (http/https/CDN) | **0** | **0** |
| Lỗi JS (pageerror + console error) | **0** | **0** |

Tĩnh trên tệp: `fetch(` = 0, `XMLHttpRequest` = 0, `apiFetch` = 0, `https://` = 0, `http://` duy nhất là namespace SVG `http://www.w3.org/2000/svg`; không có `LG-Trial-2026`, `sess-`, `token`, `password`, `MONGODB_URI`; không có mã lô/khách khác ngoài Lục Giác.

## 4. Bản vá chỉ áp cho tệp DEMO (không sửa `core/hexa_trial_portal.py`)

1. **Nhãn DEMO thành dải trên cùng trong luồng trang** — bản `position: fixed` che chữ ở mobile và che pill header ở desktop.
2. **Mobile: 7 node xếp 3 cột × 3 hàng (snake)** thay vì 4 cột × 2 hàng; node 110×74px, chữ 11px để không cắt “NHẬN & GHÉP / THÔNG QUAN”; nền hải đồ `background-size: cover` để không còn dải trống trên/dưới; thanh zoom `white-space: nowrap` + nhãn Fit/Đọc rõ nới rộng (trước đây chữ tràn ra ngoài nút 36px).
3. **Bộ đếm chứng từ/trao đổi chuyển lên hàng đầu của node**, tránh footer node bị ép 2 dòng trên desktop.
4. **Ký tự thay thế cho font hệ thống**: `✕→×`, bỏ `⤢`, `⬇`, thay `📎/💬` bằng `▤ n · m BL` — các glyph emoji không có trong font Linux/Windows nên trước đó hiện thành ô trống.
5. **“← Quay lại hải đồ” mở lại đúng bubble của công đoạn** (node → bubble → popup → back là một vòng khép kín), thêm phím **Esc**.

## 5. Cách dùng & giới hạn

- Gửi **đúng 1 tệp** `HEXA_LucGiac_DEMO.html`; Owner/khách mở bằng Chrome/Safari/Edge (double-click). Không cần cài gì, không cần mạng.
- Nút “Tải PDF minh họa” chỉ tạo tệp PDF giả lập ngay trong trình duyệt (“Chỉ minh họa — không lưu dữ liệu thật”).
- Đây **không** phải bản deploy, không nối dữ liệu thật, không thay thế UAT trên hệ thống; mọi số liệu là mẫu để xin ý kiến giao diện.

## 6. Bằng chứng

`docs/evidence/hexa-lucgiac-demo-2026-10-23/` — 12 ảnh desktop + 12 ảnh mobile:

- `*-01-dashboard` (2 lô), `*-02-journey-map` (7 node), `*-03-bubble`, `*-04-modal-plan`, `*-05-modal-finance`, `*-06-back-dashboard`
- `*-07-shipment2-map` (ROAD-LG-002, công nợ UNKNOWN), `*-08-shipment2-bubble` (node 06 chờ thông tin)
- `*-09-documents`, `*-10-utility-docs`, `*-11-docs-chat-debt` (chứng từ + trao đổi + công nợ), `*-12-back-to-map` (quay lại hải đồ, bubble mở lại)
- `browser-test-log.txt` — log 3 lượt kiểm tự động (cơ bản / mở rộng / chứng từ–trao đổi–công nợ), cả 2 viewport.
