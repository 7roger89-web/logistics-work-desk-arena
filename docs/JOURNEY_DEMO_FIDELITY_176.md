# Journey demo fidelity — Issue #176 follow-up

## Contract and scope

The owner's October 4, 2026 instruction supersedes the earlier diagnosis-only
lane for this implementation: clone the previously approved shipment Journey
map into the app and connect its current processes. Issue #160 remains the
three-layer contract: Journey Map → Quick Panel → Stage Workspace. Prototype B
provides geometry and composition; canonical app projections, dispatcher,
permission checks and fresh backend readback provide business behavior.

Baseline: `7roger89-web/logistics-work-desk-arena@main`
`ab5131092c6f29a34d9fbbef3a61da7ae7f2c882`. No backend, schema, secrets or
production data changes. No Community Cloud reboot or deployment performed.
`PRODUCTION_WRITES=0`; `TIENTHANHLOG_TOUCHED=NO`.

Original approved ZIP B SHA-256:
`cfe20232afcd8c0872825658378d08d428f9f5525a6642fa629a457718673cac`.
The geometry fixture records the original JourneyMap source hash and the two
ID adaptations (`sivgm` → `si-vgm`, `onboard` → `on-board`). It was extracted
from the reference source independently of the implementation.

## Implementation

- Restore demo B's 164×136 cards, exact canvas positions, parallel SI/VGM and
  Gate-in group, merge into ETD, downward On-board edge and return row.
- Restore fit, zoom, pan, reset, drag-click guard, current/blocker badges,
  grid background, selected outline and status legend.
- Restore the right-hand Quick Panel, replaced by Stage/Global Workspace
  for real app work; restore map collapse and a stage rail.
- Reuse the current Sea Export facts, document, finance, history, shipment
  process and module attach/step controls. Module rollups remain compact and
  show steps on demand. Scoped journeys use projected nodes/edges only.
- Retain canonical states, owner, actual attachments and authoritative primary
  action. Unknown evidence is never completion. Prototype mock data, finance
  and completion engines are not copied. Terminals are presentational; the
  final terminal becomes green only when projected stages/modules are done.
- Keep the existing app shell and use a stacked map/panel on small screens.
  This adaptation is not claimed to be an exact mobile copy of the prototype,
  whose original shell requires a minimum 1100px width.

## Evidence and limits

`P2P_LAW_SOURCE=CANONICAL_AUTHENTICATED`
Canonical source SHA-256:
`316936bc951a466c89cc8efb9291f9425571cf886199c8f4f4372be5d7c25ae4`.
`OE_VERDICT=DO_IT`: reuse the approved geometry and existing app process
components; no additional engine, store or backend model.

Passed in the isolated QA environment:

- TypeScript typecheck; production Vite build; process scan reports zero
  executable process references. Two consecutive builds produce identical
  JS and CSS bytes. Package manifests and lockfile are unchanged.
- 52 focused Python tests: visual shipment workspace and work module library.
- Existing #160 DOM acceptance: stage selection, scoped real work, bounded
  dispatch, pending/refusal behavior, canonical fresh readback, documents,
  finance/history navigation, viewer permissions and global escape.
- Existing #162 DOM acceptance: scoped seven-node base map, module gates,
  on-demand steps, backend-confirmed completion, refusal, viewer permissions
  and bounded attachment/library behavior.
- New demo fidelity DOM acceptance against the built production bundle:
  eleven reference positions, exact parallel edge paths, panel placement in
  the DOM, fit/zoom/pan/reset, drag guard, all node selections, collapse and
  global work navigation; navigation emits zero business writes.
- Negative challenge: the same reference test rejects the pinned old main
  bundle at `booking: approved demo B geometry`. Existing node-count tests
  alone did not protect this property.

All backend fixtures use the existing harness, which asserts isolated
`SANDBOX_TRANSPORT` before any fixture write. Fixture writes are not production
writes. DOM tests mock viewport dimensions for transform mathematics and do
not prove browser CSS layout, screen-reader behavior or screenshot similarity.

**Verdict: INCOMPLETE for visual/release acceptance.** The cloud browser blocked
the localhost preview (`ERR_BLOCKED_BY_CLIENT`) and rejected local-file
navigation by URL security policy. No workaround was attempted. A real-browser
desktop/mobile visual comparison, actual form fit in the side pane and a fresh
authenticated thu-log read-only production smoke remain unverified. Do not
report this PR as pixel-identical, deployed or production-smoke PASS.

Project experience candidate: preserve an immutable approved-demo geometry
oracle alongside behavioral acceptance; node counts and writer readback do
not establish layout fidelity. Advisory only; no automatic promotion.
