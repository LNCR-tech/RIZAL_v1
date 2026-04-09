$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "Starting containers (build if needed)..."
docker compose up -d --build

Write-Host ""
Write-Host "Services:"
docker compose ps

Write-Host ""
Write-Host "Dev URLs:"
Write-Host "Frontend: http://localhost:5174"
Write-Host "Backend:  http://localhost:8001/docs"
Write-Host "pgAdmin:  http://localhost:5051"
Write-Host "Mailpit:  http://localhost:8026"

Write-Host ""
Write-Host "Seed output (URLs + credentials):"
docker compose logs --no-color --tail=200 seed

