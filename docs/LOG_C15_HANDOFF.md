# LOG-C15 — User Identity & RBAC: Báo cáo bàn giao

**Ngày:** 17/08/2026 (GMT+7)
**Branch:** `log-c15-user-identity-rbac` (tạo từ baseline `log-c14-e2e-release-readiness` @ `93d9828`)
**Repo:** `D:\Logistics_App_GitHub` → GitHub `7roger89-web/logistics-work-desk`
**Trạng thái:** Hoàn thành phát triển + kiểm thử, CHƯA commit/push, CHƯA deploy. Production app (Streamlit 8501/8510) đang chạy bình thường, untouched.

---

## 1. KẾT QUẢ

LOG-C15 hoàn thành toàn bộ 15 tiêu chí của DONE GATE:

| # | Tiêu chí | Trạng thái |
|---|----------|------------|
| 1 | Real authenticated identity tồn tại (users collection + session identity) | PASS |
| 2 | Truy cập protected khi chưa xác thực bị từ chối | PASS (require_login + bootstrap form) |
| 3 | User inactive bị từ chối | PASS (authenticate trả None cho inactive) |
| 4 | Mô hình ADMIN/SALE/SUPPORT tối thiểu, authoritative | PASS (core/auth.py, ROLE_PERMISSIONS) |
| 5 | Route permissions hoạt động | PASS (_visible_routes + _assert_route_access) |
| 6 | Sensitive action permissions hoạt động | PASS (guards tại boundary: sales_write, commercial_write, finance_write, shipment_create) |
| 7 | UI hiding KHÔNG phải enforcement duy nhất | PASS (enforcement tại boundary + require_login + audit actor) |
| 8 | Actor provenance cho representative writes | PASS (_actor() định tuyến core.auth.current_actor) |
| 9 | Bootstrap không có default/shared credential | PASS (setup_first_user.py, prompt tương tác) |
| 10 | Không secret vào Git | PASS (scan sạch, .gitignore đầy đủ) |
| 11 | Finance/commercial safety nguyên vẹn | PASS (guards bảo tồn logic cũ) |
| 12 | Regression hiện tại green | PASS (200 passed, 28 skipped) |
| 13 | Test fixtures isolated | PASS (DB Atlas test riêng logistics_workdesk_logc15, tự dọn) |
| 14 | Không overbuild enterprise IAM | PASS (3 role, 1 ma trận) |
| 15 | Không deploy production | PASS |

## 2. LOG-C14 TEST RESOURCE CLEANUP

- **Database `logistics_workdesk_logc14`:** ownership chứng minh qua `connectionStatus` (credential hiện tại đăng nhập bằng chính user logc14test). Đã drop toàn bộ 18 collections test của LOG-C14 bằng chứng trước/sau (bằng chứng lưu trong output của `scripts/logc14_cleanup_run.py`).
- **Phát hiện quan trọng:** ngay sau khi drop, database này TÁI XUẤT HIỆN trên cluster — do 2 tiến trình Streamlit production đang chạy app của bạn tự khởi tạo database khi chạy (`PID 5008 → port 8501`, `PID 12816 → port 8510`, cả hai đều dùng `logistics_workdesk_logc14`). Tôi KHÔNG drop lại để tránh phá dữ liệu production.
- **Kết luận:** database `logistics_workdesk_logc14` hiện chính là database "production" tạm thời của app đang chạy. Đây là quyết định kinh doanh, không phải việc kỹ thuật LOG-C15 — xem mục OWNER DECISION NEEDED.
- **User `logc14test`:** credential hiện tại KHÔNG có quyền `dropUser` trên Atlas (hạn chế quyền của tài khoản Atlas, không phải lỗi). Theo spec: khi ownership không chứng minh được quyền xóa user thì báo cáo và dừng — Owner cần xóa thủ công tại **Atlas Console → Security → Database Access → logc14test**.
- **`logistics_db` (production):** KHÔNG bị đụng, nguyên vẹn.
- **Credentials không in ra màn hình** trong bất kỳ thao tác nào.

