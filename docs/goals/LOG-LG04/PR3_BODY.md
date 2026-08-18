# LG04 — Đơn giản hóa công việc hàng ngày & ưu tiên nhập liệu

## Bối cảnh

Owner phản hồi thực tế (file `Trải nghiệm app.docx`): màn hình lô hàng lộn xộn, việc quan trọng không nổi bật, tab Tài chính chỉ hiện số tổng hợp mà không cho nhập ngay, form báo giá nhiều trường không kẻ khung, luồng Báo giá → Thỏa thuận → Bàn giao khó hiểu.

## Thay đổi

| File | Thay đổi |
|---|---|
| `core/next_action_card.py` (mới) | Card "VIỆC TIẾP THEO" với viền 3px theo mức nghiêm trọng + nút "Xử lý ngay" nhảy thẳng đến khối việc |
| `views/shipment_360.py` | Viết lại không gian lô hàng: card việc tiếp theo trên cùng → 3 thẻ việc chính (🚛 Lấy hàng & Xuất khẩu / 🛃 Nhập khẩu & Giao hàng / 💰 Chi phí & Công nợ) → khối tham khảo thu gọn vào expander; ẩn khối kỹ thuật khi chưa có dữ liệu |
| `views/shipment.py` | Neo nhảy (anchor) đến khối việc chính; tab Tài chính mở ở phần nhập liệu khi chọn "Mở Chi phí"; giữ UNKNOWN != ZERO |
| `views/quotations.py` | Mỗi dòng dịch vụ kẻ khung riêng; cài đặt nâng cao gom vào expander, chỉ còn các trường thiết yếu trên màn hình |
| `views/agreements.py` | Hành trình 4 bước (Báo giá → Thỏa thuận → Bàn giao → Lô hàng) giải thích bằng tiếng Việt thường; nhãn "chi tiết bàn giao" → "Tóm tắt bàn giao (đã khóa)" |

## An toàn

- Chỉ đọc production DB trong suốt quá trình; không tạo/sửa dữ liệu thật.
- Regression: **226 passed / 28 skipped / 0 failed** (thêm 9 test UI mới LG04).
- Mojibake/encoding/secrets scan: CLEAN.
- RBAC + finance mutation oracles: 50 test PASS.
- Không đổi cấu trúc dữ liệu, không đổi quyền.

## Trạng thái

- Draft theo quy trình Owner gate: **không merge** cho đến khi Owner duyệt.
- Dừng tại `READY_FOR_OWNER_LG04_RELEASE_GATE`.
- LOG-LG05: chưa bắt đầu.
