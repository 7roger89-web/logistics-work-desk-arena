# LOGI-197 follow-up — zero-node closure (Issue #197)

Companion to `EVIDENCE.md` (which binds the 53/53 acceptance to product HEAD
`fc41beed8de13ffd34c3af1ef630d3c2536124de`). This record covers ONLY the
zero-node follow-up repair. The 53/53 result is NOT relabelled: it tested
`fc41bee`, not the head below.

## Tested HEAD

- `624f858d159eed21290eff9b621bbf09417585fb` (`fix(logi197): zero-node Journey renders the compact five-phase view`)
- Parent: `c0766158520af662cf3dedb192b768ea0edc57ca` (evidence-only)
- Branch: `ct/logi197-journey-operator-clarity`, PR #198 (draft, unmerged)

## Change (source)

`component/src/components/ShipmentJourney.tsx`:

- Removed `FreshShipmentCockpit` + `EMPTY_PHASES` (the old six-phase canvas +
  Quick Panel that invented "Đang ở: HỒ SƠ" with zero authoritative nodes).
- New `ZeroNodeJourney`: the zero-node / missing-Journey path (`!journey?.nodes.length`)
  renders the SAME five compact macro phases as the populated path via the
  existing `JourneyStageSummaryCards` with `nodes={[]}`:
  - toolbar reads "📍 Đang ở: Chưa xác định" — never an invented phase;
  - steps 1–4 Công việc/Chứng từ disabled without a canonical node
    ("Chưa có công đoạn", no global fallback);
  - one obvious "BỔ SUNG HỒ SƠ →" action (`runPrimary`) completes the
    execution profile;
  - step 5 keeps whole-lot Hồ sơ/Chi phí/Lịch sử via `onGlobal`;
  - the global branch still renders the page tab content (`{children}` carries
    the whole-lot tab panels incl. the Execution Profile editor) once a global
    tab is explicitly opened — the CTA flow is unchanged.
- Populated-Journey behavior unchanged (the reroute is the only behavioral delta).

## Gates

| Gate | Result |
|---|---|
| Typecheck (`tsc --noEmit`) | PASS |
| Build (`vite build`) | PASS |
| Executable-process scan | PASS (`FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`) |
| pytest `test_journey_fresh_parity_188.py` | 7/7 PASS (contract rewritten for the new shape) |
| pytest `test_shipment_document_picker_v1.py` | 16/16 PASS (unchanged behavior) |
| DOM `dom_acceptance_journey_fresh_188.mjs` | PASS, variants `nodes` + `absent` (real bundle, real fixture, zero business writes; CTA reaches the Execution Profile editor) |
| DOM `dom_acceptance_logi197_journey_clarity.mjs` | PASS (populated path unchanged) |
| DOM `dom_acceptance_logi195_compact_journey_smooth.mjs` | PASS (delegate) |
| Dist rebuilt from source and committed | YES |

Dist SHA-256 (committed):
- `logi-shell.js`: `8b5950b1e7195413b1ef16b1feb9e974d0d8699356ae1f37a8b2e6d293744414`
- `logi-shell.css`: `117a35c5cac4bf55a918a9096e179264aa26d6b86862709ac4ef59399ea5d78d`

## Real-Chromium visual QA — BLOCKED (environment)

The bounded real-Chromium pass (desktop 1440 + mobile 390 zero-node, populated
smoke, scrolled stage-document list) could not run in this session:

- Local Chromium 152: the VM is out of memory (~130–400MB available; the OOM
  killer takes down any Chrome launch). Retried with cgroup containment —
  the browser starts but renderers die.
- Managed browser task (leased VM): the self-contained harness
  (`evidence/197/harness-zero-node.html`, synthetic data only) was uploaded,
  but the leased browser's org policy blocks `muse.ai`; a public re-upload
  needs an egress approval card that timed out unclicked.

What stands in: the deterministic jsdom DOM lane above mounts the EXACT
committed bundle over a REAL sandbox projection and asserts the full new
zero-node contract (5 phases, disabled steps, truthful UNKNOWN, one CTA,
zero writes) for both `nodes=[]` and absent-Journey. The harness file is
preserved at `evidence/197/harness-zero-node.html` so the visual pass can be
run on any machine with a working Chromium: open it, wait for
`window.__mounted`, click "Lô Hàng" → period "Tất cả" → "SEA-188" (zero-node)
or "SEA-160" (populated).

`VISUAL_VERDICT=NEEDS_EVIDENCE` for the new head. `HUMAN_UAT=NOT_CLAIMED`.

## Files

- `evidence/197/EVIDENCE-ZERO-NODE.md` (this file)
- `evidence/197/results-zero-node.json` (machine-readable)
- `evidence/197/harness-zero-node.html` (self-contained visual harness, synthetic data)
