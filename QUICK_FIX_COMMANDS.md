# ⚡ QUICK FIX COMMANDS

Copy and paste these commands on your production server:

```bash
# Navigate to project
cd ~/RIZAL_v1

# Rollback failed migration
docker compose -f docker-compose.prod.yml run --rm migrate alembic downgrade -1

# Pull the fix
git pull origin aura_ci_cd

# Restart everything
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d

# Monitor migration
docker logs rizal_v1-migrate-1 -f

# Check services (press Ctrl+C to exit logs first)
docker compose -f docker-compose.prod.yml ps
```

**Done!** ✅

---

## If Rollback Fails

```bash
# Manually reset alembic version
docker exec rizal_v1-db-1 psql -U postgres -d fastapi_db -c "UPDATE alembic_version SET version_num = '85616f5dcc97';"

# Then continue with git pull and restart
git pull origin aura_ci_cd
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

---

## Verify Success

```bash
# All services should be "Up"
docker compose -f docker-compose.prod.yml ps

# Backend should be healthy
curl http://localhost:8001/health

# Frontend should be accessible
curl -I http://localhost:5173
```

---

**That's it!** 🎉

