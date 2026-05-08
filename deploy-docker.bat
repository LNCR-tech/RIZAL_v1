@echo off
echo ========================================
echo   Aura Docker Deployment
echo ========================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not found!
    echo Please install Docker Desktop and make sure it's running.
    pause
    exit /b 1
)

echo Docker found!
echo.

REM Copy environment files if they don't exist
echo Setting up environment files...
if not exist "backend\.env" (
    if exist "backend\.env.example" (
        copy "backend\.env.example" "backend\.env" >nul
        echo Created backend\.env
    )
)

if not exist "database\.env" (
    if exist "database\.env.example" (
        copy "database\.env.example" "database\.env" >nul
        echo Created database\.env
    )
)

if not exist "assistant\.env" (
    if exist "assistant\.env.example" (
        copy "assistant\.env.example" "assistant\.env" >nul
        echo Created assistant\.env
    )
)

if not exist "frontend-web\.env" (
    if exist "frontend-web\.env.example" (
        copy "frontend-web\.env.example" "frontend-web\.env" >nul
        echo Created frontend-web\.env
    )
)

if not exist "seeder\.env" (
    if exist "seeder\.env.example" (
        copy "seeder\.env.example" "seeder\.env" >nul
        echo Created seeder\.env
    )
)

echo.
echo ========================================
echo   Deployment Options
echo ========================================
echo.
echo 1. Start Development Stack (with pgAdmin, logs)
echo 2. Start Production Stack
echo 3. Stop All Services
echo 4. View Logs
echo 5. Rebuild Backend Only
echo.

set /p choice="Select option (1-5): "

if "%choice%"=="1" (
    echo.
    echo Starting development stack...
    echo This may take 5-10 minutes on first run.
    echo.
    docker compose --profile dev up --build
) else if "%choice%"=="2" (
    echo.
    echo Starting production stack...
    echo.
    docker compose --profile prod up --build
) else if "%choice%"=="3" (
    echo.
    echo Stopping all services...
    docker compose down
    echo Done!
) else if "%choice%"=="4" (
    echo.
    docker compose logs -f
) else if "%choice%"=="5" (
    echo.
    echo Rebuilding backend...
    docker compose up --build -d backend worker beat
    echo Done!
) else (
    echo Invalid option!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Access Your Application
echo ========================================
echo.
echo Frontend:     http://localhost:5173
echo Backend API:  http://localhost:8001/docs
echo Assistant:    http://localhost:8500/docs
echo pgAdmin:      http://localhost:5050
echo Log Viewer:   http://localhost:8080
echo.
echo View logs:    docker compose logs -f
echo Stop:         docker compose down
echo.
pause
