# Quick Fix Script for Migration Failure (Windows PowerShell)

Write-Host "🔍 Diagnosing migration failure..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Check migration logs
Write-Host "📋 Step 1: Checking migration logs..." -ForegroundColor Yellow
docker logs rizal_v1-migrate-1 --tail 50

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

# Step 2: Check if pgvector is available
Write-Host "🔌 Step 2: Checking pgvector extension..." -ForegroundColor Yellow
$pgvectorResult = docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>&1
Write-Host $pgvectorResult

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ pgvector extension is NOT available" -ForegroundColor Red
    Write-Host ""
    Write-Host "📝 RECOMMENDED SOLUTION:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Option 1: Use pgvector-enabled Postgres image (BEST)" -ForegroundColor Green
    Write-Host "  1. Edit docker-compose.yml"
    Write-Host "  2. Change: image: postgres:15"
    Write-Host "  3. To:     image: pgvector/pgvector:pg15"
    Write-Host "  4. Run:    docker compose down"
    Write-Host "  5. Run:    docker compose up -d"
    Write-Host ""
    Write-Host "Option 2: Skip pgvector migration temporarily" -ForegroundColor Yellow
    Write-Host "  1. Edit: backend/alembic/versions/f7a8b9c0d1e2_*.py"
    Write-Host "  2. Wrap migration in try-except block"
    Write-Host "  3. Run:    docker compose up migrate"
    Write-Host ""
} else {
    Write-Host "✅ pgvector extension is available" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 The issue is likely with our new migration." -ForegroundColor Yellow
    Write-Host "Check the logs above for the specific error."
    Write-Host ""
}

# Step 3: Check current alembic version
Write-Host "🔖 Step 3: Checking current database migration version..." -ForegroundColor Yellow
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "SELECT * FROM alembic_version;" 2>&1

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

# Step 4: Check if attendances table exists
Write-Host "📊 Step 4: Checking if attendances table exists..." -ForegroundColor Yellow
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "\d attendances" 2>&1

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

Write-Host "✅ Diagnosis complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 SUMMARY:" -ForegroundColor Cyan
Write-Host "  - Check the logs above to identify the failing migration"
Write-Host "  - If pgvector error: Use Option 1 or 2 above"
Write-Host "  - If our migration error: Check migration syntax"
Write-Host "  - If database doesn't exist: Initialize database first"
Write-Host ""
Write-Host "🚀 QUICK RESTART (if you want to try again):" -ForegroundColor Cyan
Write-Host "  docker compose up -d"
Write-Host ""
