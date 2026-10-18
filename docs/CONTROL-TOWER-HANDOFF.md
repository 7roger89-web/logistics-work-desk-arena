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

## MỤC 3 — TRẠNG THÁI

*(cập nhật cho khớp sự thật — mỗi task)*

- **Nhánh/PR**: `arena/a3117943-logistics-work-desk-arena` → PR **#211** OPEN/MERGEABLE, base `ct/logi199-journey-main-integration-20261017` (PR #210 OPEN, HEAD `408b980`). Chưa merge, chưa deploy, không backport.
- **Batch 2 (false-done đợt 2) — TỪNG MẤT TÍCH, ĐÃ PHỤC HỒI**: `f51710b` bị push mồ côi vào nhánh `arena/da9aa3db-logistics-work-desk-arena` (không vào nhánh/PR nào). Đã tìm lại được (còn nguyên trên GitHub) và cherry-pick vào nhánh này — commit **`162036f`** (6 thay đổi: tách GNT khỏi TAX_PAID, `taxPaid` projection, writer chặn `vgm_*` khi LCL, importer `legalImporterName`, journey LCL chỉ SI, + docs/tests). Test đợt 1 khớp semantics mới: **`8a9d4f1`**. Giải conflict: LCL giữ node `si-vgm` SI-only (xem ĐANG CHỜ).
- **Lộ trình**:
  - (0) 3 bug node truth — **XONG** (`61f0714`): booking `done=bool(booking) and booking_status=='ACCEPTED'`; on-board `done=bool(atd) and bool(on_board_at)`. Riêng bug si-vgm/LCL: đã thay bằng semantics batch 2 (dưới).
  - (1) diệt false-done — **một phần XONG**: `d1340a5` (JourneyBubble docs, ô nhập fact, CẦN LÀM ra mặt tiền) + batch 2 `162036f` (GNT ≠ TAX_PAID, importer, LCL SI-only). Kiểm tiếp các surface khác nếu có biểu thức false-done.
  - (2) backport #200/#204/#208 vào #210 — **CHƯA**.
  - (3) commercial-flow + legal parties + 2 stage `entrustment-ready`/`tt-warehouse-handover` (CHỈ TT_ENTRUSTED_SUB) — **CHƯA**.
  - (4) nội dung công đoạn (guidance) — **CHƯA** (UI đã nhận `n.guidance`; hiện trống nên hiển thị "Chưa có hướng dẫn cho công đoạn này").
  - (5) E2E + UAT + merge — **CHƯA**.
- **Sự thật kỹ thuật**: facts `booking_status`, `on_board_at` ghi được qua writer `shipment_sea_facts_save` + ô nhập metadata-driven. **Bundle đã build lại từ source HEAD** (`b512822` — typecheck sạch, scan 0 executable, marker parity source↔dist) — màn hình giờ ĐÃ phản ánh các fix. Suite tích hợp: **40 failed / 1937 passed / 45 skipped** — 40 failure còn lại là xung đột test-main × code-#210 có sẵn (188/186/190, `test_visual_shipment_workspace::test_same_attachment...`).

### MỤC 3 — ĐANG CHỜ

- **Owner xác nhận semantics LCL si-vgm**: theo TASK 2 của prompt hồi phục batch 2, node `si-vgm` cho LCL là **SI-only** (label 'SI', done theo SI, không VGM) — ĐẢO quy tắc đợt 1 "LCL KHÔNG có node si-vgm". Nếu Owner vẫn muốn rule đợt 1, báo lại để đảo trong 1 commit.
- **Owner duyệt**: scope-guard 2 fact `booking_status`/`on_board_at` trong `views/logi_view_model.py` (đề xuất từ đợt 1, chưa đụng file ngoài phạm vi).
- **Owner quyết định** hướng xử lý 40 failure test-main × code-#210 (mục riêng hay bỏ qua).
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
