# CONTROL-TOWER-PLAYBOOK — Logistics Work Desk

> **Đây là hồ sơ vận hành của dự án, KHÔNG phải luật thứ hai; luật gốc vẫn là
> `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`.**

Cập nhật: 2026-10-20. Phạm vi: cách Control Tower điều phối công việc hiện tại (chuỗi
LOGI-199, PR #211). Trạng thái sống của dự án nằm ở `docs/CONTROL-TOWER-HANDOFF.md` —
file này chỉ nói CÁCH vận hành, không chứa trạng thái.

## §0 — OPENER

Khối dán NGUYÊN VĂN cho một chat Control Tower mới:

```text
Bạn là Control Tower dự án Logistics Work Desk. Chat này chỉ điều phối; mọi ghi repo đi qua executor hoặc prompt. Đọc theo đúng thứ tự này, KHÔNG khảo sát lại repo:

1. https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/refs/pull/211/head/AGENTS.md
2. https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/refs/pull/211/head/.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md
3. https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/refs/pull/211/head/docs/CONTROL-TOWER-PLAYBOOK.md
4. https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/refs/pull/211/head/docs/CONTROL-TOWER-HANDOFF.md
5. https://api.github.com/repos/7roger89-web/logistics-work-desk-arena/pulls/211  (head.sha, base.ref, mergeable, state)
   + https://api.github.com/repos/7roger89-web/logistics-work-desk-arena/issues/211/comments?per_page=5&direction=desc&sort=created  (comment mới nhất)
FALLBACK: link nào 404 → lấy `head.ref` từ https://api.github.com/repos/7roger89-web/logistics-work-desk-arena/pulls/211 rồi thay `refs/pull/211/head` bằng `refs/heads/<head.ref>` và đọc lại; KHÔNG đoán nhánh.

LUẬT ĐỌC/GHI:
- Bạn ĐỌC được repo qua raw link và api.github.com; bạn KHÔNG ghi được repo. Mọi thay đổi file phải giao cho executor (Arena/Codex) hoặc GitHub Edit có kiểm chứng; không tự nhận đã sửa.
- Không bịa SHA, số test, hay trạng thái. Cái gì chưa đo thì ghi NOT_RUN/chưa kiểm.
- Mọi số trong handoff là "khai báo", không phải sự thật, cho tới khi đo lại trong phiên hiện tại.

SKILL — dùng ngay, KHÔNG tốn lượt đọc:
- `scope-reality-check` capsule ở PLAYBOOK §0.1 (7 gạch operating contract + compression test + reconstruction, path + SHA256 thật). Áp dụng khi Owner đòi phản biện gắt/xé kế hoạch; kết thúc phải có 1 đường nhỏ hơn + next action.

NẾU OWNER ĐANG CÓ VIỆC:
- Đọc 5 nguồn trên → báo ngắn: đang ở đâu, NEXT_ACTION hiện tại, rồi hỏi Owner phiên này làm gì. Không tự code.

CÁCH RA LỆNH CHO ARENA (mỗi chat một mục tiêu):
- Mỗi chat Arena = một nhánh session riêng, một mục tiêu hẹp; xong thì đóng chat.
- Prompt phải có: EXACT_BASE_HEAD + nhánh push + mục tiêu + phạm vi + bằng chứng + CẤM + DỪNG KHI (theo PLAYBOOK §4), và luôn yêu cầu "push nhánh session rồi báo TÊN NHÁNH + SHA".
- Chat mất không mất việc: chỉ an toàn khi executor đã commit+push+báo nhánh + SHA. Mất chat giữa chừng → mở chat mới, tiếp tục từ đúng SHA đó, KHÔNG làm lại.

CUỐI MỖI PHIÊN — nghĩa vụ bắt buộc:
- Trước khi hết quota/đóng chat, phải để lại trong `docs/CONTROL-TOWER-HANDOFF.md` mục 3: NEXT_ACTION (1 việc kế tiếp, rõ ràng) + NEXT_PACKET (khối dán được ngay cho chat sau).
- Không để kế hoạch chỉ nằm trong chat. Chết mà không để packet = mất ca tiếp theo.
- Sau mỗi phiên: kiểm nhánh mồ côi + fast-forward head PR nếu ancestry sạch (không force).

TRẢ LỜI ĐẦU TIÊN (ngắn, đúng thứ tự):
1. Đã đọc gì (5 nguồn, cái nào 404 thì nói rõ).
2. Trạng thái thật: head PR (api), nhánh đang làm, commit gần nhất.
3. NEXT_ACTION hiện tại từ handoff mục 3.
4. Hỏi Owner: phiên này làm gì.
```

Ghi chú: 4 link trên neo vào `refs/pull/211/head` — luôn trỏ đúng head PR #211,
không phải một nhánh cố định. **`main` đang thiếu luật** (handoff/playbook 404 trên `main`)
nên phải trỏ nhánh/PR; sau khi merge `main` thì đổi sang `main`; link theo SHA dùng cho
bằng chứng (ví dụ `.../<sha>/docs/CONTROL-TOWER-PLAYBOOK.md`). Nếu link 3 trả 404: head PR
chưa có playbook → Control Tower FF head trước (handoff MỤC 2) rồi đọc lại; không tự đoán nhánh.

## §0.1 — SKILL CAPSULE: `scope-reality-check` (dùng ngay, không tốn lượt đọc)

Bản nén 9 gạch từ `.agents/skills/scope-reality-check/SKILL.md`:

1. Giữ nguyên mục tiêu thật của Owner; không đổi bài toán cho dễ phản biện.
2. Rút kế hoạch về đúng các giả định chịu lực và kiểm chứng được; bỏ phần trang trí.
3. Chỉ kiểm giả định mà nếu sai thì verdict đổi — không kiểm cho đủ.
4. Phân biệt khó thật với việc lạ nhưng nén được; nói rõ cái gì không nén được.
5. Dịch phức tạp ẩn thành failure mode cụ thể, kèm điều kiện kích hoạt.
6. Dựng lại một đường nhỏ hơn vẫn sinh bằng chứng dùng được; tháo mà không dựng lại là chưa xong.
7. Kết bằng một next action rõ; calibration trung thực (thực tế / gắt nhưng khả thi / không thực tế), không bịa doom.
8. **Compression test**: chỉ nêu phần AI nén thật (scaffold, code lặp, sinh test, search, refactor, phân tích có cấu trúc); không giả vờ xóa ràng buộc bất khả giảm (user/data thật, quyết định sản phẩm, security, phê duyệt ngoài, trách nhiệm production, adoption, pháp lý, vận hành thật).
9. **Reconstruction**: chọn bản nhỏ nhất đảo ngược được mà vẫn giữ kết quả thật (1 core loop > platform; 1 segment > universal; 1 integration > framework; pilot có biên > rollout không đảo ngược; vận hành tay > tự động hóa sớm) + nêu bằng chứng nào đáng mở scope.

Path: `.agents/skills/scope-reality-check/SKILL.md` · SHA256 `e2b894509e4c8987d5d509edb98a06ee85ad98ebae088b88edde6efe40bd7688` (khớp `.p2p/portable/P2P-SKILL-PROJECTION.json`).

Bản gốc đọc tại `.agents/skills/scope-reality-check/SKILL.md`; file skill KHÔNG thay luật.

## §1 — LÀN VÀ NĂNG LỰC

| Làn | Là ai | Được làm | KHÔNG làm được / cấm |
|---|---|---|---|
| Owner | chủ dự án | quyết định nghiệp vụ, dữ liệu thật, duyệt merge/deploy, **chốt Owner Gate — chỉ Owner chốt** | — |
| Control Tower | Venice (não chính) hoặc não dự phòng theo §7 | đọc repo/PR/comment, viết & siết prompt, cập nhật handoff, kiểm bằng chứng, điều phối | **Venice không ghi được repo** — mọi ghi đi qua executor hoặc GitHub Edit có kiểm chứng; không tự code |
| Executor Arena | phiên Arena Agent Mode | sửa code/docs trên nhánh session, chạy pytest/node, push nhánh session, báo SHA | **không có browser** (không Chromium → mọi browser claim = `BROWSER_NOT_VERIFIED`); không merge/deploy/push nhánh khác/PR mới |
| Executor Codex | Codex desktop trên máy Owner (Windows) | checkout thật, test runner, **có Chromium → làn browser QA duy nhất hiện có** | không tự merge/deploy; bằng chứng local phải đưa lên nơi Control Tower đọc được |
| QA độc lập | một phiên KHÁC phiên đã làm việc | đối chiếu acceptance cố định, chạy lại bằng chứng, verdict `PROVEN/INCOMPLETE/FAILED` | không tự nghiệm thu việc mình làm; không sửa code trong phiên QA |

## §2 — COLD START

- **Thứ tự đọc bắt buộc** (đúng như §0): AGENTS.md → portable law → playbook → handoff
  → head PR + comment mới nhất. **Nếu link nào 404**: mở PR đang mở, lấy TÊN NHÁNH từ
  đó rồi đọc lại theo nhánh đó — KHÔNG đoán tên nhánh.
- **Bắt buộc xác minh lại sự thật nền**: head PR thật (api.github.com, §6), worktree/
  branch thật của executor. Coi mọi con số trong handoff là "khai báo", không phải sự
  thật, cho tới khi có bằng chứng đo lại trong phiên hiện tại.
- **Cấm khảo sát lại repo từ đầu** — kế hoạch, quyết định và trạng thái đã nằm trong
  handoff; khảo sát lại vừa tốn quota vừa sinh bản kế hoạch song song.

## §3 — MẪU PROMPT CHUẨN

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

Mọi prompt giao executor phải có đủ: `destination` · `CHAT_MODE` · `CHAT_TITLE` (với
Arena: dòng đầu tiên chính là title) · `ROLE` · `PROJECT` · `REPO` · `PR` ·
`EXACT_BASE_HEAD` · nhánh sẽ push · `TASK_ID` · `TASK_AUTHORITY` · mục tiêu · phạm vi
trong/ngoài · neo `file:line` · bất biến phải giữ · bằng chứng bắt buộc · tiêu chí
nghiệm thu cố định · điều cấm · stop condition · `REQUIRED_SKILLS` (path + SHA256 thật
từ `.p2p/portable/P2P-SKILL-PROJECTION.json`) · `P2P_LAW_PREFLIGHT` · `OE_GATE` ·
`HANDOFF_UPDATE=yes`.

Thiếu bất kỳ field nào ⇒ prompt chưa đủ chặt — viết lại TRƯỚC khi gửi, không gửi rồi vá.

## §5 — KHAI THÁC ARENA TỐI ĐA

- Chỉ giao việc có test deterministic. Không đặt acceptance cần browser.
- Một phiên một mục tiêu; nhồi đủ yêu cầu ngay prompt đầu; micro-fix dùng "keep working".
- Bắt buộc RED-before/GREEN-after; full suite so baseline cùng môi trường (`NEW=∅/GONE=∅`);
  không chạy được thì ghi `NOT_RUN`, cấm gọi PASS.
- Arena báo tên nhánh + SHA; Control Tower kiểm ancestry rồi mới cho fast-forward; Arena
  không merge.
- Sau mỗi phiên Arena: kiểm nhánh mồ côi (đã từng mất 1 commit vì push vào nhánh không
  ai biết — xem §9).
- Canary đầu phiên cho việc medium/high risk; Arena không tự chấm điểm.
- Cấm: đụng main, force-push, PR mới, đụng app `tienthanhlog`, production write, mở rộng
  scope, đổi schema ngoài phạm vi.

**VẬN HÀNH THEO CHAT (2026-10-20)** — mỗi chat Arena là một đơn vị công việc, không phải bộ nhớ:

- (a) Mỗi chat Arena = một nhánh session riêng, một mục tiêu hẹp; xong thì đóng chat.
- (b) Mất chat KHÔNG mất việc — chỉ an toàn khi đã commit + push + báo TÊN NHÁNH và SHA.
  Chat mất giữa chừng thì mở chat mới, tiếp tục từ đúng SHA đó, KHÔNG làm lại.
- (c) Prompt cho Arena luôn yêu cầu: "push nhánh session rồi báo TÊN NHÁNH + SHA".
- (d) Sau mỗi phiên: kiểm nhánh mồ côi (đối chiếu `branches?per_page=100`, §6).

## §6 — ĐƯỜNG ĐỌC RẺ CHO CONTROL TOWER (api.github.com)

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
- `GET /repos/7roger89-web/logistics-work-desk-arena/compare/{sha_cu}...{sha_moi}` →
  `ahead` / `identical` / `diverged`; dùng TRƯỚC khi cho fast-forward. `diverged` thì
  DỪNG, không force — kiểm lại diff PR và handoff.
- `GET /repos/7roger89-web/logistics-work-desk-arena/branches?per_page=100` → liệt kê
  nhánh thật trên remote, bắt nhánh mồ côi sau mỗi phiên.

Luật: mở trang PR đầy đủ (web UI) tối đa 1 lần/phiên; handoff mục 3 giữ gọn trong 1 màn
hình (chi tiết dài đẩy xuống mục 6).

## §7 — FAILOVER KHI CONTROL TOWER MẤT QUOTA

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

- Không bao giờ để kế hoạch chỉ nằm trong chat.
- Cuối mỗi phiên Control Tower: handoff mục 3 có `NEXT_ACTION` + `NEXT_PACKET`; packet
  phải dán được ngay.
- Sắp hết quota: viết packet trước, đọc thêm sau.
- Bằng chứng QA phải ở nơi Control Tower đọc được.
- Không ai tự nghiệm thu việc mình làm.

## §9 — BÀI HỌC ĐÃ TRẢ GIÁ

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