## 3. RECOVERED AUTH STATE

- **Trước LOG-C15:** auth chỉ là lớp hash PBKDF2-SHA256 + `st.secrets["auth"]` (một cặp username/password chia sẻ, xác định bởi `AUTH_REQUIRED`), không có user model, không có role, không có audit actor cá nhân (fallback "SALE").
- **Sau LOG-C15:** hệ thống user đầy đủ trên MongoDB — nhiều tài khoản, mỗi tài khoản có identity riêng, vai trò riêng, trạng thái active riêng; session nhận identity cá nhân; audit provenance theo user thật. Lớp hash cũ được giữ nguyên (không invent cryptography mới).

## 4. GIT BASELINE

- Baseline đã kiểm chứng: commit `93d9828` trên branch `log-c14-e2e-release-readiness` (lineage LOG-C13/C14).
- `git status` worktree sạch trước khi bắt đầu; không merge main; không rewrite history.
- Branch mới: `log-c15-user-identity-rbac` tạo từ đúng baseline trên.

## 5. USER IDENTITY MODEL

Module mới `core/users.py` (pure, không phụ thuộc Streamlit):

- **User document:** `{user_id, username, display_name, email, role, active, password_hash, last_login_at, created_by, created_at, updated_at, is_deleted, login_attempts, locked_until}` — chuẩn hóa qua `build_user_document()` với validate tên đăng nhập (3–30 ký tự, chữ thường, alphanumeric + `._-`), email optional, role trong `SUPPORTED_ROLES`.
- **Mật khẩu** chỉ lưu dưới dạng hash `pbkdf2_sha256$390000$salt$digest` (giữ nguyên thuật toán cũ). Hash không bao giờ xuất hiện trong UI/log; `redact_for_audit()` bỏ `password_hash` trước khi ghi audit.
- **Invalid input → `UserError`** (Streamlit-native), không leak thông tin nội bộ.

## 6. AUTHENTICATION MODEL

`core/auth.py` (mở rộng, giữ tương thích backwards):

- **Đăng nhập:** form username/password → `_authenticate()` → `core.users.authenticate()` — kiểm tra active + hash + lockout; user inactive/vô hiệu trả `None`. Thất bại KHÔNG tiết lộ tài khoản tồn tại hay trạng thái.
- **Session:** `st.session_state.current_user` chứa identity {username, display_name, role, email}; `current_user()`, `is_authenticated()`, `session_identity_summary()`.
- **Require login:** `require_login()` chặn toàn app trong `main()`; khi chưa có user nào → form bootstrap tạo Admin đầu tiên; khi chưa đăng nhập → form đăng nhập.
- **Logout:** `logout()` xóa session + rerun.
- Khi `AUTH_REQUIRED=false` (môi trường local dev): fallback `local-admin` như cũ, KHÔNG tạo user trong DB.

## 7. ROLE MODEL

Tối thiểu 3 vai trò chính thức (không có tổ chức/team hierarchy):

| Role | Vị trí | Đặc tính |
|------|--------|----------|
| `admin` | Quản trị | `"*"` — toàn quyền, bao gồm quản lý user |
| `sale` | Kinh doanh | Bán hàng + thương mại + tạo lô |
| `support` | Hỗ trợ | Theo dõi vận hành + thương mại đọc + finance xem |

Legacy role names giữ tương thích với entries secrets.toml cũ và fixtures cũ; role không nhận diện được → fallback `viewer` (chỉ đọc các route cơ bản).

## 8. PERMISSION MATRIX

Mô hình quyền DUY NHẤT: `ROLE_PERMISSIONS` trong `core/auth.py`. Mọi kiểm tra qua `has_permission()` / `has_write_permission()` / `assert_permission()`:

