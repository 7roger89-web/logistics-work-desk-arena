VỊ TRÍ: main
BASE_SHA: ee31b0f3344cd9b23c39c01a8d14b7581ffa0d23

> BASE_SHA đầu file là commit main ngay sau khi merge PR #220, trước commit cập nhật tài liệu này; không phải SHA tự tham chiếu của commit chứa file. Số liệu suite bên dưới vẫn thuộc baseline lịch sử a98884b, chưa chạy lại.

## FALLBACK ĐỌC FILE

Thử lần lượt khi URL raw trên main trả 404 (không kết luận file mất chỉ từ một URL):

1. Raw main: https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/main/docs/NEXT.md
2. GitHub main: https://github.com/7roger89-web/logistics-work-desk-arena/blob/main/docs/NEXT.md
3. Contents API main: `gh api 'repos/7roger89-web/logistics-work-desk-arena/contents/docs/NEXT.md?ref=main' --jq .content | base64 -d`
4. Git main: `git fetch origin main && git show origin/main:docs/NEXT.md`
5. Nếu main thực sự chưa có file, đọc PR #220: `gh pr view 220 --json state,headRefName,mergeCommit`; dùng headRefName trả về để đọc Contents API với `ref=<headRefName>`. Bản nhánh phải ghi `VỊ TRÍ: nhánh <tên> — CHƯA MERGE`, không coi là bản main.
6. Nếu nhánh PR đã bị xoá, lấy mergeCommit.oid từ bước 5 và đọc Contents API với `ref=<mergeCommit.oid>` hoặc `git show <mergeCommit.oid>:docs/NEXT.md`. Phân biệt lỗi mạng/quyền truy cập với HTTP 404; ghi lại cách đọc thực sự thành công.

---

# NEXT — Trạng thái bàn giao và việc tiếp theo

Session: `LOG-NEXT-W1-BOOTSTRAP-HANDOFF`
Nhánh làm việc: `arena/19722cb4-logistics-work-desk-arena`

Tài liệu này được tạo từ việc **đo lại** trạng thái repo, không sao chép từ các tài liệu bàn giao cũ. Mọi sha và số liệu bên dưới là kết quả đo tại thời điểm viết.

## 1. TRẠNG THÁI

| Mục | Giá trị đo được |
|---|---|
| BASE_SHA (`main`, nguồn: GitHub API `commits/main`) | `a98884b1905c2470fae750d93526fe69930b1958` |
| Ngày commit BASE_SHA | 2026-10-26T07:13:41Z |
| Thông điệp commit | `Merge pull request #219 from 7roger89-web/arena/9ef9189e-logistics-work-desk-arena` |
| PR merge cuối cùng | #219 — "Fix 12 known red tests (A1/A2/B1/B2/B3) + README tidy (D); C reported" |
| `mergeCommit.oid` của PR #219 | `a98884b1905c2470fae750d93526fe69930b1958` (khớp BASE_SHA) |
| `mergedAt` PR #219 | 2026-10-26T07:13:42Z |
| PR merge gần kế trước | #218 (merge commit `342b4ffe088996be36caba0b5f79a4a4955f4ba9`) |
| Nhánh làm việc khi bắt đầu | tạo từ BASE_SHA, không có thay đổi chưa commit |

Kết luận: PR #219 là PR merge cuối cùng và chính là commit đứng đầu `main`.

## 2. ĐO LẠI

### 2.1 Kiểm tra tồn tại `docs/NEXT.md`

Kết quả: **KHÔNG TỒN TẠI** trên `main` (BASE_SHA) và trên nhánh làm việc.

| Cách kiểm tra | Kết quả |
|---|---|
| `contents/docs?ref=main` (GitHub API) | Không có file nào có tên chứa `NEXT` |
| `contents/docs/NEXT.md?ref=main` (GitHub API) | HTTP 404 |
| `contents/?ref=main` (thư mục gốc) | Không có file nào có tên chứa `NEXT` |
| `git ls-tree -r a98884b` | Không có `docs/NEXT.md` (chỉ có `.agents/.../nextjs-app-router.md` và `core/next_action_card.py`, không liên quan) |
| Thư mục local `docs/` | Không có `NEXT.md` |
| `raw.githubusercontent.com/.../docs/NEXT.md` | Không kiểm tra được: sandbox không truy cập được host này (lỗi SSL/chặn mạng). Không dùng kết quả này làm bằng chứng. |

