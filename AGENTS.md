# AGENTS.md — Logistics Work Desk

## P2P Supreme Law bootstrap (mandatory)

Before substantive P2P-managed analysis, planning, prompt writing, implementation, review, testing, or merge decisions, the current actor must establish its own valid law source.

Use this operational order:

1. `CANONICAL_AUTHENTICATED` — use the canonical P2P notebook only when this same actor/session has already successfully reached `7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`.
2. `LOCAL_INSTALLED` — otherwise use a valid, not-known-stale installed projection under `.p2p/system` when present.
3. `LOCAL_PORTABLE` — in a repo-scoped remote clone, use `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md` directly when it carries `P2P_PORTABLE_LAW_PROJECTION=YES`, canonical provenance, and a valid source identity.
4. `INLINE_CAPSULE` — otherwise use only a fresh explicit `SUPREME_LAW_CAPSULE` from the current Control Tower handoff.
5. If none is valid, stop at `P2P_LAW_SOURCE=LAW_CONTEXT_BLOCKED`.

`TARGET_REPO_AUTH != CANONICAL_CROSS_REPO_REACHABILITY`. Authentication to this project does not prove that the private canonical P2P repository is readable. A repo-scoped executor with valid portable law must not issue a cross-repository `gh`/API request solely to manufacture a 404 before fallback. If canonical is already successfully reachable in that same session, canonical wins.

Never claim a law source was read when it was not. `TASK_BRANCH != LAW_AUTHORITY`. `TARGET_PROJECT != LAW_SOURCE`.

At task start report exactly one:
`P2P_LAW_SOURCE=CANONICAL_AUTHENTICATED|LOCAL_INSTALLED|LOCAL_PORTABLE|INLINE_CAPSULE|LAW_CONTEXT_BLOCKED`.
## Evidence-first verification (P2P)

For non-trivial implementation, repair, review, testing, or any correctness/readiness claim, apply `P2P_EVIDENCE_FIRST_VERIFICATION_V1`. When canonical cross-repository access is available, read:
`7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-EVIDENCE-FIRST-VERIFICATION.md`.

If that profile cannot be read, apply this minimum capsule:
- `AGENT_CLAIM_IS_NOT_EVIDENCE`: worker self-report is never acceptance authority.
- `TEST_PASS_PROVES_ONLY_CHALLENGED_BEHAVIOR`: a passing test/build/lint/coverage/static check proves only the boundary/property it actually exercised.
- Reuse existing execution lanes `FAST|STANDARD|STRICT|CRITICAL`; do not create a second risk classifier.
- Non-trivial changes carry recoverable intent, behavior/regression proof, relevant environment/risk proof, provenance, and a truthful `PROVEN|INCOMPLETE|FAILED` verdict using existing P2P evidence stores.
- `STRICT`/`CRITICAL` require an independent challenge appropriate to the changed surface. Targeted mutation, adversarial, negative, or property checks are tools, not rituals.
- UI/API/provider/deployment/migration claims require representative real-path evidence when practical; otherwise downgrade the claim to the strongest truthful unverified/incomplete state.
- Stop once bounded acceptance is proven; do not run broad mutation campaigns, extra reviewers, or full-suite ceremonies without decision value.

## Mandatory prompt serialization contract

Xem mục “Mandatory prompt serialization contract” trong managed P2P block bên dưới; không lặp thân luật top-level.

## NGUỒN SỰ THẬT & THỨ TỰ TIN (đọc trước khi tin bất kỳ số nào)
Khi hai nguồn mâu thuẫn, tin theo đúng thứ tự này, dừng ở nguồn đầu tiên có dữ liệu:
1. api.github.com/repos/7roger89-web/logistics-work-desk-arena/pulls/211 → state, head.sha, merged (MÁY ĐO — tin nhất)
2. docs/CONTROL-TOWER-HANDOFF.md MỤC 3 (TRẠNG THÁI SỐNG — chỉ file này giữ trạng thái)
3. Comment PR mới nhất (BẰNG CHỨNG, có timestamp)
4. MỤC 4 (bằng chứng, phải có nhãn ngày)
5. Body PR (KHAI BÁO — thường cũ, không tin nếu chưa đối chiếu)
6. MỤC 6 + docs/CONTROL-TOWER-ARCHIVE.md (LỊCH SỬ — số chỉ đúng tại thời điểm viết)
Luật: (a) mọi con số phải kèm NGÀY ĐO + SHA nguồn, thiếu ngày ⇒ đo lại; (b) file ngoài MỤC 3 chỉ TRỎ tới trạng thái, không chép lại; (c) PASS/FAIL/DONE phải kèm phạm vi + ngày + SHA; (d) link theo nhánh = trạng thái, link theo SHA = bằng chứng; (e) head.sha trong tài liệu khác api.github.com ⇒ tin API và ghi lại.

**STALE_KNOWN — chuỗi đã biết là cũ, ĐỪNG TIN** (ghi 2026-10-20, HEAD_AT_WRITE=`365ad6d`; chính bảng này là nhãn lịch sử cho các chuỗi bên trong):

