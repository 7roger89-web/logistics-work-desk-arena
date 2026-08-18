# LOG-LG03 — XAC NHAN LATENT BUG save_user/load_users (cap nhat)

Ngay: 2026-08-18

## Kiem chung
- Import trong core/auth.py va views/web_app.py la LAZY (nam trong ham, khong tai module-level) → import khong fail; test test_logc15_auth_rbac.py chi test validation doc (build_user_document, normalize) KHONG cham persistence → pass 27/0.
- Tren HEAD main 09e2426: khong co `def save_user/load_users/delete_user/update_user` o bat ky noi nao → goi runtime se AttributeError.

## Mau thuan voi thuc te
- Owner dang nhap duoc thanh cong tren production (1 user admin), bootstrap "da tao tai khoan Admin dau tien" da hien thanh cong khi LG02.
- Giai thich hop ly: Owner's local repo MAY da co ban database.py khac (LG02 session da sua database.py nhieu lan; cac lan "restore clean" da loai bo mot commit them user API?) HOAC headless_bootstrap LG02 duoc chay khi LG02 branch con co file database.py voi user API (commit 4578d3f da them? — phai kiem tra 4578d3f:core/database.py co save_user khong).

## Kiem tra tiep
- `git show 4578d3f:core/database.py` co save_user khong?
