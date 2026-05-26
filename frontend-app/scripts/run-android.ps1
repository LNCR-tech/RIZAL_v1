# Aura — run the Flutter app on the first connected Android device.
#
# Picks the first android-arm64 / android-arm device `flutter devices`
# reports, loads endpoints from config/cloud.json, and runs in debug
# mode with hot-reload enabled. Hot-reload keys once it boots:
#   r  hot reload
#   R  hot restart
#   q  quit
#
# Usage (from anywhere):
#   pwsh -File C:\Users\DjMhel\Documents\Software\RIZAL_v1-integrate-pilot-merge\frontend-app\scripts\run-android.ps1
# Or from frontend-app/:
#   .\scripts\run-android.ps1
#
# Override the device by passing -DeviceId 'YOURDEVICEID':
#   .\scripts\run-android.ps1 -DeviceId IJH6BYNNIZ8DIV69
#
# Prerequisite: USB debugging enabled on the phone + you tapped "Allow"
# on the RSA fingerprint prompt the first time. Confirm with
# `flutter devices` — your phone should show as android-arm64.

param(
    [string]$DeviceId = ''
)

$ErrorActionPreference = 'Stop'

# Always run from the Flutter app root (one level up from this script).
$appRoot = Split-Path -Parent $PSScriptRoot
Set-Location $appRoot

if (-not $DeviceId) {
    # Find the first connected Android device.
    $line = & flutter devices --machine 2>$null |
        ConvertFrom-Json |
        Where-Object { $_.targetPlatform -match 'android' } |
        Select-Object -First 1

    if (-not $line) {
        Write-Host "No Android device connected. Plug in your phone, enable USB debugging, and approve the RSA prompt." -ForegroundColor Red
        Write-Host "Then run: flutter devices  — it should list an android-arm64 entry." -ForegroundColor DarkGray
        exit 1
    }
    $DeviceId = $line.id
    Write-Host "Picked Android device: $($line.name) ($DeviceId)" -ForegroundColor Cyan
}

Write-Host "Launching Aura on $DeviceId..." -ForegroundColor Cyan

& flutter run `
    --dart-define-from-file=config/cloud.json `
    -d $DeviceId