| Chuỗi cũ | Đúng hiện nay | Vì sao còn |
|---|---|---|
| head trong body PR (mọi SHA cụ thể) | head thật — luôn đo api.github.com | body PATCH mỗi phiên, trễ 1 nhịp so với commit docs |
| [LỊCH SỬ @8aba473] BROWSER QA FAIL / repair task UI copy (body PR; chuỗi cũ `FIX=NOT_STARTED` không còn trong body) | FIX=DONE @afbc18d · BROWSER_MODE_COPY=PASS | body đã PATCH 2026-10-20 (gắn `[LỊCH SỬ]` @8aba473 + `FIX=DONE @afbc18d`) |
| "còn 40 failure" (MỤC 3 ĐANG CHỜ) | 37 failed (đo 2026-10-20) | 40 là số 2026-10-19 |
| BASELINE_FAILED='41' (ci.yml) | 37 cho nhánh tích hợp; 31 cho main | gắn ngày 2026-10-19 |
| FULL_SUITE=NOT_RUN (dòng docs-only) | đã đo 37/2110/44 | ghi trước khi đo |
| guide §7 → "bảng T1–T6 ở playbook §0.2" | §0.2 chưa có bảng đó | con trỏ sai |
| 61/2048 · 63/2047 · 37/2089 · 37/2100 · 37/2108 | 37/2110/44 | lịch sử MỤC 6 |

## Baseline hiện tại

- **Trạng thái sống của dự án nằm ở `docs/CONTROL-TOWER-HANDOFF.md`** — đọc TRƯỚC khi làm bất cứ việc gì; file được cập nhật cuối mỗi task và là sự thật mới nhất về đang ở đâu / còn gì / cần Owner gì.
- **Công việc hiện tại:** chuỗi LOGI-199 trên PR **#211** — head `arena/a3117943-logistics-work-desk-arena`, base `ct/logi199-journey-main-integration-20261017`.
- Chuỗi LOG-C13/C14/C15 (`log-c15-user-identity-rbac` @ `e518cae`) là **lịch sử** — ngữ cảnh xem `docs/LOG_C15_HANDOFF.md`; KHÔNG dùng làm baseline cho công việc hiện tại.
- KHÔNG deploy production; KHÔNG merge main cho đến khi Owner xác nhận.

## Quy ước quan trọng

- **Credential:** chỉ trong `.streamlit/secrets.toml` (gitignored). Không bao giờ in/hardcode URI/mật khẩu trong code.
- **App chạy trên máy Owner:** 2 instance production Streamlit (port 8501, 8510). Trước khi test UI, mở port khác (vd 9501), tắt sau khi xong.
- **Git credential helper:** `git config --global credential.helper manager` (helper cũ chỉ đường dẫn exe trực tiếp bị lỗi word-split trên máy này).
- **Database:** `logistics_workdesk_logc14` hiện là DB app đang dùng; `logistics_db` tồn tại trên cluster chưa dùng; DB test tạo riêng với prefix `logistics_workdesk_logc15+` và TỰ DROP sau khi chạy.
- **Quyền Atlas user hiện tại** chỉ đọc/ghi trên `logistics_workdesk_logc14` — không `dropUser`, không `listIndexes`.
- **Production untouched:** không drop/tạo database app, không thay đổi instance production.

## Testing

- Full suite (lệnh CI): `python -m pytest tests -q --ignore=tests/test_partner_reconciliation_desk_write_oracle.py` → số thật gần nhất: **37 failed / 2110 passed / 44 skipped / 0 errors** (đo 2026-10-20 tại SHA `8f4d15ff581c1fa3daf12626ae5d02d7b734d649` & `a4c49a0e90694bee48da175980f875eda02f489d`, pytest 9.1.1 + node 22–24 + `npm --prefix component ci`; mốc lịch sử 2026-10-20 trước `@afbc18d` tại `8aba473` là 37 / 2109 / 44 / 0, bản ghi lịch sử 2026-10-19 là 37 / ~2100 / 44 / 2 — chênh trong biên flaky ±1 và khác phiên bản pytest). Kỳ vọng cũ "200 passed, 28 skipped" là của chuỗi LOG-C15 đã kết thúc — không còn đúng, đừng dùng.
- Cách đọc đúng: tập failure = **31 lỗi có sẵn trên main** + **6 xung đột test-main × code-#210 còn lại** (tên đã biết: `test_journey_super_goal_186`, họ `test_journey_visual_fidelity_190` ×4, `test_visual_shipment_workspace::test_same_attachment_id_...`; 4 ca `test_journey_fresh_parity_188` đã sửa ở `c5e904d` nên còn 37 thay vì 41 — 41 là số đo 2026-10-19, đã cũ, xem bảng STALE_KNOWN). **ĐỎ = hồi quy so với baseline**, không phải "phải 0 lỗi": so tập FAILED/ERROR với baseline cùng môi trường — chấp nhận khi `NEW=∅` và `GONE=∅`.
- Baseline đã mã hoá trong `.github/workflows/ci.yml` (`BASELINE_FAILED` kèm phân rã thành phần trong comment) — CI đỏ khi vượt baseline đó.
- Tests runtime cần Streamlit/Mongo thực được skip theo thiết kế — không cố sửa chúng thành chạy được.
- Số flaky ±1 skip/fail theo môi trường; vượt 1 test thì re-run xác nhận trước khi gọi hồi quy.
- Auth/RBAC: `tests/test_logc15_auth_rbac.py` (pure, mock streamlit).
- DB users: `scripts/logc15_db_users_test.py` + runner — chạy trên DB test riêng, tự dọn.

