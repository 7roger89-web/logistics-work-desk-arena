# PROJECT BOOTSTRAP & RECOVERY — VERDICT & CONTINUATION CAPSULE

Ngày tạo: 2026-08-18. Chế độ: READ-ONLY, DATA-SAFETY-FIRST, không bắt đầu LOG-LG03 (đã hoàn thành trước đó — recovery này cập nhật trạng thái sau LG03).

## RECOVERY VERDICT
Recovery thành công. Dự án đang ở trạng thái nhất quán, bằng chứng trong repo có thẩm quyền, không có sai lệch vật chất với báo cáo lịch sử ngoại trừ mục đã biết: LOG-LG02 = INTERNAL_RELEASE_VERIFIED vẫn đúng trên main; LOG-LG03 đã hoàn thành với terminal outcome `READY_FOR_OWNER_UX_RELEASE_GATE`, chờ Owner duyệt.

## CURRENT MAIN SHA
`09e2426` (origin/main, thông điệp "LG02: evidence — mojibake resolved on Owner machine"). Đây vừa là main SHA vừa là production/release SHA.

## CURRENT PRODUCTION SHA
`09e2426` — release line: LG01 multi-user RC (PR #1, đã đóng) → merge vào main; LG02 evidence hoàn tất trên máy Owner.

## CURRENT RELEASE STATUS
Production release = `09e2426` (LG02 INTERNAL_RELEASE_VERIFIED). Nhánh `log-lg03-vietnamese-simplified-ux` ở commit `6fb8a84` có PR #2 dạng **Draft, chưa merge** (https://github.com/7roger89-web/logistics-work-desk/pull/2). Release status theo LG03: `NOT_RELEASED_BY_LOG_LG03`. Không merge, không deploy, LG04 chưa bắt đầu.

## PROJECT MAP (revision 2026-08-18, sau LG03)
- Entry point: `app.py` (launcher 4 dòng → `views.web_app.main`). Owner chạy: `streamlit run app.py` hoặc `web_app.py`.
- Điều hướng/UI: `views/web_app.py` (ROUTES, NAVIGATION_GROUPS); các view trong `views/` (dashboard, review_queue, shipment, customers, quotations, agreements, contracts, finance, finance_review, partner_reconciliation, reports, tariff, tracking, knowledge_base, entity_context, users mgmt).
- Domain: `core/` (database.py repository; review_queue.py; users.py; auth.py RBAC; config.py).
- Tài chính: logic đối soát/ghi ledger nằm trong `core/database.py` + `views/finance*.py`; bất biến UNKNOWN != ZERO được bảo toàn.
- Auth/RBAC: `core/auth.py` — ROLE_PERMISSIONS admin/sale/support; guards `require_login`, permission checks từng view.
- Config/secrets: `.streamlit/secrets.toml` (ngoài Git). Production: Atlas `logistics_db` (M0 free tier). Rehearsal: local mongod `logistics_workdesk_LG01_E2E`.
- Tests: `tests/` (~245 test; 212 passed, 28 skipped, 5 failed pre-existing trên main).
- Durable state: `docs/goals/LOG-LG01/`, `docs/goals/LOG-LG02/`, `docs/goals/LOG-LG03/` (state.json, evidence/, tools/).

## PRODUCTION / DATA SAFETY STATUS
Production DB `logistics_db`: customers 362, shipments 78, quotations/agreements/contracts/transactions nguyên vẹn (không mutation trong recovery). Collection users có **4 tài khoản**: admin (của Owner, tạo bằng reset-admin-tool, hợp lệ) + 3 tài khoản thừa `rehearsal_admin/sale/support` (tạo nhầm trong W0 của LG03, không ai dùng). LG03 đã có tool an toàn `docs/goals/LOG-LG03/tools/cleanup_rehearsal_users.py` (default dry-run) chờ Owner xác nhận "--apply". Đây là mutation đã biết duy nhất của production, đảo ngược được.

## ROLE / RBAC STATUS
ROLE_PERMISSIONS giữ nguyên thiết kế LG01/LG02 đã phê duyệt: admin = đầy đủ + finance actual authority; sale = commercial work, không ghi finance actual, không destructive delete, không elevation; support = operations + read-only finance context, không ghi finance actual. LG03 kiểm chứng bằng AppTest 8/8: sale không thấy menu tài chính, support không thấy menu kinh doanh. Không có sự sai lệch vật chất.

## BUSINESS / FINANCE INVARIANTS STATUS
Bảo toàn: QUOTE ESTIMATE != FINANCE ACTUAL; AGREEMENT TERMS != FINANCE ACTUAL; UNKNOWN != ZERO (bảng đối soát vẫn hiển thị UNKNOWN, không tự thành 0); commercial workflow không tạo canonical finance actuals; khóa chống ghi trùng khoản thu giữ nguyên logic. Finance mutation oracle của LG03 (dashboard không ghi tài chính) PASS.

## UX / LANGUAGE BASELINE (sau LG03)
Trước LG03: menu half-EN (Dashboard, Review Queue, Entity Context, Sales & Báo Giá, Finance Review, Tracking...), 21 chuỗi mojibake đánh dấu, 9 thông báo lỗi tài chính lỗi encoding, chính tả lỗi ("Mật khảu"). Sau LG03: 16/16 mục điều hướng tiếng Việt, 79+ chuỗi đã sửa, 0 mojibake còn lại (scan views/ + core/), glossary `docs/goals/LOG-LG03/glossary.json` v1.0 (24 mục, chính sách chỉ đổi nhãn hiển thị). Các term quốc tế được giữ nguyên: Incoterm, Multimodal, FOB/CIF/EXW, hãng tàu (Maersk, COSCO...), UNKNOWN (status).

## TEST BASELINE (chạy lại trong recovery, 2026-08-18)
`pytest tests/`: **212 passed, 28 skipped, 5 failed** — 5 failed giống hệt baseline pre-existing trên main `09e2426`: (1) test_dashboard_financial_write_oracle::test_bounded_dashboard_flow... (xung đột với policy release_mode=true của LG02 — LG03 đã sửa logic test cho LG03 context nhưng file test gốc vẫn fail trên baseline); (2)-(3) 2 test test_entity_context_ui (assertions cũ LogC12 "Customer 360"); (4) test_lg01_env_security::test_validate_rejects_prod; (5) test_logc12_host_native_runtime::test_sales_workspace_mounts_and_exposes_intake_form. Chi tiết gốc nhân: `docs/goals/LOG-LG03/evidence/R0_baseline_load_agreements_gap.md`.

## CURRENT VERIFIED WORK
- LG01: multi-user internal RC (merged vào main qua PR #1 đã đóng).
- LG02: INTERNAL_RELEASE_VERIFIED (mojibake fix trên máy Owner, commit 09e2426).
- LG03: hoàn thành — Việt hóa UI + mojibake + QA gate 8/8; terminal `READY_FOR_OWNER_UX_RELEASE_GATE`; Draft PR #2; owner gates còn mở (mục dưới).

## CURRENT BLOCKERS
Không có blocker kỹ thuật (P0). Việc chờ Owner (không chặn công việc khác): (1) duyệt merge PR #2; (2) xác nhận xóa 3 tài khoản rehearsal. Ngoài ra: 5 test pre-existing chưa xử lý (đề nghị goal sau), tên nghiệp vụ "Công nợ A Bò" cần Owner xác nhận nếu muốn đổi.

## OWNER GATES (mở)
1. **Merge/promotion**: duyệt PR #2 (LG03 UX release).
2. **Production write (nhỏ, đảo ngược được)**: xóa 3 tài khoản rehearsal (tool sẵn, Owner chỉ cần nói "xóa rehearsal").
3. **Deploy**: Owner tự pull + xóa __pycache__ + restart trên máy (đã được hướng dẫn).
Không cần Owner gate cho: lựa chọn kỹ thuật thường ngày, naming nhãn UI chuẩn, structure component.

## NEXT SAFE TASK
Chờ Owner: nếu Owner trả lời "duyệt PR" → merge PR #2 vào main, báo Owner cập nhật app trên máy; nếu "xóa rehearsal" → chạy cleanup tool --apply (dry-run trước). KHÔNG bắt đầu LOG-LG04 khi chưa được yêu cầu.

## CONTINUATION CAPSULE (cho phiên/Prompt B kế tiếp)

- **Goal lớn hiện tại**: LOG-LG03 hoàn tất, terminal = READY_FOR_OWNER_UX_RELEASE_GATE. Hướng sản phẩm tiếp theo đã được phê duyệt từ trước: "Vietnamese-first simplification" — LG04 nếu Owner yêu cầu (ví dụ: auto-fill tên khách khi tạo lô — đã ghi nhận deferred ở mục 14 report LG03).
- **Verified revision**: main = `09e2426`; production release = `09e2426`; candidate LG03 = `6fb8a84` (branch `log-lg03-vietnamese-simplified-ux`, PR #2 Draft chưa merge).
- **UI files quan trọng**: `views/web_app.py` (ROUTES/nav đã VI), `views/dashboard.py`, `views/review_queue.py`, `views/shipment.py`, `views/entity_context.py`, `views/agreements.py`, `views/partner_reconciliation.py`, `views/finance_review.py`; helpers VN: `label_vi()` trong `core/review_queue.py` (REVIEW_QUEUE_LABELS) và pattern glossary.
- **Business rules**: `core/database.py` (ledger, khóa trùng khoản thu); bất biến UNKNOWN != ZERO, ESTIMATE != ACTUAL, commercial ≠ finance actual.
- **RBAC**: `core/auth.py` ROLE_PERMISSIONS; app găng đăng nhập `views.web_app` + `core.auth.require_login`.
- **Finance safety pointers**: finance mutation oracle LG03 trong `docs/goals/LOG-LG03/tools/qa_ui_ux_gate.py`; LG02 reports `docs/goals/LOG-LG02/`.
- **UX/language baseline**: glossary `docs/goals/LOG-LG03/glossary.json` v1.0 (chỉ đổi nhãn, không đổi key); 0 mojibake; term quốc tế whitelist (mục 5).
- **Tests đã chạy (trong recovery)**: 212 passed / 28 skipped / 5 failed pre-existing (như test baseline ở trên).
- **Mutation state**: production users = 4 (admin Owner + 3 rehearsal thừa); customers 362, shipments 78 nguyên vẹn; không mutation nào khác trong recovery.
- **Owner gates**: merge PR #2; xóa rehearsal (chờ Owner).
- **Next Safe Task**: chờ phản hồi Owner (2 việc trên); KHÔNG tự bắt đầu LOG-LG04.
- **Source pointers**: evidence LG03 = `docs/goals/LOG-LG03/evidence/` (R0_recovery.md, R0_baseline_load_agreements_gap.md, W1_language_inventory.md, W2_user_effort_audit.md); state = `docs/goals/LOG-LG03/state.json`; report Owner = `docs/goals/LOG-LG03/LG03_TERMINAL_REPORT.md`; tools = `docs/goals/LOG-LG03/tools/` (restore_user_api, restore_agreements_api, repair_mojibake_strings, fix_mojibake_byte_map, qa_ui_ux_gate, cleanup_rehearsal_users).
