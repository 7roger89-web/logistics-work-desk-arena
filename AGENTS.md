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

Every P2P-generated operational prompt handed to another executor must explicitly serialize both gates below. Do not leave them implicit merely because the current chat already read the law.

`P2P_LAW_PREFLIGHT` must tell the executor to read repository-root `AGENTS.md`, use canonical only if already successfully reachable; otherwise installed > valid portable > inline capsule > blocked; repo-scoped portable requires no cross-repo probe solely for fallback, and report exactly one `P2P_LAW_SOURCE=<actual source>`.

`OE_GATE` must ask exactly `Không bị over engineering chứ?`, evaluate `SIMPLER_PATH`, `MATERIAL_PROGRESS`, `NECESSITY`, `CORE_BEFORE_SUPPORT`, and `SMALLER_VERIFIABLE_SLICE`, then return `OE_VERDICT=DO_IT|SKIP_IT|DEFER_UNTIL_NEEDED` with one concrete reason. A weak/negative answer means reduce, remove, or defer the step; never return a ceremonial PASS.

This applies to NEW_CHAT and SAME_CHAT prompts for Arena, Codex, Manus, reviewers, supervisors, and other delegated executors. Do not repeat the whole law body when a valid law source is readable.

## Baseline hiện tại

- **Branch verified:** `log-c15-user-identity-rbac` @ `e518cae` (LOG-C13 + LOG-C14 + LOG-C15, đã kiểm chứng).
- Lineage: `main` ← `log-c13-contract-commercial-handoff` ← `log-c14-e2e-release-readiness` ← `log-c15-user-identity-rbac`.
- Merge strategy được khuyến nghị: 1 PR cumulative (C13+C14+C15) vào `main`, xem `docs/LOG_C15_HANDOFF.md` mục 37.
- KHÔNG deploy production; KHÔNG merge main cho đến khi Owner xác nhận.

## Quy ước quan trọng

- **Credential:** chỉ trong `.streamlit/secrets.toml` (gitignored). Không bao giờ in/hardcode URI/mật khẩu trong code.
- **App chạy trên máy Owner:** 2 instance production Streamlit (port 8501, 8510). Trước khi test UI, mở port khác (vd 9501), tắt sau khi xong.
- **Git credential helper:** `git config --global credential.helper manager` (helper cũ chỉ đường dẫn exe trực tiếp bị lỗi word-split trên máy này).
- **Database:** `logistics_workdesk_logc14` hiện là DB app đang dùng; `logistics_db` tồn tại trên cluster chưa dùng; DB test tạo riêng với prefix `logistics_workdesk_logc15+` và TỰ DROP sau khi chạy.
- **Quyền Atlas user hiện tại** chỉ đọc/ghi trên `logistics_workdesk_logc14` — không `dropUser`, không `listIndexes`.
- **Production untouched:** không drop/tạo database app, không thay đổi instance production.

## Testing

- Full suite: `python -m pytest tests -q` → kỳ vọng 200 passed, 28 skipped (pure tests).
- Tests runtime cần Streamlit/Mongo thực được skip theo thiết kế — không cố sửa chúng thành chạy được.
- Auth/RBAC: `tests/test_logc15_auth_rbac.py` (pure, mock streamlit).
- DB users: `scripts/logc15_db_users_test.py` + runner — chạy trên DB test riêng, tự dọn.

## Quyền (ma trận duy nhất: core/auth.py ROLE_PERMISSIONS)

admin=`*`, sale=sales_write + commercial_write + shipment_create + ops + knowledge + customers + tracking + tariff + commercial_view..., support=commercial_view + ops + finance_view + customers + tracking..., viewer=fallback read-only.

## Bootstrap

Chưa có user → app render form tạo Admin đầu tiên (không default credential). CLI: `python scripts/setup_first_user.py` (tương tác, mật khẩu không qua args).

## Native long-running goal bridge (P2P)

For a clear long-running task on a host that supports native `/goal`, use `/goal` only as a session-continuation primitive. Canonical P2P GoalPlan/TaskPlan, durable task state, evidence, and verifier remain authoritative.

- Prefer `.p2p/system/p2p_capabilities/native_goal_bridge.py` when an installed P2P runtime is present.
- If installed runtime is absent in a fresh clone, derive the `/goal` completion condition directly from the active P2P goal/task contract. Do not create a second roadmap, state machine, memory authority, router, ledger, daemon, or scheduler.
- Do not conflate host semantics. Only claim automatic continuation or evaluator behavior that is documented or directly verified for that host; do not assume Codex CLI has Claude Code's evaluator semantics.
- Recovery remains failure-class adaptive. Never introduce a fixed retry-count hard stop such as `three strikes => BLOCKED`.
- Before completion, compare the exact original baseline with the complete worktree: committed-after-baseline, staged, unstaged, deleted tracked, and untracked files. Prefer `.p2p/system/p2p_capabilities/worktree_evidence.py` when installed; otherwise use equivalent read-only Git inspection.
- Before claiming done, replay the original task contract and re-check acceptance requirements and evidence. Host-native `/goal` evaluation and executor self-report are never P2P acceptance authority.
- If the host has no native `/goal`, continue with the normal P2P execution path; do not add a substitute control plane just to imitate `/goal`.

## Native `/goal` auto-activation (P2P)

After law preflight and after durable P2P GoalPlan/TaskPlan state exists, but before the first substantive execution turn for that goal, decide native `/goal` activation automatically. Do not ask the Owner whether to use `/goal`.

- If installed runtime contains `.p2p/system/p2p_capabilities/native_goal_activation.py`, run `python .p2p/system/p2p_capabilities/native_goal_activation.py --host <claude_code|codex_cli> --format json`. Host identity comes from the current executor; Claude Code may use its stable in-session markers, while Codex passes `codex_cli` from known executor identity and must not infer it from `CODEX_HOME` alone.
- `decision=ACTIVATE_NATIVE_GOAL` -> if this same goal is not already active in the current host session, immediately invoke the returned `command` once, then continue the same P2P task.
- `decision=NORMAL_P2P_PATH` -> continue the normal P2P path.
- helper `status=BLOCKED` -> treat it as a durable-state/control-plane blocker; never fabricate a `/goal` condition.
- If the helper is absent, apply the exact same deterministic rule directly from authoritative durable state: activate only for Goal `APPROVED|IN_PROGRESS` + TaskPlan `ACTIVE` + at least two tasks + unfinished work; otherwise use the normal P2P path. Do not create another detector, state machine, router, ledger, daemon, or scheduler.
- Native `/goal` remains session continuation only. P2P task state, Owner Gates, evidence and independent verifier remain authoritative.

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
- if the answer is weak or negative, reduce/remove/defer the step instead of returning a ceremonial PASS.

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

