## Quy trình bắt buộc
Mọi task đi theo docs/PROCESS.md. Năm bước, ba cổng. Chưa có trang mô tả ở
bước 1 thì dừng, hỏi lại, không tự đoán. Một phiên một ticket. Chưa qua cổng
CI thì chưa được coi là xong. Đọc docs/PROCESS.md trước khi bắt đầu.

## Đọc gì trước
Đọc `AGENTS.md`, `docs/PROCESS.md` và Luật Tối Thượng P2P hợp lệ trước khi
làm việc thực chất. Ưu tiên nguồn canonical đang truy cập được; nếu không,
dùng bản portable `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md` còn hiệu lực.
Không có nguồn luật hợp lệ thì dừng. Báo `LAW_CHECK` với nguồn đã thực đọc;
không dùng trí nhớ hoặc bản portable đã lỗi thời để thay luật.

## Luật nhánh
Một task một nhánh, tên task/<số-issue>-<mô-tả>. Nhánh quá 30 ngày chưa gộp
thì xoá. Gộp xong xoá ngay. Không đẩy thẳng main. Mục tiêu dưới 20 nhánh mở.

## Bằng chứng
Lời tự khai không tính. Phải có test đã chạy, ảnh chụp, log, hoặc số đo.
Test xanh chỉ chứng minh đúng cái test đó chạm tới. Kết luận cuối task chỉ
một trong ba: XONG / CHƯA XONG / HỎNG.

## Kiểm tra trước khi mở PR
Theo thứ tự, dừng ở việc nào hỏng: ruff check .; python scripts/check_router.py;
python -m pytest tests -q --continue-on-collection-errors.
tests/BASELINE_FAILED.txt là nợ cũ, chỉ chịu trách nhiệm lỗi MỚI. Sửa được
lỗi cũ thì xoá dòng đó khỏi baseline và ghi vào PR. Test cần Streamlit/Mongo
thật được skip theo thiết kế. Không dùng database app để test.

## Định nghĩa xong
Xem docs/DONE.md. Đúng 5 điều. Xong 5 điều là xong, không tự thêm.

## Quyền
Ma trận duy nhất: core/auth.py::ROLE_PERMISSIONS, 7 role. Chỉ 3 role tạo được
từ UI: admin, sale, support. accounting, operations, sales là tên cũ giữ
tương thích. Role lạ rơi về viewer.

## Cấm
Không deploy production khi chưa có lệnh Owner cho đúng task đó. Không chạm
logistics_db. Không in URI, khóa, mật khẩu. Không thêm thư viện khi thư viện
hiện có làm được. Không đổi stack.

## Skill
Skill có sẵn trong `.agents/skills/`: security-audit, frontend-code-review,
react-doctor, qa, debugging, p2p-uiux, scope-reality-check, p2p-karpathy.
Chọn tối đa 3 skill phù hợp cho mỗi task, không tải hết các skill.
Khi triển khai, sửa lỗi hoặc refactor code: đọc và áp dụng
`.agents/skills/p2p-karpathy/SKILL.md` trước khi sửa; kiểm SHA-256 trong
`.p2p/portable/P2P-SKILL-PROJECTION.json`. Skill này chiếm một trong ba suất.
Nếu xung đột kỹ năng bắt buộc hoặc yêu cầu bảo mật/quyền Owner, ưu tiên luật
và phạm vi task; ghi rõ lý do thay thế. Không ép skill code cho task chỉ viết
tài liệu hoặc nghiên cứu. Không đọc skill thay cho đọc Luật Tối Thượng.
Skill ngoài đã cài, gọi thẳng tên, KHÔNG thuộc danh sách P2P: grill-me,
diagnosing-bugs, tdd, code-review, developing-with-streamlit, webapp-testing.
Cài thêm phải báo Owner. Không cài gói lớn.

## Tài liệu
README.md là tài liệu cài DUY NHẤT. Kiến trúc: docs/ARCHITECTURE-PRINCIPLES.md.
Việc tiếp theo và lịch sử phiên: docs/NEXT.md. Quy trình: docs/PROCESS.md.
Các README_* ở gốc là hồ sơ lịch sử, không dùng để cài.

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
