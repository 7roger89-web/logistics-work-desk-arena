# CẶP VÍ DỤ
## XẤU (UI)
Mục tiêu: làm bình luận mượt hơn. Vị trí: component comment. Nghiệm thu: chạy tốt.
## TỐT (UI)
Mục tiêu: gõ bình luận và gửi được ngay trong node đang mở, không rời màn hình.
Vị trí: tự tìm component render node, báo file:dòng trước khi sửa.
Hợp đồng: textarea max 500, nút Gửi disable khi rỗng, chèn ngay dưới node.
Non-goals: không sửa form đầu trang.
Nghiệm thu: form nằm trong card; gửi xong hiện ngay, không reload; 501 ký tự disable.
Lệnh: pytest tests/<file> -q
MUST NOT: mở form ở đầu trang dù dữ liệu vẫn lưu đúng.
Phép thử: xoá hẳn form đầu trang, luồng vẫn chạy.
## XẤU (backend)
Mục tiêu: sửa validate. Nghiệm thu: validate đúng.
## TỐT (backend)
Mục tiêu: POST /api/x thiếu `code` trả 422, không tạo bản ghi.
Hợp đồng: 422 body {"error":"code_required"}
Nghiệm thu: thiếu code / code rỗng / code hợp lệ
Lệnh: pytest tests/<file> -q
MUST NOT: trả 200 rồi ghi code=None
Phép thử: assert số bản ghi không tăng