## Quyền (ma trận duy nhất: core/auth.py ROLE_PERMISSIONS)

admin=`*`, sale=sales_write + commercial_write + shipment_create + ops + knowledge + customers + tracking + tariff + commercial_view..., support=commercial_view + ops + finance_view + customers + tracking..., viewer=fallback read-only.

## Bootstrap

Chưa có user → app render form tạo Admin đầu tiên (không default credential). CLI: `python scripts/setup_first_user.py` (tương tác, mật khẩu không qua args).

## Native long-running goal bridge (P2P)

Xem mục “Native long-running goal bridge” trong managed P2P block bên dưới; heading này chỉ dẫn đường.

## Native `/goal` auto-activation (P2P)

Quy tắc auto-activation nằm trong mục “Native long-running goal bridge” của managed P2P block bên dưới; heading này chỉ dẫn đường.

## Prompt authoring discipline (P2P)

`PROMPT_AUTHORING_DISCIPLINE_V1` applies only when the active task writes, improves, revises, or delegates a prompt. Reuse the existing P2P task contract, destination, durable state, evidence, Owner Gates, and stop conditions. This is not a second prompt framework.

- Internally classify supplied material as `READY_PROMPT`, `PARTIAL_DRAFT`, `CLEAR_SIMPLE_REQUEST`, or `AMBIGUOUS_HIGH_IMPACT`; narrate the classification only when useful.
- Preserve known task/output/constraints for ready prompts; fill only material gaps in partial drafts; compose clear simple requests immediately with the smallest reasonable assumptions; ask questions for ambiguous/high-impact requests only when answers can materially change correctness, authority, acceptance, risk, or destination execution.
- Never re-ask facts already explicit in the Owner request, durable project state, or active task contract. Group genuinely blocking questions compactly, normally 2–4 at a time. After one useful clarification round, state reasonable assumptions and proceed for non-blocking gaps instead of creating an interview loop.
- Resolve the destination/model/executor from the Owner request and fresh durable routing state when already known. Ask only when the destination is truly unknown and materially changes execution.
- Adapt structure and transport to verified/current destination capabilities or authoritative instructions. Do not hard-code model-specific prompting stereotypes as law; fresh capability evidence outranks stale prompting folklore.
- Keep prompt complexity proportional to task complexity. Simple task -> concise executable prompt. Multi-part/high-risk task -> add only structure that materially improves acceptance or recovery. No decorative roles, duplicated constraints, or checklist inflation.
- Never request private chain-of-thought, hidden scratchpad, or step-by-step internal reasoning. Request concise rationale, assumptions, evidence, calculations, verification results, or an auditable action summary when needed.
- When revising an existing prompt, edit that prompt instead of restarting requirements collection. Preserve unaffected constraints and return the complete revised prompt unless the Owner explicitly asks for only a diff or fragment.
- Use the output surface that fits the destination and workflow; do not force Markdown, files, XML, JSON, tables, or another wrapper unless the task contract, destination capability, machine parsing, or copy/paste workflow materially benefits.
- Stop when the prompt is executable and aligned to outcome, destination, scope, acceptance, evidence, authority boundaries, and stop condition. Do not append optional prompt theory, examples, or future-proofing unless requested.

### Prompt-writer skill routing (chi tiết không có trong managed block)

- `PROMPT_WRITER_SKILL_ROUTING_V1=YES`: before any P2P-generated delegated repository-work prompt, the prompt writer must inspect the target repo's supported skill metadata/projection and select the smallest relevant set (max 3). Reuse the existing Skill Consumption Wire when available; do not create a second router.
- Explicit Owner `@skill` / `$skill` / `REQUIRED_SKILLS` wins when valid. No relevant match => serialize `SKILL_CHECK=NO_MATCH` and continue normally; unknown/missing/ambiguous/hash-mismatched required skill => fail closed before delegation.
- For every selected skill, bind exact repo-local `SKILL.md` path + SHA-256 into the handoff, require executor read/apply before substantive work, and require one exact `p2p-skill-consumption-receipt/1`. A downstream `@skill` token alone is not consumption evidence.
- Do not preload every skill or add another router, registry, vector DB, daemon, or background skill scanner for prompt-writer routing.

## Control Tower handoff — bắt buộc mọi task

Repo này có một file bàn giao ca cho Control Tower: `docs/CONTROL-TOWER-HANDOFF.md`.

Cuối MỌI task có thay đổi file, TRƯỚC khi báo cáo hoàn tất:

