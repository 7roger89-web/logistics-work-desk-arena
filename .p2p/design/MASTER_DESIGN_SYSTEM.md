# MASTER DESIGN SYSTEM — LOGI-APP-RENEWAL-01
Status: `OWNER_DIRECTION_APPROVED / IMPLEMENTATION_PARTIAL / RUNTIME_VISUAL_QA_PENDING`
Authority: Owner message 2026-10-14; goal [#199](https://github.com/7roger89-web/logistics-work-desk-arena/issues/199).
Approved visual donor: `logi_journey_mimo_sonnet_fusion_demo.html`, SHA-256 `d400c2769a40df604d9b2037a2909f55813a74aa2f6d22b6567664557fb8579d`. Donor governs *look and interaction language*, **not business state**.

## Screen contract
The entire visible Logistics Work Desk shares the same font, palette, hierarchy, button/field, cards, status language and popup geometry. **This does NOT mean every screen should contain a map.**
- Entry/Home: who needs attention and next action (not decorative overview first).
- Shipments: dense scan-friendly table with query/status and direct links.
- Shipment detail: compact five macro phases per [#197](https://github.com/7roger89-web/logistics-work-desk-arena/issues/197); detailed evidence-backed Journey drill-down; phase-only docs/actions; finance belongs to final macro-phase. Never let route/transport background dominate above critical attention.
- Sales quotation and contract: short primary fields, optional details behind `Xem thêm`; document and price precision unchanged.
- Customers, partner, control tower, finance/reconciliation: readable tables and record details; one obvious primary action, no unsolicited workflow navigation.
- Reference utilities, library, policies, tariff and admin: same shell, typography and controls; domain-specific content remains intact.
- Authentication: consistent visual family, but DO NOT weaken or rework the auth boundary to restyle.

## Visual tokens (captured from donor CSS and demo status metadata)
| Role | Token | Value |
|---|---|---|
| Vietnamese UI | `font.sans` | `Be Vietnam Pro`, system fallback |
| Exact codes/technical identifiers | `font.mono` | `IBM Plex Mono`, system-monospace fallback |
| Main text | `color.ink` | `#10263C` |
| Deep navy | `color.navy` | `#123A5E` |
| Action/link blue | `color.blue` | `#1D6FA8` |
| App canvas | `color.canvas` | `#EDF1F5` |
| Surface | `color.surface` | `#FFFFFF` |
| Border | `color.border` | `#D6DEE7` |
| Muted text | `color.muted` | `#5B6875` |
| Success/evidence | `color.success` | `#2F7D5E` |
| Waiting | `color.warning` | `#C97A16` |
| Blocker | `color.danger` | `#B4402F` |

Typography: normal text **14–16px** unless density warrants a justified local exception; headings 18–24px, captions normally >=12px; touch controls ~44px target; dark text on legible background; focus visible; reduced-motion respected. Numeric tables keep tabular alignment. Semantic states always include label+icon as well as color.

## Architecture/reuse limits
Production is **Streamlit Components v2 -> existing shadow-root React shell**: `views/logi_shell.py` loads `component/dist`, `component/src/index.css` and `component/src/shell.css` already hold the existing visual foundation. Reuse `components/ui.tsx`, `Layout.tsx`, current Tailwind and existing tokens FIRST; do not add a second UI library, root, framework, global CSS reset or workflow renderer. Note: `index.css` already uses Be Vietnam Pro globally but `.journey-demo` explicitly overrides it with Inter. Apply typography correction at the owning selector, not by piling `!important` on every page. New colors should be incrementally mapped into existing primitives/screens rather than blindly rewriting hard-coded production color classes.

No changes to generated Word/Excel files, legal records, storage formats or financial data. No external design/font files uploaded through this contract.

## Readability and runtime acceptance
- Screenshot and interaction proof at 1440×900 and 390×844 on the **real app build**, for each materially affected route; no mobile horizontal overflow.
- Inspect long Vietnamese labels, data-dense tables, popup keyboard/focus, action loading states, empty/UNKNOWN, finance rounding and error copy.
- Evidence levels: `SOURCE_REVIEW` is not `RUNTIME_VISUAL_REVIEW`. A demo screenshot does not certify the production shell.
- No production business writes during visual smoke. An accepted PR cannot auto-merge to `main` without explicit production Owner Gate because `main` is linked to deployment.
- Close exactly the scope required by goal #199 and stop; extra animation/brand overhaul is deferred.

## Delivery dependencies
Visual foundation may be prepared in parallel, but replacing all screens awaits the mode-aware Journey task/data contract. Existing #197 is not rebuilt here. Unknown customer identity, country of customs, carrier event, package condition, delivery and finance values remain UNKNOWN until confirmed.
