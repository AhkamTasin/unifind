@echo off
REM ============================================================
REM  UniFind - Campus Lost & Found Management System
REM  One-click launcher for Windows (Command Prompt)
REM ============================================================
setlocal
cd /d "%~dp0"

REM --- 1. Create virtual environment if missing ---
if not exist ".venv" (
    echo [1/3] Creating virtual environment ...
    python -m venv .venv
    if errorlevel 1 goto :error
)

REM --- 2. Activate venv ---
call .venv\Scripts\activate.bat

REM --- 3. Install dependencies ---
echo [2/3] Installing dependencies ...
pip install -r requirements.txt -q
if errorlevel 1 goto :error

REM --- Apply migrations ---
echo Applying database migrations ...
python manage.py migrate --noinput

REM --- Seed categories & demo accounts (safe to re-run) ---
echo Seeding categories and demo accounts ...
python manage.py seed_data

REM --- Run the server ---
echo.
echo [3/3] Starting UniFind at http://127.0.0.1:8000
echo       Press Ctrl+C to stop the server.
echo.
python manage.py runserver
goto :eof

:error
echo.
echo Something went wrong. Make sure Python 3.10+ is installed and on your PATH.
pause
