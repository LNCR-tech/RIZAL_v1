---
sidebar_position: 1
title: Docker Deployment
---

# Docker Deployment

🔒 **Restricted**: Developer documentation

## Quick Start

```bash
# Start all services
docker compose up --build

# Start specific services
docker compose up backend frontend postgres redis
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| `backend` | 8001 | FastAPI backend |
| `frontend` | 5173 | Vue 3 frontend |
| `postgres` | 5432 | PostgreSQL database |
| `redis` | 6379 | Redis cache |
| `assistant` | 8500 | AI assistant |
| `doc-site` | 3000 | Documentation |

## Environment Variables

Copy `.env.example` to `.env` for each service:

```bash
cp backend/.env.example backend/.env
cp frontend-web/.env.example frontend-web/.env
```

## Health Checks

All services include health checks:

```bash
docker compose ps
```

## Logs

View logs:

```bash
docker compose logs -f backend
```

## Troubleshooting

**Port conflicts?**
Change ports in `docker-compose.yml`

**Database not starting?**
Check PostgreSQL logs: `docker compose logs postgres`
