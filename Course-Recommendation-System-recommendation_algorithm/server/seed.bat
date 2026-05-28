@echo off
setlocal EnableExtensions

set "SERVER_DIR=%~dp0"
cd /d "%SERVER_DIR%"

if not exist "%SERVER_DIR%.venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found. Run setup.bat first.
    exit /b 1
)

if not exist "%SERVER_DIR%.env" (
    echo ERROR: server\.env not found. Copy .env.example to .env
    exit /b 1
)

echo [seed] Running scripts\seed.py ...
"%SERVER_DIR%.venv\Scripts\python.exe" "%SERVER_DIR%scripts\seed.py"
exit /b %ERRORLEVEL%
