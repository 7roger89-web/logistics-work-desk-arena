# Supervisor Report: Responsive Login Background Fit — PR #102 Live Preview

Verdict: PASS

## Metadata

- Report file: `rp_supervisor_260924_lo_responsive-background-fit-01-preview_by_arena-agent.md`
- Preview time: `260924` (Asia/Saigon)
- Executor: Arena agent, role `RESPONSIVE_UI_PREVIEW_EXECUTOR`
- Repo/project: `7roger89-web/logistics-work-desk-arena` (isolated worktree at the PR head)
- Scope verified: PR **#102** (`LOGI_LOGIN_RESPONSIVE_BACKGROUND_FIT_01`), live preview for the
  Owner's real-device inspection — portrait/tall `contain`, landscape/desktop `cover`.
- Authority used: Owner task contract; repository `AGENTS.md`; fresh `gh api` PR state; the exact
  PR head source; focused pytest; real rendered Streamlit/Chromium runtime.
- Related artifacts: `docs/LOGI_LOGIN_RESPONSIVE_BACKGROUND_FIT_01_PREVIEW/EVIDENCE.md`,
  `preview_only_shim.py`, and the `evidence/` captures.

## Executive Summary

- Problem: the Owner must judge the responsive login artwork on a real phone, including the
  browser's "Desktop site" mode, before PR #102 is accepted.
- Decision: PASS. A live preview is running from the **exact** PR #102 head
  (`b9f8f93054179b1e6f871ffc7d297bd49156fd97`), and the responsive contract is confirmed by
  measurement: `contain` with the whole artwork visible in portrait, `cover` unchanged in
  landscape/desktop.
- Required outcome: Owner real-device inspection can proceed. No code was changed.

## Fresh Durable State

- PR #102: **OPEN**, base `478eba2b2b435c88faf465d53ad95972030ac5f4` (current `main` tip),
  head **`b9f8f93054179b1e6f871ffc7d297bd49156fd97`** — exact match to the expected head, no drift.
- `mergeable: true`, `mergeable_state: clean`.
- Diff: `CHANGELOG.md`, `core/auth.py` (+17 lines inside the CSS template), `tests/test_login_visual_compact.py`
  (+115 lines) — no auth/DB/secret/asset/deployment change.
- PR #101 was not checked out, reopened, or repaired.

## Preview

- `PREVIEW_SOURCE_SHA=b9f8f93054179b1e6f871ffc7d297bd49156fd97` (isolated worktree).
- Real `streamlit run app.py`, staging only: `MONGO_DB_NAME=logistics_staging`,
  `ENV_IDENTITY=PREVIEW`, in-process `mongomock` transport (declared for sandbox/preview in
  `requirements.txt`), one local staging user so the real login form renders.
- `?bg=1..10` pins an artwork for Owner inspection through a preview-level wrapper; with no `bg`
  parameter the shipped rotation runs untouched. `core/auth.py` is not modified by the preview.
- Production DB / secrets / deployment: **not used**, **not touched**.

## Evidence Checked

Passed:

- `PYTHONPATH=. pytest tests/test_login_visual_compact.py -v` at the exact head → **25 passed**
  (20 inherited from PR #101 + the 5 responsive-fit tests added by PR #102), 2.22 s.
- Portrait/tall (390×844 and 980×1743 "Desktop site" mode): `background-size: contain`,
  `background-position: center 85%`; whole artwork visible (full width visible in **7/7**
  measured artworks), aspect preserved by a single uniform scale — no stretch, no left/right crop.
- Landscape (844×390): `background-size: cover` with the per-image focal position, artwork
  visible fraction 0.821 — unchanged from PR #101 (numerically identical).
- Desktop (1440×900): `cover`, visible fraction 0.9005 — unchanged from PR #101.
- Rotate test in one session (portrait → landscape → portrait → landscape → portrait):
  `contain`/`cover` alternate correctly at every step, panel transparency delta 0, artwork never
  changes, no horizontal overflow.
- Transparency/veil at every step: form `rgba(0, 0, 0, 0)`, `backdrop-filter: none`,
  `box-shadow: none`, container `background-image` = artwork data-URI only, solved veil alpha
  ≈ 0.002–0.013, block delta vs source artwork median ≤ 4.8 of 255, input contrast 7.91–18.31,
  button contrast 8.72.

Failed:

- None for the reviewed claim.

Not run:

- Merge, deployment, production data, and unrelated surfaces — prohibited by the task.
- The full repository suite: outside this bounded preview/verification scope.

## Expectations the Owner Should Hold While Inspecting

- **Portrait**: the 16:9 artwork renders as a full-width band (390×219.5 CSS px) on the neutral
  `#071019` colour, with the transparent form above it (`margin-top: 6vh`, band nudged to
  `center 85%`). This is the explicit "whole artwork visible" rule; a taller phone therefore shows
  more neutral colour than artwork.
- **Landscape**: full-screen `cover` still applies; on a 390-px-high viewport the login button
  starts 468 px down, so a short scroll (~294 px inside Streamlit's main section) is needed to
  reach it. Reachable, not clipped.
- **Desktop-site mode**: the fix is owned by `orientation: portrait`, not by the 768-px width
  breakpoint, so this mode now shows the whole artwork too.
- `login-bg-05` is a warehouse interior, not a collage; the collage backgrounds are 06/07/08.
- `login-bg-09` and `login-bg-10` remain byte-identical Owner artwork; the rotation rule that never
  shows them consecutively is unchanged.

## Regression Boundary

- 10 WebP assets: unchanged (identical Git blobs; sha256 in the evidence pack).
- Background rotation: unchanged; the `?bg=N` pin lives only in the preview process.
- Duplicate 09/10 handling: unchanged.
- Auth decisions, DB, secrets: unchanged / untouched.
- Deployment: none performed; production untouched.
