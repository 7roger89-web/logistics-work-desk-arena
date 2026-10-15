@echo off
setlocal
cd /d "%~dp0\.."
if exist .streamlit\secrets.toml (
  echo STOP: Khong dung thu muc co secrets production. Hay giai nen ZIP vao thu muc moi.
  pause
  exit /b 1
)
set "MONGO_URI="
set "MONGO_DB_NAME="
set "AUTH_REQUIRED=false"
set "STREAMLIT_BROWSER_GATHER_USAGE_STATS=false"
python --version >nul 2>&1
if errorlevel 1 (
  echo Can Python 3.11+ tren may. Khong thay doi app production.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt pytest
if errorlevel 1 (
  echo Chua cai duoc thu vien. Giu cua so nay de nguoi ho tro xem loi.
  pause
  exit /b 1
)
echo Mo http://localhost:9501 - du lieu mau, khong production. Ctrl+C de tat.
.venv\Scripts\python.exe -m streamlit run scripts/logi199_t6_staging_app.py --server.port 9501 --server.address 127.0.0.1 --server.headless true
pause
