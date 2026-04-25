# Frontend Configuration

<!--nav-->
[← Frontend Local Dev](local-dev.md) | [🏠 Home](/README.md) | [Frontend Architecture →](architecture.md)

---
<!--/nav-->

This page is the frontend-specific env matrix.

The frontend has its own configuration paths:

- local setup
- production setup
- manual
- Docker
- values shared across both

## Separation Of Concerns

Use the frontend env file that matches the way you are starting the frontend:

- `frontend/.env.development.local`
  Manual `npm run dev`
- `frontend/.env.docker`
  Standalone frontend-only Docker flow inside `frontend/`
- root `.env`
  Repo-root full-stack Docker Compose

Do not put frontend `VITE_*` dev overrides in the root `.env`.

## Local Setup

### Variables That Apply To Both Manual And Docker

The current frontend does not have a shared frontend-only env block that applies to both local manual and local Docker.

- manual local frontend config lives in `frontend/.env.development.local`
- standalone frontend Docker config lives in `frontend/.env.docker`
- repo-root Docker frontend config comes from the root `.env`

### Manual

Env file:

- `frontend/.env.development.local`

Required:

- `VITE_BACKEND_PROXY_TARGET`

Optional:

- `VITE_API_BASE_URL`
- `VITE_API_TIMEOUT_MS`
- `VITE_NATIVE_API_BASE_URL`
- `VITE_ASSISTANT_PROXY_TARGET`
- `VITE_ASSISTANT_BASE_URL`

Tracked starting point:

- `frontend/.env.development.local.example`

Current local example:

```env
VITE_BACKEND_PROXY_TARGET=http://127.0.0.1:8000
VITE_ASSISTANT_PROXY_TARGET=http://127.0.0.1:8500
VITE_ASSISTANT_BASE_URL=http://127.0.0.1:8500
VITE_API_BASE_URL=/__backend__
VITE_API_TIMEOUT_MS=15000
```

Assistant note:

- these assistant variables exist and are valid local frontend config inputs
- however, the current `frontend/vite.config.js` only defines a Vite proxy for `VITE_BACKEND_PROXY_TARGET`
- treat the assistant variables as assistant connectivity config rather than assuming the same proxy behavior is fully wired today

### Docker

There are two Docker paths for the frontend.

#### Standalone Frontend Docker

Env file:

- `frontend/.env.docker`

Required:

- `BACKEND_ORIGIN`

Optional:

- `AURA_PORT`
- `VITE_API_BASE_URL`
- `VITE_API_TIMEOUT_MS`
- `AURA_API_BASE_URL`
- `AURA_API_TIMEOUT_MS`

Tracked starting point:

- `frontend/.env.docker.example`

#### Repo-Root Full-Stack Docker Compose

Env file:

- root `.env`

Required:

- none beyond the backend/assistant shared root `.env` requirements already documented in [Environment Variables](../reference/env.md)

Optional:

- `FRONTEND_PORT`
- `BACKEND_ORIGIN`
- `ASSISTANT_ORIGIN`
- `AURA_API_BASE_URL`
- `AURA_ASSISTANT_BASE_URL`
- `AURA_API_TIMEOUT_MS`

Important:

- the current repo-root `docker-compose.yml` uses backend-facing defaults that are already wired for the local stack
- the frontend service there does not read `frontend/.env.docker`

## Production Setup

### Variables That Apply To Both Manual And Docker

The current frontend does not define a separate shared frontend-only production env block.

### Manual

This usually means a frontend built and hosted outside Docker, with configuration coming from build-time `VITE_*` values or runtime config.

Required:

- a valid backend API target, usually through one of:
  - `VITE_API_BASE_URL`
  - `VITE_BACKEND_PROXY_TARGET`
  - runtime `apiBaseUrl`

Optional:

- `VITE_API_TIMEOUT_MS`
- `VITE_NATIVE_API_BASE_URL`
- `VITE_ASSISTANT_PROXY_TARGET`
- `VITE_ASSISTANT_BASE_URL`

### Docker

#### Standalone Frontend Docker

Required:

- `BACKEND_ORIGIN`

Optional:

- `AURA_PORT`
- `AURA_API_BASE_URL`
- `AURA_API_TIMEOUT_MS`

#### Repo-Root Docker Compose

Important:

- the current repo-root `docker-compose.yml` is local-stack oriented
- for real production frontend Docker deployment against external infra, use a compose override or deployment-specific config instead of assuming the repo-root Compose file is production-ready

## Vite Dev Server Proxy

Configured in `frontend/vite.config.js`.

- `VITE_BACKEND_PROXY_TARGET`: proxy target for requests under `/__backend__`

Current limitation:

- the Vite config currently does not define a matching `/__assistant__` proxy block, even though assistant env vars exist in local frontend configuration

## Runtime Config (Docker / NGINX)

When running in Docker, the frontend container renders `frontend/runtime-config.js.template` and serves:

- `apiBaseUrl`
- `apiTimeoutMs`

The current NGINX template proxies:

- `/__backend__/` -> `${BACKEND_ORIGIN}`

## Source Of Truth

- Vite dev env loading: `frontend/vite.config.js`
- Runtime config template: `frontend/runtime-config.js.template`
- Standalone frontend Docker wiring: `frontend/docker-compose.yml`
- Repo-root frontend Docker wiring: `docker-compose.yml`
