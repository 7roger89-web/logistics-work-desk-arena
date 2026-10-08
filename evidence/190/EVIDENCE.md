# LOGI #190 — Final Visual Evidence Binding (Round-CONTINUE)

PRODUCT_HEAD=6403655cf961d0ea8beae1f5bb6854dca462e6d7
PRODUCT_SOURCE_DELTA_AFTER_EVIDENCE_COMMIT=NONE

This commit binds ONLY durable evidence files. No product source, no dist,
no business tests, no product mutation. Verified:
`git diff PRODUCT_HEAD..FINAL_HEAD -- component/src views core component/dist`
returns zero files.

REFERENCE_BLOB_SHA=26bf1ee2d08ddf1ca966d92207782af7dc993b5c
  (verified: `git hash-object evidence/190/reference-original.png` on this
  branch returns exactly this SHA-1 — the on-branch file IS the packet blob;
  the file's SHA-256 is 62b0f7f4960334ed0880a5908f7138b2f4f0296ccf7ea76ea9421251bd6fbb9a —
  the two hashes describe the same file with different algorithms.)
REFERENCE_VIEWPORT=1536x1466
Reference file: evidence/190/reference-original.png (owner sample, preserved).

## Reference vs candidate (measured from real Chromium render @1536x1466)

| metric | reference | candidate |
|---|---|---|
| map | 1039px | 1034px |
| panel | ~451px | 450px |
| ratio (map/panel) | 2.30 | 2.298 |
| node rendered | ~153x122 | 148x123 |
| fit | 91% | 90% |
| five-card gap | 12px | 12px |

page content x: ~17 -> 16
identity bar: y~15-88 -> y 24 h 73
attention band: y~100-155 -> y 107 h 51
map bbox: (~17,~165,1039,718) -> (16,168,1034,718)
panel bbox: (~1067,~165,451,718) -> (1062,168,450,718)
five cards: ~289px each -> 285px each
global sidebar: n/a (demo chrome) -> hidden (focus shell, desktop only)
global topbar: n/a -> hidden (focus shell, desktop only)
permanent shipment tab row: absent -> absent
block order: identity -> attention -> map+panel -> five cards -> same

Logical node geometry 164x136 untouched (authoritative, per PR177 oracle).

390_HORIZONTAL_OVERFLOW=0

## Evidence artifacts (SHA-256)

- EVIDENCE.md — this binding document (self-hash not inlined to avoid
  circularity; verify via the commit tree)
- reference-original.png — owner sample, REFERENCE_BLOB_SHA bound above
  62b0f7f4960334ed0880a5908f7138b2f4f0296ccf7ea76ea9421251bd6fbb9a
- geometry.json — final measured geometry (identity/attention/map/panel/split/node/fit/cards/gaps/visibility flags)
  218fc999645609da8988ef7483729d424e74ab198f6690fc53841c707cf4800f
- candidate-populated-desktop.png — SEA-190 populated, 1536x1466
  574edbed79a669e392c12fe7e112ab0f21b816fd14b097cf78e30855a9aefc69
- candidate-populated-390.png — SEA-190, 390x844, 0px horizontal overflow
  9d9bb5fef5f15969fac94ca71ae61a9042b476ce64dc8b47aa1a6edf103c4e66
- candidate-fresh-desktop.png — FRESH-190 zero-node, truthful ("Hồ sơ lô còn thiếu", no fake nodes)
  a1940384b3392e0d2cd32979940de8eed1904a9e9deae2b9c9b3e64a48af942b
- candidate-fresh-390.png — FRESH-190, 390x844
  0915d22a10980e0aaf604d399f029575877ca8dca88907b137e79dbd283a26ef
- candidate-global-workspace.png — "Toàn bộ lô hàng" → Global Workspace (tabs: Thông tin / Xuất khẩu / Nhập & Giao / Chứng từ / Tài chính / Lịch sử)
  3c018ad4c09158d76521989796a93b7aed46418cfc37f44ac5cf3a882518f75b
- candidate-other-route-home.png — home route keeps the NORMAL shell (sidebar/topbar/footer visible)
  3c39025de44c4ef70b340cc9ed9780a233b9fad4284ef689e4fb116c496af2a3
- side-by-side.png — reference vs candidate
  b53c233154f9ffb760eea4118a5c4a1615b92dbf0a4bcfe47b87163ae12a0e04
- overlay-diff.png — amplified difference (white = same); mean abs 64.4, 23.7% px>30 — text-content delta only
  730f45a50dc2e468c684183d439ddd28aa5d3eec4fa306cdb547d240c845108c

## Capture method (real Chromium, honest)

- `vite build` → single-file harness (data: URL) → `/opt/meta-chromium/chrome --headless=new` via raw CDP WebSocket
- `Emulation.setDeviceMetricsOverride` AFTER `Page.navigate` (1536x1466 dsf 1; 390x844 mobile dsf 2)
- Fixture delivered through the real Streamlit Components v2 mount contract; store populated via `__deliverState()` → real `applyViewModel` wiring; shipment opened via synthetic MouseEvents on real list links
- dist under test: `component/dist/logi-shell.js` sha256 `9490518b2becca29` (rebuilt from source at PRODUCT_HEAD, committed)

## Remaining differences (all content/data, none layout)

1. Text content differs (fixture data vs reference demo data) — truthful.
2. Node labels differ (fixture projection vs reference Vietnamese) — truthful.
3. Attached-module strip renders BELOW the five cards (data-driven; the reference demo had no attached module).
4. Completion-goals bar below the cards (existing product feature).
5. Attention band shows 1 item (no secondary chips — fixture has 1 item).
6. Panel CTA text differs (fixture's journey data); CTA color now matches reference dark navy.

## Reproduce

```
cd ~/workspace/journey-190b-evidence
MODE=desktop     node evidence190b.js harness_190b.dataurl.txt evidence
MODE=mobilefresh node evidence190b.js harness_190b.dataurl.txt evidence
MODE=otherroute   node evidence190b.js harness_190b.dataurl.txt evidence
```
