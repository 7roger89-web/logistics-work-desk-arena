# LOGI-199 G3 — Business & Operations Routes

Scope: Business and operational routes in `component/src/App.tsx` verified on real Streamlit staging (`:9501`, isolated mongomock) at `1440×900` (`desktop-*`) and `390×844` (`mobile-*`):
1. `/` (`01-home`) — Tổng Quan Công Việc (desktop + mobile)
2. `/dieu-hanh` (`02-dieu-hanh`) — Điều hành / Operations Control Tower (desktop + mobile)
3. `/lo-hang` (`03-lo-hang`) — Danh sách Lô Hàng (desktop + mobile)
4. `/lo-hang/:id` (`evidence/logi-199-g2/` & `evidence/logi-199-t6/`) — Journey map-first (`T6-FCL`, `T6-LCL`, `T6-AIR`, `T6-AIR-CONSOLIDATED`, `T6-ROAD-FTL`, `T6-ROAD-LTL`, `LO-0306`) (desktop + mobile)
5. `/tao-lo-moi` (`04-tao-lo-moi`) — Tạo Lô Mới (desktop + mobile)
6. `/khach-hang` (`05-khach-hang`) & `/khach-hang/:id` (`05b-customer-playbook`) — Khách Hàng & Customer Playbook (desktop + mobile)
7. `/ngu-canh-doi-tac` (`06-doi-tac`) — Đại Lý Trường Thành / Ngữ cảnh đối tác (desktop + mobile)
8. `/kinh-doanh-bao-gia` (`07-bao-gia`) — Báo Giá (desktop + mobile)
9. `/hop-dong` (`08-hop-dong`), `/hop-dong/:id` (`08b-hop-dong-chi-tiet`), & `/hop-dong/moi` (`08c-hop-dong-moi`) — Hợp đồng, Chi tiết hợp đồng (`HDMB-0306`), Tạo hợp đồng mới (desktop + mobile)
10. `/tai-chinh/thu-tien` (`09-thu-tien`) & receipt modal (`09b-thu-tien-popup`) — Thu tiền khách / Phải thu & popup Ghi nhận khoản thu (desktop + mobile)
11. `/tai-chinh/doi-soat` (`10-doi-soat`) — Đối soát (desktop + mobile)
12. `/tai-chinh/cong-no-doi-tac` (`11-cong-no-doi-tac`) — Công nợ đối tác / Phải trả (desktop + mobile; `11b-cong-no-popup` ghi nhận `NOT_RUN` trong `g3_report.json` vì fixture staging có `0 dòng` công nợ đối tác đã xác nhận theo đúng quy tắc `UNKNOWN != 0`, nên nút `Trả đối tác` không hiển thị)
13. `/bao-cao-ceo` (`12-bao-cao-ceo`) — Báo cáo CEO (desktop + mobile)

Machine-verified in `g3_report.json`: `overflowPx = 0`, `tooSmallCount = 0`, `errors = []` across all captured desktop and mobile screens.
