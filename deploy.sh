#!/usr/bin/env bash
set -Eeuo pipefail

# Production deployment entrypoint. It is designed to be idempotent and safe to
# run from GitHub Actions over SSH or manually on the VPS.

DEPLOY_DIR="${DEPLOY_DIR:-/opt/aura}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.production}"
HEALTHCHECK_URL="${HEALTHCHECK_URL:-http://18.142.190.113:8001/health}"
BACKUP_DIR="${BACKUP_DIR:-${DEPLOY_DIR}/backups}"
LOCK_FILE="${LOCK_FILE:-/tmp/aura-production-deploy.lock}"

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

mkdir -p "${BACKUP_DIR}" .deploy

PREVIOUS_REVISION="$(git rev-parse HEAD)"
printf '%s\n' "${PREVIOUS_REVISION}" > .deploy/previous_revision
log "current revision: ${PREVIOUS_REVISION}"

rollback_on_error() {
  local exit_code=$?
  log "deployment failed; starting automatic rollback to ${PREVIOUS_REVISION}"
  if ./rollback.sh "${PREVIOUS_REVISION}"; then
    log "rollback completed"
  else
    log "rollback failed; manual intervention required"
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

log "validating compose configuration"
compose config --quiet

if compose ps postgres --status running >/dev/null 2>&1; then
  BACKUP_FILE="${BACKUP_DIR}/postgres-$(date -u +%Y%m%dT%H%M%SZ)-${PREVIOUS_REVISION:0:12}.sql.gz"
  log "creating database backup: ${BACKUP_FILE}"
  POSTGRES_USER_VALUE="$(grep -E '^POSTGRES_USER=' "${ENV_FILE}" | tail -n 1 | cut -d= -f2- || true)"
  POSTGRES_USER_VALUE="${POSTGRES_USER_VALUE:-postgres}"
  compose exec -T postgres pg_dumpall -U "${POSTGRES_USER_VALUE}" | gzip > "${BACKUP_FILE}"
else
  log "postgres is not running yet; skipping pre-deploy database backup"
fi

log "pulling upstream images where available"
compose pull --ignore-buildable --quiet || log "compose pull skipped or no pullable images were available"

log "building updated images"
compose build --pull postgres migrate bootstrap backend worker beat assistant

log "starting infrastructure"
compose up -d --remove-orphans postgres redis

log "running migrations and bootstrap"
compose up --abort-on-container-exit --exit-code-from migrate migrate
compose up --abort-on-container-exit --exit-code-from bootstrap bootstrap

log "restarting changed application containers"
compose up -d --remove-orphans backend worker beat assistant frontend

log "waiting for Docker health checks"
compose ps

log "verifying public backend health"
wait_for_health "${HEALTHCHECK_URL}" 36 5

log "pruning dangling images older than 24 hours"
docker image prune -f --filter "until=24h" >/dev/null

trap - ERR
log "deployment complete: ${NEW_REVISION}"
