# CONTROL_TOWER_RETURN_PACKET

## Identity / status

- **PROJECT:** `7roger89-web/logistics-work-desk-arena`
- **GOAL / ISSUE:** `LOGI-APP-RENEWAL-01` / #199
- **BRANCH:** `arena/7d8e8372-logistics-work-desk-arena`
- **New, single Draft PR:** [#208](https://github.com/7roger89-web/logistics-work-desk-arena/pull/208)
- **Tested product + primary evidence commit:** `ecf6c88da6523028195918e1440cc3b413bfad7c`
- **Base:** `arena/18ef00cf-logistics-work-desk-arena` @ `7a73e484446bf8ab79f405125d6ba0589e8ab56a`. **#207 remains OPEN/Draft, head/base unchanged.** No other old branches/PRs mutated.
- The follow-up on this same branch only pins this packet, current goal state, publication receipt and manifest; product/dist bytes remain those tested above.
- **INITIAL_PLANNING_CLASSIFICATION=UIUX; FINAL_ROUTING_CLASSIFICATION=UIUX**
- **FULL_GOAL_199=IN_PROGRESS; PRODUCTION_READY=NO**

## Actual tested flow

Real existing React/Streamlit app, genuine Sale UI login, `AUTH_REQUIRED=true`, no shell before login, **isolated Mongomock only**.

**Both 1440×900 and 390×844:** Home → click backend-authoritative `/lo-hang/FLOW199-FCL?tab=van-tai&stage=si-vgm&work=info` → correct shipment and SI/VGM popup → map → selected node → task/document bubble → correct short stage popup → edit on-board value → actual Save → full page reload → navigate back → UI **and independent canonical DB/audit** readback.

- #207 rendering gap closed for the tested Home: attention **132.625 px** vs sibling **473.171875 px**, `align-items:flex-start`. Mobile shell overflow **0**.
- Export/main-carriage fixture: **9 applicable nodes**, nautical-paper map and SI/VGM ∥ gate-in preserved. Additional existing full-scope T6-FCL: **11 nodes** retained.
- Linked customer `CUST-ANPHAT` preserved; no customer reselection required.

| Viewport | Actual distinct edit | Version | Audit / reload |
|---|---|---|---|
| Desktop | `2026-10-04 → 2026-10-05` | `1 → 2` | +1, `flow199.sale` / `sale`; UI + DB readback PASS |
| Mobile | `2026-10-05 → 2026-10-06` | `2 → 3` | +1, same Sale actor; UI + DB readback PASS |

No unrelated sea fact changed. Same-process/page-reload persistence only: **production/Atlas durability is NOT claimed**.

## Demonstrated defects / bounded repairs

1. **Manual-task route:** finance/import/pickup tasks were all hardcoded to `?tab=lay-hang`. Their schema has no stage authority. Both existing projections now open the task's **own encoded shipment map**, explicitly say **“Chưa gắn công đoạn”**, and show that reason on mobile. No text heuristic or unrelated primary-action substitution. Existing task deadline/owner/priority/manager UNKNOWN metrics retained.
2. **Document scope:** SI/VGM popup offered customs/transport/booking as well as SI/VGM. Now it uses only the selected node's exact categories; explicit `[]` stays empty, undefined remains whole-lot.
3. **Global work leaking into a node:** the on-board popup showed the whole-lot “Thiếu 3 thông tin”. Existing scope guards now keep global missing-info and sticky actions outside stage popups. Global checklist/finance remain accessible once in whole-lot workspace.

Only four product source files changed plus synchronized JS dist. **Map geometry, business writers, schema, auth/RBAC, finance authority and product dependencies unchanged.**

## Verification / evidence

- Typecheck / official build / scan: **PASS**, executable process references **0**; CSS byte-identical.
- Routing + Attention + manager regressions: **23 PASS**.
- Current compiled-bundle node/file/category scope DOM check and existing Home layout DOM check: **PASS**. Negative task-content/encoded-ID/untrusted-route cases and category/file sentinels included.
- Wider related Python selection: **95 PASS / 6 existing FAIL**. Initial broader pre-edit baseline: **131 PASS / same 6 FAIL**, a different selection. Five pre-existing profile-route expectation mismatches and one existing zero-node JSDOM timing/render lane; no blanket skip/deletion. **Not an all-green suite.**
- Real browser: **PASS**, both viewports, both distinct saves/reloads, 11-node read-only guard, zero page errors.
- GitHub readback: published source/dist/result blob IDs **match local tested files**. Own #208 verified OPEN/Draft; #207 unchanged. **No CI checks reported** at the tested commit; no CI PASS claim. Independent external review **NOT_RUN**; Owner UAT **NOT_RUN**.

**Evidence:** [README](README.md), [raw browser result](result.json), [provenance](provenance.json), [GitHub readback](github-published-readback.json), [integrity manifest](manifest.sha256), `readback/`, `logs/`.

**Real screenshots, opened and inspected:**
- Home: `after/desktop-home.png`, `after/mobile-home.png`.
- Correct Home target: `after/desktop-home-fcl-target.png`, `after/mobile-home-fcl-target.png`.
- Preserved map: `after/desktop-fcl-initial.png`, `after/mobile-fcl-initial.png`, `after/desktop-t6-full-scope-map.png`.
- SI documents before/after: `before/desktop-si-docs.png` → `after/desktop-si-docs.png`.
- Save/reload: `after/desktop-on-board-reloaded.png`, `after/mobile-on-board-reloaded.png`; edited-state images and independent DB snapshots also retained.
- Unknown T6 node: `after/mobile-t6-on-board-popup.png`; global missing-info 3 still retained outside the stage.
- Exact Owner HTML oracle rendered at both sizes in `reference/`. Design oracle only, not business-data authority.

**Browser boundary:** Chromium 141.0.7390.0 / temporary Playwright 1.56.1. Missing NSS/NSPR resolved with locally extracted bundled libraries and runner-only `LD_LIBRARY_PATH`; no OS/product dependency or browser web-security change. **VISUAL_VERDICT=BOUNDED_RENDERED_PASS**, not full pixel parity or whole-app acceptance. Test server **stopped** after capture; no Owner Python/ZIP/CMD/screenshot task.

## Unfinished / next

- **Exact-stage navigation for unbound legacy manual tasks remains incomplete**: their current data cannot honestly identify a stage. Correct-shipment fallback is not exact-stage completion.
- Broader #199 mode coverage, six existing test gaps, independent review and Owner UAT remain open.
- No main merge, production data/config change, deployment, public hosting or auth bypass.

**Single highest-value next step:** establish an authoritative stage binding for manual tasks and verify Home → exact node for finance/import tasks **without inferring from free text**.

**Không bị over engineering chứ?** Existing route/scope guards and canonical writer are the simpler path; three reproduced defects and two real readbacks are material progress; every source change was necessary; the core flow preceded this one evidence checkpoint; broader refactoring/schema design was deferred. **OE_VERDICT=DO_IT** for this bounded slice.

**P2P_LAW_SOURCE=LOCAL_PORTABLE**; own AGENTS/law/active-experience/required skill receipts were issued. No Control Tower receipt was inherited as current-source proof.
