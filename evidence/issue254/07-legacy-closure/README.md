# LOGI-255-LEGACY-FAILCLOSED — đóng đường fail-open của `lastWrites`

- Task: `LOGI-255-LEGACY-FAILCLOSED-20261101`
- Base/expected HEAD: `911f3174596245fc8ec4d68daef634fa07032f90` (PR #255 head, branch `arena/0d73ca3b-logistics-work-desk-arena`)
- Branch làm việc: `arena/31b6af11-logistics-work-desk-arena`
- SPEC_REF: Issue #254 (comment SPEC_LOCK bổ sung: `00-spec-lock-legacy.md`)
- Phạm vi sửa: `views/logi_view_model.py`, 2 file test liên quan trực tiếp, thư mục evidence này.
- Không sửa: RBAC matrix, `finance_view` gate, session key, workbook, UI filter, Cloud, `main`.

## 1. Root cause (đo trên code, không suy đoán)

`views/logi_view_model.py::_last_writes_for_actor()` có hai lớp:

1. lớp `finance_view` (cũ) — actor không có quyền không nhận `FINANCE_WRITE_EVENTS`;
2. lớp provenance (mới, commit `911f317`) — row mang `_provenance` chỉ được giao cho đúng actor/role.

Lớp 2 **fail-open** với row không có provenance:

```python
written = row.pop(LAST_WRITES_PROVENANCE, None)
if not isinstance(written, Mapping):
    delivered.append(row)   # ← row legacy / fixture ghi tay vẫn được giao
    continue
```

Hệ quả: row legacy còn trong `LAST_WRITES_KEY` (session đang mở khi nâng cấp code, hoặc
script/fixture ghi thẳng) được giao cho **bất kỳ** actor nào dùng cùng session, và với cả
event **không** nằm trong `FINANCE_WRITE_EVENTS` (`cost_rate_save` mang readback giá vốn).
Nghĩa là kết quả ghi tiền/giá vốn không chứng minh được danh tính và quyền của người tạo.

## 2. FAIL-before (đo TRƯỚC khi sửa, cùng máy, cùng venv)

`02-fail-before.txt` — `python -m pytest tests/test_logi255_lastwrites_legacy_failclosed.py -q`
→ **4 failed, 6 passed in 1.97s, EXIT_CODE=1**

| Test (mới) | Trước sửa |
|---|---|
| `test_legacy_rows_without_provenance_not_delivered_to_support_b` | FAIL — Support B nhận `PAY-255-LEGACY-A` + `COST-255-LEGACY-A` |
| `test_legacy_rows_without_provenance_not_delivered_to_sale` | FAIL — Sale nhận `COST-255-LEGACY-A` (readback giá vốn 4.250 USD) |
| `test_invalid_provenance_never_delivers_legacy_row[qa.s255.support.a]` | FAIL — provenance kiểu `str` (không phải mapping) vẫn được giao |
| `test_empty_role_is_not_identity_proof` | FAIL — role rỗng ở cả hai bên bị coi là "khớp quyền" |

Payload thật trước sửa (`03-payload-fail-open-before.json`, cùng discriminator: Support A ghi
`payment_record` 35.000.000 VND + `cost_rate_save`, bỏ `_provenance`, đổi actor):

- `SUPPORT_B`: `[{"event":"payment_record","requestId":"PAY-255-LEGACY-A","persisted.amount":35000000.0, "readback.finance.received":35000000.0, ...}, {"event":"cost_rate_save","readback.costAmount":4250.0}]`
- `SALE`: `[{"event":"cost_rate_save","requestId":"COST-255-LEGACY-A","readback.costAmount":4250.0}]`
- `SUPPORT_A` (không đổi danh tính/quyền): cả hai outcome, đầy đủ readback.

## 3. Sửa nhỏ nhất tại boundary đang có

`views/logi_view_model.py` (32 dòng đổi, không thêm module/key/RBAC):

- `_last_writes_for_actor`: row thiếu provenance → `continue` (không giao) thay vì `delivered.append`.
- `_provenance_matches`: fail-closed — `actor`/`role` rỗng ở **một trong hai** phía là không khớp;
  `actor`, `userId`, `role` vẫn phải bằng nhau sau chuẩn hoá.
- Giữ nguyên lớp `finance_view` và `_stamp_last_writes()`; không thêm session key.

## 4. PASS-after

`04-payload-fail-closed-after.json` (cùng discriminator, sau sửa):

- legacy rows (đã bỏ `_provenance`): `SUPPORT_B=[]`, `SALE=[]`, `SUPPORT_A=[]`
  → row không chứng minh được người tạo **không** được giao cho bất kỳ actor nào.
- provenance hợp lệ (không bỏ stamp): `SUPPORT_A` nhận `PAY-255-LEGACY-A`
  (`persisted.amount=35.000.000`, `readback.finance.received=35.000.000`) và
  `COST-255-LEGACY-A` (`readback.rows[0].amount=4250.0`); `SUPPORT_B=[]`, `SALE=[]`.

### Test đã chạy (raw log + exit code)

| Lệnh | File log | Kết quả | Exit |
|---|---|---|---|
| `pytest tests/test_logi255_lastwrites_finance_boundary.py -q` | `05-pass-after-finance-boundary.txt` | 4 passed | 0 |
| `pytest tests/test_logi255_lastwrites_actor_isolation.py -q` | `05-pass-after-actor-isolation.txt` | 5 passed | 0 |
| `pytest` (3 file LOGI-255) `-q` | `05c-pass-after-new-and-existing-tests.txt` | 19 passed | 0 |
| `pytest tests -q -rs` (lượt 1) | `07-full-pytest-after-rs.txt` | **2385 passed, 44 skipped, 10 subtests passed, 0 failed** | 0 |
| `pytest tests -q -rs` (lượt 2) | `08-full-pytest-after-run2.txt` | **2385 passed, 44 skipped, 10 subtests passed, 0 failed** | 0 |

Gate yêu cầu: `0 FAILED / 0 ERROR`, SKIPPED không tăng từ 44 → **đạt (44)**.
`0 FAILED` được đo trên môi trường có `component/node_modules` (`npm ci`, gồm `jsdom`);
trước khi cài, 7 test DOM/bundle fail vì thiếu `jsdom` trên máy này — log giữ nguyên tại
`06a-env-missing-jsdom-full-pytest.txt` (lỗi môi trường, không phải hành vi sản phẩm).

### Baseline so sánh (worktree sạch tại `911f317`)

| Lượt | File | Kết quả | Exit |
|---|---|---|---|
| 1 | `09a-baseline-911f317-full-run1-flaky.txt` | 1 failed, 2374 passed, 44 skipped | 1 |
| 2 | `09b-baseline-911f317-full-run2-clean.txt` | **2375 passed, 44 skipped, 0 failed** | 0 |

Lượt 1 fail `test_gnt_revision_comes_from_durable_docgen_metadata_after_session_clear`
(`second["persisted"]["attachmentDuplicate"]`), chạy riêng tại baseline vẫn **PASS** và
lượt 2 baseline sạch → **flaky/order-dependent có sẵn**, không liên quan `lastWrites`.
Chênh lệch pass: `2375 → 2385` = **+10 test mới**, tập SKIPPED giống hệt (44).

## 5. Test cũ được chuyển sang boundary thật (không xoá/skip/xfail/nới assert)

`tests/test_logi255_lastwrites_finance_boundary.py` có 2 test positive ghi thẳng
`st.session_state[LAST_WRITES_KEY] = [pay_out]` với outcome **không** có provenance
(`_dispatch` gọi `consume_phase_b_triggers`, không đi qua `dispatch()`):

- `test_support_finance_write_kept_in_lastwrites`
- `test_lastwrites_finance_not_leaked_to_sale_same_session`

Cả hai nay gửi qua `vm.dispatch(..., allow_rerun=False)` (helper
`_write_payment_via_dispatch`), tức chính boundary gắn provenance. Toàn bộ assert cũ giữ
nguyên (số tiền, `requestId`, readback, `canViewFinance`, không lộ `amount/derivedPaid/
derivedDebt`). 4/4 test của file PASS.

## 6. Giới hạn / UNKNOWN

- `SUPPORT_A` trong ca "legacy đã bị bỏ stamp" nhận `[]` — đúng MUST NOT "giao kết quả thiếu
  provenance cho bất kỳ actor nào"; readback đầy đủ của A chỉ còn khi row giữ provenance hợp lệ.
- Không chứng minh được gì về Cloud/OIDC/Atlas (ngoài scope). Không merge/deploy.
- Cửa sổ thực tế của lỗi: row còn trong `LAST_WRITES_KEY` của một session đang mở, hoặc
  fixture/script ghi thẳng session. Sau sửa, mọi nguồn ghi hợp lệ vẫn duy nhất là `dispatch()`.
