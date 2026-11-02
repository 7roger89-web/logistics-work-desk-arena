# LOGI-255-LASTWRITES-ISOLATION — 05 CLOSURE

- Task: `LOGI-255-LASTWRITES-ISOLATION` · Role: IMPLEMENTER · PR #255 · Spec ref: Issue #254
- Target repo: `7roger89-web/logistics-work-desk-arena` (KHÔNG phải `logistics-work-desk`)
- `EXPECTED_PR_HEAD` đo trước khi sửa: **`05b65537bb524b6c0c550f538cce1032f934a6e7`** — khớp `gh pr view 255` (`headRefOid`), branch làm việc `arena/c8ce75e6-logistics-work-desk-arena` cùng commit ⇒ không lệch, không rebase.
- `P2P_LAW_SOURCE=LOCAL_PORTABLE` (`.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md`, `P2P_PORTABLE_LAW_PROJECTION=YES`, canonical provenance + SHA256 có mặt). Không thử cross-repo probe để "tạo 404".
- `docs/NEXT.md` đọc tại target ref `05b6553`.

## 1. Root cause

`views/logi_view_model.py::dispatch()` lưu outcome vào `st.session_state["logi_last_writes"]`. Trước thay đổi này, `_last_writes_for_actor()` chỉ lọc theo:

1. quyền `finance_view` của actor **hiện tại**, và
2. danh sách 5 tên sự kiện `FINANCE_WRITE_EVENTS`.

Hai lỗ hổng đo được trên exact source (xem `01-fail-before.txt`):

- **A** — outcome không mang thông tin *ai đã ghi*. Cùng session, Support A ghi `payment_record` 35.000.000 VND; Support B (cùng quyền) đăng nhập và nhận **nguyên outcome của A**: `requestId`, `persisted.amount`, `readback.finance`.
- **C** — lớp lọc dựa trên **tên sự kiện** nên các sự kiện anh em mang tiền đi qua tự do: `cost_rate_save` trả `readback` là snapshot giá vốn (USD) và vẫn được tra cho actor đã bị hạ xuống Sale (không còn `finance_view`).

## 2. Diff (giải pháp nhỏ nhất tại boundary sẵn có)

`views/logi_view_model.py` (+70/−7):

- `LAST_WRITES_PROVENANCE = "_provenance"` + `_actor_provenance()` (username, user_id, role — đã chuẩn hoá).
- `_stamp_last_writes(outcomes)` — gọi đúng **một chỗ** trong `dispatch()` thay cho `st.session_state[LAST_WRITES_KEY] = outcomes`.
- `_provenance_matches()` + `_last_writes_for_actor()` — trả outcome **chỉ khi** provenance khớp actor/role hiện tại; field nội bộ bị bóc trước khi vào payload; **giữ nguyên** bộ lọc `finance_view`/`FINANCE_WRITE_EVENTS` đang có cho row không mang provenance.

Không thêm session key mới, không bảng quyền mới, không framework, không đụng `FINANCE_WRITE_EVENTS` (nên không phải bảo trì danh sách tên sự kiện khi có sự kiện anh em mới), không đổi hình dạng outcome mà component đang đọc.

`core/auth.py::logout()` (đã có ở `05b6553`) vẫn xoá `current_user` + `LAST_WRITES_KEY` — váy hai lớp: xoá lúc logout, và kiểm provenance lúc dựng payload.

## 3. WRONG_PASS (đã chặn)

1. Support B cùng quyền đọc được tiền Support A vừa ghi (requestId/amount/readback) → phải FAIL.
2. Cùng account hạ xuống Sale vẫn nhận `cost_rate_save.readback` giá vốn → phải FAIL.
3. Row mang `_provenance` lọt ra payload component → phải FAIL.
4. Ngược lại, Support hợp lệ không đổi actor/role phải **vẫn** nhận đúng outcome + requestId + readback (`D`).

## 4. FAIL-before / PASS-after

| Lát | Test | Trước fix | Sau fix |
|---|---|---|---|
| A | `test_support_b_same_session_never_receives_support_a_outcome` | **FAIL** (`payment_record PAY-255-A-1` tới B) | PASS |
| B | `test_downgraded_sale_same_account_does_not_receive_finance_outcome` | PASS (bộ lọc `finance_view` cũ) | PASS |
| C | `test_cost_rate_readback_not_delivered_to_sale_same_session` | **FAIL** (`cost_rate_save COST-255-C-1` + giá vốn tới Sale) | PASS |
| D | `test_unchanged_actor_keeps_outcome_requestid_and_readback` | PASS (không bị chặn oan) | PASS |
| E | `test_new_actor_gets_only_its_own_outcome_after_own_write` | **FAIL** (B kế thừa outcome của A) | PASS |

