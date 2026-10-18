# CONTROL-TOWER-HANDOFF — Logistics Work Desk

Bàn giao ca cho Control Tower. Mọi task có thay đổi file PHẢI cập nhật file này trước khi báo cáo hoàn tất — quy tắc đứng tại `AGENTS.md` mục `## Control Tower handoff — bắt buộc mọi task`.

## MỤC 1 — MỤC ĐÍCH DỰ ÁN

Journey map-first để Support/Sale nhìn biết lô đang ở công đoạn nào và công đoạn đó còn phải
làm gì. Owner là Sale, giao việc cho Support trên app, dùng hằng ngày cho MỌI luồng. Họ không
đọc code, chỉ tin màn hình. Node báo "xong" khi chưa xong là lỗi nặng nhất.

## MỤC 2 — QUYẾT ĐỊNH ĐÃ CHỐT

- Bên liên kết đứng tên nhập khẩu resolve từ `authority_companies`, KHÔNG authority_agents
- Duyệt 2 stage mới CHỈ cho TT_ENTRUSTED_SUB: `entrustment-ready`, `tt-warehouse-handover`
- Lộ trình: (0) 3 bug → (1) diệt false-done → (2) backport #200/#204/#208 vào #210
  → (3) nối commercial-flow + legal parties + 2 stage → (4) nội dung công đoạn
  → (5) E2E + UAT + merge
- Support/Sale dùng cho MỌI luồng → Luồng B KHÔNG được hoãn
- Journey là lớp trình bày từ facts, không phải kho trạng thái
- Merge main = deploy production. Không đụng app `tienthanhlog`.
- **Batch 2 semantics (LCL si-vgm) — CHỐT ĐÚNG (Owner, 2026-10-19)**: LCL CÓ node
  `si-vgm` SI-only (label 'SI', done theo `si_status=='ACCEPTED'`, không VGM).
  Rule đợt 1 "LCL không có node si-vgm" là SAI và đã bỏ.

## MỤC 3 — TRẠNG THÁI

*(cập nhật cho khớp sự thật — mỗi task)*

- **Nhánh/PR**: `arena/a3117943-logistics-work-desk-arena` → PR **#211** OPEN/MERGEABLE, base `ct/logi199-journey-main-integration-20261017` (PR #210 OPEN, HEAD `408b980`). Chưa merge, chưa deploy, không backport.
  - **2026-10-18 — tích hợp chuỗi T1–T5**: phiên này làm trên nhánh session `arena/441d2013-logistics-work-desk-arena` (cùng cây với `a3117943` @ `6f9d156` — session rule cấm switch/push nhánh khác): merge `07dc8f8` (2 cha: `6f9d156` + chuỗi `c53437e`) + dist `1b1cc13`. Title/body PR #211 đã cập nhật theo diff thật. **PR head vẫn là `arena/a3117943`** → commit tích hợp chưa hiện trên diff #211; Control Tower retarget head (hoặc fast-forward `a3117943 := 441d2013`) khi duyệt — Arena không push nhánh khác.
