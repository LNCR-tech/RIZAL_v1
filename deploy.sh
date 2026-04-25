#!/usr/bin/env bash
# =============================================================================
# Aura — Linux Deployment Script
# =============================================================================
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh
#
# What this does:
#   1. Installs Docker and Docker Compose plugin if not present
#   2. Clones the repo (or pulls latest if already cloned)
#   3. Creates .env from .env.example if it doesn't exist
#   4. Prompts for required secrets
#   5. Runs docker compose up --build -d
#
# Requirements:
#   - Ubuntu 22.04+ or Debian 12+ (or any distro with apt)
#   - sudo access
#   - Git installed (or will be installed)
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Config — edit these before running or pass as env vars
# -----------------------------------------------------------------------------
REPO_URL="${REPO_URL:-https://github.com/LNCR-tech/RIZAL_v1.git}"
REPO_BRANCH="${REPO_BRANCH:-integrate/pilot-merge}"
DEPLOY_DIR="${DEPLOY_DIR:-/opt/aura}"

# -----------------------------------------------------------------------------
# Colors
# -----------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${GREEN}[aura]${NC} $*"; }
warn()    { echo -e "${YELLOW}[warn]${NC} $*"; }
error()   { echo -e "${RED}[error]${NC} $*"; exit 1; }

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
    warn "Docker installed. You may need to log out and back in for group changes to take effect."
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
    info "Creating .env from .env.example..."
    cp .env.example .env

    echo ""
    warn "Required secrets — these must be set before the stack will work."
    echo ""

    read -rp "  SECRET_KEY (long random string): " SECRET_KEY_VAL
    read -rp "  AI_API_KEY: " AI_API_KEY_VAL
    read -rp "  AI_API_BASE (e.g. https://api.openai.com/v1): " AI_API_BASE_VAL
    read -rp "  AI_MODEL (e.g. gpt-4o): " AI_MODEL_VAL
    read -rp "  FRONTEND_PORT (default 80): " FRONTEND_PORT_VAL
    FRONTEND_PORT_VAL="${FRONTEND_PORT_VAL:-80}"

    sed -i "s|SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY_VAL}|" .env
    sed -i "s|AI_API_KEY=.*|AI_API_KEY=${AI_API_KEY_VAL}|" .env
    sed -i "s|AI_API_BASE=.*|AI_API_BASE=${AI_API_BASE_VAL}|" .env
    sed -i "s|AI_MODEL=.*|AI_MODEL=${AI_MODEL_VAL}|" .env
    sed -i "s|FRONTEND_PORT=.*|FRONTEND_PORT=${FRONTEND_PORT_VAL}|" .env

    echo ""
    read -rp "  Enable email? (y/N): " ENABLE_EMAIL
    if [[ "${ENABLE_EMAIL,,}" == "y" ]]; then
        read -rp "  MAILJET_API_KEY: " MAILJET_KEY_VAL
        read -rp "  MAILJET_API_SECRET: " MAILJET_SECRET_VAL
        sed -i "s|EMAIL_TRANSPORT=.*|EMAIL_TRANSPORT=mailjet_api|" .env
        sed -i "s|MAILJET_API_KEY=.*|MAILJET_API_KEY=${MAILJET_KEY_VAL}|" .env
        sed -i "s|MAILJET_API_SECRET=.*|MAILJET_API_SECRET=${MAILJET_SECRET_VAL}|" .env
    fi

    info ".env configured."
else
    warn ".env already exists — skipping configuration. Edit it manually if needed."
fi

# -----------------------------------------------------------------------------
# 4. Start the stack
# -----------------------------------------------------------------------------
info "Starting Aura stack..."
docker compose up --build -d

echo ""
info "Stack is starting. Migrations and bootstrap run automatically."
info "Follow logs with: docker compose logs -f"
echo ""
info "Once ready:"
echo "  Frontend:        http://$(hostname -I | awk '{print $1}'):$(grep FRONTEND_PORT .env | cut -d= -f2)"
echo "  Backend API:     http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "  Assistant API:   http://$(hostname -I | awk '{print $1}'):8500/docs"
echo "  pgAdmin:         http://$(hostname -I | awk '{print $1}'):5050"
echo "  Mailpit:         http://$(hostname -I | awk '{print $1}'):8025"
echo ""
