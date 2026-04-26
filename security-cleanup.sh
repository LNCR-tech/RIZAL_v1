#!/usr/bin/env bash
# =============================================================================
# Aura Security Cleanup Script
# =============================================================================
# This script removes sensitive files and prepares the repository for
# secure deployment by cleaning up exposed credentials and demo data.
#
# Usage:
#   chmod +x security-cleanup.sh
#   ./security-cleanup.sh
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${GREEN}[security]${NC} $*"; }
warn()    { echo -e "${YELLOW}[warning]${NC} $*"; }
error()   { echo -e "${RED}[error]${NC} $*"; }
section() { echo -e "\n${CYAN}==> $*${NC}"; }

section "Aura Security Cleanup"
echo ""
warn "This script will remove sensitive files and exposed credentials."
warn "Make sure you have backed up any data you need before proceeding."
echo ""
read -rp "Continue? (yes/no): " confirm

if [[ "$confirm" != "yes" ]]; then
    info "Cleanup cancelled."
    exit 0
fi

# =============================================================================
# 1. Remove exposed .env file
# =============================================================================
section "Removing exposed .env file..."

if [ -f .env ]; then
    info "Backing up current .env to .env.backup.$(date +%Y%m%d_%H%M%S)"
    cp .env ".env.backup.$(date +%Y%m%d_%H%M%S)"
    rm .env
    info ".env removed"
else
    info ".env not found (already removed)"
fi

# =============================================================================
# 2. Remove seed credentials
# =============================================================================
section "Removing seed credentials..."

if [ -f Backend/storage/seed_credentials.csv ]; then
    rm Backend/storage/seed_credentials.csv
    info "Backend/storage/seed_credentials.csv removed"
else
    info "seed_credentials.csv not found (already removed)"
fi

if [ -f Backend/storage/seed_credentials.json ]; then
    rm Backend/storage/seed_credentials.json
    info "Backend/storage/seed_credentials.json removed"
else
    info "seed_credentials.json not found (already removed)"
fi

# =============================================================================
# 3. Update .gitignore
# =============================================================================
section "Updating .gitignore..."

if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
    info "Added .env to .gitignore"
else
    info ".env already in .gitignore"
fi

if ! grep -q "^\.env\.backup\." .gitignore 2>/dev/null; then
    echo ".env.backup.*" >> .gitignore
    info "Added .env.backup.* to .gitignore"
fi

# =============================================================================
# 4. Create secure .env template
# =============================================================================
section "Creating secure .env from template..."

if [ -f .env.secure.example ]; then
    cp .env.secure.example .env
    info "Created .env from .env.secure.example"
    warn "IMPORTANT: Edit .env and replace ALL placeholder values with real credentials"
else
    error ".env.secure.example not found. Please create it first."
    exit 1
fi

# =============================================================================
# 5. Check for other sensitive files
# =============================================================================
section "Checking for other sensitive files..."

sensitive_patterns=(
    "*.pem"
    "*.key"
    "*_rsa"
    "*.p12"
    "*.pfx"
    "id_rsa*"
    "*.crt"
)

found_sensitive=false
for pattern in "${sensitive_patterns[@]}"; do
    if find . -name "$pattern" -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | grep -q .; then
        warn "Found files matching pattern: $pattern"
        find . -name "$pattern" -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null
        found_sensitive=true
    fi
done

if [ "$found_sensitive" = false ]; then
    info "No additional sensitive files found"
fi

# =============================================================================
# 6. Generate helper commands for new credentials
# =============================================================================
section "Credential generation commands..."

echo ""
info "Use these commands to generate secure credentials:"
echo ""
echo "  SECRET_KEY (copy to .env):"
echo "    openssl rand -hex 32"
echo ""
echo "  DB_PASSWORD (copy to .env):"
echo "    openssl rand -base64 32"
echo ""
echo "  PGADMIN_PASSWORD (copy to .env):"
echo "    openssl rand -base64 24"
echo ""
echo "  ADMIN_PASSWORD (set as environment variable):"
echo "    export ADMIN_PASSWORD=\"\$(openssl rand -base64 16)\""
echo ""

# =============================================================================
# 7. Summary
# =============================================================================
section "Cleanup Summary"

echo ""
info "✅ Removed exposed .env file"
info "✅ Removed seed credentials"
info "✅ Updated .gitignore"
info "✅ Created new .env from secure template"
echo ""
warn "NEXT STEPS:"
echo "  1. Edit .env and replace ALL placeholder values"
echo "  2. Revoke exposed API keys:"
echo "     - SiliconFlow AI API Key"
echo "     - Mailjet API Key and Secret"
echo "  3. Generate new API keys from providers"
echo "  4. Set ADMIN_EMAIL and ADMIN_PASSWORD environment variables"
echo "  5. Review SECURITY_CHECKLIST.md for complete deployment guide"
echo ""
warn "DO NOT commit .env to git!"
echo ""