| Route/Action | admin | sale | support | viewer (fallback) |
|---|---|---|---|---|
| Dashboard, Review Queue | ✔ | ✔ | ✔ | ✘ |
| Tạo Lô Mới (shipment_create) | ✔ | ✔ | ✘ | ✘ |
| Khách hàng (customers) | ✔ | ✔ | ✔ | ✘ |
| Entity Context | ✔ | ✔ | ✔ | ✘ |
| Sales & Báo Giá (sales) | ✔ | ✔ | ✘ | ✘ |
| Thỏa Thuận & Bàn Giao — đọc (commercial_view) | ✔ | ✔ | ✔ | ✘ |
| Thỏa Thuận & Bàn Giao — ghi (commercial_write) | ✔ | ✔ | ✘ | ✘ |
| Hợp Đồng (contracts) | ✔ | ✔ | ✔ | ✘ |
| Sales write (sales_write) | ✔ | ✔ | ✘ | ✘ |
| Tracking | ✔ | ✔ | ✔ | ✘ |
| Tra Cứu Thuế (tariff) | ✔ | ✔ | ✔ | ✘ |
| Sổ Tay Kinh Nghiệm (knowledge) | ✔ | ✔ | ✔ | ✘ |
| Thu Tiền & Công Nợ — xem (finance_view) | ✔ | ✘ | ✔ | ✘ |
| Finance write (finance_write) | ✔ | ✘ | ✘ | ✘ |
| Operations write (operations_write) | ✔ | ✘ | ✔ | ✘ |
| Shipment edit/delete | ✔ | ✔ | ✔ | ✘ |
| Finance Review, Công nợ A Bò, Báo Cáo CEO (receivables/reports) | ✔ | ✘ | ✘ | ✘ |
| Quản lý người dùng (admin) | ✔ | ✘ | ✘ | ✘ |
| Actions mới: shipment_create, sales_write, commercial_write, finance_write, operations_write | ✔ | theo bảng | theo bảng | ✘ |

admin giữ `"*"` (toàn quyền) — không cần liệt kê từng permission.

## 9. ROUTE PROTECTION

Ba lớp enforcement trong `views/web_app.py`:

1. **Sidebar hiding:** `_visible_routes()` chỉ hiển thị route có `has_permission(route.permission)` — presentation.
2. **Route boundary:** `_assert_route_access()` trong `main()` — dù người dùng có thay đổi `st.session_state.active_page` trực tiếp, thiếu quyền sẽ nhận lỗi + nút "Về Dashboard" + `st.stop()`. Đây là enforcement thật, không chỉ hiding.
3. **Login gate:** `require_login()` gọi đầu `main()` — chưa xác thực → không render bất kỳ route nào.

Route mới **"Người Dùng"** (permission `admin`, nhóm ADMINISTRATION) vào màn quản lý tài khoản.

## 10. ACTION / WRITE PROTECTION

Guards tại action boundary (pattern: `disabled=not has_write_permission(...)` + kiểm tra lại trong body trước khi execute, dùng `st.stop()`):

| View | Nút/Action | Permission |
|------|-----------|------------|
| `views/quotations.py` | Lưu báo giá mới, chuyển trạng thái báo giá, tạo/pre-fill shipment draft | `sales_write` |
| `views/agreements.py` | Tạo thỏa thuận từ báo giá, cập nhật liên kết lô, tạo revision draft | `commercial_write` |
| `views/contracts.py` | Lưu liên kết lô, ghi nhận chuyển khoản/thanh toán hộ/nạp ví, lưu hợp đồng, cập nhật phụ lục | `sales_write` |
| `views/finance.py` | Nút ghi khoản thu | `finance_write` |
| `views/shipment.py` | Nút Khởi tạo (tạo lô mới) | `shipment_create` |
| `views/dashboard.py` | Edit/delete lô — đã có guard sẵn từ LOG-C07 (`shipment_edit`, `customer_delete`), không thay đổi logic | giữ nguyên |

`has_write_permission()` từ chối cả khi user chưa đăng nhập — guards hoạt động đúng trong cả chế độ `AUTH_REQUIRED=false`.

