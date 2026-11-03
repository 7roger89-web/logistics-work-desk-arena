# EVIDENCE — LOGI-IMPECCABLE-FIT-20261103

Đánh giá fit của Impeccable (pbakaus/impeccable) cho màn Journey Map + panel
trao đổi/chứng từ của logistics-work-desk-arena. Task đánh giá READ-ONLY:
không cài Impeccable, không chạy executable/live mode/hook, không sửa code.

Kết luận cuối task: **XONG** (xem mục 9).

---

## 1. Skill consumption receipt — p2p-uiux

```
RECEIPT: SKILL_CONSUMPTION
TASK_ID: LOGI-IMPECCABLE-FIT-20261103
SKILL: p2p-uiux
PATH: .agents/skills/p2p-uiux/SKILL.md
EXPECTED_SHA256 (staging d4c7365): 98f26873e48cc87e34d132478f73672a80d20b3a8e1a2256bdcdab4d6107e7b2
ACTUAL_SHA256:                   98f26873e48cc87e34d132478f73672a80d20b3a8e1a2256bdcdab4d6107e7b2
VERIFY: PASS (byte-identical với kỳ vọng staging d4c7365)
SKILL_VERSION_IN_FILE: 8.4.7-C-codex.15
CONSUMED_FOR: UI/UX fit evaluation — runtime evidence contract, bounded
  runtime review (desktop ~1440x900 / mobile ~390x844), read-only safety,
  accessibility checklist, SOURCE_REVIEW vs RUNTIME_VISUAL_REVIEW split.
NOTE: commit d4c7365 KHÔNG tồn tại trong repo này (git cat-file: Not a valid
  object name); việc verify bằng SHA256 là bằng chứng thay thế ref.
```

## 2. P2P_LAW_PREFLIGHT — P2P_LAW_SOURCE & LAW_CHECK

```
P2P_LAW_SOURCE=INSTALLED_AGENTS_MD + VALID_PORTABLE_PROJECTION
LAW_CHECK=PASS
```

- **Canonical** (`7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/
  P2P-OPERATIONS-NOTEBOOK.md`): KHÔNG truy cập trong session này → không dùng,
  và **không probe** để tạo lỗi (đúng luật preflight; TARGET_REPO_AUTH không
  đồng nghĩa canonical reachable).
- **Installed**: `AGENTS.md` đọc tại ref thực tế
  `23c4e00f2b2d3c43b984db41e99f3f3b74e687e5` (HEAD nhánh arena, branched from
  main). SHA256 `c3b34184967e7e720038380442d5b0a5648639d673524de782d81520c76177cb`.
- **Valid portable**: `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md` — header
  `P2P_PORTABLE_LAW_PROJECTION=YES`, `SCHEMA=p2p-portable-law-projection/1`,
  `CANONICAL_SOURCE=7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/
  P2P-OPERATIONS-NOTEBOOK.md`, `PACKAGE_VERSION=8.4.7-C-codex.74`,
  `PROJECTION_DO_NOT_EDIT=YES`. SHA256 `75d4d1d589b3bfd4ef70a12a93878664766f657
  34075fd14f398a76a9fddde1e`. Đọc trực tiếp, không chỉnh sửa.
- Ưu tiên đúng thứ tự: canonical (chưa từng với tới) → installed → valid
  portable. Inline capsule không cần kích hoạt.

## 3. OE_GATE (RULE 14) — đã hỏi đúng câu

- Câu hỏi đã hỏi user, nguyên văn: **"Không bị over engineering chứ?"**
- Trả lời user: **"Không — giữ tối giản"** (keep-minimal).
- Năm tiêu chí (đánh giá trên phạm vi task):

| Tiêu chí | Trả lời | Diễn giải hướng |
|---|---|---|
| SIMPLER_PATH | NO | Đường hiện tại (đọc code + ảnh thật có attribution + DOM run bằng harness có sẵn) đã là đơn giản nhất đạt acceptance; không tạo hạ tầng mới |
| MATERIAL_PROGRESS | YES | Tạo quyết định FIT + receipt + evidence + 1 đề xuất đo được |
| NECESSITY | YES | Thiếu nó thì không có OUTPUT 5 phần bắt buộc |
| CORE_BEFORE_SUPPORT | YES | Đánh giá fit là lõi; không build supporting infra, không cài gói mới |
| SMALLER_VERIFIABLE_SLICE | NO | Slice đã tối thiểu: một màn, tối đa một đề xuất, zero implementation |