### 2.2 Baseline test suite tại BASE_SHA

Lệnh chạy (venv riêng, cài `requirements.txt` + `pytest 9.1.1`, Python 3.11.2, trên commit `a98884b`):

```
python -m pytest tests -q --continue-on-collection-errors
```

| Chỉ số | Số đo |
|---|---|
| passed | **1948** |
| failed | **18** |
| skipped | **45** |
| error (collection) | **0** |
| subtests passed | 10 |
| Thời gian | 115.46 s |

Danh sách test FAILED (18, không có ERROR):

1. `tests/test_agreements_api.py::LoadAgreementsTests::test_load_agreements_returns_dict_from_load_dict`
2. `tests/test_all_tabs_smoke.py::AllTabsSmokeTest::test_all_routes_render`
3. `tests/test_inbox_snippets.py::test_dom_acceptance_inbox_desktop_and_mobile`
4. `tests/test_intl_payment_comparator.py::ProvenanceImmutabilityTest::test_snapshot_immutability_via_mongomock_if_available`
5. `tests/test_lg08_1_safety.py::test_identity_gate_enforcement`
6. `tests/test_lg08_1_safety.py::test_production_identity_pass`
7. `tests/test_logc15_auth_rbac.py::TestRoleMatrix::test_unknown_role_falls_back_to_viewer`
8. `tests/test_logi_cn_truck_type_persist_01.py::test_whitelist_gained_exactly_the_one_approved_key`
9. `tests/test_logi_finance_actual_entry_parity_01.py::test_service_catalog_is_projected_from_core_config`
10. `tests/test_logi_finance_actual_entry_parity_01.py::test_service_catalog_is_not_hardcoded_in_react`
11. `tests/test_logi_interaction_latency_repair_01.py::InteractionLatencyRepairTests::test_adversarial_reverting_to_baseline_produces_double_build_and_rerun`
12. `tests/test_logi_interaction_latency_repair_01.py::InteractionLatencyRepairTests::test_duplicate_trigger_in_same_prefix_batch_does_not_double_dispatch`
13. `tests/test_logi_shipment_operational_data_v1.py::test_lightweight_create_starts_one_canonical_leg_and_navigable_detail_data`
14. `tests/test_login_visual_compact.py::test_bootstrap_path_still_reachable_with_hero`
15. `tests/test_phase_a_component.py::test_view_model_shape_via_app`
16. `tests/test_phase_b_real_data.py::test_pxk_operator_identity_generates_persisted_office_file`
17. `tests/test_session_truth_repair.py::test_bootstrap_first_admin_flow_still_runs_with_no_session_and_no_users`
18. `tests/test_shipment_slash_route_repair_01.py::TestBackendRouteProducers::test_primary_action_composes_encoded_segment_then_query_then_anchor`

Lưu ý: tiêu đề PR #219 ghi "Fix 12 known red tests", nhưng lần đo này vẫn còn 18 test đỏ trên đúng commit đó. Chưa xác định nguyên nhân (có thể do môi trường cài đặt khác, ví dụ phiên bản streamlit/pymongo/mongomock, hoặc do PR chưa sửa hết). Chưa điều tra sâu vì phạm vi phiên này không cho sửa code/test.

### 2.3 Số chuẩn

Số chuẩn cho các lần bàn giao sau là số đo ở mục 2.2 tại BASE_SHA: **1948 passed / 18 failed / 45 skipped / 0 error**. Không dùng số hard-code từ tài liệu cũ.

## 3. VIỆC TIẾP THEO

