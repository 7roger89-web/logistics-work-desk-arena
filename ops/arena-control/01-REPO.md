# SỰ THẬT REPO
7roger89-web/logistics-work-desk-arena. Python + Streamlit. main là baseline.
AGENTS.md ở gốc là luật gốc, bắt buộc preflight.
Test: python -m pytest tests -q. Suite đỏ có chủ ý — lấy baseline trước khi sửa.
Bằng chứng: `evidence/<task-id>/`. Không nhận tự khai.
Không deploy production khi chưa có Owner gate.

## Ngân sách token, Arena có ~98k
AGENTS.md 29,9KB ≈ 8k. Notebook 138,8KB ≈ 35k. p2p-uiux SKILL.md 9,5KB ≈ 2k.
Đọc AGENTS.md là đủ. Notebook chỉ khi AGENTS.md trỏ mục cụ thể.

## HEAD
Ghi HEAD và PR head. Lệch thì so sánh worktree với PR head rồi báo.
Không reset, không stash, không xoá thay đổi chưa commit, không commit ngoài yêu cầu.

## Skill
Chỉ khi khớp, tối đa 3. UI: .agents/skills/p2p-uiux/SKILL.md sha256
98f26873e48cc87e34d132478f73672a80d20b3a8e1a2256bdcdab4d6107e7b2.
Backend thuần: không nạp pack frontend. Không khớp: SKILL_CHECK=NO_MATCH.
