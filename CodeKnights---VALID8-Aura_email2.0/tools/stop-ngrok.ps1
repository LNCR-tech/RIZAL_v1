$ErrorActionPreference = "Stop"

$processes = Get-Process ngrok -ErrorAction SilentlyContinue
if ($null -eq $processes) {
    Write-Host "No ngrok process is running."
    exit 0
}

$processes | Stop-Process -Force
Write-Host "Stopped ngrok."
