# CONTROL-TOWER-PLAYBOOK — Logistics Work Desk

> **Đây là hồ sơ vận hành của dự án, KHÔNG phải luật thứ hai; luật gốc vẫn là
> `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`.**

Cập nhật: 2026-10-20. Phạm vi: cách Control Tower điều phối công việc hiện tại (chuỗi
LOGI-199, PR #211). Trạng thái sống của dự án nằm ở `docs/CONTROL-TOWER-HANDOFF.md` —
file này chỉ nói CÁCH vận hành, không chứa trạng thái.

**PROJECT_DELTA_ONLY:** Đây là hướng dẫn riêng của LOGI, không được thay thế U1 (luật P2P), U2 (giao thức Arena), U3 (hợp đồng Control Tower). Đối chiếu bản thủy tổ pin theo SHA dưới §0.2; Arena repo-scoped đọc luật LOCAL_PORTABLE hợp lệ trong chính repo đích, **không fetch cross-repo**.

## §0 — OPENER

NGUỒN=AGENTS.md §"Control Tower handoff" | U1 RULE 04/05/16.


Khối dán NGUYÊN VĂN cho một chat Control Tower mới:

```text
Bạn là Control Tower dự án Logistics Work Desk. Đọc theo đúng thứ tự này, KHÔNG khảo sát lại repo:
1. https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/refs/pull/211/head/AGENTS.md
2. https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/refs/pull/211/head/.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md
3. https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/refs/pull/211/head/docs/CONTROL-TOWER-PLAYBOOK.md
4. https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/refs/pull/211/head/docs/ARENA-OPERATING-GUIDE.md
5. https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/refs/pull/211/head/.p2p/portable/P2P-EXPERIENCE-CAPSULE.json (kinh nghiệm ACTIVE — non-authoritative, 4KB)
6. Bài học đã trả giá: docs/CONTROL-TOWER-PLAYBOOK.md §9 + AGENTS.md §"Bài học tích lũy" — đọc TRƯỚC khi viết prompt giao việc
Kiểm tra head PR + comment mới nhất qua api.github.com (xem §6).
Sau đó báo ngắn: đang ở đâu, NEXT_ACTION, rồi hỏi Owner phiên này làm gì. Không tự code.
```

Link neo theo PR #211 thường là bản mới nhất; raw.githubusercontent có thể bị CDN trả bản CŨ (đã gặp ca này với AGENTS.md ngày 2026-10-20) — khi cần chắc, đối chiếu head.sha qua api.github.com rồi đọc theo SHA đó.

Năm link raw `refs/pull/211/head` trỏ theo trạng thái PR #211, không phụ thuộc tên nhánh. Nếu link 404 thì dùng `head.ref` theo fallback dưới đây; đừng đọc `main` thay cho PR đang mở.

link 404 → mở https://api.github.com/repos/7roger89-web/logistics-work-desk-arena/pulls/211 lấy head.ref rồi thay chuỗi refs/pull/211/head bằng tên nhánh đó; sau khi merge main thì đổi 5 link sang .../main/...; link theo SHA dùng cho bằng chứng

## §0.2 — QUAN HỆ VỚI LUẬT P2P

NGUỒN=U1 §1, §2A, §4 | U2 §1/§6/§8 | U3 §"Three-layer lifecycle".


- File này là HỒ SƠ VẬN HÀNH cấp dự án, không phải luật. Luật gốc: .p2p/portable/P2P-OPERATIONS-NOTEBOOK.md (projection hợp lệ, không sửa tay).
- Thứ bậc khi khác nhau: notebook (luật P2P) > AGENTS.md (luật dự án) > playbook > arena guide > handoff (chỉ là TRẠNG THÁI, không phải luật).
- Không mục nào được nới quyền Owner, đổi acceptance, hay tạo router/registry/daemon mới. Muốn nâng quy tắc LOGI thành P2P phải qua `RULE_ASSIMILATION_GATE_V1` tại thủy tổ, không sửa tay `.p2p/portable/*`.
- Mỗi mục ghi nguồn gốc rule notebook; notebook đổi thì cập nhật theo, không tự nghĩ luật mới. Gắn nguồn cho tối thiểu: §3/§4 (hợp đồng prompt ← §2A mandatory prompt serialization + RULE 06/09/10), §7 (failover ← §2A executor-aware + RULE 20), §8 (bất biến liên tục ← RULE 04/05/16).
- NEXT_PACKET là PROMPT GIAO VIỆC cấp dự án, KHÔNG phải packet schema mới. Packet P2P thực: `P2P_CONTROL_TOWER_SUCCESSOR_PACKET`, `CONTROL_TOWER_ROTATION_HANDOFF`, `CONTROL_TOWER_RETURN_PACKET` (U3).
- LOGI `docs/CONTROL-TOWER-HANDOFF.md` chở **STATE**, KHÁC với thủy tổ `docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md` (hợp đồng P2P). `GITHUB_PROJECT_STATE_IS_CANONICAL`, `ARENA_CHAT_STATE_IS_EPHEMERAL` (U2); state không tự sinh luật.


**Nguồn U1/U2/U3 — pin theo commit thủy tổ `db9d39798ddb80990757c65ddf2eb95f9f734fd6` (đã đối chiếu nội dung `main` ngày 2026-10-20):**

- U1 · luật P2P: https://raw.githubusercontent.com/7roger89-web/P2P-upgrade-github-1/db9d39798ddb80990757c65ddf2eb95f9f734fd6/docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md · SHA-256 `11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`.
- U2 · hợp đồng Arena: https://raw.githubusercontent.com/7roger89-web/P2P-upgrade-github-1/db9d39798ddb80990757c65ddf2eb95f9f734fd6/docs/ARENA_AGENT_MODE_PROTOCOL.md · SHA-256 `9315f603ab80dc45e46fc6c2dabb98e7f5e0a212108ff3504fd8515f4bb900c3`.
- U3 · handoff Control Tower: https://raw.githubusercontent.com/7roger89-web/P2P-upgrade-github-1/db9d39798ddb80990757c65ddf2eb95f9f734fd6/docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md · SHA-256 `d5e45cea2e75ac0b9c10110423165c2f42b0f40436b3267a55ef08db9de9c443`.

Các URL pin là **chứng cứ nguồn gốc**, không đóng băng luật hiệu lực: ChatGPT/Codex phải ưu tiên canonical hiện hành khi đọc được. Arena đang giới hạn repo phải đọc `AGENTS.md` và bản `LOCAL_PORTABLE`, không bị yêu cầu truy vấn repo thủy tổ. Thang law-source của `AGENTS.md`: `CANONICAL_AUTHENTICATED > LOCAL_INSTALLED > LOCAL_PORTABLE > INLINE_CAPSULE > LAW_CONTEXT_BLOCKED`. Không tạo notebook hay schema packet song song.

## §1 — LÀN VÀ NĂNG LỰC

NGUỒN=U3 §"Beginner workflow" | U2 §2–4 | AGENTS.md Owner Gate.


| Làn | Là ai | Được làm | KHÔNG làm được / cấm |
|---|---|---|---|
| Owner | chủ dự án | quyết định nghiệp vụ, dữ liệu thật, duyệt merge/deploy, **chốt Owner Gate — chỉ Owner chốt** | — |
| Control Tower | Venice (não chính) hoặc não dự phòng theo §7 | đọc repo/PR/comment, viết & siết prompt, cập nhật handoff, kiểm bằng chứng, điều phối | **Venice không ghi được repo** — mọi ghi đi qua executor hoặc GitHub Edit có kiểm chứng; không tự code |
| Executor Arena | phiên Arena Agent Mode | sửa code/docs trên nhánh session, chạy pytest/node, push nhánh session, báo SHA | **không có browser** (không Chromium → mọi browser claim = `BROWSER_NOT_VERIFIED`); không merge/deploy/push nhánh khác/PR mới |
| Executor Codex | Codex desktop trên máy Owner (Windows) | checkout thật, test runner, **có Chromium → làn browser QA duy nhất hiện có** | không tự merge/deploy; bằng chứng local phải đưa lên nơi Control Tower đọc được |
| QA độc lập | một phiên KHÁC phiên đã làm việc | đối chiếu acceptance cố định, chạy lại bằng chứng, verdict `PROVEN/INCOMPLETE/FAILED` | không tự nghiệm thu việc mình làm; không sửa code trong phiên QA |

## §2 — COLD START

NGUỒN=U1 §2A preflight + RULE 05/16 | AGENTS.md TASK 0.
Link neo theo PR #211 thường là bản mới nhất; raw.githubusercontent có thể bị CDN trả bản CŨ (đã gặp ca này với AGENTS.md ngày 2026-10-20) — khi cần chắc, đối chiếu head.sha qua api.github.com rồi đọc theo SHA đó.
Notebook portable 139KB — đủ dùng cho Control Tower là §2A + các RULE được trỏ tới trong playbook §0.2; phần còn lại tra khi cần, đừng đọc hết mặc định.


- **Thứ tự đọc bắt buộc** (đúng như §0): AGENTS.md → portable law → playbook → handoff
  → head PR + comment mới nhất. **Nếu link nào 404**: mở PR đang mở, lấy TÊN NHÁNH từ
  đó rồi đọc lại theo nhánh đó — KHÔNG đoán tên nhánh.
- **Bắt buộc xác minh lại sự thật nền**: head PR thật (api.github.com, §6), worktree/
  branch thật của executor. Coi mọi con số trong handoff là "khai báo", không phải sự
  thật, cho tới khi có bằng chứng đo lại trong phiên hiện tại.
- **Cấm khảo sát lại repo từ đầu** — kế hoạch, quyết định và trạng thái đã nằm trong
  handoff; khảo sát lại vừa tốn quota vừa sinh bản kế hoạch song song.

## §3 — MẪU PROMPT CHUẨN

NGUỒN=U1 §2A prompt serialization + RULE 06/09/10 | U2 §6.


Mọi mẫu phải đủ hợp đồng §4; dưới đây chỉ nêu field riêng và điểm siết của từng làn.

- **W1 — sửa code (Arena/Codex)**. Field riêng: `RED_BEFORE` (chạy lại test/module trên
  code cũ, fail đúng phản ví dụ), `GREEN_AFTER`,
  `BASELINE_COMPARE=NEW=∅/GONE=∅ cùng môi trường`, `REBUILD_DIST` (nếu đụng source
  React: cùng commit + marker parity source↔dist), `BROWSER_QA` khi task đụng UI theo
  "Definition of Done tối thiểu cho task đụng UI" trong AGENTS.md. Bắt buộc neo
  file:line ở đúng HEAD; cấm mở rộng scope; không chạy được thì ghi `NOT_RUN`, cấm PASS.
- **W2 — QA độc lập (phiên khác, không phải phiên đã làm)**. Field riêng:
  `QA_TARGET_SHA=<sha được kiểm>`, `ACCEPTANCE_SOURCE` (trỏ tiêu chí cố định của W1,
  không tự viết lại), `VERDICT=PROVEN|INCOMPLETE|FAILED`,
  `EVIDENCE_LOCATION=<comment PR hoặc docs/>` (nơi Control Tower đọc được). QA chỉ
  đọc/đo/chạy lại, không sửa; không tin self-report của executor.
- **W3 — docs**. Field riêng: `DOCS_ONLY=yes`,
  `FORBID=code Python/React, component/dist, .p2p/portable/*, mọi block <!-- BEGIN P2P -->`,
  `HANDOFF_UPDATE=yes`. Mọi nhận định về code/trạng thái phải trích `file:line` ở đúng
  HEAD và đính kèm số liệu đo được, không chép lại số cũ mù.
- **W4 — kiểm ancestry + fast-forward head PR**. Field riêng:
  `EXPECTED_SESSION_HEAD=<sha executor báo>`, `FF_ONLY=yes`, `DIVERGENT=STOP` (không
  force-push; DỪNG, kiểm lại diff PR và handoff). Arena/executor không bao giờ merge;
  bước này do Control Tower/Owner chạy sau khi kiểm ancestry.

## §4 — HỢP ĐỒNG PROMPT BẮT BUỘC

NGUỒN=U1 §2A mandatory prompt serialization + skill routing | AGENTS.md.


Mọi prompt giao executor phải có đủ: `destination` · `CHAT_MODE` · `CHAT_TITLE` (với
Arena: dòng đầu tiên chính là title) · `ROLE` · `PROJECT` · `REPO` · `PR` ·
`EXACT_BASE_HEAD` · nhánh sẽ push · `TASK_ID` · `TASK_AUTHORITY` · mục tiêu · phạm vi
trong/ngoài · neo `file:line` · bất biến phải giữ · bằng chứng bắt buộc · tiêu chí
nghiệm thu cố định · điều cấm · stop condition · `REQUIRED_SKILLS` (path + SHA256 thật
từ `.p2p/portable/P2P-SKILL-PROJECTION.json`) · `P2P_LAW_PREFLIGHT` · `OE_GATE` ·
`HANDOFF_UPDATE=yes`.

Thiếu bất kỳ field nào ⇒ prompt chưa đủ chặt — viết lại TRƯỚC khi gửi, không gửi rồi vá.

## §5 — KHAI THÁC ARENA TỐI ĐA

NGUỒN=U2 §1–7 | docs/ARENA-OPERATING-GUIDE.md (project delta).


- Chỉ giao việc có test deterministic.
- Không đặt acceptance cần browser.
- Kiểm nhánh mồ côi (`GET /repos/.../branches?per_page=100` — xem §9).

chi tiết đầy đủ: docs/ARENA-OPERATING-GUIDE.md

## §6 — ĐƯỜNG ĐỌC RẺ CHO CONTROL TOWER (api.github.com)

NGUỒN=AGENTS.md evidence/TASK 0 | U1 RULE 04/05/16.


- `GET /repos/7roger89-web/logistics-work-desk-arena/pulls/211` → `head.sha`, `base.ref`,
  `mergeable`, `state`.
- `GET /repos/7roger89-web/logistics-work-desk-arena/issues/211/comments?per_page=5&direction=desc&sort=created`
  → comment mới nhất (bằng chứng QA, quyết định Owner — ví dụ comment `#6281985539`).
- `GET /repos/7roger89-web/logistics-work-desk-arena/pulls/211/commits?per_page=5` → các
  commit mới trên head.
- `GET /repos/7roger89-web/logistics-work-desk-arena/git/ref/heads/arena/a3117943-logistics-work-desk-arena`
  → head ref thật khi cần đối chiếu nhanh trước fast-forward.
- `GET /repos/7roger89-web/logistics-work-desk-arena/contents/docs/CONTROL-TOWER-HANDOFF.md?ref=<nhánh đang làm>`
  → đọc handoff qua API khi không mở trang PR.
- `GET /repos/7roger89-web/logistics-work-desk-arena/compare/{sha_cu}...{sha_moi}`
  → kiểm ancestry trước fast-forward; diverged thì DỪNG.
- `GET /repos/7roger89-web/logistics-work-desk-arena/branches?per_page=100`
  → bắt nhánh mồ côi.

Luật: mở trang PR đầy đủ (web UI) tối đa 1 lần/phiên; handoff mục 3 giữ gọn trong 1 màn
hình (chi tiết dài đẩy xuống mục 6).

## §7 — FAILOVER KHI CONTROL TOWER MẤT QUOTA

NGUỒN=U1 §2A executor-aware + RULE 20 | U3 §"Durable Control Tower".


Thang 5 tầng, chuyển xuống khi tầng trên chết:

- **L1 — Venice (não chính)**: điều phối đầy đủ theo playbook này.
- **L2 — ChatGPT + GitHub connector**. Trigger: **Venice không đọc được repo** → chuyển
  L2; connector đọc/ghi repo, giữ nguyên hợp đồng §4 và thứ tự đọc §0.
- **L3 — Codex (desktop máy Owner)**. Trigger: **L2 cũng chết** → Codex vừa điều phối tối
  thiểu vừa tự thực thi bounded task (có checkout thật + Chromium).
- **L4 — Owner điều phối tay**. Trigger: cả L1–L3 không dùng được → Owner đọc handoff
  mục 3, tự chuyển `NEXT_PACKET` cho executor sẵn có.
- **L5 — Arena-only**. Trigger: **hết não** → dán nguyên `NEXT_PACKET` (handoff mục 3)
  vào Arena NEW_CHAT; executor tự law-preflight theo AGENTS.md.

Mọi não khi kết phiên PHẢI để lại `NEXT_ACTION` + `NEXT_PACKET` ở handoff mục 3 trước
khi hết quota — chết mà không để packet là mất ca tiếp theo.

## §8 — BẤT BIẾN LIÊN TỤC

NGUỒN=U1 RULE 04/05/16 | U2 §8 | U3 §"Three-layer lifecycle".


- Không bao giờ để kế hoạch chỉ nằm trong chat.
- Cuối mỗi phiên Control Tower: handoff mục 3 có `NEXT_ACTION` + `NEXT_PACKET`; packet
  phải dán được ngay.
- Sắp hết quota: viết packet trước, đọc thêm sau.
- Bằng chứng QA phải ở nơi Control Tower đọc được.
- Không ai tự nghiệm thu việc mình làm.

## §9 — BÀI HỌC ĐÃ TRẢ GIÁ

NGUỒN=docs/CONTROL-TOWER-HANDOFF.md MỤC 6 (LOGI-only evidence) + docs/CONTROL-TOWER-ARCHIVE.md; not a new P2P law.


- Commit mồ côi: `f51710b` bị push vào nhánh không ai theo dõi (`arena/da9aa3db-...`) →
  mất một lượt tìm, phải truy vết + cherry-pick (`162036f`). Sau mỗi phiên phải kiểm
  nhánh mồ côi.
- Sửa source React mà không rebuild `component/dist` → màn hình chạy bundle cũ, người QA
  nhìn thấy hành vi không còn tồn tại trong source (đã mất một vòng "fix" ma).
- Bằng chứng QA/browser chỉ nằm ở ổ đĩa máy trạm → Control Tower không đọc được, coi như
  không có (browser QA 2026-10-20 phải đăng lại qua comment PR `#6281985539`).
- Prompt 1 dòng thiếu law preflight / OE gate → executor làm lệch chuẩn, mất cả phiên
  làm lại; hợp đồng §4 không phải thủ tục.
- Hướng dẫn stale ("kỳ vọng 200 passed, 28 skipped"; baseline C13/C14/C15) làm người đọc
  sau hiểu sai cả trạng thái lẫn cách đọc test — đã sửa tại AGENTS.md ngày 2026-10-20.

