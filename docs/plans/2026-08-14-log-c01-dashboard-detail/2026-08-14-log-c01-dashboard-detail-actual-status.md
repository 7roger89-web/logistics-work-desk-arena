# LOG-C01 Dashboard Detail Actual Status

Title: LOG-C01 Dashboard Detail
Date: 2026-08-14
Status: BLOCKED overall; P1-A locally verified; supervisor closure REJECT
Companion plan: `docs/plans/2026-08-14-log-c01-dashboard-detail/2026-08-14-log-c01-dashboard-detail-plan.md`
Companion evidence: `docs/plans/2026-08-14-log-c01-dashboard-detail/2026-08-14-log-c01-dashboard-detail-evidence.md`
Companion benchmark: `docs/plans/2026-08-14-log-c01-dashboard-detail/2026-08-14-log-c01-dashboard-detail-benchmark.md`

## Purpose

This file records the current project state after the selected one-click dashboard implementation slice. It is based on current source, project state, refreshed Anvien graph evidence, and a fresh local runtime verification.

## Freshness / Refresh Rules

P0 is the baseline at 2026-08-14. R1 below records the only changed behavior. No next implementation phase is started until the remaining acceptance boundary is reviewed.

## Scope

Target scope:

- Dashboard shipment list -> detail state transition and its read-only runtime proof.

Out of scope:

