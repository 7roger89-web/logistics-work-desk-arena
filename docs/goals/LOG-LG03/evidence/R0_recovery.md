# LOG-LG03 — CHECKPOINT_RECOVERY (Phase 0)

Ngày: 2026-08-18 (Owner phê duyệt "APPROVE LOG-LG03")

## Git truth (đã xác thực từ remote origin)
- CURRENT_MAIN_SHA = 09e2426 (origin/main) — "LG02: evidence — mojibake resolved on Owner machine"
- rc SHA = 4633711 (origin/log-lg01-multi-user-internal-rc)
- Divergence: main chỉ hơn rc 1 commit (evidence file); rc hơn main 8 commits (fix_vietnamese.py, reset_admin.py...)
- LG02 released_main_sha = 724ea38 (trong state LG02)
- Production release baseline cho LG03 = origin/main 09e2426 (LG02 state.json INTERNAL_RELEASE_VERIFIED)
- Branch LG03 mới: log-lg03-vietnamese-simplified-ux, tạo từ origin/main 09e2426 (verified release baseline)
- LG02 state.json đã lưu tại docs/goals/LOG-LG02/state.json (không ghi đè, chỉ đọc)
- Working tree: sạch (chỉ có untracked evidence LG02 cũ, sẽ không commit vào LG03)

## Cấu trúc repo
- views/: 22 module UI (web_app.py = điều hướng/sidebar chính; dashboard, review_queue, shipment, customers, quotations, agreements, contracts, finance, finance_review, partner_reconciliation, reports, tariff, tracking, knowledge_base, entity_context, sales, tracking, proxy_payment, entrustment, partner_finance, historical_review, shipment_360...)
- core/: auth.py (ROLE_PERMISSIONS: admin{"*"}, sale, support, accounting, operations, sales, viewer), config.py, database.py, users.py, state.py, logic.py, validators.py...
- tests/: 35+ file unit test (playwright test suite riêng)
- app.py (entry chuẩn), web_app.py (launcher 4 dòng)

## UI route map (ROUTES trong views/web_app.py, dòng 37-51)
1. Dashboard (ui_dashboard)
2. Review Queue (ui_review_queue)
3. Tạo Lô Mới (ui_create_new_shipment)
4. Khách Hàng (ui_customers)
5. Entity Context (ui_entity_context) — TIẾNG ANH
6. Sales & Báo Giá (ui_sales_module) — MIXED
7. Thỏa Thuận & Bàn Giao (ui_agreements_module)
8. Hợp Đồng (ui_contracts_management)
9. Thu Tiền & Công Nợ (ui_receivables_management)
10. Finance Review (ui_finance_review) — TIẾNG ANH (hợp đồng gợi ý "Đối soát tài chính")
11. Công nợ A Bò (ui_partner_reconciliation_desk)
12. Báo Cáo CEO (ui_reports_dashboard)
13. Tra Cứu Thuế (ui_super_tariff_hub)
14. Tracking (ui_tracking_tool) — TIẾNG ANH
15. Sổ Tay Kinh Nghiệm (ui_knowledge_base)
16. Người Dùng (admin, ui_user_management)

Nhóm điều hướng: OPERATIONS (Dashboard, Review Queue, Tạo Lô Mới, Tracking, Khách Hàng, Entity Context), COMMERCIAL CONTEXT (Sales & Báo Giá, Thỏa Thuận & Bàn Giao, Hợp Đồng, Thu Tiền & Công Nợ...) — kiểm tra nhóm thực tế tại dòng 164-182.

## Role model (core/auth.py ROLE_PERMISSIONS, dòng 67+)
- admin: {"*"} — quản trị, finance actual write, user admin
- sale: dashboard, shipment_create/edit, customers, sales, sales_write, contracts, tariff, tracking, knowledge, shipment_360_read, entity_context, commercial_view, commercial_write — KHÔNG finance write, KHÔNG delete
- support: dashboard, shipment_edit, customers, shipment_360_read, entity_context, contracts, tariff, tracking, knowledge, commercial_view, finance_view, operations_write — read-only finance, KHÔNG delete
- accounting, operations, sales, viewer (legacy)
- _role_permissions fallback = viewer

## Production DB (read-only baseline từ LG02 R1, chưa kiểm tra lại)
- logistics_db: customers 362, shipments 78, audit_logs 54, contracts 6, users=1 (admin Owner), canonical finance collections = 0 docs
- LG03 rule: PRODUCTION DATA MUTATION = 0; QA trên DB rehearsal local (mongod đang chạy)

## Ghi chú encoding LG03
- Source phải UTF-8 sạch (LG02 đã fix mojibake toàn repo, 0 FFFD)
- Section 25: không "sửa" mojibake bằng double-encoding; có thể thêm .editorconfig UTF-8
- Kiểm tra: git diff encoding scan, browser output
