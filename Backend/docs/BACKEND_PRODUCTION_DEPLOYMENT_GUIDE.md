# Backend Production Deployment Guide

## Purpose

This guide documents the production-oriented Docker release path added beside the existing local development stack.

## Main Files

- `Backend/Dockerfile.prod`
- `Backend/.dockerignore`
- `Frontend/Dockerfile.prod`
- `Frontend/nginx.prod.conf`
- `Frontend/.dockerignore`
- `docker-compose.prod.yml`
- `tools/load_test.py`

## What Changed

- added a backend production image that runs `uvicorn` without `--reload`
- added separate worker and beat runtime support through the same production image
- added a frontend production image that builds Vite assets and serves them through `nginx`
- added `nginx` proxy rules so the release frontend still forwards:
  - `/api/*`
  - `/token`
  - `/openapi.json`
  - `/docs`
  - `/redoc`
  - `/media/school-logos/*`
- added a separate `docker-compose.prod.yml` so the current dev compose flow stays unchanged
- corrected the production build contexts to use the real `Backend/` and `Frontend/` directory casing so Linux deployments do not fail on case-sensitive filesystems
- added a reusable concurrent load-test script for health, login, events, and mixed authenticated traffic

## Release Startup

1. prepare `.env` with real production values
2. build and start the release stack:

`docker compose -f docker-compose.prod.yml --env-file .env up -d --build`

3. open the frontend at:

`http://localhost:${FRONTEND_PORT:-80}`

4. open the backend docs through the frontend proxy at:

`http://localhost:${FRONTEND_PORT:-80}/api/docs`

## Runtime Notes

- the production frontend is the only public service by default
- the backend is kept on the internal Docker network and is reached through the frontend proxy
- backend media and import storage remain on named volumes
- Celery worker and beat still require Redis and the same backend environment variables

## Load Testing

### Health-only smoke load

`python tools/load_test.py --base-url http://127.0.0.1 --scenario health --requests 50 --concurrency 10`

### Direct backend login load

`python tools/load_test.py --base-url http://127.0.0.1:8000 --scenario login --email your-user@example.com --password your-password --requests 100 --concurrency 20`

### Frontend-proxied mixed traffic

`python tools/load_test.py --base-url http://127.0.0.1 --api-prefix /api --scenario mixed --email your-user@example.com --password your-password --requests 100 --concurrency 20 --include-governance`

## Testing

- validate config:
  - `docker compose -f docker-compose.prod.yml config -q`
- verify frontend lint/build still pass:
  - `npm run lint`
  - `npm run build`
- verify backend tests still pass:
  - `Backend\\.venv\\Scripts\\python.exe -m pytest -q Backend/app/tests`
- verify the load-test tool help output:
  - `python tools/load_test.py --help`
- optional smoke checks after startup:
  - `GET /`
  - `GET /api/docs`
  - `GET /openapi.json`
  - run `tools/load_test.py` in `health` mode first, then in `login` or `mixed` mode with a real account