```
OE_VERDICT=DO_IT
Lý do (một câu): đây là lõi yêu cầu với slice đã nhỏ nhất có thể; user xác
nhận giữ tối giản, mọi bước tiếp theo chỉ là đọc/đo/ghi bằng chứng.
```

## 4. Nguồn nghiên cứu Impeccable

| Nguồn | Chi tiết |
|---|---|
| github.com/pbakaus/impeccable | main @ `24aa254` (2026-11-02, "Fix: disclose the live Apply agent subprocess in the README"), 2.615 commits, 284 nhánh, 93 tags |
| README (api.github.com/repos/pbakaus/impeccable/readme) | blob sha `555fd9a67de957c750950e62bf1baad167f61b00`, 16.573 bytes — nguồn chính cho mọi claim năng lực dưới đây |
| Docs tham chiếu (không fetch): impeccable.style/docs | dẫn theo README |

**Không có thao tác cài đặt nào**: không `npx impeccable`, không npm/pip package
Impeccable, không binary, không hook, không Chrome extension, không ghi
`.impeccable/`, `PRODUCT.md`, `DESIGN.md`. Bằng chứng: mục 7.

## 5. Năng lực Impeccable — tài liệu nói gì vs thực tế chạy được trên stack Streamlit + React

Stack thực tế: Streamlit (Python, `st.components.v2.component`) + React 19
bundle Vite (`component/dist/logi-shell.js`) mount qua hợp đồng
`mount({data, parentElement, setTriggerValue})`; Tailwind v4; font Be Vietnam
Pro; data qua view-model dispatcher.

