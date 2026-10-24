@echo off
chcp 65001 >nul
title AI Final Project - 1-Click Automated Run (Nhom 08 - TDTU)

echo ===============================================================================
echo        TRUONG DAI HOC TON DUC THANG - KHOA CONG NGHE THONG TIN
echo            DO AN CUOI KY: NHAP MON TRI TUE NHAN TAO (503043)
echo           NHOM 08 ^| GIANG VIEN HUONG DAN: ThS. NGUYEN THANH AN
echo ===============================================================================
echo [INFO] Dang khoi dong che do 1-CLICK RUN kiem thu tu dong toan bo 3 Task...
echo.

:: 1. Kich hoat moi truong ao neu co
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

:: 2. Chay 1-Click Run voi tham so --1click
python main.py --1click

if errorlevel 1 (
    echo.
    echo [THONG BAO] Ung dung da dong hoac xay ra loi.
    pause
)
