# Aura — clear a corrupted Gradle transforms cache.
#
# Run this if Flutter's Android build fails with:
#   "Could not read workspace metadata from
#    C:\Users\<you>\.gradle\caches\<ver>\transforms\<hash>\metadata.bin"
#
# That message means Gradle's per-version transforms directory has half-
# written entries (usually because a previous daemon was killed mid-run).
# Deleting the directory makes Gradle re-download + re-transform on the
# next build (~2–5 minutes the first time, normal afterwards).
#
# Usage (from anywhere):
#   pwsh -File C:\Users\DjMhel\Documents\Software\RIZAL_v1-integrate-pilot-merge\frontend-app\scripts\fix-gradle-cache.ps1
# Or from frontend-app/:
#   .\scripts\fix-gradle-cache.ps1

$ErrorActionPreference = 'Continue'   # individual deletes shouldn't kill the script

$appRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Stopping any running java/Gradle daemons..." -ForegroundColor Cyan
Get-Process -Name java -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "Running flutter clean..." -ForegroundColor Cyan
Set-Location $appRoot
& flutter clean | Out-Host

$gradleCache = Join-Path $env:USERPROFILE ".gradle\caches"
if (Test-Path $gradleCache) {
    Write-Host "Clearing Gradle transforms cache under $gradleCache ..." -ForegroundColor Cyan

    # Delete the version-pinned transforms dir (8.14, 8.x, etc.) if present.
    Get-ChildItem -Path $gradleCache -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^\d+(\.\d+)+$' } |
        ForEach-Object {
            $tx = Join-Path $_.FullName 'transforms'
            if (Test-Path $tx) {
                Write-Host "  removing $tx"
                Remove-Item -Recurse -Force $tx -ErrorAction SilentlyContinue
            }
        }

    # Older Gradle put transforms-* at the cache root — clean those too.
    Get-ChildItem -Path $gradleCache -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like 'transforms-*' } |
        ForEach-Object {
            Write-Host "  removing $($_.FullName)"
            Remove-Item -Recurse -Force $_.FullName -ErrorAction SilentlyContinue
        }
} else {
    Write-Host "No Gradle cache at $gradleCache — nothing to clear." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Cache cleared. Next Flutter run will re-download transforms (~2-5 min)." -ForegroundColor Green
Write-Host "Run:" -ForegroundColor Green
Write-Host "  .\scripts\run-android.ps1" -ForegroundColor White
