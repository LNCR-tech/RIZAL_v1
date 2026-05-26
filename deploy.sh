#!/usr/bin/env bash
set -Eeuo pipefail

# Production deployment entrypoint. It is designed to be idempotent and safe to
# run from GitHub Actions over SSH or manually on the VPS.

DEPLOY_DIR="${DEPLOY_DIR:-/opt/aura}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-http://18.142.190.113:8001/health}"
ASSISTANT_HEALTHCHECK_URL="${ASSISTANT_HEALTHCHECK_URL:-http://18.142.190.113:8500/health}"
LOCAL_LLM_HEALTHCHECK_URL="${LOCAL_LLM_HEALTHCHECK_URL:-http://127.0.0.1:8091/v1/models}"
BACKUP_DIR="${BACKUP_DIR:-${DEPLOY_DIR}/backups}"
LOCK_FILE="${LOCK_FILE:-/tmp/aura-production-deploy.lock}"
DEPLOY_SCOPE="${DEPLOY_SCOPE:-backend}"
DB_SERVICE="${DB_SERVICE:-db}"
LOCAL_AI_MODEL_FILE="${LOCAL_AI_MODEL_FILE:-jose.gguf}"
LOCAL_AI_MODEL_PATH="${LOCAL_AI_MODEL_PATH:-${DEPLOY_DIR}/${LOCAL_AI_MODEL_FILE}}"

log() {
  printf '[deploy] %s\n' "$*"
}

fail() {
  printf '[deploy] ERROR: %s\n' "$*" >&2
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
  local attempts="${2:-30}"
  local delay="${3:-5}"

  for attempt in $(seq 1 "${attempts}"); do
    if curl -fsS "${url}" >/dev/null; then
      log "health check passed: ${url}"
      return 0
    fi
    log "waiting for health check ${attempt}/${attempts}: ${url}"
    sleep "${delay}"
  done

  return 1
}

wait_for_compose_service() {
  local service="$1"
  local attempts="${2:-30}"
  local delay="${3:-5}"
  local status=""

  for attempt in $(seq 1 "${attempts}"); do
    status="$(compose ps --format json "${service}" 2>/dev/null | grep -o '"Health":"[^"]*"' | head -n 1 | cut -d'"' -f4 || true)"
    if [ "${status}" = "healthy" ]; then
      log "${service} is healthy"
      return 0
    fi
    if [ "${status}" = "unhealthy" ]; then
      log "${service} is unhealthy; recent logs follow"
      compose logs --tail=80 "${service}" || true
      return 1
    fi
    log "waiting for ${service} health ${attempt}/${attempts}: ${status:-starting}"
    sleep "${delay}"
  done

  log "${service} did not become healthy; recent logs follow"
  compose logs --tail=80 "${service}" || true
  return 1
}

exec 9>"${LOCK_FILE}"
if ! flock -n 9; then
  fail "another deployment is already running"
fi

command -v git >/dev/null || fail "git is not installed"
command -v docker >/dev/null || fail "docker is not installed"
docker compose version >/dev/null || fail "docker compose plugin is not installed"

cd "${DEPLOY_DIR}" || fail "DEPLOY_DIR does not exist: ${DEPLOY_DIR}"

if [ ! -f "${ENV_FILE}" ]; then
  fail "${ENV_FILE} is missing. Copy .env.production.example to ${ENV_FILE} and fill in real secrets on the VPS."
fi
apply_legacy_env_defaults

if [ "${DEPLOY_SCOPE}" = "backend-assistant" ] || [ "${DEPLOY_SCOPE}" = "full" ]; then
  if [ ! -f "${LOCAL_AI_MODEL_PATH}" ]; then
    fail "local AI model is missing: ${LOCAL_AI_MODEL_PATH}"
  fi
fi

mkdir -p "${BACKUP_DIR}" .deploy

PREVIOUS_REVISION="$(git rev-parse HEAD)"
printf '%s\n' "${PREVIOUS_REVISION}" > .deploy/previous_revision
log "current revision: ${PREVIOUS_REVISION}"

rollback_on_error() {
  local exit_code=$?
  log "deployment failed; starting automatic rollback to ${PREVIOUS_REVISION}"
  if [ -f "./rollback.sh" ]; then
    if ./rollback.sh "${PREVIOUS_REVISION}"; then
      log "rollback completed"
    else
      log "rollback failed; manual intervention required"
    fi
  else
    log "rollback.sh not found; performing basic git rollback"
    git checkout "${PREVIOUS_REVISION}" || true
  fi
  exit "${exit_code}"
}
trap rollback_on_error ERR

log "fetching ${DEPLOY_BRANCH}"
git fetch origin "${DEPLOY_BRANCH}"
if git show-ref --verify --quiet "refs/heads/${DEPLOY_BRANCH}"; then
  git checkout "${DEPLOY_BRANCH}"
else
  git checkout -b "${DEPLOY_BRANCH}" "origin/${DEPLOY_BRANCH}"
fi
git pull --ff-only origin "${DEPLOY_BRANCH}"
NEW_REVISION="$(git rev-parse HEAD)"
printf '%s\n' "${NEW_REVISION}" > .deploy/current_revision
log "deploying revision: ${NEW_REVISION}"
log "deployment scope: ${DEPLOY_SCOPE}"

log "validating compose configuration"
compose config --quiet

if compose exec -T "${DB_SERVICE}" pg_isready -U "${POSTGRES_USER}" >/dev/null 2>&1; then
  BACKUP_FILE="${BACKUP_DIR}/postgres-$(date -u +%Y%m%dT%H%M%SZ)-${PREVIOUS_REVISION:0:12}.sql.gz"
  log "creating database backup: ${BACKUP_FILE}"
  compose exec -T "${DB_SERVICE}" pg_dumpall -U "${POSTGRES_USER}" | gzip > "${BACKUP_FILE}" || log "WARNING: Database backup failed!"
else
  log "postgres is not running or ready yet; skipping pre-deploy database backup"
fi

log "pulling upstream images where available"
case "${DEPLOY_SCOPE}" in
  backend)
    compose pull --quiet redis || log "redis image pull skipped; existing image will be used"
    ;;
  backend-assistant|full)
    compose pull --quiet redis local-llm || log "redis/local-llm image pull skipped; existing images will be used"
    ;;
