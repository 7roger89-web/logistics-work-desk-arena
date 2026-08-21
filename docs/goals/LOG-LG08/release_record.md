# LOG-LG08 — Bản Ghi Phát Hành (Release Record)

Ngày phát hành: 2026-08-21 (UTC+7)

## 1. Trạng thái Git (SHA đầy đủ)

| Hạng mục | Giá trị |
|---|---|
| CURRENT_MAIN_SHA (full) | `05f4b76`+ (HEAD tại thời điểm phát hành là `05f4b76b197881886790e241a795c20cf639906a`; chứa thêm bản ghi phát hành này) |
| CURRENT_MAIN_SHA (short) | `05f4b76` |
| CURRENT_PRODUCTION_SHA (full) | `b6fde2b46e36f65947867f3b8aeee5c2c98f8f04` |
| CURRENT_PRODUCTION_SHA (short) | `b6fde2b` |
| CLOUD_DEPLOYMENT_BRANCH | `production` |
| CLOUD_LIVE_SHA | `b6fde2b` |
| PREVIOUS_PRODUCTION_SHA | `5aba4c2` (LG07 — trên app cũ) |
| OWNER_APPROVED_LIVE_SHA | `b6fde2b` |

## 2. App Cloud (Streamlit)

| App | URL | Nhánh | SHA | Trạng thái |
|---|---|---|---|---|
| Mới (chính thức) | https://logisticspro-1.streamlit.app/ | `production` | `b6fde2b` | LIVE — đã xác minh đăng nhập + dữ liệu |
| Cũ (giữ lại) | https://tienthanhlog.streamlit.app/ | `main` | `e859d73` | Hoạt động, nhưng không còn là nguồn chính |

Cách ly phát hành đã được chứng minh: khi đẩy commit thử `36c01cb` lên nhánh `test/release-isolation`, nhánh `production` vẫn nguyên ở `b6fde2b`. Các commit tương lai lên `main` hoặc nhánh tính năng sẽ không tự động chạm vào bản production; chỉ khi Owner chủ động merge vào nhánh `production` thì app mới cập nhật. Nhánh thử nghiệm đã được xóa sau kiểm tra.

## 3. Kiểm chứng chất lượng (tại SHA phát hành)

| Hạng mục | Kết quả |
|---|---|
| Full regression (278 tests) | 278 passed / 28 skipped / 0 failed |
| RBAC | 28 passed |
| Mojibake tiếng Việt | 0 |
| Secrets lộ trong file committed | 0 (quét sạch) |
| Browser QA app mới | PASS (đăng nhập, dashboard, 13 lô cần xử lý, lịch sử) |

## 4. Dữ liệu Production (đọc ngược)

| Hạng mục | Giá trị |
|---|---|
| Customers | 362 |
| Shipments | 91 |
| Duplicate shipment IDs | 0 |
| Users active | admin (admin), 7roger (admin), sami (sale), fiona (support) |
| Users inactive | rehearsal_admin, rehearsal_sale, rehearsal_support |
| Vai trò lệch chuẩn | 0 — khớp chính sách Owner phê duyệt |

## 5. Vệ sinh mật khẩu (Credential Hygiene)

Mật khẩu plaintext từng bị commit trong `docs/goals/LOG-LG08/final_report.md` (và nhiều tài liệu LG03–LG07) đã bị xóa toàn bộ khỏi repo (commit `e859d73`). Kết quả xử lý theo tài khoản:

| Tài khoản | Hành động | Lý do |
|---|---|---|
| admin | Giữ nguyên (Owner-kept) | Do chính Owner sử dụng |
| 7roger | Giữ nguyên (Owner-kept) | Do chính Owner sử dụng |
| sami | Đã đổi mật khẩu mới (2026-08-21) | Từng bị ghi plaintext trong tài liệu |
| fiona | Đã đổi mật khẩu mới (2026-08-21) | Từng bị ghi plaintext trong tài liệu |

Đọc ngược xác minh: mật khẩu cũ của sami/fiona bị từ chối, mật khẩu mới chấp nhận, admin/7roger vẫn đăng nhập bình thường. Owner cần nhắn riêng cho sami và fiona mật khẩu mới (đã cung cấp qua kênh nhắn tin riêng, không ghi vào repo).

## 6. Kết luận

**LOG_LG08_RELEASE_SAFETY_CLOSED**
**PRODUCTION_BRANCH_IS_LIVE_SOURCE**

Bản production hiện do nhánh `production` quyết định duy nhất. LG09 không được bắt đầu tự động.