`01-fail-before.txt` = 3 failed / 2 passed, `EXIT=1` trên source `05b6553` (stash fix, cùng file test cuối cùng).
`02-pass-after-focused.txt` = 511 passed / 6 skipped, `EXIT=0` (5 test mới + 21 file RBAC/lastWrites/finance liên quan).

## 5. Full pytest (baseline vs after, cùng máy)

| Lượt | Kết quả | FAILED | SKIPPED |
|---|---|---|---|
| Baseline `05b6553` (stash fix + tạm bỏ file test mới) | 2370 passed | 0 | 44 |
| Sau fix (+5 test mới) | **2375 passed** | **0** | **44** |

- Tập SKIPPED: `diff` giữa 18 dòng `-rs` của hai lượt = **rỗng**; 44 node id ở `03-skipped-ids.txt`.
- Chạy full suite lần 2 (verbose, không thao tác git song song): 2375 passed / 44 skipped / `EXIT=0`.
- Ghi chú trung thực: một lượt verbose trước đó có 1 FAILED `tests/test_logi_shipment_core_gaps_01.py::test_new_event_reuses_the_existing_writer_and_whitelist_only` — nguyên nhân là **tôi** chạy `git stash`/`git checkout` song song trong lúc suite đang đọc source bằng `inspect.getsource` (file trên đĩa bị đổi giữa lượt). Chạy lại sạch: 0 FAILED. Không gọi đây là lỗi môi trường khi chưa đối chứng — đã đối chứng bằng lượt chạy sạch và bằng baseline 0 FAILED.

## 6. Component / DOM

- `npm ci` trong `component/` → 87 packages.
- `npm run typecheck` → `EXIT=0`. `npm run build` → `EXIT=0` (dist 1.593 kB).
- DOM lane thật trong repo (`tests/test_issue254_shipment_debt_glance.py::test_shipments_list_dom_bundle_acceptance`, jsdom + bundle vừa build): **PASSED**.
- Ba lane headless khác (`dom_acceptance_c2a`, `dom_acceptance_c2c`, `dom_acceptance_real_use_repair`) fail **giống hệt nhau** trước và sau fix (cùng assert, cùng fixture committed) ⇒ 0 regression, đã lỗi từ trước khi chạy trực tiếp bằng `node` ngoài pytest harness. Chi tiết `04-dom-and-build.txt`.

## 7. Phép thử MUST NOT

Support A tạo `payment_record` (35.000.000 VND) và `cost_rate_save` (4.250 USD/40HC) trong cùng session; đổi sang Support B **hoặc** hạ account xuống Sale:

- `model["lastWrites"] == []` — payload của actor sau **không** chứa `requestId`, `persisted.amount`, `readback`, giá vốn của A.
- Row gốc trong session vẫn còn (không xoá dữ liệu của người khác), chỉ không được tra cho actor sai.

## 8. Quan sát NGOÀI scope (không sửa trong task này)

`build_view_model()["costIntelligence"]["rates"]` vẫn trả snapshot giá vốn (kể cả `request_id` + `amount` USD) cho role **không** có `finance_view` (Sale), vì đây là projection read-only khác `lastWrites` và hiện không có gate quyền. Đã đối chứng bằng script: `sale_model["lastWrites"] == []` nhưng `costIntelligence.rates[0].id == "COST-255-C-1"`. Đây là quyết định quyền của Owner/Control Tower (NON-GOALS của task: không mở rộng scope, không sửa filter UI/không đổi bảng quyền) — ghi nhận, không tự sửa.

## 9. Tái lập

```bash
cd /home/user/logistics-work-desk-arena
python -m pytest tests/test_logi255_lastwrites_actor_isolation.py -q -p no:cacheprovider   # 5 passed
python -m pytest tests -q -rs -p no:cacheprovider                                          # 2375 passed, 44 skipped
cd component && npm ci && npm run typecheck && npm run build
cd .. && python -m pytest tests/test_issue254_shipment_debt_glance.py -q -p no:cacheprovider
```
