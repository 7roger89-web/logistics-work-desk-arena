# LOGI #190 — exact evidence binding

PRODUCT_HEAD=`f604d71547dea9a8b6f7cba2607bca555a5adb3d`
PRODUCT_TREE=`a15c913c0f448bf6c3365561de4943303f04f2a3`
INTEGRATED_PARENT=`92f012d1f726b1a6db02462c2e57046f8da96ccb`
PR_191_REMOTE_CHECKPOINT=`ce6324ba1d834856da5a5a33c0f1d199eec5a009`
PRODUCT_SOURCE_DELTA_AFTER_EVIDENCE_COMMIT=`NONE`

The product commit above contains the bounded B1/B2 repair, regression harness,
and rebuilt committed dist. The following commit is evidence-only. Verify after
checkout with:

```bash
git diff f604d71547dea9a8b6f7cba2607bca555a5adb3d..HEAD -- component/src component/dist views core tests
```

Expected output: no files. Evidence was captured from the exact product tree
through canonical isolated mongomock hosts; it did not use production data or
perform production writes.

## Runtime binding

- Captured: `2026-10-08T11:22:37.212Z`
- Browser: real Chromium `110.0.5478.0`
- Viewports: `1536×1466` and `390×844`
- Chromium's real layout scrollbars enabled (`--hide-scrollbars` removed)
- Product bundle SHA-256: `63884a6506a84674d28071f5304236df034c83b356d6b13c040b5f8cfd0dbfb2`
- Product CSS SHA-256: `cc5432a57e26c477fce6c27112dbef6cf888c314ff7465b5b25bb9574200f8a3`
- Owner reference blob SHA-1: `26bf1ee2d08ddf1ca966d92207782af7dc993b5c`
- Owner reference SHA-256: `62b0f7f4960334ed0880a5908f7138b2f4f0296ccf7ea76ea9421251bd6fbb9a`
- Runtime result: 33/33 #190 checks passed

## Measured acceptance summary

- `.logi-shell`: client `1536×1409`, scroll `1536×1409`, vertical overflow `0px`
- map/panel/gap: `1039 / 451 / 12px`; ratio `2.304`
- map fit: `0.90704` (91%); immutable logical nodes `164×136`; 11/11 `DEMO_POS` exact
- Customs content: `685px` scroll height in `551px` client; internal scroll `134px`
- Customs footer y: `811.859375` before and after internal scroll
- Customs action counts: one primary and one workspace navigation action
- Stage Workspace opening and optional-module reveal: zero `/event` writes
- fresh 390 top: shell `scrollTop=0`, phase strip visible, canvas entrance visible
- populated/fresh 390: zero page and app-scrollport horizontal overflow
- list: three canonical `OVERDUE` rows and three no-band rows; no text-derived urgency

## Gates bound to this product tree

- TypeScript typecheck: PASS
- Vite build: PASS (1,914 modules)
- executable-process scan: PASS, `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`
- focused #190/#188/#186/#184 pytest: PASS, 41 tests
- Prototype-B DOM geometry oracle: PASS, 11 exact positions and zero navigation writes
- #190 real Chromium: PASS, 33 checks
- #188 real Chromium: PASS, 31 checks
- `git diff --check` and Node harness syntax: PASS

## Artifact SHA-256 manifest

`EVIDENCE.md` intentionally omits its own hash to avoid a circular self-hash;
Git's evidence commit tree binds this file itself.

| Artifact | SHA-256 | Bytes |
|---|---|---:|
| `README.md` | `a1955db9ae15114ba1673baadc5b9d2439073fc7ea5fe1fa5a241e294663178e` | 7,995 |
| `candidate-fresh-390-onboarding.png` | `334b47eb377ed9c94d67aa18cc303b69d8fefcac18fa90c21421329c25e2a7f8` | 52,260 |
| `candidate-fresh-390-top.png` | `fa1c5e037e868a8bb31dce271fb476fb7310077af02e2b1e66931759cb06cf5a` | 72,166 |
| `candidate-fresh-desktop-cockpit.png` | `9d7e595149397894b60a38be570a7fd3c44e9ff9fee15fe1823d9b3c471b9f58` | 105,795 |
| `candidate-fresh-desktop.png` | `70dbad015bd7a3d63cf37d85a55ab1858dbbc2a6e203b4660a6473bd92e92433` | 154,338 |
| `candidate-global-workspace.png` | `0f3d371fabc63cacd4c6efe8327d6fcba58a102cd2728ec5368469819fbc329b` | 238,644 |
| `candidate-other-route-home.png` | `03220346d6711ff6ca5e432a2477e44b4063d4e07f327ba451db0b07d6722106` | 251,810 |
| `candidate-populated-390.png` | `58f8a2ddd30e610e57aacd8fdc3c254aac70ca3454d13f20984239204cacf707` | 83,589 |
| `candidate-populated-desktop.png` | `a691472bdd296d71ab7269523953caf5eae935ccc4c850d8b65edf45231672f3` | 301,630 |
| `candidate-populated-fullpage.png` | `2615d597c953790c5eaabbcc5f1692748f74ad6e21b55d48e6696e5b5aee541f` | 301,313 |
| `candidate-populated-journey.png` | `30201cadcba1ad2d10fb6e2c83dd00134ddc0d014a8f02df74e457eb4436ef61` | 253,601 |
| `completion-collapsed.png` | `b009ba7e2e94f85ffa23c4657ff4fa1a9f1326ce08c62ae241fbc2822436c8b2` | 12,911 |
| `completion-goals-expanded.png` | `7797d4951307fa8d3e43d94bf9815ddbd4aa85621e26a971b97fb345efd6450a` | 166,354 |
| `diff-populated-ref.json` | `5aaf0ca6901daeeb1e86b6531d561c8dfb9d0627e42989521160de53584f12be` | 1,908 |
| `diff-populated-ref.png` | `6154126f4a604797c5f14fa38902d0a93606c46003d3699ea329b400067a80ac` | 633,882 |
| `geometry.json` | `3c03c2d0a2531f7efed229201b02d533d8193806dd398677d2600c92ffec0bf0` | 23,868 |
| `overlay-populated-ref.png` | `b50d01600baa276a49786df1fe7e8955ef23012b824c560d76e32ec4ee6d8a1d` | 621,910 |
| `quick-panel-action-order.png` | `bd6c5ab19fb57f626fc96f8338ccaa2d7cbb3ac3c402610a0595891f25d18667` | 319,114 |
| `quick-panel-pinned-footer.png` | `03ff2f4a95f16b72a3898846384279e39dc8ed638f4c524bc8770e70357b6a1b` | 322,871 |
| `reference-measure.json` | `abe3eccb9d2a6db2073926c41d87ece19a678d3ac95330caf865889ea785ff09` | 37,844 |
| `reference-original.png` | `62b0f7f4960334ed0880a5908f7138b2f4f0296ccf7ea76ea9421251bd6fbb9a` | 392,238 |
| `shipment-list-alerts-fullpage.png` | `98f2e24d07d2f3f5d630469d33d112cfdcfeaa78a9046c453b8c24672ca06992` | 348,170 |
| `shipment-list-alerts.png` | `f5f4c7f1c24bf374dc826c0dd4a17322ad9755fc82fbf90864d8793e26838e01` | 348,271 |
| `side-by-side-populated-ref.png` | `8518e578d32e6b0ca55620784e6ea8259eda003c93762d71a1b998a0f89a6151` | 685,535 |
