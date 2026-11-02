## SPEC_LOCK bổ sung (pre-code) — LOGI-255-LEGACY-FAILCLOSED-20261101

- Date locked (pre-code, trước khi sửa `views/logi_view_model.py`): `2026-11-01` (UTC)
- Scope: `views/logi_view_model.py::_last_writes_for_actor` (đường fail-open cho row thiếu provenance)
- Không mở Issue mới. Không mở PR mới. Không sửa RBAC/session key.

### 1. Hành vi quan sát được (actor → entrypoint → action → dữ liệu/quyền → kết quả)
- Entrypoint: payload `lastWrites` do `build_view_model()` dựng cho component shell (`/lo-hang` và các màn ghi nghiệp vụ).
- Support A (có `finance_view`) ghi `payment_record` 35.000.000 VND và `cost_rate_save` (readback giá vốn USD) qua `dispatch()`.
- `dispatch()` gắn `_provenance` = {actor, userId, role} vào từng outcome trước khi lưu `LAST_WRITES_KEY`.
- `_last_writes_for_actor()` phải chỉ trả outcome cho ĐÚNG actor/userId/role đang có hiệu lực.

### 2. WRONG_PASS (đã tồn tại TRƯỚC khi sửa — đóng ở slice này)
Row trong `LAST_WRITES_KEY` **không có** `_provenance` (row legacy còn trong session khi nâng cấp code, hoặc fixture/script ghi thẳng) hiện được `delivered.append(row)` **bất kể** actor/role đang dùng session.

Phép thử phân biệt:
1. Support A ghi 35.000.000 VND (`payment_record`) + `cost_rate_save` qua `dispatch()`.
2. Bỏ `_provenance` khỏi các row đã lưu (mô phỏng row legacy) — không đổi gì khác.
3. Cùng session, đổi `current_user` sang **Support B** (cùng `finance_view`) → `lastWrites` hiện vẫn trả `requestId`, `persisted.amount = 35.000.000`, `readback.finance` và readback giá vốn của A ⇒ **WRONG_PASS**.
4. Cùng session, đổi sang **Sale** → lớp `finance_view` chặn `payment_record`, nhưng `cost_rate_save` (mang giá vốn) vẫn được giao ⇒ **WRONG_PASS**.

Kỳ vọng sau sửa: cả hai trường hợp (Support B, Sale) → `lastWrites == []`; Support A không đổi danh tính/quyền vẫn nhận đủ `requestId`, `ok`, `persisted`, `readback`, `status`.
Không được coi `username`/`role` rỗng là bằng chứng "cùng danh tính" (rỗng == rỗng phải fail-closed).

### 3. Acceptance (positive + negative)
- Negative N1: Support A ghi → bỏ provenance → Support B: `lastWrites == []`.
- Negative N2: Support A ghi → bỏ provenance → Sale cùng session: `lastWrites == []`, không có `requestId`/số tiền/giá vốn.
- Negative N3: row có provenance nhưng danh tính/role lệch, hoặc provenance rỗng/không hợp lệ: không deliver.
- Positive P1: Support A không đổi danh tính/quyền: vẫn nhận `requestId`, `ok`, `persisted`, `readback` (kể cả `readback` lỗi thật của một lần ghi fail — kết quả fail vẫn được báo).
- Giữ nguyên lớp `finance_view` hiện có; không thêm session key, không thêm RBAC matrix.

### 4. Lệnh kiểm + exit code kỳ vọng
- `python -m pytest tests/test_logi255_lastwrites_finance_boundary.py -q`
- `python -m pytest tests/test_logi255_lastwrites_actor_isolation.py -q`
- `python -m pytest tests -q -rs`
- Gate: `0 FAILED / 0 ERROR`, SKIPPED không tăng so với 44 (đo lại thực tế trên HEAD này).