| Năng lực (README) | Tài liệu nói | Trên stack này, trong task này |
|---|---|---|
| 24 lệnh steer/review/finish (`bolder`, `critique`, `audit`, `polish`, `adapt`…) | Lệnh agent skill + engine binary | **Không chạy được** (không cài — MUST NOT). Bản chất là prompt playbook cho agent; nội dung review chồng lấp lớn với p2p-uiux runtime review + baseline-ui |
| Detector 62 rules "AI slop" (static patterns trên JSX/TSX) | `npx impeccable detect src/`, hook quét mọi file UI khi agent sửa | **Không chạy được** (không cài). Về nguyên tắc sẽ quét được `component/src` (JSX/TSX đúng đối tượng) — nhưng nhiều rule (padding chật, text nhỏ 10px, heading) sẽ **đánh trúng thiết kế đã được Owner khóa** ở #190 (node card 164×136, chữ 10–11px là chủ ý) → nguy cơ false-positive tạo "design drift" ngược |
| Detector rendered rules (contrast, tiny text) | Quét URL bằng Chrome/Edge đã cài | **Không chạy được**: sandbox không có browser (mục 6); ngoài ra trang thật là shell Streamlit chứ không phải trang Vite thuần |
| Live mode (overlay chọn element, hot-swap variant, ghi ngược vào source) | "Works with Vite, Next, SvelteKit, Astro, Nuxt, plain HTML" | **Không có trong danh sách hỗ trợ của chính Impeccable cho Streamlit**. Component Vite dev server là đường documented gần nhất nhưng mount contract của Components v2 không phải app Vite thường — overlay/ghi ngược trên host Streamlit là **chưa ai chứng minh**. Và task MUST NOT cấm live mode |
| Apply subprocess (copy edits gửi agent) | Chạy `codex`/`claude` CLI với `--dangerously-bypass-approvals-and-sandbox` / `--permission-mode bypassPermissions`, kế thừa env | **Rủi ro quyền nghiêm trọng** (mục 8). README vừa phải disclose điều này ở commit `24aa254` (issue #1274) |
| `init`/`document` → PRODUCT.md, DESIGN.md, `.impeccable/` | Ghi file làm working state | Không chạy (MUST NOT "không ghi sản phẩm"). Tạo **authority thiết kế song song** với `.p2p/design/MASTER_DESIGN_SYSTEM.md` (p2p-uiux) — chưa tồn tại trong repo, càng dễ xung đột khi có hai nguồn |
| Hook design scan khi agent sửa file | "The installer sets it up. Say yes." | Không cài. Đây là **lớp enforce ngoài repo law** (mục 8) |
| Chrome extension overlay | Cửa hàng Chrome | Không dùng (cài thêm phải báo Owner) |

**Đối chiếu công bằng với p2p-uiux** — cùng loại "documented vs chạy được":
`SKILL.md` p2p-uiux liệt kê lệnh `python scripts/p2p_router.py` /
`python scripts/p2p_uiux.py` (recommend/design-system/contract/drift/a11y) —
**hai script này KHÔNG tồn tại trong repo** (ls: No such file), `.p2p/design/`
chưa có. Phần "chạy được thật" của bộ p2p-uiux hiện tại là: workflow + runtime
evidence contract, baseline-ui constraints, source-contract tests
(`tests/test_journey_visual_fidelity_190.py`…), visual oracle
(`docs/JOURNEY_ORIGINAL_VISUAL_ORACLE_190.md` + `tests/component/fixtures/
journey_demo_b_geometry.json`), và harness DOM/browser
(`tests/component/*.mjs`, `playwright/*.py`). Phân biệt này áp dụng cho cả hai
bên.

## 6. Bằng chứng browser desktop/mobile

**Phân loại capability (p2P-uiux contract): `UNAVAILABLE` (pixel) +
`EQUIVALENT_DOM` (jsdom trên production bundle — pattern sandbox được chính
repo chuẩn hoá, xem header `tests/component/dom_acceptance_phase_a.mjs`).**

Real-browser download bị chặn (Playwright CDN ngoài allowlist; không có
chromium nào trên hệ thống; `~/.cache/ms-playwright` rỗng). Do đó:

**a) Ảnh thật Chromium (attribution: phiên trước, harness
`tests/component/browser_journey_visual_fidelity_190.mjs`, evidence #190):**

| Ảnh | Viewport | SHA256 |
|---|---|---|
| `evidence/190/candidate-populated-desktop.png` | 1536×1466 (= Owner reference dims) | `a691472bdd296d71ab7269523953caf5eae935ccc4c850d8b65edf45231672f3` |
| `evidence/190/candidate-populated-390.png` | 390×844 (đúng mobile viewport hợp đồng) | `58f8a2ddd30e610e57aacd8fdc3c254aac70ca3454d13f20984239204cacf707` |

Quan sát từ hai ảnh thật (mô tả trung thực, không chấm điểm đẹp):
- **Desktop**: hierarchy rõ 4 tầng — identity bar → attention strip (1 việc cần
  xử lý) → map + Quick Panel (451px) → 5 work-card + strip rà soát read-only.
  Map: canvas chấm bi, node 164×136, nhánh song song SI/VGM + Gate-in, cạnh
  màu theo trạng thái, legend góc dưới-phải, zoom/fit/reset góc dưới-trái, hint
  góc trên-phải. Quick Panel mở node PROBLEM (ARRIVAL) mặc định: 1 action
  dominant ("CẦN LÀM NGAY — Thiếu ETA" + CTA "XỬ LÝ NGAY"), facts bên dưới, 1
  CTA cuối ("MỞ CÔNG ĐOẠN"). Đúng composition #190.
- **Mobile 390px**: attention strip + identity wrap/truncate ("Chưa xác nh…",
  "Bổ sung số …"); map cuộn/pan được; **legend (5 dòng) phủ lên ~1/4 bề rộng ×
  ~1/3 chiều cao vùng canvas, che khu vực node TRANSIT** — ăn "không gian bản
  đồ" đúng trọng tâm scope; hint "Cuộn để zoom" hiển thị cả trên mobile (thiết
  bị touch không có wheel — zoom chỉ dùng nút +/−, không có pinch; xem source
  `JourneyMap.tsx`: zoom gắn duy nhất với sự kiện `wheel`, pan 1 con trỏ).
- **Lưu ý trạng thái**: hai ảnh trên chụp mặc định CHI TIẾT map thời #190. Từ
  #195, mặc định là compact overview (stepper + panel), map chi tiết nằm sau
  nút "🗺 Bản đồ chi tiết" — DOM run hôm nay xác nhận điều này. Các quan sát
  map/legend áp dụng cho trạng thái map chi tiết.

**b) DOM acceptance chạy hôm nay (2026-11-03, production bundle
`component/dist/logi-shell.js` SHA256 `b34c8f52…`, jsdom 30, node v22.22.3,
fixture sinh từ stack thật mongomock — `scripts/gen_*.py`, không data bịa):**

