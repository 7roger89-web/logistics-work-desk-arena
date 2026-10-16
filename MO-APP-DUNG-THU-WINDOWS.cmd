@echo off
rem =====================================================================
rem  LOGI #199 - Trinh mo ban DUNG THU tren Windows (nhap dup de chay).
rem  Chi chay voi DU LIEU MAU trong bo nho tam (Mongomock). Khong dung
rem  du lieu that, khong can tai khoan that, khong sua ung dung that.
rem  Tep nay chi goi lai launcher da co san: scripts\logi199_uat.cmd
rem =====================================================================
chcp 65001 >nul
cd /d "%~dp0"
if not exist scripts\logi199_uat.cmd (
  echo DUNG: Thieu tep scripts\logi199_uat.cmd. Hay giai nen LAI goi ZIP day du.
  pause
  exit /b 1
)
call "%~dp0scripts\logi199_uat.cmd"
