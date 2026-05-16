@echo off
setlocal EnableExtensions

cd /d "%~dp0"

echo [docker-reset] Stopping containers and removing volumes (pgdata + pgadmin_data)...
docker compose down -v
if errorlevel 1 (
    docker-compose down -v
)

echo [docker-reset] Starting fresh stack...
docker compose up -d
if errorlevel 1 (
    docker-compose up -d
)

echo.
echo Waiting for Postgres healthcheck...
:wait_loop
docker inspect --format "{{.State.Health.Status}}" course_db 2>nul | findstr /i "healthy" >nul
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto wait_loop
)

echo.
echo Done.
echo   Postgres (host): 127.0.0.1:5433  user=admin  password=password123  db=course_recommender
echo   pgAdmin:         http://localhost:8080  login=admin@admin.com / admin
echo   pgAdmin DB host: db  port 5432  (Docker internal — use pre-registered server)
echo.
echo Next: cd server ^&^& seed.bat
endlocal
