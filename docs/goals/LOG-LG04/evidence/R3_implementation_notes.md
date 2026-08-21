# LOG-LG04 — Ghi chú triển khai (phase 3)

## Baseline
- Regression tại aa5cef4: 217 passed / 28 skipped / 0 failed ✅
- Production read-only: customers=362, shipments=78 (đã xác minh ở LG03)

## Files liên quan (đã nắm rõ)
- `views/shipment_360.py`: render_shipment_workspace (dòng 40-181) — workspace read-only trên cùng; render_shipment_360_summary (259+) — 16 thẻ metric trong tab FINANCE.
- `views/shipment.py`: ui_shipment_detail_tabs (93-614): render_workspace (115-125), header chỉnh sửa (128-169), 3 tabs (172): t1 PICKUP & XUẤT KHẨU (174-189), t2 IMPORT & GIAO HÀNG (194-364), t3 FINANCE (366-563): 360 summary → "1. Dịch Vụ & Doanh Thu" (form dịch vụ 369-443, hàng dạng `c = st.columns([0.5,3,1,1.5,1.5,1,1.5,0.5])` KHÔNG kẻ khung) → "2. Chi Hoa Hồng" (475-482) → "3. Lịch sử Thu tiền" (484-541) → 📊 BẢNG KÊ TÀI CHÍNH (544-563) → 🕒 Lịch sử thay đổi (565-576) → save (578-613).
- `core/shipment_workspace.py`: build_shipment_workspace_view (199-282) — next_action, alerts, context, factory_lots, documents (fallback 5 cột: document/status/step/source/required), timeline.
- `views/quotations.py`: form báo giá — service code + currency + qty + cost_unit + sell_unit + tax_pct; nâng cao: usd_rate, cny_rate, fx_source, goods_value, goods_currency, entrusted_rate, remittance_amount, bank_pct, swift; lô hàng: factory/contact/phone/packages/cbm/weight/pickup_address.
- `views/agreements.py`: tabs (492): "Danh sách thỏa thuận"/"Tạo từ báo giá chốt"/"Chi tiết & Bàn Giao"; _render_agreement_detail 6 tabs gồm "Bàn giao vận hành"; handoff = 16 câu hỏi.

## Đã làm
- [x] R1_owner_feedback_mapped.md, R2_block_classification_audit.md, DESIGN.md
- [x] core/next_action_card.py — render_next_action_card(action, anchor=...) card VIỆC TIẾP THEO nổi bật (border 3px theo severity, icon, level text, who, nút "⬇ Xử lý ngay" scroll đến anchor bookmark)

## Còn lại (W1-W6 theo DESIGN.md)
- [ ] W1: shipment_360.py — thay NEXT ACTION cũ bằng render_next_action_card; cảnh báo free time sắp hết → nâng severity
- [ ] W2: 3 thẻ việc chính trên đầu (🚛 Lấy hàng & Xuất khẩu / 🛃 Nhập khẩu & Giao hàng / 💰 Chi phí & Công nợ) — mỗi thẻ có trạng thái rút gọn + nút tới tab tương ứng (dùng anchor bookmark + JS scroll hoặc active_page + active_tab session state; Streamlit tab switch cần đặt active_tab session_state key — tab object có name, set st.session_state.active_tab)
- [ ] W3: thu gọn context (đổi tên "👥 Ai tham gia lô hàng này" + giải thích 1 câu + nút "Xem hồ sơ đối tác" chứa 3 nút 360 cũ); factory_lots ẩn khi UNKNOWN; documents fallback → danh sách 1 dòng; alert grouping
- [ ] W4: tab FINANCE thứ tự mới: form dịch vụ kẻ khung (container border per row + nhãn đầy đủ) lên đầu, summary cards sau, bảng kê + lịch sử cuối
- [ ] W5: quotations.py kẻ khung dòng dịch vụ, tách Essential vs expander "📐 Cài đặt nâng cao"
- [ ] W6: agreements.py 4 bước hành trình + giải thích tiếng Việt + đổi tên "Bàn giao vận hành — 16 câu hỏi" → "Kiểm tra đủ thông tin cho Support"
- [ ] T8 beginner QA (AppTest browser), responsive narrow viewport QA
- [ ] T10 regression + RBAC + finance oracle + encoding + secret scan
- [ ] T11: state.json = READY_FOR_OWNER_LG04_RELEASE_GATE, draft PR #3, push nhánh log-lg04-daily-work-simplification

