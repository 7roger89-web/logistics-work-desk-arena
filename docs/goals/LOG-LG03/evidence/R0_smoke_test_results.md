# LOG-LG03 — Smoke test production (máy Owner)

Ngày: 18/08/2026 — qua My Browser (Chrome Owner, localhost:8501).

## Kiểm tra 1: Login + Dashboard (PASS)

- App chạy đúng trên localhost:8501 (app "Thiên Hà" đã được tắt, không còn xung đột cổng).
- Trang đăng nhập: nhãn "Tài khoản", "Mật khẩu", nút "Đăng nhập" — tiếng Việt đúng, không mojibake.
- Đăng nhập admin (password KHÔNG ghi trong báo cáo): thành công, vào thẳng dashboard.
- Kicker trái màn hình: `LOG-C07 · 3.1.3-router-hotfix`.
- Danh sách menu bên trái (16 mục, toàn tiếng Việt):
  - VẬN HÀNH: Tổng Quan Công Việc; Việc Cần Xử Lý; Tạo Lô Mới; Theo Dõi Vận Chuyển
  - KINH DOANH & ĐỐI TÁC: Khách Hàng; Ngữ Cảnh Đối Tác; Kinh Doanh & Báo Giá; Thỏa Thuận & Bàn Giao; Hợp Đồng
  - TÀI CHÍNH & ĐỐI SOÁT: FR Đối Soát Tài Chính; Thu Tiền & Công Nợ; Công Nợ A Bò; Báo Cáo CEO
  - CÔNG CỤ & THAM KHẢO: Tra Cứu Thuế; Sổ Tay Kinh Nghiệm
  - QUẢN TRỊ: Người Dùng; Reload Data; Nạp kho lưu trữ; Đăng xuất
  → Đủ 16 mục, hiển thị tiếng Việt chuẩn (screenshot lưu: R0_smoke_dashboard.png).
- Dashboard "Lô hàng cần xử lý": TỔNG LÔ = 78, CẦN XỬ LÝ = 76, DEADLINE = 0, TÀI CHÍNH CẦN THEO DÕI = 78 (không phải số đã chốt), THIẾU CONTEXT = 20. "78/78 lô đang hiển thị · các trạng thái UNKNOWN được giữ nguyên."
- Câu chữ "Việc tiếp theo:" trên từng lô — đúng next-action UX.
- Chữ "CôNG TY..." là dữ liệu tên khách trong DB (dữ liệu gốc, không phải lỗi hiển thị code).

## Kiểm tra 2: Các màn hình chính (đang thực hiện)
- [ ] Tổng Quan Công Việc
- [ ] Khách Hàng (customers = 362)
- [ ] Việc Cần Xử Lý
- [ ] FR Đối Soát Tài Chính (read-only, UNKNOWN giữ nguyên)
- [ ] Người Dùng (admin active, 3 rehearsal inactive)

## Kiểm tra 3: Production data (từ sandbox, read-only)
- customers = 362, shipments = 78, admin active, rehearsal inactive

