@echo off
echo ========================================
echo    Pharma AI Backend Server
echo ========================================
echo.

cd /d "%~dp0"

REM Activate virtual environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo Warning: Virtual environment not found at .venv
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
)

cd backend

REM Check if .env exists
if not exist ".env" (
    echo Warning: .env file not found!
    echo Please copy .env.example to .env and configure it.
    echo.
)

echo.
echo Starting backend server on http://localhost:8000
echo Press Ctrl+C to stop the server.
echo.

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause
