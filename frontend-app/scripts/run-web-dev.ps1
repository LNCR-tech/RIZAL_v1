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
#
# Why web-server + manual Chrome spawn (not `flutter run -d chrome`):
# Flutter's chrome_device launches Chrome with --remote-debugging-port and
# waits for the DevTools handshake on stderr. On Chrome 130+/Windows that
# handshake intermittently never arrives when another Chrome session is
# already running — three retries fail, you get "Failed to launch browser
# after 3 tries". `-d web-server` binds a port without auto-launching, and
# we own the Chrome spawn so the failure mode is gone.

$ErrorActionPreference = 'Stop'
$appRoot = Split-Path -Parent $PSScriptRoot
Set-Location $appRoot

$port       = 5174
$profileDir = Join-Path $env:TEMP 'chrome-aura-dev'
$chromeExe  = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
if (-not (Test-Path $chromeExe)) {
    Write-Host "Chrome not found at $chromeExe — edit this script if it lives elsewhere." -ForegroundColor Red
    exit 1
}

# Prune flutter_tools.* temp dirs older than 1 day. Flutter leaves a ~50MB
# Chrome profile per failed/Ctrl-C'd launch; without this the temp folder
# accumulates indefinitely (you had 7+ GB of these before this cleanup ran).
$stale = Get-ChildItem "$env:TEMP\flutter_tools.*" -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-1) }
if ($stale) {
    Write-Host "Pruning $($stale.Count) stale Flutter temp dirs..." -ForegroundColor DarkGray
    $stale | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

# Clear Chrome singleton lock files from prior runs of this profile. These
# coordinate inter-process Chrome instances; if a previous Chrome left them
# behind (crash / kill / failed launch) our spawn would refuse to start on
# the same --user-data-dir. Session state (cookies, local storage, app
# prefs) lives elsewhere in the profile and is preserved.
if (Test-Path $profileDir) {
    Get-ChildItem $profileDir -Filter 'Singleton*' -ErrorAction SilentlyContinue |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

# Free $port if a previous flutter run / dartvm is still holding it.
# Flutter binds 0.0.0.0:$port; if anything else is on that port we'd hit
# "Only one usage of each socket address (errno = 10048)" and fail to
# start. Kill ONLY the process bound to the exact port — not all dart
# processes, since an IDE / Pad / second project may legitimately have
# its own dart running. Targeted, not nuclear.
$existing = Get-NetTCPConnection -LocalPort $port -State Listen `
    -ErrorAction SilentlyContinue
if ($existing) {
    foreach ($conn in @($existing)) {
        $owner = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        $name = if ($owner) { $owner.ProcessName } else { '(unknown)' }
        Write-Host "Port $port is held by PID $($conn.OwningProcess) ($name) — stopping it" -ForegroundColor Yellow
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    }
    # Windows can keep the socket in TIME_WAIT briefly after the holder dies;
    # poll until the bind would succeed (capped — bail with an error if it
    # never frees so the user isn't left staring at an unexplained hang).
    $deadline = (Get-Date).AddSeconds(10)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 200
        $still = Get-NetTCPConnection -LocalPort $port -State Listen `
            -ErrorAction SilentlyContinue
        if (-not $still) { break }
    }
    $still = Get-NetTCPConnection -LocalPort $port -State Listen `
        -ErrorAction SilentlyContinue
    if ($still) {
        Write-Host "Port $port is still held after 10s — kill PID $($still.OwningProcess) manually and retry." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Launching Aura on http://localhost:$port (Chrome, CORS off)" -ForegroundColor Cyan
Write-Host "Chrome profile: $profileDir" -ForegroundColor DarkGray
Write-Host ""

# Spawn Chrome asynchronously — it polls the dev-server port and only opens
# once Flutter is actually serving. Without this we'd race Flutter and
# Chrome would hit ERR_CONNECTION_REFUSED before Flutter finished compiling.
$chromeArgs = @(
    '--disable-web-security',
    "--user-data-dir=$profileDir",
    '--new-window',
    "http://localhost:$port"
)
$null = Start-Job -Name 'aura-chrome-launcher' -ScriptBlock {
    param($exe, $argv, $portToWait)
    $deadline = (Get-Date).AddSeconds(180)
    while ((Get-Date) -lt $deadline) {
        try {
            $c = New-Object System.Net.Sockets.TcpClient
            $c.Connect('localhost', $portToWait)
            $c.Close()
            break
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    Start-Process -FilePath $exe -ArgumentList $argv
} -ArgumentList $chromeExe, $chromeArgs, $port

try {
    # web-server: no auto-launch, hot-reload via stdin still works (r / R / q).
    #
    # --no-web-resources-cdn: serve CanvasKit from the local Flutter SDK
    # instead of fetching it from gstatic.com. Without this, modern
    # Flutter web's default CanvasKit renderer fails its initial
    # `import("https://www.gstatic.com/.../canvaskit.js")` whenever the
    # network can't reach the CDN (corporate firewall, flaky DNS, slow
    # link, offline) - and Flutter cannot render at all when that import
    # rejects: the body stays empty, Chrome shows pure white, and the
    # only symptom in DevTools is a single TypeError far from any app
    # code. Serving CanvasKit from the dev server itself is fast and has
    # no offline failure mode.
    & flutter run `
        --dart-define-from-file=config/cloud.json `
        -d web-server `
        --web-port $port `
        --no-web-resources-cdn `
        --web-header "Cross-Origin-Opener-Policy=same-origin-allow-popups"
} finally {
    Get-Job -Name 'aura-chrome-launcher' -ErrorAction SilentlyContinue |
        Remove-Job -Force -ErrorAction SilentlyContinue
}
