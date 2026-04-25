#!/usr/bin/env bash
# =============================================================================
# Aura — Production Stack Manager
# =============================================================================
# Usage:
#   chmod +x start.sh
#   ./start.sh            — start (or restart) the full stack
#   ./start.sh stop       — stop all services
#   ./start.sh restart    — stop then start
#   ./start.sh update     — pull latest code and rebuild
#   ./start.sh logs       — follow all logs
#   ./start.sh logs <svc> — follow logs for one service (e.g. backend)
#   ./start.sh status     — show running containers
#   ./start.sh reset      — stop and wipe all volumes (DELETES DATABASE)
# =============================================================================

set -euo pipefail

COMPOSE_FILE="docker-compose.prod.yml"
COMPOSE="docker compose -f $COMPOSE_FILE"

# -----------------------------------------------------------------------------
# Colors
# -----------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${GREEN}[aura]${NC} $*"; }
warn()    { echo -e "${YELLOW}[warn]${NC} $*"; }
error()   { echo -e "${RED}[error]${NC} $*"; exit 1; }
section() { echo -e "\n${CYAN}==> $*${NC}"; }

# -----------------------------------------------------------------------------
# Guards
# -----------------------------------------------------------------------------
[ -f "$COMPOSE_FILE" ] || error "Run this script from the repo root (docker-compose.prod.yml not found)."
[ -f ".env" ]          || error ".env not found. Run ./deploy.sh first to configure the environment."

CMD="${1:-start}"

# -----------------------------------------------------------------------------
# Commands
# -----------------------------------------------------------------------------
do_start() {
    section "Starting Aura production stack..."

    # 1. Pull images that don't need building (postgres, redis)
    info "Pulling base images..."
    $COMPOSE pull db redis

    # 2. Build app images
    info "Building app images..."
    $COMPOSE build --parallel backend assistant frontend

    # 3. Start infrastructure first and wait for healthy DB
    info "Starting database and redis..."
    $COMPOSE up -d db redis

    info "Waiting for database to be healthy..."
    until $COMPOSE exec -T db pg_isready -U "${DB_USER:-postgres}" -d "${DB_NAME:-fastapi_db}" &>/dev/null; do
        echo -n "."
        sleep 2
    done
    echo ""
    info "Database is ready."

    # 4. Run migrations
    info "Running migrations..."
    $COMPOSE run --rm migrate

    # 5. Run bootstrap
    info "Running bootstrap..."
    $COMPOSE run --rm bootstrap

    # 6. Start all app services
    info "Starting backend, worker, beat, assistant, frontend..."
    $COMPOSE up -d backend worker beat assistant frontend

    # 7. Print status
    echo ""
    $COMPOSE ps
    echo ""

    PUBLIC_IP=$(curl -sf https://checkip.amazonaws.com 2>/dev/null || hostname -I | awk '{print $1}')
    info "Stack is up."
    echo "  Frontend:      http://${PUBLIC_IP}"
    echo "  Backend API:   http://${PUBLIC_IP}:8000/docs"
    echo "  Assistant API: http://${PUBLIC_IP}:8500/docs"
    echo ""
    info "Follow logs: ./start.sh logs"
}

do_stop() {
    section "Stopping Aura production stack..."
    $COMPOSE down
    info "Stack stopped."
}

do_restart() {
    do_stop
    do_start
}

do_update() {
    section "Pulling latest code..."
    git fetch origin
    git pull --rebase origin "$(git rev-parse --abbrev-ref HEAD)"
    info "Code updated. Rebuilding and restarting..."
    do_stop
    do_start
}

do_logs() {
    local svc="${2:-}"
    if [ -n "$svc" ]; then
        $COMPOSE logs -f "$svc"
    else
        $COMPOSE logs -f
    fi
}

do_status() {
    $COMPOSE ps
}

do_reset() {
    echo ""
    warn "WARNING: This will stop all services and DELETE all data including the database."
    read -rp "  Type YES to confirm: " confirm
    [[ "$confirm" == "YES" ]] || { info "Aborted."; exit 0; }
    section "Wiping stack and volumes..."
    $COMPOSE down -v
    info "Done. Run ./start.sh to start fresh."
}

# -----------------------------------------------------------------------------
# Dispatch
# -----------------------------------------------------------------------------
case "$CMD" in
    start)          do_start ;;
    stop)           do_stop ;;
    restart)        do_restart ;;
    update)         do_update ;;
    logs)           do_logs "$@" ;;
    status)         do_status ;;
    reset)          do_reset ;;
    *)              error "Unknown command: $CMD. Usage: ./start.sh [start|stop|restart|update|logs|status|reset]" ;;
esac
