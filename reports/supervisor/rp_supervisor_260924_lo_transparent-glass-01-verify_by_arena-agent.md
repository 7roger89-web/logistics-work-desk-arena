# Supervisor Report: Transparent Login over Owner Artwork — PR #101 Verification

Verdict: PASS

## Metadata

- Report file: `rp_supervisor_260924_lo_transparent-glass-01-verify_by_arena-agent.md`
- Verification time: `260924` (Asia/Saigon)
- Executor: Arena agent, role `UI_VERIFICATION_EXECUTOR`
- Repo/project: `7roger89-web/logistics-work-desk-arena` (isolated worktree at the PR head)
- Scope verified: PR **#101** (`LOGI_LOGIN_TRANSPARENT_GLASS_01`) — the merged transparent-login
  contract, `core/auth.py` + `tests/test_login_visual_compact.py`.
- Authority used: Owner task contract; repository `AGENTS.md`; fresh `gh api` PR state; the
  exact PR head source; focused pytest; real rendered Streamlit/Chromium runtime.
- Related artifacts: `docs/LOGI_LOGIN_TRANSPARENT_GLASS_01_VERIFY/EVIDENCE.md` and its
  `evidence/` captures.

## Executive Summary

- Problem: PR #101 changed only `core/auth.py` and `tests/test_login_visual_compact.py`; before
  merge/acceptance the transparent-login claim needed independent focused test + real rendered
  visual verification at the exact head.
- Decision: PASS. The transparent-login contract is confirmed on real rendered pixels at
  desktop 1440×900 and phone 390×844: no dark full-screen veil, no blur, no card shadow, a fully
  transparent form, and the Owner artwork visibly unmodified behind and through the control area.
- Required outcome: PR #101 accepted as-is. No repair was made, per the instruction not to
  rewrite the implementation unless a real defect is found.

## Durable State Actually Verified

| Item | Prompt expectation | Observed | Verdict |
|---|---|---|---|
| PR #101 state | OPEN | closed / merged (`0ba11a2c5a5838089327b5e55ee47fd737bf8d2d`) | already merged |
| base | `4704528f…` | `4704528f…` | exact |
| head | `55d7fcd6…` | **`d8103e0750170a4ea4c1150a6fc45cd119b63a59`** | HEAD DRIFT (+2 commits) |
| changed files | `core/auth.py`, `tests/test_login_visual_compact.py` | exactly those two | exact |

`55d7fcd6…` remains an ancestor of the merged head. The two later commits on the same PR
(`c6fed8e` — neutralise Streamlit's opaque text-input shell plate; `d8103e0` — tighten the brand
line halo) are inside the same CSS template. AST comparison of `core/auth.py` between the base
and the merged tip shows exactly one differing top-level node: `_LOGIN_HERO_CSS_TEMPLATE`.

## Evidence Checked

Passed:

- `gh api repos/…/pulls/101` → state, base SHA, head SHA, merge commit; `git merge-base
  --is-ancestor` confirms `55d7fcd6…` ⊂ merged head.
- `git diff --stat 4704528 d8103e0` → 2 files, +101/−17; no DB, secrets, deployment, or asset file.
- `PYTHONPATH=. pytest tests/test_login_visual_compact.py -v` at the exact head → **20 passed**
  in 2.49 s (prompt expected 19; file defines 20 — 18 at the base commit, +2 added by PR #101).
- Real runtime (Streamlit 1.64.0, staging-only `mongomock` transport at the exact head) in real
  Chromium 153:
  - `stForm`: `background: rgba(0, 0, 0, 0)`, `backdrop-filter: none`, `box-shadow: none`;
  - container `background-image` is the artwork data-URI only — no `linear-gradient` scrim;
  - solved dark-veil alpha ≈ **0.003** (0.3 %) from bright source blocks → veil removed;
  - block-level comparison against the source artwork: median 0.6–1.5, p90 2.9–6.3 of 255;
  - **0** channel difference over 4 800–18 831 empty pixels sampled *inside* the panel between
    the UI screenshot and the background-only screenshot → artwork fully visible behind the panel;
  - WCAG contrast on the measured backdrop: inputs 7.91–15.65, login button 8.72;
  - no horizontal overflow; form and button fully visible at both mandatory viewports.

Failed:

- None for the reviewed claim.

Not run:

- Authenticated post-login surfaces and the rest of the repository suite: outside this bounded
  claim (the login screen is the entire changed surface).
- Production database, production secrets, deployment: prohibited by the task.

## Residual / Carried Forward

- On phone **portrait**, PR #101's merged CSS still uses `background-size: cover`, so only
  ~26 % of each artwork is visible. Commit `55d7fcd6…` had proposed a narrow-viewport `contain`
  rule, but the merged head's only media query is `@media (max-width: 768px)` with `cover`
  retained. This is a known limitation, not a defect of the transparent-glass scope, and is the
  explicit scope of PR #102 (`LOGI_LOGIN_RESPONSIVE_BACKGROUND_FIT_01`), which fixes it
  (`0.2601 → 1.0` visible fraction).
- `login-bg-09.webp` and `login-bg-10.webp` are byte-identical Owner artworks (pixel difference
  0.00); the existing rotation equivalence rule for 09/10 is correct and unchanged.
- PR #101's head is byte-identical to `main` today for both of its files
  (`git diff d8103e0 478eba2 -- core/auth.py tests/test_login_visual_compact.py` is empty).

## Regression Boundary

- 10 WebP assets: unchanged (identical Git blobs; sha256 recorded in the evidence pack).
- Background rotation and the 09/10 duplicate rule: unchanged (no diff outside the CSS template;
  observed stable within a session and varying across fresh visits).
- Auth decisions, DB, secrets: unchanged / untouched.
- Deployment: none performed.