- **Batch 2 (false-done đợt 2) — TỪNG MẤT TÍCH, ĐÃ PHỤC HỒI**: `f51710b` bị push mồ côi vào nhánh `arena/da9aa3db-logistics-work-desk-arena` (không vào nhánh/PR nào). Đã tìm lại được (còn nguyên trên GitHub) và cherry-pick vào nhánh này — commit **`162036f`** (6 thay đổi: tách GNT khỏi TAX_PAID, `taxPaid` projection, writer chặn `vgm_*` khi LCL, importer `legalImporterName`, journey LCL chỉ SI, + docs/tests). Test đợt 1 khớp semantics mới: **`8a9d4f1`**. Giải conflict: LCL giữ node `si-vgm` SI-only — **Owner đã chốt 2026-10-19: batch 2 ĐÚNG** (xem MỤC 2), không còn chờ xác nhận.
- **Lộ trình**:
  - (0) 3 bug node truth — **XONG, semantics cập nhật bởi tích hợp T1–T5** (`61f0714` → `07dc8f8`): booking `done=booking_status=='CONFIRMED'` (chuỗi T1, `BOOKING_STATES` — bỏ biến thể `'ACCEPTED'` + bỏ điều kiện có số); on-board `done=bool(on_board_at)` (bỏ điều kiện ATD). Riêng bug si-vgm/LCL: giữ semantics batch 2 (dưới) — chuỗi T1–T5 tự có nhánh LCL SI-only.
  - (1) diệt false-done — **một phần XONG**: `d1340a5` (JourneyBubble docs, ô nhập fact, CẦN LÀM ra mặt tiền) + batch 2 `162036f` (GNT ≠ TAX_PAID, importer, LCL SI-only) + guard factFields LCL `53ccddc` (node SI-only của LCL giữ ô `si_status`/`si_cutoff`, chỉ bỏ ô `vgm_*` — guard `continue` cũ bỏ trắng form khiến node không bao giờ xong). Kiểm tiếp các surface khác nếu có biểu thức false-done.
  - (2) backport #200/#204/#208 vào #210 — **#204 (chuỗi T1–T5) ĐÃ tích hợp vào nhánh phiên** (`07dc8f8`); #200 (AIR_DOCUMENTS) + #208 (routing/stage scope) **CHƯA** (prompt phiên này loại trừ). Gợi ý thứ tự 1 dòng: **#200 trước #208** (stage AIR phải tồn tại trước khi routing gate theo stage scope), cả hai backport vào #210 trước khi tích hợp vào main.
  - (3) commercial-flow + legal parties + 2 stage `entrustment-ready`/`tt-warehouse-handover` (CHỈ TT_ENTRUSTED_SUB) — **CHƯA**.
  - (4) nội dung công đoạn (guidance) — **CHƯA** (UI đã nhận `n.guidance`; hiện trống nên hiển thị "Chưa có hướng dẫn cho công đoạn này").
  - (5) E2E + UAT + merge — **CHƯA**.
- **Sự thật kỹ thuật**: facts `booking_status`, `on_board_at` ghi được qua writer `shipment_sea_facts_save` + ô nhập metadata-driven. **Bundle đã build lại từ source HEAD** (`b512822` — typecheck sạch, scan 0 executable, marker parity source↔dist) — màn hình giờ ĐÃ phản ánh các fix. **CI main**: `.github/workflows/ci.yml` (`0b0fe85`) — push/PR vào main, pytest so baseline (đỏ = hồi quy); workflow vào main khi Owner merge tích hợp (Arena KHÔNG merge). **AGENTS.md** đã có 9 mục luật (4 charter `be3a96b` + 5 luật vận hành phiên `d57fab4`: bằng chứng trước kết luận, TASK 0, TASK CUỐI, xoay phiên, bài học tích lũy), **README.md** đã có (`77febe5`). Suite tích hợp (đo 2026-10-19, sau `53ccddc`): **41 failed / 1940 passed / 44 skipped** — 41 = 31 failure main-baseline + 10 xung đột test-main × code-#210 (188 x4/186/190 x4, `test_visual_shipment_workspace::test_same_attachment...`); suite flaky ±1 skip/fail theo môi trường (record cũ 40/45 không tái hiện được tại cùng HEAD).
- **Tích hợp chuỗi T1–T5 (`07dc8f8` + dist `1b1cc13`, 2026-10-18)**: nguồn `origin/ct/logi199-t5-app-identity@c53437e` (11 commit, merge-base `5c6642a`), 7 conflict resolve theo luật — `core/shipment_journey.py` lấy bản chuỗi (`fields=`/`_fact_field`, chuỗi AIR `core/shipment_journey.py:258-266`, ROAD `:301-320`, LCL CFS `:219`, `AIR_FACT_FIELDS/ROAD_FACT_FIELDS` `:26-30`, popup ≤5 primary trong `add()` `:127-133`) **+ documentIds theo category #210 giữ nguyên** (`:366-377`, `add()` không attribute trực tiếp `:142-145`); scope gate mọi fact mới `views/logi_view_model.py:2956-3003`; ShipmentDetail giữ ô nhập/`hasStageContent` nhưng gate `Boolean(node.factFields?.length)` (`ShipmentDetail.tsx:1385-1389`, hết list id hard-code); JourneyMap/ShipmentJourney/JourneyBubble/QuickPanel **giữ bản nhánh phiên** (auto-merge hoặc resolve-rule); `index.css:1` import Google Fonts (Be Vietnam Pro + IBM Plex Mono) + palette nhánh phiên, `.journey-demo` hết Inter (`:103`). Journey giờ có node **AIR/ROAD/LCL/CFS** (pin bởi `tests/test_logi199_t2_t4_mode_truth.py` — xanh). Re-pin ngữ nghĩa cũ ở 6 test file (booking CONFIRMED, on-board standalone, fields= sets, air form, unowned owned-gate, mount factFields) — không xoá test nào. **Suite CI-flag (2026-10-18): 40 failed / 1989 passed / 45 skipped — tập failure GIỐNG ĐÚNG baseline `6f9d156` (40, NEW=∅ GONE=∅)**; typecheck `tsc --noEmit` sạch, `scan_process.py` 0 executable, marker parity source↔dist (node mới đủ, chuỗi cũ biến mất).

