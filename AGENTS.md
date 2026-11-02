# AGENTS.md — Logistics Work Desk

## Đọc gì trước

Đọc hết file này là đủ để bắt đầu. Có `.p2p/portable/` thì đọc thêm
`P2P-OPERATIONS-NOTEBOOK.md` trong đó; thiếu không được dừng.
In `LAW_SOURCE=<file|NONE>` theo file thực sự đã đọc, hoặc `NONE` khi không có.
Áp dụng hướng dẫn ngắn này cho giao diện và tài liệu; giữ nghi thức P2P cho tiền,
chứng từ và danh tính database theo `docs/PROCESS.md`.

## Luật nhánh

Một task một nhánh: `task/<số-issue>-<mô-tả>`. Không đẩy thẳng `main`.
Gộp xong xoá nhánh ngay; nhánh quá 30 ngày chưa gộp thì xoá.
Giữ mục tiêu dưới 20 nhánh mở. Đây là luật cho việc mới, không phải lệnh xoá nhánh hàng loạt.

## Bằng chứng

Lời tự khai không tính. Đưa test đã chạy, ảnh chụp, log hoặc số đo có thể kiểm tra.
Kết luận cuối chỉ chọn một: `XONG` / `CHƯA XONG` / `HỎNG`.

## Kiểm tra trước khi mở PR

Chạy `ruff check .`, `python scripts/check_router.py`, rồi pytest theo README mục 8.
`tests/BASELINE_FAILED.txt` là nợ cũ; chỉ chịu trách nhiệm lỗi mới trong phạm vi task.
Sửa được lỗi cũ thì xoá dòng đó khỏi baseline. Không cập nhật baseline để che lỗi mới.

## Định nghĩa xong

Dùng đúng 5 điều trong [docs/DONE.md](docs/DONE.md). Không tự thêm điều kiện.
Việc ngoài phạm vi đưa sang issue riêng; không kéo dài task đang làm.

## Quyền

Ma trận duy nhất: `core/auth.py::ROLE_PERMISSIONS`. Có 7 role: `admin`, `sale`,
`support`, `accounting`, `operations`, `sales`, `viewer`. Chỉ 3 role tạo/gán được
qua UI: `admin`, `sale`, `support` (`core/users.py::SUPPORTED_ROLES`).
Role lạ rơi về `viewer`; không dựng ma trận quyền thứ hai.

## Cấm

Không deploy production khi chưa có lệnh Owner; không chạm `logistics_db`.
Không in URI, khoá hoặc mật khẩu. Không thêm thư viện khi thư viện hiện có làm được.
Không đổi stack.

## Skill

Gọi thẳng tên skill có sẵn trong `.agents/skills/`: `security-audit`,
`frontend-code-review`, `react-doctor`, `qa`, `debugging`, `p2p-uiux`,
`scope-reality-check`.

Các skill khác đã có trong repo: `baseline-ui`, `composition-patterns`,
`frontend-design`, `frontend-development`, `react-best-practices`,
`UI-animation-design`, `mcp-management`. Skill nghiệp vụ có tại
`skills/logistics/`: `business_context`, `customer_intake`, `payment_scenario`,
`quote_builder`, `sales_enablement`.

Skill ngoài đã cài trong môi trường executor như `coder`, `supervisor`,
`imagegen`, `docx`, `pdf`, `xlsx` được gọi thẳng tên khi có trong danh sách
skill của phiên; chúng không thuộc danh sách P2P và không phải phụ thuộc bắt buộc của repo.
Chỉ đọc skill cần cho việc đang làm. Cài thêm phải báo Owner. Không cài gói lớn.

## Tài liệu

`README.md` là tài liệu cài DUY NHẤT. Kiến trúc ở
`docs/ARCHITECTURE-PRINCIPLES.md`; việc tiếp theo ở `docs/NEXT.md`.
Các `README_*` ở gốc là hồ sơ lịch sử, không dùng làm hướng dẫn cài.

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
