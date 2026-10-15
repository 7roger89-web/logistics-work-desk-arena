# LOGI-199 G2 — Journey map-first (evidence)

Scope: Journey only (map-first canvas, node → bubble → task popup, save/readback). Not whole-app VISUAL_PASS.

Capture: `capture_journey_flow.py` (Playwright + @sparticuz/chromium), against isolated staging app on :9501 (AUTH_REQUIRED=false, mongomock).

| Oracle (evidence/logi-199-g0/reference-html) | Our capture (this folder) | Note |
|---|---|---|
| ref-01-journey-initial.png | desktop-01-journey-initial.png | Map-first OK; main row sits lower than ref; default zoom 85% vs 100% in ref |
| ref-02-node-bubble.png | desktop-02-node-bubble.png | Bubble attached to real node, only that node's tasks |
| ref-03-task-popup.png | desktop-03-task-popup.png | Centered modal, primary fields first, extras folded |
| ref-04-mobile-initial.png | mobile-01-journey-initial.png | Map-first at 390×844, zoom bar above tab bar |
| ref-04b-mobile-node.png | mobile-02-node-bubble.png | Bubble below node when node is near top; zoom top-right |
| (save & reopen) | desktop-04-after-save.png, desktop-05-reopen-readback.png | Saved value read back: 2026-10-03 |
| (mobile sheet) | mobile-03-task-sheet.png | Bottom sheet, 0 horizontal overflow |

Fonts: Be Vietnam Pro and IBM Plex Mono FontFace reported `loaded`.
Not verified: pixel diff, process restart between save and reopen, mobile save click.
Visual fidelity status: FAIL until Owner review of the comparison.
