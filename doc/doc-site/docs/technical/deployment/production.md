---
sidebar_position: 2
title: Production Deployment
---

# Production Deployment

🔒 **Restricted**: Developer documentation

## Prerequisites

- Docker & Docker Compose installed
- Domain name configured
- SSL certificates ready
- Production environment variables set

## Deployment Steps

### 1. Configure Environment

Set production values in each `.env` file:

```env
# backend/.env
DATABASE_URL=postgresql://user:pass@prod-db:5432/aura
SECRET_KEY=your-production-secret
DEBUG=false
```

### 2. Build Images

```bash
docker compose --profile prod build
```

### 3. Start Services

```bash
docker compose --profile prod up -d
```

### 4. Run Migrations

```bash
docker compose exec backend alembic upgrade head
```

### 5. Create Admin User

```bash
docker compose exec backend python -m app.cli bootstrap \
  --email admin@school.edu \
  --password SecurePassword123
```

## SSL/TLS

Use a reverse proxy (nginx/Caddy) for SSL termination.

## Monitoring

- Check logs: `docker compose logs -f`
- Monitor health: `docker compose ps`
- Set up alerts for service failures

## Backup

Regular database backups:

```bash
docker compose exec postgres pg_dump -U aura aura > backup.sql
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Set strong SECRET_KEY
- [ ] Enable HTTPS only
- [ ] Configure firewall rules
- [ ] Set up monitoring
- [ ] Regular security updates
