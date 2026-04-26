# =============================================================================
# Aura Security Cleanup Script (PowerShell)
# =============================================================================
# This script removes sensitive files and prepares the repository for
# secure deployment by cleaning up exposed credentials and demo data.
#
# Usage:
#   .\security-cleanup.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[security] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[warning] $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[error] $Message" -ForegroundColor Red
}

function Write-Section {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

Write-Section "Aura Security Cleanup"
Write-Host ""
Write-Warn "This script will remove sensitive files and exposed credentials."
Write-Warn "Make sure you have backed up any data you need before proceeding."
Write-Host ""

$confirm = Read-Host "Continue? (yes/no)"

if ($confirm -ne "yes") {
    Write-Info "Cleanup cancelled."
    exit 0
}

# =============================================================================
# 1. Remove exposed .env file
# =============================================================================
Write-Section "Removing exposed .env file..."

if (Test-Path ".env") {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupName = ".env.backup.$timestamp"
    Write-Info "Backing up current .env to $backupName"
    Copy-Item ".env" $backupName
    Remove-Item ".env"
    Write-Info ".env removed"
} else {
    Write-Info ".env not found (already removed)"
}

# =============================================================================
# 2. Remove seed credentials
# =============================================================================
Write-Section "Removing seed credentials..."

if (Test-Path "Backend\storage\seed_credentials.csv") {
    Remove-Item "Backend\storage\seed_credentials.csv"
    Write-Info "Backend\storage\seed_credentials.csv removed"
} else {
    Write-Info "seed_credentials.csv not found (already removed)"
}

if (Test-Path "Backend\storage\seed_credentials.json") {
    Remove-Item "Backend\storage\seed_credentials.json"
    Write-Info "Backend\storage\seed_credentials.json removed"
} else {
    Write-Info "seed_credentials.json not found (already removed)"
}

# =============================================================================
# 3. Update .gitignore
# =============================================================================
Write-Section "Updating .gitignore..."

$gitignoreContent = Get-Content ".gitignore" -ErrorAction SilentlyContinue

if ($gitignoreContent -notcontains ".env") {
    Add-Content ".gitignore" ".env"
    Write-Info "Added .env to .gitignore"
} else {
    Write-Info ".env already in .gitignore"
}

if ($gitignoreContent -notcontains ".env.backup.*") {
    Add-Content ".gitignore" ".env.backup.*"
    Write-Info "Added .env.backup.* to .gitignore"
}

# =============================================================================
# 4. Create secure .env template
# =============================================================================
Write-Section "Creating secure .env from template..."

if (Test-Path ".env.secure.example") {
    Copy-Item ".env.secure.example" ".env"
    Write-Info "Created .env from .env.secure.example"
    Write-Warn "IMPORTANT: Edit .env and replace ALL placeholder values with real credentials"
} else {
    Write-Error-Custom ".env.secure.example not found. Please create it first."
    exit 1
}

# =============================================================================
# 5. Check for other sensitive files
# =============================================================================
Write-Section "Checking for other sensitive files..."

$sensitivePatterns = @(
    "*.pem",
    "*.key",
    "*_rsa",
    "*.p12",
    "*.pfx",
    "id_rsa*",
    "*.crt"
)

$foundSensitive = $false
foreach ($pattern in $sensitivePatterns) {
    $files = Get-ChildItem -Path . -Filter $pattern -Recurse -ErrorAction SilentlyContinue |
             Where-Object { $_.FullName -notmatch "node_modules|\.git" }
    
    if ($files) {
        Write-Warn "Found files matching pattern: $pattern"
        $files | ForEach-Object { Write-Host "  $($_.FullName)" }
        $foundSensitive = $true
    }
}

if (-not $foundSensitive) {
    Write-Info "No additional sensitive files found"
}

# =============================================================================
# 6. Generate helper commands for new credentials
# =============================================================================
Write-Section "Credential generation commands..."

Write-Host ""
Write-Info "Use these PowerShell commands to generate secure credentials:"
Write-Host ""
Write-Host "  SECRET_KEY (copy to .env):"
Write-Host "    -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]`$_})"
Write-Host ""
Write-Host "  DB_PASSWORD (copy to .env):"
Write-Host "    -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]`$_})"
Write-Host ""
Write-Host "  PGADMIN_PASSWORD (copy to .env):"
Write-Host "    -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 24 | ForEach-Object {[char]`$_})"
Write-Host ""
Write-Host "  ADMIN_PASSWORD (set as environment variable):"
Write-Host "    `$env:ADMIN_PASSWORD = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 16 | ForEach-Object {[char]`$_})"
Write-Host ""

# =============================================================================
# 7. Summary
# =============================================================================
Write-Section "Cleanup Summary"

Write-Host ""
Write-Info "✅ Removed exposed .env file"
Write-Info "✅ Removed seed credentials"
Write-Info "✅ Updated .gitignore"
Write-Info "✅ Created new .env from secure template"
Write-Host ""
Write-Warn "NEXT STEPS:"
Write-Host "  1. Edit .env and replace ALL placeholder values"
Write-Host "  2. Revoke exposed API keys:"
Write-Host "     - SiliconFlow AI API Key"
Write-Host "     - Mailjet API Key and Secret"
Write-Host "  3. Generate new API keys from providers"
Write-Host "  4. Set ADMIN_EMAIL and ADMIN_PASSWORD environment variables"
Write-Host "  5. Review SECURITY_CHECKLIST.md for complete deployment guide"
Write-Host ""
Write-Warn "DO NOT commit .env to git!"
Write-Host ""
