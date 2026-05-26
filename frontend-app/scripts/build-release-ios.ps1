# Aura — release iOS build (IPA) with anti-reverse-engineering flags.
# Same security posture as build-release-android.ps1 — obfuscation +
# split debug info + tree-shaken icons + ATS-only network stack.
#
# Run on a macOS host with Xcode installed. On Windows this will fail
# fast with a clear message — it only exists as a parallel for ops docs.

$ErrorActionPreference = 'Stop'

if (-not $IsMacOS) {
    Write-Host "iOS release builds require macOS + Xcode. Run this script from a Mac." -ForegroundColor Red
    exit 1
}

$appRoot = Split-Path -Parent $PSScriptRoot
Set-Location $appRoot

$version = (Get-Content pubspec.yaml |
  Where-Object { $_ -match '^version:\s*(\S+)' } |
  Select-Object -First 1) -replace '^version:\s*', ''

$symbolsDir = Join-Path $appRoot "build/symbols/$version"
if (-not (Test-Path $symbolsDir)) { New-Item -ItemType Directory -Force $symbolsDir | Out-Null }

Write-Host "Building Aura $version (iOS, obfuscated, symbols → $symbolsDir)" -ForegroundColor Cyan

& flutter build ipa `
    --release `
    --dart-define-from-file=config/cloud.json `
    --obfuscate `
    --split-debug-info=$symbolsDir `
    --tree-shake-icons

Write-Host ""
Write-Host "IPA:     build/ios/ipa/aura.ipa (filename depends on bundle id)" -ForegroundColor Green
Write-Host "Symbols: $symbolsDir" -ForegroundColor Green
