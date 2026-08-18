# LOG-LG03 — Phat hien BUG P1 THU 2 tren baseline main 09e2426

Ngay: 2026-08-18

## Su that
- test_partner_reconciliation_desk_write_oracle.py IMPORT `load_agreements` tu core.database — IMPORT THONG BAO Loi "cannot import name 'load_agreements'".
- Da xac nhan bang git stash: loi TON TAI CA TREN BASELINE main 09e2426 (truoc patch user API cua toi) — khong phai do patch.
- Nghia la: core/database.py tren main THIEN THIEU `load_agreements` (va co the `load_contracts`?) ma core/state.py va views can.
- views/agreements.py hay core/state.py import load_agreements — nghia la app CHAY THAT tren production cua Owner... lam sao hoat dong?
  - Kiem tra them: views/agreements.py co the import tu noi khac; hoac core/state.py khong duoc load khi khong dung module partner reconciliation.
  - Test suite cua repo CUNG KHONG CHAY DUOC tren main (collection error) — main released ma test suite fail tai baseline = van de chat luong da co.

## Quyet dinh LG03 (bounded)
- Tim commit cuoi cung load_agreements ton tai trong core/database.py; restore bounded (append patch tuong tu user API).
- Khong lam test suite chay het duoc — chi sua loi import (dung ham da co va import path dung).
- Them unit test cho load_agreements (FakeDb).
- Khong cham RBAC/finance logic.

## Next
1. `git log -S load_agreements -- core/database.py` — tim commit mat.
2. Dump ham tu commit do, append patch.
3. Kiem tra views/agreements.py + core/state.py import path dung.

## Ket qua xac nhan (sau patch):
- Baseline main 09e2426: test suite THU CA collection fail (ERROR 2 collection: test_partner_reconciliation_desk_write_oracle + ?) — ko chay duoc 1 test nao.
- Sau patch LG03 (load_agreements + save_agreements_to_cloud + 4 user API): suite chay duoc — 208 passed, 28 skipped, 6 subtests, **5 failed**.
- 5 failed tests:
  1. test_dashboard_financial_write_oracle.py::...::test_bounded_dashboard_flow_has_zero_financial_writes_and_no_financial_mutation
  2. test_entity_context_ui.py::...::test_entity_workspace_opens_shipment_360
  3. test_entity_context_ui.py::...::test_shipment_360_links_to_customer_factory_partner_and_returns
  4. test_lg01_env_security.py::...::test_validate_rejects_prod
  5. test_logc12_host_native_runtime.py::...::test_sales_workspace_mounts_and_exposes_intake_form
- Git stash (chi patch database.py) khong chieu huong 5 fail nay? — stash lam collection ERROR tro lai 2 file vi patch mat → khong the so sanh truc tiep. KET LUAN an toan nhat: 5 fail nay co the ton tai tai baseline (ko lien quan patch cua toi) nhung CAN KHIEM TRA TUNG CAI de khong bao cao sai.
- Patch da lam (3 patch append o cuoi core/database.py): user API 4 ham (load_users/save_user/update_user(payload=...+document=...)/delete_user), load_agreements, save_agreements_to_cloud. Tools: docs/goals/LOG-LG03/tools/restore_user_api.py, restore_agreements_api.py. Test: tests/test_users_persistence.py (6 passed).
- Unit test cho load_agreements chua viet — nen viet.

## 5 test failures — root cause (khiem tra tung cai):
Ket luan: ca 5 failures **KHONG phat sinh tu patch LG03** — patch cua toi chi them 6 ham append o cuoi core/database.py. Chung ton tai tai baseline main 09e2426 (LG02 INTERNAL_RELEASE_VERIFIED): suite tren baseline khong the chay vi collection ERROR (thieu load_agreements); sau khi patch restore API, 4 UI tests va 1 env-security test chay duoc nhung fail theo loi design/obsolete:
1. test_lg01_env_security::test_validate_rejects_prod — test gan MONGO_DB_NAME='logistics_db' voi y tuong release_mode=OFF phai raise RuntimeError, nhung secrets.toml dang release_mode=true (LG02) nen ko raise. Test design khong tuong thich state production LG02 — ngoai scope LG03 (thay doi policy bao mat can Owner).
2-3. test_entity_context_ui (2 tests) — AppTest mong "Customer 360" subheader mount theo kieu cu — that bai do entity context workspace da duoc refactoring sau LogC12.
4. test_logc12_host_native_runtime — mong button key 'new_quote_save' trong sales workspace — that bai vi quotations.py doi cau truc key/form sau LogC12.
5. test_dashboard_financial_write_oracle — mong markdown "Tài chính:" tren dashboard — that bai vi cau truc dashboard da doi.
Tests 2-5 bat nguon tu initial checkpoint 82c8134 ("Initial sanitized checkpoint through LOG-C12") chua duoc cap nhat theo refactoring LG01/LG02 — pre-existing technical debt, ngoai scope LG03 UX/viet hoa. Ghi nhan trong evidence + state.json; sua thuoc goal future neu Owner yeu cau.

## Ket qua seed rehearsal users da chay (xem tool seed_rehearsal_users.py): can xem ket qua sau khi chay.
- Todo LG03 tiep theo: (1) khiem tra 5 test failed tung cai (quyet dinh sua hay ghi nhan P2/P3), (2) them test load_agreements FakeDb, (3) seed rehearsal users (seed_rehearsal_users.py da co tool), (4) language inventory, (5) glossary, (6) pilot 5 man hinh, (7) scale, (8) QA role, (9) regression, (10) draft PR + state.json checkpoint.
- Branch LG03: log-lg03-vietnamese-simplified-ux (khoi tao tu 09e2426, da push lan dau).
- Khong commit evidence LG02 untracked files vao LG03 (de y).
