# Deploy Aura to Docker on Your Laptop

## Quick Start (5 Minutes)

### Step 1: Check Prerequisites

```powershell
# Check Docker is running
docker --version
docker compose version
```

You should see Docker version 20+ and Docker Compose version 2+.

### Step 2: Setup Environment Files

Each service needs its own `.env` file. Copy the examples:

```powershell
# From the project root (C:\Users\USER\IdeaProjects\auraproduction\new)
cd C:\Users\USER\IdeaProjects\auraproduction\new

# Backend
Copy-Item .\backend\.env.example .\backend\.env -Force

# Database
Copy-Item .\database\.env.example .\database\.env -Force

# Assistant
Copy-Item .\assistant\.env.example .\assistant\.env -Force

# Frontend
Copy-Item .\frontend-web\.env.example .\frontend\.env -Force

# Seeder
Copy-Item .\seeder\.env.example .\seeder\.env -Force
```

### Step 3: Configure Backend Environment

Edit `backend\.env`:

```powershell
notepad .\backend\.env
```

**Minimum required settings:**

```env
# Database (matches database/.env)
DATABASE_URL=postgresql://postgres:cmpjdatabase@postgres:5432/fastapi_db

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars

# Redis
REDIS_URL=redis://redis:6379/0

# Email (disabled for local dev)
EMAIL_TRANSPORT=disabled

# API Settings
API_DOCS_ENABLED=true
CORS_ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Face Recognition (optional, can disable)
FACE_SCAN_BYPASS_ALL=true
PRIVILEGED_FACE_VERIFICATION_ENABLED=false

# Rate Limiting (disabled for dev)
RATE_LIMIT_ENABLED=false
```

### Step 4: Configure Database Environment

Edit `database\.env`:

```powershell
notepad .\database\.env
```

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=cmpjdatabase
POSTGRES_DB=fastapi_db

# pgAdmin (optional)
PGADMIN_DEFAULT_EMAIL=admin@example.com
PGADMIN_DEFAULT_PASSWORD=admin123
```

### Step 5: Configure Assistant Environment

Edit `assistant\.env`:

```powershell
notepad .\assistant\.env
```

```env
# Database (same as backend)
ASSISTANT_DB_URL=postgresql://postgres:cmpjdatabase@postgres:5432/fastapi_db

# AI Settings (if you have an AI API)
AI_API_KEY=your-ai-api-key-here
AI_API_BASE=https://api.openai.com/v1
AI_MODEL=gpt-4
```

### Step 6: Configure Frontend Environment

Edit `frontend\.env`:

```powershell
notepad .\frontend\.env
```

```env
VITE_API_BASE_URL=http://localhost:8001
VITE_ASSISTANT_BASE_URL=http://localhost:8500
```

### Step 7: Deploy!

```powershell
# Development mode (includes pgAdmin and log viewer)
docker compose --profile dev up --build

# Or production mode (no dev tools)
docker compose --profile prod up --build
```

**First time will take 5-10 minutes to:**
1. Build all Docker images
2. Download dependencies
3. Run database migrations
4. Bootstrap initial data (roles, admin user)
5. Start all services

### Step 8: Access Your Application

Once you see "AURA SYSTEM IS READY!" in the logs:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173 | See bootstrap output |
| **Backend API** | http://localhost:8001/docs | N/A (Swagger UI) |
| **Assistant API** | http://localhost:8500/docs | N/A (Swagger UI) |
| **pgAdmin** | http://localhost:5050 | admin@example.com / admin123 |
| **Log Viewer** | http://localhost:8080 | N/A |

**Default Admin Login:**
- Email: Check `backend/app/core/app_settings.py` or bootstrap output
- Password: Check bootstrap output (usually printed during first run)

---

## Troubleshooting

### Port Already in Use

If you get "port already allocated" errors:

```powershell
# Check what's using the port
netstat -ano | findstr :8001
netstat -ano | findstr :5173

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or change ports in docker-compose.yml
```

### Database Connection Failed

```powershell
# Check if postgres is healthy
docker compose ps

