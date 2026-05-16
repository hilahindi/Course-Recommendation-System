@echo off
setlocal EnableExtensions

cd /d "%~dp0"

where node >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js was not found on PATH. Install Node.js 18+ and try again.
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm was not found on PATH.
    exit /b 1
)

if not exist "package.json" (
    echo ERROR: package.json not found in %cd%
    exit /b 1
)

echo Installing npm dependencies...
call npm install
if errorlevel 1 exit /b 1

echo.
echo Setup complete. Run: run_client.bat
endlocal
