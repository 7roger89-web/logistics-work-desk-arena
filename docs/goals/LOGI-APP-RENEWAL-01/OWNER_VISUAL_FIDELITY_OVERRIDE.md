# LOGI-199 — OWNER VISUAL FIDELITY OVERRIDE (15/10/2026)

**STATUS=OWNER_CORRECTION / DESIGN_AUTHORITY**. This supersedes incompatible *visual and default-layout* decisions in Issue #199, prior master-design contract, Issue #197, PR #198, and any earlier inspector PASS. It does not supersede authenticated business/data/security invariants or Owner release gates.

## Exact Owner-approved source
- Reference file (bytes saved unmodified): [logi-journey-mimo-sonnet-fusion.html](../../reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html) — actual repository root path `reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html`.
- Uploaded source size = **866,917 bytes**; uploaded SHA-256 = **26e2e5cf81db1d991a9442872cfde1b7b6a7726e8f0832c76e23a52189c3647f**. This is the **new, exact** Owner file (not the prior donor with a different hash).
- The reference is **visual + interaction authority only**, not canonical business state, not a production component bundle. Embedded chart-paper JPEG is part of this HTML. Standalone HTML declares Be Vietnam Pro and IBM Plex Mono in CSS but has **no @font-face/import**: the executor must load actual legitimate assets and verify rendered font faces in the real app, not copy a fallback screenshot or claim style declaration equals font loaded.

## Why #199 has missed the Owner outcome
The visually approved standalone demo is a **large, paper-chart Journey canvas** with a slim horizontal vessel-style information/status toolbar, small flow nodes connected on a route, node-attached task bubbles and short task dialogs. On mobile the map remains the primary navigable canvas with pan/zoom, overlays/sheets and compact chrome.

The integrated current UI instead uses a `340px` dotted background mini-map (`.journey-split-small-map .journey-canvas { width: 340px; }`) plus dominant generic white workspace cards and the generic app shell. 100% initial zoom fixed readability of one cropped node, **not the reference composition**. 21 route overflows=0, fonts loaded, and all CI tests green for a focused subset are NOT full-app visual parity.

## Mandatory design authority (source, not generic interpretation)
1. **Journey is map-first by default**, matching the attached screenshot/layout/flow proportions and chart-paper texture. No default 340px mini-map/split-dashboard or forced five macro-cards ahead of the map. Use the existing five macro logical groupings for orientation and stage scoping where useful, but they must not displace the approved detailed Journey map. Keep zoom/pan/Fit and active node clarity.
2. **Node -> nearby compact task bubble -> task-specific popup**. Bubble contains only that node's tasks + relevant Work Modules. Popup starts with the small set of essential fields; `Xem thêm chi tiết` folds extras; evidence, owner, deadline, validation and completion reason remain accessible. Modal desktop and bottom-sheet mobile match the donor proportions and focus behavior.
3. **App-wide visual family** across every real route and state: compact top chrome/identity/status, Be Vietnam Pro body/UI, IBM Plex Mono codes/small technical labels, colors `#10263C` ink, `#123A5E` navy, `#1D6FA8` blue, `#EDF1F5` background, `#D6DEE7` borders, `#FFFFFF` surfaces, semantic red/orange/green; matched corner radii, chip microtypography, spacing, border weights, shadows, buttons, filters, tables, popovers, panels, dialogs and empty states. Reuse existing React shell/components; do NOT put a fake shipment map on finance/contracts/customer/admin routes. Adapt the donor's visual grammar to each route's actual work.
4. **Visual priority:** default hierarchy, real visible font, node proportions/positions/edges, paper background, panel geometry and interaction placement matter **more** than ticking token, CSS, no-overflow or test-count checkboxes. Tiny chip metadata in the reference may remain compact when readable; do not forcibly enlarge every label or make every page generic white cards under a universal 12px assertion.
5. **Mobile**: preserve the donor's map-first composition, pan/zoom with touch, unclipped quick overlays and task bottom sheets, accessible controls; do not merely stack a 620px map above a 720px generic dashboard. Test at desktop 1440x900 and mobile 390x844.