1. Cập nhật `docs/CONTROL-TOWER-HANDOFF.md`:
   - Mục 6 NHẬT KÝ PHIÊN: thêm mục mới LÊN TRÊN — ngày, commit SHA, đã làm, còn lại, cần Owner.
   - Mục 3 TRẠNG THÁI: cập nhật cho khớp sự thật.
   - MỤC 3 phải ≤ ~1 màn hình (CURRENT + ĐANG CHỜ + NEXT_ACTION/NEXT_PACKET). Mốc lịch sử đẩy xuống MỤC 6; khi MỤC 6 vượt ~10 mục thì chuyển các mục cũ nhất NGUYÊN VĂN sang docs/CONTROL-TOWER-ARCHIVE.md (lịch sử, không phải luật). MỤC 4 chỉ giữ bằng chứng của các mốc còn sống.
   - Mục 1, 2, 5: GIỮ NGUYÊN, chỉ đổi khi prompt nói rõ.
   - File chưa có thì tạo đúng cấu trúc mục 1→6.
2. Commit cùng branch.
3. Phát receipt trong báo cáo:
   `HANDOFF_UPDATE=YES | PATH=docs/CONTROL-TOWER-HANDOFF.md | COMMIT=<sha>`
   hoặc `HANDOFF_UPDATE=SKIPPED | REASON=<lý do>` nếu task chỉ đọc.

Không cập nhật handoff = task CHƯA hoàn tất. Task chỉ đọc thì không bắt buộc.

## Hai vòng phát triển — không trộn

Nguồn: P2P-DEVELOPMENT-CHARTER §5A (bản rút gọn cho dự án này).

PRODUCT FAST LOOP: Business/Owner Outcome → Minimum Product Truth → Product/UX Synthesis
→ Interactive Prototype → Owner Review → Visual/Product Reference Lock → Real Implementation
→ Targeted Tests → Human Outcome Test.

ASSURANCE / RELEASE LOOP: Risk-Proportional Hardening → Independent Verification → Release.

Trạng thái đi theo bậc, không nhảy:
IDEA → PROTOTYPE → OWNER TRUTH → IMPLEMENTATION → SYSTEM TRUTH → VERIFICATION → RELEASE TRUTH.

Luật:
- "Xong kỹ thuật" KHÁC "được phát hành". Goal PASS, verify candidate, sẵn sàng phát hành,
  và phát hành là bốn trạng thái riêng.
- KHÔNG kéo một việc qua vòng assurance khi vòng product chưa xong.
- Gia cố theo rủi ro, dùng đúng lane đã có: FAST | STANDARD | STRICT | CRITICAL.
  Rủi ro thấp → kiểm hẹp sát chỗ đổi. Việc thường → bằng chứng acceptance/regression rõ.
  Việc chặt → thêm kiểm độc lập khi có giá trị quyết định.
  Việc nguy (auth, migration, xoá dữ liệu, phát hành) → verifier độc lập + bằng chứng
  đường thật + Owner duyệt.
- Chạy một agent tử tế từ đầu tới cuối trước; chỉ thêm verifier khi rủi ro đòi.
- Tiêu chí người: Owner phải nhận ra việc cần xử lý trong 30 giây.

## Thang chống over-engineering

Nguồn: P2P-DEVELOPMENT-CHARTER §5A.

Trước khi thêm bất cứ gì, thử theo ĐÚNG thứ tự này và DỪNG ở bậc đầu tiên giải quyết được:
1. Không code — trả lời hoặc ra quyết định
2. Đổi cấu hình
3. Sửa quy trình
4. Sửa hẹp đúng chỗ
5. Dùng helper/component đã có
6. Thay skill/tool sẵn có
7. Chỉ tạo abstraction mới khi chứng minh được là bắt buộc về mặt cơ học

Câu hỏi bắt buộc kèm theo: `Không bị over engineering chứ?`

## Owner Gate — chỉ hỏi Owner những việc này

Nguồn: P2P-DEVELOPMENT-CHARTER §4.

Chỉ hỏi Owner khi thuộc một trong các loại: ý định sản phẩm/kinh doanh · dữ liệu nghiệp vụ
thật · hành động xoá dữ liệu · cấp quyền secret/credential · chi tiêu đáng kể · deploy
production · phát hành cần duyệt · mơ hồ không gỡ được bằng kỹ thuật và hậu quả lớn.

KHÔNG hỏi Owner chọn cơ chế kỹ thuật mà tự xác định được từ bằng chứng.

## Bất biến then chốt

Nguồn: P2P-DEVELOPMENT-CHARTER §3.

- OUTPUT_NOT_EVIDENCE — output của executor là ĐỀ XUẤT cho tới khi được kiểm với bằng chứng.
- INVENTORY_NOT_BEHAVIOR — file/class/registry tồn tại KHÔNG phải bằng chứng nó hoạt động.
- UNKNOWN_IS_NOT_SUPPORTED — cái không kiểm được thì giữ UNKNOWN, không coi là đã hỗ trợ.
- GOAL_PASS_NOT_PROMOTION — PASS mục tiêu ≠ đã phát hành.
- PROJECT_STATE_NOT_CHAT_HISTORY — phiên mới hồi phục từ trạng thái dự án, không từ chat.
- DETERMINISTIC_FIRST — kiểm được bằng máy thì kiểm trước, đừng suy luận.

