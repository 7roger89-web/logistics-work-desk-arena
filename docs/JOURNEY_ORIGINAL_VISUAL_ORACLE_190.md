# LOGI #190 — ORIGINAL SAMPLE VISUAL ORACLE

Owner directive: **code 100% giao diện của ảnh mẫu gốc**.

This file makes that visual acceptance concrete. It does not create new business
authority. Current production facts/writers remain authoritative; this is the
layout/style oracle only.

## Source of truth

1. Owner-provided original reference screenshot in the 2026-10-08 review.
   Native image dimensions: **1536 × 1466**.
2. Approved Prototype-B donor code:
   - commit `70fd3610fdf9e2dacc7c5f7ac65440ad52e0ced7`
   - `docs/JOURNEY_DEMO_FIDELITY_176.md`
   - `tests/component/fixtures/journey_demo_b_geometry.json`
3. Current real data/action authorities on this branch.

If donor source and the screenshot disagree visually, the **Owner screenshot wins**
for visible composition. Donor source remains the implementation donor.

## Non-negotiable populated-desktop composition

At the reference desktop viewport:

1. compact shipment identity/header rhythm;
2. ONE attention strip directly above the Journey workspace;
3. main Journey row:
   - large left map;
   - fixed right Quick Panel;
   - no six-phase strip inserted above the populated map;
   - no extra populated map toolbar between attention and canvas;
4. map:
   - dotted canvas;
   - 164×136 node cards;
   - approved positions from `DEMO_POS`;
   - SI/VGM + Gate-in parallel group;
   - start and neutral end marker;
   - fit/zoom/reset lower-left;
   - status legend lower-right;
   - interaction hint upper-right;
5. right panel:
   - current/problem node shown by default;
   - one dominant action;
   - factual information below;
   - one bottom workspace CTA;
6. lower rail:
   - exactly five compact work cards in one desktop row:
     1. BOOKING – ĐẦU ĐI
     2. TÀU ĐẾN – CHẶNG CHÍNH
     3. NHẬP KHẨU – ỦY THÁC
     4. GIAO HÀNG
     5. HỒ SƠ & PHẠM VI
   - same visual language: numbered badge, title/status, four compact tabs,
     dense read-only information;
   - facts come from current authorities, never demo mock values.

## Current donor constants that must stay exact unless the screenshot requires otherwise

From the approved Journey map:
- node width: **164 px**
- node height: **136 px**
- horizontal pitch: **212 px**
- canvas x padding constant: **48 px**
- populated canvas logical height: **690 px**
- default side panel width: **420 px**
- populated Journey split height: **760 px**

These are geometry authority, not suggestions.

## Later features must not distort the default first screen

Keep the capability but move it behind interaction:

- six-phase mental model:
  - required for truthful fresh/zero-node onboarding;
  - must NOT create a permanent populated phase strip when the original sample has none.
- Completion Goals:
  - derived/read-only;
  - collapsed by default;
  - explicitly NOT fields required at shipment creation;
  - expanded on demand.
- Global Workspace:
  - when opened, automatically collapse the map to the existing rail;
  - never squeeze full production forms into the 420px Quick Panel.
- Work Modules:
  - remain accessible;
  - must not permanently push the approved map/panel composition down unless actually present and operator-expanded.

## Fresh zero-node exception

The original screenshot is a populated shipment. It is **not** authority to fabricate
nodes on a fresh shipment.

For `journey.nodes=[]`:
- preserve the same Journey shell visual language;
- HỒ SƠ is the one actionable phase;
- downstream phases remain UNKNOWN;
- use a compact canvas, not the populated 760px empty area;
- right onboarding Quick Panel remains;
- no fake Booking/SI-VGM/Customs/Delivery nodes.

## Shipment list screenshot comments

- Urgency indicator must be driven only by canonical Attention bands.
- BLOCKING/OVERDUE: small red pulse dot + restrained red surface.
- DUE_SOON: static amber.
- no whole-row/text blinking.
- responsibility line:
  - `Phụ trách` = canonical shipment owner (`s.sale`);
  - `Cập nhật bởi` = `updated_by`, secondary only.

## Visual acceptance — no “looks close”

Writer must provide real-browser evidence at the same reference viewport.

Required:
- populated desktop candidate;
- original/reference reconstruction;
- side-by-side;
- overlay/diff;
- populated 390px;
- fresh desktop;
- fresh 390px;
- Completion Goals collapsed/expanded;
- Global Workspace after map auto-collapse;
- list urgent/non-urgent comparison.

FAIL if there is an intentional mismatch in:
- block order;
- map/panel ratio;
- card geometry;
- spacing/radius/borders;
- typography hierarchy;
- control placement;
- lower five-card rail;
- default visible density.

Dynamic text/value differences caused by truthful production-shaped fixture facts must
be listed separately and are not permission to change layout.

## Truth invariants that visual fidelity may not violate

- declaration registration != customs clearance
- generated GNT != tax paid
- UNKNOWN != 0
- suggested catalog partner != established payable
- no fake FX/cross-currency total
- upload != business completion
- B7 end-of-map marker is not whole-shipment CLOSED
- B8 finance UNKNOWN remains UNKNOWN
- fresh zero-node Cockpit remains
- profile CTA still reaches existing Execution Profile

## Stop rule

No merge/deploy until:
1. exact-head source/build/test evidence;
2. real-browser visual evidence against this oracle;
3. fresh independent Supervisor PASS;
4. Owner production gate.
