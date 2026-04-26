#!/usr/bin/env bash
# =============================================================================
# migrate-volumes-v2.sh
# Migrates Docker named volumes (or old ./docker-data/) to the canonical
# bind-mount location: /home/ubuntu/Aura/docker-data/
#
# Safe to re-run — skips any destination that already has data.
# Supports --dry-run to preview actions without making changes.
# =============================================================================
set -euo pipefail

APP_DIR="/home/ubuntu/Aura/Testing/RIZAL_v1"
DATA_DIR="/home/ubuntu/Aura/docker-data"
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

has_data() {
  # Returns 0 (true) if directory exists and is non-empty
  local dir="$1"
  [[ -d "$dir" ]] && [[ -n "$(ls -A "$dir" 2>/dev/null)" ]]
}

cd "$APP_DIR"

# -----------------------------------------------
# 1. Stop the stack
# -----------------------------------------------
echo ">>> Stopping Docker Compose stack..."
run docker compose -f "$COMPOSE_FILE" down

# -----------------------------------------------
# 2. Create host directories
# -----------------------------------------------
echo ">>> Creating host directories under $DATA_DIR/"
run mkdir -p "$DATA_DIR/postgres"
run mkdir -p "$DATA_DIR/imports"
run mkdir -p "$DATA_DIR/branding"
run mkdir -p "$DATA_DIR/insightface"
run mkdir -p "$DATA_DIR/pgadmin"

# -----------------------------------------------
# 3. Migrate each data directory
#    Priority: already at destination > old ./docker-data/ > named volume
# -----------------------------------------------

migrate_one() {
  local label="$1"
  local dest="$DATA_DIR/$2"
  local old_local="$APP_DIR/docker-data/$2"
  local named_vol_primary="$3"
  local named_vol_fallback="${4:-}"

  echo ""
  echo "--- $label ---"

  if has_data "$dest"; then
    echo "    ✓ Already at destination ($dest) — skipping"
    return
  fi

  # Try old ./docker-data/ location first (from migrate-volumes.sh v1)
  if has_data "$old_local"; then
    echo "    Found data at $old_local — copying to $dest"
    run cp -a "$old_local/." "$dest/"
    echo "    ✓ Copied from old local path"
    return
  fi

  # Try primary named volume
  if docker volume inspect "$named_vol_primary" &>/dev/null; then
    echo "    Found named volume '$named_vol_primary' — copying to $dest"
    run docker run --rm \
      -v "${named_vol_primary}:/src:ro" \
      -v "${dest}:/dst" \
      alpine sh -c "cp -a /src/. /dst/"
    echo "    ✓ Copied from named volume '$named_vol_primary'"
    return
  fi

  # Try fallback named volume
  if [[ -n "$named_vol_fallback" ]] && docker volume inspect "$named_vol_fallback" &>/dev/null; then
    echo "    Found fallback volume '$named_vol_fallback' — copying to $dest"
    run docker run --rm \
      -v "${named_vol_fallback}:/src:ro" \
      -v "${dest}:/dst" \
      alpine sh -c "cp -a /src/. /dst/"
    echo "    ✓ Copied from named volume '$named_vol_fallback'"
    return
  fi

  echo "    ⚠ No source found — destination will start empty (fresh data)"
}

migrate_one "PostgreSQL data"       "postgres"    "rizal_v1_postgres_data"     "aura_postgres_data"
migrate_one "Import files"          "imports"     "rizal_v1_import_storage"    "aura_import_storage"
migrate_one "Branding / logos"      "branding"    "rizal_v1_branding_storage"  "aura_branding_storage"
migrate_one "InsightFace models"    "insightface" "rizal_v1_insightface_models" "aura_insightface_models"
migrate_one "pgAdmin config"        "pgadmin"     "rizal_v1_pgadmin_data"      "aura_pgadmin_data"

# -----------------------------------------------
# 4. Fix ownership
# -----------------------------------------------
echo ""
echo ">>> Fixing ownership..."
run sudo chown -R 999:999   "$DATA_DIR/postgres"
run sudo chown -R 5050:5050 "$DATA_DIR/pgadmin"
run sudo chown -R 1000:1000 "$DATA_DIR/imports"
run sudo chown -R 1000:1000 "$DATA_DIR/branding"
run sudo chown -R 1000:1000 "$DATA_DIR/insightface"
echo "    ✓ postgres    → 999:999"
echo "    ✓ pgadmin     → 5050:5050"
echo "    ✓ imports     → 1000:1000 (appuser)"
echo "    ✓ branding    → 1000:1000 (appuser)"
echo "    ✓ insightface → 1000:1000 (appuser)"

# -----------------------------------------------
# 5. Summary
# -----------------------------------------------
echo ""
echo "=== Migration complete ==="
echo ""
echo "Data directories:"
ls -lht "$DATA_DIR/"
echo ""
echo "Named volumes still present (safe to remove after verifying):"
for vol in rizal_v1_postgres_data rizal_v1_import_storage rizal_v1_branding_storage \
           rizal_v1_insightface_models rizal_v1_pgadmin_data \
           aura_postgres_data aura_import_storage aura_branding_storage \
           aura_insightface_models aura_pgadmin_data; do
  if docker volume inspect "$vol" &>/dev/null; then
    echo "  docker volume rm $vol"
  fi
done
echo ""
echo ">>> Stack is STOPPED. Start it with:"
echo "    docker compose -f docker-compose.prod.yml up -d --build"