```
node tests/component/dom_acceptance_logi195_compact_journey_smooth.mjs /tmp/logi195-dom.json
→ LOGI-195 DOM acceptance: compact journey + smooth operations — all assertions passed.
   (compact là mặc định; "Bản đồ chi tiết" mount map 11 node; pick node là local
   state; mở/đóng node state; picker chứng từ PXK; flow GÁN với backend refusal thật)

node tests/component/dom_acceptance_shipment_document_review.mjs
→ SHIPMENT_DOCUMENT_REVIEW_DOM_ACCEPTANCE=PASSED checks=17
   (gồm STEP 12 — mobile-first at 390px: no forced horizontal overflow)

node tests/component/dom_acceptance_shipment_attachments.mjs
→ SHIPMENT_ATTACHMENT_DOM_ACCEPTANCE=PASSED checks=13
   (gồm STEP 10 — mobile: no forced horizontal overflow; thumb-sized controls)
```

Tổng: **3/3 suite PASS** — bằng chứng trạng thái mở node, nút thao tác
(XỬ LÝ NGAY / MỞ CÔNG ĐOẠN / GÁN / Save…), panel chứng từ/trao đổi, và hành
vi mobile 390px ở mức DOM.

**c) Giới hạn bằng chứng (không PROVEN khi thiếu):** không có pixel review mới
của phiên này (`RUNTIME_REVIEWED=NO` cho claim pixel mới; `VISUAL_VERDICT` cho
phát hiện mới = `PROVISIONAL`/`NEEDS_EVIDENCE`). Kết luận thị giác mới duy
nhất (legend che map ở 390px) = `PROVISIONAL_VISUAL_FINDING` — nguồn: ảnh thật
390px có attribution + source CSS/JSX xác nhận, chưa chụp lại bằng browser
phiên này.

## 7. Phép thử MUST NOT — git status & dependency trước/sau

```
TRƯỚC: git status = clean (trước khi làm việc)
       requirements.txt       7d3a758476485d86082b5b5459da5f9ab14a8185c02eef3fe22cefa1b75b327b
       component/package.json 2c6e0bec2653192378c319bba25748017bc32f60e0d5d28aa2cf9f6902126c24
SAU:   git status = CHỈ ?? evidence/LOGI-IMPECCABLE-FIT-20261103/ (evidence của task)
       requirements.txt       7d3a758476485d86082b5b5459da5f9ab14a8185c02eef3fe22cefa1b75b327b  (không đổi)
       component/package.json 2c6e0bec2653192378c319bba25748017bc32f60e0d5d28aa2cf9f6902126c24  (không đổi)
       component/package-lock.json 1f3a4543… tracked, KHÔNG bị sửa (npm install không ghi khác)
KẾT LUẬN: PASS — không code mới, không package mới, không dependency manifest đổi.
```

Ghi chú trung thực: hai fixture tracked (`tests/component/fixtures/
view_model_attachments.json`, `view_model_document_review.json`) bị chính
generator của repo ghi lại khi chạy test (diff 6.326+/918−, chỉ dữ liệu
fixture) — đã `git checkout --` **restore về bytes gốc** để tree đúng trạng
thái tìm thấy. venv Python (`/tmp/logivenv`) + `node_modules` (giống bước cài
đặt chuẩn của repo) nằm ngoài tầm theo dõi git, không phải package mới của repo.

## 8. Rủi ro cài đặt & quyền thực thi (nếu sau này cài Impeccable)

