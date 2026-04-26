# Vue 3 + Vite

This template should help get you started developing with Vue 3 in Vite. The template uses Vue 3 `<script setup>` SFCs, check out the [script setup docs](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup) to learn more.

Learn more about IDE Support for Vue in the [Vue Docs Scaling up Guide](https://vuejs.org/guide/scaling-up/tooling.html#ide-support).

## Docker

This repo ships with a production-style Docker setup so the frontend can be demoed consistently without relying on a local Node install.

### Files

- `Dockerfile`
  Builds the Vue app with Vite, then serves the built files from Nginx.
- `docker-compose.yml`
  Starts the demo container and maps the app to a local port.
- `nginx.conf.template`
  Handles SPA routing and proxies backend requests from `/__backend__` to the configured backend origin.
- `runtime-config.js.template`
  Generates the runtime backend configuration file so the same build can point to a different cloud backend later.
- `public/runtime-config.js`
  Safe browser fallback for local development when no runtime override is injected.
- `.env.docker.example`
  Example runtime configuration for Docker.

### Container

- `aura-web`
  Serves the built Aura frontend on port `80`, keeps Vue Router working with `try_files`, forwards API requests to the external backend through `/__backend__`, and injects runtime backend config on container start.

### Start

1. Copy `.env.docker.example` to `.env.docker`.
2. Set `BACKEND_ORIGIN` to the backend root URL.
   Use the host root, not the `/api` suffix.
   Example: `https://your-ngrok-host.ngrok-free.dev`
3. Optional:
   - keep `AURA_API_BASE_URL=/__backend__` to use the built-in nginx proxy
   - or set `AURA_API_BASE_URL=https://your-cloud-api.example.com` to call the cloud API directly from the browser
   - if you use a direct cloud URL, make sure the backend allows your frontend origin with CORS
4. Run:

```bash
docker compose --env-file .env.docker up --build -d
```

5. Open:

```text
http://localhost:8080
```

### Stop

```bash
docker compose --env-file .env.docker down
```

### Health Check

The container exposes a simple health endpoint at `/healthz` for Docker health checks.

## Cloud Backend Flexibility

The frontend now resolves the backend in this order:

1. `window.__AURA_RUNTIME_CONFIG__.apiBaseUrl`
2. `VITE_API_BASE_URL`
3. default proxy path `/__backend__`

This means you can keep one frontend build and change only runtime config when the backend moves.

### Local Vite development

Use a proxy target in `.env.development.local`:

```env
VITE_API_BASE_URL=/__backend__
VITE_BACKEND_PROXY_TARGET=https://your-cloud-backend.example.com
```

### Docker demo

Use the nginx proxy:

```env
BACKEND_ORIGIN=https://your-cloud-backend.example.com
AURA_API_BASE_URL=/__backend__
```

### Static / cloud frontend hosting

Publish a `runtime-config.js` alongside the built app with:

```js
window.__AURA_RUNTIME_CONFIG__ = {
  apiBaseUrl: 'https://your-cloud-backend.example.com',
  apiTimeoutMs: 15000,
}
```

If your backend root is accidentally configured as `https://host/api`, Aura now normalizes that to the host root automatically to avoid duplicated `/api/api/...` requests.
