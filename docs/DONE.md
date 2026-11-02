# Định nghĩa xong

Chỉ chuyển trạng thái khi có bằng chứng kiểm tra được; mặc định là CHƯA.

| Số | Điều kiện | Đo bằng | Trạng thái |
|---|---|---|---|
| 1 | Sửa thông tin lô mở được, lưu được, đọc lại đúng. | Log hoặc test luồng mở → sửa → lưu → tải lại; đối chiếu giá trị đã lưu. | CHƯA |
| 2 | Tạo lô mới từ đầu tới cuối không lỗi. | Test hoặc bản ghi chạy toàn luồng tạo lô; mở lại lô và đối chiếu dữ liệu. | CHƯA |
| 3 | Sinh được chứng từ FORM_07 có dữ liệu đúng. | File FORM_07 đã sinh và đối chiếu các trường với dữ liệu nguồn. | CHƯA |
| 4 | Viewer không sửa được tiền, có thông báo rõ. | Test hoặc ảnh/log phiên viewer thử sửa tiền: bị chặn, có thông báo, dữ liệu không đổi. | CHƯA |
| 5 | Không lỗi mới trong CI. | Kết quả CI của đúng commit: so baseline không có node lỗi mới và các kiểm tra bắt buộc xanh. | CHƯA |

Điều 6 trở đi: đóng issue, không làm.
