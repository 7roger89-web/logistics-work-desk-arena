# Quy trình làm việc

Đi đúng 5 bước. Chốt phạm vi trước khi thi công; không thêm mục tiêu giữa chừng.

| Bước | Ai làm | Ra cái gì | Cổng |
|---|---|---|---|
| 1. Hỏi cho rõ | Owner nêu mục tiêu; người thực hiện hỏi phần còn thiếu | Mục tiêu, phạm vi, điều cấm, tiêu chí nhận | Owner xác nhận: **mày đọc thấy đúng ý**. Đã rõ trong yêu cầu thì làm, không hỏi lại. |
| 2. Chia nhỏ | Người thực hiện | Các phần nhỏ có đầu ra và cách kiểm tra; một task một nhánh | Mỗi phần kiểm tra được; việc phát sinh tách issue, không nới phạm vi. |
| 3. Thi công | Người thực hiện | Thay đổi đúng phạm vi trên nhánh task | Có bằng chứng cho phần vừa làm; không sửa phần không liên quan. |
| 4. Soát | Người thực hiện kiểm tra; CI chạy tự động; Owner xem diff | Kết quả kiểm tra, diff và PR nháp có bằng chứng | **CI xanh không lỗi mới**; lỗi cũ nằm trong baseline, không thêm regression vào baseline. |
| 5. Ghi lại | Người thực hiện | PR ghi thay đổi, bằng chứng, giới hạn và việc còn lại; cập nhật tài liệu trong phạm vi được phép | **Phiên sau đọc hiểu**: biết đã làm gì, chưa làm gì và bước tiếp theo. Kết luận XONG / CHƯA XONG / HỎNG theo bằng chứng. |

## Khi nào bỏ nghi thức P2P

Giao diện và tài liệu: bỏ chuỗi bootstrap, phân vai, receipt, plan và báo cáo P2P
riêng. Dùng yêu cầu đã rõ, nhánh task, diff và bằng chứng phù hợp; không thêm file
thủ tục chỉ để đủ nghi thức. Vẫn giữ ba cổng trên và mọi giới hạn Owner.

Tiền, chứng từ và danh tính database: giữ nghi thức P2P tương ứng trong phần
managed của AGENTS.md và nguồn portable nếu có. Chốt nguồn luật, phạm vi, quyền,
bằng chứng kiểm tra và cổng Owner trước thao tác có ảnh hưởng. Thiếu nguồn portable
không chặn việc đọc hoặc làm tài liệu; không tự cấp quyền thao tác dữ liệu.
Nếu việc giao diện/tài liệu mở rộng sang các luồng này, áp dụng nghi thức cho phần
có ảnh hưởng và tách issue khi vượt phạm vi.

## Giới hạn hoàn thành

Dùng đúng 5 điều trong [DONE.md](DONE.md). Lời tự khai không tính là bằng chứng.
Không thêm điều kiện thứ sáu vào task. Không xoá nhánh hàng loạt hoặc deploy
chỉ vì quy trình có nhắc đến việc dọn nhánh hay phát hành.