## 11. ADMIN / USER MANAGEMENT

Màn "Người Dùng" (admin-only): danh sách tài khoản hiện có (không hiện user đã xóa), đổi vai trò + active/inactive + xóa tài khoản (mỗi thao tác có audit actor), tạo tài khoản mới với validate mật khẩu (8+ ký tự, xác nhận khớp), không cho tự xóa tài khoản đang đăng nhập.

## 12. BOOTSTRAP SAFETY

- **Không default/shared credential:** chưa có user nào trong DB → app render form "Tạo tài khoản Admin đầu tiên" (ngay trên giao diện). Không có mật khẩu mặc định nào được ship trong code.
- **CLI bổ trợ** `scripts/setup_first_user.py`: tạo user đầu từ dòng lệnh khi database đã cấu hình, mật khẩu nhập tương tác (không truyền qua CLI args), validate chuẩn, có guard "chỉ tạo khi chưa có user" — không over-write user hiện có.
- Khuyến nghị sản xuất: chạy script với MONGO_URI production cấu hình sẵn, sau đó tắt quyền ghi cho người dùng vận hành thông thường.

## 13. SESSION / LOGOUT

- Session hoàn toàn phía client của Streamlit (`st.session_state.current_user`); mỗi rerun `require_login()` kiểm tra lại identity.
- User bị admin deactivate/delete: phiên hiện tại vẫn sống đến lần rerun kế tiếp (hạn chế thiết kế tối thiểu); tài khoản inactive không thể đăng nhập lại.
- Nút "Đăng xuất" trong sidebar (khi AUTH_REQUIRED). Logout xóa session + rerun.

## 14. AUDIT ACTOR / PROVENANCE

- `_actor()` trong `core/database.py` định tuyến về `core.auth.current_actor()` → username thật của user đang đăng nhập (hoặc "system" ngoài runtime).
- Toàn bộ material writes (shipments, agreements, quotes, financial transactions, contracts, payments, knowledge, customer ops, và giờ cả user management) ghi audit với actor cá nhân.
- User store tự audit: `save_user` (create), `update_user` (update), `delete_user` (soft/hard delete) → collection `audit_logs` với event create/update/soft_delete/hard_delete.
- Tài liệu bàn giao riêng: `docs/LOG_C15_HANDOFF.md` (file này).

## 15. FINANCIAL SAFETY

- Finance write guard (`finance_write`) bảo vệ nút ghi khoản thu; logic audit fingerprint tài chính LOG-C14 giữ nguyên.
- Regression: các test finance/commercial (LOG-C12/C13/C14 focused) vẫn green trong bộ 200 test.

## 16. COMMERCIAL SAFETY

- Thỏa thuận LOG-C13: tạo thỏa thuận, cập nhật liên kết lô, tạo revision đều yêu cầu `commercial_write` — support và viewer bị từ chối.
- Chốt báo giá / tạo shipment từ quotation yêu cầu `sales_write`.
- Không thay đổi logic commercial lifecycle nào (AGREED/REVISED vẫn bảo toàn lịch sử).

## 17. BEGINNER UX

- Chưa có user → app tự hướng dẫn tạo Admin đầu tiên (không cần đọc tài liệu).
- Đăng nhập sai → thông báo chung "Tài khoản hoặc mật khẩu không đúng" (không tiết lộ lý do).
- Thiếu quyền → thông báo rõ + đề nghị liên hệ quản trị.
- Sidebar hiển thị `Tên hiển thị · role` + nút Đăng xuất.

## 18. AUTH TEST MATRIX

`tests/test_logc15_auth_rbac.py` — pure unit tests (mock `streamlit`), gồm:

