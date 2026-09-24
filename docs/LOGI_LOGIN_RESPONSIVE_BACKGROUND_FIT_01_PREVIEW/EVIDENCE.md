# LOGI_LOGIN_RESPONSIVE_BACKGROUND_FIT_01_PREVIEW — EVIDENCE

- Task: `LOGI_LOGIN_RESPONSIVE_BACKGROUND_FIT_01_PREVIEW`
- Role: `RESPONSIVE_UI_PREVIEW_EXECUTOR` (Arena)
- Repo: `7roger89-web/logistics-work-desk-arena`
- Verdict: **PASS** — live preview started from the exact PR #102 head; Owner
  real-device inspection can proceed
- Date: `260924` (Asia/Saigon) · Runtime: real Chromium 153 + real Streamlit 1.64 app

## 1. Fresh durable state

| Item | Prompt expectation | Observed (fresh `gh api`) |
|---|---|---|
| PR #102 state | OPEN | **OPEN** |
| PR #102 head | `b9f8f93054179b1e6f871ffc7d297bd49156fd97` | **`b9f8f93054179b1e6f871ffc7d297bd49156fd97`** (no drift) |
| PR #102 base | `478eba2b2b435c88faf465d53ad95972030ac5f4` | `478eba2b2b435c88faf465d53ad95972030ac5f4` (branch `main`, current tip) |
| Mergeability | MERGEABLE | `mergeable: true`, `mergeable_state: clean` |
| Changed files | auth/responsive only | `core/auth.py`, `tests/test_login_visual_compact.py`, `CHANGELOG.md` (+152/−0) |

PR #101 was **not** checked out, inspected for repair, or reopened. It is closed/merged;
its verification is a separate document
([`../LOGI_LOGIN_TRANSPARENT_GLASS_01_VERIFY/EVIDENCE.md`](../LOGI_LOGIN_TRANSPARENT_GLASS_01_VERIFY/EVIDENCE.md)).

## 2. What PR #102 adds (only this)

```css
/* Portrait / tall viewports — geometry, not device names. */
@media (orientation: portrait) {
  [data-testid="stAppViewContainer"] {
    background-size: contain;
    background-position: center 85%;
    background-repeat: no-repeat;
  }
  [data-testid="stForm"] { margin-top: 6vh; }
}
```

No auth, DB, secret, asset, rotation, or deployment change is part of the diff.

## 3. Live preview

- Source: isolated worktree checked out at **exactly**
  `b9f8f93054179b1e6f871ffc7d297bd49156fd97` (`PREVIEW_SOURCE_SHA`).
- Command (preview/staging only):

```bash
MONGO_URI="mongodb://127.0.0.1:27017" \
MONGO_DB_NAME="logistics_staging" ENV_IDENTITY="PREVIEW" AUTH_REQUIRED=true \
PYTHONPATH=<preview-shim>:. \
python -m streamlit run app.py --server.port=8601 --server.address=0.0.0.0 \
  --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false
```

- `PYTHONPATH` carries a **preview-only shim that is not part of the application**
  (`preview_only_shim.py` next to this document). It does two things:
  1. swaps `pymongo.MongoClient` for the in-process `mongomock` staging transport
     already declared for sandbox/preview in `requirements.txt`, and seeds one local
     staging user so the real login form renders;
  2. optionally **pins an artwork for Owner inspection**: `?bg=1..10`
     wrapper around `_current_login_bg_index`; with no `bg` parameter the shipped
     rotation function runs untouched.
  `core/auth.py` is **not** modified — the shim lives only in the preview process.
- Production DB: **not used**. Production secrets: **not used**. Production: **not deployed**.

## 4. Runtime acceptance (measured, not asserted)

Method: the artwork is re-laid-out at its computed rendered rect (`background-size`
+ focal `background-position`) on `#071019` and compared block-by-block (8×8 CSS px)
against the real browser screenshot; a dark scrim would appear as a systematic
offset, and the scrim alpha is solved directly from bright source blocks. Panel
transparency is proven by comparing a **UI screenshot** with a **background-only
screenshot** (form hidden) over every empty pixel inside the panel rectangle.

