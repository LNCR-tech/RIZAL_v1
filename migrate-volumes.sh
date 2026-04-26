#!/usr/bin/env bash
# =============================================================================
# migrate-volumes.sh
# Migrates Docker named volumes to host bind mounts under ./docker-data/
# =============================================================================
set -euo pipefail

APP_DIR="/home/ubuntu/Aura/Testing/RIZAL_v1"
COMPOSE_FILE="docker-compose.prod.yml"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  echo "=== DRY RUN MODE — no changes will be made ==="
fi

run() {
  if $DRY_RUN; then
    echo "[DRY RUN] $*"
  else
    "$@"
  fi
}

cd "$APP_DIR"

# -----------------------------------------------
# 1. Backup current compose file
# -----------------------------------------------
echo ">>> Backing up $COMPOSE_FILE → ${COMPOSE_FILE}.bak"
run cp "$COMPOSE_FILE" "${COMPOSE_FILE}.bak"

# -----------------------------------------------
# 2. Stop the stack
# -----------------------------------------------
echo ">>> Stopping Docker Compose stack..."
run docker compose -f "$COMPOSE_FILE" down

# -----------------------------------------------
# 3. Create host directories
# -----------------------------------------------
echo ">>> Creating host directories under ./docker-data/"
run mkdir -p docker-data/postgres
run mkdir -p docker-data/imports
run mkdir -p docker-data/branding
run mkdir -p docker-data/insightface
run mkdir -p docker-data/pgadmin

# -----------------------------------------------
# 4. Migrate data from Docker named volumes
# -----------------------------------------------

# Map: old_volume_name → host_directory
declare -A VOLUME_MAP=(
  ["rizal_v1_postgres_data"]="docker-data/postgres"
  ["rizal_v1_import_storage"]="docker-data/imports"
  ["rizal_v1_branding_storage"]="docker-data/branding"
  ["rizal_v1_insightface_models"]="docker-data/insightface"
  ["rizal_v1_pgadmin_data"]="docker-data/pgadmin"
)

for old_vol in "${!VOLUME_MAP[@]}"; do
  dest="${VOLUME_MAP[$old_vol]}"

  # Check if the old volume exists
  if docker volume inspect "$old_vol" &>/dev/null; then
    echo ">>> Migrating volume '$old_vol' → './$dest'"
    run docker run --rm \
      -v "${old_vol}:/src:ro" \
      -v "$(pwd)/${dest}:/dst" \
      alpine sh -c "cp -a /src/. /dst/"
    echo "    ✓ Data copied from '$old_vol'"
  else
    echo ">>> Volume '$old_vol' not found — skipping (may already be migrated)"
  fi
done

# Also check for aura_* external volumes (from the intermediate refactor)
declare -A EXT_VOLUME_MAP=(
  ["aura_postgres_data"]="docker-data/postgres"
  ["aura_import_storage"]="docker-data/imports"
  ["aura_branding_storage"]="docker-data/branding"
  ["aura_insightface_models"]="docker-data/insightface"
  ["aura_pgadmin_data"]="docker-data/pgadmin"
)

for old_vol in "${!EXT_VOLUME_MAP[@]}"; do
  dest="${EXT_VOLUME_MAP[$old_vol]}"
  if docker volume inspect "$old_vol" &>/dev/null; then
    echo ">>> Migrating external volume '$old_vol' → './$dest'"
    run docker run --rm \
      -v "${old_vol}:/src:ro" \
      -v "$(pwd)/${dest}:/dst" \
      alpine sh -c "cp -a /src/. /dst/"
    echo "    ✓ Data copied from '$old_vol'"
  fi
done

# -----------------------------------------------
# 5. Summary
# -----------------------------------------------
echo ""
echo "=== Migration complete ==="
echo ""
echo "Host directories created:"
ls -la docker-data/
echo ""
echo "Old Docker volumes (can be removed after verifying data):"
for old_vol in "${!VOLUME_MAP[@]}"; do
  if docker volume inspect "$old_vol" &>/dev/null; then
    echo "  - $old_vol  (run: docker volume rm $old_vol)"
  fi
done
for old_vol in "${!EXT_VOLUME_MAP[@]}"; do
  if docker volume inspect "$old_vol" &>/dev/null; then
    echo "  - $old_vol  (run: docker volume rm $old_vol)"
  fi
done
echo ""
echo ">>> Stack is STOPPED. Start it manually after verifying:"
echo "    docker compose -f docker-compose.prod.yml up -d --build"