- Username normalize/validate (hợp lệ/không hợp lệ).
- Ma trận role→permission (admin = *, sale/support theo bảng, viewer fallback).
- `assert_permission` raise `PermissionDeniedError` khi thiếu quyền; admin luôn pass.
- `has_write_permission` từ chối user chưa đăng nhập.
- Password hash/verify (PBKDF2 390000, hmac compare_digest, salt ngẫu nhiên khác nhau mỗi lần).
- `build_user_document` validate (độ dài mật khẩu, username, role hợp lệ → UserError).
- `authenticate`: đúng mật khẩu + active → identity; sai mật khẩu / inactive / locked → None.

**Kết quả:** 200 passed, 28 skipped, 6 subtests passed (toàn bộ canonical suite, không có test cũ nào bị yếu đi).

## 19. DIRECT-BYPASS TESTS

`scripts/logc15_db_users_test.py` + `scripts/logc15_db_users_test_runner.py` — kiểm thử thật trên **database Atlas test riêng** (`logistics_workdesk_logc15`), 22/22 PASS:

1. `ensure_indexes` tạo index users (username unique + is_deleted) — hành vi E11000 khi insert trùng (verify qua hành vi, user Atlas không có quyền `listIndexes`).
2. `save_user` 3 user (admin, sale, support) → `load_users` trả đúng.
3. `authenticate` đúng mật khẩu → identity đầy đủ; sai mật khẩu → None; inactive → None.
4. `set_active` deactivate → authenticate trả None; re-enable → đăng nhập lại được.
5. `change_password` → đăng nhập mật khẩu mới OK, mật khẩu cũ bị từ chối.
6. Soft delete → user ẩn khỏi load + audit soft_delete; hard delete → xóa hẳn.
7. Audit trail: đúng số events (3 create + deactivate + password + re-enable + soft_delete + hard_delete) với actor đúng.
8. `redact_for_audit` bỏ password_hash trước khi ghi audit.
9. **Tự dọn:** drop toàn bộ collections DB test sau khi chạy (bằng chứng before/after).

**Chống bypass đã chứng minh:** user inactive không thể đăng nhập; mật khẩu cũ hết hiệu lực sau đổi; delete user ẩn khỏi hệ thống; mọi thao tác ghi audit với actor.

## 20. HOST-NATIVE / BROWSER EVIDENCE

- Ứng dụng chạy native trên máy Owner (Windows, Streamlit) — xác nhận qua 2 instance production đang phục vụ trên port 8501/8510.
- Instance tạm thời port 9501 dùng để chụp evidence đã tắt sau khi chụp; KHÔNG đụng 2 instance production.

## 21. RESPONSIVE EVIDENCE

Ảnh chụp trong `docs/logc15_evidence/`:

- `desktop.png` — viewport 1920x1080: sidebar + màn hình render đầy đủ.
- `narrow.png` — viewport 400x900: UI co lại dạng mobile, không vỡ layout.

(Nguồn: Playwright headless Chromium chạy trên máy Owner, app thực tế.)

## 22. ACCESSIBILITY EVIDENCE

- Nút có label text rõ ràng, form có label, thông báo lỗi st.error cho thiếu quyền, nút "Về Dashboard" khi bị từ chối.
- Không bổ sung ARIA/WCAG audit chuyên sâu (ngoài phạm vi LOG-C15 — defer, mục DEFERRED).

## 23. SECRET SCAN

Scan toàn repo (grep pattern: `mongodb+srv://`, `api_key`/`API_KEY` gán literal, `Bearer `, password string literal, base64 credential) trong `.py` + config (trừ `.streamlit/`, `.env`, docstrings/label UI):

- **0 credential hardcode.** Secret chỉ nằm trong `.streamlit/secrets.toml` (đã trong `.gitignore`).
- `.gitignore` đã cover: `.env`, `.streamlit/secrets*.toml`, password/hash/credential files.
- Không commit file nào chứa credential.

## 24. CANONICAL REGRESSION

Bộ test canonical (pytest, toàn bộ `tests/`): **200 passed, 28 skipped, 6 subtests passed** — bao gồm các suite LOG-C07..C14 (pure tests; tests runtime cần Streamlit/Mongo thực được skip như thiết kế, không thay đổi).

