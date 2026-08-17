# LG01-T03: W1a Dev/Prod App + Data Boundary Evidence

Goal: LOG-LG01. Task LG01-T03 (W1a). Branch log-lg01-multi-user-internal-rc.
Date: 2026-08-17.

## 1. Bien app DEV (duoc xac nhan truoc tiep)

- Thu muc code: D:/Logistics_App_GitHub (repo git 7roger89-web/logistics-work-desk).
- Port: :8501 (streamlit dev).
- DB: logistics_workdesk_logc14 (secrets.toml [mongo].uri, gitignored).
- Moi truong LG01: logistics_workdesk_LG01_E2E (E2E tests, chua co du lieu).
- ENV_IDENTITY = DEV (mac dinh moi core/config.py sau T02).

## 2. Bien app PROD (legacy, KHONG duoc dung/anh huong)

- Thu muc code: D:/Logistics_App_Copy (copy legacy, khong phai repo git).
- Port: :8510 (streamlit live).
- DB: logistics_db (cluster0.qvjh5ji.mongodb.net) — PRODUCTION duy nhat.

## 3. Chung cu tach bien

- Repo git dev va thu muc copy PROD la 2 thu muc vat ly rieng; dev chi tren branch, khong deploy.
- Secrets dev (secrets.toml) gitignored; khong ton tai trong git.
- Sau T02: core/config.py raise RuntimeError neu dat DB = logistics_db (PRODUCTION) o moi truong dev.
- MONGO_ALLOWED_DB_NAMES chi cho phep: logistics_workdesk_logc14 + logistics_workdesk_LG01_E2E.

## 4. Xac thuc (2026-08-17, may chu Owner)

- Port :8501: streamlit app dev dang chay tu D:/Logistics_App_GitHub, khong ghi vao PROD.
- secrets.toml [mongo].uri -> logistics_workdesk_logc14 (kieu tra ket noi thanh cong).
- validate_mongo_identity() PASS voi dev DB; FAIL dung (RuntimeError) voi logistics_db.

## 5. Ket luan

Bien DEV/PROD ro rang, unambiguous. App dev khong the ket noi PROD bang cau hinh mac dinh.
