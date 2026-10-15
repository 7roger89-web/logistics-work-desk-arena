# LOGI-199 G3 — Business & Operations Routes

Scope: All business and operational routes in `component/src/App.tsx` verified on real Streamlit staging (`:9501`, isolated mongomock) at `1440×900` (`desktop-*`) and `390×844` (`mobile-*`):
1. `/` (`01-home`) — Tổng Quan Công Việc
2. `/dieu-hanh` (`02-dieu-hanh`) — Điều hành (Operations Control Tower)
3. `/lo-hang` (`03-lo-hang`) — Danh sách Lô Hàng
4. `/lo-hang/:id` (`evidence/logi-199-g2/` & `evidence/logi-199-t6/`) — Journey map-first (`T6-FCL`, `T6-LCL`, `T6-AIR`, `T6-AIR-CONSOLIDATED`, `T6-ROAD-FTL`, `T6-ROAD-LTL`, `LO-0306`)
5. `/tao-lo-moi` (`04-tao-lo-moi`) — Tạo Lô Mới
6. `/khach-hang` (`05-khach-hang`) & `/khach-hang/:id` (`05b-customer-playbook`) — Khách Hàng & Playbook
7. `/ngu-canh-doi-tac` (`06-doi-tac`) — Đại Lý Trường Thành / Ngữ cảnh đối tác
8. `/kinh-doanh-bao-gia` (`07-bao-gia`) — Báo Giá
9. `/hop-dong` (`08-hop-dong`) & `/hop-dong/moi` (`08c-hop-dong-moi`) — Hợp đồng
10. `/tai-chinh/thu-tien` (`09-thu-tien`) & receipt modal (`09b-thu-tien-popup`) — Thu tiền khách / Phải thu
11. `/tai-chinh/doi-soat` (`10-doi-soat`) — Đối soát
12. `/tai-chinh/cong-no-doi-tac` (`11-cong-no-doi-tac`) — Công nợ đối tác / Phải trả
13. `/bao-cao-ceo` (`12-bao-cao-ceo`) — Báo cáo CEO

Machine-verified in `g3_report.json`: `overflowPx = 0`, `tooSmallCount = 0`, `errors = []` across all desktop and mobile captures.