- P2P development checkout, secrets, auth policy, worker packaging, payment/database redesign, real-data writes, release, and deployment.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `views/dashboard.py` / `ui_dashboard` | E0-P0A-ANV2 | 1 direct file; 2 direct file relationships; 6 downstream symbol references | 117 symbols, 7 local relationships, 434 unresolved references; dashboard consumes state, filters, and detail renderer | high scope warning; surgical edit only |
| `views/shipment.py` / detail renderer | E0-P0A-ANV2 plus source inspection | inspect-only relationship surface | existing detail tabs render after active id is available | preserve; not the observed first-click cause |
| `core/database.py` read path | E0-P0A-ANV2 plus source inspection | 1 inspected source file; 56 linked flows in file projection | read/load and save functions share the file, but P1 performs no writes | preserve; do not expand P1 |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Some required behavior exists, but gaps remain. | Change only the missing parts. |
| `wrong` | Current behavior conflicts with the required outcome. | Replace only the failed transition. |
| `missing` | Required behavior does not exist. | Implement the missing piece only. |
| `unbound` | Surface exists but is not wired to the real flow. | Bind to the real source only. |
| `fake-or-stub` | Demo or placeholder behavior is used as real behavior. | Remove or make the state truthful. |
| `blocked` | Required authority/evidence is unavailable. | Stop and record the blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| P2P installation | Version `8.4.7-C-codex.15`; canonical 8/8, optional Aesthetica separation, foundation, decision trace, and project eval still pass, but final doctor/governance drift is FAIL for unlocked `.agents/skills` files and protected `P2P_INSTRUCTIONS_BLOCK` drift | Installed project runtime must be governance-clean before overall acceptance | partial / blocked | 86 managed files in release metadata; 8 profiles; current drift failures | E0-P0A-P2P1..P2P3, E1-P1A-P2P1 | owner/governance review required; preserve-only |
| Project P2P state | Profile/status/trusted evidence/execution ledger were missing before bootstrap and were created; policy/eval reused | Readable local project state without changing valid governance | correct | state boundary | E0-P0A-STATE1 | preserve-only |
| Dashboard previous-month filter | `01/07/2026`–`31/07/2026` renders and one shipment is visible | Filter remains active across selection and close | correct | part of dashboard file | E0-P0A-UI1 | preserve |
| Dashboard list -> detail first click | Row handler now assigns both existing selection keys and calls `st.rerun()`; fresh flow renders detail after one click | One click renders detail heading | correct for bounded scope | high-risk dashboard surface; 1 direct file, 6 downstream symbol references | E1-P1A-SRC1, E1-P1A-UI1 | preserve; no redesign |
| Dashboard detail renderer/close | Existing detail branch renders after active id; close clears both selection keys | Preserve existing detail form and explicit close | correct for observed scope | `views/shipment.py` inspect-only | E0-P0A-UI1 | preserve-only |
| Lump-sum customer payment | Mongo session transaction, idempotency key, version check, receipt/audit writes exist in source | Keep atomic path and later prove durable behavior safely | partial: source positive, runtime persistence unproven | `core/payment_logic.py` and `core/database.py` high-risk | E0-P0A-PAY1, E0-P0A-PERSIST1 | later / separate phase |
| Contract proxy payment pair | Two independent save calls can leave one collection updated if the second fails | Atomic multi-collection transaction or explicit safe recovery contract | partial / still present | `views/contracts.py` 75 symbols; 4 linked flows | E0-P0A-PAY2 | later / separate owner-approved data phase |
| Credential hygiene | Secret-bearing `.streamlit/secrets.toml` and tracked `google_key.json` exist | Rotate/revoke and remove from release/tracked history | blocked | protected security boundary | E0-P0A-SEC1 | owner decision required; do not touch in P1 |
| Authentication posture | Local Admin is granted while `AUTH_REQUIRED` is false | Authenticated role boundary for non-local deployment | blocked | `core/auth.py` + config/runtime | E0-P0A-OPS1 | owner decision required; do not touch in P1 |
| Worker/dependency/startup | `start.sh` starts `bot_service.py`; imported modules are absent from manifest; `$PORT` is unbounded | Declared startup contract is internally consistent and supervised | partial / still present | `start.sh`, `bot_service.py`, `requirements.txt` | E0-P0A-OPS1 | separate ops decision; do not touch in P1 |
| Durable persistence proof | Mongo read/ping evidence exists; no safe write -> reload -> read-back proof | Safe fixture or isolated test DB proves durability | unknown / blocked for current goal | DB boundary | E0-P0A-PERSIST1 | later; no real-data writes |
| Docker acceptance | No Dockerfile/docker-compose/Docker command found | Built container runtime for full app acceptance | blocked | runtime boundary | plan inventory and E0-P0A-RUN1 | report blocker; do not create infrastructure in P1 |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-14 | current source, P2P state, Anvien graph, and fresh local runtime before implementation | P2P, dashboard, payment, security, worker, persistence, Docker boundary | initial classifications above | E0-P0A-P2P1..E0-P0A-PERSIST1 | proceed only with P1-A dashboard transition; preserve all other boundaries |
| R1 | 2026-08-14 | post-edit source, refreshed Anvien graph, restarted local runtime, compile/tests | dashboard first-click transition | `partial/wrong -> correct for bounded scope`; P2P governance drift is a final blocker | E1-P1A-SRC1..E1-P1A-P2P1 | run independent supervisor review; do not broaden implementation |
| R2 | 2026-08-14 | supervisor review and cleanup | closure boundary | supervisor `REJECT`; runtime stopped; temp logs removed; overall `BLOCKED` | E2-PnA-SUP1..E2-PnC-CLOSE1 | owner/governance/security review required before any next phase |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `views/dashboard.py` | `views/shipment.py` | consumer -> detail renderer | P1-A | edit target; preserve renderer | E0-P0A-ANV2, E0-P0A-UI1 | minimal handler change only |
| `views/shipment.py` | none beyond dashboard call | detail renderer | P1-A | preserve-only | E0-P0A-UI1 | no render redesign |
| `core/database.py` | `views/dashboard.py` | read source and separate write boundary | P1-A | inspect-only | E0-P0A-PAY1, E0-P0A-PERSIST1 | no DB writes |
| `.streamlit/secrets.toml`, `core/auth.py`, `start.sh`, `bot_service.py`, `requirements.txt` | runtime/security surfaces | separate blockers, not required by P1-A | P1-A | do-not-touch | E0-P0A-SEC1, E0-P0A-OPS1 | owner decision / separate phase |
| `.p2p/system/*`, `.codex/agents/*` | protected P2P runtime | project governance boundary | P1-A | preserve-only | E0-P0A-P2P1..P2P3 | do not modify P2P |

## Detailed Findings

### Dashboard list-to-detail transition

Current state:

`active_sid` is read at the start of the dashboard tab. The row button now assigns both existing selection keys and explicitly schedules a rerun, allowing the existing detail branch to consume the selection in the same user flow. Current Browser evidence proves one click is sufficient.

Required state:

```text
The same row click that sets the active shipment must cause the existing detail branch to render, without changing filter state or writing business data.
```

Evidence:

- E0-P0A-UI1: fresh runtime reproduction.
- E0-P0A-SRC1: current source ordering and handler behavior.
- E0-P0A-ANV2: current file/impact scope.

