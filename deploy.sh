#!/usr/bin/env bash
# =============================================================================
# Aura — AWS Ubuntu Deployment Script
# =============================================================================
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh
#
# What this does:
#   1. Installs Docker and Docker Compose plugin if not present
#   2. Clones the repo (or pulls latest if already cloned)
#   3. Creates .env from .env.production.example if it doesn't exist
#   4. Prompts for required secrets
#   5. Runs docker compose -f docker-compose.prod.yml up --build -d
#
# Requirements:
#   - Ubuntu 22.04+ (tested on AWS EC2 Ubuntu AMI)
#   - sudo access
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Config — override via environment variables before running
# -----------------------------------------------------------------------------
REPO_URL="${REPO_URL:-https://github.com/LNCR-tech/RIZAL_v1.git}"
REPO_BRANCH="${REPO_BRANCH:-Pre-Production-v1}"
DEPLOY_DIR="${DEPLOY_DIR:-/opt/aura}"
COMPOSE_FILE="docker-compose.prod.yml"

# -----------------------------------------------------------------------------
# Colors
# -----------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[aura]${NC} $*"; }
warn()  { echo -e "${YELLOW}[warn]${NC} $*"; }
error() { echo -e "${RED}[error]${NC} $*"; exit 1; }

# -----------------------------------------------------------------------------
# 1. Install dependencies
# -----------------------------------------------------------------------------
info "Checking dependencies..."

if ! command -v git &>/dev/null; then
    info "Installing git..."
    sudo apt-get update -qq && sudo apt-get install -y -qq git
fi

if ! command -v docker &>/dev/null; then
    info "Installing Docker..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker "$USER"
    warn "Docker installed. You may need to log out and back in for group changes."
    warn "If the next steps fail with permission errors, run: newgrp docker"
fi

if ! docker compose version &>/dev/null; then
    info "Installing Docker Compose plugin..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-compose-plugin
fi

info "Docker: $(docker --version)"
info "Docker Compose: $(docker compose version)"

# -----------------------------------------------------------------------------
# 2. Clone or update repo
# -----------------------------------------------------------------------------
if [ -d "$DEPLOY_DIR/.git" ]; then
    info "Repo already exists at $DEPLOY_DIR — pulling latest..."
    cd "$DEPLOY_DIR"
    git fetch origin
    git checkout "$REPO_BRANCH"
    git pull origin "$REPO_BRANCH"
else
    info "Cloning repo to $DEPLOY_DIR..."
    sudo mkdir -p "$DEPLOY_DIR"
    sudo chown "$USER":"$USER" "$DEPLOY_DIR"
    git clone --branch "$REPO_BRANCH" "$REPO_URL" "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
fi

cd "$DEPLOY_DIR"

# -----------------------------------------------------------------------------
# 3. Set up .env
# -----------------------------------------------------------------------------
if [ ! -f .env ]; then
    info "Creating .env from .env.production.example..."
    cp .env.production.example .env

    echo ""
    warn "Fill in required values. Press Enter to skip optional ones."
    echo ""

    prompt() {
        local key="$1" label="$2" required="${3:-false}"
        read -rp "  $label: " val
        if [[ -z "$val" && "$required" == "true" ]]; then
            error "$key is required and cannot be empty."
        fi
        [[ -n "$val" ]] && sed -i "s|^${key}=.*|${key}=${val}|" .env
    }

    prompt SECRET_KEY        "SECRET_KEY (run: openssl rand -hex 32)" true
    prompt DB_PASSWORD        "DB_PASSWORD" true
    prompt AI_API_KEY         "AI_API_KEY" true
    prompt AI_API_BASE        "AI_API_BASE (e.g. https://api.openai.com/v1)" true
    prompt AI_MODEL           "AI_MODEL (e.g. gpt-4o)" true

    echo ""
    # Detect public IP for URL defaults
    PUBLIC_IP=$(curl -sf https://checkip.amazonaws.com || hostname -I | awk '{print $1}')
    warn "Detected public IP: $PUBLIC_IP"
    warn "If you have a domain, use that instead."
    echo ""

    read -rp "  Frontend public URL (default: http://${PUBLIC_IP}): " FRONTEND_URL
    FRONTEND_URL="${FRONTEND_URL:-http://${PUBLIC_IP}}"

    read -rp "  Backend public URL (default: http://${PUBLIC_IP}:8000): " BACKEND_URL
    BACKEND_URL="${BACKEND_URL:-http://${PUBLIC_IP}:8000}"

    sed -i "s|^LOGIN_URL=.*|LOGIN_URL=${FRONTEND_URL}|" .env
    sed -i "s|^CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=${FRONTEND_URL}|" .env
    sed -i "s|^BACKEND_ORIGIN=.*|BACKEND_ORIGIN=${BACKEND_URL}|" .env
    sed -i "s|^BACKEND_API_BASE_URL=.*|BACKEND_API_BASE_URL=${BACKEND_URL}|" .env

    echo ""
    read -rp "  Enable email? (y/N): " ENABLE_EMAIL
    if [[ "${ENABLE_EMAIL,,}" == "y" ]]; then
        prompt MAILJET_API_KEY    "MAILJET_API_KEY" true
        prompt MAILJET_API_SECRET "MAILJET_API_SECRET" true
        sed -i "s|^EMAIL_TRANSPORT=.*|EMAIL_TRANSPORT=mailjet_api|" .env
    fi

    info ".env configured."
else
    warn ".env already exists — skipping configuration. Edit it manually if needed."
fi

# -----------------------------------------------------------------------------
# 4. Open firewall ports (ufw)
# -----------------------------------------------------------------------------
if command -v ufw &>/dev/null && sudo ufw status | grep -q "Status: active"; then
    info "Opening firewall ports 80, 8000, 8500..."
    sudo ufw allow 80/tcp
    sudo ufw allow 8000/tcp
    sudo ufw allow 8500/tcp
fi

# -----------------------------------------------------------------------------
# 5. Build and start the stack
# -----------------------------------------------------------------------------
info "Building and starting Aura production stack..."
docker compose -f "$COMPOSE_FILE" up --build -d

echo ""
info "Stack is starting. Migrations and bootstrap run automatically."
info "Follow logs:  docker compose -f $COMPOSE_FILE logs -f"
info "Stop stack:   docker compose -f $COMPOSE_FILE down"
echo ""

PUBLIC_IP=$(curl -sf https://checkip.amazonaws.com || hostname -I | awk '{print $1}')
info "Once ready:"
echo "  Frontend:      http://${PUBLIC_IP}"
echo "  Backend API:   http://${PUBLIC_IP}:8000/docs"
echo "  Assistant API: http://${PUBLIC_IP}:8500/docs"
echo ""
warn "Remember to configure your AWS Security Group to allow inbound TCP on ports 80, 8000, and 8500."
