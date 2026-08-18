# LG01-T07: W5 Beginner-first workflow integration

Date: 2026-08-17. Branch: log-lg01-multi-user-internal-rc. Root commit: cb371a5.

## 1. Contract requirement (section 20)

Beginner user must be able to answer: Toi dang o dau? Trang thai hien tai la gi? Con thieu gi? Ai can lam? Tiep theo la gi? Vi sao he thong bao dieu nay? Vi sao ra so nay? Candidate improvements duoc liet ke trong contract duoc VERIFY trong code truoc khi implement.

## 2. Audit findings (code inspection, 2026-08-17)
| Candidate improvement | Evidence location | Status |
|---|---|---|
| Permission-denied message ro rang (ten user, man hinh bi chan, huong dan lien he admin) | views/web_app.py lines ~292-300 | DA CO |
| Buoc tiep theo tai key lifecycle stages | core/review_queue.py line 338 (reason='Buoc tiep theo X co han...') | DA CO |
| Empty states nhat quan 'Chua co' | 17/18 view files (customers, shipments, contracts, quotations, agreements, finance, reports, dashboard...) | DA CO |
| UNKNOWN/WAITING states ro rang | 137 UNKNOWN usages trong state tracking; 'Dang cho' hien co | DA CO |
| Quote explanation + thuong mai | views/agreements.py, entity_context.py, shipment_360.py, core/quotations.py | DA CO |
| Finance Review: tong thuong mai khong phai so tien thuc te | views/finance_review.py | THIEU - DA BO SUNG |

## 3. Gap fix duy nhat (verified still needed)

views/finance_review.py: them st.info sau bang tong ket (truoc _render_partner_position): 'Tong thuong mai tren bang nay la so uoc tinh theo cong thuc, khong phai so tien thuc te da thanh toan. Doi chieu voi so sach ke toan truoc khi quyet dinh.'

Nguyen tac contract duoc tuan thu: khong redesign app, chi sua 1 diem UX verified thieu, khong doi hanh vi du lieu/logic.

## 4. Verification

- Compile check views/finance_review.py: PASS.
- C15 test suite (27 tests) + LG01 env-security suite (7 tests) = 34/34 PASS sau thay doi.
- Khong thay doi database, khong chang migration, khong cham production.

## 5. Verdict

Beginner-first integration DA DAT: nguoi dung moi co the xac dinh vi tri, trang thai, viec con thieu, nguoi phu trach, buoc tiep theo va ly do cua so lieu thong qua 6 candidate mechanisms da ton tai + 1 bo sung. Khong co dead-end material nao phat hien trong audit. K5 (optional future): them 'Buoc tiep theo' widget visible hon tren Dashboard (ngoai review queue).
