
# BÁO CÁO ĐỐI SOÁT SỰ THẬT (TRUTH RECONCILIATION) — LOG-LG08.1

Báo cáo này trình bày kết quả xác minh độc lập cuối cùng (Read-only) về hiện trạng hệ thống Production sau khi hoàn tất LG08.1. Mọi mâu thuẫn trong các báo cáo trước đó đã được giải quyết bằng bằng chứng thực tế từ mã nguồn và cơ sở dữ liệu.

## 1. OFFICIAL APP TRUTH (Ứng dụng chính thức)

Hiện tại, hệ thống đang vận hành với cấu hình như sau:

| Mục | Giá trị thực tế | Ghi chú |
|---|---|---|
| **OFFICIAL_PRODUCTION_URL** | https://tienthanhlog.streamlit.app/ | App chính thức Owner đang dùng |
| **STREAMLIT_DEPLOYMENT_BRANCH** | `production` | Đã chuyển nhánh an toàn ✅ |
| **STREAMLIT_LIVE_SHA** | `1bc48b6` | SHA khớp với mã nguồn an toàn ✅ |

> **Giải thích mâu thuẫn:** App `logisticspro-1.streamlit.app` trước đó được tạo để kiểm tra tính năng release safety. Sau khi xác minh thành công, Owner đã chọn quay lại sử dụng URL quen thuộc `tienthanhlog.streamlit.app` nhưng đã chuyển nhánh cấu hình từ `main` sang `production` để đảm bảo cách ly an toàn.

## 2. SHA TRUTH (Mã nguồn & Lịch sử)

Xác minh tính nhất quán của mã nguồn trên các môi trường:

| Vị trí | SHA | Trạng thái |
|---|---|---|
| **LOCAL_MAIN_HEAD** | `1bc48b6` | Khớp ✅ |
| **ORIGIN_MAIN_HEAD** | `1bc48b6` | Khớp ✅ |
| **LOCAL_PRODUCTION_HEAD** | `1bc48b6` | Khớp ✅ |
| **ORIGIN_PRODUCTION_HEAD** | `1bc48b6` | Khớp ✅ |
| **STREAMLIT_LIVE_SHA** | `1bc48b6` | Khớp ✅ |

**Ancestry (Phả hệ Git):** Commit `1bc48b6` là hậu duệ trực tiếp của `f2885ff` (chứa các bản vá bảo mật và hồ sơ xác minh cuối cùng). Hiện tại `main` và `production` đang hội tụ tại cùng một điểm an toàn nhất.

## 3. CHỨNG MINH AN TOÀN DỮ LIỆU (Technical Proof)

### Getfly Zero-Write Proof
Mã nguồn tại `views/dashboard.py` (dòng 520-600) và `core/excel_roundtrip.py` thực thi cơ chế **Zero-Write** nghiêm ngặt:
- **NEW:** Chỉ cho phép ghi mới lô hàng chưa tồn tại.
- **UNCHANGED / CONFLICT / AMBIGUOUS:** Hoàn toàn **KHÔNG** gọi lệnh ghi vào DB, giữ nguyên trạng thái để Owner phê duyệt thủ công.
- **Finance Protection:** Lịch sử thanh toán (`data.3.4.payments`) được bảo vệ bởi hàm `_payment_history_is_unchanged`, chặn mọi hành vi ghi đè trái phép từ Getfly import.

### GNT Contract Proof
Luồng dữ liệu Giấy nộp thuế (GNT) đảm bảo tính toàn vẹn:
- **Fail-Closed:** UI chặn xuất file nếu thiếu MST, Tên người nộp hoặc Số tờ khai.
- **Date Handling:** Nếu thiếu ngày tờ khai, hệ thống sử dụng ngày hiện tại làm mặc định để đảm bảo cấu trúc file Excel, trong khi các trường tài chính/ngân hàng nhạy cảm được giữ trống để điền thủ công (Do Not Guess).

### Atomic Shipment Proof
Hàm `save_shipment_atomic` (dòng 450-504) thực thi tính nguyên tử qua **MongoDB Transaction**:
- Ghi lô hàng, ghi Audit log và ghi Outbox thông báo được thực hiện trong cùng một phiên (session).
- Nếu bất kỳ bước nào thất bại, toàn bộ thay đổi sẽ bị hủy bỏ (Rollback).
- Cơ chế `expected_version` chặn đứng các xung đột cập nhật đồng thời (Concurrent updates).

## 4. VỆ SINH BÍ MẬT (Credential Hygiene)

| Mục | Trạng thái |
|---|---|
| **CURRENT_TREE_SECRET_STATUS** | **CLEAN** (Không có mật khẩu lộ trong mã nguồn hiện tại) |
| **GIT_HISTORY_SECRET_STATUS** | **TRACE_EXISTS** (Lịch sử Git cũ vẫn còn vết tích mật khẩu lộ) |
| **CREDENTIAL_ROTATION** | **DONE** (Tất cả mật khẩu admin, 7roger, sami, fiona đã được đổi mới) |
| **LIVE_EXPOSED_CREDENTIAL** | **NONE** (Không có mật khẩu đang hoạt động nào bị lộ) |

> **Khuyến nghị:** Mặc dù mã nguồn hiện tại đã sạch, lịch sử Git vẫn chứa vết tích cũ. Tuy nhiên, vì toàn bộ mật khẩu thật đã được xoay (rotated), các vết tích này không còn giá trị truy cập trái phép.

## 5. DỮ LIỆU THỰC TẾ (Read-only Check)

- **Database:** `logistics_db` (Atlas Cluster0)
- **Customers:** 362
- **Shipments:** 91 (Total) / 66 (Active)
- **Roles:** Khớp 100% chính sách (admin=admin, 7roger=sale, sami=support, fiona=support).

---
**KẾT LUẬN CUỐI CÙNG:**

**LOG_LG08_1_FULLY_VERIFIED**
**PRODUCTION_SAFE_FOR_NORMAL_DAILY_USE**

Hệ thống đã đạt trạng thái an toàn nhất theo yêu cầu. Tôi dừng công việc tại đây và **không bắt đầu LG09**.
