#!/bin/sh
set -eu

mode="${SERVICE_MODE:-web}"
import_dir="${IMPORT_STORAGE_DIR:-/tmp/valid8_imports}"
logo_dir="${SCHOOL_LOGO_STORAGE_DIR:-/tmp/valid8_school_logos}"

case "$mode" in
  web)
    exec python /app/scripts/run_runtime_stack.py
    ;;
  worker)
    exec celery -A app.workers.celery_app.celery_app worker \
      --loglevel="${CELERY_LOGLEVEL:-info}" \
      --pool "${CELERY_WORKER_POOL:-solo}" \
      --concurrency "${CELERY_WORKER_CONCURRENCY:-1}"
    ;;
  beat)
    exec celery -A app.workers.celery_app.celery_app beat \
      --loglevel="${CELERY_LOGLEVEL:-info}" \
      --schedule /tmp/celerybeat-schedule
    ;;
  migrate)
    exec alembic upgrade heads
    ;;
  *)
    echo "Unsupported SERVICE_MODE: $mode" >&2
    exit 1
    ;;
esac