| Criterion | Result | Measured |
|---|---|---|
| `BACKGROUND_ART_IS_PRIMARY_VISUAL` | **YES** | block delta vs artwork median 0.4–3.0 / p90 ≤ 9.9 of 255; veil alpha ≈ 0.2–1.3 % |
| `FULL_SCREEN_DARK_VEIL_REMOVED` | **YES** | `background-image` = artwork data-URI only, no gradient; solved veil alpha ≈ 0.003 |
| `FORM_PANEL_NEAR_TRANSPARENT` | **YES** | `background: rgba(0, 0, 0, 0)`, `backdrop-filter: none`, `box-shadow: none`, `border: 0` |
| `BACKDROP_BLUR_REMOVED` | **YES** | `none` on every view measured |
| `LARGE_DARK_CARD_SHADOW_REMOVED` | **YES** | `none` on every view measured |
| `ART_VISIBLE_BEHIND_FORM_AREA` | **YES** | max channel delta 0 over 18 831 sampled empty panel pixels (portrait), 4 800+ desktop |
| `INPUTS_READABLE` | **YES** | contrast 7.91–18.31 (portrait 17.68 because the panel sits on the neutral colour) |
| `LOGIN_BUTTON_READABLE` | **YES** | 8.72 |
| `DESKTOP_USABLE` | **YES** | 1440×900: form + button fully visible, no horizontal overflow |
| `MOBILE_USABLE` | **YES** | 390×844 portrait: form + button fully visible, no horizontal overflow; 844×390 landscape: reachable with a normal 294 px scroll |
| `PORTRAIT_WHOLE_ARTWORK_VISIBLE` | **YES** | `background-size: contain`; full-width visible **7/7** artworks measured; rendered box 390×219.5 for 1672×941 art → aspect preserved, no distortion |
| `NO_STRETCH` | **YES** | single uniform scale (x = y); only `cover`/`contain` ever computed; no two-axis sizing |
| `LANDSCAPE_KEEPS_COVER` | **YES** | `cover` with the per-image focal position in all 7 landscape views |
| `ROTATE_BACK_PORTRAIT` | **YES** | one session, one artwork: portrait→landscape→portrait→landscape→portrait ⇒ `contain`→`cover`→`contain`→`cover`→`contain`, panel Δ = 0 at every step, artwork never changes |

### 4.1 Portrait fix, measured before/after (same artwork, same viewport)

| Artwork | Viewport | PR #101 head | PR #102 head |
|---|---|---|---|
| `login-bg-01` | 390×844 portrait | `cover`, visible **0.2601**, full width **no** | `contain`, visible **1.0**, full width **yes** |
| `login-bg-03` | 390×844 portrait | `cover`, visible **0.2601**, full width **no** | `contain`, visible **1.0**, full width **yes** |
| `login-bg-04` | 390×844 portrait | `cover`, visible **0.2601**, full width **no** | `contain`, visible **1.0**, full width **yes** |
| `login-bg-03` | 980×1743 (Desktop-site mode) | `cover`, visible **0.3164**, full width **no** | `contain`, visible **1.0**, full width **yes** |
| `login-bg-03` | 844×390 landscape | `cover`, visible 0.821, full width yes | `cover`, visible 0.821, full width yes (**unchanged**) |
| `login-bg-01` | 1440×900 desktop | `cover`, visible 0.9005 | `cover`, visible 0.9005 (**unchanged**) |

Desktop and landscape are numerically unchanged; portrait is the only behaviour that moved.

### 4.2 Captures

- [`evidence/contact_sheet_phone_portrait_390x844.jpg`](evidence/contact_sheet_phone_portrait_390x844.jpg) — 7 artworks
- [`evidence/contact_sheet_desktopsite_980x1743.jpg`](evidence/contact_sheet_desktopsite_980x1743.jpg) — 7 artworks (browser Desktop-site mode)
- [`evidence/contact_sheet_phone_landscape_844x390.jpg`](evidence/contact_sheet_phone_landscape_844x390.jpg) — 7 artworks
- [`evidence/contact_sheet_desktop_1440x900.jpg`](evidence/contact_sheet_desktop_1440x900.jpg) — 8 artworks
- [`evidence/rotate_sequence.jpg`](evidence/rotate_sequence.jpg) — portrait → landscape → portrait → landscape → portrait
- [`evidence/measurements.md`](evidence/measurements.md) · [`evidence/measurements.json`](evidence/measurements.json)

## 5. Owner real-device checklist (preview)