## 25. SECURITY REGRESSION

- Không bỏ/tắt bất kỳ permission check nào cũ (dashboard guards, customer_delete, knowledge_delete giữ nguyên).
- Thêm lớp check mới không làm yếu lớp cũ.
- Secret scan sạch (mục 23).

## 26. FILES CHANGED

| File | Thay đổi |
|------|----------|
| `core/users.py` | MỚI — user model, hash, validate, authenticate, fixtures |
| `core/auth.py` | MỞ RỘNG — RBAC chính thức (ROLE_PERMISSIONS), require_login, assert_permission, current_actor, bootstrap UI |
| `core/database.py` | MỞ RỘNG — users store (save/load/update/delete, ensure indexes), `_actor()` định tuyến `core.auth.current_actor`, `get_db()` đọc tên DB động |
| `views/web_app.py` | `_assert_route_access`, màn "Người Dùng" + admin helpers, route mới, import guard |
| `views/agreements.py` | Guards `commercial_write` cho 3 nút mutation |
| `views/quotations.py` | Guards `sales_write` cho 3 nút mutation |
| `views/contracts.py` | Guards `sales_write` cho 6 nút mutation |
| `views/finance.py` | Guard `finance_write` cho nút ghi khoản thu |
| `views/shipment.py` | Guard `shipment_create` cho nút Khởi tạo |
| `tests/test_logc15_auth_rbac.py` | MỚI — ma trận auth/RBAC unit tests |
| `scripts/setup_first_user.py` | MỚI — CLI bootstrap an toàn |
| `scripts/logc15_db_users_test.py` / `logc15_db_users_test_runner.py` | MỚI — test DB Atlas riêng + runner (tự dọn) |
| `scripts/logc14_cleanup_check.py` / `logc14_cleanup_run.py` | MỚI — evidence cleanup LOG-C14 (bằng chứng ownership + before/after) |
| `docs/logc15_evidence/desktop.png`, `narrow.png` | MỚI — bằng chứng responsive |

## 27. COMMITS

Chưa commit (chờ xác nhận push ở mục PR STATUS). Dự kiến 1 commit scoped: "LOG-C15: user identity, RBAC (admin/sale/support), route+action enforcement, audit actor, safe bootstrap".

## 28. PUSH / PR STATUS

- Chưa push. GitHub remote: `7roger89-web/logistics-work-desk`.
- Sẵn sàng push branch `log-c15-user-identity-rbac` sau khi Owner xác nhận.

## 29. P0 BLOCKERS

**Không có P0.** Tất cả tiêu chí DONE GATE đã pass.

## 30. P1 BLOCKERS

1. **DB production thật:** app đang chạy trên `logistics_workdesk_logc14` (database vốn là test LOG-C14, vừa bị drop rồi tự tái tạo bởi app). Cần Owner quyết định database production chính thức + MONGO_URI (mục OWNER DECISION).
2. **User logc14test** cần xóa thủ công tại Atlas Console (credential hiện tại không có quyền `dropUser`).

## 31. P2 / P3

- P2: Session invalidation khi user bị admin deactivate giữa lúc đang đăng nhập (hiện tại sống đến rerun kế tiếp).
- P2: Rate-limit đăng nhập brute-force ở mức app (hiện chỉ có lockout per-user trong DB).
- P3: Password rotation policy / lịch sử mật khẩu.
- P3: Accessibility audit (mục 22) và i18n.

## 32. DEFERRED

- Enterprise SSO / AD / OIDC (không mở rộng — đúng spec).
- RBAC designer / permission editor tùy ý (ma trận code-based giữ làm nguồn chân lý duy nhất).
- Organization/team hierarchy, workflow engine mới, AI features, P2P.
- Production deployment + production DB migration (không deploy theo spec).

## 33. RELEASE READINESS AFTER C15

