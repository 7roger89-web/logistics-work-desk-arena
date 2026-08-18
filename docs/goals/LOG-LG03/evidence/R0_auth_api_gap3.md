# LOG-LG03 — NGUYEN NHAN GOC user API mat (xac nhan)

Ngay: 2026-08-18

## Su that
- Commit 4578d3f (LG02 cutover) CO dinh nghia load_users (1259), save_user (1271), update_user (1290), delete_user (1309) trong core/database.py.
- Commit 0d6ce55 (LG02 hotfix mojibake: quotations.py + database.py message) DA DE LEN database.py = version moi hon 4578d3f (lay tu commit khac) → MAT 4 ham user API.
- Main hien tai 09e2426 ke thua 0d6ce55 → khong con save_user → user-management UI + bootstrap se crash tai runtime.
- Nhung Owner van dang nhap duoc tren production! Kiem tra: Owner's local DB co users collection 1 admin (khai bao truoc do). Owner kich hoat user-management/tao user moi se crash — day la BUG P1 dang ton tai tren main released.

## Quyet dinh LG03 (bounded, an toan)
- Phuc hoi 4 ham user API tu 4578d3f vao database.py hien tai (dung _save_document/_load_dict pattern — verify noi dung 4578d3f).
- Them unit test user persistence (test_users_persistence.py) voi rehearsal DB.
- Khong thay doi RBAC, khong cham finance, khong data mutation production.
- Owner's local file khac voi GitHub la van de cua LG02 moi giai quyet (anh da pull a77c675+; may anh co the van giu database.py cu khong bi anh huong vi git pull ghi de — nhung main GitHub cung mat API roi → anh se gap crash. Sua LG03 se ve may anh qua pull).

## Sau fix
- Kiem tra: `from core.database import save_user, load_users, update_user, delete_user` OK; unit test pass; replay Owner's production shape tren rehearsal DB.