## Bằng chứng trước khi kết luận

Nguồn: bài học từ các phiên Arena — có phiên kết luận "KHÔNG phải lỗi" trên cây thiếu file.

Trước khi kết luận bất cứ điều gì về code:
- Đọc file THẬT ở ĐÚNG HEAD. Không suy từ trí nhớ, không suy từ mô tả.
- Trích `file:line` làm căn cứ.

Kết luận "KHÔNG phải lỗi" PHẢI kèm đoạn code thật làm căn cứ, không suy đoán.

Nếu file không tồn tại ở cây đang xét, kiểm tra lại ở HEAD của nhánh/PR đích trước khi
kết luận — file có thể chỉ tồn tại trên nhánh đó.

Không có bằng chứng thì ghi `[KHÔNG CÓ BẰNG CHỨNG]`, đừng kết luận.

## Khảo sát bắt buộc trước khi sửa (TASK 0)

Mọi prompt có sửa file PHẢI mở đầu bằng TASK 0, làm TRƯỚC mọi thay đổi:

- Nêu branch + HEAD SHA đang làm việc.
- Với TỪNG file sẽ đụng: nó CÓ tồn tại ở HEAD đó không? Trích NGUYÊN đoạn dòng sẽ sửa.
- Nêu sẽ đổi gì ở mỗi file.
- Nêu chỗ CHƯA CHẮC → đánh dấu `[CHƯA CHẮC]`.
- Nếu file KHÔNG tồn tại ở cây hiện tại: kiểm ở HEAD nhánh/PR đích rồi nói rõ.
- Nếu phát hiện prompt của Control Tower SAI: NÓI RA, đừng im lặng làm theo.
- Receipt: `PREFLIGHT_READ=PASS | HEAD=<sha> | FILES=<n> | MISSING=<n>`

## Tự kiểm trước khi báo xong (TASK CUỐI)

Mọi prompt có sửa file PHẢI kết thúc bằng TASK CUỐI, làm TRƯỚC khi báo hoàn tất:

- Đọc lại diff của chính mình.
- Với TỪNG tiêu chí acceptance: trích DÒNG CODE THẬT chứng minh đã đạt.
- Tick checklist. Tiêu chí nào không đạt thì KHÔNG tick, ghi rõ lý do.
- Receipt: `SELF_VERIFY=PASS | ACCEPTANCE=<đạt>/<tổng> | CHECKLIST=<tick>/<tổng>`

Không có SELF_VERIFY tick đủ = task CHƯA hoàn tất.

## Xoay phiên Arena

Mở CHAT MỚI khi: PR vừa merge/đóng · xong một mục tiêu · Arena bắt đầu lặp lại ·
phải giải thích lại điều đã nói. Chat dài làm chất lượng giảm.

Một prompt chỉ nên chứa MỘT loại việc. Việc khác loại thì tách prompt.

## Bài học tích lũy

Mỗi lần một phiên làm sai và được Control Tower chỉ ra, thêm MỘT DÒNG luật vào mục này.
Giữ mỗi dòng thật ngắn. Nếu dài quá thì để chi tiết ở playbook §9.

- Push vào nhánh không ai theo dõi thì coi như mất việc — sau mỗi phiên phải kiểm nhánh mồ côi (`GET /repos/.../branches?per_page=100`).
- Sửa source React mà không rebuild `component/dist` trong CÙNG commit → QA nhìn bundle cũ, mất một vòng "fix" ma.
- Bằng chứng chỉ nằm ở ổ đĩa máy trạm thì Control Tower coi như KHÔNG CÓ — phải đưa lên comment PR hoặc `docs/`.
- Prompt giao việc thiếu `P2P_LAW_PREFLIGHT`/`OE_GATE` → executor lệch chuẩn, mất cả phiên làm lại.
- Hướng dẫn stale (số test cũ, baseline chuỗi cũ) làm người đọc sau hiểu sai trạng thái — phát hiện là sửa ngay.
- **Đồng bộ head PR là việc của phiên Arena (2026-10-20)**: base commit LUÔN từ head PR (không từ main); push nhánh session; rồi PATCH ref arena/a3117943-... qua API force=false — PATCH ref KHÔNG phải "push nhánh khác"; nếu 403 mới báo FF_BLOCKED.
- Mode của lô KHÔNG đọc từ `s.mode` (có thể là chặng đầu, vd Truck); Journey dùng `executionProfile.mode` — đối chiếu trước khi kết luận câu chữ.

Chi tiết + bối cảnh: docs/CONTROL-TOWER-PLAYBOOK.md §9. Mỗi dòng ở đây phải ngắn.
- Mọi LEARNING_RECONCILIATION=CANDIDATE phải hạ xuống đây đúng 1 dòng trước khi kết phiên — không để mắc trong nhật ký.
- Trước khi đính log/ZIP lên PR công khai: quét secret và redaction TRƯỚC, vì attachment GitHub không xoá được về sau.

