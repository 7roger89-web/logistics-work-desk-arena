# ARENA-OPERATING-GUIDE — Logistics Work Desk

**PROJECT_DELTA_ONLY:** hướng dẫn những khác biệt đã quan sát khi làm LOGI. Đây KHÔNG phải luật P2P thứ hai, không thêm quyền, router, registry, daemon hoặc điều kiện nghiệm thu.
Thứ bậc: notebook canonical đang tới được > AGENTS.md (ràng buộc dự án) > playbook > guide này > handoff (chỉ chở trạng thái). Khi không thể đọc canonical, Arena làm theo thang preflight trong AGENTS.md và bản `LOCAL_PORTABLE` hợp lệ.
Nguồn tham chiếu thủy tổ (pin `db9d39798ddb80990757c65ddf2eb95f9f734fd6`, dùng để truy vết; không phải bản luật mới):
- **U1 — notebook:** https://raw.githubusercontent.com/7roger89-web/P2P-upgrade-github-1/db9d39798ddb80990757c65ddf2eb95f9f734fd6/docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md
- **U2 — hợp đồng Arena:** https://raw.githubusercontent.com/7roger89-web/P2P-upgrade-github-1/db9d39798ddb80990757c65ddf2eb95f9f734fd6/docs/ARENA_AGENT_MODE_PROTOCOL.md
- **U3 — handoff Control Tower:** https://raw.githubusercontent.com/7roger89-web/P2P-upgrade-github-1/db9d39798ddb80990757c65ddf2eb95f9f734fd6/docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md

**Ranh giới truy cập:** phiên Arena đang dùng chỉ đọc repo đích; **KHÔNG yêu cầu Arena fetch cross-repo**. ChatGPT/Codex/Owner có đường đọc thủy tổ khi công cụ cho phép; Arena đọc `AGENTS.md` và `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`. Link pin là nguồn gốc bằng chứng, luật hiệu lực luôn theo nguồn hợp lệ mới nhất.
Arena là executor thực thi; Control Tower điều phối, nhưng không bên nào được tự nghiệm thu.

## 1. Arena thực sự làm việc thế nào (sự thật đã quan sát)

NGUỒN=U2 §1–4 và §6 | quan sát repo/phiên Arena, không coi đặc tính host là luật phổ quát.

- Mỗi chat Arena là một phiên riêng, tự sinh một NHÁNH SESSION riêng: `arena/<session-id>-logistics-work-desk-arena`.
- Session rule: Arena push được nhánh session của nó, KHÔNG push nhánh khác → head PR phải được fast-forward riêng (Control Tower/Owner/Codex làm).
- Dòng đầu tiên của prompt đầu tiên trở thành TIÊU ĐỀ chat → luôn đặt tiêu đề ngắn, có từ khóa dự án.
- Có hành động "keep working" để làm tiếp trong CÙNG chat — dùng cho vòng sửa, đừng mở chat mới cho từng micro-fix.
- Arena có shell: python/pytest, node/npm (jsdom chạy được DOM lane), git. GitHub repo-scoped: CHỈ thấy repo này, KHÔNG đọc được repo P2P riêng → phải dùng portable law.
- Arena KHÔNG có Chromium → mọi claim giao diện là `BROWSER_NOT_VERIFIED`. Browser là việc của Codex/Windows.
- Arena không merge, không deploy. Sandbox có thể bị dựng lại giữa phiên → commit + push SỚM.

## 2. Luật bất biến khi giao việc cho Arena

NGUỒN=U1 §2A, RULE 06/07/09/10 | U2 §2/§6 | AGENTS.md hợp đồng prompt.