esac

log "building updated images"
case "${DEPLOY_SCOPE}" in
  backend)
    compose build --pull migrate
    ;;
  backend-assistant)
    compose build --pull migrate assistant
    ;;
  full)
    compose build --pull "${DB_SERVICE}" migrate assistant frontend
    ;;
  *)
    fail "unsupported DEPLOY_SCOPE: ${DEPLOY_SCOPE}. Use 'backend', 'backend-assistant', or 'full'."
    ;;
esac

log "starting infrastructure"
compose up -d "${DB_SERVICE}" redis
wait_for_compose_service "${DB_SERVICE}" 36 5
if [ "${DEPLOY_SCOPE}" = "backend-assistant" ] || [ "${DEPLOY_SCOPE}" = "full" ]; then
  log "starting local LLM"
  compose up -d local-llm
  wait_for_health "${LOCAL_LLM_HEALTHCHECK_URL}" 36 5
fi

log "running migrations and bootstrap"
compose up --abort-on-container-exit --exit-code-from migrate migrate
compose up --abort-on-container-exit --exit-code-from bootstrap bootstrap

log "restarting changed application containers"
# --force-recreate is required: without it, `compose up -d` sometimes keeps
# the old container alive when only the image content changed (image tag
# stays as aura-backend:prod). The result was deploys that "succeeded"
# while the live backend kept serving pre-fix code for ~50 minutes
# (2026-05-26 token-500 incident). Force-recreate guarantees the freshly
# built image actually runs.
case "${DEPLOY_SCOPE}" in
  backend)
    compose up -d --force-recreate --no-deps backend worker beat
    ;;
  backend-assistant)
    compose up -d --force-recreate --no-deps backend worker beat
    compose up -d --force-recreate --no-deps assistant
    ;;
  full)
    compose up -d --force-recreate --remove-orphans backend worker beat assistant frontend
    ;;
esac

log "waiting for Docker health checks"
compose ps

log "verifying public backend health"
wait_for_health "${HEALTHCHECK_URL}" 36 5
if [ "${DEPLOY_SCOPE}" = "backend-assistant" ] || [ "${DEPLOY_SCOPE}" = "full" ]; then
  log "verifying public assistant health"
  wait_for_health "${ASSISTANT_HEALTHCHECK_URL}" 36 5
fi

log "pruning dangling images older than 24 hours"
docker image prune -f --filter "until=24h" >/dev/null

trap - ERR
log "deployment complete: ${NEW_REVISION}"
