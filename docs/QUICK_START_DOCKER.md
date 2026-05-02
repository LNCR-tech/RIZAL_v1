# 🚀 Quick Start - Deploy to Docker

## Option 1: Automated Script (Recommended)

### Windows:
```cmd
deploy-docker.bat
```

Select option 1 for development mode.

### Manual:
```powershell
# Copy environment files
Copy-Item .\backend\.env.example .\backend\.env
Copy-Item .\database\.env.example .\database\.env
Copy-Item .\assistant\.env.example .\assistant\.env
Copy-Item .\frontend-web\.env.example .\frontend\.env
Copy-Item .\seeder\.env.example .\seeder\.env

# Start development stack
docker compose --profile dev up --build
```

## Option 2: Quick Deploy (One Command)

```powershell
docker compose --profile dev up --build
```

**Note**: You'll need to create `.env` files first (see above).

---

## Access Your Application

Once deployed (5-10 minutes first time):

| Service | URL | Notes |
|---------|-----|-------|
| **Frontend** | http://localhost:5173 | Main application |
| **Backend API** | http://localhost:8001/docs | Swagger UI |
| **Assistant** | http://localhost:8500/docs | AI Assistant API |
| **pgAdmin** | http://localhost:5050 | Database admin (dev only) |
| **Log Viewer** | http://localhost:8080 | Container logs (dev only) |

---

## Default Credentials

### Admin Login
Check the bootstrap output in Docker logs for admin credentials, or see `backend/app/core/app_settings.py`.

### pgAdmin
- Email: `admin@example.com`
- Password: `admin123`

---

## Common Commands

```powershell
# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend

# Stop services
docker compose down

# Restart backend after code changes
docker compose up --build -d backend worker beat

# Clean everything (DELETES DATA!)
docker compose down -v
```

---

## Troubleshooting

### Port Already in Use
```powershell
# Find what's using port 8001
netstat -ano | findstr :8001

# Kill the process
taskkill /PID <PID> /F
```

### Backend Won't Start
```powershell
# Check logs
docker compose logs backend
docker compose logs migrate

# Common fix: Restart postgres
docker compose restart postgres
```

### Database Connection Failed
Make sure `DATABASE_URL` in `backend/.env` matches `database/.env`:
```env
DATABASE_URL=postgresql://postgres:cmpjdatabase@postgres:5432/fastapi_db
```

---

## What's Included

✅ **All 8 test fixes** from the final stabilization patch  
✅ **PostgreSQL** database with migrations  
✅ **Redis** for caching and Celery  
✅ **Backend API** with all endpoints  
✅ **Celery Worker** for background tasks  
✅ **Celery Beat** for scheduled tasks  
✅ **Assistant API** for AI features  
✅ **Frontend** React application  
✅ **pgAdmin** for database management (dev)  
✅ **Log Viewer** for container logs (dev)  

---

## Next Steps

1. ✅ Deploy with `deploy-docker.bat`
2. ✅ Access frontend at http://localhost:5173
3. ✅ Login with admin credentials
4. ✅ Test all features
5. 📝 Configure for production (see DOCKER_DEPLOYMENT_GUIDE.md)

**Your latest code is now running in Docker!** 🎉

For detailed documentation, see [DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md)
