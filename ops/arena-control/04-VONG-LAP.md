# VÒNG LẶP
Việc mới = chat mới = reset 05-TRANG-THAI.md.
Người dùng gõ "tiếp tục đi" = đọc 05 + 06, làm tiếp từ dòng cuối.
Người dùng dán "KẾT QUẢ ARENA:" = phân loại, rồi ra prompt tiếp.

## Phân loại
| Loại | Dấu hiệu | Xử lý |
| HIỂU_SAI_Ý | đúng chữ, sai trải nghiệm | sửa prompt, không sửa code |
| THIẾU_HỢP_ĐỒNG | lặp đúng một chỗ | thêm chữ ký/schema |
| QUÁ_RỘNG | lỗi lan file khác | cắt lát, thêm non-goals |
| THIẾU_PHỤ_THUỘC | gọi thứ không có | dán chữ ký thật |
| TRÀN_CONTEXT | quên ràng buộc | chat mới, prompt ngắn hơn |

Cùng loại 2 lần: đổi cách. Ba loại khác nhau liên tiếp: nói người dùng bằng
tiếng thường là nên dừng, đề xuất đổi hướng.

## Mức bằng chứng
PROVEN: có lệnh đã chạy + output khớp nghiệm thu + đường dẫn evidence.
Test xanh nhưng chưa nhìn màn hình thật: INCOMPLETE.
Tự khai suông: INCOMPLETE.

## Dừng và báo
Repo mâu thuẫn yêu cầu · cần quyền chưa có · chạm quá 5 file · cần dữ liệu
production · ba loại lỗi liên tiếp.
