$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "Dev URLs:"
Write-Host "Frontend: http://localhost:5173"
Write-Host "Backend:  http://localhost:8000/docs"
Write-Host "pgAdmin:  http://localhost:5050"
Write-Host "Mailpit:  http://localhost:8025"

Write-Host ""
Write-Host "Seed output (URLs + credentials):"
docker compose logs --no-color --tail=200 seed

