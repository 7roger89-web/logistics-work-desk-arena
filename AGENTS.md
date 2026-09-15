# AGENTS.md — Logistics Work Desk

## P2P Supreme Law bootstrap (mandatory)

Before substantive analysis, planning, prompt writing, implementation, review, testing, or merge decisions, establish exactly one valid P2P law source in this order:

1. `CANONICAL_AUTHENTICATED` — read `7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md` when actually reachable.
2. `LOCAL_INSTALLED` — otherwise use `.p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md` only when it contains `P2P_SUPREME_OPERATING_LAW_V1` and is not known stale.
3. `LOCAL_PORTABLE` — otherwise use `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md` only when it carries `P2P_PORTABLE_LAW_PROJECTION=YES`, canonical-source provenance, and a source identity (`SOURCE_CONTENT_SHA256` from the canonical projector or `SOURCE_GIT_BLOB_SHA` from an authenticated GitHub transport snapshot).
4. `INLINE_CAPSULE` — otherwise use only a fresh explicit `SUPREME_LAW_CAPSULE` supplied by the current P2P Control Tower prompt.

If none is available, stop before substantive work with `P2P_LAW_SOURCE=LAW_CONTEXT_BLOCKED`.

Do not treat an unauthenticated or repo-scoped 404 as proof that canonical law is absent. Do not claim a law source was read unless it actually was. `TASK_BRANCH != LAW_AUTHORITY`. `TARGET_PROJECT != LAW_SOURCE`. Fresh reachable canonical law wins over stale local projections or chat memory.

At task start report exactly one:
`P2P_LAW_SOURCE=CANONICAL_AUTHENTICATED|LOCAL_INSTALLED|LOCAL_PORTABLE|INLINE_CAPSULE|LAW_CONTEXT_BLOCKED`.

## Mandatory prompt serialization contract

Every P2P-generated operational prompt handed to another executor must explicitly serialize both gates below. Do not leave them implicit merely because the current chat already read the law.

`P2P_LAW_PREFLIGHT` must tell the executor to read repository-root `AGENTS.md`, establish the valid law source using canonical > installed > portable > inline capsule > blocked, and report exactly one `P2P_LAW_SOURCE=<actual source>`.

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
