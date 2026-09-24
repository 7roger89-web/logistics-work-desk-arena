# LOGI_LOGIN_TRANSPARENT_GLASS_01_VERIFY — EVIDENCE

- Task: `LOGI_LOGIN_TRANSPARENT_GLASS_01_VERIFY`
- Role: `UI_VERIFICATION_EXECUTOR` (Arena)
- Repo: `7roger89-web/logistics-work-desk-arena`
- Verdict: **PASS** (transparent-login contract holds at PR #101's real head)
- Date: `260924` (Asia/Saigon) · Runtime: real Chromium 153 + real Streamlit 1.64 app

## 1. Durable state actually verified

| Item | Prompt expectation | Observed (fresh `gh api`) | Note |
|---|---|---|---|
| PR #101 state | OPEN | **`closed` / merged** | already merged — nothing left to merge |
| PR #101 base | `4704528f26ae6b67b5b455c03e26438ab1cc6724` | `4704528f26ae6b67b5b455c03e26438ab1cc6724` | exact match |
| PR #101 head | `55d7fcd66c5a20eb3e8acdfce8ed15fe2544fe67` | **`d8103e0750170a4ea4c1150a6fc45cd119b63a59`** | **HEAD DRIFT** (+2 commits, see §2) |
| Changed files | only `core/auth.py`, `tests/test_login_visual_compact.py` | exactly those two | match |
| Merge commit on `main` | — | `0ba11a2c5a5838089327b5e55ee47fd737bf8d2d` | — |

`55d7fcd` is still an ancestor of the merged head, so the prompt's expected head is
contained in what was merged — it is simply not the final head.

### 2. Drift detail (why the head moved)

```
git log --oneline 4704528..d8103e0
d8103e0 LOGI_LOGIN_TRANSPARENT_GLASS_01_VERIFY — tighten the brand line halo
c6fed8e LOGI_LOGIN_TRANSPARENT_GLASS_01_VERIFY — stop the input shell showing as an opaque grey plate
55d7fcd LOGI_LOGIN_TRANSPARENT_GLASS_01 — lock transparent login visual contract   <- prompt's expected head
fff8331 LOGI_LOGIN_TRANSPARENT_GLASS_01 — make login surface transparent
```

`c6fed8e` neutralises Streamlit's own `stTextInputRootElement` plate
(`background/border/box-shadow`), and `d8103e0` tightens the brand-line halo. Both
are transparency-surface edits inside the same CSS template — no auth-surface change.
Verified at AST level: between `4704528` and the merged tip, the **only** top-level
construct that differs in `core/auth.py` is the `_LOGIN_HERO_CSS_TEMPLATE` string
(52 top-level nodes before and after).

## 3. Focused test (exact head)

```
cd <checkout of d8103e0>
PYTHONPATH=. pytest tests/test_login_visual_compact.py -v
```

Result: **20 passed** in 2.49 s.

Prompt expected `19`. The file defines **20** test functions at this head, of which
**18** exist at the prompt's base `4704528`; PR #101 added exactly two:

```
> def test_transparent_glass_form_is_near_transparent_no_dark_veil
> def test_text_input_shell_stays_transparent_so_artwork_shows_through
```

So the `19` in the prompt does not correspond to any commit in this branch
(base = 18, PR #101 head = 20). No test was skipped or deselected; pytest
collected 20 items and all 20 passed.

## 4. Real rendered verification

Method (no mocking of the UI layer):

1. Real repository code at the exact PR head checked out in an isolated worktree.
2. Real `streamlit run app.py` process on a staging-only transport
   (`MONGO_DB_NAME=logistics_staging`, `ENV_IDENTITY=PREVIEW`, in-process
   `mongomock`, one staging user — the transport this repo already declares for
   sandbox/preview in `requirements.txt`). No production URI, DB, or secret.
3. Real Chromium 153 driven at real viewports; the login screen was loaded and the
   rotation was re-rolled with fresh sessions until the required artworks appeared.
4. Each view was measured three ways:
   - computed CSS (`getComputedStyle`) for the container / form / inputs / button;
   - a **UI screenshot** and a **background-only screenshot** (form hidden) so the
     panel's transparency can be proven by pixel identity of the artwork behind it;
   - an **artwork-vs-render** comparison: the Owner artwork is re-laid-out at its
     computed rendered rect (`cover` + focal `background-position`) over `#071019`
     and compared block-by-block against the browser screenshot.

### 4.1 Acceptance

| Criterion | Result | Evidence |
|---|---|---|
| `BACKGROUND_ART_IS_PRIMARY_VISUAL` | **YES** | block delta vs source artwork: median 0.6–1.5 / p90 2.9–6.3 (of 255); no tint layer (`background-image` is the artwork data-URI only; `rgba(0,0,0,0)` panel) |
| `FULL_SCREEN_DARK_VEIL_REMOVED` | **YES** | no `linear-gradient` in `background-image`; solved veil alpha ≈ **0.3 %** median |
| `FORM_PANEL_NEAR_TRANSPARENT` | **YES** | `stForm` computed `background: rgba(0, 0, 0, 0)` |
| `BACKDROP_BLUR_REMOVED` | **YES** | `backdrop-filter: none` (incl. `-webkit-`) |
| `LARGE_DARK_CARD_SHADOW_REMOVED` | **YES** | `box-shadow: none` |
| `ART_VISIBLE_BEHIND_FORM_AREA` | **YES** | 4 800–18 831 empty pixels sampled **inside** the panel: max channel difference vs the background-only shot = **0** |
| `INPUTS_READABLE` | **YES** | WCAG contrast on the measured backdrop: 7.91–15.65 (threshold 4.5) |
| `LOGIN_BUTTON_READABLE` | **YES** | `#1E40AF` + white = 8.72 |
| `DESKTOP_USABLE` | **YES** | 1440×900, no horizontal overflow, form and button fully visible |
| `MOBILE_USABLE` | **YES** | 390×844, no horizontal overflow, form and button fully visible |

### 4.2 Measured (exact numbers)

See [`evidence/measurements.md`](evidence/measurements.md) and
[`evidence/measurements.json`](evidence/measurements.json).

Desktop 1440×900, artwork `cover` + per-image focal position, artwork visible
fraction 0.90 (16:9 art in a 16:10 viewport), no veil, panel `rgba(0,0,0,0)`:

| Artwork | pose | input contrast | button contrast | panel Δ vs artwork-only |
|---|---|---|---|---|
| `login-bg-02` (sea/port) | `50% 35%` | 10.96 / 11.47 | 8.72 | 0 |
| `login-bg-04` (collage) | `50% 42%` | 15.49 / 7.91 | 8.72 | 0 |

Phone 390×844 (`max-width: 768px` + focal mobile position), artwork visible
fraction **0.2601** (75 % of the artwork is off-screen because `cover` fills a
390×844 viewport with a 1672×941 artwork) — see the rendered captures:

| Artwork | pose | visible fraction | panel Δ | input contrast | button contrast |
|---|---|---|---|---|---|
| `login-bg-01` | `32% 40%` | 0.2601 | 0 | 10.83 / 15.01 | 8.72 |
| `login-bg-03` (road/border) | `28% 45%` | 0.2601 | 0 | 10.72 / 8.07 | 8.72 |

### 4.3 Rendered captures

- [`evidence/contact_sheet_desktop_1440x900.jpg`](evidence/contact_sheet_desktop_1440x900.jpg)
- [`evidence/contact_sheet_phone_portrait_390x844.jpg`](evidence/contact_sheet_phone_portrait_390x844.jpg)
- [`evidence/fullsize_desktop_1440x900_bg02.jpg`](evidence/fullsize_desktop_1440x900_bg02.jpg)
- [`evidence/fullsize_phone_portrait_390x844_bg01.jpg`](evidence/fullsize_phone_portrait_390x844_bg01.jpg)

## 5. Defects found in PR #101

- **Material defects at the verified head: none.** The transparent-login contract
  holds on desktop and on phone, on real rendered pixels.
- **Artwork subject index (verified, see the PR #102 evidence
  `evidence/artwork_index.jpg`):** 01 = road/border gate + container truck,
  02 = sea/port, 03 = air cargo, **04/05/06/08 = collage montages**, 07 = air cargo,
  09/10 = air cargo (byte-identical to each other). The inline comments for 4, 5 and 7
  in `_LOGIN_BG_POSITIONS` (`air cargo`, `warehouse`, `collage montage`) describe them
  the other way round; that is a pre-existing PR #100 comment inaccuracy with no
  behavioural effect, and it was **not** changed here because this task must not
  rewrite the implementation.
- **Carry-over limitation (already known, not repaired here):** on a phone
  **portrait** viewport PR #101 still uses `cover`, so only ~26 % of each artwork is
  visible (heavy left/right crop). PR #101's own commit `55d7fcd` contained a
  narrow-viewport `contain` rule, but the merged head's only media query is
  `@media (max-width: 768px)` with `background-size` left at `cover`. This
  limitation is the explicit scope of **PR #102**
  (`LOGI_LOGIN_RESPONSIVE_BACKGROUND_FIT_01`), which was verified separately and
  fixes it (`0.2601 → 1.0` visible fraction, `contain`, no distortion).
- Therefore **no repair was made on PR #101**, per the instruction *"Do not rewrite
  the implementation unless a real defect is found"*. PR #101 is closed/merged and
  was not reopened, modified, or replaced.

## 6. Regression boundary (PR #101)

| Boundary | Result | Evidence |
|---|---|---|
| 10 WebP assets | **unchanged** | identical Git blobs at base and at PR #101 head; sha256 of all ten recorded in `measurements.json` |
| Background rotation | **unchanged** | rotation/PREV-key logic untouched (`fff8331`/`c6fed8e`/`d8103e0` touch only the CSS template; AST comparison in §2); observed at runtime: fresh sessions returned different artworks, one artwork stayed stable within a session, and it did not change across login attempts |
| Duplicate 09/10 handling | **unchanged** (`_choose_login_bg_index` keeps its 9/10 exclusion). Note: `login-bg-09.webp` and `login-bg-10.webp` are byte-identical and visually identical (mean abs pixel difference 0.00) — the Owner-artwork pairing, not something PR #101 introduced |
| Auth decisions | **unchanged** | no diff outside the CSS template; login route, `_authenticate`, session keys, error message all identical |
| DB / secrets | **untouched** | no file under `core/database.py`, `core/users.py`, `.streamlit/`, `.env*` in the PR diff |
| Deployment | **not deployed** | no deploy, no production DB, no production secrets used |
| Footer/carried-in `core/auth.py` change | **not from PR #101** | `git diff 55d7fcd..d8103e0 -- core/auth.py` vs `git diff 4704528..d8103e0 -- core/auth.py` are identical, and `git diff d8103e0 478eba2 -- core/auth.py tests/test_login_visual_compact.py` is **empty** — PR #101's head is byte-identical to what is on `main` today for those two files |

No changes were made to the repository for this verification task.
