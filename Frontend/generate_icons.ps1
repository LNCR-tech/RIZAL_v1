Add-Type -AssemblyName System.Drawing

$preferredSource = Join-Path $PSScriptRoot "public\logos\apk_icon.png"
$fallbackSource = Join-Path $PSScriptRoot "public\logos\aura.png"
$source = if (Test-Path $preferredSource) { $preferredSource } else { $fallbackSource }
$resBase = Join-Path $PSScriptRoot "aura-apk\android\app\src\main\res"
$img = [System.Drawing.Image]::FromFile($source)
$legacyIconInsetRatio = 0.10
$adaptiveForegroundInsetRatio = 0.18
Write-Host "Source: $($img.Width)x$($img.Height)"

function Resize-Image($srcImg, $width, $height, $outFile) {
    $bmp = New-Object System.Drawing.Bitmap($width, $height)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $g.DrawImage($srcImg, 0, 0, $width, $height)
    $g.Dispose()
    $bmp.Save($outFile, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
}

function New-BitmapGraphics($width, $height) {
    $bmp = New-Object System.Drawing.Bitmap($width, $height, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    return @{
        Bitmap = $bmp
        Graphics = $g
    }
}

function Draw-ContainedImage($srcImg, $canvasWidth, $canvasHeight, $outFile, $insetRatio, $backgroundColor) {
    $drawing = New-BitmapGraphics $canvasWidth $canvasHeight
    $bmp = $drawing.Bitmap
    $g = $drawing.Graphics

    if ($null -eq $backgroundColor) {
        $g.Clear([System.Drawing.Color]::Transparent)
    } else {
        $g.Clear($backgroundColor)
    }

    $insetX = [math]::Round($canvasWidth * $insetRatio)
    $insetY = [math]::Round($canvasHeight * $insetRatio)
    $availableWidth = [math]::Max(1, $canvasWidth - (2 * $insetX))
    $availableHeight = [math]::Max(1, $canvasHeight - (2 * $insetY))
    $scale = [math]::Min($availableWidth / $srcImg.Width, $availableHeight / $srcImg.Height)
    $drawWidth = [math]::Max(1, [math]::Round($srcImg.Width * $scale))
    $drawHeight = [math]::Max(1, [math]::Round($srcImg.Height * $scale))
    $drawX = [math]::Round(($canvasWidth - $drawWidth) / 2)
    $drawY = [math]::Round(($canvasHeight - $drawHeight) / 2)

    $g.DrawImage($srcImg, $drawX, $drawY, $drawWidth, $drawHeight)
    $g.Dispose()
    $bmp.Save($outFile, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
}

$densities = @(
    @{ name="mipmap-mdpi";    icon=48;  fg=108 },
    @{ name="mipmap-hdpi";    icon=72;  fg=162 },
    @{ name="mipmap-xhdpi";   icon=96;  fg=216 },
    @{ name="mipmap-xxhdpi";  icon=144; fg=324 },
    @{ name="mipmap-xxxhdpi"; icon=192; fg=432 }
)

foreach ($d in $densities) {
    $dir = Join-Path $resBase $d.name
    $s = $d.icon
    $fg = $d.fg
    
    Draw-ContainedImage $img $s $s (Join-Path $dir "ic_launcher.png") $legacyIconInsetRatio ([System.Drawing.Color]::Black)
    Draw-ContainedImage $img $s $s (Join-Path $dir "ic_launcher_round.png") $legacyIconInsetRatio ([System.Drawing.Color]::Black)
    Draw-ContainedImage $img $fg $fg (Join-Path $dir "ic_launcher_foreground.png") $adaptiveForegroundInsetRatio $null
    
    Write-Host "OK: $($d.name) - icon:${s}x${s}, fg:${fg}x${fg}"
}

Resize-Image $img 192 192 (Join-Path $PSScriptRoot "public\pwa-192.png")
Resize-Image $img 512 512 (Join-Path $PSScriptRoot "public\pwa-512.png")
Resize-Image $img 512 512 (Join-Path $PSScriptRoot "public\pwa-maskable-512.png")
Write-Host "OK: web PWA icons regenerated"

$img.Dispose()
Write-Host "All Aura icons generated!"