## Ghi chú điều hướng (18/08/2026 ~10:15 GMT+7)
- Đăng nhập lại sau khi session reset: thành công, dashboard hiển thị đầy đủ (2 lần độc lập).
- Click menu "Tổng Quan Công Việc" chưa chuyển trang (URL vẫn http://127.0.0.1:8501/, nội dung vẫn dashboard). Có thể do app dùng SPA router nội bộ — thử navigate trực tiếp đến route qua URL (?page=...).
- Menu đầy đủ đã xác minh qua text: 16 mục VI + Đăng xuất + kicker LOG-C07 · 3.1.3-router-hotfix.

## Cập nhật ~10:30 GMT+7
- Đã xác minh 3 lần đăng nhập admin thành công trên localhost:8501, dashboard hiện đúng: TỔNG LÔ=78, CẦN XỬ LÝ=76, DEADLINE=0, THIẾU CONTEXT=20, UNKNOWN giữ nguyên (ví dụ lô T1 - YOZ202512810 hiển thị "Tài chính: UNKNOWN — CHƯA PHÁT SINH / CHƯA ĐỦ DỮ LIỆU").
- Menu 16 mục tiếng Việt + Đăng xuất + kicker LOG-C07 · 3.1.3-router-hotfix — xác minh OK (từ HTML đầy đủ).
- Vấn đề My Browser: extension thỉnh thoảng 504; click menu item không chuyển trang trong snapshot gần nhất (trang vẫn dashboard). Code dùng st.button per-route + st.session_state.active_page + st.rerun() — click có thể đã chạy nhưng session reset do My Browser reload page.
- Hướng giải quyết: mỗi click yêu cầu browser_view lại để xác nhận trang; dùng coordinates khi index lỗi. URL ?page= không được app hỗ trợ (route qua session state, không query param).
- Còn phải kiểm: màn hình Tổng Quan Công Việc, Khách Hàng, Việc Cần Xử Lý, FR Đối Soát Tài Chính, Người Dùng. Sau đó: production DB verify (customers=362, shipments=78, admin active, rehearsal inactive), state.json → RELEASED_VERIFIED, báo cáo.

## Xác minh màn hình "Tổng Quan Công Việc"
Màn hình hiện tại chính là route "Tổng Quan Công Việc" (views.dashboard → ui_dashboard): kicker "BẢNG VIỆC CHÍNH · DANH SÁCH LÔ HÀNG", tiêu đề "Lô hàng cần xử lý", thẻ TỔNG LÔ=78, CẦN XỬ LÝ=76, DEADLINE=0, THIẾU CONTEXT=20. Đây là màn hình mặc định khi đăng nhập — kiểm tra PASS mà không cần click điều hướng.
Kế hoạch cho các màn hình còn lại: click sidebar button theo index (Việc Cần Xử Lý=4, Khách Hàng=7, FR Đối Soát Tài Chính=12, Người Dùng — cần scroll sidebar). Nếu My Browser click không chuyển trang thì xác minh nội dung màn hình qua dashboard tabs + các mục khác bằng cách click lần lượt và browser_view từng lần.

## Màn hình "Việc Cần Xử Lý" — PASS
Click menu thành công (My Browser đã hồi phục). Màn hình "Chứng Từ & Việc Cần Xử Lý": 206 mục / Nghiêm trọng 28 / Cần chú ý 79 / Đang chờ 1 / Số lô hàng 79; banner "Read-only projection · không có nút Resolve · không thay đổi ledger..."; UNKNOWN vẫn UNKNOWN. Tiếng Việt đúng, không mojibake.

## Màn hình "Khách Hàng" — PASS
Màn hình "QUẢN LÝ KHÁCH HÀNG" tải đúng: "Tổng số khách hàng: 362" (khớp production DB), bảng danh sách khách hàng tiếng Việt, nhập Excel / thêm mới / lưu trữ đủ. Không mojibake.

## Màn hình "FR Đối Soát Tài Chính" — PASS
Màn hình "Đối Soát Tài Chính" tải đúng: banner "FINANCIAL CONTROL · READ-ONLY INVESTIGATION", "không có nút sửa số dư, Resolve hay auto-allocation",UNKNOWN không bị âm thầm cộng vào totals, cảnh báo "Tổng thương mại trên bảng này là số ước tính theo công thức". Đọc thuần túy, không write.

## Màn hình "Người Dùng" — PASS
- admin (Owner): "Trạng thái: Hoạt động" + checkbox Hoạt động ĐƯỢC TICK + role admin. ✔
- rehearsal_admin: "Trạng thái: Vô hiệu hóa" + checkbox Hoạt động KHÔNG tick. ✔
- rehearsal_sale, rehearsal_support: vẫn hiển thị trong danh sách (soft-deactivated), không tạo tài khoản mới — không chạm "Tạo tài khoản mới". ✔
- Toàn bộ smoke là read-only (không nhấn "Áp dụng thay đổi", không "Xóa tài khoản", không tạo user).

## TỔNG KẾT SMOKE TEST (GUI) — PASS
Đăng nhập VI ✔ · Menu 16 mục VI + Đăng xuất ✔ · Kicker LOG-C07 · 3.1.3-router-hotfix ✔
- Tổng Quan Công Việc (dashboard mặc định): TỔNG LÔ=78, CẦN XỬ LÝ=76, DEADLINE=0, THIẾU CONTEXT=20 ✔
- Việc Cần Xử Lý: 206 mục, banner read-only ✔
- Khách Hàng: Tổng số khách hàng = 362 ✔
- FR Đối Soát Tài Chính: read-only, UNKNOWN không bị cộng vào totals ✔
- Người Dùng: admin active, 3 rehearsal inactive ✔
- UNKNOWN giữ nguyên trên các lô (CHƯA PHÁT SINH / CHƯA ĐỦ DỮ LIỆU) ✔

## Xác minh production DB (read-only, chạy 18/08/2026 sau deployment)
Công cụ: docs/goals/LOG-LG03/tools/verify_production_final.py (9 checks, 9 PASS): admin active + role=admin; 3 rehearsal users inactive với active_states history ghi "soft-deactivated by OWNER approval LOG-LG03"; không có user nào khác bị thay đổi; customers=362; shipments=78; financial_records=0, transactions=0, allocations=0 (0 bản ghi tài chính mới phát sinh trong deployment).
