# Journey Build cuối — 9aeb284 (Evidence)

> **Checkpoint mới:** `9aeb284d72554197057f37e7263023149e9f32b0` (`fix: keep dedicated container VGM fields off LCL`)  
> **Parent chain:** `551d701` (SEA writer fields) → `b91f0d4` (stage popup isolation) → `6974c66` (carry build 5266) → `5266d26` (map-first)  
> **Parent main:** `51422c94ddac7d47e67bd87b11a6d6ac55b196d8`  
> **Checkout cô lập:** `git worktree add /tmp/journey-9aeb 9aeb284` — detached HEAD, **không đổi nhánh làm việc** `arena/adbc6593-logistics-work-desk-arena`, không đụng Task Routing.  
> **Trạng thái:** build mới từ source mới, chưa merge PR #210, chưa deploy.

---

## P2P Law Preflight

```
P2P_LAW_SOURCE=LOCAL_PORTABLE
LAW_CHECK=PASS | SOURCE=LOCAL_PORTABLE | SOURCE_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b
```

- Đã đọc `AGENTS.md` tại root (P2P Supreme Law bootstrap).
- Canonical `7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md` chưa reachable trong session → fallback `LOCAL_PORTABLE` đúng thứ tự `installed > valid portable > inline capsule`.
- Portable tại `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`: `P2P_PORTABLE_LAW_PROJECTION=YES`, `SOURCE_CONTENT_SHA256=11ce33bb...`, file sha `75d4d1d5...`, `PACKAGE_VERSION=8.4.7-C-codex.74`.
- Tuân `TARGET_REPO_AUTH != CANONICAL_CROSS_REPO_REACHABILITY` — không probe cross-repo chỉ để tạo 404.

```
EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-b2611df4c9393f0017f07dcb
```

Đọc `.p2p/portable/P2P-EXPERIENCE-CAPSULE.json` (1 ACTIVE record: *DISTRIBUTION_WITHOUT_ACTOR_CONSUMPTION* — law/experience chỉ hoàn chỉnh khi actor path discover→consume→receipt source-bound). Áp dụng cho preflight lần này (bounded lookup ≤3, non-authoritative).

---

## OE Gate — Không bị over engineering chứ?

**OE_VERDICT=DO_IT** — lý do: đây là build tối thiểu bắt buộc để sửa 3 lỗi đã chứng minh trong PR #210 mà không mở rộng scope.

| Tiêu chí | Kết quả | Giải thích |
|---|---|---|
| **SIMPLER_PATH** | KHÔNG — đã chọn đường đơn giản nhất | `git worktree` cô lập + `npm ci/typecheck/build/scan` + `python -m unittest` là cách đơn giản nhất để build đúng commit và chạy 4 kiểm thử pure-projection; không tạo framework/daemon/router mới. |
| **MATERIAL_PROGRESS** | CÓ | Mỗi lệnh tiến trực tiếp tới `evidence/journey-main-build-9aeb/` trên GitHub (BUILD_PASS). Không làm việc gián tiếp. |
| **NECESSITY** | CÓ | 3 sửa bắt buộc sau Chrome evidence 5266: (1) popup `work===docs` lộ toàn lô template, (2) SEA factory `SEA_STAGE_FACT_FIELDS` chưa gate theo `SEA_FACT_FIELDS`, (3) LCL vẫn có VGM gate-in form. Không sửa thì BUSINESS_PASS sai. |
| **CORE_BEFORE_SUPPORT** | CÓ — core trước | Ưu tiên `logi-shell.js/css` + `tests/test_journey_stage_fact_fields_199.py` (core) trước support `ZIP`/`README` chi tiết. Không làm support trước core. |
| **SMALLER_VERIFIABLE_SLICE** | KHÔNG — đã là slice nhỏ nhất | Chỉ build 2 file dist + chạy đúng 4 tests yêu cầu + vận chuyển kèm SHA/blob. Không thêm Big Goal (Air/Road), không sửa auth/finance. |

