# TRẠNG THÁI
TASK_ID: OPS-FIX-2
MỤC TIÊU: Chèn thứ bậc luật (AGENTS.md > file này > instructions ChatGPT) lên đầu ops/arena-control/00-LUAT.md; xoá dòng cuối trùng lặp về thứ tự thắng-thua.
GIAI ĐOẠN: xong
ĐÃ THỬ: head -4 thấy tiêu đề + 2 dòng thứ bậc; grep -c `<mẫu-cấm-dòng-cuối>` = 0; grep -n `<mẫu-cấm>` không ra kết quả; git diff --stat chỉ 1 file (2 thêm, 1 xoá).
ĐANG CHỜ: Review/merge PR #252 (nhánh arena/82bbe73c-logistics-work-desk-arena, head d8524c2).
BƯỚC TIẾP: Chờ review PR #252 rồi merge vào main.
BLOCKER: Không có.
