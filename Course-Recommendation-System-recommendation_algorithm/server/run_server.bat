@echo off
setlocal EnableExtensions

set "SERVER_DIR=%~dp0"
cd /d "%SERVER_DIR%"

if not exist "%SERVER_DIR%.venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found at server\.venv
    echo.
    echo Run setup first:
    echo   setup.bat
    echo.
    exit /b 1
)

call "%SERVER_DIR%.venv\Scripts\activate.bat"

if exist "%SERVER_DIR%.env" (
    echo [run_server] Using server\.env
) else (
    echo [run_server] Warning: server\.env not found. Copy .env.example to .env
)

cd /d "%SERVER_DIR%src"
echo [run_server] Starting uvicorn at http://127.0.0.1:8000  (API: /api/v1)
uvicorn main:app --reload

endlocal