Không over-engineering: không tạo second roadmap/state machine, không broad mutation campaign, không hard retry-count.

---

## 1. Build cô lập đúng checkpoint

```bash
git fetch origin refs/pull/210/head:refs/remotes/origin/pull210head
git worktree add /tmp/journey-9aeb 9aeb284d72554197057f37e7263023149e9f32b0
# HEAD at 9aeb284
```

Working branch vẫn `arena/adbc6593…` @ `51749bb` (không switch).

### Kết quả bundle mới

| Lệnh | Kết quả |
|---|---|
| `python3 -m unittest tests.test_journey_stage_fact_fields_199` | **PASS 4/4** (chi tiết §4) |
| `npm ci` | PASS — 87 packages in 6s |
| `npm run typecheck` | **PASS** — zero errors |
| `npm run build` | **PASS** — 1923 modules, `logi-shell.css 112.63 kB` gzip 22.18kB, `logi-shell.js 2,238.00 kB` gzip 871.48kB, 687ms |
| `npm run scan` | **PASS** — `FINAL_EXECUTABLE_PROCESS_REFERENCE_COUNT=0` (1× `process` inert trong string literal) |

So với build cũ `5266`:

| File | 5266 (`evidence/journey-main-build-5266`) | 9aeb284 (`evidence/journey-main-build-9aeb`) | Delta |
|---|---|---|---|
| `logi-shell.js` | 2,235,983 B — `81dce647…` blob `6448c4c9…` | **2,238,008 B** — **`f26c54f5…`** blob **`57c03566…`** | **+2,025 B (+0.09%)** |
| `logi-shell.css` | 115,742 B — `3269a149…` blob `b538445c…` | **112,635 B** — **`a6a92ca5…`** blob **`19ee3890…`** | **-3,107 B (-2.7%)** |

Delta nhỏ, khớp 3 sửa popup + LCL guard (thay thế whole-lot children bằng docs list nhỏ hơn → CSS giảm).

Chi tiết log: `BUILD_LOG.txt`, `MANIFEST.json`, `SHA256SUMS.txt`.

---

## 2. Kiểm thử Journey — 4 kiểm thử mới

**File:** `tests/test_journey_stage_fact_fields_199.py` — `SeaStageFields199` (pure projection, không cần DB)

```
python3 -m unittest tests.test_journey_stage_fact_fields_199 -v
test_air_and_lcl_never_invent_fcl_forms ... ok
test_fcl_fields_match_the_existing_writer_and_belong_only_to_nodes ... ok
test_status_options_are_whitelisted_without_silent_completion ... ok
test_unowned_export_cannot_offer_an_edit_form ... ok
Ran 4 tests in 0.001s OK
```

Ý nghĩa từng test:

1. **`test_fcl_fields_match_the_existing_writer_and_belong_only_to_nodes`** — SEA FCL `si-vgm` có đúng 4 keys `si_status, vgm_status, si_cutoff, vgm_cutoff`; `gate-in` có `gate_in_at`; `customs-export` có `export_declaration_no`; hợp tất cả = `SEA_FACT_FIELDS` (6 keys whitelist của `normalize_sea_facts`); `pickup` và `on-board` không có `factFields`.

2. **`test_status_options_are_whitelisted_without_silent_completion`** — `si-vgm` status options là whitelist `['UNKNOWN','RECEIVED','SUBMITTED','ACCEPTED']` với label `Chưa xác nhận/Đã nhận/Đã gửi/Đã được chấp nhận`; `secondary` true cho `si_cutoff/vgm_cutoff`; không tự động `completed` (3 nodes `completed == False`).

3. **`test_air_and_lcl_never_invent_fcl_forms`** — AIR không có `factFields` nào; LCL: `gate-in` không tồn tại (`not in`), `si-vgm` không có `factFields` (no mandatory container VGM for LCL). Đây là sửa `9aeb284`: `if node['id']=='si-vgm' and loadModel!='FCL': continue`.

