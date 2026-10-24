#!/bin/bash
# AI Final Project - Master Dashboard Launcher (Nhom 08 - TDTU)

echo "==============================================================================="
echo "       TRUONG DAI HOC TON DUC THANG - KHOA CONG NGHE THONG TIN"
echo "           DO AN CUOI KY: NHAP MON TRI TUE NHAN TAO (503043)"
echo "          NHOM 08 | GIANG VIEN HUONG DAN: ThS. NGUYEN THANH AN"
echo "==============================================================================="
echo ""

# 1. Kiem tra Python
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "[LOI] Khong tim thay Python! Vui long cai dat Python 3.10+."
    exit 1
fi

# 2. Kich hoat virtual environment neu co
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# 3. Kiem tra thu vien
$PY_CMD -c "import pygame" &>/dev/null
if [ $? -ne 0 ]; then
    echo "[THONG BAO] Dang tu dong cai dat requirements.txt..."
    $PY_CMD -m pip install -r requirements.txt
fi

# 4. Khoi dong Master Dashboard
echo "[INFO] Dang khoi dong Master Dashboard GUI..."
$PY_CMD main.py
