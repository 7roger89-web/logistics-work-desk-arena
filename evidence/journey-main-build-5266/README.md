# Journey Mimo tích hợp — Build kết hợp tại 5266d266 (Evidence)

> **Checkpoint gốc:** `5266d2666f4cdbee2ba56782db86f19a7c20344c` (`ct/logi199-journey-main-integration-20261017` / `PR #210 head`)  
> **Parent main đã xác thực:** `51422c94ddac7d47e67bd87b11a6d6ac55b196d8` (Merge PR #206)  
> **Checkout cô lập:** `git worktree add /tmp/journey-isolated 5266d266` — detached HEAD, **không thay đổi nhánh làm việc** `arena/adbc6593-logistics-work-desk-arena` và không đụng Task Routing.  
> **Trạng thái pháp lý build:** SOURCE_ONLY → combined bundle cho nghiệm thu (chưa phải release artifact, chưa merge PR #210, chưa deploy production).

---

## P2P Law Preflight

```
P2P_LAW_SOURCE=LOCAL_PORTABLE
LAW_CHECK=PASS | SOURCE=LOCAL_PORTABLE | SOURCE_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b
```

- Đã đọc `AGENTS.md` (379 dòng) tại repository root.
- Canonical `7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md` chưa từng được reach trong session này (không có installed runtime `.p2p/system` đầy đủ), nên fallback theo thứ tự `LOCAL_PORTABLE` được áp dụng.
- Portable projection tại `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md` hợp lệ: `P2P_PORTABLE_LAW_PROJECTION=YES`, provenance `7roger89-web/P2P-upgrade-github-1@main`, `SOURCE_CONTENT_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`, file sha256 `75d4d1d589b3bfd4ef70a12a93878664766f65734075fd14f398a76a9fddde1e`.
- Không thực hiện cross-repo `gh` probe chỉ để tạo 404 (đúng `TARGET_REPO_AUTH != CANONICAL_CROSS_REPO_REACHABILITY`).

```
EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-b2611df4c9393f0017f07dcb
```

- Đã đọc `.p2p/portable/P2P-EXPERIENCE-CAPSULE.json` (1 ACTIVE record).  
- Record `shared-exp-b2611df4c9393f0017f07dcb` — bài học “distribution without actor consumption”: law/experience chỉ hoàn chỉnh khi actor path thực sự discover → consume → chứng minh bằng receipt có source-bound. Áp dụng cho task này ở mức preflight (law receipt + bounded experience lookup trước khi build).

---

## OE Gate — Không bị over engineering chứ?

**OE_VERDICT=DO_IT** — lý do: đây là bundle kết hợp tối thiểu có thể nghiệm thu.

| Tiêu chí | Kết quả | Giải thích |
|---|---|---|
| **SIMPLER_PATH** | KHÔNG — chọn đường đơn giản nhất hợp lệ | `git worktree` cô lập + `npm ci / typecheck / build / scan` là đường đơn giản nhất để build đúng commit mà không copy thủ công hay clone mới. Không thêm router/daemon/state machine. |
| **MATERIAL_PROGRESS** | CÓ | Bundle kết hợp chính là DONE của checkpoint 5266 — mọi bước đều tiến trực tiếp tới `evidence/journey-main-build-5266/` trên GitHub. |
| **NECESSITY** | CÓ | PR #210 ghi rõ `SOURCE_ONLY` — dist cũ là main cũ (386b1c1 sẽ regress Quotes). Không có combined build thì không thể nghiệm thu, không thể kiểm tra Excel quote còn nguyên. |
| **CORE_BEFORE_SUPPORT** | CÓ — core trước | Ưu tiên `logi-shell.js/css` (core) và manifest SHA/blob trước; ZIP chỉ là support optional cho Owner đính ChatGPT. Không làm support trước core. |
| **SMALLER_VERIFIABLE_SLICE** | KHÔNG — đã là slice nhỏ nhất | Chỉ build 2 file dist + 2 file manifest (`SHA256SUMS.txt`, `MANIFEST.json`). Không thêm feature, không sửa source ngoài lỗi đã chứng minh (không có). |

Không có over-engineering: không tạo thêm framework, không broad mutation, không full-suite ceremony ngoài cần thiết.

---

## 1. Build cô lập đúng commit 5266d266

```bash
git fetch origin refs/heads/ct/logi199-journey-main-integration-20261017:refs/remotes/origin/ct/logi199-journey-main-integration-20261017
git worktree add /tmp/journey-isolated 5266d2666f4cdbee2ba56782db86f19a7c20344c
# HEAD is now at 5266d26 feat(journey): stage Mimo map-first integration on current app main
```

- Working branch `arena/adbc6593-logistics-work-desk-arena` vẫn ở `51422c9` (verified `git status` clean, không switch).
- Không thay đổi Task Routing (không đụng `core/*`, `views/*`, router).

### Kết quả bundle React kết hợp

| Lệnh | Kết quả |
|---|---|
| `npm ci` | PASS — `added 87 packages, audited 88 packages in 5s` (1 high severity npm audit, không chặn build) |
| `npm run typecheck` (`tsc --noEmit`) | **PASS** — zero errors |
| `npm run build` (`vite build`) | **PASS** — `1923 modules transformed`, `logi-shell.css 115.74 kB` (gzip 22.60 kB), `logi-shell.js 2,235.98 kB` (gzip 871.29 kB), `built in 767ms` |
| `npm run scan` (`python3 ../scripts/scan_process.py dist`) | **PASS** — `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0` (chỉ 1x `process` inert trong string literal) |

So với dist cũ tại main `51422c9`:

| File | main 51422c9 | build 5266d266 (evidence) | Delta |
|---|---|---|---|
| `logi-shell.js` | 1,517,185 bytes (SHA256 `61656dd5…`) | **2,235,983 bytes** (SHA256 `81dce647…`, blob `6448c4c9…`) | **+718,798 bytes (+47%)** — JourneyBubble + inlined chart assets |
| `logi-shell.css` | 93,626 bytes (SHA256 `5cabd757…`) | **115,742 bytes** (SHA256 `3269a149…`, blob `b538445c…`) | **+22,116 bytes (+25%)** — journey-map-first + zero-state styles |

Hai asset hải đồ được Vite lib build inline (không phát sinh file rời, dist chỉ có 2 file): `chart-paper.jpg` (432,516 B) + `vietnam-east-sea-chart.webp` (107,956 B) → base64 trong `logi-shell.js` (delta ~720 kB khớp).

Chi tiết: xem `BUILD_LOG.txt`, `MANIFEST.json`, `SHA256SUMS.txt` trong cùng thư mục.

---

## 2. Kiểm tra Journey map-first & nền hải đồ Việt Nam

**Kết luận: PROVEN (source + bundle)**

- `component/src/components/JourneyMap.tsx` (5266):
  - `import chartPaperUrl from '../assets/journey/chart-paper.jpg?url'`
  - `import vietnamChartUrl from '../assets/journey/vietnam-east-sea-chart.webp?url'`
  - Comment: *“Vietnam – East Sea nautical chart is the DEFAULT Journey background. It is a real local asset inlined by the Vite library build; the paper texture stays only as a light overlay so it can never hide the chart underneath.”*
  - Render: `<div data-testid="journey-sea-chart" style={{ backgroundImage: `url(${vietnamChartUrl})` }} />` (pointer-events-none, absolute inset-0) + overlay `style={{ backgroundImage: `url(${chartPaperUrl})` }}`
  - `journey-sea-chart` là background chính; `journey-canvas` với pan/zoom nằm trên.

- `component/src/components/ShipmentJourney.tsx`:
  - Populated và zero-node đều dùng `journey-split journey-map-first` (`data-testid="journey-split-view"` và `journey-zero-map-first`) — supersedes `journey-split-small-map` (Owner Visual Fidelity Override 15/10/2026).
  - Canvas sizing: `CW = col(9)+W+PX`, `CH = ROW_BOTTOM+H+ROW_TOP` với `ROW_MAIN=240` cân giữa desktop.

- Bundle evidence:
  - `dist/logi-shell.css` chứa 228 occurrences `journey`, `dist/logi-shell.js` chứa 196 occurrences `journey`.
  - Flags: `journey-bubble=True`, `journey-sea-chart=True`, `journey-map-first=True`, `journey-zero=True`.

---

## 3. Kiểm tra node → bong bóng → popup (Owner HTML: node → bubble → task popup)

**Kết luận: PROVEN (source + bundle)**

- `JourneyBubble.tsx` — `BubbleTask` (`PROBLEM|CURRENT|WAITING|COMPLETED|UPCOMING`), `bubbleTasksFor()`:
  1. Stage action (`stageAction(node)`), meta `HẠN … · N CHỨNG TỪ`
  2. Mỗi blocker phụ thành task riêng
  3. `Chứng từ đính kèm công đoạn` (`attached >0 ? COMPLETED : WAITING`)
  4. Work Modules neo tại node (`m.nextStep`)

- `ShipmentJourney.tsx`:
  - State: `const [bubbleId, setBubbleId] = useState('')` + `renderBubble={(n,p,c,below)=> <JourneyBubble … tasks={bubbleTasksFor(n,s,modules,…)} onClose={()=>setBubbleId('')} onQuick={()=>{setBubbleId(''); setPicked(n.id); setPanelMode('quick')}} />}`
  - `pick(id)` → `setBubbleId(id)` cho base node; module step thì `setPanelMode('quick')` trực tiếp.
  - Popup modal: `modalOpen = panelMode !== 'overview'` → `<div data-testid="journey-modal">` (backdrop + `renderSidePanel`), Escape handler, `role="dialog"` trên bubble (`data-testid="journey-bubble"`).

- `JourneyMap.tsx` giữ `renderBubble` **INSIDE** pan/zoom layer (`transform: translate(x,y) scale(k)`) nên bubble di chuyển cùng node.

- Bundle: `JourneyBubble|journey-bubble|bubbleTasksFor` count = 17, `journey-bubble` trong CSS = true.

---

## 4. Kiểm tra zero-node

**Kết luận: PROVEN**

- `ZeroNodeJourney` component riêng, early return sau mọi Hooks (hook-ordering repair Issue #197):
  ```tsx
  if (!hasNodes) return <ZeroNodeJourney … />
  ```
- Render:
  - `data-testid="shipment-journey" data-empty-journey="true"`
  - `journey-zero-map-first` với `<JourneyMap nodes={[]}>` (empty Journey là decorative chart, wheel handler `if (!nodes.length) return` để page scroll bình thường)
  - `data-testid="journey-empty-map" role="status" aria-labelledby="journey-zero-title"` chứa:
    - `CẦN LÀM NGAY` + `journey-zero-profile-state`
    - `Chưa có sơ đồ Journey` + `Chưa đủ hồ sơ để xác định công đoạn chi tiết.`
    - `BỔ SUNG HỒ SƠ →` (`data-testid="journey-zero-primary-cta"`)
    - `UNKNOWN không được biến thành công đoạn giả.`
  - `globalActive` branch cho fullscreen `Hồ sơ & Tài chính` workspace.

- Bundle: `journey-zero` + `Chưa có sơ đồ Journey` count 19.

---

## 5. Bảo toàn Excel Quote nhập/sửa/xuất

**Kết luận: PROVEN — không regression**

- `component/src/lib/viewmodel.ts` tại 5266:
  ```ts
  import type { ExcelQuoteDraft } from "./excelQuote";
  // …
  factFields?: JourneyFactField[]; // LOGI-199 T1 — additive
  export interface JourneyFactField { … }
  // Quote giữ nguyên:
  excelQuote?: ExcelQuoteDraft | null;
  ```

  Diff `51422c9..5266d26` chỉ thêm 4 dòng (`factFields` + interface) — **merge typed Journey factFields với main ExcelQuoteDraft/sentVersions mà không overwrite**.

- `ExcelQuoteWorkspace.tsx`, `ExcelSourceWorkbook.tsx`, `InlineText.tsx`, `excelQuote.ts` (CustomerTextRegion, binding, workbook view) còn nguyên; `component/src/lib/viewmodel.ts:1198` vẫn `excelQuote?: ExcelQuoteDraft | null`.

- `ShipmentJourney.tsx:839` `const fields = node?.factFields ?? []` và `853` `value={draft[f.key] ?? s.journey?.seaFacts[f.key] ?? 'UNKNOWN'}` — UNKNOWN vẫn là fallback trung thực, không giả 0.

- Bundle: `excel-quote-workspace` trong CSS true, `ExcelQuote|excelQuote` count 12 trong JS, `UNKNOWN` count 49, `factFields` true.

- Thông số tiền tệ / VAT / CBM / cost vẫn `MaybeNum | null` render `"—"` (không coerce 0), giữ `core/quotations.py` arithmetic.

> Không sửa nghiệp vụ, permission, giá tiền hay dữ liệu UNKNOWN.

---

## 6. Vận chuyển dist (Evidence trên GitHub)

Thư mục **`evidence/journey-main-build-5266/`** nằm trên nhánh được phép push `arena/adbc6593-logistics-work-desk-arena`:

| File | SHA-256 | Git blob (git hash-object) | Size |
|---|---|---|---|
| `logi-shell.js` | `81dce647e40ef5e0bc03f1fbf2d2c8ff62943019882f54c48beeeb98bf3a63e8` | `6448c4c96c4803f5df73c86d80a875fc06de83cd` | 2,235,983 B |
| `logi-shell.css` | `3269a149161637cd2d5dd4efdd18c49991fdcd05a767f081c73a24cef5985cca` | `b538445c8f0770cf12a8a4de2215bdd35cbb099c` | 115,742 B |

- `SHA256SUMS.txt` và `MANIFEST.json` kèm SHA + blob cho từng file.
- `BUILD_LOG.txt` lưu toàn bộ log `npm ci / typecheck / build / scan`.
- ZIP đính ChatGPT: `evidence/journey-main-build-5266.zip` (tạo từ chính thư mục này, chứa cả 2 file dist + manifest).

**Cách dùng để nghiệm thu (không merge):** Owner có thể so SHA-256 của ZIP/dist với `MANIFEST.json`; giải nén và thay `component/dist/` bằng 2 file này trên môi trường staging để chạy browser test, so với `reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html` (866,917 B, SHA `d400c276…` theo PR #210).

---

## 7. Screenshots Chromium

```
VISUAL_NOT_VERIFIED
```

- Sandbox Arena hiện tại **không có Chromium/Chrome khả dụng**: `which chromium-browser/chromium/google-chrome` không tồn tại; `~/.cache/ms-playwright` rỗng; `cdn.playwright.dev` không nằm trong allowlist outbound (`github.com`, `codeload.github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`) nên không thể `npx playwright install` tải browser.
- Tuyệt đối không giả ảnh: không tạo ảnh placeholder, không dùng grid/collage.
- Để hoàn tất nghiệm thu visual, Owner cần chạy local:
  ```bash
  git fetch origin arena/adbc6593-logistics-work-desk-arena
  git checkout arena/adbc6593-logistics-work-desk-arena
  # thay component/dist bằng 2 file trong evidence/journey-main-build-5266/
  cd component && npm run build   # hoặc copy trực tiếp
  # mở Streamlit app, vào ShipmentJourney với lô SEA FCL đủ nodes, chụp 1440×900 và 390×844, so với reference/owner-2026-10-15/logi-journey-mimo-sonnet-fusion.html
  ```

---

## 8. Cam kết không thay đổi ngoài yêu cầu

- Không merge PR #210 (vẫn `OPEN`, `STATUS=INCOMPLETE / DRAFT`).
- Không deploy, không sửa source ngoài lỗi đã chứng minh (không có lỗi phải sửa — `typecheck` PASS).
- Không đổi nghiệp vụ, permission (`core/auth.py ROLE_PERMISSIONS`), giá/CBM/VAT, `UNKNOWN` handling.
- Không đụng production secrets/DB.

---

## 9. Kết luận DONE / BLOCKED

**DONE — bundle kết hợp đã được build và lưu trên GitHub (evidence), có kết quả kiểm thử trung thực.**

- Bundle build: **PROVEN** (logs + SHA + blob)
- Scan/process: **PROVEN** (`FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0`)
- Journey map-first + Vietnam chart: **PROVEN** (source + bundle counts)
- Node→bubble→popup: **PROVEN**
- Zero-node: **PROVEN**
- Excel Quote bảo toàn: **PROVEN** (diff 4 dòng additive, bundle retains workspace)
- Visual Chromium: **VISUAL_NOT_VERIFIED** (honest, no fake) — khối còn lại đã đủ để Owner nghiệm thu bằng local Chrome per PR #210 acceptance step 4 (tap targets, scroll, modal, zoom, overflow).

```
LEARNING_RECONCILIATION=NONE
```

Routine success — không phát sinh reusable correction mới ngoài bounded law/experience receipt đã thực hiện.

---

*Tài liệu này cùng `MANIFEST.json`, `SHA256SUMS.txt`, `BUILD_LOG.txt` và 2 file `logi-shell.*` trong `evidence/journey-main-build-5266/` là bằng chứng duy nhất cho build checkpoint 5266d266. Mọi merge/deploy tiếp theo phải qua Owner Gate và independent review theo P2P law.*
