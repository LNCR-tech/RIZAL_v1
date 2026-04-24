# Frontend Configuration

[<- Back to frontend index](./README.md)

This frontend supports both:

- Web dev server (Vite) configuration via `VITE_*` variables.
- Docker/NGINX runtime config via injected `window.__AURA_RUNTIME_CONFIG__`.

## Vite Dev Server Proxy

Configured in `frontend/vite.config.js`.

- `VITE_BACKEND_PROXY_TARGET`: proxy target for requests under `/__backend__`.
- `VITE_ASSISTANT_PROXY_TARGET`: proxy target for requests under `/__assistant__`.

When set, Vite will rewrite:

- `/__backend__/...` -> `<VITE_BACKEND_PROXY_TARGET>/...`
- `/__assistant__/...` -> `<VITE_ASSISTANT_PROXY_TARGET>/...`

Note: `frontend/.env.development` sets sensible defaults for local dev. It also sets `VITE_ASSISTANT_BASE_URL` to bypass the proxy for the assistant so server-sent events (SSE) streaming is not buffered by the dev proxy.

## Runtime Config (Docker/NGINX)

When running in Docker, the frontend container renders `frontend/runtime-config.js.template` and serves it so the SPA can read:

- `apiBaseUrl` (default `/__backend__`)
- `apiTimeoutMs` (default `15000`)
- `assistantBaseUrl` (default `/__assistant__`)

NGINX reverse-proxy rules live in `frontend/nginx.conf.template` and map:

- `/__backend__/` -> `${BACKEND_ORIGIN}` (default `http://backend:8000`)
- `/__assistant__/` -> `${ASSISTANT_ORIGIN}` (default `http://assistant:8500`)

## Docker Compose Defaults

See `docker-compose.yml` service `frontend` for defaults:

- `BACKEND_ORIGIN`
- `ASSISTANT_ORIGIN`
- `AURA_API_BASE_URL`
- `AURA_API_TIMEOUT_MS`
- `AURA_ASSISTANT_BASE_URL`

For a complete list of env keys, use: [Environment Variables](../reference/env.md).
