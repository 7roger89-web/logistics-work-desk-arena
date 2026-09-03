# LOGISTICS DeepL Translation V1 Actual Status

Title: LOGISTICS DeepL Translation V1
Date: 2026-09-03
Status: Ready for exact Supervisor review; mocked/local code gates complete and Owner real-key gate blocked.
Companion plan: `docs/plans/2026-09-03-logistics-deepl-translation-v1/2026-09-03-logistics-deepl-translation-v1-plan.md`
Companion evidence: `docs/plans/2026-09-03-logistics-deepl-translation-v1/2026-09-03-logistics-deepl-translation-v1-evidence.md`
Companion benchmark: `docs/plans/2026-09-03-logistics-deepl-translation-v1/2026-09-03-logistics-deepl-translation-v1-benchmark.md`

## Purpose

Classify the fresh branch before implementation and keep the status current as
each bounded slice changes the repository.

## Freshness / Refresh Rules

P0 is bound to fresh `origin/main` at `c1c9468a814a2c0e56cefcf2851a2cadf46df436`
and tree `6466d7fa435b46d4d13b0b92558ed354f62c4363`. The original detached
checkout and its untracked files remain preserve-only. Refresh affected rows
after each implementation slice; do not convert mocked evidence into real API
readiness.

## Scope

Target scope:

- `core/config.py`, `core/auth.py`, `views/web_app.py` supporting boundaries;
- new `core/deepl_translation.py`, `views/translation.py`, and focused tests;
- local-only Streamlit route and safe external HTTP behavior.

Out of scope:

- all existing database/business surfaces, production instances/data, root
  secrets contents, unrelated worktrees, push/PR/merge/deploy, and non-text
  translation features.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `core/config.py` | `E0-P0A-REL1` | 3 | existing secret loader; imported by config consumers | high; edit only new DeepL setting |
| `core/auth.py` | `E0-P0A-REL1` | 4 | sole role permission matrix and auth consumers | high; add one permission only |
| `views/web_app.py` | `E0-P0A-REL1` | 1 | route tuple/group/sidebar/route boundary | high; add one route/group entry only |
| `core/deepl_translation.py` | `E0-P0A-MISSING1` | 0 before implementation | missing service boundary | bounded new source |
| `views/translation.py` | `E0-P0A-MISSING1` | 0 before implementation | missing UI boundary | bounded new source |
| `tests/test_deepl_translation.py` | `E0-P0A-MISSING1` | 0 before implementation | missing focused behavior evidence | bounded new test |
| `.streamlit/secrets.toml` in clean worktree | `E0-P0A-SECRET1` | N/A | absent in branch; root presence not read | preserve-only; Owner supplies locally |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Some required behavior exists, but gaps remain. | Change only missing parts. |
| `wrong` | Conflicts with the requirement. | Replace only the conflicting behavior. |
| `missing` | Required behavior does not exist. | Implement bounded surface. |
| `unbound` | Exists but is not wired to the required flow. | Bind to the real surface. |
| `fake-or-stub` | Demo/mock is presented as real behavior. | Remove or replace with truthful state. |
| `blocked` | Authority/evidence is insufficient. | Stop and record blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Fresh branch/base | clean branch from fresh origin/main with PR #8 merge | exact branch base preserved | correct | N/A | `E0-P0A-GIT1`, `E0-P0A-BRANCH1` | proceed |
| Original root checkout | detached, untracked Owner files, local main diverged | unchanged preserve-only checkout | correct boundary | N/A | `E0-P0A-PRESERVE1` | do not touch |
| `core/config.py` DeepL setting | list loader now exposes `DEEPL_API_KEYS`; no values persisted | backend receives list via existing loader | correct | 3 | `E0-P0A-SRC1`, `E1-P1A-CONFIG1` | preserve |
| DeepL service | requests-based client/key pool implemented with 14 focused tests | safe text client/key pool with finite failover | correct | 1 related file | `E1-P1A-IMPACT1`, `E1-P1A-TEST1`, `E1-P1B-ROTATE1` | proceed P2 |
| DeepL usage checker | explicit `check_usage()` returns index-only rows | explicit-call-only indexed status rows | correct | covered by service family | `E1-P1C-USAGE1`, `E1-P1C-BOUNDARY1` | proceed P2 |
| `core/auth.py` translation permission | matrix now grants only `translation` to sale/support in addition to current PR #8 policy | sale/support access only | correct | 4 | `E0-P0A-REL1`, `E2-P2A-RBAC1`, `E2-P2A-TEST1` | preserve |
| `views/web_app.py` translation route | route/group system now mounts one DeepL route | one grouped route with route boundary | correct | 1 | `E0-P0A-REL1`, `E2-P2A-RBAC1`, `E2-P2A-TEST1` | preserve |
| Translation UI | text-only view renders and mounted support flow passes | safe text-only view | correct | 2 | `E2-P2B-UI1`, `E2-P2B-FLOW1`, `E2-P2C-TEST1` | Owner visual gate |
| Focused DeepL tests | 50 focused service/config/RBAC/UI tests pass | mocked behavior and mounted RBAC/UI evidence | correct | 2 | `E1-P1A-TEST1`, `E2-P2A-TEST1`, `E2-P2C-TEST1` | preserve |
| Clean-branch DeepL secrets | no key configured; root secret contents not inspected | local Owner-supplied keys only | blocked for real smoke, not implementation | N/A | `E0-P0A-SECRET1` | mock first; Owner gate later |
| Production DB/runtime | not invoked | zero mutations and no production start | correct boundary | N/A | `E0-P0A-BOUNDARY1` | preserve |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-09-03 | fresh fetch, branch creation, Anvien baseline, source inspection | authority, config, auth, route, missing DeepL surfaces | initial classifications recorded | `E0-P0A-GIT1`, `E0-P0A-ANV1`, `E0-P0A-REL1`, `E0-P0A-MISSING1`, `E0-P0A-SECRET1` | P1-A starts on clean branch |
| R1 | 2026-09-03 | P1 service/config implementation and 14 focused tests | config, translation key pool, bounded retry, usage rows, secret safety | config/service/usage missing -> correct; focused tests missing -> partial | `E1-P1A-IMPACT1`, `E1-P1A-TEST1`, `E1-P1B-ROTATE1`, `E1-P1C-USAGE1` | P2-A route/RBAC is next |
| R2 | 2026-09-03 | P2 route/RBAC/UI implementation and 50 focused tests | permission, route, view, mounted support flow | route/UI/tests partial -> correct; real smoke remains blocked | `E2-P2A-IMPACT1`, `E2-P2A-RBAC1`, `E2-P2B-FLOW1`, `E2-P2C-TEST1`, `E2-P2C-LOCAL1` | stop at Owner key gate |
| R3 | 2026-09-03 | final compileall, reverse-flow coverage, candidate closure package, coder report | final implementation/evidence identity and Owner stop boundary | P2 implementation remains correct; external real-key gate remains blocked | `E2-P2C-REVERSE1`, `E3-CLOSURE1`, `E3-CLOSURE2`, `E3-CLOSURE3` | exact Supervisor review |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `core/config.py` | existing config consumers | source-of-truth / config | P1-A | edit | `E0-P0A-REL1` | add only DeepL list setting |
| `core/auth.py` | auth/RBAC tests | source-of-truth / permission | P2-A | edit | `E0-P0A-REL1` | add only `translation` to sale/support |
| `views/web_app.py` | existing route/UI tests | route consumer / render | P2-A | edit | `E0-P0A-REL1` | preserve all labels and groups except one entry |
| `core/deepl_translation.py` | new focused service tests | new service/test boundary | P1-A/P1-B/P1-C | edit | `E0-P0A-MISSING1` | no DB/generic provider abstraction |
| `views/translation.py` | new focused AppTest | new UI/test boundary | P2-B/P2-C | edit | `E0-P0A-MISSING1` | no history, upload, or customer-data flow |
| root checkout and existing `.tmp` worktrees | N/A | Owner data / unrelated candidate work | all | do-not-touch | `E0-P0A-PRESERVE1` | no cleanup/reset/merge |
| production DB/instances | N/A | protected external boundary | all | do-not-touch | `E0-P0A-BOUNDARY1` | no production access or writes |

