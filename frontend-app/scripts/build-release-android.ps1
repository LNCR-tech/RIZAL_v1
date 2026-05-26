# Aura — release Android build with anti-reverse-engineering flags.
#
# What this gives you over `flutter build apk`:
#   --obfuscate                Replaces Dart symbols (class / method names) with
#                              short tokens. Decompiled output is no longer
#                              human-readable.
#   --split-debug-info=...     Strips the symbol map into a separate file in
#                              build/symbols/<version>/. The APK ships without
#                              it, so a crash stack trace from the wild is
#                              meaningless to anyone who doesn't have the map.
#                              KEEP THESE — without them you can't symbolicate
#                              crashes.
#   --tree-shake-icons         Removes unused MaterialIcons code-points. Shrinks
#                              the APK and removes hints about which icons
#                              (and therefore which screens) exist.
#   --no-pub                   Skip pub get; assume the lockfile is current.
#
# Gradle's R8 (default in Flutter release) runs on top of the obfuscated Dart
# output, so Kotlin/Java glue is also minified + obfuscated.
#
# Usage (from anywhere):
#   pwsh -File C:\Users\DjMhel\Documents\Software\RIZAL_v1-integrate-pilot-merge\frontend-app\scripts\build-release-android.ps1
#
# Output:
#   build\app\outputs\flutter-apk\app-release.apk
#   build\symbols\<version>\  (keep this checked into infra; do NOT publish)
#
# Sign the APK separately with your release keystore — the play-store keystore
# is NEVER committed to git.

$ErrorActionPreference = 'Stop'

$appRoot = Split-Path -Parent $PSScriptRoot
Set-Location $appRoot

$version = (Get-Content pubspec.yaml |
  Where-Object { $_ -match '^version:\s*(\S+)' } |
  Select-Object -First 1) -replace '^version:\s*', ''

$symbolsDir = Join-Path $appRoot "build\symbols\$version"
if (-not (Test-Path $symbolsDir)) { New-Item -ItemType Directory -Force $symbolsDir | Out-Null }

Write-Host "Building Aura $version (Android, obfuscated, symbols → $symbolsDir)" -ForegroundColor Cyan

& flutter build apk `
    --release `
    --dart-define-from-file=config/cloud.json `
    --obfuscate `
    --split-debug-info=$symbolsDir `
    --tree-shake-icons

Write-Host ""
Write-Host "APK:     build\app\outputs\flutter-apk\app-release.apk" -ForegroundColor Green
Write-Host "Symbols: $symbolsDir" -ForegroundColor Green
Write-Host ""
Write-Host "Keep the symbols folder safe — you cannot symbolicate release crashes without it." -ForegroundColor Yellow
