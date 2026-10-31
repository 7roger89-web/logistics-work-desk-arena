# TRẠNG THÁI
TASK_ID: LOGI-247-STAGING-READBACK-20261031
MỤC TIÊU: Xác minh staging sau merge PR #248 (PR MERGED + staging chứa head đã nghiệm thu + S1/S2/S3 còn nguyên).
GIAI ĐOẠN: xong phần đo — BLOCKED, chưa nghiệm thu được.
ĐÃ THỬ: `gh api .../pulls/248` = state open, merged false, merged_at null; `gh api .../pulls/248/merge` = 404, exit 1; `gh api .../branches` 124 nhánh, grep staging/stage/preprod/uat = không có, `branches/staging` = 404; compare staging...head = ahead_by 8, behind_by 0, merge_base = đúng tip staging; compare main...head = diverged; sha256 + `cmp` 5 file S1/S2/S3 ở 4 ref; `contract-shape` = pass. Toàn bộ transcript: `evidence/LOGI-247-STAGING-READBACK-20261031/`.
ĐANG CHỜ: Owner/Control Tower merge PR #248 rồi chạy lại `collect.sh`.
BƯỚC TIẾP: Sau khi merge, chạy lại collector để nghiệm thu lại tiêu chí "staging chứa head đã nghiệm thu".
BLOCKER: PR #248 chưa merge (state open), và repo không có nhánh tên `staging`; "staging" trong PR là `arena/ae5f9f47` đang đứng sau head 8 commit.
GHI CHÚ: Không tự merge, không sửa staging, không suy ra Cloud/OIDC PASS từ merge GitHub.
