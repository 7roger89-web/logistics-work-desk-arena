# Streamlit vs SPA — đo trước khi bàn rewrite (Phase H)

Ngày đo: 2026-10-26. Trạng thái: **báo cáo đo, không sửa code**. Mọi con số dưới
đây là output thật của bốn bộ test latency/render có sẵn, chạy lại trong phiên
làm việc; không suy diễn từ tài liệu cũ.

## 1. Phương pháp và môi trường

- Lệnh chạy:

  ```bash
  python -m pytest \
    tests/test_logi_interaction_latency_finalize_02.py \
    tests/test_logi_interaction_latency_repair_01.py \
    tests/test_logi_render_performance_01.py \
    tests/test_login_shell_latency.py \
    -v --durations=25 --continue-on-collection-errors --junitxml=/tmp/phaseH.xml
  ```

- Môi trường: Python 3.11.2, pytest 9.1.1, Streamlit 1.66.1, mongomock 4.3.0,
  Linux sandbox 2 CPU, transport `SANDBOX_STAGING` (không có Atlas thật, không
  có nhà cung cấp ngoài). Quy mô fixture: **N=95 lô hàng**.
- Kết quả phiên: **54 passed / 2 failed / 56 test, 10.19s** (tổng thời lượng
  junit 9.11s). Hai test đỏ nằm trong `tests/known_red.txt` từ BASE — không phải
  regression của phase này.
- Giới hạn đo phải nói thẳng: đây là thời lượng **server-side trong process trên
  mongomock**. Chính test đã in `LOCAL sandbox timing — Atlas latency not
  represented`; `RTT_MODEL=0ms/op`, `PROVIDER_MODEL=0ms` vì không gọi network/AI
  thật. Chưa có số browser thật (FCP/TTI/INP), chưa đo đa người dùng.

## 2. Số đo thật

### 2.1. Chi phí mỗi tương tác server-side (`..._finalize_02`, N=95)

| Tương tác | TOTAL_SERVER_MS | callback | script body | Ghi chú |
|---|---:|---:|---:|---|
| `translate_text` | 471.2 | 2.3 | 468.9 | payload 1.730.122 byte; build view-model 468.5ms |
| `shipment_commercial_flow_save` | 217.2 | 9.5 | 207.6 | |
| `payment_record` | 170.5 | 8.0 | 162.5 | |
| `shipment_document_selection_save` | 162.3 | 6.1 | 156.1 | |
| `shipment_field_save` | 154.1 | 9.6 | 144.5 | payload 1.745.593 byte |

Phân tách sâu của lần đắt nhất (translate_text): `READ_SHARED_SOURCES_MS=319.6`
là thành phần lớn nhất, sau đó `PER_SHIPMENT_PROJECTION_MS=71.9`,
`LOAD_SHIPMENTS_MS=20.1`, `SERIALIZATION_MS=22.1`. Phần callback Streamlit chỉ
2.3ms — chi phí nằm ở **đọc dữ liệu và dựng lại view-model**, không phải ở lớp
vẽ của framework.

### 2.2. Render performance (`test_logi_render_performance_01`, N=95)

- In thật từ test: `legacy projections+payables=203.9ms  build_view_model=227.3ms
  (LOCAL sandbox timing — Atlas latency not represented)`. Hai đường cho kết quả
  bằng nhau (`test_fast_path_output_equals_legacy_per_call_readers` pass) — đường
  "fast" không làm đổi kết quả, chỉ đổi cách đọc.
- Acceptance mang tính quyết định trong bộ test này là **số lần đọc collection bị
  chặn trên (bounded)**, không phải thời gian: mỗi ledger collection đọc tối đa
  một lần/lần render, đọc docgen bị chặn, đọc audit hằng số. Tất cả guard pass.
- Ba test chậm nhất file: 0.541s, 0.536s, 0.276s (thời lượng process, gồm dựng
  fixture).

### 2.3. Login shell (`test_login_shell_latency`)

4/4 pass. Probe tồn tại user chỉ lấy 3 field (`_id`, `username`, `is_deleted`),
một lần đọc; module đồ thị đã đăng nhập (`views.logi_shell`,
`views.logi_view_model`) không bị import cho đến khi đăng nhập thành công —
đường tới màn hình login được giữ lazy có kiểm định.

### 2.4. Điểm "đánh vật với framework" có số liệu

Hai test đỏ đăng ký ở known_red đều nằm ở lớp tương thích mô hình chạy của
Streamlit (`test_logi_interaction_latency_repair_01`):

