# Start ngrok tunnels for Aura system
# This script starts two ngrok tunnels: one for frontend (5173) and one for backend (8000)

Write-Host "Starting ngrok tunnels for Aura..." -ForegroundColor Cyan

# Check if ngrok is installed
if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: ngrok is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Install it from: https://ngrok.com/download" -ForegroundColor Yellow
    Write-Host "Or via chocolatey: choco install ngrok" -ForegroundColor Yellow
    exit 1
}

# Check if Docker services are running
$frontendRunning = docker ps --filter "name=rizalmvp-frontend" --filter "status=running" --format "{{.Names}}"
$backendRunning = docker ps --filter "name=rizalmvp-backend" --filter "status=running" --format "{{.Names}}"

if (-not $frontendRunning -or -not $backendRunning) {
    Write-Host "WARNING: Docker services may not be running" -ForegroundColor Yellow
    Write-Host "Run 'docker compose up -d' first" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 0
    }
}

# Create ngrok config file
$ngrokConfig = @"
version: "2"
authtoken: 3A7WPglodFxBO8vBtbGxqfArraN_4fE15e3KEkcRgh5dFmpnJ
tunnels:
  frontend:
    proto: http
    addr: 5173
    inspect: false
"@

$configPath = "$env:TEMP\ngrok-aura.yml"
$ngrokConfig | Out-File -FilePath $configPath -Encoding UTF8

Write-Host ""
Write-Host "Starting ngrok with config:" -ForegroundColor Green
Write-Host "  - Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  - Backend:  http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all tunnels" -ForegroundColor Yellow
Write-Host ""

# Start ngrok with both tunnels
ngrok start --all --config=$configPath

# Cleanup
Remove-Item $configPath -ErrorAction SilentlyContinue
