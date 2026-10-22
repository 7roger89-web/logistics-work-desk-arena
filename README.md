## OPENER — DÁN VÀO CHAT MỚI

Bạn là Control Tower dự án Logistics Work Desk — repo 7roger89-web/logistics-work-desk-arena, PR #211.
Đọc file này TRƯỚC, rồi làm đúng theo nó trỏ tới — KHÔNG khảo sát lại repo:
https://raw.githubusercontent.com/7roger89-web/logistics-work-desk-arena/refs/pull/211/head/docs/CONTROL-TOWER-HANDOFF.md
Làm đúng block COLD START ở đầu file. Luật cứng: bạn ĐỌC được, KHÔNG ghi được. Mọi SHA/tên nhánh trong tài liệu là MỐC LỊCH SỬ — phải đo lại bằng api.github.com trước khi tin; không đoán, không bịa.
Cuối câu trả lời, in ra 2 phần: (a) đang ở đâu / việc kế tiếp / còn thiếu gì / lệch gì so với thực tế; (b) một khối PACKET dán được để tôi gửi cho Arena.

# Logistics Work Desk

Bàn làm việc logistics cho Support/Sale/Operations: một app Streamlit + component bundle hiển thị hành trình đơn hàng (công đoạn nào xong, công đoạn nào kẹt, việc cần làm là gì) trên dữ liệu shipment thật — không demo, không dữ liệu giả.

## Đọc gì trước — theo đúng thứ tự này

1. `AGENTS.md` — luật chơi khi sửa repo: P2P, hai vòng phát triển, thang chống over-engineering, Owner Gate, handoff, testing, quyền.
2. `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md` — bộ luật P2P đầy đủ (bản portable).
3. `docs/CONTROL-TOWER-HANDOFF.md` — bàn giao ca hiện tại: trạng thái thật, việc đang chờ, nhật ký phiên.

## Trạng thái hiện tại

Trỏ thẳng tới `docs/CONTROL-TOWER-HANDOFF.md` — đó là nguồn sự thật duy nhất cho "đang ở đâu, còn gì, cần Owner quyết gì". Không chép lại vào đây để tránh hai nguồn lệch nhau.
Thứ tự tin khi hai nguồn mâu thuẫn: api.github.com/pulls/211 (state/head.sha/merged — MÁY ĐO) → handoff MỤC 3 → comment PR mới nhất → MỤC 4 → body PR → MỤC 6/archive — chi tiết + bảng STALE_KNOWN ở §"NGUỒN SỰ THẬT & THỨ TỰ TIN" trong `AGENTS.md` và `docs/CONTROL-TOWER-HANDOFF.md`.

## Cách làm việc

- **Arena code** — sửa/thêm trên nhánh arena, kèm test âm + dương, commit + push đúng nhánh đó.
- **Control Tower đọc source kiểm** — không tin báo cáo suông; mở code/diff/test mà kiểm.
- **Owner quyết** — các việc thuộc Owner Gate: ý định sản phẩm, dữ liệu nghiệp vụ thật, xoá dữ liệu, secret, chi tiêu, deploy, phát hành.

CI (`.github/workflows/ci.yml`) chạy trên main: đỏ = hồi quy so với failure baseline đã ghi nhận ngay trong workflow.
