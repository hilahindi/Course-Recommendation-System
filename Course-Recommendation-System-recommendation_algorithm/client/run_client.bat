@echo off
setlocal EnableExtensions

set "CLIENT_DIR=%~dp0"
cd /d "%CLIENT_DIR%"

where node >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js was not found on PATH.
    exit /b 1
)

if not exist "%CLIENT_DIR%node_modules" (
    echo ERROR: node_modules not found.
    echo.
    echo Run setup first:
    echo   setup.bat
    echo.
    exit /b 1
)

echo [run_client] Starting Vite at http://localhost:5173
echo [run_client] Ensure the backend is running: server\run_server.bat
call npm run dev

endlocal
