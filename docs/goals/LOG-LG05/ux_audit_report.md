# UX AUDIT REPORT — LOGISTICS PRO (CHECKLIST DESIGN)

**Ngày:** 20/08/2026
**App:** LOGISTICS PRO · LOG-C07 · 3.1.3-router-hotfix
**Branch:** `log-lg05-excel-round-trip-gnt` (HEAD: `a8035c9`)
**Phương pháp:** Browser thật (Chromium), read-only, KHÔNG sửa code
**Tác giả:** Manus AI

---

## TỔNG KẾT ĐIỂM

| Hạng mục | Tổng điểm | Điểm tối đa | Tỷ lệ |
|----------|-----------|-------------|-------|
| LOGIN | 7/10 | 10 | 70% |
| DASHBOARD & SHIPMENT LIST | 6/12 | 12 | 50% |
| XỬ LÝ LÔ / EDITABLE FORM | 11/16 | 16 | 69% |
| FINANCE (CÔNG NỢ) | 9/10 | 10 | 90% |
| GETFLY IMPORT | 4/8 | 8 | 50% |
| CUSTOMERS | 4/4 | 4 | 100% |
| **TỔNG** | **41/60** | 60 | **68%** |

---

## FAIL (Score = 0) — 4 FINDINGS

### UX-008: "Vì sao ra số này?" quá dài, chặn toàn bộ dashboard
- **Severity:** P1
- **Mô tả:** Mỗi shipment card hiển thị 7 bullet UNKNOWN trong "Vì sao ra số này?" — tổng 13 cards = 91 bullet. Người dùng phải scroll liên tục để xem danh sách lô hàng.
- **Khuyến nghị:** Collapsed by default, chỉ hiện khi user click. Hoặc thay bằng badge nhỏ "7 UNKNOWN".

### UX-014: Nút XÓA shipment không có confirmation dialog
- **Severity:** P1 — HIGH RISK
- **Mô tả:** Nút "🗑️ XÓA" nằm ngay cạnh "💾 LƯU". Một click nhầm sẽ xóa shipment vĩnh viễn.
- **Khuyến nghị:** BoundingBox confirm dialog ("Bạn có chắc muốn xóa lô này? Hành động không thể hoàn tác.")

### UX-025/UX-026: Đóng inline form gây stuck loading
- **Severity:** P1
- **Mô tả:** Click ❌ để đóng form → trang vào trạng thái "Đang đồng bộ dữ liệu hệ thống..." và BỊ KẸT, không thể tương tác đến khi reload trang.
- **Khuyến nghị:** Cancel action không nên trigger data sync. Hiển thị spinner riêng, timeout rõ ràng.

### UX-028: Login mất ~60 giây
- **Severity:** P1
- **Mô tả:** Sau click "Đăng nhập", trang hiển thị "Đang đồng bộ dữ liệu hệ thống..." và mất ~60 giây để hoàn tất. Người dùng bị block hoàn toàn.
- **Khuyến nghị:** Lazy-load data, chỉ load dashboard sau khi login thành công. Hiển thị progress bar.

---

## PARTIAL (Score = 1) — 11 FINDINGS

| ID | Màn hình | Vấn đề | Khuyến nghị |
|----|----------|--------|-------------|
| UX-003 | Login | Form không centered, lệch trái | Dùng CSS center |
| UX-004 | Login | Form span full width ở 1024px | Max-width 400px |
| UX-005 | Login | Không có spinner rõ ràng khi sync | Thêm st.spinner |
| UX-006 | Dashboard | Cards quá lớn (~300px/card), chỉ thấy 2-3 lô | Compact row ~50px, expand on click |
| UX-007 | Dashboard | Redundant warning ("🔴 13 lô cần xử lý" + "🟠 Việc tiếp theo" lặp lại) | Deduplicate alerts |
| UX-009 | Dashboard | 10+ filter controls trên table | Progressive disclosure |
| UX-010 | Dashboard sidebar | 19 nav items, phải scroll | Collapsible sections |
| UX-011 | Dashboard | Label "Xử lý" vs "Mở thùng nhập liệu" inconsistent | Chọn 1 label duy nhất |
| UX-015 | XỬ LÝ LÔ | Form inline cramped ở 1024px | Better spacing / 2-column layout |
| UX-016 | XỬ LÝ LÔ | Date picker yêu cầu keyboard navigation | Calendar icon click-to-open |
| UX-017 | IMPORT TAB | Form rất dài, phải scroll nhiều | Visual section separators |
| UX-021 | FINANCE | Input fields trực tiếp editable, không validation | Warning khi giá = 0 |

---

## PASS (Score = 2) — 11 FINDINGS

| ID | Màn hình | Điểm tốt |
|----|----------|----------|
| UX-001 | Login | Compact form, 2 fields + 1 button |
| UX-002 | Login | Password show/hide toggle |
| UX-012 | XỬ LÝ LÔ | Direct editable form (no intermediate screen) |
| UX-013 | XỬ LÝ LÔ | 3 tabs correct, default = PICKUP & XUẤT KHẨU |
| UX-018 | IMPORT TAB | COPY NHANH box — rất hữu ích |
| UX-019 | IMPORT TAB | GNT trong đúng tab IMPORT & GIAO HÀNG |
| UX-020 | FINANCE | Comprehensive finance view với bảng kê |
| UX-022 | FINANCE | Gross-up calculator — good utility |
| UX-023 | FINANCE | Payment history entry — simple & functional |
| UX-024 | Dashboard | NHẬP TỪ GETFLY / XUẤT CHO GETFLY prominent, dễ tìm |
| UX-027 | Login | Compact centered form (re-entry) |
| UX-029 | GETFLY IMPORT | Clear upload instructions + format guidance |
| UX-030 | Customers | Clean layout, functional table |
| UX-031 | Customers | Data protection messaging ("Bỏ qua không ghi đè") |

---

## RECOMMENDATIONS (PRIORITY ORDER)

1. **P1 — Fix stuck loading on form close** (UX-025/UX-026): Cancel action should not trigger full data sync.
2. **P1 — Add delete confirmation** (UX-014): One-click delete is too dangerous for financial data.
3. **P1 — Reduce login time** (UX-028): 60 seconds is unacceptable for daily use.
4. **P1 — Collapse "Vì sao ra số này?"** (UX-008): Default collapsed, show count badge.
5. **P2 — Compact shipment rows** (UX-006): 50px rows instead of 300px cards.
6. **P2 — Fix filter overload** (UX-009): Progressive disclosure for filters.

---

## TERMINAL STATE

```
UX_AUDIT_COMPLETE
AWAITING_TRIAGE
```

**Đã hoàn tất audit read-only. KHÔNG có code bị thay đổi. KHÔNG có data bị sửa.**

Owner review các P1 findings để quyết định triage order.
