# 01 — WRONG_PASS on the pristine head (`6934f4b1`)

Runtime: real Streamlit app at `/home/user/pr255` (exact pre-fix tree), Chromium
153.0.8010.0 via Playwright, `http://127.0.0.1:9517/`.
Raw: `results/return-nav-baseline-{A,B,C,D,E}.json`.

## What the operator sees today

| Test | Baseline verdict | Observed |
| --- | --- | --- |
| **A** `q="LO-0"` → debt cluster → return | **FAIL** | control `present=false`; `q "LO-0" → ""`; rows `[LO-0299, LO-0306, LO-0307, LO-0308, LO-0295] → []`; summary after “return” `Tìm thấy 0 lô` |
| **B** status + period(khác, from/to) + archive → return | **FAIL** | no control; all five params lost, rows `[…] → []` |
| **C** native Chrome Back | **FAIL** | `history_before=2`, `history_on_detail=2` (opening a lot adds **no** history entry — MemoryRouter), URL never changes, `url_after_back="about:blank"`, `blankPage=true` |
| **D** entry from Tổng quan (no list history) | **FAIL** | no control to even measure |
| **E** control present 1440x900 / 390x844 | **FAIL** | no control to measure |

So the WRONG_PASS is confirmed on the real app, in a real browser, with real
filters: **the operator cannot get back to the filtered list at all** — not with a
control (there is none) and not with Chrome Back (which lands on `about:blank`).

Screenshots: `shots/nav-A-baseline.png`, `nav-B-baseline.png`,
`nav-C-native-back-baseline.png`, `nav-D-other-entry-baseline.png`,
`nav-E-desktop-baseline.png`, `nav-E-mobile-baseline.png`.

## Root cause

`component/src/App.tsx` mounts a **`MemoryRouter`**. Consequences:

1. In-app navigation to a record creates **no history entry** and never changes the
   URL → Chrome Back walks out of the app (here: `about:blank`).
2. `/lo-hang` keeps its filters in its **own search params** (`useQueryParam`), and
   **nothing carried them to the detail screen** — the detail screen is a sibling
   route with no knowledge of the list's location, and had **no back control** at all.
   The list's `q`/`status`/`period`/`from`/`to`/`archive` therefore died with the
   list instance.
