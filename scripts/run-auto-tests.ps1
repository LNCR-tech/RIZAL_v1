$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

# Ensure stack is up (no rebuild).
docker compose up -d

# Run the API-based tester runner and emit PSV logs under ./cmpj.
docker compose --profile test run --rm auto_tests

