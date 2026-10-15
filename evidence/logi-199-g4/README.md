# LOGI-199 G4 — Tools & Admin Routes + Global Drawers/Sheets

Scope: All tool, reference, and admin routes in `component/src/App.tsx` plus global drawers/sheets verified on real Streamlit staging (`:9501`, isolated mongomock) at `1440×900` (`desktop-*`) and `390×844` (`mobile-*`):
1. `/tra-cuu-thue` (`01-bieu-thue`) — BIỂU THUẾ (desktop + mobile)
2. `/tra-cuu-chinh-sach` (`02-tra-cuu-chinh-sach`) — Tra cứu chính sách (desktop + mobile)
3. `/so-tay` (`03-so-tay`) — Sổ tay nội bộ (desktop + mobile)
4. `/dich-thuat` (`04-dich-thuat`) — Dịch thuật (desktop + mobile)
5. `/thanh-toan-quoc-te` (`05-thanh-toan-quoc-te`) — Thanh toán quốc tế (desktop + mobile)
6. `/quy-trinh` (`06-quy-trinh`) — Thư viện quy trình phát sinh / Work Modules (desktop + mobile)
7. `/bieu-mau` (`07-bieu-mau`) — Biểu mẫu Office / Docgen Templates (desktop + mobile)
8. `/nguoi-dung` (`08-nguoi-dung`) — Người dùng & Vai trò / User Access (desktop + mobile)
9. Global Notification Drawer (`09-notif-drawer`) — desktop + mobile
10. Global Quick Add Sheet (`10-quick-add-sheet`, `"Thêm mới nhanh"`) — desktop + mobile

Machine-verified in `g4_report.json`: `overflowPx = 0`, `tooSmallCount = 0`, `errors = []` across all desktop and mobile captures.