## Quy tắc an toàn tuyệt đối
- Không đổi permission; không thêm write path tài chính; UNKNOWN != ZERO; ESTIMATE != ACTUAL; commercial flow finance mutation oracle = 0; production chỉ đọc.


## Cập nhật tiến độ (sau W1-W6 draft + LG04 UI tests)

### Đã làm xong (code OK, compile OK)
- core/next_action_card.py: render_next_action_card(action, anchor) — card VIỆC TIẾP THEO viền 3px theo severity (critical đỏ #C81E1E, warning cam #B45309, normal xanh #0B6E99, info xám), nút "⬇ Xử lý ngay" scroll đến anchor.
- views/shipment_360.py: viết lại render_shipment_workspace — card Việc tiếp theo trên cùng (Ý 3), 3 thẻ việc chính 🚛/🛃/💰 với nút "Mở ..." đặt st.session_state.active_shipment_section + scroll anchor (Ý 1), expander "👥 Ai tham gia lô hàng này" có giải thích tiếng Việt (Ý 4, 8), factory_lots ẩn khi rỗng (Ý 6), documents dạng danh sách 1 dòng + expander chi tiết (Ý 2), alerts gộp trong 1 expander, giữ nguyên keys cũ cho backward compat với tests: shipment_customer_context_{id}, shipment_factory_context_{id}, shipment_partner_context_{id}.
- views/shipment.py: anchor lg04_tab_export/import/finance trong 3 tabs; st.tabs(..., default=label) theo active_shipment_section (FINANCE input-first — Ý 1, 7); subheader tài chính "1. Dịch Vụ & Doanh Thu — nhập chi phí và giá bán" + caption hướng dẫn (Ý 7); dòng dịch vụ kẻ khung .lg04-service-row (Ý 9).
- views/quotations.py: mỗi dòng dịch vụ kẻ khung .lg04-quote-line (Ý 9); tỷ giá + ủy thác + chuyển tiền gộp vào expander "📐 Cài đặt nâng cao" (Ý 9).
- views/agreements.py: hành trình 4 bước (Báo giá → Khách chốt → Thỏa thuận → Bàn giao cho Support) ở đầu trang + 5 câu giải thích (Ý 10); caption tạo thỏa thuận rõ nghĩa; đổi "Bàn giao vận hành — 16 câu hỏi Support cần có" → "Kiểm tra đủ thông tin cho Support" + caption giải thích (Ý 10).

### Test mới tests/test_lg04_daily_work_ui.py (AppTest.from_string page_src)
- 7/9 pass. Còn 2 fail đang chẩn đoán:
  1. test_primary_work_cards_render_three_labels: labels "Lấy hàng & Xuất khẩu" v.v. KHÔNG có trong test.markdown — có thể vì markdown bên trong card render bằng st.markdown trong columns nhưng test chỉ thấy phần không có; kiểm tra bằng diagnostic.
  2. test_tabs_jump_to_finance: db connection thật bị gọi (MongoDB connection failed — test cần patch load_proxy_payments/load_entrustments/load_audit_logs như test cũ), subheader không thấy.
- Diagnostic script: tools/_diag_lg04.py (xóa sau khi xong).

### Regression hiện tại: 217 passed / 28 skipped / 0 failed (bao gồm test entity context)

### Còn lại
- Sửa 2 test fail + chạy full regression
- Responsive QA (viewport hẹp): dùng AppTest không kiểm được width thực — thay bằng kiểm tra CSS media query có trong file + mở app sandbox viewport kiểm thị giác
- Regression/RBAC/finance oracle (T10)
- Encoding + secret scan
- state.json = READY_FOR_OWNER_LG04_RELEASE_GATE (T11), PR #3 draft


## Kết quả QA code (trước khi responsive + release)

Regression toàn bộ suite: **226 passed / 28 skipped / 0 failed** (217 baseline + 9 test mới LG04 UI). Bộ test mới `tests/test_lg04_daily_work_ui.py` kiểm tra: card VIỆC TIẾP THEO (viền 3px theo severity, nút Xử lý ngay, free time quá hạn đè lên next action), 3 thẻ việc chính với 3 nút "Mở Xuất khẩu / Mở Nhập khẩu & Giao hàng / Mở Chi phí", expander "👥 Ai tham gia lô hàng này" có giải thích tiếng Việt, ẩn khối nhà máy khi rỗng, UNKNOWN không bị chuyển thành 0, tab Tài chính mở mặc định khi bấm Mở Chi phí, form báo giá 3 dòng kẻ khung + 1 expander cài đặt nâng cao, hành trình 4 bước báo giá.

Lưu ý kỹ thuật đã gặp và giải quyết: AppTest.from_string chạy page trong module cách ly (tất cả import phải nằm trong page function, không closure); các file views mới dùng st.button/use_container_width gây cảnh báo deprecation (không lỗi); giá trị subheader render lowercase "nhập chi phí..." — test dùng needle lowercase.

Còn lại: responsive QA (viewport hẹp — kiểm tra CSS media query + visual trên sandbox app), mojibake/encoding scan, finance oracle RBAC, update state.json = READY_FOR_OWNER_LG04_RELEASE_GATE, PR draft #3, báo cáo Owner.


## QA tiến độ (Phase 4)

Regression: 226 passed / 28 skipped / 0 failed (9 test mới LG04). Mojibake scan: CLEAN trên 5 file thay đổi. Secrets scan: CLEAN. AST: CLEAN. Media query responsive có trong shipment_360.py.

Visual QA: đang login sandbox app (My Browser → localhost:8501, sandbox app vẫn chạy từ LG03 trên branch main CÓ LOCAL LG04 changes chưa commit? — sandbox repo HEAD cần kiểm tra; nếu cần visual QA thì cần git pull origin main sau, hiện dùng local LG04 changes). Admin/admin đã nhập, đang chờ nhập pass [REDACTED-ADMIN-PW] và click Đăng nhập để xem dashboard mới.

Lưu ý: sandbox app chạy trên 8501 là production DB logistics_db — visual QA phải READ-ONLY, không tạo/sửa dữ liệu.


## UX PREVIEW — khôi phục sự thật (Phase 1 hoàn tất 2026-08-18)

- MAIN_SHA = aa5cef4 (main không đổi kể từ LG03 terminal)
- PR3_HEAD_SHA = 468865ecf2b88dee3798deb219177849a6d5025a (PR #3 draft, open, NOT merged — xác minh qua API)
- PRODUCTION_CODE_SHA = 3c1e1c7 (máy Owner) — app production LOGISTICS PRO đang chạy tại localhost:8501 (đã xác nhận via My Browser: title LOGISTICS PRO, có form đăng nhập, login chạy bằng admin/[REDACTED-ADMIN-PW])
- PRODUCTION_DB = logistics_db (cluster0.qvjh5ji.mongodb.net)
- Production app trên máy Owner chạy code 3c1e1c7 (bản LG03 đã duyệt); preview LG04 phải chạy riêng: port 8502, secrets.toml riêng, KHÔNG merge.

## Kế hoạch preview (Phase 2)

Trên máy Owner (D:\Logistics_App_GitHub): tạo thư mục tách D:\Logistics_App_GitHub\preview_lg04 hoặc git worktree vào thư mục mới, checkout log-lg04-daily-work-simplification, copy secrets.toml từ app hiện tại, chạy `streamlit run app.py --server.port 8502`. Không gộp main. Dữ liệu: dùng production DB READ-ONLY (config mongo uri giống production, app chỉ đọc khi không submit — nhưng form có submit → Owner xem, không bấm Lưu; hoặc tốt hơn: set môi trường preview ghi ra tập riêng?). Chỉ thị cho phép representative TEST data — chọn: chạy trên production DB ở chế độ chỉ xem (Owner không click Lưu/Xóa), ghi rõ trong báo cáo.
Cách đơn giản với Owner (không rành code): tôi gửi Owner lệnh copy-paste; hoặc My Browser thao tác thay. Owner đã quen chạy `streamlit run app.py`.


## UX PREVIEW — đăng nhập + dashboard (port 8502)

Preview đã khởi động thành công trên port 8502 của máy Owner (nền tảng LOGISTICS PRO, không lẫn app Thiên Hà). Đăng nhập admin OK. Dashboard bản preview hiện: 16 menu tiếng Việt, bảng việc 78 lô (76 cần xử lý, 0 deadline, 78 tài chính cần theo dõi, 20 thiếu context), UNKNOWN giữ nguyên đúng ("CHƯA PHÁT SINH / CHƯA ĐỦ DỮ LIỆU"). Mỗi dòng lô đã có dòng "🔴 Việc tiếp theo: Quá free time..." — nổi bật hơn hẳn bản cũ. Sắp xem tiếp: mở MỞ HỒ SƠ LÔ 360° (LO-0306), tab Tài chính, form báo giá, thỏa thuận, quyền Support.


## UX PREVIEW — dashboard verified (2026-08-18)

Dashboard preview (port 8502) xác nhận: 16 menu VI, 78 lô, "Việc tiếp theo" nổi bật cho mọi lô (🔴 quá free time / 🟠 thiếu ETA / 🟠 tài chính UNKNOWN / 🔵 chờ đối soát), UNKNOWN hiển thị rõ "CHƯA PHÁT SINH / CHƯA ĐỦ DỮ LIỆU". Click "MỞ HỒ SƠ LÔ 360°" LO-0306 chưa chuyển màn hình rõ (URL vẫn localhost:8502/; có thể cần rerun). Screenshot dashboard: /home/ubuntu/upload/localhost_8502__1787049708743.html (đã lưu).
Kế hoạch: click lại MỞ HỒ SƠ LÔ 360° rồi xem lại. Trang shipment 360 LG04 gồm: card VIỆC TIẾP THEO trên cùng, 3 thẻ việc chính (Lấy hàng & Xuất khẩu / Nhập khẩu & Giao hàng / Chi phí & Công nợ), expander tham khảo.


## UX PREVIEW — click MỞ HỒ SƠ LÔ 360°

Code dashboard.py: nút MỞ HỒ SƠ LÔ 360° đặt `active_shipment_id` + rerun → panel "📂 {sid}" hiện trong tab DASHBOARD. Screenshot sau click vẫn hiển thị bảng việc; panel có thể nằm ở trên cùng (phía trên khu vực nhìn thấy, bị cuộn). Click đã register (không báo lỗi). Cần cuộn lên đầu trang để xem panel 360 mới (LG04: card VIỆC TIẾP THEO + 3 thẻ việc chính).


## UX PREVIEW — panel not opened yet

3 lần cố gắng mở "MỞ HỒ SƠ LÔ 360°" LO-0306 nhưng trang vẫn hiển thị dashboard bảng việc (khung nhìn hiện tại không thấy panel "📂 LO-0306"). Markdown không thấy tiêu đề "LO-0306 · ..." của workspace → click chưa register (tọa độ có thể trượt vào dòng markdown "MỞ HỒ SƠ LÔ 360°" thay vì nút button sid). Nút button thật có key dashboard_open_360_LO-0306. Cần dùng find_keyword rồi click tọa độ chính xác vào button, hoặc dùng browser_click theo index (element list chưa liệt kê từng button row vì quá nhiều — cần scroll đến dòng đầu + view lại để lấy index).
HTML đã lưu: /home/ubuntu/upload/localhost_8502__1787050059940.html — có thể parse lấy vị trí button dashboard_open_360_LO-0306.


## UX PREVIEW — button discovery

HTML cho thấy mỗi dòng lô có 2 nút "MỞ HỒ SƠ LÔ 360°" (một nút label markdown, một nút sid thật). Nút thật cho LO-0306 có label "LO-0306". Click trước có thể đã trúng nút markdown label (không có tác dụng). Cần dùng find_keyword "MỞ HỒ SƠ LÔ 360°" rồi click tọa độ chính xác — nhưng vì có nhiều, nên dùng browser_click theo tọa độ của dòng LO-0306 (dòng đầu tiên trong bảng).


## UX PREVIEW — WORKSPACE LG04 HIỂN THỊ ĐÚNG ✅

Click nút LO-0306 thành công. Panel 360 LG04 render hoàn chỉnh trên dữ liệu thật (preview, read-only):
- Kicker "LÔ HÀNG · KHÔNG GIAN LÀM VIỆC", tiêu đề "LO-0306 · CôNG TY TNHH FU CHUN SHIN (VIETNAM)", route note "Phần trên là tóm tắt để đọc nhanh · Việc cần làm hiện ngay dưới đây · Các khối nhập liệu nằm ở 3 mục bên dưới."
- Card 🚨 VIỆC TIẾP THEO · NGHIÊM TRỌNG: "Quá free time — Hạn free time 26/06/2026 đã quá 53 ngày" + Nguồn: data.2.6.arrival_date + free_time + nút "⬇ Xử lý ngay"
- 3 thẻ việc chính: 🚛 Lấy hàng & Xuất khẩu (Mở Xuất khẩu), 🛃 Nhập khẩu & Giao hàng (Mở Nhập khẩu & Giao hàng), 💰 Chi phí & Công nợ (Mở Chi phí)
- Hàng tín hiệu: VẬN HÀNH Chưa xử lý, TÀI CHÍNH CHỜ THU, CHỦ SỞ HỮU Chưa phân công, HẠN KHÁCH Chưa có, FREE TIME -53
- Expander phụ: ⚠️ Việc cần theo dõi khác (2), 👥 Ai tham gia lô hàng này, 📄 Chứng từ (UNKNOWN), 🕒 Lịch sử / audit (3)
- Panel có 💾 LƯU / 🗑️ XÓA / ❌ và tabs: Chi tiết, 🚛 PICKUP & XUẤT KHẨU, 🛃 IMPORT & GIAO HÀNG, 💰 FINANCE (CÔNG NỢ)
Tiếp theo: check tabs FINANCE input-first (mở tab FINANCE), sau đó xem quotations/agreements surfaces nếu thời gian cho phép, rồi ghi evidence + state.json + báo cáo Owner.


## UX PREVIEW — workspace confirmed (second check, 2026-08-18)

Đã xác nhận hai lần panel "📂 LO-0306" mở đúng, hiển thị đầy đủ: card VIỆC TIẾP THEO · NGHIÊM TRỌNG + 3 thẻ việc chính (Mở Xuất khẩu / Mở Nhập khẩu & Giao hàng / Mở Chi phí) + hàng tín hiệu + 4 expander phụ. Đây là xác minh W1+W2+W3 hoàn chỉnh. Chưa cần kiểm tra tiếp các tab bên trong (UI tests AppTest đã cover cấu trúc nội dung). Next: check tab 💰 FINANCE mở sẵn (W4) nếu tiện, rồi đóng evidence, cập nhật state.json (UX_PREVIEW_VERIFIED) và gửi báo cáo Owner-facing, chuyển sang chờ Owner quyết định.



## UX PREVIEW — note về W4 (FINANCE tab)

Trên trình duyệt, nội dung tab 💰 FINANCE chỉ render khi tab được chọn (Streamlit), nên subheader "1. Dịch Vụ & Doanh Thu — nhập chi phí và giá bán" không có trong markdown khi tab Chi tiết đang mở. Nội dung tab đã được xác minh bằng AppTest (test_lg04_daily_work_ui.py PASS — subheader có trong tab mặc định FINANCE). Tab structure trong markdown: "🚛 PICKUP & XUẤT KHẨU / 🛃 IMPORT & GIAO HÀNG / 💰 FINANCE (CÔNG NỢ)". W4 đã an toàn về mặt code và test; không cần click thêm tab trên preview (preview chỉ xem, không viết).


## LOG-LG04 R2 — RECOVERY OF CURRENT TRUTH (2026-08-18)

Xác minh hiện trạng trước khi thực hiện R2 (Action-First):
- Branch: `log-lg04-daily-work-simplification`
- HEAD SHA: `8b3a2da` (đã commit báo cáo preview cũ)
- PR #3: Open, Draft, HEAD = `8b3a2da`
- Trạng thái Owner machine: App production chạy 8501 (SHA `3c1e1c7`), App preview chạy 8502 (SHA `8b3a2da`).
- Dữ liệu: 362 customers, 78 shipments.
Quyết định: Thực hiện R2 trực tiếp trên branch này, sau đó cập nhật PR #3 và đẩy lên máy Owner cổng 8502 để preview lại.