### MỤC 3 — ĐANG CHỜ

- ~~scope-guard 2 fact `booking_status`/`on_board_at` trong `views/logi_view_model.py`~~ — **ĐÃ CÓ từ chuỗi T1–T5** (`views/logi_view_model.py:2979`, gate `MAIN_CARRIAGE`), Owner không còn phải duyệt việc "đụng file"; nếu muốn gỡ thì Owner nói riêng.
- **Owner quyết định** hướng xử lý 10 failure xung đột test-main × code-#210 (mục riêng hay bỏ qua) — xem số liệu Suite ở trên (sau tích hợp còn 40, gồm 188×3/186/190×4 + main-baseline).
- **Owner**: các mục MỤC 5 (danh sách pháp nhân `authority_companies`; nội dung hướng dẫn công đoạn).

## MỤC 4 — BẰNG CHỨNG & KIỂM CHỨNG

- Đợt 1 (`61f0714`): `tests/test_journey_node_done_facts.py` — 13 test âm+dương cho 3 bug (cây main-based 1905→1918 passed, 31 failure cũ giữ nguyên).
- Đợt 2 (`d1340a5`): `tests/test_journey_ui_truth.py` — 6 test (docs badge âm+dương; ô nhập + flow ghi→đọc lại qua **writer thật** `shipment_sea_facts_save`; CẦN LÀM source-contract). `tests/test_journey_stage_fact_fields_199.py` hồi xanh (2) theo hành vi Owner xác nhận.
- Full suite cây tích hợp: 42 failed/1912 passed → 40/1920 — **0 failure mới**.
- P0 JourneyBubble đã đọc source tại **đúng HEAD #210** (`408b980`, `component/src/components/JourneyBubble.tsx`) → kết luận LÀ lỗi → sửa trong PR #211 (bằng chứng file:line nằm trong body PR).
- Chưa có browser-lane cho UI đợt 2 (bundle `9aeb` frozen — cần quyết định build lại bundle).

## MỤC 5 — CẦN OWNER

- Danh sách pháp nhân thật trong `authority_companies` (tên + vai trò)
- Nội dung hướng dẫn công đoạn (Owner sửa từ bản nháp)

## MỤC 6 — NHẬT KÝ PHIÊN

### 2026-10-18 — tích hợp chuỗi sự thật T1–T5 (PR #204) vào nhánh phiên

