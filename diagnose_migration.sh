#!/bin/bash
# Quick Fix Script for Migration Failure

echo "🔍 Diagnosing migration failure..."
echo ""

# Step 1: Check migration logs
echo "📋 Step 1: Checking migration logs..."
docker logs rizal_v1-migrate-1 --tail 50

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 2: Check if pgvector is available
echo "🔌 Step 2: Checking pgvector extension..."
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>&1

PGVECTOR_STATUS=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $PGVECTOR_STATUS -ne 0 ]; then
    echo "❌ pgvector extension is NOT available"
    echo ""
    echo "📝 RECOMMENDED SOLUTION:"
    echo ""
    echo "Option 1: Use pgvector-enabled Postgres image (BEST)"
    echo "  1. Edit docker-compose.yml"
    echo "  2. Change: image: postgres:15"
    echo "  3. To:     image: pgvector/pgvector:pg15"
    echo "  4. Run:    docker compose down"
    echo "  5. Run:    docker compose up -d"
    echo ""
    echo "Option 2: Skip pgvector migration temporarily"
    echo "  1. Edit: backend/alembic/versions/f7a8b9c0d1e2_*.py"
    echo "  2. Wrap migration in try-except block"
    echo "  3. Run:    docker compose up migrate"
    echo ""
else
    echo "✅ pgvector extension is available"
    echo ""
    echo "📝 The issue is likely with our new migration."
    echo "Check the logs above for the specific error."
    echo ""
fi

# Step 3: Check current alembic version
echo "🔖 Step 3: Checking current database migration version..."
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "SELECT * FROM alembic_version;" 2>&1

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 4: Check if attendances table exists
echo "📊 Step 4: Checking if attendances table exists..."
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "\d attendances" 2>&1

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "✅ Diagnosis complete!"
echo ""
echo "📋 SUMMARY:"
echo "  - Check the logs above to identify the failing migration"
echo "  - If pgvector error: Use Option 1 or 2 above"
echo "  - If our migration error: Check migration syntax"
echo "  - If database doesn't exist: Initialize database first"
echo ""
echo "🚀 QUICK RESTART (if you want to try again):"
echo "  docker compose up -d"
echo ""
