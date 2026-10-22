# HEXA V0 — bằng chứng và bàn giao demo

## 1. Định danh và đường mở

- `TASK_ID=HEXA-V0-DEMO-01`
- `EXACT_BASE_HEAD=83162293036414dcafa01072b93eece8733b8688`
- `DEMO_CODE_COMMIT=6d7b2b299172d21dfc8e7fdeab76c42fc561cba0`
- `BRANCH=arena/5009c0d2-logistics-work-desk-arena`
- `DEMO_SCOPE=STANDALONE_HTML_ONLY`; không phải chức năng production, không phải nghiệm thu tích hợp Journey.
- HTML tại commit cố định: [`experiments/hexa-v0-demo/index.html`](https://github.com/7roger89-web/logistics-work-desk-arena/blob/6d7b2b299172d21dfc8e7fdeab76c42fc561cba0/experiments/hexa-v0-demo/index.html)
- HTML theo nhánh làm việc: [`arena/5009c0d2-logistics-work-desk-arena`](https://github.com/7roger89-web/logistics-work-desk-arena/blob/arena/5009c0d2-logistics-work-desk-arena/experiments/hexa-v0-demo/index.html)

### Mở bằng Chrome Windows — tối đa 3 bước

1. Mở **HTML tại commit cố định** ở trên, bấm **Raw**, rồi `Ctrl+S` và lưu thành `hexa-v0-demo.html`. Nếu đã có checkout, bỏ qua thao tác tải và dùng trực tiếp `experiments/hexa-v0-demo/index.html`.
2. Nhấp đúp tệp đã lưu để mở bằng Chrome. Không cần server, đăng nhập, CDN hoặc kết nối mạng.
3. Chọn **LG ↔ TT**, một trong **bốn mốc** hoặc nút hành động mô phỏng; bấm **Vì sao hiển thị như vậy?** để xem nguồn/lịch sử. **Reset demo** trở về trạng thái đầu.

> Các thao tác chỉ đổi dữ liệu trong bộ nhớ trang. Tải lại trang hoặc Reset không ghi database, không gửi email/Zalo, không điều xe và không tạo phân quyền thật.

## 2. Kết quả kiểm thử đã chạy

Môi trường: Node `v22.22.3`, repository root, source tại `DEMO_CODE_COMMIT` ở trên.

```bash
node experiments/hexa-v0-demo/verify.mjs
```

Kết quả thật sau khi commit và chạy lại:

```text
HEXA_V0_LOGIC=PASS | TOTAL=24 | PASS=24 | FAIL=0
```

Các nhóm được kiểm tra bằng chính logic inline trích từ HTML, không phải bản dữ liệu tách rồi:

| Nhóm kiểm tra | Kết quả |
|---|---|
| Không tài nguyên ngoài, API, storage hay script dependency; nhãn DEMO và Reset | PASS |
| Chỉ hai role; role toggle không được gọi là bảo mật đa khách hàng | PASS |
| Bốn mốc LTL: tin chưa xác minh → ETA xác minh → LG phản hồi → TT chốt phương án | PASS |
| Đúng vai trò mới thực hiện hành động mô phỏng tương ứng; sai vai trò không đổi state | PASS |
| Đổi TT ↔ LG giữ nguyên lô, mốc và ba dữ kiện giờ; Reset về initial state | PASS |
| Lịch khách yêu cầu, ETA và giờ cam kết tách riêng ở cả hai góc nhìn | PASS |
| Tin chưa xác minh không thành ETA/cam kết; phản hồi LG không tự điều xe | PASS |
| Popup của việc hiện tại có tối đa bốn trường; không form upload/gửi tin giả | PASS |
| Sao chép nội dung không đổi lần cập nhật khách, không đổi state và không có lệnh SEND | PASS |
| Tệp đính kèm không tự thành chứng từ được chấp nhận | PASS |
| Chứng từ thanh toán tiền hàng không chứng minh nhà máy cho xuất hoặc TT đã thu tiền | PASS |
| Góc nhìn LG không render mã ghi chú nội bộ TT hay commercial internals | PASS |
| Audit có nguồn, bên xác minh, phiên bản và lịch sử ETA tới mốc đang chọn | PASS |
| FCL có booking, SI/VGM/CY cutoff với múi giờ; SI gửi và SI accepted là hai sự kiện | PASS |
| `SUBMITTED`-only không hoàn tất SI/VGM; ETD không được dùng làm ATD khi actual trống | PASS |
| Tới cảng và thông quan độc lập; giao 4/8 kiện không hoàn tất toàn lô | PASS |
| LTL không render SI/VGM/CY hoặc node SEA | PASS |
| Source-level responsive: viewport, breakpoint, vùng cuộn Journey; urgent đứng trước stepper/Journey | PASS |

Bổ sung đã chạy:

- Inline script được trích nguyên vẹn và chạy `node --check`: `PASS` (`48,798` bytes script).
- `git diff --check`: `PASS`.
- Secret-pattern scan trên diff code so với locked base: `SECRET_SCAN=CLEAN`.
- SHA-256 tại code commit:
  - `index.html`: `815747772e18e8b39833821b58e72764b36ff2999ec34e2a5ed9efc44c05d9a2`
  - `verify.mjs`: `d38b507260f55953272b6d3143f9334e338e7a4b4f11b4abc5655785426dd25c`

## 3. Browser và visual — chưa xác minh

`BROWSER_QA=BROWSER_NOT_VERIFIED`

Probe trong sandbox không tìm thấy executable `chromium`, `chromium-browser`, `google-chrome`, `chrome` hoặc `msedge`; không có thư mục browser Playwright. Python chỉ resolve namespace `playwright` cục bộ, không có `playwright.sync_api` hoặc `playwright.__main__`; Node không có browser runner đã cài. Vì vậy:

- `CHROME_WINDOWS=NOT_VERIFIED`
- `VISUAL_1440x900=NOT_VERIFIED`
- `VISUAL_390x844=NOT_VERIFIED`
- `DIALOG_AND_CLIPBOARD_RUNTIME=NOT_VERIFIED`
- Không có ảnh chụp rendered, không tự nhận visual PASS, không khẳng định đã hết tràn ngang hoặc lỗi tương tác browser.

Các mục responsive được đánh PASS ở Mục 2 chỉ là **kiểm tra source và thứ tự DOM do logic tạo ra**, không thay thế Chrome Windows ở hai viewport. Owner/UAT cần mở file offline và kiểm lại popup, Reset, sao chép, cuộn ngang Journey và bố cục thực tế.

## 4. Đối chiếu sự kiện với mã nguồn Arena

Các mốc dưới đây đọc tại locked base. “Demo giả lập” là phần mới trong HTML; không được diễn giải thành tích hợp đã hoàn thành.

| Sự kiện / phần hiển thị | Mã nguồn Arena đã có | Phần demo giả lập | Khoảng trống khi triển khai thật |
|---|---|---|---|
| Hồ sơ EXW tách ROAD/LTL và SEA/FCL | `core/shipment_execution_profile.py:88-105` (EXW any-mode), `:232-345` (mode/load model và validate) | `DEMO_DATA.ltl/fcl`, nhãn `EXW · Đường bộ · LTL` và `EXW · Đường biển · FCL` | Đọc profile đã persist, chặn profile thiếu/không hợp lệ; không suy mode từ mã lô demo. |
| Journey LTL: lấy hàng, nhận/ghép, qua cửa khẩu, giao hàng | `core/shipment_journey.py:1-5` (visual index, không phải workflow authority), `:307-334` (road facts/LTL/border), `:376-379` (delivery) | `ltlJourney()` rút gọn bốn node và bốn trạng thái phối hợp | Dùng `build_journey` và canonical facts/scope thật; không dựng bản đồ thứ hai làm authority. Phải chứng minh từng actual event, không suy từ profile hoặc ngày dự kiến. |
| Booking, SI/VGM, gate-in/CY, ETD/ATD/on-board, arrival/customs/delivery FCL | `core/shipment_journey.py:39-45` (`SUBMITTED`/`ACCEPTED`, booking), `:169-258` (booking/SI/VGM/gate-in/ETD/ATD/on-board/arrival), `:347-379` (customs/delivery), `:506-524` (acceptance gate) | `DEMO_DATA.fcl`, `fclJourney()` và bảng dữ kiện tách biệt | Nối từng fact với writer/nguồn thật. **CY cutoff và timestamp gửi/accepted riêng là dữ kiện demo mới**, chưa được gán là field production đã có; cần chốt nơi lưu, múi giờ, actor và nguồn. |
| Việc khẩn, owner/deadline, mở đúng popup từ một việc | `component/src/components/AttentionNow.tsx:6-17,125-153`; `component/src/components/JourneyBubble.tsx:7-60` | Urgent card, queue và `dialogFor()` với tối đa bốn trường | Derive từ projection thật, deep-link đúng stage, enforce writer permission; danh tính/assignee thật và next-update deadline phải có source. Role demo không phải phân công nhân sự chính thức. |
| Tệp đính kèm nhưng chưa được chấp nhận | `component/src/components/JourneyBubble.tsx:16-18,47-59` (`FILE_PRESENT != DOCUMENT_ACCEPTED`) | `packing-list-DEMO.pdf`, `Tệp đã ghi nhận`, `Chưa xác nhận` | Dùng attachment/document ID thật và acceptance authority phù hợp; upload/copy không được tự hoàn tất chứng từ. |
| Lịch yêu cầu ≠ ETA ≠ giờ cam kết; lịch sử thay đổi | `core/shipment_journey.py:178-180,243-258,376-379` giữ actual/evidence/deadline riêng; file cũng nêu không suy actual từ ETA/past ETD | Ba time card, `LTL-v0…v4`, audit source/verifier/ETA history | Chốt canonical fields cho nhu cầu khách, ETA vận hành và cam kết; cần event/version/actor store thật. Demo không chứng minh các field/history này đã tồn tại. |
| Cập nhật khách và sao chép nhưng chưa gửi | `AttentionNow.tsx` và `JourneyBubble.tsx` chỉ là nguồn tham chiếu UI; không được coi là email/Zalo outbox | Nội dung mẫu, last/next update, nút sao chép không có lệnh gửi | Nếu tích hợp sau này cần message event + delivery receipt độc lập; không đánh dấu đã gửi từ clipboard. Demo không tích hợp thông báo. |
| Hai góc nhìn và giới hạn dữ liệu LG/TT | `core/auth.py:63-147` (ROLE_PERMISSIONS, `has_permission`) | Role toggle và conditional rendering của ghi chú nội bộ | Phải enforce server-side shipment scope, field filtering và cô lập từng khách hàng bằng test thật. Toggle demo **không phải bằng chứng RBAC hay bảo mật đa khách hàng**. |
| Giao một phần không hoàn tất lô | `core/shipment_journey.py:352-379` tách actual delivery/POD và dùng delivery fact riêng | `4/8 kiện`, `Hoàn tất toàn lô: Chưa xác nhận` | Persist số lượng giao từng lần và final-delivery fact riêng; không suy hoàn tất từ một partial event hoặc POD. |
| Chứng từ tiền hàng, xuất nhà máy và tiền TT thu | **Không tự gán mapping trong packet này**; không dùng module thanh toán khác để suy quan hệ pháp lý | Một dòng tham khảo tách `payment proof`, `factoryRelease=Chưa xác nhận`, `ttReceipt=Chưa xác nhận` | Owner phải xác định chủ thể trả/nhận, nguồn chứng từ, quyền xem và ba fact độc lập trước khi triển khai. |

## 5. Ranh giới bàn giao

- Code commit chỉ thêm `experiments/hexa-v0-demo/index.html` và `verify.mjs`; không sửa Python, React, `component/dist`, `.p2p/portable/*`, quyền hiện có hay production data.
- Không backend, API, database, login, CDN, server, GPS, xếp xe, thanh toán hay tích hợp thông báo.
- Không dashboard thứ ba: chỉ LG và TT trên cùng hồ sơ/mốc; LTL và FCL là hai hồ sơ demo được chọn trong cùng artifact.
- Không merge `main`, không deploy, không cập nhật hoặc mở lại PR #211, không tạo PR mới.
- `OWNER_UAT=INCOMPLETE`; `VISUAL_ACCEPTANCE=INCOMPLETE`; `PRODUCTION_INTEGRATION=NOT_STARTED`.
- OE Gate: `SIMPLER_PATH=YES | MATERIAL_PROGRESS=YES | NECESSITY=YES | CORE_BEFORE_SUPPORT=YES | SMALLER_VERIFIABLE_SLICE=YES`; verdict `DO_IT` vì artifact này đủ đánh giá bài toán phối hợp trước khi viết chức năng thật, không mở rộng V1.