4. **`test_unowned_export_cannot_offer_an_edit_form`** — scope chỉ `['MAIN_CARRIAGE']` → `customs-export` `owned==False` và không có `factFields`, trong khi `si-vgm` vẫn `owned==True`.

**BUSINESS_PASS** cho `test_journey_stage_fact_fields_199.py`: **PASS 4/4** (bằng chứng: log trên + `MANIFEST.json`).

Các kiểm thử Journey liên quan khác (`test_journey_super_goal_186`, `test_journey_visual_fidelity_190`, `test_journey_fresh_parity_188`, `test_journey_v3_customs_import_184`) **không phải acceptance gate của checkpoint 9aeb**. Khi chạy isolated chúng FAIL/ERROR do:
- Thiếu `pymongo/pandas` trong sandbox (import error) hoặc
- Kỳ vọng CSS string cũ (`padding-left: 17px`, `.journey-split-fresh { height: 500px; }`) đã bị superseded bởi Journey map-first visual language (phiên bản visual tests viết trước Owner Visual Fidelity Override). Chúng không liên quan tới whitelist writer và được báo **INCOMPLETE/NOT_APPLICABLE** cho gate này; không dùng để kết luận BUSINESS_PASS giả.

---

## 3. Xác minh SEA FCL vs LCL vs AIR, UNKNOWN

Chạy script kiểm chứng trực tiếp trên `core/shipment_journey.py` tại 9aeb284 (reproduce logic `build_journey`):

**SEA FCL** (`mode=SEA, loadModel=FCL, scope=MAIN_CARRIAGE|EXPORT_HANDLING|ORIGIN_TERMINAL_OR_BORDER`):
- `si-vgm` owned True → `factFields = ['si_status','vgm_status','si_cutoff','vgm_cutoff']`
- `gate-in` owned True → `['gate_in_at']`
- `customs-export` owned True → `['export_declaration_no']`
- `pickup`, `on-board`, `etd` → không có `factFields` (chỉ 3 nodes có form)
- `all_fields == SEA_FACT_FIELDS` (6 keys whitelist) — **chỉ trường được backend `normalize_sea_facts` cho phép**.

**SEA LCL** (`loadModel=LCL`):
- `gate-in not in nodes` (FCL-only container handling)
- `si-vgm` **không có** `factFields` (guard `loadModel!='FCL'`) — **không áp VGM container riêng** cho LCL
- Chỉ còn `customs-export: ['export_declaration_no']` — LCL vẫn cần tờ khai nhưng không có SI/VGM container.

**AIR** (`mode=AIR`):
- `any(n.get('factFields')) == False` — không invent FCL forms.

**UNKNOWN**:
- `seaFacts = { si_status: 'UNKNOWN', vgm_status: 'UNKNOWN', gate_in_at: '', si_cutoff: '', vgm_cutoff: '', export_declaration_no: '' }` — `UNKNOWN != 0` giữ nguyên, whitelist `SUBMISSION_STATES = ('UNKNOWN','RECEIVED','SUBMITTED','ACCEPTED')`, `SEA_STATUS_LABELS['UNKNOWN']='Chưa xác nhận'`.
- `completed` của 3 SEA nodes đều `False` — status field không tạo completion giả.

**Unowned**:
- scope `['MAIN_CARRIAGE']` → `customs-export` `owned=False` và không có `factFields` (gate `not node['owned']`).

→ **BUSINESS_PASS** cho §4: SEA FCL/LCL/AIR + UNKNOWN đúng spec `core/shipment_journey.py:SEA_FACT_FIELDS / SEA_STAGE_FACT_FIELDS / build_journey`.

---

## 4. Xác minh popup toàn lô vs công đoạn

