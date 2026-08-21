# LOG-LG07 — BÁO CÁO HOÀN THÀNH: DEPLOY APP LÊN STREAMLIT CLOUD

## Kết quả: THÀNH CÔNG

App **LOGISTICS PRO** đã được deploy thành công lên Streamlit Community Cloud và sẵn sàng cho team sử dụng từ bất kỳ máy nào có internet.

---

## Thông tin truy cập

| Mục | Giá trị |
|-----|---------|
| **Link app** | https://tienthanhlog.streamlit.app/ |
| **Kho code** | 7roger89-web/logistics-work-desk (branch: main) |
| **File chính** | web_app.py |
| **Chế độ chia sẻ** | Public (ai có link cũng truy cập được) |

## Tài khoản team

| Tên đăng nhập | Vai trò | Mật khẩu | Quyền hạn |
|--------------|---------|----------|-----------|
| admin | Admin (chủ) | [REDACTED-ADMIN-PW] | Toàn quyền, quản lý tài khoản |
| 7roger | Admin | [REDACTED-ADMIN-PW] | Toàn quyền, quản lý tài khoản |
| sami | Sale | [REDACTED-SAMI-PW] | Tạo lô, xử lý lô, báo giá, khách hàng |
| fiona | Support | [REDACTED-FIONA-PW] | Xem lô, theo dõi vận chuyển, tra cứu |

## Các chức năng đã kiểm tra trên cloud (tất cả PASS)

1. **Đăng nhập** — cả 4 tài khoản đăng nhập thành công
2. **Dashboard** — hiển thị đúng 13 lô cần xử lý, 362 khách hàng, 91 lô
3. **Form lô hàng** — 1 click "Xử lý" → mở form 3 tab (PICKUP & XUẤT KHẨU, IMPORT & GIAO HÀNG, FINANCE)
4. **NHẬP TỪ GETFLY** — giao diện upload file Excel hoạt động
5. **XUẤT CHO GETFLY** — nút xuất hiện và hoạt động
6. **GNT** — nằm đúng trong tab IMPORT & GIAO HÀNG
7. **RBAC (phân quyền)** — sale không thấy mục tài chính/admin; support thấy ít menu hơn; admin thấy tất cả

## Vấn đề đã xử lý trong quá trình deploy

1. **Timeout kết nối DB** — Streamlit Cloud cần timeout dài hơn (30s thay vì 5s) do DNS giải quyết chậm hơn. Đã fix trong `core/database.py` và push lên main.
2. **Mật khẩu hash sai** — ban đầu tài khoản team được tạo với hash format sai. Đã fix bằng cách re-hash với hàm đúng của app (`hash_password()`).
3. **Secrets** — Owner đã cấu hình secrets đúng trên Streamlit Cloud dashboard.

## Lưu ý khi sử dụng

- **Đăng nhập lần đầu** có thể mất 30-60 giây (do kết nối đến MongoDB Atlas từ cloud server). Sau khi đăng nhập xong, app chạy nhanh bình thường.
- **Mật khẩu** của sami và fiona có thể đổi trong mục "Người Dùng" (chỉ admin).
- **App tự động cập nhật** khi có commit mới trên branch main — không cần làm gì thêm.

## Rollback plan (nếu cần)

Nếu app trên cloud bị lỗi, Owner có thể:
1. Vào Streamlit Cloud dashboard → app "logistics-work-desk" → nhấn 3 chấm → chọn "Edit secrets" để sửa config
2. Hoặc quay lại dùng app local trên máy (localhost:8501) nếu server local vẫn chạy
3. DB không bị ảnh hưởng bởi bất kỳ thay đổi nào trên cloud — dữ liệu an toàn

---
*LOG-LG07 hoàn thành ngày 20/08/2026*
