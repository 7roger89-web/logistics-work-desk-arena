# LOGI-199 G2 — Journey map-first + Vietnam East Sea chart (N1 + N2 complete)

Scope: G2 Journey map-first canvas over the Owner-approved `component/src/assets/journey/vietnam-east-sea-chart.webp` (SHA-256 `f83d42167dffcb1ac629f261923408a2c6d5d6d7564cf63083aa869bababdef9`), symmetric main node row (`ROW_MAIN`), bottom-left `CHÚ GIẢI TRẠNG THÁI` legend, top-right floating `▤ HỒ SƠ & TÀI CHÍNH` trigger + utility bubble + whole-lot overlay, `node → bubble → task popup` (centered modal on desktop `1440×900`, bottom sheet on mobile `390×844`), and real write/readback verified on both desktop and mobile.

Capture: `capture_journey_flow.py` (Playwright + headless Chromium 153) against isolated staging app on `:9501` (`AUTH_REQUIRED=false`, `MONGO_URI=""`, mongomock).

| Oracle (`evidence/logi-199-g0/reference-html`) | Our capture (`evidence/logi-199-g2`) | Verification result |
|---|---|---|
| `ref-01-journey-initial.png` | `desktop-01-journey-initial.png` | Full-bleed `1440×900`; Vietnam / Biển Đông / Hoàng Sa / Trường Sa WebP rendered; `ROW_MAIN` centered at 50% vertical height; default fit zoom `95%` shows all 11 route nodes unclipped; bottom-left `CHÚ GIẢI TRẠNG THÁI (95%)` legend and top-right `▤ HỒ SƠ & TÀI CHÍNH` button visible. |
| `ref-02-node-bubble.png` | `desktop-02-node-bubble.png` | Dark-navy (`#10263C`) task bubble attached to selected node showing only that node's tasks + semantic status pills + `MỞ CÔNG ĐOẠN →`. |
| `ref-03-task-popup.png` | `desktop-03-task-popup.png` | Centered modal with `#10263C` header, `Công việc` / `Chứng từ` tabs, primary fields visible, secondary fields folded (`fact-fields-secondary`). |
| (save & reopen readback — desktop) | `desktop-04-after-save.png`, `desktop-05-reopen-readback.png` | Real write (`2026-10-03`) through dispatcher + reload/reopen readback confirmed (`readback_value = "2026-10-03"`). |
| `ref-05-finance-overlay.png` | `desktop-06-utility-bubble.png`, `desktop-07-finance-overlay.png` | Top-right `▤ HỒ SƠ & TÀI CHÍNH` opens `TIỆN ÍCH TOÀN LÔ` bubble and whole-lot `Tổng quan lô hàng` modal (`Tài chính` tab, VND/USD separated). |
| `ref-04-mobile-initial.png` | `mobile-01-journey-initial.png` | Mobile `390×844`: `vietnam-east-sea-chart.webp` rendered at `background-size: 100% auto` in upper half with zero aspect distortion and zero side cropping (`VIỆT NAM`, `BIỂN ĐÔNG`, `Quần đảo Hoàng Sa (Việt Nam)`, `Quần đảo Trường Sa (Việt Nam)` all visible); active route nodes visible below; `0px` horizontal overflow. |
| `ref-04b-mobile-node.png` | `mobile-02-node-bubble.png` | Mobile task bubble opens cleanly above selected node with `#10263C` header unobstructed (`z-30`). |
| (mobile sheet + save/readback) | `mobile-03-task-sheet.png` | Mobile bottom sheet (`0px` overflow); real write (`2026-10-04`) + reload/reopen readback confirmed (`mobile_readback_value = "2026-10-04"`). |

- Fonts: `Be Vietnam Pro` (400/500/600/700/800) and `IBM Plex Mono` (400/500/600/700) all `loaded` (`beLoaded: true`, `plexLoaded: true`).
- Persistence note: Isolated staging uses in-memory `mongomock`; readback across page reload within the running staging process is `PASS` (`2026-10-03` desktop, `2026-10-04` mobile), while a full OS process restart resets `mongomock` by design.
