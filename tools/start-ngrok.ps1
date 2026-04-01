param(
    [switch]$KeepExisting,
    [int]$FrontendPort = 0
)

$ErrorActionPreference = "Stop"

function Test-FrontendPort {
    param(
        [int]$Port
    )

    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/" -TimeoutSec 2
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    } catch {
        return $false
    }
}

if ($FrontendPort -le 0) {
    foreach ($candidatePort in @(80, 5173)) {
        if (Test-FrontendPort -Port $candidatePort) {
            $FrontendPort = $candidatePort
            break
        }
    }
}

if ($FrontendPort -le 0) {
    throw "Could not detect a running frontend on ports 80 or 5173. Start the app first or pass -FrontendPort explicitly."
}

if (-not $KeepExisting) {
    Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
}

Start-Process -FilePath "ngrok" -ArgumentList @(
    "http",
    "$FrontendPort",
    "--log",
    "false"
)

$frontendTunnel = $null
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Seconds 1
    try {
        $frontendResponse = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 2
        $frontendTunnel = $frontendResponse.tunnels | Select-Object -First 1
    } catch {
    }

    if ($null -ne $frontendTunnel) {
        break
    }
}

if ($null -eq $frontendTunnel) {
    throw "ngrok started but the local inspector did not report a frontend tunnel yet. Check the ngrok window."
}

$frontendUrl = $frontendTunnel.public_url
$backendUrl = "$frontendUrl/api"

Write-Host ""
Write-Host "ngrok tunnel is running." -ForegroundColor Green
Write-Host "System URL:   $frontendUrl" -ForegroundColor Cyan
Write-Host "Backend URL:  $backendUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "Phone access:" -ForegroundColor Yellow
Write-Host "  Open the System URL in your phone browser."
Write-Host ""
Write-Host "Teammate backend env:" -ForegroundColor Yellow
Write-Host "  VITE_API_URL=$backendUrl"
Write-Host ""
Write-Host "Notes:" -ForegroundColor Yellow
Write-Host "  This uses the frontend tunnel on port $FrontendPort."
Write-Host "  The API is available through the same public URL plus /api."
Write-Host "  On the current ngrok plan, one public URL is used for both the app and API."
Write-Host ""