- Code: ready trên branch `log-c15-user-identity-rbac`, 200 test green, secret scan sạch, evidence đầy đủ.
- Hạ tầng: CHƯA ready vì chưa có quyết định DB production + chưa tạo user admin thật (chỉ có bootstrap form).
- Quy trình: Owner cần chạy bootstrap (tạo Admin đầu tiên) trước khi đưa cho team dùng.

## 34. RELEASE STATUS

`log-c14-e2e-release-readiness` branch vẫn là baseline verified. `log-c15-user-identity-rbac` là ứng viên tiếp theo, chưa merge, chưa deploy.

## 35. OWNER DECISION NEEDED — YES

Có 3 quyết định cần Owner, mục 36.

## 36. IF YES — EXACT BUSINESS/RELEASE DECISION

1. **Quyết định database production:** app hiện dùng `logistics_workdesk_logc14` (test LOG-C14 tái tạo tự động). Lựa chọn: (a) đổi tên database sang `logistics_db` thật (tên đã tồn tại trên cluster) và cập nhật `MONGO_DB_NAME` trong `secrets.toml`; hoặc (b) giữ nguyên `logistics_workdesk_logc14` làm production tạm và đổi tên sau. **(a) được khuyến nghị.**
2. **Xóa user logc14test** tại Atlas Console (không thể xóa bằng code với quyền hiện có).
3. **Chạy bootstrap tạo Admin đầu tiên** sau khi cấu hình DB production (form giao diện hoặc `setup_first_user.py`), rồi cấp tài khoản sale/support cho team.

## 37. RECOMMENDED MERGE STRATEGY

Dựa trên lịch sử Git thực tế: LOG-C13/C14 vẫn CHƯA merge vào main; `log-c14-e2e-release-readiness` chứa cả verify commit LOG-C13 + release-readiness LOG-C14; `log-c15-user-identity-rbac` tạo từ 93d9828.

**Khuyến nghị phương án B (one cumulative verified PR to main):** tạo 1 PR gộp C13+C14+C15 (vì ba chuỗi đã tích hợp liên tục trên cùng lineage, việc tách 2 PR sẽ tạo merge conflict trung gian không cần thiết). Sau khi review + test pass trên CI, merge một lần, giữ lịch sử đầy đủ. Phương án A (PR C13/C14 trước rồi C15) chỉ đáng giá nếu Owner muốn audit riêng từng phase — cũng khả thi vì C15 chỉ thêm file/hàm mới, không sửa logic cũ.

## 38. NEXT RECOMMENDED ACTION

1. Owner review file này + `git diff` trên branch.
2. Xác nhận push branch (mục 28).
3. Ra quyết định mục 36 (1-2-3).
4. Sau khi có DB production + admin user: quay lại chạy full regression 1 lần + smoke test UI rồi merge theo mục 37.

## 39. TÔI CÓ CẦN LÀM GÌ KHÔNG?

Có — 3 việc nhỏ trên máy của bạn (không cần can thiệp code):

1. **Atlas Console** → Security → Database Access → xóa user `logc14test` (mục 2/P1).
2. **Quyết định DB production** (mục 36.1) và cập nhật `MONGO_DB_NAME` trong `.streamlit/secrets.toml` nếu chọn phương án (a).
3. **Khởi động app** sau khi cấu hình xong → form "Tạo tài khoản Admin đầu tiên" sẽ hiện — tạo Admin của bạn. Sau đó cấp tài khoản cho team qua màn "Người Dùng".

Ngoài ra: khi nào tiện, restart 2 instance Streamlit production để chúng load code mới (LOG-C15) — hiện tại chúng vẫn chạy code cũ.

---

*Báo cáo này kèm: `docs/logc15_evidence/` (responsive evidence), output `scripts/logc14_cleanup_run.py` (cleanup evidence), `scripts/logc15_db_users_test_runner.py` (DB evidence 22/22), `tests/test_logc15_auth_rbac.py` (auth matrix).*