1. Điều tra 18 test FAILED ở mục 2.2 và phân loại: lỗi môi trường (phiên bản thư viện) hay lỗi thật trong code/test. Đây là việc thuộc phiên khác, không làm trong phiên này.
2. Đối chiếu với PR #219 để làm rõ vì sao tiêu đề ghi "Fix 12 known red tests" nhưng vẫn còn 18 test đỏ.
3. Khi có thay đổi code/test ở phiên sau, chạy lại đúng lệnh ở mục 2.2 và cập nhật bảng số ở mục 2.2 và mục 2.3, đồng thời thêm entry vào mục 4.
4. Nếu cần chạy lại trên môi trường sạch, cài đúng `requirements.txt` trong venv (PEP 668 chặn cài pip toàn cục trên sandbox).

Ràng buộc phiên này: không merge `main`, không deploy, không sửa app code, không sửa test.

## 4. LỊCH SỬ

Mỗi phiên append một entry mới ở cuối mục này. Không có entry = phiên coi như chưa xảy ra.

### Entry template

```
- [YYYY-MM-DD] SESSION <session-id> — <tên phiên>
  - BASE_SHA: <sha>
  - Làm: <việc đã làm>
  - Đo được: passed=<n> failed=<n> skipped=<n> error=<n>
  - Bị bác bỏ: <giả định/khẳng định đã kiểm tra và bác bỏ, hoặc "không có">
  - Còn lại: <việc chưa làm>
  - Head sha: <sha>
```

### Entries

- [2026-10-26] SESSION LOG-NEXT-W1-BOOTSTRAP-HANDOFF — Bootstrap và đo lại trạng thái
  - BASE_SHA: a98884b1905c2470fae750d93526fe69930b1958 (PR #219 merge, 2026-10-26T07:13:41Z)
  - Làm: đo BASE_SHA từ GitHub API; kiểm tra tồn tại `docs/NEXT.md` (contents API + thư mục gốc + local + git ls-tree); xác nhận PR #219 là PR merge cuối; chạy full suite trên BASE_SHA; tạo `docs/NEXT.md` này.
  - Đo được: passed=1948 failed=18 skipped=45 error=0 (xem danh sách 18 test ở mục 2.2)
  - Bị bác bỏ:
    - "docs/NEXT.md tồn tại" — BÁC BỎ: contents API trả 404, không có trong `git ls-tree` của BASE_SHA. Chưa thể kiểm tra qua raw.githubusercontent.com vì sandbox không truy cập được host này.
    - "PR #219 đã sửa 12 test đỏ nên suite xanh" — BÁC BỎ một phần: đo lại thấy 18 test FAILED trên đúng commit đó.
    - "Tài liệu bàn giao có sẵn số suite" — không dùng: mọi số liệu lấy từ lần đo này, không hard-code từ tài liệu cũ.
  - Còn lại: điều tra 18 test FAILED; xác minh raw URL khi có mạng.
  - Head sha: xem commit tương ứng trên nhánh `arena/19722cb4-logistics-work-desk-arena` (sha ghi trong PR).

- [2026-10-26] SESSION LOG-NEXT-MAIN-RECOVERY — Đưa bàn giao lên main
  - BASE_SHA: ee31b0f3344cd9b23c39c01a8d14b7581ffa0d23 (main ngay sau merge PR #220).
  - Làm: xác nhận đủ TRẠNG THÁI / ĐO LẠI / VIỆC TIẾP THEO / LỊCH SỬ và template; undraft và merge PR #220; thêm VỊ TRÍ, BASE_SHA đầu file và chuỗi fallback; giữ nguyên mọi entry cũ.
  - Đo được: không chạy lại suite (chỉ sửa docs); số liệu cũ không phải kết quả đo phiên này.
  - Bị bác bỏ: không có; thông tin 404 và ràng buộc không merge trong entry bootstrap là lịch sử, không mô tả phiên này.
  - Còn lại: điều tra 18 test FAILED theo baseline lịch sử; xác minh HTTP raw sau merge bản cập nhật.
  - Head sha: xem commit cập nhật docs/NEXT.md và merge commit của PR kế tiếp #220 trên main.
