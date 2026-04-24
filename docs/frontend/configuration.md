# Frontend Configuration

[<- Back to frontend index](./README.md)

This frontend supports both:

- Vite dev-server configuration via `frontend/.env.development.local`
- Docker/NGINX runtime configuration via injected `window.__AURA_RUNTIME_CONFIG__`

## Which File To Edit

- Manual `npm run dev`
  Edit `frontend/.env.development.local`
- Standalone frontend Docker flow inside `frontend/`
  Edit `frontend/.env.docker`
- Repo-root Docker Compose
  Edit the root `.env`, not the frontend env files

## Vite Dev Server Proxy

Configured in `frontend/vite.config.js`.

- `VITE_BACKEND_PROXY_TARGET`: proxy target for requests under `/__backend__`

Optional Vite variables used elsewhere in the frontend:

- `VITE_API_BASE_URL`
- `VITE_API_TIMEOUT_MS`
- `VITE_NATIVE_API_BASE_URL`

Start local dev from `frontend/.env.development.local.example`, then create your own untracked `frontend/.env.development.local`.

## Runtime Config (Docker/NGINX)

When running in Docker, the frontend container renders `frontend/runtime-config.js.template` and serves it so the SPA can read:

- `apiBaseUrl` (default `/__backend__`)
- `apiTimeoutMs` (default `15000`)

NGINX reverse-proxy rules live in `frontend/nginx.conf.template` and currently map:

- `/__backend__/` -> `${BACKEND_ORIGIN}` (default `http://backend:8000`)

## Repo-Root Docker Compose Defaults

See `docker-compose.yml` service `frontend` for defaults:

- `BACKEND_ORIGIN`
- `AURA_API_BASE_URL`
- `AURA_API_TIMEOUT_MS`

These values come from the root `.env`, not `frontend/.env.docker`.

## Standalone Frontend Docker Defaults

The standalone frontend flow inside `frontend/` uses:

- `frontend/.env.docker.example` as the tracked template
- `frontend/.env.docker` as the local override

For a complete list of env keys, use: [Environment Variables](../reference/env.md).
