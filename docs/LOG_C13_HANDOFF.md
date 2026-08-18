# LOG-C13 Handoff: Contract & Commercial Handoff

**Trạng thái:** Hoàn tất và đã push lên GitHub.
**Baseline:** commit `82c8134` ("Initial sanitized Logistics Work Desk checkpoint through LOG-C12").
**Branch:** `log-c13-contract-commercial-handoff` — commit `046fec3`, **không merge** vào `main`.
**Repo GitHub:** [7roger89-web/logistics-work-desk](https://github.com/7roger89-web/logistics-work-desk)
**Kết quả tests:** 194 passed / 7 skipped trên máy của bạn (baseline 150 passed; 23 tests mới cho LOG-C13).

## Pull request

Bạn có thể tạo PR từ nhánh này bất kỳ lúc nào tại:
https://github.com/7roger89-web/logistics-work-desk/pull/new/log-c13-contract-commercial-handoff

## 1. Những gì đã được xây dựng

### Miền nghiệp vụ thỏa thuận (mới) — `core/commercial_agreements.py`

Module thuần (không import DB), tuân house pattern của repo:

| Khía cạnh | Thiết kế |
|---|---|
| Chu kỳ trạng thái | `DRAFT → REVIEWING → AGREED → REVISED → REVIEWING`; `VOID` từ nhiều trạng thái. `AGREED` **không bao giờ bị ghi đè** — sửa điều khoản tạo bản revision draft mới giữ nguyên bản cũ (version tăng, status_history đầy đủ). |
| Snapshot thương mại | Copy từ báo giá đã chốt: tuyến đường, incoterm, phương thức vận tải, mô tả hàng hóa, service lines (giá bán/giá vốn từng service, thuế), tóm tắt tính toán (đánh dấu `not_finance_ledger=True`), điều khoản ủy thác nhập khẩu, điều khoản thanh toán. Chỉ snapshot, không ghi nhận chính sách. |
| Điều khoản thanh toán | Chỉ là commercial terms (cọc/không cọc, trước thông quan, trước giao hàng, sau giao hàng, credit term, due-date trigger + ghi chú). **Không chạm** collections thanh toán/sổ quỹ. |
| Trách nhiệm & chứng từ | `responsibilities` (Trường Thành thực hiện / khách cung cấp), `required_documents` với `evidence_state` AVAILABLE/MISSING/WAITING/UNKNOWN (không suy "đã ký" từ tên file). |
| Sẵn sàng bàn giao | Hàm đánh giá tất định, chỉ dựa trên material: thiếu quote reference/customer/service lines/lots → `MISSING_REQUIRED_DATA`; chưa AGREED hoặc thiếu evidence/chứng từ hoặc còn unresolved issues → `NEEDS_COMMERCIAL_REVIEW` kèm lý do cụ thể; ngược lại `READY_FOR_OPERATIONS`. |
| Write requests | Mọi thao tác đều qua `prepare_agreement_for_persistence` (validate + stamp write_request_id + provenance). **Zero canonical finance writes** — collection mới `agreements`, không đụng financial_transactions/obligations/allocations/payment_receipts. |

### Trang UI mới — `views/agreements.py`: "Thỏa Thuận & Bàn Giao"

Ba tab: **(1) Thỏa thuận đang theo dõi** (bảng lọc theo trạng thái), **(2) Tạo từ báo giá chốt** (chỉ cho phép chọn quote ACCEPTED/READY_TO_CREATE_SHIPMENT, khởi tạo draft với snapshot + form bổ sung điều khoản thanh toán, trách nhiệm, chứng từ, evidence, điều khoản ủy thác), **(3) Chi tiết & Bàn giao** (badge trạng thái, snapshot readonly, bảng câu hỏi handoff 16 mục tiếng Việt, banner sẵn sàng màu xanh/cam/đỏ, các nút chuyển trạng thái, link với lô hàng).

### Tích hợp read-only vào các workspace hiện có

| Workspace | Thay đổi |
|---|---|
| Shipment 360 | Section "Bối cảnh thương mại": quote reference, thỏa thuận (ref + trạng thái + incoterm + dịch vụ đã bán), banner trạng thái bàn giao, link sâu mở trang Thỏa thuận. |
| Customer 360 | Hai expander mới: "Báo giá đã chốt" và "Thỏa thuận thương mại" của từng khách hàng. |
| Review Queue | Category `COMMERCIAL` mới: báo giá đã chốt chưa có thỏa thuận, bàn giao chưa sẵn sàng, thỏa thuận AGREED nhưng thiếu evidence. Read-only, provenance nguồn, button mở trực tiếp trang Thỏa thuận của lô hàng đó. |
| Navigation | Route mới thuộc nhóm COMMERCIAL CONTEXT (quyền sales), sau mục "Sales & Báo Giá". |

### Persistence & state

`core/database.py`: `load_agreements` / `save_agreements_to_cloud` (dùng upsert idempotent `_save_document` theo `agreement_id`), index `agreements`. `core/state.py`: nạp `db_agreements` trong `refresh_core_data` như mọi store khác.

## 2. Bảo đảm chất lượng

Bộ tests mới `tests/test_commercial_agreements.py` (23 tests) phủ: ma trận transition hợp lệ, cơ chế revision (AGREED → REVISED → draft mới giữ nguyên bản cũ), bất biến snapshot, điều khoản thanh toán không sinh finance write, điều khoản ủy thác không invent chính sách, tính tất định của readiness (material only, không đòi optional fields), upsert idempotent, review-queue signals. Write oracle tài chính (test sẵn có của repo) vẫn xanh: **0 canonical finance writes** sau mọi thao tác thương mại. Ngoài ra kiểm tra UI trực tiếp bằng browser trên app chạy thật — cả ba tab và banner trạng thái hiển thị đúng.

## 3. Quy trình Git đã thực hiện

Thực hiện trên máy của bạn (D:\Logistics_App_GitHub): tạo nhánh từ baseline 82c8134 → chạy `python -m py_compile` + pytest toàn suite trên Python Windows của máy (194 passed) → commit `046fec3` (13 files, +1834/-9) → push branch. `main` không bị đụng. Sau khi push, remote `origin` được trả về URL gốc (không chứa token trong config).

## 4. Vấn đề kỹ thuật phát sinh và cách xử lý

Trong quá trình đồng bộ file từ môi trường sandbox sang máy của bạn, mount FUSE bị lỗi cache khiến một số file `core/*.py` trên máy không được ghi đè. Đã khắc phục bằng cơ chế encode base64 → script Python giải mã chạy trực tiếp trên máy Windows, sau đó xác minh nội dung từng file (size + nội dung) bằng script chạy trên máy (ground truth). Kết quả cuối: mọi file đúng nội dung, suite test pass đầy đủ trên Python Windows của bạn.

## 5. Việc mở tiếp theo (cho LOG-C14)

Trang Thỏa thuận hiện là nơi Sale quản lý điều khoản trước khi bàn giao; LOG-C14 có thể mở rộng về phía vận hành: chuyển trạng thái bàn giao thành lệnh công việc vận hành, ràng buộc chứng từ với lô hàng thực tế, và số hóa quy trình thu/cục bộ hóa evidence vào audit trail (vẫn không chạm ledger tài chính).
