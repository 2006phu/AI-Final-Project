@echo off
chcp 65001 >nul
title AI Final Project - Master Dashboard (Nhom 08 - TDTU)

echo ===============================================================================
echo        TRUONG DAI HOC TON DUC THANG - KHOA CONG NGHE THONG TIN
echo            DO AN CUOI KY: NHAP MON TRI TUE NHAN TAO (503043)
echo           NHOM 08 ^| GIANG VIEN HUONG DAN: ThS. NGUYEN THANH AN
echo ===============================================================================
echo.

:: 1. Kiem tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [LOI] Khong tim thay Python! Vui long cai dat Python 3.10 tro len va them vao PATH.
    pause
    exit /b 1
)

:: 2. Kich hoat moi truong ao neu co
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Dang kich hoat moi truong ao .venv...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [INFO] Dang kich hoat moi truong ao venv...
    call venv\Scripts\activate.bat
)

:: 3. Kiem tra thu vien co ban (pygame-ce)
python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo [THONG BAO] Phat hien thieu thu vien, dang tu dong cai dat requirements.txt...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [LOI] Khong the cai dat thu vien! Vui long kiem tra ket noi mang.
        pause
        exit /b 1
    )
)

:: 4. Khoi dong Master Dashboard
echo [INFO] Dang khoi dong Master Dashboard GUI...
python main.py

if errorlevel 1 (
    echo.
    echo [THONG BAO] Ung dung da dong hoac xay ra loi.
    pause
)
