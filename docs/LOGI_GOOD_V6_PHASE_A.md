# LOGI-GOOD V6 — Phase A Recovery (Literal Component)

Durable checkpoint for `LOGI_GOOD_LITERAL_COMPONENT_V6_RECOVERY` (Phase A only).

## Owner outcome

The visible Logistics product uses the **LITERAL Logi-good frontend** — not an
approximation. `OUTER UI/UX = LOGI-GOOD`, `INNER DATA = current real Logistics
app` (sandbox seed in Phase A).

## Architecture (proven in Phase A)

```
Python Logistics view-model            (views/logi_view_model.py, sandbox seed)
   → ONE Streamlit Components v2 root  (st.components.v2.component, views/logi_shell.py)
   → literal Logi-good React UI        (component/dist build of the donor source)
   → typed v2 component events         (setTriggerValue: shipment_update | navigate)
   → ONE bounded Python dispatcher     (views/logi_view_model.consume_triggers)
   → existing real writers (LATER, Phase B)
```

- **Single component root.** The entire visible shell + active page lives in ONE
  `st.components.v2` component. No components.v1, no iframe, no postMessage
  bridge, no query-param bridge, no synthetic popstate.
- **Literal donor reuse.** `Layout.tsx`, `ui.tsx`, `Home.tsx`, `Tasks.tsx`,
  `Shipments.tsx`, `ShipmentDetail.tsx`, `index.css` are byte-identical to the
  donor reference (`design_reference/logi-good`). The only donor edit is one
  router line in `Home.tsx` (`window.location.href` → component-local
  `useNavigate`) — an allowed router adaptation.
- **Router = component-local route state.** `BrowserRouter` → `MemoryRouter`;
  donor routing API (`Link`/`NavLink`/`useNavigate`/`useParams`/`useSearchParams`)
  is unchanged. Ordinary navigation never requires a Python rerun. Route and
  active tab survive a backend/view-model rerender (verified).
- **Missing donor lib contracts** (`lib/data`, `lib/store`, `lib/format`) are
  provided as supporting contracts; the view-model is fed from the Python
  `data` channel instead of baked-in mock data.
- **Phase A scope** = Global Layout + Home + Tasks + Shipments + Shipment Detail
  (all five donor tabs). Secondary destinations render a bounded
  "chưa triển khai Phase A" state; the shell/navigation stays donor-identical.

## The `process is not defined` fix (the critical known failure)

The component JS runs in the **browser DOM**, never Node. The prior local
Phase A failed at Preview with `BidiComponent Error: process is not defined`
because the vendor bundle referenced Node globals.

Fix, at BUILD TIME via the bundler's `define` mechanism (`component/vite.config.ts`):

- `process.env.NODE_ENV` → `"production"` (statically resolved; React ships the
  production build).
- Any remaining bare `process` identifier (react-dom's `typeof process`
  error-report fallback) → `void 0`. The reference is `typeof`-guarded in
  source, so `typeof (void 0)` keeps the branch inert. **No runtime polyfill is
  injected** and **no environment variable / secret is exposed**.

Gate: `scripts/scan_process.py` enforces
`FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0` on the built bundle (checks
`process`, `process.env`, `process.env.NODE_ENV`, `global.process`, `Buffer`,
`require(`, `__dirname`, `__filename`, excluding inert string literals).

## Files

| Path | Purpose |
| --- | --- |
| `component/src/**` | Literal donor UI + supporting lib contracts + v2 entry |
| `component/src/component-entry.tsx` | v2 mount (`export default function(component)`) |
| `component/src/lib/viewmodel.ts` | View-model contract + live holder |
| `component/src/lib/dispatcher.ts` | The ONE bounded event dispatcher (JS side) |
| `component/src/lib/store.tsx` | Donor `useStore` over the view-model |
| `component/src/lib/data.ts` | Donor `lib/data` (live arrays from view-model) |
| `component/src/lib/format.ts` | Donor `lib/format` (cx/fmtMoney/fmtVND/download) |
| `component/vite.config.ts` | Browser-only build + `define` (process fix) |
| `component/dist/logi-shell.{js,css}` | Built browser bundle (committed) |
| `views/logi_seed.py` | Sandbox seed (Phase A data; no production DB) |
| `views/logi_view_model.py` | View-model builder + `consume_triggers` dispatcher |
| `views/logi_shell.py` | Registers + mounts the ONE v2 component |
| `views/web_app.py` | `main()` — page config + render (launcher: `app.py`) |
| `scripts/scan_process.py` | Build gate: 0 executable Node-global refs |
| `tests/component/dom_acceptance_phase_a.mjs` | DOM acceptance of the production bundle |
| `tests/component/fixtures/view_model_phase_a.json` | View-model fixture for the DOM test |
| `tests/test_phase_a_component.py` | Backend acceptance (AppTest + pure dispatcher) |
| `playwright/acceptance_phase_a.py` | Real-browser 12-item acceptance (live Preview) |

## Run

```bash
# build the component (browser-only)
cd component && npm ci && npm run build && npm run scan

# serve the app
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

## Verification (evidence)

1. **Process gate** — `scan_process.py`: `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`.
2. **DOM acceptance** — `tests/component/dom_acceptance_phase_a.mjs` runs the
   real `dist/logi-shell.js` in a DOM and drives all 12 checklist actions with
   real events: boot (no `process is not defined` / BidiComponent Error),
   header, sidebar (5 groups/16 items), click Tổng Quan / Việc Cần Xử Lý /
   Lô Hàng, open LO-0306, all five donor tabs, global search finds a
   shipment, Quick Add open/close, Notifications open/close, and route+tab
   surviving a simulated backend rerun (re-invocation with new data). Also
   asserts the typed `shipment_update` event contract.
3. **Protocol** — a WebSocket client against the live server confirms the
   `bidi_component` proto is delivered with the exact dist bundle (0 process
   refs) and a JSON-serializable view-model `data` channel.
4. **Backend** — `tests/test_phase_a_component.py`: app boots the single v2
   component without exception; the bounded dispatcher merges a
   `shipment_update` (via the real `ComponentResult` type) and ignores stale
   seqs / unknown ids / unbounded events.

> This sandbox cannot download a browser (Chromium CDN unreachable), so the
> authoritative real-browser pixel check is the committed
> `playwright/acceptance_phase_a.py`, run against the live Preview. The
> structural/interaction parity is fully verified above; visual parity follows
> from byte-identical donor source + verbatim donor CSS.

## Phase A acceptance mapping

| # | Check | Verified by |
| --- | --- | --- |
| 1 | App boots without BidiComponent Error / `process is not defined` | DOM + protocol + AppTest |
| 2 | Header renders | DOM |
| 3 | Sidebar renders (donor groups/items) | DOM |
| 4 | click Tổng Quan | DOM |
| 5 | click Việc Cần Xử Lý | DOM |
| 6 | click Lô Hàng | DOM |
| 7 | open LO-0306 | DOM |
| 8 | click all five Shipment Detail tabs | DOM |
| 9 | global search opens and finds a shipment | DOM |
| 10 | Quick Add opens/closes | DOM |
| 11 | Notifications opens/closes | DOM |
| 12 | rerender does not lose route/tab | DOM (simulated rerun) |

## Out of scope (Phase B/C — NOT started)

Contracts / Finance / Customers real backends, Docgen backend, Production DB,
wiring all real Logistics writers. Phase A proves the architecture only.
