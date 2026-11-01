# TRẠNG THÁI
TASK_ID: LOGI-254-SHIPMENT-DEBT (Issue #254)
MỤC TIÊU: Xem nhanh công nợ dịch vụ (`Phải thu / Đã thu / Còn phải thu`) trên danh sách lô hàng `/lo-hang` (bảng desktop và thẻ mobile), tôn trọng `UNKNOWN != 0` và chặn rò rỉ dữ liệu tài chính ở tầng server theo quyền `finance_view`.
GIAI ĐOẠN: xong (chờ review/merge PR về staging)
ĐÃ THỬ: Ghi khóa spec `evidence/issue254/00-spec-lock.md`; fail-before `2 failed, 4 passed` tại `evidence/issue254/01-fail-before.txt`; chặn server-side `finance_view` trong `views/logi_real_data.py` và `views/logi_view_model.py`; hiển thị cụm `ShipmentFinanceSummary` trên `/lo-hang` (VND/USD/CNY, không cộng gộp FX, chưa có dòng dịch vụ thực tế giữ nguyên `—`); build bundle `component/dist`; PASS `pytest tests/test_issue254_shipment_debt_glance.py` (`6 passed`), PASS Chromium thực `playwright/issue254_browser.mjs` (`ISSUE254_REAL_CHROMIUM=PASS`) và PASS trọn bộ `pytest tests -q` không thêm skip/xfail.
ĐANG CHỜ: Review/merge PR của Issue #254 vào nhánh tích hợp staging.
BƯỚC TIẾP: Chủ dự án review PR và cấp quyền hoặc đăng bình luận khóa spec trên Issue #254 nếu cần cho cổng `contract-shape`.
BLOCKER: Token GitHub tích hợp trong sandbox trả `HTTP 403 Resource not accessible by integration` khi gọi `POST /issues/254/comments`, nên không tạo được `#issuecomment` trên Issue #254 (đã lưu bản khóa spec tại `evidence/issue254/00-spec-lock.md`, không tự bịa liên kết và không sửa workflow CI).
