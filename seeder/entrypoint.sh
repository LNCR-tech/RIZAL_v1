#!/bin/sh
# seeder/entrypoint.sh
# Confirmation gate before running the demo seeder.

if [ "$SEED_DATABASE" != "true" ]; then
    echo "[seeder] SEED_DATABASE is not true. Skipping."
    exit 0
fi

echo ""
echo "=========================================================="
echo "  WARNING: DATABASE SEEDER"
echo "=========================================================="
echo "  SEED_DATABASE=true is set."
echo ""
echo "  This will WIPE ALL EXISTING DATA and replace it with"
echo "  generated demo data. This action cannot be undone."
echo ""
echo "  To confirm, set SEED_CONFIRM=yes in your .env file."
echo "=========================================================="
echo ""

if [ "$SEED_CONFIRM" != "yes" ]; then
    echo "[seeder] Blocked: SEED_CONFIRM is not set to 'yes'."
    echo "[seeder] Set SEED_CONFIRM=yes in your .env to proceed."
    echo ""
    exit 1
fi

echo "[seeder] Confirmed. Starting demo seed..."
echo ""

cd /seeder
python seed.py demo
