# Logistics Pro UI/UX Design Specifications (P2P Standard)

Dựa trên phản hồi của Owner về việc thiếu tương phản màu sắc (không nhìn rõ chữ/icon trên nền nút bấm), chúng tôi áp dụng bộ tiêu chuẩn thiết kế **P2P Visual Suite** để tối ưu hóa giao diện.

## 1. Bảng màu (Color Palette) - Tối ưu tương phản

Chúng tôi thay thế màu Navy quá tối (`#0F2C59`) bằng bộ màu hiện đại, chuyên nghiệp và có độ tương phản cao (WCAG 2.1 compliant).

| Thành phần | Màu cũ | Màu mới (P2P Proposed) | Lý do |
|---|---|---|---|
| **Primary Color** | `#0F2C59` (Navy tối) | **`#1E40AF`** (Blue 800) | Tăng độ sáng để icon/text trắng nổi bật hơn, giữ tính chuyên nghiệp của ngành Logistics. |
| **Sidebar Background** | `#0F2C59` | **`#0F172A`** (Slate 900) | Màu Slate sâu hơn, tạo cảm giác hiện đại và cao cấp. |
| **Active Nav Item** | `#E8F1F7` | **`#3B82F6`** (Blue 500) | Tăng tính nhận diện cho mục đang chọn. |
| **Text (on Primary)** | White | **`#FFFFFF`** | Giữ trắng tinh khiết. |
| **Secondary Background**| `#FFFFFF` | **`#F8FAFC`** | Màu nền nhẹ nhàng, giảm mỏi mắt. |

## 2. Cải thiện Nút bấm (Button Refinement)

Lỗi nghiêm trọng nhất hiện nay là các selector CSS cục bộ (Local Overrides) đang ghi đè màu chữ của nút bấm Primary, dẫn đến tình trạng "chữ tối trên nền tối".

### 2.1. Loại bỏ Overrides xung đột
- Xóa bỏ selector `div[data-testid="stVerticalBlock"] button` trong `dashboard.py` vì nó áp đặt màu chữ tối cho mọi nút bấm, kể cả nút Primary.

### 2.2. Chuẩn hóa Primary Button (P2P Standard)
- **Màu nền:** `#1E40AF` (Blue 800).
- **Màu chữ:** `#FFFFFF` (White) - Bắt buộc dùng `!important` để chống ghi đè.
- **Hiệu ứng Icon:** Thêm `filter: drop-shadow(0 1px 1px rgba(0,0,0,0.3))` cho các emoji icon để tăng độ nổi khối.
- **Độ bo góc:** `8px` để tạo cảm giác hiện đại.

### 2.3. Secondary Button
- **Màu nền:** `#FFFFFF`.
- **Màu chữ:** `#1E293B` (Slate 800).
- **Viền:** `1px solid #CBD5E1`.
- **Hover:** Nền `#F1F5F9`.

## 3. Sidebar & Navigation

- **Group Headers:** Sử dụng màu `#94A3B8` (Slate 400) và font-weight 700 để phân đoạn rõ ràng.
- **Icons:** Sử dụng các icon có độ tương phản cao với nền tối.

## 4. Kế hoạch triển khai (Implementation)

1. Cập nhật `.streamlit/config.toml` với `primaryColor` mới.
2. Cập nhật `views/web_app.py` phần `_configure_page()` để tiêm CSS mới.
3. Rà soát các nút bấm "Lưu" để đảm bảo hiển thị rõ ràng trên mọi màn hình.
