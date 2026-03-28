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

# If the dev server binary is missing, we definitely need an install.
if [ ! -x "node_modules/.bin/vite" ]; then
  needs_install="true"
fi

if [ "$needs_install" = "true" ]; then
  echo "Installing frontend dependencies..."
  # Prefer reproducible installs when lockfile exists.
  # Fall back to `npm install` if CI mode fails (e.g., lockfile drift).
  npm ci || npm install

  if [ ! -x "node_modules/.bin/vite" ]; then
    echo "ERROR: Frontend dependencies install did not produce vite. Retrying with a clean node_modules..." >&2
    rm -rf node_modules
    npm install
  fi

  if [ ! -x "node_modules/.bin/vite" ]; then
    echo "ERROR: vite is still missing after install. Check npm logs above." >&2
    exit 1
  fi

  printf "%s" "$current_lock_hash" > "$STAMP_FILE"
fi

exec npm run dev -- --host 0.0.0.0
