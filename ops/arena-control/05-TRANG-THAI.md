# TRẠNG THÁI
TASK_ID: OPS-SOURCE-RETRIEVAL-FIX-20261101
MỤC TIÊU: Chọn nguồn đọc Control Tower theo capability thật; dừng khi nguồn đầu thành công; không kết luận "ba URL sai" từ CACHE_MISS/NETWORK_FAILURE.
GIAI ĐOẠN: Đã sửa 00-LUAT.md, tạo bằng chứng và đề xuất Project instructions; PR mở từ nhánh task, chờ review. Không tự merge.
ĐÃ THỬ: `bash evidence/OPS-SOURCE-RETRIEVAL-FIX-20261101/verify_source_retrieval.sh` exit 0 (gh api == git show origin/main cho 00/05/06; STATE_PREFIX động; 404 = NOT_FOUND; raw.githubusercontent = NETWORK_FAILURE rc=35; mô phỏng A/B/C đều đúng). GitHub connector: unsupported trong Arena.
ĐANG CHỜ: Owner review PR; Owner dán khối "NGUỒN ĐỌC CONTROL TOWER" vào ChatGPT Project (chưa dán, chưa xác nhận đã dán).
BƯỚC TIẾP: Sau khi Owner dán, chạy một phiên ChatGPT mới để kiểm tra kịch bản A (web fetch lỗi, connector đọc được) và ghi receipt.
BLOCKER: Kịch bản A chưa chạy live (connector GitHub không có trong Arena). ChatGPT Project chưa cập nhật.
