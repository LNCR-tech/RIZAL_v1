#!/usr/bin/env bash
set -Eeuo pipefail

# Roll back application containers to a previous git revision. Database
# downgrades are intentionally not automatic; use the backup created by
# deploy.sh when a schema rollback is required.

TARGET_REVISION="${1:-}"
DEPLOY_DIR="${DEPLOY_DIR:-/opt/aura}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-http://18.142.190.113:8001/health}"

log() {
  printf '[rollback] %s\n' "$*"
}

fail() {
  printf '[rollback] ERROR: %s\n' "$*" >&2
  exit 1
}

compose() {
  docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" "$@"
}

wait_for_health() {
  local url="$1"
  for attempt in $(seq 1 36); do
    if curl -fsS "${url}" >/dev/null; then
      log "health check passed: ${url}"
      return 0
    fi
    log "waiting for health check ${attempt}/36: ${url}"
    sleep 5
  done
  return 1
}

cd "${DEPLOY_DIR}" || fail "DEPLOY_DIR does not exist: ${DEPLOY_DIR}"

if [ -z "${TARGET_REVISION}" ] && [ -f .deploy/previous_revision ]; then
  TARGET_REVISION="$(cat .deploy/previous_revision)"
fi

[ -n "${TARGET_REVISION}" ] || fail "target revision is required"
[ -f "${ENV_FILE}" ] || fail "${ENV_FILE} is missing"

log "rolling back to ${TARGET_REVISION}"
git fetch --all --prune
git checkout --detach "${TARGET_REVISION}"

log "validating compose configuration"
compose config --quiet

log "rebuilding images for rollback revision"
compose build

log "restarting application services"
SERVICES=$(compose config --services)

start_svc() {
  local svc_list=""
  for svc in "$@"; do
    if echo "$SERVICES" | grep -q "^${svc}$"; then
      svc_list="${svc_list} ${svc}"
    fi
  done
  if [ -n "${svc_list}" ]; then
    compose up -d --remove-orphans ${svc_list}
  fi
}

run_svc() {
  for svc in "$@"; do
    if echo "$SERVICES" | grep -q "^${svc}$"; then
      compose up --abort-on-container-exit --exit-code-from "$svc" "$svc"
    fi
  done
}

start_svc postgres redis
run_svc migrate bootstrap
start_svc backend worker beat assistant frontend

wait_for_health "${HEALTHCHECK_URL}"
log "rollback complete: ${TARGET_REVISION}"