## Non-negotiable real-app invariants
- Reuse core shipment/truth/doc/work-module/finance APIs and data. Preserve SEA FCL/LCL, AIR direct/consolidated, ROAD FTL/LTL mode-correct regressions; never copy mock shipment state from HTML donor.
- UNKNOWN != 0/done; booking request != confirmed; ETD != ATD/on-board; declaration != customs clearance; file upload != stage completion; suggested partner != payable; GNT != paid; no fabricated FX or timestamps.
- Existing customer binding is not re-requested. Phase/stage documents and tasks appear only where relevant; costs/finance remain in the whole-lot/last logical group, not repeated on every node.
- No silent changes to auth/RBAC, production DB, back-office finance, export DOCX/XLSX typography or record formats. No production-linked main merge/deploy without Owner authorization.

## BIG GOAL execution, bounded visual slices

**G0 — Baseline and authority lock**: read exact HTML from the pinned repository path; run it in browser; capture desktop/mobile **initial, node bubble, modal, finance overlay** as immutable design oracle. Inventory all active routes (including record-detail routes, modals, financial/admin states, mobile). Capture *before* screenshots from latest integrated app. Build a screen-by-screen gap matrix (layout, typography loaded, colors, spacing, popup, mobile, interactions). Revalidate future screenshots against this oracle. If the reference cannot actually be opened, BLOCK visual work rather than guess.

**G1 — Shared shell and primitives**: implement compact top chrome, typography, palette, buttons, fields, chips, cards, popups, sheet/drawer and interaction styling in current `Layout.tsx`, existing `ui.tsx`, `index.css`, `shell.css`; avoid a second design system/library and conflicting `!important` overrides. First demonstrate Home, Shipments List, and Quotes or Finance *with actual app data* and compare before/after; do not stop until matched or provide concrete mismatch evidence.

**G2 — Journey anchor (highest fidelity)**: replace small-map default with full/multi-dominant paper-map composition from donor, real mode-aware nodes/edges, floating node tasks and matched modal. Keep booking/evidence/write-readback; selected task must filter stage docs; 5 macro labels only secondary orientation; preserve conditionally applicable logistics stages. Show desktop/mobile before/after and at least one real node -> bubble -> popup -> save/readback.

**G3 — All operational/business routes**: Home, dashboard/Operations, Shipments, Create Shipment, Customer/Playbook, Partner, Quotes, Contracts/new/detail, Receivables, Partner Payables, Reconciliation, CEO reports. Same donor skin, dense tables remain usable, each real route visual checked.

**G4 — All tools/admin/detail states**: BIỂU THUẾ, Tra cứu chính sách/NotebookLM, Translation, Intl Payments, Notebook, Work Modules/Process Library, Templates/Docgen, User Admin, not-found, dialogs/toasts/empty/errors, every record-detail page. Real routes + material modal states both viewports. Avoid rendering every route as a map.

**G5 — Integrated visual comparison and final Owner UAT**: visual reviewer must inspect **side-by-side current screenshot versus actual donor** for Journey initial/bubble/modal + representative shell, and screen-by-screen consistent design family for each other route; use pixel/layout diff as aid, not sole criterion. Chrome real Streamlit build (not static HTML), 1440x900 and 390x844, visible text, opened controls, FontFace.loaded, stage-specific interaction and zero overflow. Run existing business regression / DOM / typecheck / Vite / dist / CI, log full-suite pre-existing failures separately. Gate Owner UAT on a preview Owner can open. Reviewer may PASS scoped code/runtime while VISUAL_FIDELITY remains FAIL; no visual acceptance by CI alone.

## Scope / delivery rules
- This is **UI-first corrective BIG GOAL**; T1–T4 business code already built is to be preserved and only adapted for visual UI, NOT reimplemented or rewritten from scratch.
- Use **one** #199 goal and this explicit override; do not open parallel conflicting design authorities. Existing PR #198/#200–#204 remain draft until reconciled. Create isolated visual correction work branch/PR, never merge/deploy production without permission.
- Every slice produces screenshots *before and after*, code and regression, real build receipt, and concise `GOAL / PROGRESS / CURRENT / NEXT / BLOCKERS`. Continue automatically between slices; stop only for genuine Owner design decision, security/production authority, blocked source, or session exhaustion with durable checkpoint.
- `OE_VERDICT=DO_IT`: smallest path is reuse existing React app, donor visual oracle and current CI; avoid a new framework, giant redesign rewrite, new workflow engine or decorative animation campaign.
