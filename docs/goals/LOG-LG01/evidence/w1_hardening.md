# LG01-T02: W1 Fail-Closed Environment / Data-Boundary Hardening

Goal: LOG-LG01 Multi-User Internal Release Candidate. Task LG01-T02 (W1).
Branch: log-lg01-multi-user-internal-rc (base 05fa777, C15 root verified).
Date: 2026-08-17.

## 1. Finding (pre-hardening)

core/config.py trước khi sửa: MONGO_DB_NAME có giá trị mặc định là logistics_db, đúng tên database PROD. Nếu secrets.toml thiếu [mongo].database, app sẽ âm thầm kết nối PROD. Không có kiểm tra danh sách database cho phép.
MONGO_URI thiếu chỉ gây lỗi sau (kết nối lazy) thay vì fail tại khởi động.
Risk level: HIGH. Lỗi cấu hình một ký tự có thể chuyển toàn bộ app sang ghi PROD.
## 2. Hardening thuc hien (core/config.py)

Thay doi toi thieu, khong dung logic khac:
a. MONGO_DB_NAME mac dinh rong thay vi logistics_db (khong mac dinh tro PROD).
b. MONGO_ALLOWED_DB_NAMES: danh sach DB duoc phep, mac dinh 
[logistics_workdesk_logc14, logistics_workdesk_LG01_E2E].
c. ENV_IDENTITY: nhan moi truong, mac dinh DEV.
d. _PRODUCTION_DB_NAMES = {logistics_db}: tap chan cung (never allowed).
e. validate_mongo_identity(): raise RuntimeError khi:
- MONGO_URI rong (chua cau hinh),
- MONGO_DB_NAME rong (khong dung mac dinh),
- DB la ten PROD (logistics_db),
- DB khong thuoc MONGO_ALLOWED_DB_NAMES.

## 3. Verification

- C15 test suite sau patch: Ran 27 tests, OK (0 failed).
- Dev identity: ENV_IDENTITY=DEV, DB=logistics_workdesk_logc14, allowed=2. PASS.
- Fail-closed: dat MONGO_DB_NAME=logistics_db qua env, raise RuntimeError. PASS.
- Syntax check core/config.py: OK.

## 4. Production boundary decision

App PROD thuc (D:/Logistics_App_Copy, :8510, logistics_db) KHONG bi sua;
hardening chi ap tren repo dev D:/Logistics_App_GitHub. Branch chi la candidate;
chua merge, chua deploy.

## 5. Residual risk

Neu maintainer ghi logistics_db vao allowed_databases, guard van chan o
_PRODUCTION_DB_NAMES (tach lop). Secret scan T09 kiem tra tiep exposure.
