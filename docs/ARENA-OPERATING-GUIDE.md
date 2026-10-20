# ARENA-OPERATING-GUIDE — Logistics Work Desk

Hướng dẫn vận hành Arena cho dự án này. KHÔNG phải luật thứ hai; luật gốc: `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`.
Thứ bậc: notebook > AGENTS.md > file này > handoff. File này không tạo router/registry/quyền mới.
Arena là TAY (executor), không phải NÃO. Não là Control Tower.

## 1. Arena thực sự làm việc thế nào (sự thật đã quan sát)
- Mỗi chat Arena là một phiên riêng, tự sinh một NHÁNH SESSION riêng: `arena/<session-id>-logistics-work-desk-arena`.
- Session rule: Arena push được nhánh session của nó, KHÔNG push nhánh khác → head PR phải được fast-forward riêng (Control Tower/Owner/Codex làm).
- Dòng đầu tiên của prompt đầu tiên trở thành TIÊU ĐỀ chat → luôn đặt tiêu đề ngắn, có từ khóa dự án.
- Có hành động "keep working" để làm tiếp trong CÙNG chat — dùng cho vòng sửa, đừng mở chat mới cho từng micro-fix.
- Arena có shell: python/pytest, node/npm (jsdom chạy được DOM lane), git. GitHub repo-scoped: CHỈ thấy repo này, KHÔNG đọc được repo P2P riêng → phải dùng portable law.
- Arena KHÔNG có Chromium → mọi claim giao diện là `BROWSER_NOT_VERIFIED`. Browser là việc của Codex/Windows.
- Arena không merge, không deploy. Sandbox có thể bị dựng lại giữa phiên → commit + push SỚM.

## 2. Luật bất biến khi giao việc cho Arena
- Một chat = một mục tiêu hẹp = một nhánh. Việc xong thì đóng chat.
- Prompt BẮT BUỘC có: dòng đầu là tiêu đề; destination; CHAT_MODE; REPO; PR; EXACT_BASE_HEAD; TASK_ID; TASK_AUTHORITY; mục tiêu; phạm vi trong/ngoài; neo `file:line`; bất biến phải giữ; bằng chứng bắt buộc; tiêu chí nghiệm thu cố định; điều cấm; stop condition; REQUIRED_SKILLS (path + SHA256 thật); P2P_LAW_PREFLIGHT; OE_GATE; HANDOFF_UPDATE=yes.
- Luôn yêu cầu: "push nhánh session rồi BÁO TÊN NHÁNH + SHA".
- Bắt buộc RED-before/GREEN-after cho bug fix; full suite so baseline cùng môi trường (`NEW=∅/GONE=∅`); không chạy được thì ghi `NOT_RUN` — CẤM gọi PASS.
- Arena không tự chấm điểm; QA là phiên KHÁC.
- CẤM: đụng main, force-push, PR mới, đụng app `tienthanhlog`, production write, mở rộng scope, đổi schema ngoài phạm vi.

## 3. Bằng chứng Arena phải trả
Commit SHA cuối + danh sách file đổi; kết quả focused test/typecheck/build/scan; so baseline NEW/GONE; HANDOFF_UPDATE=yes; `p2p-skill-consumption-receipt/1`; nêu rõ phần CHƯA kiểm (`NOT_RUN`) thay vì gọi là PASS.

## 4. Mất chat / mất sandbox — không mất việc
- Việc chỉ an toàn khi đã COMMIT + PUSH + báo tên nhánh và SHA.
- Chat chết giữa chừng: đọc báo cáo cuối lấy nhánh + SHA → kiểm ancestry → mở chat mới, tiếp tục TỪ SHA ĐÓ. KHÔNG làm lại từ đầu.
- Sau mỗi phiên Arena: kiểm nhánh mồ côi (`GET /repos/.../branches?per_page=100`).
- Sandbox bị dựng lại: đối chiếu blob với origin rồi `reset --hard` về commit đã push, không làm lại việc.

## 5. Điểm yếu đã trả giá (đừng lặp lại)
- Commit mồ côi `f51710b`: push vào nhánh không ai biết → mất một lượt truy vết.
- Sửa source React mà không rebuild `component/dist` → QA nhìn bundle cũ, mất một vòng "fix" ma.
- Bằng chứng chỉ ở ổ đĩa local → Control Tower không đọc được, coi như không có.
- Prompt 1 dòng thiếu law preflight/OE gate → lệch chuẩn, mất cả phiên.
- Nhầm nguồn mode (`s.mode` là chặng đầu, không phải mode vận tải) → dùng `executionProfile.mode`.

## 6. KHÔNG giao cho Arena
Nghiệm thu cần nhìn giao diện (browser); merge/deploy; quyết định nghiệp vụ; viết prompt cho chính nó; xử lý dữ liệu production thật.