- `..._test_adversarial_reverting_to_baseline_produces_double_build_and_rerun` —
  kiểm chứng adversarial việc một lần tương tác có thể kéo theo **dựng lại VM hai
  lần + `st.rerun`** nếu callback không chạy trước script body.
- `..._test_duplicate_trigger_in_same_prefix_batch_does_not_double_dispatch` —
  assert thực tế: `0 != 1 : Handler must be invoked exactly once across callback
  batch`; hợp đồng "một batch prefix chỉ dispatch một lần" chưa được thỏa ở BASE.

Kiến trúc bù xung quanh Streamlit (free worker đọc ngoài script thread, replay
tuần tự, một lần dựng view-model mỗi tương tác) là lý do tồn tại cả file
`logi_sandbox.py` lẫn hai file latency test. Đây là khu vực ma sát framework rõ
nhất, nhưng nó đã được **đo và có guard**, chưa phải lý do đủ để đổi stack.

## 3. Trả lời admission gate cho ngôn ngữ/runtime mới

Tham chiếu 6 câu trong `docs/ARCHITECTURE-PRINCIPLES.md`.

1. **Bottleneck/need cụ thể, bằng chứng ở đâu?** Chưa có bottleneck framework
   nào được chứng minh. Số đo cho thấy chi phí chủ yếu ở đọc dữ liệu/dựng
   view-model server-side (319.6ms đọc shared sources trong kịch bản 471.2ms),
   còn callback Streamlit chỉ 2.3–9.6ms. Không có số browser (FCP/TTI/INP) nên
   không thể quy kết trải nghiệm chậm cho Streamlit.
2. **Tại sao stack hiện tại không giải quyết đủ tốt?** Hiện chưa trả lời được
   bằng vật chất: hai vấn đề đo được (dispatch trùng trong một batch, double
   build/rerun) là sai lệch hợp đồng trên code hiện tại, có thể sửa trong Stack
   hiện tại — chúng đã có test đỏ làm đích, không đòi SPA.
3. **Boundary tích hợp nhỏ nhất?** Nếu sau này có bằng chứng browser, boundary
   nhỏ nhất theo chính sách là một component React độc lập cho đúng điểm nghẽn
   (repo đã có một component React/Vite ở `component/`), không phải rewrite shell.
4. **Benchmark/acceptance trước-sau?** Chưa có. Cần đo Atlas thật + browser thật
   ở N=95 và N lớn hơn (FCP/TTI/INP, số lần dựng VM mỗi tương tác, payload
   serialized ~1,73MB/lần) trước và sau bất kỳ thay đổi nào.
5. **Chi phí build/deploy/observability/security/maintenance?** Chưa lượng giá
   được vì chưa có phương án cụ thể; thêm SPA nghĩa là thêm pipeline Node, nguồn
   phân quyền thứ hai phải đồng bộ với `ROLE_PERMISSIONS`, và bề mặt deploy mới —
   tất cả là chi phí thực chưa có lợi ích đo được.
6. **Rollback path?** Chưa thiết kế; theo policy, component mới phải có interface
   ổn định và gỡ được độc lập. Hiện không có gì để rollback vì chưa thay đổi.

## 4. Verdict cho Owner

**KHÔNG mở admission gate cho SPA/ngôn ngữ mới ở thời điểm này — DEFER có điều
kiện.** Lý do trung thực: (a) các số đo hiện có đều là server-side trên
mongomock và chỉ ra chi phí đọc/dựng dữ liệu, không phải giới hạn vẽ của
Streamlit; (b) chưa có một chỉ số browser/Atlas thật nào; (c) hai điểm ma sát
framework đã có test guard đỏ làm backlog sửa được trong stack hiện tại.

Việc nên làm tiếp (theo thứ tự, đều không cần rewrite):

1. Sửa hai test đỏ trong `test_logi_interaction_latency_repair_01` để khóa hợp
   đồng dispatch-một-lần và hết double-build (backlog known-red đã định danh).
2. Đo lại trên Atlas thật + trình duyệt thật (FCP/TTI/INP, payload mỗi lần
   rerun) ở N=95 và N=300; khi đó mới đủ dữ liệu tranh luận về SPA.
3. Tối ưu `READ_SHARED_SOURCES_MS` (319.6ms, thành phần lớn nhất) nếu cần cải
   thiện độ trễ — đây là tối ưu đọc dữ liệu, độc lập framework.

Mục chưa đo được trong phiên này (không che giấu): độ trễ mạng Atlas, độ trễ nhà
cung cấp AI/Drive, mọi chỉ số phía trình duyệt, tải đa người dùng, hành vi dưới
dữ liệu lớn hơn N=95.