- Một chat = một mục tiêu hẹp = một nhánh. Việc xong thì đóng chat.
- Prompt BẮT BUỘC có: dòng đầu là tiêu đề; destination; CHAT_MODE; REPO; PR; EXACT_BASE_HEAD; TASK_ID; TASK_AUTHORITY; mục tiêu; phạm vi trong/ngoài; neo `file:line`; bất biến phải giữ; bằng chứng bắt buộc; tiêu chí nghiệm thu cố định; điều cấm; stop condition; REQUIRED_SKILLS (path + SHA256 thật); P2P_LAW_PREFLIGHT; OE_GATE; HANDOFF_UPDATE=yes.
- Luôn yêu cầu: "push nhánh session rồi BÁO TÊN NHÁNH + SHA".
- Bắt buộc RED-before/GREEN-after cho bug fix; full suite so baseline cùng môi trường (`NEW=∅/GONE=∅`); không chạy được thì ghi `NOT_RUN` — CẤM gọi PASS.
- Arena không tự chấm điểm; QA là phiên KHÁC.
- CẤM: đụng main, force-push, PR mới, đụng app `tienthanhlog`, production write, mở rộng scope, đổi schema ngoài phạm vi.

## 3. Bằng chứng Arena phải trả

NGUỒN=U1 §2A evidence/skill consumption | U2 §7 | AGENTS.md TASK CUỐI.

Commit SHA cuối + danh sách file đổi; kết quả focused test/typecheck/build/scan; so baseline NEW/GONE; HANDOFF_UPDATE=yes; `p2p-skill-consumption-receipt/1`; nêu rõ phần CHƯA kiểm (`NOT_RUN`) thay vì gọi là PASS.

## 4. Mất chat / mất sandbox — không mất việc

NGUỒN=U1 RULE 04/05/16 | U2 §8 | repo GitHub là checkpoint.

- Việc chỉ an toàn khi đã COMMIT + PUSH + báo tên nhánh và SHA.
- Chat chết giữa chừng: đọc báo cáo cuối lấy nhánh + SHA → kiểm ancestry → mở chat mới, tiếp tục TỪ SHA ĐÓ. KHÔNG làm lại từ đầu.
- Sau mỗi phiên Arena: kiểm nhánh mồ côi (`GET /repos/.../branches?per_page=100`).
- Sandbox bị dựng lại: đối chiếu blob với origin rồi `reset --hard` về commit đã push, không làm lại việc.

## 5. Điểm yếu đã trả giá (đừng lặp lại)

NGUỒN=docs/CONTROL-TOWER-HANDOFF.md MỤC 6 | bài học riêng của dự án, không phải luật P2P.

- Commit mồ côi `f51710b`: push vào nhánh không ai biết → mất một lượt truy vết.
- Sửa source React mà không rebuild `component/dist` → QA nhìn bundle cũ, mất một vòng "fix" ma.
- Bằng chứng chỉ ở ổ đĩa local → Control Tower không đọc được, coi như không có.
- Prompt 1 dòng thiếu law preflight/OE gate → lệch chuẩn, mất cả phiên.
- Nhầm nguồn mode (`s.mode` là chặng đầu, không phải mode vận tải) → dùng `executionProfile.mode`.

## 6. KHÔNG giao cho Arena

NGUỒN=U2 §2–4, §7 | U3 §"Beginner workflow" | AGENTS.md Owner Gate.

Nghiệm thu cần nhìn giao diện (browser); merge/deploy; quyết định nghiệp vụ; viết prompt cho chính nó; xử lý dữ liệu production thật.

## 7. Phân biệt tài liệu và gói bàn giao

NEXT_PACKET ở handoff là **prompt công việc của dự án**, không phải schema P2P. `docs/CONTROL-TOWER-HANDOFF.md` của LOGI là STATE, khác với `docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md` của thủy tổ (hợp đồng điều hành). Nếu muốn nâng quy tắc dự án lên P2P, phải qua `RULE_ASSIMILATION_GATE_V1` ở thủy tổ, không sửa bản portable trong LOGI. Xem 6 ranh giới P2P ở docs/CONTROL-TOWER-PLAYBOOK.md §0.2 — đó là 6 GẠCH ĐẦU DÒNG mục "QUAN HỆ VỚI LUẬT P2P"; §0.2 KHÔNG có "bảng T1–T6" nào, đừng tìm bảng ở đó (con trỏ cũ sai, đã sửa 2026-10-20).

NGUỒN=U1 §1 và §4 | U3 §"Return contract" và §"Three-layer lifecycle".
