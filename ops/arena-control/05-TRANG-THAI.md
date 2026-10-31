# TRẠNG THÁI
TASK_ID: OPS-FIX-3
MỤC TIÊU: Chốt 2 luật mới (cấm tạo PR body có backtick bằng chuỗi lệnh, phải dùng `--body-file`; khung prompt ghi rõ chỉ sửa `<file>`, 05/06 chỉ để ghi log) và đưa dòng ĐANG CHỜ về PR hiện tại.
GIAI ĐOẠN: xong (chờ review/merge PR)
ĐÃ THỬ: `grep -c "body-file"` 00-LUAT.md = 1; `grep -c "chỉ để ghi log"` 02-TEMPLATE.md = 1; `grep -n "ĐANG CHỜ"` 05 khớp `git rev-parse HEAD` của commit nội dung; `git diff --stat` đúng phạm vi ops/arena-control (00, 02, 05 + 06 log).
ĐANG CHỜ: Review/merge PR #253 (nhánh arena/532dec89-logistics-work-desk-arena, head nội dung 9b6b57e; các commit nối sau chỉ ghi log 05/06 nên head thật = `git rev-parse HEAD` / `gh pr view 253 --json headRefOid`).
BƯỚC TIẾP: Chờ review/merge PR #253 rồi merge vào main.
BLOCKER: Không có.