## Detailed Findings

### Git authority and isolation

Current state:

`origin/main` was freshly fetched and includes PR #8. The implementation branch
is a clean worktree at that exact SHA/tree. The original checkout is dirty and
diverged; it remains untouched.

Required state:

```text
Implement only in feature/logistics-deepl-translation-v1 worktree from fresh origin/main.
```

Evidence:

- `E0-P0A-GIT1`, `E0-P0A-BRANCH1`, `E0-P0A-PRESERVE1`.

Classification:

correct / bound-correct

Allowed next action:

Implement bounded DeepL slices in the clean worktree.

Forbidden next action:

Reset or modify the original checkout, reconcile divergent local main, push,
merge, deploy, or open a PR.

### DeepL implementation surfaces

Current state:

No DeepL service, view, route, permission, or focused test exists. Existing
config/RBAC/router primitives are usable and are the only supporting surfaces
needed.

Required state:

```text
Small requests-based client + explicit route + focused mocked and mounted evidence.
```

Evidence:

- `E0-P0A-SRC1`, `E0-P0A-MISSING1`, `E0-P0A-REL1`.

Classification:

partial supporting surfaces; missing DeepL surfaces

Allowed next action:

Proceed through P1-A, P1-B, P1-C, then P2-A/P2-B/P2-C in order.

Forbidden next action:

Add a provider framework, database/history, document pipeline, or hidden Gemini
fallback.

### Secret and real-API gate

Current state:

The clean branch has no local DeepL key configured. The original root secret
file exists but was deliberately not opened or copied.

Required state:

```text
Mocked tests first; real smoke only after Owner adds keys to local secrets.
```

Evidence:

- `E0-P0A-SECRET1`.

Classification:

blocked for real API smoke only; implementation is not blocked

Allowed next action:

Use fake keys in tests, then stop with the Owner instruction if the clean branch
still has no configured key.

Forbidden next action:

Read, copy, print, commit, or ask the Owner to paste a real key into chat/source.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | DeepL config/service are missing; existing list loader is correct | proceed with minimal edit |
| P1-B | no translation request path exists | implement only finite key-pool behavior |
| P1-C | no usage path exists | keep usage explicit-call-only |
| P2-A | route/RBAC primitives exist; DeepL permission/route absent | add one permission and one grouped route |
| P2-B | no UI exists | add only text translation view |
| P2-C | no focused mounted evidence exists | add support/viewer/secret-safety AppTest |
| Owner real smoke | no clean-branch key configured | block only real smoke; do not block mocked/local no-key UI |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence where applicable.
- [x] Phase Touch Map defines touch mode for every plan-relevant unit.
- [x] Correct parts are preserve-only where appropriate.
- [x] Partial/missing/blocked parts have exact next actions.
- [x] Blockers are recorded without broadening the scope.
- [x] Next phase status assumptions and work steps reflect P0 evidence.
- [x] Status Refresh Log has an R0 baseline row.
- [x] Affected rows refreshed after implementation begins.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase can proceed unchanged.
- [ ] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

Authority and supporting surfaces are known. The clean branch is isolated from
the dirty root and is ready for bounded implementation. Real API smoke remains
an Owner-secret gate, not a reason to invent credentials or broaden access.
