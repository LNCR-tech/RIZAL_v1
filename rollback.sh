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
ASSISTANT_HEALTHCHECK_URL="${ASSISTANT_HEALTHCHECK_URL:-http://18.142.190.113:8500/health}"
LOCAL_LLM_HEALTHCHECK_URL="${LOCAL_LLM_HEALTHCHECK_URL:-http://127.0.0.1:8091/v1/models}"
LOG_DIR="${LOG_DIR:-${DEPLOY_DIR}/.deploy/logs}"
DEPLOY_SCOPE="${DEPLOY_SCOPE:-backend}"
DB_SERVICE="${DB_SERVICE:-db}"

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

env_file_value() {
  local key="$1"
  grep -E "^${key}=" "${ENV_FILE}" | tail -n 1 | cut -d= -f2- || true
}

apply_legacy_env_defaults() {
  local db_user_value
  local db_password_value
  local db_name_value
  local postgres_user_value
  local postgres_password_value
  local postgres_db_value
  local database_url_value

  db_user_value="$(env_file_value DB_USER)"
  db_password_value="$(env_file_value DB_PASSWORD)"
  db_name_value="$(env_file_value DB_NAME)"
  postgres_user_value="$(env_file_value POSTGRES_USER)"
  postgres_password_value="$(env_file_value POSTGRES_PASSWORD)"
  postgres_db_value="$(env_file_value POSTGRES_DB)"
  database_url_value="$(env_file_value DATABASE_URL)"

  export POSTGRES_USER="${POSTGRES_USER:-${postgres_user_value:-${db_user_value:-postgres}}}"
  export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-${postgres_password_value:-${db_password_value:-postgres}}}"
  export POSTGRES_DB="${POSTGRES_DB:-${postgres_db_value:-${db_name_value:-fastapi_db}}}"
  export DATABASE_URL="${DATABASE_URL:-${database_url_value:-postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${DB_SERVICE}:5432/${POSTGRES_DB}}}"
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
mkdir -p "${LOG_DIR}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/rollback-$(date -u +%Y%m%dT%H%M%SZ).log}"
exec > >(tee -a "${LOG_FILE}") 2>&1
log "writing rollback log to ${LOG_FILE}"

if [ -z "${TARGET_REVISION}" ] && [ -f .deploy/previous_revision ]; then
  TARGET_REVISION="$(cat .deploy/previous_revision)"
fi

[ -n "${TARGET_REVISION}" ] || fail "target revision is required"
[ -f "${ENV_FILE}" ] || fail "${ENV_FILE} is missing"
apply_legacy_env_defaults

log "rolling back to ${TARGET_REVISION}"
git fetch --all --prune
git checkout --detach "${TARGET_REVISION}"

log "validating compose configuration"
compose config --quiet

log "rebuilding images for rollback revision"
case "${DEPLOY_SCOPE}" in
  backend)
    compose build migrate
    ;;
  backend-assistant)
    compose build migrate assistant
    ;;
  full)
    compose build
    ;;
  *)
    fail "unsupported DEPLOY_SCOPE: ${DEPLOY_SCOPE}. Use 'backend', 'backend-assistant', or 'full'."
    ;;
esac

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
    compose up -d --force-recreate --remove-orphans ${svc_list}
  fi
}

run_svc() {
  for svc in "$@"; do
    if echo "$SERVICES" | grep -q "^${svc}$"; then
      compose up --abort-on-container-exit --exit-code-from "$svc" "$svc"
    fi
  done
}

start_svc "${DB_SERVICE}" redis
run_svc migrate bootstrap
case "${DEPLOY_SCOPE}" in
  backend)
    start_svc backend worker beat
    ;;
  backend-assistant)
    start_svc local-llm
    wait_for_health "${LOCAL_LLM_HEALTHCHECK_URL}"
    start_svc backend worker beat assistant
    ;;
  full)
    start_svc local-llm
    wait_for_health "${LOCAL_LLM_HEALTHCHECK_URL}"
    start_svc backend worker beat assistant frontend
    ;;
esac

wait_for_health "${HEALTHCHECK_URL}"
if [ "${DEPLOY_SCOPE}" = "backend-assistant" ] || [ "${DEPLOY_SCOPE}" = "full" ]; then
  wait_for_health "${ASSISTANT_HEALTHCHECK_URL}"
fi
log "rollback complete: ${TARGET_REVISION}"