## Definition of Done tối thiểu cho task đụng UI

1. Đổi source React ⇒ BẮT BUỘC rebuild `component/dist` trong CÙNG commit + kiểm marker parity source↔dist; bundle ship phải khớp source của đúng commit đó.
2. Browser/visual QA phải chạy trên bundle của ĐÚNG commit được kiểm, và phải có ít nhất 1 ca đúng vai trò Sale và 1 ca Support (không chỉ admin).
3. Bằng chứng QA/browser phải nằm ở nơi Control Tower đọc được (comment PR hoặc file trong `docs/`), không chỉ ổ đĩa máy trạm.
4. Task CHỈ ĐỌC mà có kết quả nghiệm thu (QA/browser/audit) thì Control Tower phải ghi 1 dòng vào `docs/CONTROL-TOWER-HANDOFF.md` mục 3/4 (hoặc ghi rõ lý do không).

Cách vận hành Control Tower + mẫu prompt + thang failover: `docs/CONTROL-TOWER-PLAYBOOK.md`.

<!-- BEGIN P2P FRONTEND CAPABILITY PACK -->
## P2P project-local frontend capability pack

This repository carries a project-local, read-only-at-discovery projection of the curated P2P frontend capability pack from:

`7roger89-web/P2P-upgrade-github-1@562764f1cdf5b672a4870d8e8311470861a2f76e`

For frontend work:

1. Concrete UI/UX outcome or review -> read `.agents/skills/p2p-uiux/SKILL.md` first.
2. Frontend implementation/change -> read `.agents/skills/frontend-development/SKILL.md`; it is the thin hub and must load only relevant specialist skills.
3. Creative visual direction -> `.agents/skills/frontend-design/SKILL.md`.
4. React engineering/performance -> `.agents/skills/react-best-practices/SKILL.md`.
5. Component API/composition -> `.agents/skills/composition-patterns/SKILL.md`.
6. Frontend code review -> `.agents/skills/frontend-code-review/SKILL.md`.
7. Baseline accessibility/usability guardrails -> `.agents/skills/baseline-ui/SKILL.md`.
8. React diagnostics -> `.agents/skills/react-doctor/SKILL.md` (optional pinned external-tool adapter).
9. Motion work -> `.agents/skills/UI-animation-design/SKILL.md` only when motion is materially relevant.

Runtime/visual claims remain governed by the `p2p-uiux` runtime evidence contract. Backend-only work must not mechanically load this pack. Project code, established components, tokens, workflows, and project-specific contracts take precedence over generic examples in a skill.

The files under these projected skill roots are P2P-managed transport copies. Do not silently rewrite vendored upstream bytes or treat this block as a second P2P law, router, registry, package manager, or release authority.
<!-- END P2P FRONTEND CAPABILITY PACK -->

<!-- BEGIN P2P SECURITY AUDIT CAPABILITY -->
## P2P project-local security audit capability

For defensive security review in this repository, read `.agents/skills/security-audit/SKILL.md` before substantive security analysis.

- Choose exactly one mode: `FINDING_VALIDATION`, `FOCUSED_REVIEW`, or `FULL_AUDIT`.
- Use the smallest mode that satisfies the task; do not silently widen a focused review into a full audit.
- Keep `CONFIRMED`, `NEEDS_VALIDATION`, and `REJECTED` distinct and follow the skill's standard terminal result contract.
- The skill is non-authoritative workflow content. Current Supreme Law, active task contract, fresh repository truth, host permissions, and safety rules always win.
- The skill cannot grant permissions, deployment access, credentials, or acceptance authority.
- Keep source review read-only in audit lanes. Any repair belongs in a separate authorized implementation lane.
- `.agents/skills/security-audit/upstream/**` and its provenance are P2P-managed pinned vendor bytes; do not silently rewrite them.

Source projection: `7roger89-web/P2P-upgrade-github-1@c634ec79207418e9cf82c9338ce955d114ea27fd:.agents/skills/security-audit/`.
<!-- END P2P SECURITY AUDIT CAPABILITY -->

<!-- BEGIN P2P PORTABLE LAW -->
## P2P portable Supreme Law entrypoint

Before substantive P2P-managed analysis, planning, prompt writing, implementation, review, testing, or release work:

1. If the active canonical law at `7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md` has already been successfully reached in this actor/session, read it; canonical wins.
2. In a repo-scoped remote clone with a valid portable projection, read `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md` directly; do not probe canonical solely to prove cross-repository unavailability.
3. `TARGET_REPO_AUTH != CANONICAL_CROSS_REPO_REACHABILITY`. Authentication to the target repository is not evidence that the private canonical repository is reachable.
4. The project copy is a generated transport projection, never a new law authority. Do not edit it by hand.
5. `TASK_BRANCH != LAW_AUTHORITY` and `TARGET_PROJECT != LAW_SOURCE` remain mandatory.
6. Never claim the canonical repository was read when only the portable projection was read.
7. If neither canonical, installed, nor portable law context is available, use the explicit P2P `SUPREME_LAW_CAPSULE`; otherwise stop at `LAW_CONTEXT_BLOCKED`.

