@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on PATH. Install Python 3.8+ and try again.
    exit /b 1
)

if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found in %cd%
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating server\.venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        exit /b 1
    )
) else (
    echo server\.venv already exists.
)

echo Upgrading pip ...
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 exit /b 1

echo Installing dependencies from requirements.txt ...
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo.
echo Setup complete.
echo   1. Copy .env.example to .env and set your API keys
echo   2. Seed DB: seed.bat
echo   3. Run: run_server.bat
endlocal
