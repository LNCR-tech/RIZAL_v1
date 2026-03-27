#!/bin/sh
set -eu

# Keep this script LF-only; Docker's /bin/sh will fail on CRLF line endings.

LOCKFILE="package-lock.json"
STAMP_FILE="node_modules/.package-lock.sha256"

current_lock_hash=""
installed_lock_hash=""

if [ -f "$LOCKFILE" ]; then
  current_lock_hash="$(sha256sum "$LOCKFILE" | awk '{print $1}')"
fi

if [ -f "$STAMP_FILE" ]; then
  installed_lock_hash="$(cat "$STAMP_FILE")"
fi

needs_install="false"

if [ ! -d "node_modules" ]; then
  needs_install="true"
fi

if [ "$current_lock_hash" != "$installed_lock_hash" ]; then
  needs_install="true"
fi

if [ ! -d "node_modules/react-leaflet" ] || [ ! -d "node_modules/leaflet" ]; then
  needs_install="true"
fi

if [ "$needs_install" = "true" ]; then
  echo "Installing frontend dependencies..."
  npm install
  mkdir -p node_modules
  printf "%s" "$current_lock_hash" > "$STAMP_FILE"
fi

exec npm run dev -- --host 0.0.0.0