- **Commit**: `07dc8f8` (merge `origin/ct/logi199-t5-app-identity@c53437e` — 2 cha `6f9d156`+`c53437e`, 7 conflict) + `1b1cc13` (dist build lại từ source merge) + commit handoff này.
- **Đã làm**: (1) **TASK 0**: sandbox là shallow clone (boundary `6f9d156`/`51422c9`) → unshallow fetch trước, đối chiếu blob với origin, không mất thay đổi; refspec mặc định thiếu chuỗi → fetch `+refs/heads/*`; merge-base `5c6642a` (Merge PR #196); liệt kê 7 conflict + vùng đụng từng file + 8 xung đột ngữ nghĩa. **Prompt lệch 2 chỗ đã nói ra**: (a) `NHÁNH ĐÍCH arena/a3117943` nhưng session cố định trên `arena/441d2013` (cùng SHA `6f9d156`); (b) prompt liệt kê JourneyBubble/QuickPanel/viewmodel/logi_view_model là conflict → thực tế auto-merge sạch, và JourneyMap/ShipmentJourney conflict nhưng prompt không có luật → đã chốt giữ bản nhánh phiên (dòng #210). (2) **TASK 1**: resolve theo luật — core lấy chuỗi + GIỮ documentIds #210 (`core/shipment_journey.py:366-377`) + batch-2 comment; ShipmentDetail giữ ô nhập, gate `factFields?.length`; index.css ghép import-font chuỗi + palette nhánh phiên; JourneyMap/ShipmentJourney/dist giữ nhánh phiên tạm. Re-pin ngữ nghĩa (booking `CONFIRMED`, on-board `bool(on_board_at)` standalone, fields= chuỗi, air form AIR, unowned owned-gate, mount factFields) ở `test_journey_node_done_facts`/`test_journey_ui_truth`/`test_journey_stage_fact_fields_199` — không xoá test. Suite CI-flag **40/1989/45**, tập failure so baseline `6f9d156` (worktree riêng): **NEW=∅ GONE=∅**. (3) **TASK 2**: `npm ci` + `tsc --noEmit` sạch + `vite build` (js 2.24 MB/css 113 kB) + scan 0 executable; marker parity ✓ (air-booking/air-acceptance/uplift/road-vehicle/road-ltl/road-border/cfs-receipt + 'Trạng thái booking' + 'Chi tiết phụ' + factFields gate + Be Vietnam Pro/IBM Plex Mono; mất: label 'Trạng thái xác nhận hãng tàu', list id hard-code, Inter; `<12px` hết ở file T5 chạm tới).
- **Không làm (theo prompt)**: tích hợp #200 (AIR_DOCUMENTS) và #208 (routing/stage scope) — gợi ý thứ tự ở MỤC 3 lộ trình (2); KHÔNG merge main, KHÔNG deploy, KHÔNG push nhánh `ct/*`.
- **Còn lại**: retarget head PR #211 (MỤC 3 Nhánh/PR); lộ trình (3)(4)(5); các ĐANG CHỜ còn lại.
- **Cần Owner**: MỤC 5 + ĐANG CHỜ + retarget head #211.

### 2026-10-19 — thêm luật vận hành phiên vào AGENTS.md + phục hồi sandbox re-clone

- **Commit**: `d57fab4` (AGENTS.md +5 mục luật nguyên văn) + commit handoff này.
- **Đã làm**: (1) **Sự cố môi trường**: sandbox bị dựng lại (fresh clone) giữa phiên — nhánh local rơi về `51422c9`, worktree overlay giữ file nhưng 2 file `component/dist/logi-shell.*` là bundle CŨ (thiếu marker `Tệp đã ghi nhận`/`journey-what-to-do`/`Chưa có hướng dẫn…`, 1.52 MB). Đối chiếu blob từng file với `origin/arena/...@9a9d96c`: 24/26 khớp, 2 dist lệch → `git reset --hard` lấy lại cây đã push (dist đã verify 2.24 MB), worktree sạch, không mất thay đổi nào. (2) Chèn NGUYÊN VĂN 5 mục luật từ paste Owner vào AGENTS.md (ngoài managed blocks, 52+/0−): **Bằng chứng trước khi kết luận**, **Khảo sát bắt buộc trước khi sửa (TASK 0)**, **Tự kiểm trước khi báo xong (TASK CUỐI)**, **Xoay phiên Arena**, **Bài học tích lũy** (placeholder cho các dòng luật tích lũy). `SOURCE_SHA256=0eef325ec4d29f5cfb64fdcff52da970deb595fdc63d212bbfc41a565df5e126`.
- **Còn lại**: các dòng ĐANG CHỜ ở MỤC 3; lộ trình (2)→(5).
- **Cần Owner**: xem MỤC 3 ĐANG CHỜ + MỤC 5.

### 2026-10-19 — guard factFields LCL + CI main + charter AGENTS.md + README

- **Commit**: `53ccddc` (guard factFields LCL + test âm/dương + căn pin 199) → `0b0fe85` (`.github/workflows/ci.yml` CI main) → `be3a96b` (AGENTS.md +4 mục charter nguyên văn, ngoài managed blocks) → `77febe5` (README.md) + commit handoff này.
- **Đã làm**: (1) Sửa guard `build_journey` (`core/shipment_journey.py:186`): `continue` bỏ trắng factFields node `si-vgm` khi LCL → node SI-only cần SI nhưng không có ô nhập, không bao giờ xong. Guard giờ lọc spec: LCL giữ `si_status`/`si_cutoff`, bỏ `vgm_status`/`vgm_cutoff`; FCL đủ 4. Test âm+dương (3 mới trong `tests/test_journey_node_done_facts.py`, pin `test_air_and_lcl_never_invent_fcl_forms` trong `tests/test_journey_stage_fact_fields_199.py` sửa theo hành vi đúng — pin cũ phong ấn chính bug này). (2) CI chạy trên main: `push` + `pull_request` vào main, `pip install -r requirements.txt pytest`, `python -m pytest tests -q` so **baseline failure đã ghi nhận** (main chưa tích hợp #210: 31; tích hợp #210+#211: 41; flaky ±1) — đỏ = hồi quy; `--ignore` file write-oracle lỗi collection có sẵn trên main. Workflow trigger main; vào main khi Owner merge tích hợp (Arena KHÔNG merge/deploy/backport). (3) AGENTS.md thêm 4 mục NGUYÊN VĂN từ paste P2P-DEVELOPMENT-CHARTER (§5A hai vòng phát triển + thang OE, §4 Owner Gate, §3 bất biến) — ngoài mọi managed block, 61 insertions/0 deletions, `SOURCE_SHA256=8108b7a4856cd7d26438c49d62e5d6d540aaff42248a6fd6c7d439351cb7068c`. (4) README.md định hướng (đọc gì trước, trỏ trạng thái sang handoff, cách làm việc). (5) Handoff: **bỏ** mục chờ "Owner xác nhận semantics LCL si-vgm", ghi **Owner chốt batch 2 ĐÚNG** vào MỤC 2.
- **Số liệu**: suite sau fix **41 failed / 1940 passed / 44 skipped**; failure set y hệt HEAD `949b089` (41/1937/44 — đã stash-diff đối chiếu, delta rỗng), +3 test mới xanh. 41 = 31 main-baseline + 10 xung đột test-main × code-#210.
- **Còn lại**: các dòng ĐANG CHỜ ở MỤC 3; lộ trình (2)→(5).
- **Cần Owner**: xem MỤC 3 ĐANG CHỜ + MỤC 5 (LCL semantics đã chốt, không còn chờ).

*(mới nhất LÊN TRÊN — mỗi task: ngày, commit SHA, đã làm, còn lại, cần Owner)*

### 2026-10-19 — hồi phục batch 2 mồ côi + build bundle

- **Commit SHA**: `162036f` (cherry-pick `f51710b` — batch 2), `8a9d4f1` (căn test đợt 1 theo semantics mới), `b512822` (build lại bundle từ source HEAD).
- **Đã làm**: (1) truy vết `f51710b` — CÒN trên GitHub, mồ côi ở nhánh `arena/da9aa3db-logistics-work-desk-arena`; cherry-pick + giải conflict `core/shipment_journey.py` theo TASK 2 prompt ("LCL chỉ cần SI, bỏ yêu cầu VGM"): LCL giữ node `si-vgm` SI-only, `sea_requirement` LCL chỉ SI — **đảo rule đợt 1** "LCL không có node si-vgm" (test đợt 1 cập nhật, âm+dương). (2) Build bundle `component/dist` từ đúng source HEAD: typecheck `tsc --noEmit` sạch, `scan_process.py` 0 executable, đối chiếu marker source↔dist (marker mới đủ, chuỗi cũ biến mất). (3) Ghi handoff (mục này + ĐANG CHỜ ở MỤC 3). (4) Sửa tiêu đề + body PR #211 khớp diff thật.
- **Còn lại**: các dòng ĐANG CHỜ ở MỤC 3; lộ trình (2)→(5).
- **Cần Owner**: xác nhận/đảo semantics LCL si-vgm; các mục MỤC 5.

### 2026-10-19

- **Commit SHA**: `61f0714` (đợt 1), `97254e9` (tích hợp base `408b980` của #210), `d1340a5` (đợt 2), `455351b` (rule AGENTS.md) + commit chứa file handoff này (sha đầy đủ trong receipt `HANDOFF_UPDATE=` của báo cáo task).
- **Đã làm**: (1) sửa 3 lỗi "báo xong khi chưa xong" ở `core/shipment_journey.py` + 13 test; (2) tích hợp base #210 vào nhánh session để sửa file chỉ có trên #210; (3) sửa P0 JourneyBubble docs (có tệp ≠ có bằng chứng), thêm ô nhập `booking_status`/`on_board_at`, đưa `what_to_do`/`done_when` ra mặt tiền QuickPanel + fallback "Chưa có hướng dẫn cho công đoạn này", 6 test mới; (4) đưa quy tắc cập nhật handoff vào `AGENTS.md` (ngoài block P2P managed) + tạo file handoff này.
- **Còn lại**: lộ trình (2)→(5) theo MỤC 3; xử lý 40 failure test-main × code-#210; browser lane cho UI (bundle refresh); scope-guard 2 fact mới trong `views/logi_view_model.py` (đã nêu từ đợt 1, chưa đụng vì ngoài phạm vi).
- **Cần Owner**: các mục MỤC 5 + xác nhận thứ tự lộ trình tiếp theo + duyệt build lại bundle `9aeb` hay không.
