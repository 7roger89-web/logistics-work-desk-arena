# Logistics Work Desk

Bàn làm việc logistics cho Support/Sale/Operations: một app Streamlit + component bundle hiển thị hành trình đơn hàng (công đoạn nào xong, công đoạn nào kẹt, việc cần làm là gì) trên dữ liệu shipment thật — không demo, không dữ liệu giả.

## Đọc gì trước — theo đúng thứ tự này

1. `AGENTS.md` — luật chơi khi sửa repo: P2P, hai vòng phát triển, thang chống over-engineering, Owner Gate, handoff, testing, quyền.
2. `.p2p/portable/P2P-OPERATIONS-NOTEBOOK.md` — bộ luật P2P đầy đủ (bản portable).
3. `docs/CONTROL-TOWER-HANDOFF.md` — bàn giao ca hiện tại: trạng thái thật, việc đang chờ, nhật ký phiên.

## Trạng thái hiện tại

Trỏ thẳng tới `docs/CONTROL-TOWER-HANDOFF.md` — đó là nguồn sự thật duy nhất cho "đang ở đâu, còn gì, cần Owner quyết gì". Không chép lại vào đây để tránh hai nguồn lệch nhau.

## Cách làm việc

- **Arena code** — sửa/thêm trên nhánh arena, kèm test âm + dương, commit + push đúng nhánh đó.
- **Control Tower đọc source kiểm** — không tin báo cáo suông; mở code/diff/test mà kiểm.
- **Owner quyết** — các việc thuộc Owner Gate: ý định sản phẩm, dữ liệu nghiệp vụ thật, xoá dữ liệu, secret, chi tiêu, deploy, phát hành.

CI (`.github/workflows/ci.yml`) chạy trên main: đỏ = hồi quy so với failure baseline đã ghi nhận ngay trong workflow.