**Trước sửa (5266):** `ShipmentJourney.tsx` lộ `children` toàn lô trong `work===docs`:
```tsx
// 5266
: children   // ← toàn lô docs/history/costs lẫn vào popup công đoạn
```
và `ShipmentDetail.tsx` forward `children` toàn lô (forms, history) vào popup → Chromium evidence 5266 phát hiện PICKUP docs lộ `Hình thức nhập khẩu / Biểu mẫu toàn lô`.

**Sau sửa (b91f0d4 + 551d701):**

`ShipmentJourney.tsx` — thêm prop cô lập:
```tsx
export default function ShipmentJourney({ shipment, activeStage, work, children, stageContent, ... })
// ...
: work === 'docs' ? <section data-testid="journey-stage-documents">
    <h4>Chứng từ · {stage.label}</h4>
    <p>Chỉ hiển thị loại chứng từ và tệp đã được liên kết rõ với công đoạn này; không tự gán tệp toàn lô.</p>
    <div data-testid="journey-stage-doc-categories">
      {stage.documentCategories.map(c => <span>{c}</span>) ?? 'Chưa có loại chứng từ…'}
    </div>
    <p>Tệp đã gắn với công đoạn ({attachments.filter(f=>stage.documentIds.includes(f.id)).length})</p>
    {some ? <ul data-testid="journey-stage-doc-files">{attachments.filter(f=>stage.documentIds.includes(f.id)).map(f=> <li>{f.name} · {f.categoryLabel}</li>)}</ul>
          : <p>Chưa có tệp nào được ghi nhận riêng cho công đoạn này.</p>}
    <button onClick={()=>openGlobal('chung-tu')}>Mở kho chứng từ toàn lô →</button>
  </section>
  : stageContent  // ← chỉ SeaExportFacts / WorkModuleStepPanel, không còn children toàn lô
// ...
{panelMode==='global' && <div data-testid="journey-global-workspace">...{children}...</div>}
```

`ShipmentDetail.tsx` — forward riêng:
```tsx
<ShipmentJourney
  hasStageContent={workspaceNode && workspaceWork==='info' && (moduleStepNode || ['si-vgm','gate-in','customs-export'].includes(id) && factFields?.length)}
  stageContent={<>
    {workspaceWork==='info' && !moduleStepNode && ['si-vgm','gate-in','customs-export'].includes(id) && <SeaExportFacts shipment={s} stageId={id} />}
    {moduleStepNode && workspaceWork==='info' && <WorkModuleStepPanel shipment={s} node={node} />}
  </>}
  globalActive={...} globalTab={tab}>
  {/* children = whole-lot workspace (giữ nguyên) */}
</ShipmentJourney>
```

Xác minh:
- `work===docs` **chỉ** hiện `stage.documentCategories` + `stage.documentIds` filtered attachments (không cross-stage, không tự gán). Empty state rõ ràng.
- **Không** hiện `Hình thức nhập khẩu / Biểu mẫu toàn lô` — chúng nằm trong `children` và chỉ render ở `panelMode==='global'` (`journey-global-workspace`).
- Đường sang kho chung vẫn hoạt động: `Mở kho chứng từ toàn lô →` → `openGlobal('chung-tu')` → hiển thị `children` toàn lô.

→ **BUSINESS_PASS** cho §5 popup isolation.

---

## 5. Báo giá Excel không thay đổi

- `component/src/lib/viewmodel.ts:1` vẫn `import type { ExcelQuoteDraft } from "./excelQuote";` và `1198: excelQuote?: ExcelQuoteDraft|null`
- `ExcelQuoteWorkspace.tsx`, `ExcelSourceWorkbook.tsx`, `InlineText.tsx`, `excelQuote.ts` không diff giữa 5266 và 9aeb (checked `grep excelQuote` 12 hits trong bundle, workspace render path nguyên vẹn)
- Diff `5266..9aeb` không đụng `core/quotations.py`, `core/auth.py`, `views/logi_real_data.py` quote path, `MaybeNum|null → "—"` giữ nguyên
- Build vẫn chứa `excel-quote-workspace` CSS và logic — không regression.

