# Aura Docker Deployment Script for Windows
# Run this from the project root: .\deploy-docker.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Aura Docker Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found or not running!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop and make sure it's running." -ForegroundColor Red
    exit 1
}

# Check Docker Compose
try {
    $composeVersion = docker compose version
    Write-Host "✓ Docker Compose found: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Compose not found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setting up Environment Files" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to copy env file if it doesn't exist
function Copy-EnvFile {
    param($Source, $Dest, $ServiceName)
    
    if (Test-Path $Dest) {
        Write-Host "✓ $ServiceName .env already exists" -ForegroundColor Green
    } elseif (Test-Path $Source) {
        Copy-Item $Source $Dest
        Write-Host "✓ Created $ServiceName .env from example" -ForegroundColor Green
    } else {
        Write-Host "✗ $Source not found!" -ForegroundColor Red
    }
}

# Copy environment files
Copy-EnvFile ".\backend\.env.example" ".\backend\.env" "Backend"
Copy-EnvFile ".\database\.env.example" ".\database\.env" "Database"
Copy-EnvFile ".\assistant\.env.example" ".\assistant\.env" "Assistant"
Copy-EnvFile ".\frontend-web\.env.example" ".\frontend\.env" "Frontend"
Copy-EnvFile ".\seeder\.env.example" ".\seeder\.env" "Seeder"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Configuration Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if SECRET_KEY is set in backend/.env
if (Test-Path ".\backend\.env") {
    $backendEnv = Get-Content ".\backend\.env" -Raw
    if ($backendEnv -match "SECRET_KEY=.*change.*" -or $backendEnv -match "SECRET_KEY=\s*$") {
        Write-Host "⚠ WARNING: SECRET_KEY not configured in backend/.env" -ForegroundColor Yellow
        Write-Host "  Please edit backend/.env and set a secure SECRET_KEY" -ForegroundColor Yellow
        Write-Host ""
        $continue = Read-Host "Continue anyway? (y/n)"
        if ($continue -ne "y") {
            Write-Host "Deployment cancelled. Please configure backend/.env first." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✓ SECRET_KEY configured" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deployment Options" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Development (includes pgAdmin, log viewer)" -ForegroundColor White
Write-Host "2. Production (minimal services)" -ForegroundColor White
Write-Host "3. Stop all services" -ForegroundColor White
Write-Host "4. Stop and remove all data (DANGEROUS!)" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Select option (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "  Starting Development Stack" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "This will take 5-10 minutes on first run..." -ForegroundColor Yellow
        Write-Host ""
        
        docker compose --profile dev up --build
    }
    "2" {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "  Starting Production Stack" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "This will take 5-10 minutes on first run..." -ForegroundColor Yellow
        Write-Host ""
        
        docker compose --profile prod up --build
    }
    "3" {
        Write-Host ""
        Write-Host "Stopping all services..." -ForegroundColor Yellow
        docker compose down
        Write-Host "✓ All services stopped" -ForegroundColor Green
    }
    "4" {
        Write-Host ""
        Write-Host "⚠ WARNING: This will DELETE ALL DATA!" -ForegroundColor Red
        $confirm = Read-Host "Type 'DELETE' to confirm"
        if ($confirm -eq "DELETE") {
            Write-Host "Stopping and removing all data..." -ForegroundColor Yellow
            docker compose down -v
            Write-Host "✓ All services and data removed" -ForegroundColor Green
        } else {
            Write-Host "Cancelled" -ForegroundColor Yellow
        }
    }
    default {
        Write-Host "Invalid option" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access your application at:" -ForegroundColor Green
Write-Host "  Frontend:     http://localhost:5173" -ForegroundColor White
Write-Host "  Backend API:  http://localhost:8001/docs" -ForegroundColor White
Write-Host "  Assistant:    http://localhost:8500/docs" -ForegroundColor White
if ($choice -eq "1") {
    Write-Host "  pgAdmin:      http://localhost:5050" -ForegroundColor White
    Write-Host "  Log Viewer:   http://localhost:8080" -ForegroundColor White
}
Write-Host ""
Write-Host "View logs: docker compose logs -f" -ForegroundColor Cyan
Write-Host "Stop services: docker compose down" -ForegroundColor Cyan
Write-Host ""
