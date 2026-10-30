# NEXT — Logistics Work Desk | checkpoint mục tiêu

> Cập nhật **30/10/2026**. Đây là snapshot để tiếp tục làm sản phẩm, không phải luật. Đọc `AGENTS.md` + Supreme Law trước; đo lại GitHub PR/HEAD trước khi dùng SHA lịch sử. Yêu cầu Owner mới nhất và GoalPlan/TaskPlan hiệu lực có ưu tiên cao hơn bản này.

## GOAL

Hoàn thiện **Logistics Work Desk thực sự dùng được**: Trường Thành nhìn Journey của một lô biết đang ở đâu, vướng gì, cần làm gì, chứng từ nào; Lục Giác xem duy nhất tiến độ/chứng từ đã được Trường Thành duyệt và trao đổi theo **đúng công đoạn**. Đơn giản, map-first; không thay phát triển chức năng bằng vòng viết prompt, QA hình thức hay framework mới.

## PROGRESS — mốc đã xác minh

- Repo đúng: `7roger89-web/logistics-work-desk-arena`.
- [PR #233](https://github.com/7roger89-web/logistics-work-desk-arena/pull/233): **MERGED** vào staging; `AGENTS.md` bắt buộc đọc checkpoint hiện tại.
- [PR #232](https://github.com/7roger89-web/logistics-work-desk-arena/pull/232): **MERGED vào staging** ở `e75a239277573f0d470607818e40b8d11f775e44`. Có Admin duyệt công bố event/document theo ID, version và hash nội dung, customer-only reader; fix modal giữ dữ liệu khi đổi khách. Bằng chứng review độc lập 29 challenge tests và focused suite ghi tại `evidence/g15-independent-review/README.md`. **G1.5 đạt code-level staging, chưa chứng minh Google OIDC và dữ liệu nghiệp vụ Lục Giác thật**.
- **Đã tích hợp:** [PR #234](https://github.com/7roger89-web/logistics-work-desk-arena/pull/234) **MERGED staging** ở `0e20a93c48f95b76839c093c9cb56bfcb1472e5f`. Comment + chứng từ gắn `customer_id + shipment_id + stage_id` của 7 mốc; cùng backend `quick_notes`, adapter `core/inbox_attachments` và pane Streamlit tại màn lô Trường Thành / dưới Journey Lục Giác. Tái kiểm tra quyền tải, khách đổi chủ, note INTERNAL, thu hồi file, ô nháp và rerun. GridFS/Drive chỉ theo cấu hình runtime, **không mặc định Drive**.
- Bản gốc PR #234 là patch `7roger89-web/CHUNLI@arena/5bc30481-chunli/logi/journey-notes/` với **7/7 Git blob SHA khớp byte-exact**; `31 PASS` của bản gốc chỉ là bối cảnh lịch sử.
- **QA trên HEAD mới (30/10):** `arena/6db41d2f-logistics-work-desk-arena` commit `2e510d50f2ec58284f4e3e8a74b1ea2bb42811e0` chạy thật: `tests/test_journey_notes.py` **48 PASS** (36 cũ + 12 mới), tập G1/G1.5 phụ thuộc **138 PASS**, full suite **34 failed / 2197 passed / 44 skipped** — trùng đúng tập FAILED nền 34 của `f80b2bd`, +12 test mới đều PASS. Ba mutation proof (stage draft, flash/rerun, recheck chủ lô) đều FAIL đúng chỗ. Bằng chứng: `evidence/journey-notes/session-qa-20261030.md`.

## CURRENT

**Staging hiện hành (30/10):** [PR #235](https://github.com/7roger89-web/logistics-work-desk-arena/pull/235) và [PR #237](https://github.com/7roger89-web/logistics-work-desk-arena/pull/237) đã merge: trao đổi/trả lời/đính kèm gắn **ngay vào node Journey Map** của cổng khách và shell nội bộ; backend tái xác minh khách + lô + công đoạn khi đọc/ghi. [PR #240](https://github.com/7roger89-web/logistics-work-desk-arena/pull/240) chỉ chứa workflow kiểm chứng công cụ ngoài app. [PR #241](https://github.com/7roger89-web/logistics-work-desk-arena/pull/241) đã merge staging tại `4dd3cb9aceaedf66a2128b8612a38012f3e13e50`, **chỉ lưu 4 ảnh/geometry/README bằng chứng QA**; không sửa hành vi sản phẩm. `main`/production không đổi.

**Browser QA Arena (bằng chứng, không phải Cloud UAT):** [evidence/arena-tooling-20261030/README.md](../evidence/arena-tooling-20261030/README.md) ghi nhận Chromium 153 thật trên E2B, chạy Streamlit + `mongomock` cô lập tại desktop 1440×900 / mobile 390×844. Shell Trường Thành: gửi và thấy bình luận ở node `LO-0306 / MAIN_CARRIAGE`; các điều khiển được kiểm `hitOk`, không tràn ngang. Cổng Lục Giác `QA-LOT / pickup`: bubble/điều khiển hiển thị và bấm được, **chưa chứng minh gửi trao đổi thành công**; ảnh customer ghi `Không gửi được trao đổi.` Source `views/customer_dashboard.py::handle_portal_events` không truyền `db` vào `consume_customer_triggers` dù đường render nhận `db` — có thể làm QA `mongomock` lỗi, cần tái hiện rồi sửa đúng ranh giới, không suy đoán production. Ảnh shell desktop cũng cho thấy khung trao đổi chiếm nhiều diện tích/khoảng trống, **chưa đủ bằng chứng trải nghiệm map-first dễ đọc**.

**Công cụ developer (tùy chọn, không phải sản phẩm):** `Playwright CLI 0.1.22` + `@sparticuz/chromium 153.0.0` chạy được **trong đúng phiên Arena** bằng cách cài cô lập qua npm, nhưng `PERSISTENCE=SESSION_ONLY`. `Serena 2.1.0` cài được nhưng `SERENA_ARENA_MCP=UNAVAILABLE` — không ép nối native tool. Graphify `graphifyy==0.9.96` đã chứng minh code-only trên **12 file của snapshot PR #237** qua [Actions 41041972435](https://github.com/7roger89-web/logistics-work-desk-arena/actions/runs/41041972435) (`678 nodes / 1463 edges`), nhưng workflow chỉ có trên nhánh `experiments/graphify-pilot-20261030`, chưa phải công cụ staging. Mỗi task code phải xác định từ source đường `entrypoint → handler → backend → test` trước khi sửa và đối chiếu `git diff --name-only` sau khi sửa. Dùng Graphify **theo nhu cầu** nếu đường liên kết nhiều module chưa rõ qua `rg`/đọc source; chạy lại trên HEAD/file liên quan, coi liên kết suy luận là gợi ý chứ không phải bằng chứng nghiệm thu. Không lấy đồ thị cũ làm nguồn hiện hành, không thêm Graphify vào app/P2P/CI mặc định.

## NEXT — công việc kế tiếp có giá trị

1. **Đóng luồng trao đổi khách hàng trong QA cô lập (một task trọn vẹn):** kiểm tra ảnh báo `Không gửi được trao đổi.`, tái hiện gửi note CUSTOMER bằng `mongomock` qua component thực, truy đường `views/customer_dashboard.py::handle_portal_events` → `views/journey_inline.py::consume_customer_triggers` → `core/journey_notes.py`. Nếu thiếu `db` trong QA là nguyên nhân, chỉ sửa đường inject/test nhỏ nhất, giữ fail-closed production. Nghiệm thu: khách gửi → reload thấy đúng node/lô → staff thấy/trả lời → khách thấy trả lời; sai khách/lô/công đoạn không thấy hoặc không ghi được. Test/browser cô lập phải có bằng chứng; **không coi việc nút `Gửi` bấm được là PASS**.
2. **Kiểm trải nghiệm map-first trên desktop/mobile sau khi chức năng đạt:** ảnh [staff-desktop](../evidence/arena-tooling-20261030/staff-desktop-1440x900-node-discussion.png) còn khung trắng lớn, map phía sau khó đọc; làm rõ và sửa bố cục theo yêu cầu Owner về diện tích, vị trí node/panel, rồi nghiệm thu ảnh thực. Không chạy vòng chỉnh CSS chỉ vì geometry test xanh.
3. **UAT Cloud an toàn:** trước ghi lên `thu-log-g1-test.streamlit.app`, phải xác minh deployed SHA, danh tính DB và quyền thật, không lộ secret; chưa có bằng chứng thì `CLOUD_QA=BLOCKED`. Kiểm chứng Google OIDC, Trường Thành gửi → Lục Giác xem/trả lời → tải lại chứng từ theo đúng lô/công đoạn. Không động `main`/production hay công bố chi phí nội bộ.

## BLOCKERS / GATES

- PR #234 đã **MERGED staging**. Bằng chứng code: QA Arena `48 PASS` stage notes, `138 PASS` tests phụ thuộc; full suite còn **34 lỗi nền** theo cùng máy/baseline. Control Tower đọc lại code/test trên HEAD QA và không thấy blocker mới; các test không được chạy lại trong container hiện tại (thiếu Streamlit/mongomock).
- **Blocker review #237 (đã sửa):** tải chứng từ trong Journey Map từng không buộc note vào đúng lô + công đoạn đang mở. Nay `read_note_attachment(..., expected_scope=…)` kiểm tra `customer_id + shipment_id + stage_id` của chính note **trước khi** đọc byte; `views/journey_inline.py` luôn truyền phạm vi server đã resolve. 5 test mới (đúng phạm vi, lô khác, công đoạn khác, lô ngoài projection, fail-closed) + mutation proof (bỏ binding → 3 test FAIL). Full suite `34F/2262P` trùng tập FAILED nền 34.
- **Khả năng browser:** nhờ npm `@sparticuz/chromium`, Arena **đã chạy được Chromium thật trong E2B cho test cục bộ**, dù CDN Playwright bị chặn. Kết quả chỉ đúng phiên sandbox đã thử; cài đặt mất khi mở phiên mới. **Chưa phải PASS của Cloud runtime/OIDC/DB hoặc UX tổng thể**. Serena native MCP vẫn không được Arena hỗ trợ.
- **QA cổng khách chưa đóng:** ảnh `customer-mobile-390x844-node-discussion.png` hiển thị `Không gửi được trao đổi.`; cần phân biệt lỗi đường inject database của fixture cô lập với lỗi production, không công nhận CUSTOMER_SEND_PASS khi chưa có readback + reload. Giao diện shell desktop còn khoảng trắng lớn, độ dễ đọc chưa nghiệm thu.
- `thu-log-g1-test.streamlit.app`: deployed SHA và danh tính DB runtime chưa được chứng minh; **không ghi Cloud/production** chỉ để test.
- Nguồn chứng từ/sự kiện Lục Giác thật chưa được nghiệp vụ xác nhận; hash/fixture chỉ chứng minh contract phần mềm. Thông tin chi phí, margin, báo giá nội bộ và công nợ thiếu đối soát tuyệt đối không công bố.
- `main` trước công việc này: `9e4190b278dd2ced8771c5249582753d34e561db`; không merge `main` hoặc deploy production nếu thiếu Owner Gate. PR #226 lịch sử Draft, không phải workstream tiếp theo.

## SUCCESS CHECKS

- Staff có `shipment_edit` ghi/xem INTERNAL và CUSTOMER; khách chỉ ghi/xem CUSTOMER đúng lô và công đoạn.
- Upload file qua kho đang có; download xác minh lại note, khách, quyền, lô **hiện tại**, tệp và trạng thái AVAILABLE. Không lộ GridFS ID/hash/link nội bộ.
- Sau reload/đổi khách, không còn dữ liệu hay bản nháp của khách trước; test trên code commit `2e510d5` được QA báo PASS và cùng code blob đã merge staging. Cần UAT Cloud riêng trước phát hành.
- Mọi phát hành/live UAT tách biệt việc merge code; không tự nhận app production đã có chức năng.

## Nhật ký mốc quan trọng

- **30/10:** PR #233 merged staging; PR #232 có independent challenge và merged staging tại `e75a239`.
- **30/10:** Patch comment/chứng từ từ CHUNLI áp dụng byte-exact lên nhánh cô lập; thêm bảo vệ đọc/tải lô đã chuyển chủ, tệp thu hồi và bản nháp đổi khách; PR #234 Draft chờ chạy test sau sửa.
- **30/10 (QA thực chạy):** 48 PASS `test_journey_notes.py`, 138 PASS tập G1.5 phụ thuộc, full suite 34F/2197P/44S trùng baseline; sửa 3 lỗi UI (nháp lẫn công đoạn, gửi xong chưa thấy note, nhãn tệp chưa escape) tại `2e510d5`; Cloud QA vẫn `BLOCKED`.

- **30/10 (staging integration):** Control Tower fast-forward patch QA Arena vào PR #234 HEAD `cc9f9a7ae50abe9244ae2a457e5e3dbcb31bcc5a`, kiểm tra nguồn/test/20 điều kiện an toàn, merge **staging** ở `0e20a93c48f95b76839c093c9cb56bfcb1472e5f`; `main` giữ nguyên. Cloud UAT vẫn BLOCKED vì runtime SHA/DB chưa xác minh.

- **30/10 (Journey Map dùng được):** thêm nút “💬 Trao đổi / Chứng từ” tại node Journey Map ở cả hai cổng; một trigger `journey_focus` read-only, server tái xác minh danh tính/lô/công đoạn, mở đúng pane đang có; sửa luôn phát hiện `views/shipment.py` (pane nội bộ PR #234) không được route. Đo tại `7ac441b`: baseline 35F/2196P → sau sửa 35F/2216P (không failure mới); `tests/test_journey_notes.py` 48 PASS. Cloud UAT vẫn BLOCKED; không browser thật trong sandbox. **Sửa blocker review:** node nội bộ thật (`MAIN_CARRIAGE`, `si-vgm`, `gate-in`, …) được ánh xạ tường minh sang 7 nhóm trao đổi ở `views/journey_focus.STAFF_NODE_STAGES` (id lạ vẫn fail closed; cổng khách giữ 7 stage canonical); fixture `LO-0307 / MAIN_CARRIAGE` → pane `Vận chuyển` đã PASS, full suite 34F/2247P trùng tập FAILED nền.

- **30/10 (browser/tooling evidence):** PR #237/#240/#241 đã merge staging; HEAD sau PR #241 `4dd3cb9`. Arena có browser cục bộ, Serena MCP native vẫn không hỗ trợ; Graphify pilot chỉ ở nhánh thử nghiệm. Ghi nhận rõ CUSTOMER_SEND chưa qua QA cô lập; Cloud UAT chưa chạy.

**Duy trì:** chỉ cập nhật CURRENT/NEXT/BLOCKERS và một mốc PR/SHA khi việc thực sự đổi. Không log từng thao tác, không dựng bảng roadmap khác.