# View postgres logs
docker compose logs postgres

# Restart postgres
docker compose restart postgres
```

### Backend Won't Start

```powershell
# Check backend logs
docker compose logs backend

# Common issues:
# 1. DATABASE_URL mismatch between backend/.env and database/.env
# 2. Missing SECRET_KEY in backend/.env
# 3. Migrations failed - check migrate service logs
docker compose logs migrate
```

### Frontend Shows API Errors

```powershell
# Check if backend is healthy
curl http://localhost:8001/health

# Check frontend environment
docker compose exec frontend cat /usr/share/nginx/html/runtime-config.js

# Verify CORS settings in backend/.env
```

---

## Useful Commands

### View Logs

```powershell
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres

# Last 100 lines
docker compose logs --tail=100 backend
```

### Restart Services

```powershell
# Restart all
docker compose restart

# Restart specific service
docker compose restart backend
docker compose restart frontend
```

### Stop Everything

```powershell
# Stop but keep data
docker compose down

# Stop and remove volumes (DELETES DATABASE!)
docker compose down -v
```

### Rebuild After Code Changes

```powershell
# Rebuild and restart backend only
docker compose up --build -d backend

# Rebuild everything
docker compose down
docker compose --profile dev up --build
```

### Access Container Shell

```powershell
# Backend shell
docker compose exec backend bash

# Run migrations manually
docker compose exec backend alembic upgrade heads

# Run Python shell
docker compose exec backend python
```

### Database Operations

```powershell
# Connect to PostgreSQL
docker compose exec postgres psql -U postgres -d fastapi_db

# Backup database
docker compose exec postgres pg_dump -U postgres fastapi_db > backup.sql

# Restore database
docker compose exec -T postgres psql -U postgres fastapi_db < backup.sql
```

---

## Development Workflow

### 1. Make Code Changes

Edit files in `backend/`, `frontend-web/`, or `assistant/`

### 2. Rebuild Affected Service

```powershell
# Backend changes
docker compose up --build -d backend worker beat

# Frontend changes
docker compose up --build -d frontend

# Assistant changes
docker compose up --build -d assistant
```

### 3. View Logs

```powershell
docker compose logs -f backend
```

### 4. Test Changes

Visit http://localhost:5173 or http://localhost:8001/docs

---

## Production Deployment

### Before Deploying to Production:

1. **Change SECRET_KEY** in `backend/.env` to a long random string
2. **Change Database Password** in `database/.env`
3. **Enable Email** - Set `EMAIL_TRANSPORT=mailjet_api` and add API keys
4. **Update CORS** - Set `CORS_ALLOWED_ORIGINS` to your production domain
5. **Disable API Docs** - Set `API_DOCS_ENABLED=false`
6. **Enable Rate Limiting** - Set `RATE_LIMIT_ENABLED=true`
7. **Increase Workers** - Set `UVICORN_WORKERS=4` (or match CPU count)
8. **Use Production Profile** - `docker compose --profile prod up -d`

---

## Quick Reference

```powershell
# Start development stack
docker compose --profile dev up --build

# Start in background
docker compose --profile dev up --build -d

# Stop everything
docker compose down

# View logs
docker compose logs -f

# Restart backend
docker compose restart backend

# Rebuild backend
docker compose up --build -d backend

# Clean everything (DELETES DATA!)
docker compose down -v
docker system prune -a
```

---

## Health Checks

All services have health checks. Check status:

```powershell
docker compose ps
```

You should see:
- postgres: healthy
- backend: healthy
- All others: running

---

## Next Steps

1. ✅ Deploy to Docker
2. ✅ Access frontend at http://localhost:5173
3. ✅ Login with admin credentials
4. ✅ Test the latest fixes (249 tests should pass!)
5. 📝 Configure email for production
6. 🚀 Deploy to production server

**Your latest code with all 8 test fixes is now running in Docker!** 🎉
