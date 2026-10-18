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
- **Lộ trình**:
  - (0) 3 bug node truth — **XONG** (`61f0714`): booking `done=bool(booking) and booking_status=='ACCEPTED'`; on-board `done=bool(atd) and bool(on_board_at)`; si-vgm chặn FCL đối xứng gate-in.
  - (1) diệt false-done — **một phần XONG** (`d1340a5`): JourneyBubble docs (FILE_PRESENT ≠ DOCUMENT_ACCEPTED), ô nhập `booking_status`/`on_board_at`, "CẦN LÀM" ra mặt tiền + "Chưa có hướng dẫn cho công đoạn này". Kiểm tiếp các surface khác nếu có biểu thức false-done.
  - (2) backport #200/#204/#208 vào #210 — **CHƯA**.
  - (3) commercial-flow + legal parties + 2 stage `entrustment-ready`/`tt-warehouse-handover` (CHỈ TT_ENTRUSTED_SUB) — **CHƯA**.
  - (4) nội dung công đoạn (guidance) — **CHƯA** (UI đã nhận `n.guidance`; hiện trống nên hiển thị "Chưa có hướng dẫn cho công đoạn này").
  - (5) E2E + UAT + merge — **CHƯA**.
- **Sự thật kỹ thuật**: facts `booking_status`, `on_board_at` ghi được qua writer `shipment_sea_facts_save` + ô nhập metadata-driven tại node booking/on-board. Bundle frontend `9aeb` giữ nguyên (chưa build lại). Trên cây tích hợp #210: **40 failed / 1920 passed / 45 skipped** — 40 failure còn lại là xung đột test-main × code-#210 có sẵn (188/186/190, `test_visual_shipment_workspace::test_same_attachment...`), cần mục riêng nếu Owner muốn #210 xanh full suite.

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

### 2026-10-19

- **Commit SHA**: `61f0714` (đợt 1), `97254e9` (tích hợp base `408b980` của #210), `d1340a5` (đợt 2), `455351b` (rule AGENTS.md) + commit chứa file handoff này (sha đầy đủ trong receipt `HANDOFF_UPDATE=` của báo cáo task).
- **Đã làm**: (1) sửa 3 lỗi "báo xong khi chưa xong" ở `core/shipment_journey.py` + 13 test; (2) tích hợp base #210 vào nhánh session để sửa file chỉ có trên #210; (3) sửa P0 JourneyBubble docs (có tệp ≠ có bằng chứng), thêm ô nhập `booking_status`/`on_board_at`, đưa `what_to_do`/`done_when` ra mặt tiền QuickPanel + fallback "Chưa có hướng dẫn cho công đoạn này", 6 test mới; (4) đưa quy tắc cập nhật handoff vào `AGENTS.md` (ngoài block P2P managed) + tạo file handoff này.
- **Còn lại**: lộ trình (2)→(5) theo MỤC 3; xử lý 40 failure test-main × code-#210; browser lane cho UI (bundle refresh); scope-guard 2 fact mới trong `views/logi_view_model.py` (đã nêu từ đợt 1, chưa đụng vì ngoài phạm vi).
- **Cần Owner**: các mục MỤC 5 + xác nhận thứ tự lộ trình tiếp theo + duyệt build lại bundle `9aeb` hay không.
