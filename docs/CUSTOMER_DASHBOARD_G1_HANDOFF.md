# Customer Dashboard G1 — staging handoff

Branch: `arena/ae5f9f47-logistics-work-desk-arena` (isolated Arena working branch;
`main` was not merged and PR #211 was not touched).
Baseline HEAD: `009c87aad9238b9d95108d63398dd0aaf377a484`.
Date: 2026-10-26 (Asia/Saigon).

## 1. Luật, skill và preflight

- `P2P_LAW_SOURCE=LOCAL_PORTABLE` — portable projection hợp lệ:
  `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`,
  `SOURCE_CONTENT_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`.
  Không probe canonical law chỉ để lấy 404.
- `LAW_CHECK=PASS | SOURCE=LOCAL_PORTABLE | SOURCE_SHA256=11ce33bb9c514d32ad3aec3eb7d8b40f0d0290b1dbe79eaa15751ef34668bd4b`.
- `EXPERIENCE_CHECK=USE_ACTIVE_EXPERIENCE | IDS=shared-exp-b2611df4c9393f0017f07dcb`.
- `p2p-skill-consumption-receipt/1`:
  `[p2p-uiux]`, `.agents/skills/p2p-uiux/SKILL.md`, SHA-256
  `98f26873e48cc87e34d132478f73672a80d20b3a8e1a2256bdcdab4d6107e7b2`,
  `SKILL_CONSUMPTION=PASS`.
- `INITIAL_PLANNING_CLASSIFICATION: UIUX`.
- Câu hỏi OE đã hỏi đúng: `Không bị over engineering chứ?`. Người dùng chọn
  `smallest_slice`; `OE_VERDICT=DO_IT` cho một lát dọc login → `customers.id` →
  lọc lô → publication allowlist. Không làm React build, không app thứ hai,
  không server HTTP mới.
- `LEARNING_RECONCILIATION=RECORDED` — full-suite comparison phát hiện control
  Owner dùng `st.form` làm đổi reason của một failure cũ (nested form trong
  AppTest). Đã sửa bằng widget thường và chạy lại full suite; failure shape
  cũ được khôi phục. Bài học: không thêm form mới vào entrypoint đã có
  login/bootstrap form.

## 2. Phạm vi đã làm

- Một entrypoint duy nhất: `web_app.py` / `views/web_app.py`. Admin và Support
  Sale vẫn đăng nhập nội bộ rồi vào React `logi_shell` như cũ; ma trận
  `core/auth.py::ROLE_PERMISSIONS` không đổi.
- Khách hàng chọn nút Google OIDC riêng trên màn login; `st.login("google")`
  chỉ chạy sau cú click đó và chỉ khi config hợp lệ. Streamlit xử lý
  `/oauth2callback` rồi quay lại chính app URL. Chưa có browser OAuth thật.
- Một cơ chế principal đáng tin: claim OIDC đã kiểm tra → email chuẩn hoá →
  đối chiếu server-side với `customers.portal_access_email` → `customers.id`.
  Browser không gửi `customer_id`, mã lô hay version. Test staging gọi cùng
  `build_customer_principal()` với email test và handle DB in-memory; không có
  UI giả lập danh tính trong production.
- `customers.email` vẫn là email liên hệ. Mặc định không có email portal;
  Owner/Admin cấp/thu hồi tối đa một email trên chính profile `customers`.
  Support không thấy control. Không có bảng mapping mới.
- Publication: chỉ `state=PUBLISHED`, đúng `customers.id`, đúng shipment, đúng
  version đã pin, có `approved_by`/`approved_at`, đúng HEXA allowlist. Màn
  khách chỉ nhận `PublicationCard` gồm mã lô, trạng thái “ĐÃ XÁC NHẬN”,
  version, phương thức, thời điểm duyệt. Không gửi cost/profit/tài liệu riêng/
  view-model nội bộ xuống frontend để ẩn.
- `shipments.customer_id` thiếu/rỗng/không tồn tại trong `customers.id` bị loại,
  log `CUSTOMER_PORTAL_INTERNAL_REVIEW`, UI chỉ báo lỗi dữ liệu chung; không
  bao giờ khớp theo tên công ty.
- Trạng thái UI: có lô, chưa có lô, từ chối/không có bản duyệt, lỗi dữ liệu,
  email không được phép, lỗi/hết hạn OIDC, đăng xuất. Làm mới trang dựng lại
  principal từ OIDC + MongoDB nên thu hồi quyền có hiệu lực.
- Business logic publication được mang từ commit nguồn
  `4c4600aa52f7b24f8d1eabf9c7df4d248e9fcb52` chỉ ở mức module pure
  `core/hexa_customer_publication.py` và test bounded tương ứng. Không mang
  trial HTTP server, tài khoản hard-code hay credential.

## 3. Files thay đổi

Modified:

- `.env.example`
- `.gitignore`
- `.streamlit/secrets.toml.example`
- `README.md`
- `requirements.txt`
- `views/customers.py`
- `views/web_app.py`

Added:

- `core/hexa_customer_publication.py`
- `core/customer_portal.py`
- `core/customer_portal_oidc.py`
- `views/customer_dashboard.py`
- `scripts/seed_customer_portal_staging.py`
- `tests/test_customer_portal_hexa_publication_v0.py`
- `tests/test_customer_portal_core_g1.py`
- `tests/test_customer_portal_oidc_g1.py`
- `tests/test_customer_dashboard_g1_runtime.py`
- `docs/CUSTOMER_DASHBOARD_G1_HANDOFF.md` (file này)

`requirements.txt` thêm `Authlib>=1.3.2`. `.streamlit/secrets.toml.example`
chỉ có placeholder `YOUR_VALUE_HERE`; không commit Client ID/Client Secret/
cookie secret thật. `.env.example` ghi rõ OIDC config nằm ở secrets.toml local.
`.gitignore` bỏ qua `.arena_g1_evidence/` (log suite nặng, giữ ở workspace để
đối chiếu, không đưa vào Git). Không sửa `component/dist`, không React build,
không ghi MongoDB production, không bật Drive sharing, không đổi financial RBAC,
không tạo role Accounting/Finance.

## 4. Tests thực sự chạy

Môi trường: `.venv`, Streamlit `1.66.1`, Authlib `1.9.1`, pytest `9.1.1`,
mongomock `4.3.0`, pymongo `4.19.0`.

1. Baseline trước sửa, tại HEAD `009c87a…`:
   `.venv/bin/python -m pytest tests -q --continue-on-collection-errors`
   → `35 failed, 1931 passed, 45 skipped, 10 subtests passed in 119.44s`,
   exit `1`. Log: `.arena_g1_evidence/baseline_full_suite.txt`.

2. New-test lane lần đầu:
   `.venv/bin/python -m pytest tests/test_customer_portal_hexa_publication_v0.py tests/test_customer_portal_core_g1.py tests/test_customer_portal_oidc_g1.py tests/test_customer_dashboard_g1_runtime.py -q`
   → `3 failed, 63 passed`. Lỗi thuộc helper đọc label nút trong AppTest; đã sửa
   helper, không đổi behaviour app.

3. New-test lane sau sửa helper + thêm check Authlib/issuer + thêm runtime test
   Owner control:
   cùng lệnh trên → `70 passed in 3.30s`, exit `0`. Log:
   `.arena_g1_evidence/new_tests_final_run.txt` (68 pass ở thời điểm trước khi
   thêm 2 test Owner control; lần chạy trực tiếp cuối cùng là 70 pass).

4. `python -m compileall` cho toàn bộ module/script/test mới: exit `0`.
   `git diff --check`: exit `0`.

5. Full suite sau thay đổi lần 1:
   `35 failed, 1999 passed, 45 skipped, 10 subtests passed in 115.89s`.
   Ở lần này failure IDs vẫn là 35 nhưng reason của
   `test_phase_a_component.py::test_view_model_shape_via_app` đổi từ assertion
   line 61 sang nested-form exception line 60. Đây là regression theo luật
   baseline, nên **không được chấp nhận**.

6. Điều tra + sửa: bisect prefix test files xác định control Owner dùng
   `st.form` tương tác với lifecycle AppTest của các test latency cũ. Đã thay
   form bằng `selectbox`/`text_input`/2 `button` thường; AppTest prefix xác
   nhận không còn `Forms cannot be nested in other forms`.

7. Full suite cuối cùng sau sửa:
   `.venv/bin/python -m pytest tests -q --continue-on-collection-errors`
   → `35 failed, 2001 passed, 45 skipped, 10 subtests passed in 125.66s`,
   exit `1` (known red baseline). Log:
   `.arena_g1_evidence/after_full_suite_v2.txt`.
   So sánh 35 failure IDs với baseline: **identical**. Chi tiết
   `test_phase_a_component.py` vẫn là `tests/test_phase_a_component.py:61:
   AssertionError`; không còn nested-form log. Pass tăng đúng `+70` so với
   baseline (`1931 → 2001`).

### Runtime UI evidence

- Các test `tests/test_customer_dashboard_g1_runtime.py` chạy thật entrypoint
  `app.py` bằng `streamlit.testing.v1.AppTest` (không phải đọc source), kiểm
  tra element tree: internal shell Admin/Support, customer login button,
  config lỗi fail-closed, OAuth-return giả lập, 2 thẻ lô Lục Giác, chi tiết
  allowlist, query params độc, chưa có lô, refresh, logout, OIDC bad states.
- Không có screenshot trình duyệt: Chromium của Playwright không có sẵn trong
  sandbox và host tải browser không nằm trong outbound allowlist. Vì vậy không
  tuyên bố visual browser PASS. `OIDC_LIVE` cũng chưa có bằng chứng redirect
  thật; phần return-to-app mới được xác minh từ source Streamlit `1.66.1` và
  test synthetic claim.

## 5. Trạng thái riêng biệt

- `CUSTOMER_AUTH_STAGING=PASS` — synthetic verified Google claims + staging
  MongoDB; không phải OAuth thật.
- `TENANT_ISOLATION=PASS` — Lục Giác chỉ thấy 2 lô public; khách B, lô draft,
  lot thiếu `customer_id` và internal sentinel không lọt qua server/view.
- `INTERNAL_REGRESSION=PASS_NO_NEW_FAILURES` — full suite cuối giữ nguyên 35
  failure IDs; Admin/Support AppTest vẫn build view-model và mount shell.
- `OIDC_LIVE=NOT_TESTED` — thiếu config Google thật và browser callback thật;
  không được gộp vào staging PASS.
- `PRODUCTION_DEPLOY=NOT_DONE_BY_BOUNDARY` — không deploy Streamlit Cloud,
  không ghi production DB, không merge main.
- `G1_STAGING_SLICE=PASS`; `DONE_G1=INCOMPLETE_LIVE_OIDC_PENDING`.

## 6. Blocker & next step

Blocker duy nhất để chuyển từ staging sang khẳng định production-ready là chưa
có một lượt Google OAuth thật trên môi trường staging có `[auth]` +
`[auth.google]` thật, `redirect_uri` đúng `/oauth2callback`, và trình duyệt để
xác minh: đăng nhập → quay lại app → refresh → logout. Không commit credential
thật; config chỉ nằm trong `.streamlit/secrets.toml` gitignored.

Next step (ngoài phạm vi G1 hiện tại, chỉ khi Owner cho phép): chạy lượt OIDC
live staging đó, chụp màn hình thật, rồi mới quyết định bật production. Không
làm phase 2, không tải tài liệu, không mở rộng role.
