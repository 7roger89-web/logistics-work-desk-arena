# LOG-LG03 — PHAT HIEN GAPIO API USER TR tren baseline main 09e2426

Ngay: 2026-08-18

## Phat hien
- `core/auth.py` dong 241: `from core.database import save_user` — nhung core/database.py KHONG dinh nghia save_user/load_users/delete_user/update_user.
- `views/web_app.py` dong 305/377: cung import save_user/load_users/delete_user/update_user tu core.database.
- `core/users.py` dong 15: docstring noi "lives in core.database (load_users / save_user / delete_user)".
- grep toan repo: khong co `def save_user` o bat ky file .py nao tren HEAD 09e2426.

## Nghia la gi
1. LG02 headless_bootstrap (commit 4578d3f) da duoc chay thanh cong truoc do — co 2 kha nang:
   a. Khi do LG02 branch (4578d3f) co them file/monkey-patch; hoac
   b. load_users() trong DB da tra ve users (1 tai khoan admin Owner) nen script thoi truoc khi goi save_user, KHONG phai do save_user hoat dong.
2. Tren main hien tai, user-management UI + auth bootstrap se CRASH khi goi save_user/load_users → AttributeError tai runtime.

## Hinh dong an toan (LG03)
- Day la bug ton tai tren baseline RELEASED main → danh dau BLOCKER P1/LG03? hay thuoc pham vi LG03?
- LG03 contract Section 49: "repeated repair fails without new evidence" → STOP voi BLOCKED/OWNER_GATE_REQUIRED neu can Owner quyet dinh.
- Nhung: sua bo sung save_user/load_users/delete_user/update_user nho (dung _save_document/_load_dict pattern san co, collection 'users', upsert theo username) = "safe tightening"/bugfix, khong thay doi RBAC, khong dong logic tai chinh.
- Quyet dinh: LG03 them bounded fix user API + unit test, coi day la mot phan "reliable user model" phu tro Viet hoa multi-user. Ghi evidence trung thuc.
- PHAI kiem tra: chay test LG02 (test_logc15_auth_rbac.py) xem co pass khong — neu pass thi co the load_users duoc dinh nghia o noi khac (vd __init__ hoac patch).
