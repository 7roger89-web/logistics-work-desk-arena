# TRẠNG THÁI
TASK_ID: OPS-SOURCE-RETRIEVAL-FIX-20261101
MỤC TIÊU: Chọn nguồn đọc Control Tower theo capability thật; dừng khi nguồn đầu thành công; SUCCESS chỉ khi nội dung đã decode đúng header và đúng ref; không kết luận "ba URL sai" từ CACHE_MISS/NETWORK_FAILURE.
GIAI ĐOẠN: Vòng 2 (PR #256): đã sửa fallback contract (thay ba URL cũ bằng raw + api.github.com), cổng nội dung chặn HTML/JSON chưa decode/rỗng/sai header/sai ref; đồng bộ 00-LUAT và đề xuất Project. Chờ review. Không tự merge.
ĐÃ THỬ: `bash evidence/OPS-SOURCE-RETRIEVAL-FIX-20261101/verify_source_retrieval.sh` exit 0 (LIVE: gh/git/api.github.com đều SUCCESS và khớp blob; github.com/blob trả HTML bị HTML_PAGE; raw.githubusercontent NETWORK_FAILURE rc=35; file 05 ở commit khác bị WRONG_REF; file thiếu NOT_FOUND. SIM: CACHE_MISS, EMPTY, HEADER_MISMATCH, WRONG_PATH, ENCODING_INVALID, JSON_INVALID; kịch bản A/B/C/D).
ĐANG CHỜ: Owner review PR #256; Owner dán khối "NGUỒN ĐỌC CONTROL TOWER" vào ChatGPT Project (chưa dán).
BƯỚC TIẾP: Sau khi dán, chạy phiên ChatGPT mới để kiểm kịch bản A live (connector được chọn trước web fetch).
BLOCKER: Kịch bản A chưa chạy live (connector GitHub không có trong Arena). ChatGPT Project chưa cập nhật.
