# Branch cleanup — 2026-10-26 (Phase B)

## Số liệu trước/sau (đo bằng `git ls-remote --heads origin`)

| Thời điểm | Số remote head | Ghi chú |
|---|---:|---|
| Trước cleanup | 267 | audit đầu phiên |
| Sau khi push nhánh session | 268 | thêm `arena/cf3205ad-logistics-work-desk-arena` |
| Sau cleanup | 115 | đã xóa 153 branch merged |

Truy vết: 268 − 153 = 115. Ngoài nhánh session, các head còn lại = `main` +
113 branch **chưa merge** (giữ nguyên, không nằm trong gate lần này).

## Tiêu chí chọn branch xóa

1. Tip commit là ancestor của `main` (`git merge-base --is-ancestor <branch> origin/main`)
   — tức toàn bộ nội dung đã nằm trong lịch sử main, xóa không mất commit nào.
2. Loại trừ `main` và chính nhánh session đang làm việc.
3. Loại trừ head của 16 PR đang mở (đối chiếu `gh pr list --state open`); thực tế
   không head PR mở nào thuộc tập merged.
4. Tag `logi199-owner-trial` được giữ nguyên (không đụng bất kỳ tag nào).
5. Không history rewrite: chỉ xóa *ref*, mọi commit vẫn nằm trong lịch sử `main`.

Danh sách đầy đủ 153 branch đã xóa: `docs/history/merged-branches-deleted-2026-10-26.txt`.
Kết quả thực thi: 153/153 thành công, 0 lỗi (152 qua batch + 1 kiểm chứng thủ công đầu tiên).

## Hạng mục bị chặn bởi quyền token

Repo description/topics và branch protection trên `main` trả về HTTP 403 với token
tích hợp (mặc dù metadata quyền hiển thị admin). Lệnh và payload cho Owner đã được
chuẩn bị sẵn tại `docs/OWNER_REPO_SETTINGS.md`.
