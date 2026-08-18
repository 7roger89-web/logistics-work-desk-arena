# LG01-T05: W3 Multi-User Write Safety Audit

Branch: log-lg01-multi-user-internal-rc. Date: 2026-08-17.

## 1. Scope
Audit toan bo cac diem ghi (mutation) cua app: shipment, customer, quotation, contract, finance, task, knowledge, user, entrustment, proxy payment.

## 2. Finding chinh
core/database.py co ham _actor() (dong 69): doc username tu session state (current_user), fallback la 'system' (KHONG bao gio la admin). Mot ai ghi mot record deu co created_by/updated_by/deleted_by ghi nhan.

## 3. Bang audit layer database (core/database.py)
Tat ca 20 diem ghi truong *_by deu co actor attribution: 11 diem dung 'actor or _actor()' (cac ham tai chinh/shipment co tham so actor tuong minh), 9 diem con lai goi truc tiep _actor().
20/20 mutation by-fields duoc ghi nhan nguoi thuc hien. Khong co mutation nao thieu attribution.

## 4. Bang audit layer views (48 call sites)
Scan 48 loi goi ham save_/update_/delete_ trong views/*.py: tat ca duoc database layer quy dinh attribution tu dong qua _actor() (doc session state), khong yeu cau views truyen actor thu cong. Thiet ke an toan: actor attribution o bien gioi persitence, khong phu thuoc tung view.

## 5. Kiem soat dong thoi (concurrency)
Cac ham ghi tai chinh trong database.py dung: version optimistic locking (version_filter trong update_one, ConcurrentUpdateError khi version khop), idempotency request qua collection financial_action_requests (fingerprint), va reversal trail (reversed_by_actor, correction record). Hai nguoi dung ghi cung luc tren cung ban ghi tai chinh se co 1 nguoi nhan loi conflict, khong mat du lieu.

## 6. Ket luan
Khong tim thay gap material ve write safety. Moi write deu co attribution (actor or system), moi write tai chinh co version lock + idempotency. Khong can hardening them. Khuyen nghi (khong block): K4 - xem xet them updated_by cho ham delete_shipment/delete_customer (hiện tai chi co deleted_by).

## 7. Residual
_actor() fallback 'system' khi khong co session — da bi ngan tai lop auth (require_login trong main app) truoc khi den lop ghi, nhat la sau LG01-T02/T04 (AUTH_REQUIRED bat buoc).
