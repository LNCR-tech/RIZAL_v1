# Aura — diagnostic Android build.
#
# Goes around the `flutter run` wrapper (which hides the actual Flutter
# stderr behind Gradle's stack trace when `compileFlutterBuildDebug`
# fails) and runs the steps individually. If anything errors, you see
# the real Flutter / Dart message instead of a Gradle wrapper trace.
#
# Order:
#   1. flutter clean              — wipe partial build artifacts
#   2. flutter pub get            — resolve deps fresh
#   3. flutter analyze --no-pub   — surface Dart errors first
#   4. flutter build apk --debug  — Dart + Gradle, prints actual errors
#   5. (manual) flutter install   — only if APK built
#
# Usage:
#   .\scripts\diagnose-android-build.ps1

$ErrorActionPreference = 'Continue'

$appRoot = Split-Path -Parent $PSScriptRoot
Set-Location $appRoot

function Step([string]$label, [scriptblock]$action) {
    Write-Host ""
    Write-Host "=== $label ===" -ForegroundColor Cyan
    & $action
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAILED at: $label (exit $LASTEXITCODE)" -ForegroundColor Red
        Write-Host "Stop here, read the error above, fix it, then re-run this script." -ForegroundColor Yellow
        exit $LASTEXITCODE
    }
}

Step "1. flutter clean" {
    & flutter clean
}

Step "2. flutter pub get" {
    & flutter pub get
}

Step "3. flutter analyze (no-pub, fast)" {
    & flutter analyze --no-pub
}

Step "4. flutter build apk --debug (full diagnostic — shows real errors)" {
    & flutter build apk `
        --debug `
        --dart-define-from-file=config/cloud.json
}

Write-Host ""
Write-Host "BUILD SUCCEEDED." -ForegroundColor Green
Write-Host "APK: build\app\outputs\flutter-apk\app-debug.apk" -ForegroundColor Green
Write-Host ""
Write-Host "Next: plug your phone in, then:" -ForegroundColor White
Write-Host "  .\scripts\run-android.ps1" -ForegroundColor White