The Owner inspects these four states on the phone. Expected result at the exact
PR #102 head:

1. **Phone portrait (normal mobile mode)** — the *whole* artwork is visible, no
   stretching, nothing cropped left/right; the artwork sits as a band with the login
   form on the neutral colour above it; transparent form, readable inputs, no veil.
2. **Phone portrait with the browser set to "Desktop site"** — same as (1): the fix is
   owned by `orientation: portrait`, not by the 768 px width breakpoint, so the wide
   CSS viewport no longer keeps `cover`.
3. **Phone landscape** — full-screen `cover` as before, artwork bright and primary;
   the form is longer than the short viewport, so scroll down a little to reach the
   login button (reachable, not clipped).
4. **Rotate back to portrait** — `contain` returns immediately, the artwork does not
   change, nothing re-crops.

## 6. Regression boundary (PR #102)

| Boundary | Result | Evidence |
|---|---|---|
| 10 WebP assets | **unchanged** | identical Git blobs from PR #102's base to its head; sha256 recorded in `measurements.json` |
| Background rotation | **unchanged** | no diff in the rotation/session-key logic; runtime: rotation still picks different artworks across fresh sessions and keeps one artwork stable within a session and across login attempts; the preview-level `?bg=N` pin is **not** in repository code |
| Duplicate 09/10 handling | **unchanged** | `git diff 478eba2 b9f8f93 -- core/auth.py` touches only the CSS template (+17 lines); `_choose_login_bg_index` untouched |
| Auth decisions | **unchanged** | no change outside the CSS template string |
| DB | **unchanged** | `git diff --name-only 478eba2 b9f8f93` → `CHANGELOG.md`, `core/auth.py`, `tests/test_login_visual_compact.py` only |
| Secrets | **unchanged** | no `.streamlit/`, `.env*`, or credential file in the diff |
| Deployment | **NOT deployed** | preview only; production untouched |

## 7. Focused tests at this head

```
cd <checkout of b9f8f93>
PYTHONPATH=. pytest tests/test_login_visual_compact.py -v
```

Result: **25 passed** in 2.22 s (no skips, no deselections).

PR #102's base already carries the 20 tests merged from PR #101; PR #102 adds 5:

```
test_wide_default_keeps_cover_and_per_image_focal_position
test_portrait_viewport_fits_whole_artwork_with_contain
test_portrait_fit_does_not_depend_only_on_max_width_breakpoint
test_no_artwork_stretch_dimensions_anywhere
test_portrait_keeps_transparent_card_and_no_dark_veil
```

All 25 pass, and the same five properties were independently reproduced as **live
runtime measurements** in §4 (contain, per-image focal positions, no distortion, no
veil, transparent panel) — so the contract is held both statically and on rendered
pixels.

## 8. Honest limits / residual notes

- **No blocking defect found** in the PR #102 responsive implementation at this head.
  The items below are expectations the Owner should hold correctly while inspecting.
- **Landscape needs a short scroll** on a 390-px-high viewport. Measured: the login
  button first renders at y = 468 in a 390-px-high viewport, and the Streamlit main
  section scrolls 294 px to bring it fully into view. This is normal phone behaviour
  and satisfies "normal full-screen cover remains visually good"; it is *not* a
  clipping defect, but the Owner should expect to scroll.
- **Portrait artwork band is smaller than before.** `contain` means the 16:9 artwork
  renders as a full-width band (390×219.5 CSS px) instead of a zoomed crop, per the
  explicit acceptance rule *"whole artwork visible / no important left/right crop"*.
  On a very tall phone most of the screen is therefore the neutral `#071019`
  colour. The `center 85%` position puts the band under the form so the transparent
  panel reads against the neutral colour; `margin-top: 6vh` moves the form up
  accordingly.
- **`login-bg-05` is not a collage.** The Owner's "collage" background is drawn from
  the 4-panel artworks numbered 06, 07 and 08 (see the PR #101 contact sheets);
  artwork 05 is a warehouse interior. No code depends on this — only the artwork
  expectations of the reviewer — but it is worth correcting the written checklist.
- **`login-bg-09` and `login-bg-10` are byte-identical** (verified by Git blob and by
  pixel difference = 0). That is Owner-supplied art, unchanged by PR #101 or #102.

No code was changed for this preview task.
