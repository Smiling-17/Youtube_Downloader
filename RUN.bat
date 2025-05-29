@echo off
echo Dang khoi dong YouTube Downloader Pro...
echo.

REM Kiem tra xem co môi truong ao khong
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo Khong tim thay moi truong ao, dang kiem tra Python...
    python --version >nul 2>&1
    if errorlevel 1 (
        echo Loi: Khong tim thay Python. Vui long cai dat Python truoc khi chay.
        pause
        exit /b 1
    )
)

REM Kiem tra va cai dat cac thu vien can thiet
echo Dang kiem tra va cai dat cac thu vien...
pip install -r requirements.txt

REM Chay chuong trinh
echo.
echo Dang chay chuong trinh...
python main.py

REM Neu co loi, dung man hinh de doc thong bao
if errorlevel 1 (
    echo.
    echo Co loi xay ra khi chay chuong trinh.
    pause
)

REM Thoat moi truong ao neu co
if exist "venv\Scripts\deactivate.bat" (
    call venv\Scripts\deactivate.bat
) 