@echo off
echo ========================================
echo   Waiting for Docker Desktop to start...
echo ========================================
echo.

:check_docker
docker ps >nul 2>&1
if errorlevel 1 (
    echo Docker not ready yet... waiting 5 seconds
    timeout /t 5 /nobreak >nul
    goto check_docker
)

echo.
echo ========================================
echo   Docker is ready! Starting deployment...
echo ========================================
echo.

cd C:\Users\USER\IdeaProjects\auraproduction\new

echo Building and starting all services...
echo This will take 5-10 minutes on first run.
echo.

docker compose --profile dev up -d --build

echo.
echo ========================================
echo   Checking service status...
echo ========================================
echo.

timeout /t 5 /nobreak >nul
docker compose ps

echo.
echo ========================================
echo   Deployment Started!
echo ========================================
echo.
echo View logs: docker compose logs -f
echo.
echo Services will be available at:
echo   Frontend:     http://localhost:5173
echo   Backend API:  http://localhost:8001/docs
echo   Assistant:    http://localhost:8500/docs
echo   pgAdmin:      http://localhost:5050
echo   Log Viewer:   http://localhost:8080
echo.
echo Press any key to view logs...
pause >nul

docker compose logs -f
