@echo off
REM Aura Documentation Deployment Script for Windows

echo 🚀 Deploying Aura Documentation...

REM Load environment
if exist .env.production (
    for /f "tokens=*" %%a in (.env.production) do (
        set %%a
    )
)

REM Build Docker image
echo 📦 Building Docker image...
docker build -t aura-doc-site:latest .

REM Stop existing container
echo 🛑 Stopping existing container...
docker stop aura-doc-site 2>nul
docker rm aura-doc-site 2>nul

REM Create network if it doesn't exist
docker network create aura-network 2>nul

REM Run new container
echo ▶️  Starting new container...
docker run -d ^
  --name aura-doc-site ^
  --network aura-network ^
  -p 3000:80 ^
  -e REACT_APP_BACKEND_URL=%REACT_APP_BACKEND_URL% ^
  -e REACT_APP_AUTH_ENABLED=%REACT_APP_AUTH_ENABLED% ^
  --restart unless-stopped ^
  aura-doc-site:latest

echo ✅ Deployment complete!
echo 📖 Documentation available at: http://localhost:3000
echo.
echo Health check: curl http://localhost:3000/health

pause