Relationship and impact:

- Related file count: 1 direct file; `views/shipment.py` is a preserve-only consumer.
- Relationship summary: high-risk file projection with 117 symbols and 6 downstream symbol references.
- Impact note: high scope warning, not a prohibition; keep the change surgical.

Classification:

`correct for bounded scope`.

Allowed next action:

Edit only the selection transition, then verify the real flow.

Forbidden next action:

Do not rewrite the dashboard, detail renderer, database, auth, or secrets.

### Non-scope safety blockers

Current state:

Credentials, auth posture, worker packaging, Contract proxy atomicity, durable persistence proof, and Docker acceptance remain unresolved or blocked by owner/access boundaries.

Required state:

```text
Each issue needs its own evidence-backed phase and, for secrets/auth/real data/release, explicit owner authorization.
```

Evidence:

- E0-P0A-SEC1, E0-P0A-OPS1, E0-P0A-PAY2, E0-P0A-PERSIST1.

Relationship and impact:

- Related file count: multiple separate surfaces; not part of P1-A.
- Relationship summary: business/data/security/runtime boundaries.
- Impact note: preserve and report; do not silently fold into the UI fix.

Classification:

`blocked` or `partial` depending on the item above.

Allowed next action:

Prepare a separate owner decision/evidence package later.

Forbidden next action:

Do not rotate, delete, migrate, deploy, or write real business data during P1-A.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Surgical rerun fix is implemented; one-click detail and close/filter behavior are proven in the local runtime; Python checks pass | mark the bounded implementation slice complete; route only closure/acceptance review next |
| P1-B | No second implementation slice is needed for this single transition | remove/omit; do not expand scope |
| P2/Pn | Docker, safe commit boundary, supervisor, and closure evidence are not yet available | keep pending; stop at BLOCKED/PARTIAL and do not start optional hardening |
| Separate security/ops/data phase | current findings remain unresolved | keep later; requires owner decision or separate approved scope |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status and exact evidence IDs.
- [x] Target file relationship/impact evidence is recorded.
- [x] Phase Touch Map defines edit/preserve/inspect/do-not-touch modes.
- [x] Correct parts are marked preserve-only.
- [x] Partial/wrong/blocked parts have exact next actions.
- [x] Status Refresh Log has an R0 baseline row.
- [x] P0 decision is complete before implementation.
- [x] Affected rows and an R1 refresh were recorded after implementation.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [ ] P0 complete. Next phase can proceed unchanged.
- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 was complete for the bounded dashboard phase, and P1-A is now locally verified. The plan must not claim overall Logistics release readiness because credential/auth, worker, payment atomicity, durable persistence, Docker, and dirty-worktree boundaries remain unresolved.

## R1 - Post-implementation Refresh

- Date: `2026-08-14`
- Source change: `views/dashboard.py:366-371` adds an explicit rerun after the existing two selection aliases are assigned.
- Runtime result: local Streamlit health `200/ok`; the real in-app Browser flow observed detail after one click and no detail after close while retaining the July filter; the flow was read-only.
- Regression result: compile passed; all 24 available unit tests passed.
- Graph result: refreshed Anvien graph has 81 scanned files, 53 parsed code files, 0 parse failures; target file remains high-risk with 117 symbols and 435 unresolved references. The high-risk label is a scope warning, not a failure.
- Boundary: Docker is unavailable; the target file and wider repo remain dirty with unrelated user changes; no commit was created. Credential/auth, worker, payment atomicity, and durable persistence remain unresolved and were not changed.
- Governance refresh: final doctor and `p2p_governance.py drift` both report FAIL for unlocked `.agents/skills` runtime files and protected `P2P_INSTRUCTIONS_BLOCK` drift; this task did not edit the P2P checkout or those governance files.
- Classification: `P1-A PASS locally; overall task BLOCKED pending governance, supervisor, Docker, and owner/access boundaries`.

## R2 - Closure Refresh

- Supervisor verdict: `REJECT` for overall LOG-C01 closure; bounded P1-A behavior remains locally proven.
- Cleanup: verified port `8516` is no longer listening; exact temporary LOG-C01 stdout/stderr logs were removed; no business fixture or real-data write was performed.
- Final terminal status: `BLOCKED`.
- Required next decision: owner/governance review of P2P drift and security/operations boundaries before any broader hardening, deployment, or release work.