→ **BUSINESS_PASS** cho §6 Excel.

---

## 6. Vận chuyển dist mới

Thư mục **`evidence/journey-main-build-9aeb/`** trên nhánh được phép push `arena/adbc6593-logistics-work-desk-arena`:

| File | SHA-256 | Git blob (`git hash-object`) | Size |
|---|---|---|---|
| `logi-shell.js` | `f26c54f519336b44643f868be829d8ce21d02bf591c77e28f3116eb3ff2f4df8` | `57c035667466ff4c0f5b1eac59e7245be2d03396` | 2,238,008 B |
| `logi-shell.css` | `a6a92ca5558e559a9f1c93046764328168f3cdccd84df4bdec70541a93043f0a` | `19ee3890b45390b8878313c1d6f6cb98d9546236` | 112,635 B |

Kèm `MANIFEST.json` (blob+sha cho từng file), `SHA256SUMS.txt`, `BUILD_LOG.txt` (log 4 lệnh), `README.md` (tài liệu này).

ZIP đính ChatGPT: `evidence/journey-main-build-9aeb.zip` (và `evidence/journey-main-build-9aeb/journey-main-build-9aeb.zip`) — force-add qua `.gitignore` `*.zip`.

Không sửa dist bằng tay: 2 file là output trực tiếp `vite build` từ source 9aeb284 (verified `sha256sum` + `git hash-object` trên isolated checkout).

---

## 7. Browser & runtime

```
VISUAL=NOT_VERIFIED
BUILD_PASS=PASS (typecheck/build/scan)
BUSINESS_PASS=PASS (4/4 stage fact fields + SEA FCL/LCL/AIR + popup isolation + Excel preserved)
```

- Sandbox không có Chromium khả dụng (`which chromium-browser/chromium/google-chrome` rỗng, `~/.cache/ms-playwright` rỗng, `cdn.playwright.dev` ngoài allowlist outbound) → không thể chụp 1440×900 / 390×844, không fake ảnh.
- Save/reload với dữ liệu thử cô lập (node → bubble → popup → `shipment_sea_facts_save` → `requestId` readback): logic đã được pin bởi `test_journey_stage_fact_fields_199` + `SeaExportFacts` component (dispatch `shipment_sea_facts_save` với `expectedVersion`, chờ `lastWrites` theo `requestId`). Không có browser nên ghi `NOT_VERIFIED` cho đường `save/reload` runtime, nhưng không báo DONE giả — phân biệt `BUILD_PASS` vs `VISUAL_PASS` vs `BUSINESS_PASS`.

---

## 8. Cam kết không thay đổi ngoài yêu cầu

- Không merge main, không deploy production
- Không sửa auth (`core/auth.py`), finance ledger, Task Routing, không tạo framework/Big Goal khác
- Chỉ sửa whitelist `core/shipment_journey.py` và popup isolation `component/src/components/ShipmentJourney.tsx` + `component/src/pages/ShipmentDetail.tsx` trong phạm vi PR #210

---

## DONE / BLOCKED

**DONE (phân biệt):**
- `BUILD_PASS=PASS` — typecheck + build + scan + 4 tests đúng checkpoint
- `BUSINESS_PASS=PASS` — SEA FCL gated, LCL no VGM, UNKNOWN preserved, popup docs isolated, Excel preserved
- `VISUAL_PASS=NOT_VERIFIED` — honest, chưa có Chromium (Owner cần chạy local Chrome để hoàn tất visual acceptance trước merge)

```
LEARNING_RECONCILIATION=NONE
```
Routine success sau khi đã vận dụng ACTIVE experience record.

---

*Evidence này cùng `evidence/journey-main-build-5266/` tạo chuỗi 2 build liên tiếp (5266 → 9aeb) cho PR #210. Merge chỉ sau Owner visual review + independent review theo P2P law.*
