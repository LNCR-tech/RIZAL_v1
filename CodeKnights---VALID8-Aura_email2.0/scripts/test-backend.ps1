$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

# Runs backend pytest inside the already-built backend image.
# No DB/Redis required: tests use in-memory SQLite fixtures.
docker compose run --rm test_backend

