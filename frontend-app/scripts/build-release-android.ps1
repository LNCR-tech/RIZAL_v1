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
#   --split-per-abi            Emits one APK per CPU architecture
#                              (arm64-v8a, armeabi-v7a, x86_64) instead of a
#                              single fat APK. Each per-ABI APK is roughly a
#                              third the size of the fat one (~25-35MB vs
#                              ~80MB) — install the matching one for the
#                              target device.
#
# Gradle's R8 (default in Flutter release) runs on top of the obfuscated Dart
# output, so Kotlin/Java glue is also minified + obfuscated.
#
# Usage (from anywhere):
#   pwsh -File C:\Users\DjMhel\Documents\Software\RIZAL_v1-integrate-pilot-merge\frontend-app\scripts\build-release-android.ps1
#
# Output:
#   build\app\outputs\flutter-apk\app-arm64-v8a-release.apk     ← most modern phones
#   build\app\outputs\flutter-apk\app-armeabi-v7a-release.apk   ← older 32-bit ARM
#   build\app\outputs\flutter-apk\app-x86_64-release.apk        ← Intel Atom (rare)
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

Write-Host "Building Aura $version (Android, obfuscated, per-ABI split, symbols → $symbolsDir)" -ForegroundColor Cyan

& flutter build apk `
    --release `
    --split-per-abi `
    --dart-define-from-file=config/cloud.json `
    --obfuscate `
    --split-debug-info=$symbolsDir `
    --tree-shake-icons

Write-Host ""
Write-Host "APKs (one per CPU architecture):" -ForegroundColor Green
Write-Host "  build\app\outputs\flutter-apk\app-arm64-v8a-release.apk     ← most modern phones, including OPPO A5s"
Write-Host "  build\app\outputs\flutter-apk\app-armeabi-v7a-release.apk   ← older 32-bit ARM devices"
Write-Host "  build\app\outputs\flutter-apk\app-x86_64-release.apk        ← Intel Atom (rare)"
Write-Host "Symbols: $symbolsDir" -ForegroundColor Green
Write-Host ""
Write-Host "Keep the symbols folder safe — you cannot symbolicate release crashes without it." -ForegroundColor Yellow
