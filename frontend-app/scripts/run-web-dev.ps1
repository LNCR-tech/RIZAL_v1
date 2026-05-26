# Aura — run the Flutter web client against the cloud backend with web
# security disabled. CORS-only workaround for dev; the backend at
# 18.142.190.113:8001 does not list http://localhost:5174 as an allowed
# origin, so a normal Chrome blocks the API call.
#
# Usage (from anywhere):
#   pwsh -File C:\Users\DjMhel\Documents\Software\RIZAL_v1-integrate-pilot-merge\frontend-app\scripts\run-web-dev.ps1
# Or from frontend-app/:
#   .\scripts\run-web-dev.ps1
#
# NEVER browse the wider web in the Chrome window this opens — the isolated
# profile lives in $env:TEMP\chrome-aura-dev and has web security OFF.

$ErrorActionPreference = 'Stop'

# Always run from the Flutter app root (one level up from this script).
$appRoot = Split-Path -Parent $PSScriptRoot
Set-Location $appRoot

$port = 5174
$profileDir = Join-Path $env:TEMP 'chrome-aura-dev'

Write-Host "Launching Aura on http://localhost:$port (Chrome, CORS off)..." -ForegroundColor Cyan
Write-Host "Chrome profile: $profileDir" -ForegroundColor DarkGray

& flutter run `
    --dart-define-from-file=config/cloud.json `
    -d chrome `
    --web-port $port `
    --web-browser-flag="--disable-web-security" `
    --web-browser-flag="--user-data-dir=$profileDir"