1. **Apply subprocess bypass quyền** — Impeccable live Apply tự chạy
   `codex`/`claude` CLI với `--dangerously-bypass-approvals-and-sandbox` /
   `--permission-mode bypassPermissions`, kế thừa toàn bộ env (README tự
   disclose ở commit `24aa254`, issue #1274). Trực tiếp mâu thuẫn read-only
   safety của p2p-uiux (`CLICK_CAPABILITY != WRITE_AUTHORITY`) và luật repo
   ("Không deploy khi chưa có lệnh Owner"; Owner Gate).
2. **Hook enforce ngoài law** — design hook quét mọi file UI khi agent sửa,
   cài vào tool config (project/global), cần trust/approve ở Codex `/hooks`,
   Grok `/hooks-trust`, Hermes plugin. Đây là lớp cưỡng chế thứ hai bên cạnh
   CI gate + tests của repo, không chịu AGENTS.md.
3. **Chân dung cài đặt lớn** — npm package + engine binary Rust tải về
   `~/.impeccable/bin/` (checksum-verified nhưng là network fetch + executable
   trong HOME) + bản copy skill cho 17 tool目录; `npx impeccable update` tự
   nâng version. AGENTS.md: "Cài thêm phải báo Owner. Không cài gói lớn."
4. **Authority thiết kế song song** — `PRODUCT.md`/`DESIGN.md`/`.impeccable/
   design.json` vs `.p2p/design/MASTER_DESIGN_SYSTEM.md` + visual oracle #190
   ("code 100% giao diện của ảnh mẫu gốc"). Lệnh aesthetic (`bolder`,
   `delight`, `overdrive`) hợp lệ của Impeccable nhưng là **drift** với oracle
   Owner đã khóa (geometry 164×136/212/48/690/420/760 là "geometry authority,
   not suggestions").
5. **Ignore-authority song song** — `impeccable ignores add-value` +
   comment `impeccable-disable` tạo kênh tắt rule riêng, cạnh
   `tests/BASELINE_FAILED.txt`.
6. **Detector vs thiết kế dày đặc** — node card 10–11px text, padding chặt
   theo prototype B sẽ bị rule "tiny text/cramped padding" phàn nàn lặp lại →
   hoặc sửa loạn oracle, hoặc tắt rule hàng loạt → giảm giá trị.
7. **Live mode ngoài danh sách hỗ trợ** — Streamlit Components v2 mount không
   nằm trong "Vite, Next, SvelteKit, Astro, Nuxt, plain HTML"; CSP/iframe shell
   của Streamlit là vùng Impeccable chưa nhận hỗ trợ.

## 9. Kết luận & khuyến nghị

```
FIT = SKIP
```

**Lý do chính**: với đúng phạm vi (Journey Map + panel trao đổi/chứng từ: dễ
đọc, không gian bản đồ, hierarchy, desktop/mobile, nút thao tác, trạng thái mở
node), phần Impeccable *thêm được* so với bộ p2p-uiux hiện tại chỉ là (a) detector
62 rule deterministic, (b) critique có điểm số, (c) live variant iteration:

- (a) phần static có thể quét JSX đã có đối trọng là source-contract tests +
  baseline-ui + check_router/scan_process/ruff; phần rendered cần Chrome (không
  có) và sẽ xung đột với oracle #190;
- (b) điểm số đẹp là thứ p2p-uiux **cấm có chủ đích** ("Do not emit an arbitrary
  numeric beauty score"), finding ranked theo bằng chứng runtime đã có;
- (c) live/write-back vi phạm read-only law + rủi ro bypass quyền ở mục 8,
  và không nằm trong stack được hỗ trợ.

Bằng chứng runtime (3 DOM suite PASS + ảnh thật 2 viewport) cho thấy các tiêu
chí scope đã được test-pin sẵn; gap thật còn lại là trải nghiệm touch trên map
chi tiết — sửa bằng <10 dòng code là đủ, không cần bộ công cụ mới.

**Khuyến nghị nhỏ nhất (tối đa một, không triển khai trong task này):**

> Trên viewport < 640px, chuyển legend trạng thái của Journey Map (`div` legend
> góc dưới-phải trong `JourneyMap.tsx`, `bottom-16 right-3`) thành nút "Chú
> thích" nhỏ chỉ mở khi bấm. **Đo được**: ở 390×844 trạng thái map chi tiết,
> diện tích canvas bị legend che = 0 px² khi mặc định (hiện tại ~¼ bề rộng ×
> ⅓ chiều cao vùng map, che node TRANSIT — ảnh
> `evidence/190/candidate-populated-390.png`); desktop 1536px giữ nguyên;
> DOM test thêm assert legend `hidden`/`aria-expanded=false` ở mobile.

(Nhận xét phụ, không phải đề xuất: hint "Cuộn để zoom" không đúng trên touch —
zoom chỉ có nút +/−, không pinch.)

**Kết luận cuối task theo AGENTS.md: XONG** — đủ OUTPUT 5 phần, receipt, bằng
chứng + giới hạn ghi rõ, không PROVEN quá bằng chứng.

## 10. Giới hạn nguồn

- Nhánh `staging` không tồn tại trên origin; ref `d4c7365` không có trong repo
  → "SHA256 tại staging d4c7365" được verify bằng hash file (PASS), không bằng
  ref.
- Impeccable chỉ được nghiên cứu từ README + tree GitHub; không có claim nào
  về hành vi runtime của Impeccable được coi là PROVEN trên stack này.
- Không có Issue/PR nào được tạo cho báo cáo này (đúng NON-GOAL); Issue #263
  không bị chạm tới (toàn bộ thao tác nằm ngoài code sản phẩm).