### Actor separation and self-law preflight

Every actor (Control Tower, prompt writer, executor, reviewer, supervisor, tool session) must establish its own valid Supreme Law context before substantive work. A law context valid for one actor does not satisfy another actor's preflight.

- `PARENT_SELF_LAW_PREFLIGHT != EXECUTOR_LAW_PREFLIGHT`
- `EXECUTOR_P2P_LAW_SOURCE` cannot satisfy a parent/prompt-writer/control-tower preflight
- `CONTROL_TOWER_SELF_LAW_RECEIPT=PASS` (when serialized by Control Tower) proves only the parent Control Tower's own preflight; it never proves executor preflight and never substitutes for `P2P_LAW_PREFLIGHT`
- No actor may fake, infer, or copy another actor's receipt/source. Only an actually performed read counts
- If no valid law source can be established for the current actor, stop at `LAW_CONTEXT_BLOCKED`
- Every actor must visibly emit its own self-read receipt before first substantive work:
  `LAW_CHECK=PASS | SOURCE=<actual source> | SOURCE_SHA256=<canonical source content sha256>`
  or: `LAW_CHECK=BLOCKED | REASON=<reason>`
- A portable PASS must bind to the recorded `SOURCE_CONTENT_SHA256` from `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`. A stale portable copy cannot produce PASS

### Remote repo-scoped handoff freshness

- Before delegating to a repo-scoped remote executor that may not reach canonical P2P, the parent Control Tower/prompt writer must fresh-compare this projection's source identity with reachable canonical law.
- If this projection is stale or missing and an authorized repository write path is available, refresh the generated portable notebook and managed AGENTS block before handoff.
- If refresh cannot be performed safely, mark the portable projection stale/missing and hand off a fresh SUPREME_LAW_CAPSULE; the executor must not rely on a known-stale portable copy.
- An authenticated GitHub connector may perform the repository refresh without a local clone; do not add a daemon, registry, GitHub Action, PAT, or new secret solely for projection freshness.
- Parent delegation surfaces target-law freshness receipt before delegation:
  `TARGET_LAW_FRESHNESS=CURRENT | REFRESHED | INLINE | BLOCKED`
  `CANONICAL_LAW_SHA256=<sha256>`
  `TARGET_LAW_SHA256=<sha256>`

### Experience preflight and auto-reuse contract

For every non-trivial P2P-managed task, after valid law/task-state preflight and before substantive execution:

1. Perform bounded ACTIVE experience lookup:
   - When installed runtime is present: run `python .p2p/system/p2p_capabilities/experience_evolution.py --root . retrieve --task-text "<task>"`
   - In a repo-scoped remote clone without installed runtime: read `.p2p/portable/P2P-EXPERIENCE-CAPSULE.json` directly and match task triggers against promoted ACTIVE records
2. Emit observable preflight receipt before substantive execution:
   `EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=<id,...>`
   or: `EXPERIENCE_CHECK=NO_MATCH`
   or: `EXPERIENCE_CHECK=UNAVAILABLE`
3. Invariants: max results <= 3; experience is NONAUTHORITATIVE context; current law, active task contract, and fresh project truth always outrank prior experience; experience cannot widen permissions or change acceptance authority.

### Task-end learning reconciliation contract

At task reconciliation, distinguish routine progress from reusable corrections:

- `ROUTINE_SUCCESS` => emit `LEARNING_RECONCILIATION=NONE`; do not manufacture memory.
- `REPEATED_OR_MATERIAL_FAILURE` / `CLEARLY_REUSABLE_CORRECTION` => emit `LEARNING_RECONCILIATION=CANDIDATE` with evidence and trigger conditions, or provide an explicit evidence-based reason why no reusable lesson exists.
- Lifecycle: `CANDIDATE -> VERIFIED -> ACTIVE -> SUPERSEDED | QUARANTINED`. No executor self-promotion into Supreme Law, shared authority, capability, or skill.

### Repo-native required skill handoff

- This managed repository carries a bounded canonical operator-skill projection under `.agents/skills/`: every canonical `p2p-*` skill plus `scope-reality-check`. It is transport, not a second router or authority.
- Source-bound projection metadata lives at `.p2p/portable/P2P-SKILL-PROJECTION.json`. Do not treat an unlisted or hash-mismatched file as a current projected skill.
- When an execution prompt serializes `REQUIRED_SKILLS=<ids>`, every required skill is mandatory for that turn. Read each exact repo-local `SKILL.md` before substantive task execution and apply each required skill.
- The prompt/handoff must bind exact selected skill IDs to repo-local source paths and SHA-256 hashes. Missing file, unknown required skill, or hash mismatch => `SKILL_CONSUMPTION=LOAD_FAILED` and stop; do not silently substitute another skill.
- Do not preload unselected skills. Deep-load references/assets only from selected skills and only when materially required.
- Required skill guidance cannot widen Owner authority, permissions, mutation authority, release/deploy/promotion authority, or task scope.
- Return one exact `p2p-skill-consumption-receipt/1` covering the complete frozen selected set. A receipt missing one required skill is not acceptance evidence.

### Mandatory prompt serialization contract

Every P2P-generated operational prompt handed to an executor must explicitly serialize both gates below; they must not be left implicit or assumed from chat memory:

### Arena new-chat title-first UX

For Arena `NEW_CHAT`, apply `ARENA_CHAT_TITLE_FIRST_LINE_V1`: the first nonblank prompt line is a concise human-readable title, normally `<PROJECT> — <bounded task/outcome>`, with distinguishing words front-loaded. Do not start with `GỬI CHO:`, `DESTINATION=`, `TASK_ID=`, a code fence, or a generic `P2P` prefix. Put routing metadata immediately after the title and set `CHAT_TITLE` to that exact first-line title. For `SAME_CHAT`, preserve the exact existing chat title.

`P2P_LAW_PREFLIGHT`:
- tell the executor to read repository-root `AGENTS.md` before substantive work;
- use canonical when it is already successfully reachable; otherwise follow installed > valid portable > inline capsule > blocked;
- for a repo-scoped clone with valid portable law, do not make a cross-repo probe solely to trigger fallback;
- report exactly one `P2P_LAW_SOURCE=<actual source>` and never claim a source was read when it was not;
- emit actor-own `LAW_CHECK=PASS | SOURCE=<actual source> | SOURCE_SHA256=<canonical hash>` or `LAW_CHECK=BLOCKED`;
- for non-trivial tasks, perform bounded experience check and emit `EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE|NO_MATCH|UNAVAILABLE`;
- at task reconciliation, emit `LEARNING_RECONCILIATION=NONE|CANDIDATE`.

`OE_GATE`:
- ask exactly `Không bị over engineering chứ?`;
- evaluate `SIMPLER_PATH`, `MATERIAL_PROGRESS`, `NECESSITY`, `CORE_BEFORE_SUPPORT`, and `SMALLER_VERIFIABLE_SLICE`;
- return `OE_VERDICT=DO_IT|SKIP_IT|DEFER_UNTIL_NEEDED` with one concrete reason;
- interpret directionally: SIMPLER_PATH=YES or SMALLER_VERIFIABLE_SLICE=YES means choose the simpler/smaller valid path; MATERIAL_PROGRESS=NO, NECESSITY=NO, or CORE_BEFORE_SUPPORT=NO means reduce/remove/defer; do not treat every negative answer as failure or return a ceremonial PASS.

### Native long-running goal bridge

For a clear long-running task on a host that supports native `/goal`, use native `/goal` only as a session continuation primitive; canonical P2P GoalPlan/TaskPlan, task state, evidence, and verifier remain authoritative.

- Prefer `.p2p/system/p2p_capabilities/native_goal_bridge.py` when an installed P2P runtime is present.
- After durable GoalPlan/TaskPlan exists and before the first substantive execution turn for that goal, run `.p2p/system/p2p_capabilities/native_goal_activation.py` when installed and use its decision automatically; do not ask the Owner whether `/goal` should be used.
- `ACTIVATE_NATIVE_GOAL` means invoke the returned host-native command once unless the same goal is already active in the current host session. `NORMAL_P2P_PATH` means continue normally. Helper `BLOCKED` means fail closed on the state/control-plane issue; never synthesize a goal condition.
- Auto-activation is intentionally narrow: Goal status must be `APPROVED` or `IN_PROGRESS`, TaskPlan lifecycle must be `ACTIVE`, the canonical plan must contain at least two tasks, and at least one task must remain non-terminal. If the helper is absent but authoritative durable state is readable, apply exactly this same rule directly; do not invent another detector or state machine.
- Choose `claude_code` or `codex_cli` from the current executor identity, never by asking the Owner. Claude Code may be identified from stable in-session markers; do not treat `CODEX_HOME` alone as proof of a Codex session.
- If installed runtime is absent in a fresh clone, derive the `/goal` completion condition directly from the active P2P goal/task contract. Do not create a second roadmap, state machine, memory authority, router, ledger, daemon, or scheduler.
- Do not conflate host semantics: only claim automatic continuation/evaluator behavior that is documented or directly verified for that host. In particular, do not assume Codex CLI has Claude Code's evaluator semantics.
- Recovery remains failure-class adaptive. Never introduce a fixed retry-count hard stop such as `three strikes => BLOCKED`.
- Before completion, compare against the original baseline across the complete worktree: committed-after-baseline, staged, unstaged, deleted tracked, and untracked files. Prefer `.p2p/system/p2p_capabilities/worktree_evidence.py` when installed; otherwise use equivalent read-only Git inspection.
- Before claiming done, replay the original task contract and re-check acceptance requirements/evidence. Host-native `/goal` evaluation and executor self-report are never P2P acceptance authority.
- If the host has no native `/goal`, continue with the normal P2P execution path; do not add a substitute control plane just to imitate `/goal`.

This serialization requirement applies to NEW_CHAT and SAME_CHAT execution prompts, including Arena, Codex, Manus, reviewers, supervisors, and other delegated executors. It does not require repeating the whole law body in every prompt.

<!-- END P2P PORTABLE LAW -->
